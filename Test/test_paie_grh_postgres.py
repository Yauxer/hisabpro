"""GRH et simulation API réellement connectées à PostgreSQL éphémère."""
from pathlib import Path
import json
import uuid
import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_paie_grh_service import parametres_laboratoire


@pytest.fixture(scope='module')
def app_paie(application):
    cible = application['cluster']
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    with application['engine'].connect() as connection:
        migration = (Path(__file__).resolve().parents[1] / 'hisabpro-backend/080_dossiers_employes.sql').read_text(encoding='utf-8')
        connection.exec_driver_sql(migration)
        connection.exec_driver_sql(migration)
        connection.commit()
    yield application


def compte(api):
    suffix = uuid.uuid4().hex[:8]
    email = f'paie-{suffix}@example.com'
    password = 'PaieGRH2026!'
    response = api.post('/api/auth/register', json={'nom':'Admin GRH fictif','email':email,
            'password':password,'raison_sociale':f'GRH fictive {suffix}'})
    assert response.status_code == 200, response.text
    api.headers['Authorization'] = 'Bearer ' + response.json()['access_token']
    return email,password


def dossier(**champs):
    return {'nom':'Salarié fictif','poste':'Comptable','salaire_brut':10000,
            'matricule':'FICTIF-001','numero_cnss':'FICTIF-NON-DECLARABLE',
            'personnes_charge_ir':0,'date_embauche':'2025-01-01',**champs}


def test_api_grh_creer_modifier_archiver_restaurer_et_societes(app_paie):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        response = api.post('/api/employes',json=dossier())
        assert response.status_code == 201,response.text
        premier=response.json()['id']
        autre=api.post('/api/employes',json=dossier(nom='Dernier fictif')).json()['id']
        assert api.get('/api/employes').json()[0]['id'] == autre
        response=api.put(f'/api/employes/{premier}',json=dossier(poste='Responsable fictif',type_contrat='CDD'))
        assert response.status_code == 200,response.text
        assert response.json()['poste'] == 'Responsable fictif'
        assert api.delete(f'/api/employes/{premier}').status_code == 204
        assert premier not in [e['id'] for e in api.get('/api/employes').json()]
        assert premier in [e['id'] for e in api.get('/api/employes?inclure_archives=true').json()]
        assert api.put(f'/api/employes/{premier}',json=dossier(actif=True)).status_code == 200
        compte(api)
        assert api.get('/api/employes?inclure_archives=true').json() == []
        assert api.put(f'/api/employes/{premier}',json=dossier()).status_code == 404
        assert api.delete(f'/api/employes/{premier}').status_code == 404


@pytest.mark.parametrize('valeur',[float('nan'),float('inf'),True,-1])
def test_api_salaire_invalide_ne_persiste_pas(app_paie,valeur):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        avant=api.get('/api/employes?inclure_archives=true').json()
        r=api.post('/api/employes',content=json.dumps(dossier(salaire_brut=valeur)),headers={'Content-Type':'application/json'})
        assert r.status_code == 422,r.text
        assert api.get('/api/employes?inclure_archives=true').json() == avant


def test_api_lecture_interdit_mutations_reelles(app_paie):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        email=f'lecteur-grh-{uuid.uuid4().hex[:8]}@example.com'
        password='LectureGRH2026!'
        response=api.post('/api/utilisateurs',json={'nom':'Lecteur fictif','email':email,'mot_de_passe':password,'role':'lecture'})
        assert response.status_code == 201,response.text
        api.headers.clear()
        response=api.post('/api/auth/login',json={'email':email,'password':password})
        assert response.status_code == 200,response.text
        api.headers['Authorization']='Bearer '+response.json()['access_token']
        assert api.get('/api/employes').status_code == 200
        assert api.get('/api/employes/cotisations?annee=2026&mois=10').status_code == 200
        assert api.post('/api/employes',json=dossier()).status_code == 403
        assert api.put(f'/api/employes/{eid}',json=dossier()).status_code == 403
        assert api.delete(f'/api/employes/{eid}').status_code == 403


def test_api_annee_obligatoire_aucun_fallback(app_paie):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        assert api.get('/api/employes/cotisations').status_code == 422
        assert api.get('/api/employes/cotisations?annee=2026&mois=13').status_code == 422
        result=api.get('/api/employes/cotisations?annee=2099&mois=10').json()
        assert result['annee_taux'] == 2099
        assert result['statut'] == 'bloque'
        assert result['totaux'] is None
        assert result['parametres']['taux'] == []


def test_api_simulation_oracle_et_entrees_sorties(app_paie):
    taux,bareme,deductions=parametres_laboratoire()
    annee=2088  # Paramètres de laboratoire, jamais présentés comme taux légaux.
    with Session(app_paie['engine']) as db:
        db.add_all([models.TauxCotisation(annee=annee,code=t.code,libelle='LABORATOIRE NON REGLEMENTAIRE',
                taux_sal=float(t.taux_sal),taux_pat=float(t.taux_pat),plafond=t.plafond) for t in taux])
        db.add_all([models.BaremeIR(annee=annee,tranche_min=t.tranche_min,tranche_max=t.tranche_max,
                taux=float(t.taux),deduction=t.deduction) for t in bareme])
        db.add_all([models.DeductionIR(annee=annee,code=d.code,montant_an=d.montant_an,max_beneficiaires=d.max_beneficiaires) for d in deductions])
        db.commit()
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        r=api.get(f'/api/employes/cotisations?annee={annee}&mois=10')
        assert r.status_code == 200,r.text
        result=r.json()
        assert result['statut'] == 'simulation'
        assert float(result['totaux']['salaire_net']) == 8903.64
        assert float(result['totaux']['cout_employeur']) == 11749.8
        assert result['avertissements']
        api.put(f'/api/employes/{eid}',json=dossier(personnes_charge_ir=None))
        result=api.get(f'/api/employes/cotisations?annee={annee}&mois=10').json()
        assert result['totaux'] is None
        assert result['employes'][0]['cotisations'] is None
        api.put(f'/api/employes/{eid}',json=dossier(date_embauche=f'{annee}-10-15'))
        result=api.get(f'/api/employes/cotisations?annee={annee}&mois=10').json()
        assert 'proratisation' in str(result['employes'][0]['blocages'])
        api.put(f'/api/employes/{eid}',json=dossier(date_embauche=f'{annee}-11-01'))
        assert api.get(f'/api/employes/cotisations?annee={annee}&mois=10').json()['employes'] == []
        with Session(app_paie['engine']) as db:
            emp=db.get(models.Employe,eid)
            assert db.query(models.Ecriture).filter_by(societe_id=emp.societe_id).count() == 0


def test_migration_droits_colonnes_sans_societe_update(app_paie):
    with app_paie['engine'].begin() as c:
        assert not c.execute(text("SELECT has_table_privilege('hisabpro','employes','UPDATE')")).scalar()
        assert c.execute(text("SELECT has_column_privilege('hisabpro','employes','salaire_brut','UPDATE')")).scalar()
        assert not c.execute(text("SELECT has_column_privilege('hisabpro','employes','societe_id','UPDATE')")).scalar()
        assert not c.execute(text("SELECT has_table_privilege('hisabpro','employes','DELETE')")).scalar()


def test_080_legacy_preserve_et_vrai_runtime_non_owner():
    migration = (Path(__file__).resolve().parents[1] / 'hisabpro-backend/080_dossiers_employes.sql').read_text(encoding='utf-8')
    with cluster_isole() as cible:
        verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
        owner=create_engine(cible['url'])
        runtime=None
        try:
            with owner.begin() as c:
                c.exec_driver_sql('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')
                c.exec_driver_sql('CREATE TABLE employes(id serial PRIMARY KEY,societe_id integer NOT NULL,nom varchar(150) NOT NULL,poste varchar(150),salaire_brut double precision NOT NULL,situation_familiale varchar(20),nb_enfants integer,date_embauche date,actif boolean,created_at timestamp DEFAULT now())')
                c.exec_driver_sql("INSERT INTO employes(societe_id,nom,salaire_brut,actif) VALUES(17,'Historique fictif',7123.45,true)")
                avant=c.exec_driver_sql('SELECT id,societe_id,nom,salaire_brut,actif,created_at FROM employes').all()
                c.exec_driver_sql(migration)
                c.exec_driver_sql(migration)
                assert c.exec_driver_sql('SELECT id,societe_id,nom,salaire_brut,actif,created_at FROM employes').all() == avant
                assert c.exec_driver_sql('SELECT personnes_charge_ir FROM employes').scalar() is None
                assert c.exec_driver_sql('SELECT type_contrat FROM employes').scalar() is None
                c.exec_driver_sql('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
                c.exec_driver_sql('GRANT USAGE ON SCHEMA public TO hisabpro')
            runtime=create_engine(make_url(cible['url']).set(username='hisabpro'))
            with runtime.begin() as c:
                assert c.exec_driver_sql('SELECT current_user,session_user').one() == ('hisabpro','hisabpro')
                assert not c.exec_driver_sql("SELECT has_schema_privilege(current_user,'public','CREATE')").scalar()
                c.exec_driver_sql("UPDATE employes SET poste='Poste fictif',personnes_charge_ir=0 WHERE id=1")
                c.exec_driver_sql("INSERT INTO employes(societe_id,nom,salaire_brut,actif) VALUES(17,'Ajout fictif',0,true)")
                assert c.exec_driver_sql('SELECT count(*) FROM employes').scalar() == 2
            for sql,etat in [
                ('UPDATE employes SET societe_id=18 WHERE id=1','42501'),
                ('UPDATE employes SET id=8 WHERE id=1','42501'),
                ('UPDATE employes SET personnes_charge_ir=7 WHERE id=1','23514'),
                ('DELETE FROM employes WHERE id=1','42501'),
                ('TRUNCATE employes','42501'),
            ]:
                with pytest.raises(DBAPIError) as error:
                    with runtime.begin() as c: c.exec_driver_sql(sql)
                assert error.value.orig.pgcode == etat
            with owner.begin() as c:
                assert c.exec_driver_sql('SELECT id,societe_id,nom,salaire_brut,actif,created_at FROM employes WHERE id=1').all() == avant
        finally:
            if runtime is not None: runtime.dispose()
            owner.dispose()
    assert not cible['directory'].exists()


def test_api_historique_nan_lisible_et_simulation_bloquee(app_paie):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        eid=api.post('/api/employes',json=dossier()).json()['id']
        with Session(app_paie['engine']) as db:
            emp=db.get(models.Employe,eid)
            emp.salaire_brut=float('nan')
            emp.situation_familiale='ancien-code'
            db.commit()
        r=api.get('/api/employes')
        assert r.status_code == 200,r.text
        assert r.json()[0]['salaire_brut'] is None
        assert r.json()[0]['situation_familiale'] == 'ancien-code'
        r=api.get('/api/employes/cotisations?annee=2088&mois=10')
        assert r.status_code == 200,r.text
        assert r.json()['statut'] == 'bloque'
        assert r.json()['totaux'] is None
        assert r.json()['employes'][0]['cotisations'] is None
        with Session(app_paie['engine']) as db:
            assert str(db.get(models.Employe,eid).salaire_brut).lower() == 'nan'
