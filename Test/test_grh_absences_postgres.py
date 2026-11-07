"""Demandes GRH, vrai JWT/FastAPI/PostgreSQL éphémère, aucun calcul de droits."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import uuid
import httpx
import pytest
from sqlalchemy import text,create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
import models
from postgres_isole import cluster_isole,verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_paie_grh_postgres import compte,dossier


@pytest.fixture(scope='module')
def app_grh(application):
    cible=application['cluster']
    verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    with application['engine'].connect() as c:
        for migration in ['080_dossiers_employes.sql','081_grh_absences.sql','081_grh_absences.sql']:
            c.exec_driver_sql((Path(__file__).resolve().parents[1]/'hisabpro-backend'/migration).read_text(encoding='utf-8'))
        c.commit()
    yield application


def demande(eid,**champs):
    return {'employe_id':eid,'type_absence':'conge','date_debut':'2026-07-01','date_fin':'2026-07-03','motif':'Demande fictive',**champs}


def test_parcours_demande_approbation_annulation_historique_persistant(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        r=api.post('/api/employes/conges',json=demande(eid))
        assert r.status_code == 201,r.text
        initial=r.json()
        assert initial['statut']=='demande' and initial['jours_calendaires']==3
        assert initial['peut_decider'] and initial['peut_annuler']
        assert len(initial['historique'])==1
        aid=initial['id']
        r=api.patch(f'/api/employes/conges/{aid}',json={'statut':'approuve','commentaire_decision':'Accord fictif'})
        assert r.status_code==200,r.text
        assert r.json()['statut']=='approuve' and len(r.json()['historique'])==2
        assert not r.json()['peut_decider']
        r=api.patch(f'/api/employes/conges/{aid}',json={'statut':'annule','commentaire_decision':'Annulation fictive'})
        assert r.status_code==200,r.text
        final=r.json()
        assert [e['nouveau_statut'] for e in final['historique']]==['demande','approuve','annule']
        assert not final['peut_annuler'] and not final['peut_decider']
        assert api.get('/api/employes/conges').json()==[final]
        assert api.patch(f'/api/employes/conges/{aid}',json={'statut':'approuve'}).status_code==409
        assert api.post('/api/employes/conges',json=demande(eid)).status_code==201 # Annulé ne consomme aucun solde.
        with Session(app_grh['engine']) as db:
            emp=db.get(models.Employe,eid)
            assert db.query(models.Ecriture).filter_by(societe_id=emp.societe_id).count()==0
            assert emp.salaire_brut==10000


def test_periodes_chevauchement_dates_et_societes(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        first=api.post('/api/employes/conges',json=demande(eid))
        assert first.status_code==201,first.text
        aid=first.json()['id']
        assert api.post('/api/employes/conges',json=demande(eid,date_debut='2026-07-03',date_fin='2026-07-04')).status_code==409
        assert api.post('/api/employes/conges',json=demande(eid,date_debut='2026-07-04',date_fin='2026-07-04')).status_code==201
        assert api.post('/api/employes/conges',json=demande(eid,date_debut='2024-12-31',date_fin='2024-12-31')).status_code==400
        compte(api)
        assert api.get('/api/employes/conges').json()==[]
        assert api.post('/api/employes/conges',json=demande(eid)).status_code==404
        assert api.patch(f'/api/employes/conges/{aid}',json={'statut':'annule'}).status_code==404


def utilisateur(api,role):
    email=f'grh-{uuid.uuid4().hex[:8]}@example.com'
    password='AbsencesGRH2026!'
    r=api.post('/api/utilisateurs',json={'nom':'Utilisateur fictif','email':email,'mot_de_passe':password,'role':role})
    assert r.status_code==201,r.text
    with httpx.Client(base_url=str(api.base_url)) as login:
        r=login.post('/api/auth/login',json={'email':email,'password':password})
        assert r.status_code==200,r.text
        return {'Authorization':'Bearer '+r.json()['access_token']}


def test_permissions_lecture_comptable_et_annulation_auteur(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as admin:
        compte(admin)
        eid=admin.post('/api/employes',json=dossier()).json()['id']
        comptable=utilisateur(admin,'comptable')
        second=utilisateur(admin,'comptable')
        lecture=utilisateur(admin,'lecture')
        with httpx.Client(base_url=app_grh['api_url'],headers=comptable) as api:
            r=api.post('/api/employes/conges',json=demande(eid))
            assert r.status_code==201,r.text
            aid=r.json()['id']
            assert not r.json()['peut_decider'] and r.json()['peut_annuler']
            for cible in ['approuve','refuse']:
                assert api.patch(f'/api/employes/conges/{aid}',json={'statut':cible}).status_code==403
            with httpx.Client(base_url=app_grh['api_url'],headers=second) as autre:
                assert not autre.get('/api/employes/conges').json()[0]['peut_annuler']
                assert autre.patch(f'/api/employes/conges/{aid}',json={'statut':'annule'}).status_code==403
            with httpx.Client(base_url=app_grh['api_url'],headers=lecture) as lecteur:
                result=lecteur.get('/api/employes/conges')
                assert result.status_code==200 and not result.json()[0]['peut_annuler']
                assert lecteur.post('/api/employes/conges',json=demande(eid)).status_code==403
                assert lecteur.patch(f'/api/employes/conges/{aid}',json={'statut':'annule'}).status_code==403
            assert api.patch(f'/api/employes/conges/{aid}',json={'statut':'annule'}).status_code==200


def test_concurrence_deux_demandes_chevauchantes(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        headers=dict(api.headers)
    barriere=Barrier(2)
    def creer(_):
        with httpx.Client(base_url=app_grh['api_url'],headers=headers) as api:
            barriere.wait(timeout=10)
            r=api.post('/api/employes/conges',json=demande(eid))
            return r.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(creer,range(2)))==[201,409]


def test_historique_immutable_owner_runtime_et_migration_idempotente(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        r=api.post('/api/employes/conges',json=demande(eid))
        assert r.status_code==201,r.text
        aid=r.json()['id']
    with app_grh['engine'].begin() as c:
        avant=c.execute(text('SELECT * FROM grh_absence_evenements WHERE absence_id=:id'),{'id':aid}).all()
        c.exec_driver_sql((Path(__file__).resolve().parents[1]/'hisabpro-backend/081_grh_absences.sql').read_text(encoding='utf-8'))
        assert c.execute(text('SELECT * FROM grh_absence_evenements WHERE absence_id=:id'),{'id':aid}).all()==avant
    for sql in ['UPDATE grh_absence_evenements SET commentaire=\'interdit\'', 'DELETE FROM grh_absence_evenements','TRUNCATE grh_absence_evenements']:
        with pytest.raises(DBAPIError) as error:
            with app_grh['engine'].begin() as c:c.exec_driver_sql(sql)
        assert error.value.orig.pgcode=='23514'
        with pytest.raises(DBAPIError) as error:
            with app_grh['engine'].begin() as c:
                c.exec_driver_sql('SET LOCAL ROLE hisabpro')
                c.exec_driver_sql(sql)
        assert error.value.orig.pgcode=='42501'
    with app_grh['engine'].begin() as c:
        assert c.execute(text('SELECT * FROM grh_absence_evenements WHERE absence_id=:id'),{'id':aid}).all()==avant


def test_concurrence_deux_decisions_une_seule_trace(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        r=api.post('/api/employes/conges',json=demande(eid))
        assert r.status_code==201,r.text
        aid=r.json()['id']
        headers=dict(api.headers)
    barriere=Barrier(2)
    def decider(statut):
        with httpx.Client(base_url=app_grh['api_url'],headers=headers) as api:
            barriere.wait(timeout=10)
            r=api.patch(f'/api/employes/conges/{aid}',json={'statut':statut})
            return r.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(decider,['approuve','refuse']))==[200,409]
    with httpx.Client(base_url=app_grh['api_url'],headers=headers) as api:
        result=api.get('/api/employes/conges').json()[0]
        assert len(result['historique'])==2
        assert result['historique'][-1]['nouveau_statut']==result['statut']


def test_fk_societe_interdit_absence_autre_employe_meme_en_sql(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        email,_=compte(api)
    with Session(app_grh['engine']) as db:
        user=db.query(models.Utilisateur).filter_by(email=email).one()
        sid,uid=user.societe_id,user.id
    with pytest.raises(DBAPIError) as error:
        with app_grh['engine'].begin() as c:
            c.execute(text("INSERT INTO grh_absences(societe_id,employe_id,type_absence,date_debut,date_fin,created_by,statut) VALUES(:sid,:eid,'conge','2026-07-01','2026-07-03',:uid,'demande')"),{'sid':sid,'eid':eid,'uid':uid})
    assert error.value.orig.pgcode=='23503'


def test_081_sur_cluster_sans_role_applicatif_et_sans_donnees():
    with cluster_isole() as cible:
        verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
        owner=create_engine(cible['url'])
        try:
            models.Base.metadata.create_all(owner)
            with owner.begin() as c:
                sql=(Path(__file__).resolve().parents[1]/'hisabpro-backend/081_grh_absences.sql').read_text(encoding='utf-8')
                c.exec_driver_sql(sql)
                c.exec_driver_sql(sql)
                assert c.exec_driver_sql("SELECT count(*) FROM pg_roles WHERE rolname='hisabpro'").scalar()==0
                assert c.exec_driver_sql('SELECT count(*) FROM grh_absences').scalar()==0
                assert c.exec_driver_sql('SELECT count(*) FROM grh_absence_evenements').scalar()==0
                assert c.exec_driver_sql('SELECT count(*) FROM ecritures').scalar()==0
        finally:
            owner.dispose()
    assert not cible['directory'].exists()


def test_081_retire_default_cdi_sans_reclasser_valeurs_ambigues(app_grh):
    with httpx.Client(base_url=app_grh['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier(type_contrat='CDI')).json()['id']
    with app_grh['engine'].begin() as c:
        sid=c.execute(text('SELECT societe_id FROM employes WHERE id=:id'),{'id':eid}).scalar()
        c.exec_driver_sql("ALTER TABLE employes ALTER COLUMN type_contrat SET DEFAULT 'CDI'")
        c.execute(text("INSERT INTO employes(societe_id,nom,salaire_brut,actif) VALUES(:sid,'Ancienne colonne fictive',1000,true)"),{'sid':sid})
        avant=c.execute(text('SELECT id,type_contrat FROM employes WHERE societe_id=:sid ORDER BY id'),{'sid':sid}).all()
        assert all(row.type_contrat=='CDI' for row in avant)
        c.exec_driver_sql((Path(__file__).resolve().parents[1]/'hisabpro-backend/081_grh_absences.sql').read_text(encoding='utf-8'))
        assert c.execute(text('SELECT id,type_contrat FROM employes WHERE societe_id=:sid ORDER BY id'),{'sid':sid}).all()==avant
        c.execute(text("INSERT INTO employes(societe_id,nom,salaire_brut,actif) VALUES(:sid,'Contrat non renseigné fictif',1000,true)"),{'sid':sid})
        assert c.execute(text('SELECT type_contrat FROM employes WHERE societe_id=:sid ORDER BY id DESC LIMIT 1'),{'sid':sid}).scalar() is None
