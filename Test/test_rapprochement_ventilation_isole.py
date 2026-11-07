"""Une ligne bancaire réelle de240 rapproche deux lignes comptables120."""
from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path
import uuid
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
import httpx
import models
from test_e2e_facturation_isole import application
from test_reglements_par_tiers_isole import dossier,poster
from test_ras_lecture_conservation import client
from test_lecture_reglements_historiques import photo
from test_articles_alertes_stock_historique_postgres import cible

@pytest.fixture(scope='module',autouse=True)
def migration(application):
    p=Path(__file__).resolve().parents[1]/'hisabpro-backend/084_rapprochement_ventilations.sql'
    if p.exists():
        cible(application)
        with application['engine'].connect() as c:
            raw=c.connection.driver_connection
            for _ in range(2):
                with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf-8'))
                raw.commit()

def preparer(application,api,sens='vente',valider=True):
    _,_,payload=dossier(api,sens)
    r=poster(api,payload);assert r.status_code==201,r.text
    rows=r.json()
    if valider:
        for row in rows:
            r=api.post(f"/api/ecritures/{row['ecriture_id']}/valider",json={})
            assert r.status_code==200,r.text
    r=api.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),
        'libelle':payload['reference'],'montant':240,'sens':'credit' if sens=='vente' else 'debit'})
    assert r.status_code==201,r.text
    with Session(application['engine']) as db:
        lids=sorted(l.id for row in rows for l in db.get(models.Ecriture,row['ecriture_id']).lignes if l.compte=='5141')
    return payload,rows,r.json()['id'],lids

def situation(api,compte='5141'):
    r=api.get(f'/api/rapprochement/{compte}/situation',params={'date_debut':f'{date.today().year}-01-01','date_fin':f'{date.today().year}-12-31'})
    assert r.status_code==200,r.text
    return r.json()

def rapprocher(api,rid,payload):
    return api.post(f'/api/rapprochement/{rid}/rapprocher-ventilation',json={'operation_id':payload['operation_id']})

@pytest.mark.parametrize('sens',['vente','achat'])
def test_240_rapproche120_plus120_origines_inchangees_et_rejeu(application,sens):
    with closing(client(application)[0]) as api:
        payload,rows,rid,lids=preparer(application,api,sens)
        avant=photo(application)
        assert api.post(f'/api/rapprochement/{rid}/rapprocher',json={'ecriture_ligne_id':lids[0]}).status_code==409
        r=rapprocher(api,rid,payload)
        assert r.status_code==200,(r.text,application['api_log'].read_text(encoding='utf-8')[-6500:])
        data=situation(api)
        releve=next(l for l in data['lignes_releve'] if l['id']==rid)
        assert releve['rapprochee'] and releve['ecriture_ligne_ids']==lids
        assert {l['ligne_id'] for l in data['ecritures'] if l['rapprochee']}==set(lids)
        assert len(data['lignes_releve'])==1 and photo(application)==avant
        assert rapprocher(api,rid,payload).status_code==200
        assert photo(application)==avant
        r=api.post(f'/api/rapprochement/{rid}/derapprocher',json={})
        assert r.status_code==200,r.text
        assert not any(l['rapprochee'] for l in situation(api)['ecritures'])
        assert photo(application)==avant

@pytest.mark.parametrize('cas',['montant','sens','compte','brouillon','annule_partiel','absent','autre_societe','periode','reference'])
def test_refus_atomiques(application,cas):
    with closing(client(application)[0]) as api:
        payload,rows,rid,lids=preparer(application,api,valider=cas!='brouillon')
        attendu=409
        if cas=='montant':
            assert api.patch(f'/api/rapprochement/{rid}',json={'montant':240.01}).status_code==200
        elif cas=='sens':
            assert api.patch(f'/api/rapprochement/{rid}',json={'sens':'debit'}).status_code==200
        elif cas=='compte':
            r=api.post('/api/rapprochement',json={'compte':'5142','date':date.today().isoformat(),
                'libelle':'Autre banque fictive','montant':240,'sens':'credit'})
            assert r.status_code==201,r.text
            rid=r.json()['id']
        elif cas=='annule_partiel':
            assert api.post(f"/api/reglements/{rows[0]['id']}/annuler",json={}).status_code==200
        elif cas=='absent':payload['operation_id']=str(uuid.uuid4());attendu=404
        elif cas=='autre_societe':
            with closing(client(application)[0]) as autre:
                autre_payload,_,_,_=preparer(application,autre)
            payload['operation_id']=autre_payload['operation_id'];attendu=404
        elif cas in {'periode','reference'}:
            cible(application)
            with Session(application['engine']) as db:
                if cas=='periode':
                    sid=db.get(models.Reglement,rows[0]['id']).societe_id
                    db.query(models.ExerciceComptable).filter_by(societe_id=sid,annee=date.today().year).one().statut='cloture'
                else:db.get(models.Reglement,rows[1]['id']).reference='AUTRE-REFERENCE-FICTIVE'
                db.commit()
        avant=photo(application)
        r=rapprocher(api,rid,payload)
        assert r.status_code==attendu,r.text
        assert photo(application)==avant
        assert not next(l for l in situation(api,'5142' if cas=='compte' else '5141')['lignes_releve'] if l['id']==rid)['rapprochee']

def test_double_pointage_et_remplacement_refuses_puis_patch_depointage(application):
    with closing(client(application)[0]) as api:
        payload,_,rid,lids=preparer(application,api)
        assert rapprocher(api,rid,payload).status_code==200
        r=api.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),'libelle':'SECOND FICTIF','montant':240,'sens':'credit'})
        assert r.status_code==201
        assert rapprocher(api,r.json()['id'],payload).status_code==409
        assert api.patch(f'/api/rapprochement/{rid}',json={'montant':241}).status_code==409
        assert api.delete(f'/api/rapprochement/{rid}').status_code==409
        assert api.post(f'/api/rapprochement/{rid}/rapprocher',json={'ecriture_ligne_id':lids[0]}).status_code==409
        assert api.patch(f'/api/rapprochement/{rid}',json={'rapprochee':False}).status_code==200
        assert rapprocher(api,r.json()['id'],payload).status_code==200

def test_lien_simple_ancien_et_ventilation_se_protegent_mutuellement(application):
    with closing(client(application)[0]) as api:
        payload,_,rid,lids=preparer(application,api)
        r=api.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),'libelle':'Ligne simple fictive','montant':120,'sens':'credit'})
        assert r.status_code==201
        simple=r.json()['id'];avant=photo(application)
        assert api.post(f'/api/rapprochement/{simple}/rapprocher',json={'ecriture_ligne_id':lids[0]}).status_code==200
        assert rapprocher(api,rid,payload).status_code==409
        assert api.post(f'/api/rapprochement/{simple}/derapprocher',json={}).status_code==200
        assert rapprocher(api,rid,payload).status_code==200
        assert api.post(f'/api/rapprochement/{simple}/rapprocher',json={'ecriture_ligne_id':lids[0]}).status_code==409
        assert photo(application)==avant

def test_concurrence_deux_releves_un_seul_pointage(application):
    with closing(client(application)[0]) as api:
        payload,_,rid,_=preparer(application,api)
        r=api.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),'libelle':'Concurrent fictif','montant':240,'sens':'credit'})
        assert r.status_code==201
        ids=[rid,r.json()['id']];avant=photo(application)
        def requete(i):
            with httpx.Client(base_url=application['api_url'],headers=dict(api.headers),timeout=30) as c:
                return rapprocher(c,i,payload).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(requete,ids))
        assert sorted(codes)==[200,409]
        assert sum(l['rapprochee'] for l in situation(api)['lignes_releve'])==1
        assert photo(application)==avant

def test_meme_uuid_deux_societes_isole_et_lecture_ne_mute_pas(application):
    import httpx
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        payload,_,rid,lids=preparer(application,api)
        _,_,p2=dossier(autre);p2['operation_id']=payload['operation_id']
        r=poster(autre,p2);assert r.status_code==201,r.text
        for row in r.json():assert autre.post(f"/api/ecritures/{row['ecriture_id']}/valider",json={}).status_code==200
        r=autre.post('/api/rapprochement',json={'compte':'5141','date':date.today().isoformat(),'libelle':'Autre société fictive','montant':240,'sens':'credit'})
        assert r.status_code==201;r2=r.json()['id']
        avant=photo(application)
        assert rapprocher(api,rid,payload).status_code==200
        assert rapprocher(autre,r2,p2).status_code==200
        assert rapprocher(autre,rid,payload).status_code==404
        assert {l['ligne_id'] for l in situation(api)['ecritures'] if l['rapprochee']}==set(lids)
        email='lecture392-'+uuid.uuid4().hex[:8]+'@example.com';password='Lecture392!Fictive'
        r=api.post('/api/utilisateurs',json={'nom':'Lecture fictive392','email':email,'mot_de_passe':password,'role':'lecture'})
        assert r.status_code==201,r.text
        with httpx.Client(base_url=application['api_url']) as lecture:
            r=lecture.post('/api/auth/login',json={'email':email,'password':password})
            assert r.status_code==200,r.text
            lecture.headers['Authorization']='Bearer '+r.json()['access_token']
            assert situation(lecture)['ventilations_activees']
            assert rapprocher(lecture,rid,payload).status_code==403
            assert lecture.post(f'/api/rapprochement/{rid}/derapprocher',json={}).status_code==403
        assert photo(application)==avant

def test_cloture_preserve_pointage_et_bloque_sql_et_api_depointage(application):
    from sqlalchemy.exc import DBAPIError
    with closing(client(application)[0]) as api:
        payload,rows,rid,lids=preparer(application,api)
        assert rapprocher(api,rid,payload).status_code==200;cible(application)
        with Session(application['engine']) as db:
            sid=db.get(models.Reglement,rows[0]['id']).societe_id
            db.query(models.ExerciceComptable).filter_by(societe_id=sid,annee=date.today().year).one().statut='cloture'
            db.commit()
        avant=photo(application)
        assert api.post(f'/api/rapprochement/{rid}/derapprocher',json={}).status_code==409
        assert api.patch(f'/api/rapprochement/{rid}',json={'rapprochee':False}).status_code==409
        with application['engine'].connect() as c:
            with pytest.raises(DBAPIError) as err:
                c.execute(text('DELETE FROM rapprochement_ventilations WHERE releve_id=:rid'),{'rid':rid});c.commit()
            assert err.value.orig.pgcode=='23514';c.rollback()
        assert situation(api)['lecture_seule']
        l=next(l for l in situation(api)['lignes_releve'] if l['id']==rid)
        assert l['rapprochee'] and l['ecriture_ligne_ids']==lids
        assert photo(application)==avant

@pytest.mark.parametrize('cas',['rejeu_migration','delete_partiel','montant_releve','truncate','autre_societe','insert_simple_double'])
def test_gardes_postgresql_reelles_et_rejeu(application,cas):
    from sqlalchemy.exc import DBAPIError
    with closing(client(application)[0]) as api:
        payload,rows,rid,lids=preparer(application,api)
        assert rapprocher(api,rid,payload).status_code==200
        avant=photo(application);cible(application)
        with application['engine'].connect() as c:
            if cas=='rejeu_migration':
                p=Path(__file__).resolve().parents[1]/'hisabpro-backend/084_rapprochement_ventilations.sql'
                raw=c.connection.driver_connection
                with raw.cursor() as cur:cur.execute(p.read_text(encoding='utf-8'))
                raw.commit()
            else:
                with pytest.raises(DBAPIError):
                    if cas=='delete_partiel':c.execute(text('DELETE FROM rapprochement_ventilations WHERE ecriture_ligne_id=:lid'),{'lid':lids[0]})
                    elif cas=='montant_releve':c.execute(text('UPDATE rapprochement_lignes SET montant=241 WHERE id=:rid'),{'rid':rid})
                    elif cas=='truncate':c.execute(text('TRUNCATE rapprochement_ventilations'))
                    elif cas=='autre_societe':c.execute(text('UPDATE rapprochement_lignes SET societe_id=societe_id+1000 WHERE id=:rid'),{'rid':rid})
                    else:c.execute(text("INSERT INTO rapprochement_lignes(societe_id,compte,date,montant,sens,rapprochee,ecriture_ligne_id) SELECT societe_id,compte,date,120,sens,TRUE,:lid FROM rapprochement_lignes WHERE id=:rid"),{'rid':rid,'lid':lids[0]})
                    c.commit()
                c.rollback()
        assert photo(application)==avant

def test_role_sql_non_proprietaire_acl_et_guardes(application):
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    with closing(client(application)[0]) as api:
        payload,rows,rid,lids=preparer(application,api)
        assert rapprocher(api,rid,payload).status_code==200
        avant=photo(application);cible(application)
        with application['engine'].begin() as c:
            c.execute(text('CREATE ROLE hisabpro_392_recette LOGIN INHERIT'))
            c.execute(text('GRANT hisabpro TO hisabpro_392_recette'))
        url=make_url(application['cluster']['url']).set(username='hisabpro_392_recette')
        assert url.host=='127.0.0.1' and url.port==application['cluster']['port'] and url.port!=5432
        engine=create_engine(url)
        try:
            with engine.connect() as c:
                assert c.execute(text('SELECT current_user')).scalar()=='hisabpro_392_recette'
                assert not c.execute(text('SELECT rolsuper FROM pg_roles WHERE rolname=current_user')).scalar()
                assert c.execute(text("SELECT pg_get_userbyid(relowner)<>current_user FROM pg_class WHERE relname='rapprochement_ventilations'")).scalar()
                assert c.execute(text('SELECT COUNT(*) FROM rapprochement_ventilations WHERE releve_id=:rid'),{'rid':rid}).scalar()==2
                for sql in ('UPDATE rapprochement_ventilations SET operation_id=operation_id WHERE releve_id=:rid',
                            'DELETE FROM rapprochement_ventilations WHERE ecriture_ligne_id=:lid',
                            'TRUNCATE rapprochement_ventilations'):
                    c.rollback()
                    with pytest.raises(DBAPIError) as err:
                        c.execute(text(sql),{'rid':rid,'lid':lids[0]});c.commit()
                    assert err.value.orig.pgcode==('23514' if sql.startswith('DELETE') else '42501')
                    c.rollback()
            from routers import rapprochement as banque
            with Session(application['engine']) as db:
                releve=db.get(models.RapprochementLigne,rid)
                utilisateur={'societe_id':releve.societe_id,'id':releve.rapproche_par}
            with Session(engine) as db:
                assert banque.rapprocher_ventilation(rid,banque.RapprocherVentilationIn(operation_id=payload['operation_id']),utilisateur,db)['ok']
                assert not banque.derapprocher_ligne(rid,utilisateur,db).rapprochee
                assert banque.rapprocher_ventilation(rid,banque.RapprocherVentilationIn(operation_id=payload['operation_id']),utilisateur,db)['ok']
        finally:engine.dispose()
        assert photo(application)==avant
        l=next(l for l in situation(api)['lignes_releve'] if l['id']==rid)
        assert l['ecriture_ligne_ids']==lids and l['rapprochee']
        r=api.post(f'/api/rapprochement/{rid}/derapprocher',json={})
        assert r.status_code==200,r.text
        assert not any(l['rapprochee'] for l in situation(api)['ecritures'])
        assert photo(application)==avant
