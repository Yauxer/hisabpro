"""Reproduction du crash sur ancienne base ; PostgreSQL éphémère uniquement."""
import os
from datetime import date
from pathlib import Path
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError, ProgrammingError
from sqlalchemy.orm import Session

import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from services.grh_bootstrap_service import initialiser_schema_developpement

BACK = Path(__file__).resolve().parents[1] / 'hisabpro-backend'


def ancienne_base(engine):
    exclues = {'employes', 'grh_absences', 'grh_absence_evenements'}
    models.Base.metadata.create_all(engine, tables=[
        t for t in models.Base.metadata.sorted_tables if t.name not in exclues])
    with Session(engine) as db:
        societe = models.Societe(raison_sociale='Société fictive reprise GRH')
        db.add(societe)
        db.commit()
        sid = societe.id
        ecriture = models.Ecriture(societe_id=sid, date=date(2025, 1, 1),
            journal=models.JournalEnum.BQ, libelle='Apport fictif conservé',
            reference='FICTIF-STARTUP', numero_ecriture='BQ-2025-FICTIF',
            exercice=2025, est_validee=True,
            lignes=[models.LigneEcriture(compte='5141', debit=100, credit=0),
                    models.LigneEcriture(compte='1111', debit=0, credit=100)])
        db.add(ecriture)
        db.commit()
    with engine.begin() as c:
        c.execute(text('''CREATE TABLE public.employes (
            id serial PRIMARY KEY, societe_id integer NOT NULL REFERENCES societes(id),
            nom varchar(150) NOT NULL, poste varchar(150), salaire_brut double precision NOT NULL,
            situation_familiale varchar(20), nb_enfants integer, date_embauche date,
            actif boolean, created_at timestamp DEFAULT now())'''))
        c.execute(text("""INSERT INTO employes(societe_id,nom,poste,salaire_brut,
            situation_familiale,nb_enfants,date_embauche,actif)
            VALUES(:sid,'Salarié fictif historique','Comptable',4321.75,
                   'celiba',0,'2025-01-01',true)"""), {'sid': sid})


def photographie(engine):
    with engine.connect() as c:
        employes = [tuple(r) for r in c.execute(text('''SELECT id,societe_id,nom,poste,
            salaire_brut,situation_familiale,nb_enfants,date_embauche,actif,created_at
            FROM employes ORDER BY id'''))]
        ecritures = [tuple(r) for r in c.execute(text('SELECT * FROM ecritures ORDER BY id'))]
        lignes = [tuple(r) for r in c.execute(text('SELECT * FROM lignes_ecriture ORDER BY id'))]
        return employes, ecritures, lignes


@pytest.mark.parametrize('role_present', [False, True])
def test_ancienne_table_sans_cle_composite_reproduction_et_reprise(role_present):
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        engine = create_engine(cible['url'])
        try:
            if role_present:
                with engine.begin() as c:
                    c.execute(text('CREATE ROLE hisabpro NOLOGIN'))
            ancienne_base(engine)
            avant = photographie(engine)
            with pytest.raises(ProgrammingError) as erreur:
                models.Base.metadata.create_all(engine)
            assert erreur.value.orig.pgcode == '42830'
            for _ in range(2):
                initialiser_schema_developpement(engine, models.Base.metadata)
                assert photographie(engine) == avant
            with engine.connect() as c:
                assert c.scalar(text("SELECT count(*) FROM employes WHERE type_contrat IS NULL AND personnes_charge_ir IS NULL")) == 1
                assert c.scalar(text("SELECT count(*) FROM pg_constraint WHERE conname='uq_employes_id_societe' AND conrelid='employes'::regclass")) == 1
                assert c.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgrelid='grh_absence_evenements'::regclass AND NOT tgisinternal")) == 2
                assert c.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgrelid='paie_referentiel_versions'::regclass AND NOT tgisinternal")) == 2
                assert c.scalar(text('SELECT count(*) FROM ecritures WHERE est_validee')) == 1
        finally:
            engine.dispose()
    assert not cible['directory'].exists()


def test_base_vierge_et_absences_existantes_sans_cle_composite():
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        engine = create_engine(cible['url'])
        try:
            initialiser_schema_developpement(engine, models.Base.metadata)
            with engine.begin() as c:
                # Simuler uniquement dans ce cluster un schéma partiellement migré.
                c.execute(text('DROP TABLE grh_absence_evenements'))
                c.execute(text('ALTER TABLE grh_absences DROP CONSTRAINT uq_grh_absences_id_societe'))
            initialiser_schema_developpement(engine, models.Base.metadata)
            with engine.connect() as c:
                assert c.scalar(text("SELECT count(*) FROM pg_constraint WHERE conname='uq_grh_absences_id_societe' AND conrelid='grh_absences'::regclass")) == 1
                assert c.scalar(text('SELECT count(*) FROM employes')) == 0
                assert c.scalar(text('SELECT count(*) FROM ecritures')) == 0
        finally:
            engine.dispose()


def test_import_main_reel_et_http_sur_ancienne_base():
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        engine = create_engine(cible['url'])
        try:
            ancienne_base(engine)
            avant = photographie(engine)
            env = os.environ.copy()
            env.update(DATABASE_URL=cible['url'], PYTHON_DOTENV_DISABLED='1',
                       HISABPRO_CREATE_TABLES='1', APP_ENV='test',
                       SECRET_KEY='secret-synthetique-startup-' + cible['nonce'])
            code = """import main
from fastapi.testclient import TestClient
with TestClient(main.app) as client:
    r=client.get('/api/health')
    assert r.status_code==200 and r.json()['status']=='ok',r.text
print('MAIN_HTTP_OK')
"""
            resultat = subprocess.run([sys.executable, '-X', 'utf8', '-c', code],
                cwd=BACK, env=env, capture_output=True, text=True, encoding='utf-8', timeout=45)
            assert resultat.returncode == 0, resultat.stderr[-6000:]
            assert 'MAIN_HTTP_OK' in resultat.stdout
            assert photographie(engine) == avant
            with engine.connect() as c:
                assert c.scalar(text("SELECT count(*) FROM pg_trigger WHERE tgrelid='paie_referentiel_versions'::regclass AND NOT tgisinternal")) == 2
        finally:
            engine.dispose()


def test_referentiel_protege_au_demarrage_et_version_conservee_au_rejeu():
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        engine = create_engine(cible['url'])
        try:
            initialiser_schema_developpement(engine, models.Base.metadata)
            with Session(engine) as db:
                societe = models.Societe(raison_sociale='Laboratoire démarrage paie082')
                db.add(societe)
                db.flush()
                user = models.Utilisateur(societe_id=societe.id, nom='Admin fictif',
                    email='startup082@example.com', hashed_password='NON-CONNECTABLE', role='admin')
                db.add(user)
                db.flush()
                version = models.PaieReferentielVersion(societe_id=societe.id,
                    annee=2026, version=1, empreinte='a' * 64,
                    parametres={'bareme_ir': [], 'taux_cotisations': [], 'deductions_ir': []},
                    sources=[], qualification='non_verifie', created_by=user.id)
                db.add(version)
                db.commit()
            with engine.connect() as c:
                avant = c.execute(text('SELECT * FROM paie_referentiel_versions')).one()
                taux_avant = c.execute(text('SELECT * FROM taux_cotisations ORDER BY id')).all()
            for _ in range(2):
                initialiser_schema_developpement(engine, models.Base.metadata)
            for commande in (
                    "UPDATE paie_referentiel_versions SET commentaire='altération'",
                    'DELETE FROM paie_referentiel_versions',
                    'TRUNCATE paie_referentiel_versions'):
                with engine.connect() as c:
                    with pytest.raises(DBAPIError) as erreur:
                        c.execute(text(commande))
                    assert erreur.value.orig.pgcode == '23514'
                    c.rollback()
            with engine.connect() as c:
                assert c.execute(text('SELECT * FROM paie_referentiel_versions')).one() == avant
                assert c.execute(text('SELECT * FROM taux_cotisations ORDER BY id')).all() == taux_avant
                assert c.scalar(text('SELECT count(*) FROM employes')) == 0
                assert c.scalar(text('SELECT count(*) FROM ecritures')) == 0
        finally:
            engine.dispose()
    assert not cible['directory'].exists()
