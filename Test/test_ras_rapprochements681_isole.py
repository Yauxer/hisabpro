"""Rapprochement documentaire103 : API/SQL réels sur cluster nonce seulement."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date
from decimal import Decimal
from copy import deepcopy
import json
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_factures_liees635_isole import (
    application as application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,application087,migration)
from test_ras_documents647_isole import capture
from test_ras_tva_capture_isole import preparer,capturer
from test_avances_salaries_isole import appliquer
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_permissions_tva_runtime_isole import donnees_metier
from test_restauration_runtime_acl_089 import catalogue_acl
from postgres_isole import verifier_cible_isolee


PREFIX='/api/tva/ras/captures/'


def chemin(cid):return PREFIX+str(cid)+'/rapprochements'


@pytest.fixture(scope='module')
def application(application102):
    app=application102;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    with closing(client(app)[0]) as api:assert api.get(chemin(1)).status_code==503
    avant=donnees_metier(app);acl=catalogue_acl(app['engine'])
    appliquer(app,'103_ras_rapprochements_versement.sql')
    apres=donnees_metier(app);droits=catalogue_acl(app['engine'])
    assert all(apres[k]==v for k,v in avant.items())
    assert all(all(v in droits[k] for v in vs) for k,vs in acl.items())
    appliquer(app,'103_ras_rapprochements_versement.sql')
    assert donnees_metier(app)==apres and catalogue_acl(app['engine'])==droits
    yield app


def versement(api,montant='75.00',valider=True,compte='4457',banque=True):
    e=ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'BQ' if banque else 'OD',
        'reference':'VERSEMENT-FICTIF681-'+uuid4().hex[:8], 'libelle':'Pièce fictive de rapprochement documentaire',
        'lignes':[{'compte':compte,'debit':montant},{'compte':'5141' if banque else '1111','credit':montant}]}),201)
    if valider:ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
    return e


def corps(e,montant='75.00',**kw):
    return {'ecriture_id':e['id'],'montant':montant,'cle':str(uuid4()),'rapprochement_verifie':True,**kw}


def photo(app):
    with app['engine'].connect() as db:
        return {t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x ORDER BY 1')).scalars().all()
                for t in ('ecritures','lignes_ecriture','reglements','ras_reglement_captures','ras_reglement_annulations','ras_tva_reglement_details')}


def test_681_partiels_idempotence_retrait_historique_et_sources_intactes(application):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);cid=c['capture']['id'];e=versement(api)
        avant=photo(application);initial=ok(api.get(chemin(cid)))
        assert initial['total_rapproche']=='0.00' and initial['capacite_documentaire']=='75.00'
        opt=ok(api.get(chemin(cid)+'/options'))
        assert next(r for r in opt['items'] if r['id']==e['id'])['disponible']=='75.00'
        b=corps(e,'30.00');d=ok(api.post(chemin(cid),json=b),201)
        assert d['total_rapproche']=='30.00' and d['capacite_documentaire']=='45.00'
        assert ok(api.post(chemin(cid),json=b),201)==d
        assert api.post(chemin(cid),json={**b,'montant':'31.00'}).status_code==409
        d=ok(api.post(chemin(cid),json=corps(e,'45.00')),201)
        assert len(d['items'])==2 and d['capacite_documentaire']=='0.00'
        rid=d['items'][0]['id'];retire=ok(api.post(chemin(cid)+f'/{rid}/retirer',json={'motif':'Erreur documentaire fictive'}))
        assert retire['total_rapproche']=='30.00' and retire['capacite_documentaire']=='45.00'
        assert len(retire['items'])==2 and retire['items'][0]['motif_retrait']=='Erreur documentaire fictive'
        assert ok(api.post(chemin(cid)+f'/{rid}/retirer',json={'motif':'Erreur documentaire fictive'}))==retire
        assert api.post(chemin(cid)+f'/{rid}/retirer',json={'motif':'Autre motif'}).status_code==409
        assert photo(application)==avant


@pytest.mark.parametrize('valeur',['NaN','Infinity','-Infinity','-1','0','0.001',True,'10000000000000000'])
def test_681_montants_invalides_refuses_avant_rapprochement(application,valeur):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);e=versement(api)
        avant=donnees_metier(application)
        assert api.post(chemin(c['capture']['id']),json=corps(e,valeur)).status_code==422
        assert donnees_metier(application)==avant


@pytest.mark.parametrize('genre',['brouillon','autre_compte','sans_tresorerie','capture_od','depasse_capture','depasse_piece','non_confirme'])
def test_681_sources_inadaptees_refusees_sans_mutation(application,genre):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);cid=c['capture']['id']
        e=versement(api,'50.00' if genre=='depasse_piece' else '100.00',valider=genre!='brouillon',
            compte='4455' if genre=='autre_compte' else '4457',banque=genre!='sans_tresorerie')
        if genre=='capture_od':e={'id':c['capture']['ecriture_id']}
        b=corps(e,'76.00' if genre=='depasse_capture' else '75.00',rapprochement_verifie=genre!='non_confirme')
        avant=donnees_metier(application)
        assert api.post(chemin(cid),json=b).status_code==(422 if genre=='non_confirme' else 409)
        assert donnees_metier(application)==avant


@pytest.mark.parametrize('limite',['piece','capture'])
def test_681_concurrence_capacite_piece_partagee(application,limite):
    with closing(client(application)[0]) as api:
        _,_,a=capture(api);_,_,b=capture(api);e=versement(api,'75.00')
        liens=[(a,e),(b,e)] if limite=='piece' else [(a,e),(a,versement(api,'75.00'))]
        avant=photo(application)
        def creer(lien):
            c,p=lien
            return api.post(chemin(c['capture']['id']),json=corps(p,'50.00'))
        with ThreadPoolExecutor(max_workers=2) as pool:reponses=list(pool.map(creer,liens))
        assert sorted(r.status_code for r in reponses)==[201,409],[r.text for r in reponses]
        totaux=[Decimal(ok(api.get(chemin(cid)))['total_rapproche']) for cid in {c['capture']['id'] for c,p in liens}]
        assert sum(totaux)==50 and photo(application)==avant


def test_681_capture_annulee_visible_et_nouvelle_affectation_refusee(application):
    with closing(client(application)[0]) as api:
        _,r,c=capture(api);cid=c['capture']['id'];e=versement(api)
        b=corps(e,'30.00');d=ok(api.post(chemin(cid),json=b),201)
        ok(api.post(f'/api/reglements/{r["id"]}/annuler',json={'motif':'Annulation fictive source681','date_annulation':date.today().isoformat()}))
        avant=photo(application)
        d=ok(api.get(chemin(cid)));assert d['capture_annulee'] and d['capacite_documentaire'] is None and d['total_rapproche']=='30.00'
        assert api.post(chemin(cid),json=corps(e,'10.00')).status_code==409
        assert ok(api.post(chemin(cid),json=b),201)==d
        ok(api.post(chemin(cid)+f'/{d["items"][0]["id"]}/retirer',json={'motif':'Revue après annulation source'}))
        assert photo(application)==avant


def test_681_cloisonnement_lecture_ventes_et_capture_brouillon(application):
    a,_,password=client(application);b,email,_=client(application)
    with closing(a),closing(b):
        _,_,c=capture(a);cid=c['capture']['id'];e=versement(a)
        assert b.get(chemin(cid)).status_code==404
        assert a.post(chemin(cid),json=corps(versement(b))).status_code==404
        sid=ok(a.get('/api/auth/me'))['societe_id']
        ok(a.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        b.headers['Authorization']='Bearer '+ok(b.post(f'/api/societes/switcher/{sid}'))['access_token']
        avant=donnees_metier(application)
        assert b.get(chemin(cid)).status_code==200 and b.get(chemin(cid)+'/options').status_code==200
        assert b.post(chemin(cid),json=corps(e)).status_code==403
        assert b.post(chemin(cid)+'/1/retirer',json={'motif':'Interdit'}).status_code==403
        assert donnees_metier(application)==avant
        _,rv=preparer(a,nature='vente');cv,_=capturer(a,rv,nature='vente')
        assert a.get(chemin(cv['capture']['id'])).status_code==409
        _,ra=preparer(a,nature='achat');ca,_=capturer(a,ra,nature='achat')
        assert a.post(chemin(ca['capture']['id']),json=corps(e)).status_code==409


def test_681_trace_sql_immuable_acl_et_rejeu(application):
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);e=versement(api);cid=c['capture']['id']
        d=ok(api.post(chemin(cid),json=corps(e)),201);rid=d['items'][0]['id']
        for table in ('ras_tva_rapprochements','ras_tva_rapprochement_retraits'):
            for commande in (f'UPDATE {table} SET societe_id=societe_id',f'DELETE FROM {table}',f'TRUNCATE {table}'):
                with application['engine'].begin() as db:
                    with pytest.raises(DBAPIError):db.execute(text(commande))
        with application['engine'].connect() as db:
            assert not db.scalar(text("SELECT has_table_privilege('hisabpro','ras_tva_rapprochements','UPDATE')"))
            assert not db.scalar(text("SELECT has_sequence_privilege('hisabpro','ras_tva_rapprochements_id_seq','UPDATE')"))
            assert not db.scalar(text("SELECT has_function_privilege('public','hisabpro_ras_rapprochement_liens()','EXECUTE')"))
        avant=donnees_metier(application);acl=catalogue_acl(application['engine'])
        appliquer(application,'103_ras_rapprochements_versement.sql')
        assert donnees_metier(application)==avant and catalogue_acl(application['engine'])==acl
        assert ok(api.get(chemin(cid)))==d


@pytest.mark.parametrize('limite',['capture','piece'])
def test_681_sql_direct_refuse_depassement_de_capacite(application,limite):
    from services.ras_rapprochement_service import empreinte
    with closing(client(application)[0]) as api:
        _,_,a=capture(api);_,_,b=capture(api);e=versement(api);cid=a['capture']['id']
        d=ok(api.post(chemin(cid),json=corps(e,'60.00')),201)
        f=deepcopy(d['items'][0]['faits']);f['montant']='20.00'
        if limite=='piece':
            cid=b['capture']['id']
            f['capture']={'id':cid,'montant':'75.00','compte_destination':'4457','ecriture_id':b['capture']['ecriture_id']}
        u=ok(api.get('/api/auth/me'));avant=donnees_metier(application)
        with application['engine'].begin() as db:
            with pytest.raises(DBAPIError,match='Capacité' if limite=='capture' else 'Débit disponible'):
                db.execute(text('''INSERT INTO ras_tva_rapprochements(societe_id,capture_id,ecriture_id,montant,cle,faits,empreinte_sha256,created_by)
                    VALUES(:s,:c,:e,20,CAST(:k AS uuid),CAST(:f AS jsonb),:h,:u)'''),
                    {'s':u['societe_id'],'c':cid,'e':e['id'],'k':str(uuid4()),'f':json.dumps(f),'h':empreinte(f),'u':u['id']})
        assert donnees_metier(application)==avant


def test_681_sql_direct_refuse_faits_ne_recoupant_pas_la_piece(application):
    from services.ras_rapprochement_service import empreinte
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);e=versement(api);cid=c['capture']['id']
        d=ok(api.post(chemin(cid),json=corps(e,'30.00')),201)
        f=deepcopy(d['items'][0]['faits']);f['piece']['reference']='REFERENCE INVENTEE INTERDITE'
        uid=ok(api.get('/api/auth/me'))['id'];sid=ok(api.get('/api/auth/me'))['societe_id']
        with application['engine'].begin() as db:
            with pytest.raises(DBAPIError,match='Faits'):
                db.execute(text('''INSERT INTO ras_tva_rapprochements(societe_id,capture_id,ecriture_id,montant,cle,faits,empreinte_sha256,created_by)
                    VALUES(:s,:c,:e,30,CAST(:k AS uuid),CAST(:f AS jsonb),:h,:u)'''),
                    {'s':sid,'c':cid,'e':e['id'],'k':str(uuid4()),'f':json.dumps(f),'h':empreinte(f),'u':uid})
        assert ok(api.get(chemin(cid)))==d


def test_681_pdf_logo_texte_retrait_et_recherche_litterale(application):
    from io import BytesIO
    from pypdf import PdfReader
    with closing(client(application)[0]) as api:
        _,_,c=capture(api);cid=c['capture']['id'];e=versement(api)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        d=ok(api.post(chemin(cid),json=corps(e,'30.00')),201);rid=d['items'][0]['id']
        ok(api.post(chemin(cid)+f'/{rid}/retirer',json={'motif':'Retrait documentaire PDF681'}))
        avant=donnees_metier(application)
        r=api.get(chemin(cid)+'/pdf');assert r.status_code==200,r.text
        pdf=PdfReader(BytesIO(r.content));texte=' '.join(' '.join(p.extract_text() for p in pdf.pages).split())
        assert all(s in texte for s in (e['reference'],'30,00 MAD','Retrait documentaire PDF681',d['items'][0]['empreinte_sha256']))
        assert any(p.images for p in pdf.pages) and 'Ne vaut pas preuve de versement fiscal' in texte
        assert ok(api.get(chemin(cid)+'/options',params={'recherche':'%'}))['items']==[]
        assert ok(api.get(chemin(cid)+'/options',params={'recherche':"' OR true --"}))['items']==[]
        assert api.get(chemin(cid)+'/options',params={'page':0}).status_code==422
        assert donnees_metier(application)==avant
