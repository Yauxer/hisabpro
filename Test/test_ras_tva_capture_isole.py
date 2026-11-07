"""Raccordement571 : vraies API et PostgreSQL nonce098/099, LOGIN limité."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import date, timedelta
from decimal import Decimal
import json
import hashlib
import uuid
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_journal_cloture_concurrente_isole import (
    application as application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)
from test_avances_salaries_isole import appliquer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from recette_restauration_consolidee_084 import empreintes_tables
from test_tva_verrou_exercice_isole import attendre_verrou
from test_ras_tva_simulation import donnees


@pytest.fixture(scope='module')
def application(application098):
    app = application098
    avant = empreintes_tables(app['engine'])
    appliquer(app, '099_ras_tva_details.sql')
    apres = empreintes_tables(app['engine'])
    assert all(apres[k] == v for k, v in avant.items())
    appliquer(app, '099_ras_tva_details.sql')
    assert empreintes_tables(app['engine']) == apres
    yield app


def preparer(api, nature='vente', cash='525.00', taux_ht=0):
    tid = ok(api.post('/api/tiers', json={'nom': 'Tiers TVA fictif571', 'type': 'les_deux'}), 201)['id']
    f = ok(api.post('/api/factures', json={'type': nature, 'date': date.today().isoformat(),
        'tiers': 'Tiers TVA fictif571', 'tiers_id': tid, 'ras_taux': taux_ht,
        'reference': 'FOURNISSEUR-FICTIF571-'+uuid.uuid4().hex[:8],
        'lignes': [{'description': 'Service fictif571', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
    r = paiement(api, f, cash)
    return f, r


def paiement(api, f, cash):
    return ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': f['tiers'],
        'date': date.today().isoformat(), 'montant': cash, 'mode': 'virement', 'comptabiliser': True}), 201)


def demande(**kw):
    return {'simulation': donnees(date_paiement=date.today().isoformat(), **kw),
        'justification_quote_part': 'Ventilation documentaire fictive571'}


def capturer(api, r, data=None, nature='vente'):
    data = data or demande()
    a = ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu", json=data))
    corps = {**data, 'reference': 'RAS-TVA-FICTIVE-'+str(r['id']),
        'compte_destination': '3453' if nature == 'vente' else '4457',
        'empreinte_apercu': a['empreinte_apercu'], 'pieces_verifiees': True}
    return ok(api.post(f"/api/reglements/{r['id']}/ras-tva", json=corps)), corps


@pytest.mark.parametrize('nature', ['vente', 'achat'])
@pytest.mark.parametrize('attestation,cash,ras', [('presentee','525.00','75.00'), ('absente','500.00','100.00')])
def test_571_partiels_solde_validation_idempotence_et_annulation(application, nature, attestation, cash, ras):
    with closing(client(application)[0]) as api:
        f, r = preparer(api, nature, cash)
        kwargs = {'attestation': attestation}
        if attestation == 'absente':
            kwargs.update(date_attestation=None, reference_attestation=None)
        data = demande(**kwargs)
        avant = donnees_metier(application)
        a = ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu", json=data))
        assert donnees_metier(application) == avant
        assert a['dossier']['simulation']['retenue_tva'] == ras
        c1, corps = capturer(api, r, data, nature)
        assert Decimal(str(c1['capture']['montant'])) == Decimal(ras)
        from services.ras_tva_simulation_service import SimulationRasTvaIn
        attendus = SimulationRasTvaIn.model_validate(data['simulation']).model_dump(mode='json')
        attendus.update(montant_paiement_ttc='600.00', tva_paiement='100.00')
        assert c1['dossier']['faits'] == attendus
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 600
        assert ok(api.post(f"/api/reglements/{r['id']}/ras-tva", json=corps)) == c1
        assert api.post(f"/api/reglements/{r['id']}/ras-tva", json={**corps, 'reference': 'CHANGEE'}).status_code == 409
        r2 = paiement(api, f, cash)
        c2, _ = capturer(api, r2, data, nature)
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['est_solde']
        sid = ok(api.get('/api/societe/moi'))['id']
        for c in (c1, c2):
            eid = c['capture']['ecriture_id']
            ok(api.post(f'/api/ecritures/{eid}/valider'))
            assert api.patch(f'/api/ecritures/{eid}', json={'libelle': 'Interdit'}).status_code == 409
            with application['engine'].connect() as db:
                lignes = db.execute(text('SELECT * FROM lignes_ecriture WHERE ecriture_id=:e'), {'e': eid}).mappings().all()
                assert sum(l['debit'] for l in lignes) == sum(l['credit'] for l in lignes) == Decimal(ras)
                tiers = next(l for l in lignes if l['tiers_id'] == f['tiers_id'])
                assert tiers['compte'] == ('3421' if nature == 'vente' else '4411')
                assert tiers['compte_auxiliaire_snapshot']
        dossier = ok(api.get(f"/api/reglements/{r2['id']}/ras-tva"))['dossier']
        with application['engine'].connect() as db:
            originaux = db.execute(text('SELECT row_to_json(e)::text FROM ecritures e WHERE societe_id=:s ORDER BY id'), {'s': sid}).scalars().all()
        ok(api.post(f"/api/reglements/{r2['id']}/annuler", json={'motif': 'Correction fictive571', 'date_annulation': date.today().isoformat()}))
        assert ok(api.get(f"/api/reglements/{r2['id']}/ras-tva"))['dossier'] == dossier
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 600
        with application['engine'].connect() as db:
            apres = db.execute(text('SELECT row_to_json(e)::text FROM ecritures e WHERE societe_id=:s ORDER BY id'), {'s': sid}).scalars().all()
            # L'écriture cash reçoit son lien d'annulation ; les OD validées originales sont conservées.
            for c in (c1,c2):
                oid = c['capture']['ecriture_id']
                assert next(x for x in originaux if json.loads(x)['id']==oid) == next(x for x in apres if json.loads(x)['id']==oid)


@pytest.mark.parametrize('modif,status', [
    ({'tva_paiement':'NaN'},422), ({'tva_paiement': True},422),
    ({'prestation_liste_b':False},422), ({'attestation':'a_qualifier'},422),
    ({'tva_paiement':'90.00'},409), ({'date_paiement':'2026-01-01'},422),
    ({'tva_paiement':'0.00'},422), ({'taux': 1},422),
])
def test_571_refus_sans_piece_ni_capture(application, modif, status):
    with closing(client(application)[0]) as api:
        _, r = preparer(api)
        data = demande(); data['simulation'].update(modif)
        avant = donnees_metier(application)
        refus = api.post(f"/api/reglements/{r['id']}/ras-tva/apercu", json=data)
        assert refus.status_code == status, refus.text
        assert donnees_metier(application) == avant


@pytest.mark.parametrize('quote,tva,cash', [('1250.00','200.00','1100.00'), ('600.00','201.00','449.25')])
def test_571_cumul_ne_depasse_pas_facture(application, quote, tva, cash):
    with closing(client(application)[0]) as api:
        _,r = preparer(api,cash=cash)
        data = demande(montant_paiement_ttc=quote,tva_paiement=tva)
        avant = donnees_metier(application)
        assert api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data).status_code==409
        assert donnees_metier(application)==avant


def test_571_autres_paiements_non_qualifies_et_ras_ht_refuses(application):
    with closing(client(application)[0]) as api:
        f,r=preparer(api)
        paiement(api,f,10)
        assert api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=demande()).status_code==409
        _,rht=preparer(api,taux_ht=10)
        refus=api.post(f"/api/reglements/{rht['id']}/ras-tva/apercu",json=demande())
        assert refus.status_code==409 and 'HT' in refus.text


def test_571_apercu_perime_confirmation_droits_et_societes(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        f,r=preparer(api)
        data=demande(); a=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data))
        corps={**data,'reference':'TEST571','compte_destination':'3453','empreinte_apercu':a['empreinte_apercu'],'pieces_verifiees':True}
        avant=donnees_metier(application)
        assert api.post(f"/api/reglements/{r['id']}/ras-tva",json={**corps,'pieces_verifiees':False}).status_code==422
        assert api.post(f"/api/reglements/{r['id']}/ras-tva",json={**corps,'pieces_verifiees':'true'}).status_code==422
        assert api.post(f"/api/reglements/{r['id']}/ras-tva",json={**corps,'justification_quote_part':'Autre ventilation'}).status_code==409
        assert api.post(f"/api/reglements/{r['id']}/ras-tva",json={**corps,'compte_destination':'3421'}).status_code==422
        for suffix in ('','/apercu'):
            assert autre.post(f"/api/reglements/{r['id']}/ras-tva{suffix}",json=corps if not suffix else data).status_code==404
        assert autre.get(f"/api/reglements/{r['id']}/ras-tva").status_code==404
        email='lecteur571-'+uuid.uuid4().hex[:8]+'@example.com';password='LectureFictive571!'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture571','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
            lecteur.headers['Authorization']='Bearer '+token
            assert lecteur.post(f"/api/reglements/{r['id']}/ras-tva",json=corps).status_code==403
            assert lecteur.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data).status_code==200
        # Création volontaire du lecteur mise à part, aucune pièce ou capture créée.
        for table in ('ecritures','lignes_ecriture','ras_reglement_captures','ras_tva_reglement_details'):
            assert donnees_metier(application)[table]==avant[table]


def test_571_deux_post_concurrents_un_dossier(application):
    with closing(client(application)[0]) as api:
        _,r=preparer(api);data=demande()
        a=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data))
        corps={**data,'reference':'CONCURRENT571','compte_destination':'3453','empreinte_apercu':a['empreinte_apercu'],'pieces_verifiees':True}
        def envoyer():
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as c:
                return c.post(f"/api/reglements/{r['id']}/ras-tva",json=corps)
        with application['engine'].connect() as db, ThreadPoolExecutor(2) as pool:
            tx=db.begin();db.execute(text('SELECT id FROM reglements WHERE id=:r FOR UPDATE'),{'r':r['id']})
            try:
                premier=pool.submit(envoyer);attendre_verrou(application,premier,table='reglements')
                second=pool.submit(envoyer)
            finally:tx.rollback()
            resultats=[premier.result(timeout=30),second.result(timeout=30)]
        assert [x.status_code for x in resultats]==[200,200],[x.text for x in resultats]
        assert resultats[0].json()==resultats[1].json()
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT count(*) FROM ras_tva_reglement_details d JOIN ras_reglement_captures c ON c.id=d.capture_id WHERE c.reglement_id=:r'),{'r':r['id']})==1


def test_571_dossier_sql_immuable_et_acl(application):
    with closing(client(application)[0]) as api:
        _,r=preparer(api);c,_=capturer(api,r)
        cid=c['capture']['id']
        for sql in ['UPDATE ras_tva_reglement_details SET dossier=dossier WHERE capture_id=:c',
                    'DELETE FROM ras_tva_reglement_details WHERE capture_id=:c',
                    'TRUNCATE ras_tva_reglement_details']:
            with application['engine'].connect() as db:
                with pytest.raises(DBAPIError) as erreur:db.execute(text(sql),{'c':cid})
                assert erreur.value.orig.pgcode=='23514'
                db.rollback()
        with application['engine'].connect() as db:
            assert db.scalar(text("SELECT has_table_privilege('hisabpro','ras_tva_reglement_details','SELECT,INSERT')"))
            for droit in ('UPDATE','DELETE','TRUNCATE'):
                assert not db.scalar(text("SELECT has_table_privilege('hisabpro','ras_tva_reglement_details',:d)"),{'d':droit})


def test_571_erreur_trace_annule_toute_la_transaction(application):
    """Faute native après insertion OD/capture, aucune interception du code métier."""
    with closing(client(application)[0]) as api:
        _,r=preparer(api);data=demande()
        a=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data))
        corps={**data,'reference':'ROLLBACK571','compte_destination':'3453','empreinte_apercu':a['empreinte_apercu'],'pieces_verifiees':True}
        avant=donnees_metier(application)
        with application['engine'].begin() as db:
            db.execute(text("""CREATE FUNCTION public.fictive571_refuser_trace() RETURNS trigger LANGUAGE plpgsql AS $$
                BEGIN RAISE EXCEPTION 'Faute native fictive571'; END $$;
                CREATE TRIGGER fictive571_refuser BEFORE INSERT ON public.ras_tva_reglement_details
                FOR EACH ROW EXECUTE FUNCTION public.fictive571_refuser_trace();"""))
        try:
            refus=api.post(f"/api/reglements/{r['id']}/ras-tva",json=corps)
            assert refus.status_code==500
            assert donnees_metier(application)==avant
        finally:
            with application['engine'].begin() as db:
                db.execute(text('DROP TRIGGER fictive571_refuser ON public.ras_tva_reglement_details; DROP FUNCTION public.fictive571_refuser_trace()'))
        # Le même aperçu est toujours valable : la première transaction a été annulée.
        assert api.post(f"/api/reglements/{r['id']}/ras-tva",json=corps).status_code==200


def test_571_periode_fermee_apres_apercu_refuse_capture(application):
    with closing(client(application)[0]) as api:
        _,r=preparer(api);data=demande()
        a=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data))
        corps={**data,'reference':'PERIODE571','compte_destination':'3453','empreinte_apercu':a['empreinte_apercu'],'pieces_verifiees':True}
        for e in ok(api.get('/api/ecritures',params={'exercice':date.today().year})):
            if not e['est_validee']:
                ok(api.post(f"/api/ecritures/{e['id']}/valider"))
        ok(api.patch(f'/api/exercices/{date.today().year}/periodes/{date.today().month}',json={'statut':'fermee'}))
        avant=donnees_metier(application)
        refus=api.post(f"/api/reglements/{r['id']}/ras-tva",json=corps)
        assert refus.status_code in (409,423),refus.text
        assert donnees_metier(application)==avant


def test_571_capture_libre_existante_non_requalifiee(application):
    with closing(client(application)[0]) as api:
        _,r=preparer(api)
        libre={'montant':75,'reference':'LIBRE571','date_operation':date.today().isoformat(),'compte_destination':'3453'}
        ok(api.post(f"/api/reglements/{r['id']}/ras",json=libre))
        avant=donnees_metier(application)
        assert api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=demande()).status_code==409
        assert ok(api.get(f"/api/reglements/{r['id']}/ras-tva"))['dossier'] is None
        assert donnees_metier(application)==avant


@pytest.mark.parametrize('alteration',['societe','net','tva_absente','simulation_absente','confirmation_texte'])
def test_571_sql_refuse_dossier_incoherent(application, alteration):
    with closing(client(application)[0]) as api:
        _,r=preparer(api);c,_=capturer(api,r)
        d=json.loads(json.dumps(c['dossier']))
        if alteration=='societe':d['source']['societe_id']+=1
        if alteration=='net':d['simulation']['net_apres_cette_ras_tva']='0.00'
        if alteration=='tva_absente':
            d['faits'].pop('tva_paiement');d['simulation'].pop('base_tva')
        if alteration=='simulation_absente':d.pop('simulation')
        if alteration=='confirmation_texte':d['pieces_verifiees']='true'
        with application['engine'].connect() as db:
            with pytest.raises(DBAPIError) as erreur:
                db.execute(text('INSERT INTO ras_tva_reglement_details(capture_id,societe_id,dossier) VALUES(:c,:s,CAST(:d AS jsonb))'),
                    {'c':c['capture']['id'],'s':d['source']['societe_id'],'d':json.dumps(d)})
            # Trigger avant l'unicité : ces dossiers ne passent pas le contrôle de liens.
            assert erreur.value.orig.pgcode=='23514'
            db.rollback()


def test_571_declaration_tva_ne_fabrique_pas_un_solde_sur_le_seul_cash(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        _,r=preparer(api)
        params={'exercice':date.today().year,'mois':date.today().month}
        ok(api.get('/api/tva/declaration',params=params))
        capturer(api,r)
        avant=donnees_metier(application)
        refus=api.get('/api/tva/declaration',params=params)
        assert refus.status_code==409 and 'trésorerie' in refus.text
        assert donnees_metier(application)==avant
        ok(autre.get('/api/tva/declaration',params=params))
        if date.today().month>1:
            ok(api.get('/api/tva/declaration',params={**params,'mois':date.today().month-1}))
        ok(api.post(f"/api/reglements/{r['id']}/annuler",json={'motif':'Annulation fictive571','date_annulation':date.today().isoformat()}))
        ok(api.get('/api/tva/declaration',params=params))


@pytest.mark.parametrize('ttc,tva',[('600','100'),('6E+2','1E+2')])
def test_573_rejeu_semantique_preserve_ancienne_representation(application,ttc,tva):
    """Dossier au format571 initial créé uniquement dans le cluster de test."""
    with closing(client(application)[0]) as api:
        _,r=preparer(api);data=demande()
        a=ok(api.post(f"/api/reglements/{r['id']}/ras-tva/apercu",json=data))
        d=a['dossier'];d['faits'].update(montant_paiement_ttc=ttc,tva_paiement=tva)
        empreinte=hashlib.sha256(json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
        d.update(empreinte_apercu=empreinte,pieces_verifiees=True)
        c=ok(api.post(f"/api/reglements/{r['id']}/ras",json={'montant':75,'date_operation':date.today().isoformat(),'reference':'HISTORIQUE573','compte_destination':'3453'}))
        with application['engine'].begin() as db:
            db.execute(text('INSERT INTO ras_tva_reglement_details(capture_id,societe_id,dossier) VALUES(:c,:s,CAST(:d AS jsonb))'),
                {'c':c['id'],'s':d['source']['societe_id'],'d':json.dumps(d)})
        avant=donnees_metier(application)
        corps={**data,'reference':'HISTORIQUE573','compte_destination':'3453','empreinte_apercu':empreinte,'pieces_verifiees':True}
        replay=ok(api.post(f"/api/reglements/{r['id']}/ras-tva",json=corps))
        assert replay['capture']['id']==c['id'] and replay['dossier']==d
        assert donnees_metier(application)==avant
