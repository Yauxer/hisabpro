"""Propositions en lecture seule puis pointage atomique : API/PGnonce protégés."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import uuid
import httpx
import pytest
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_reglements_par_tiers_isole import dossier
from test_rapprochement_ventilation_isole import migration,preparer,situation
from test_lecture_reglements_historiques import photo
from test_articles_alertes_stock_historique_postgres import cible

def deux_propositions(application,api):
    p,_,rid,_=preparer(application,api)
    _,ids,source=dossier(api)
    ref='SIMPLE-FICT-'+uuid.uuid4().hex[:8]
    r=api.post('/api/reglements',json={'facture_id':ids[0],'tiers_id':source['tiers_id'],
        'tiers':'Tiers fictif','date':date.today().isoformat(),'montant':60,'mode':'virement','reference':ref})
    assert r.status_code==201,r.text
    assert api.post(f"/api/ecritures/{r.json()['ecriture_id']}/valider",json={}).status_code==200
    r=api.post('/api/rapprochement',json={'date':date.today().isoformat(),'compte':'5141',
        'montant':60,'sens':'credit','libelle':ref});assert r.status_code==201,r.text
    return rid,r.json()['id']

def proposer(api,compte='5141'):
    r=api.get(f'/api/rapprochement/{compte}/propositions',params={'date_debut':f'{date.today().year}-01-01','date_fin':f'{date.today().year}-12-31'})
    assert r.status_code==200,r.text
    return r.json()

def confirmer(api,p,ids=None,compte='5141'):
    return api.post(f'/api/rapprochement/{compte}/rapprocher-propositions',json={
        'date_debut':p['date_debut'],'date_fin':p['date_fin'],'empreinte':p['empreinte'],
        'releve_ids':ids if ids is not None else [x['releve_id'] for x in p['propositions']]})

def flags(api):
    return {r['id']:r['rapprochee'] for r in situation(api)['lignes_releve']}

def test_simple_et_lot_lus_sans_mutation_puis_confirmation_unique(application,migration):
    with closing(client(application)[0]) as api:
        rid,simple=deux_propositions(application,api);avant=photo(application)
        p=proposer(api);assert len(p['propositions'])==2
        assert photo(application)==avant and not any(flags(api).values())
        r=confirmer(api,p);assert r.status_code==200,r.text
        assert r.json()['nb_rapprochees']==2 and all(flags(api).values())
        assert len([x for x in situation(api)['ecritures'] if x['rapprochee']])==3
        assert photo(application)==avant
        assert confirmer(api,p).status_code==409
        assert photo(application)==avant

@pytest.mark.parametrize('cas',['libelle','montant','pointage','autre_compte','selection_double','selection_etrangere'])
def test_preview_obsolete_ou_selection_invalides_aucun_pointage_partiel(application,migration,cas):
    with closing(client(application)[0]) as api:
        rid,simple=deux_propositions(application,api);p=proposer(api)
        ids=None;compte='5141'
        if cas in {'libelle','montant'}:
            r=api.patch(f'/api/rapprochement/{simple}',json={cas:'CHANGEMENT-FICTIF' if cas=='libelle' else 60.01})
            assert r.status_code==200,r.text
        elif cas=='pointage':
            s=next(x for x in p['propositions'] if x['releve_id']==simple)
            assert api.post(f'/api/rapprochement/{simple}/rapprocher',json={'ecriture_ligne_id':s['ecriture_ligne_id']}).status_code==200
        elif cas=='autre_compte':compte='5142'
        elif cas=='selection_double':ids=[rid,rid]
        else:
            with closing(client(application)[0]) as autre:
                foreign,_=deux_propositions(application,autre)
            ids=[simple,foreign]
        avant=photo(application);before=flags(api)
        r=confirmer(api,p,ids,compte);assert r.status_code==409,r.text
        assert flags(api)==before and photo(application)==avant

def test_sous_selection_puis_recalcul_du_reste(application,migration):
    with closing(client(application)[0]) as api:
        rid,simple=deux_propositions(application,api);p=proposer(api)
        assert confirmer(api,p,[simple]).status_code==200
        assert flags(api)=={rid:False,simple:True}
        p=proposer(api);assert [x['releve_id'] for x in p['propositions']]==[rid]
        assert confirmer(api,p).status_code==200
        assert all(flags(api).values())


@pytest.mark.parametrize('champ,valeur',[('releve_ids',[]),('releve_ids',[True]),
    ('releve_ids',[1.0]),('releve_ids',['1']),('releve_ids',list(range(501))),
    ('empreinte','invalide'),('empreinte','A'*64)])
def test_payload_confirmation_invalide_refuse_avant_mutation(application,migration,champ,valeur):
    with closing(client(application)[0]) as api:
        deux_propositions(application,api);p=proposer(api);avant=photo(application);before=flags(api)
        data={k:p[k] for k in ['date_debut','date_fin','empreinte']}
        data['releve_ids']=[x['releve_id'] for x in p['propositions']];data[champ]=valeur
        r=api.post('/api/rapprochement/5141/rapprocher-propositions',json=data)
        assert r.status_code==422,r.text
        assert photo(application)==avant and flags(api)==before

def test_trigger_refus_second_pointage_annule_toute_transaction(application,migration):
    with closing(client(application)[0]) as api:
        rid,simple=deux_propositions(application,api);p=proposer(api);avant=photo(application)
        cible(application)
        with application['engine'].connect() as db:
            liens_avant=db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_ventilations t ORDER BY releve_id,ecriture_ligne_id')).scalars().all()
        with application['engine'].begin() as db:
            db.execute(text(f"""CREATE FUNCTION refus_pointage405() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
                IF NEW.id={simple} AND NEW.rapprochee THEN RAISE EXCEPTION 'Refus nonce volontaire' USING ERRCODE='23514';END IF;RETURN NEW;END $$"""))
            db.execute(text('CREATE TRIGGER refus_pointage405 BEFORE UPDATE ON rapprochement_lignes FOR EACH ROW EXECUTE FUNCTION refus_pointage405()'))
        try:
            r=confirmer(api,p);assert r.status_code==409,r.text
            assert not any(flags(api).values()) and photo(application)==avant
            with application['engine'].connect() as db:
                assert db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_ventilations t ORDER BY releve_id,ecriture_ligne_id')).scalars().all()==liens_avant
        finally:
            with application['engine'].begin() as db:
                db.execute(text('DROP TRIGGER refus_pointage405 ON rapprochement_lignes'))
                db.execute(text('DROP FUNCTION refus_pointage405()'))


def test_pointage_simple_hors_periode_reste_exclu_des_propositions(application,migration):
    with closing(client(application)[0]) as api:
        rid,simple=deux_propositions(application,api);p=proposer(api)
        s=next(x for x in p['propositions'] if x['releve_id']==simple)
        jour=date.today();autre=date(jour.year,1,1) if (jour.month,jour.day)!=(1,1) else date(jour.year,12,31)
        r=api.post('/api/rapprochement',json={'date':autre.isoformat(),'compte':'5141',
            'montant':60,'sens':'credit','libelle':'Pointage fictif autre date'})
        assert r.status_code==201,r.text
        assert api.post(f"/api/rapprochement/{r.json()['id']}/rapprocher",json={'ecriture_ligne_id':s['ecriture_ligne_id']}).status_code==200
        r=api.get('/api/rapprochement/5141/propositions',params={'date_debut':jour.isoformat(),'date_fin':jour.isoformat()})
        assert r.status_code==200,r.text
        assert [x['releve_id'] for x in r.json()['propositions']]==[rid]
        assert flags(api)[simple] is False


def test_deux_confirmations_concurrentes_une_seule_transaction(application,migration):
    with closing(client(application)[0]) as api:
        deux_propositions(application,api);p=proposer(api);avant=photo(application)
        def envoyer(_):
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as c:
                return confirmer(c,p).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            assert sorted(pool.map(envoyer,range(2)))==[200,409]
        assert all(flags(api).values()) and photo(application)==avant


def test_periode_cloturee_ne_peut_pas_confirmer(application,migration):
    with closing(client(application)[0]) as api:
        rid,_=deux_propositions(application,api);p=proposer(api)
        cible(application)
        with application['engine'].begin() as db:
            sid=db.execute(text('SELECT societe_id FROM rapprochement_lignes WHERE id=:id'),{'id':rid}).scalar_one()
            db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:sid AND annee=:annee"),{'sid':sid,'annee':date.today().year})
        avant=photo(application)
        assert proposer(api)['lecture_seule'] is True
        r=confirmer(api,p);assert r.status_code==409,r.text
        assert not any(flags(api).values()) and photo(application)==avant


def test_role_lecture_peut_consulter_sans_pouvoir_confirmer(application,migration):
    with closing(client(application)[0]) as api:
        deux_propositions(application,api);p=proposer(api);avant=photo(application)
        email='lecture405-'+uuid.uuid4().hex[:8]+'@example.com';password='Lecture405!Fictive'
        r=api.post('/api/utilisateurs',json={'nom':'Lecture fictive405','email':email,'mot_de_passe':password,'role':'lecture'})
        assert r.status_code==201,r.text
        with httpx.Client(base_url=application['api_url']) as lecture:
            r=lecture.post('/api/auth/login',json={'email':email,'password':password})
            assert r.status_code==200,r.text
            lecture.headers['Authorization']='Bearer '+r.json()['access_token']
            assert len(proposer(lecture)['propositions'])==2
            assert confirmer(lecture,p).status_code==403
        assert not any(flags(api).values()) and photo(application)==avant
