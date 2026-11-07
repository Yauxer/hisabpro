"""Vrai rôle applicatif non propriétaire sur PostgreSQL éphémère marqué.

Cette configuration ciblée de recette ne constitue pas un manifeste exhaustif
d'installation, ni un audit des droits d'une base existante.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from auth import get_current_user, requiert_ecriture
from database import get_db
from postgres_isole import cluster_isole, verifier_cible_isolee
from routers import ecritures
from services.exercices_service import ensure_exercice
from test_session132_operations_postgres import MIGRATIONS, reponse_ok

ROOT = Path(__file__).resolve().parents[1]
TABLES_METIER = ("societes", "utilisateurs", "exercices_comptables", "periodes_comptables",
                 "comptes_societe", "ecritures", "lignes_ecriture", "tiers")
TABLES_LECTURE = ("clotures_exercice", "plan_comptable_cgnc_reference", "ecriture_justificatifs")
TABLES_PROTEGEES = ("audit_ecritures", "audit_actions", "audit_periodes_comptables",
                    "liasses_fiscales_archives", "liasse_balances_preparation")


@pytest.fixture(scope="module")
def runtime():
    with cluster_isole() as cluster:
        def garde():
            assert verifier_cible_isolee(cluster["url"], cluster["directory"], cluster["nonce"])
        garde()
        owner = create_engine(cluster["url"])
        app_engine = None
        try:
            garde()
            with owner.begin() as connection:
                connection.execute(text("CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS"))
            garde()
            models.Base.metadata.create_all(owner)
            raw = owner.raw_connection()
            try:
                raw.autocommit = True
                with raw.cursor() as cursor:
                    for migration in [*MIGRATIONS, "036_production_hardening.sql",
                                      "027_liasse_fiscale_archive.sql", "071_liasse_balances_preparation.sql"]:
                        garde()
                        cursor.execute((ROOT / "hisabpro-backend" / migration).read_text(encoding="utf-8"))
            finally:
                raw.close()
            garde()
            with Session(owner) as db:
                societe = models.Societe(raison_sociale="Runtime fictif isolé")
                db.add(societe)
                db.flush()
                utilisateur = models.Utilisateur(societe_id=societe.id, nom="Administrateur isolé",
                    email="runtime@example.invalid", hashed_password="non_utilise", role="admin")
                db.add(utilisateur)
                exercice = ensure_exercice(db, societe.id, 2025)
                for numero, libelle in [("1111", "Capital"), ("5141", "Banque")]:
                    if db.get(models.CompteCGNCReference, numero) is None:
                        db.add(models.CompteCGNCReference(numero=numero, libelle=libelle, classe=int(numero[0]), type_compte="SP"))
                    if db.query(models.CompteSociete).filter_by(societe_id=societe.id, numero=numero).first() is None:
                        db.add(models.CompteSociete(societe_id=societe.id, numero=numero, libelle=libelle, classe=int(numero[0])))
                db.commit()
                user = {"societe_id": societe.id, "id": utilisateur.id, "role": "admin",
                        "nom": utilisateur.nom, "email": utilisateur.email}
                exercice_id = exercice.id
            garde()
            with owner.begin() as connection:
                # Liste fermée : aucune permission globale ni permission sur
                # les archives/audits ne passe par un GRANT ALL/ALL TABLES.
                connection.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
                connection.execute(text("GRANT USAGE ON SCHEMA public TO hisabpro"))
                for table in TABLES_METIER:
                    connection.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON public.{table} TO hisabpro"))
                    sequence = connection.scalar(text("SELECT pg_get_serial_sequence(:table, 'id')"), {"table": table})
                    if sequence:
                        assert sequence.startswith("public.") and sequence.replace(".", "").replace("_", "").isalnum()
                        connection.execute(text(f"GRANT USAGE, SELECT ON SEQUENCE {sequence} TO hisabpro"))
                for table in TABLES_LECTURE:
                    connection.execute(text(f"GRANT SELECT ON public.{table} TO hisabpro"))
            garde()
            owner_url = make_url(cluster["url"])
            runtime_url = owner_url.set(username="hisabpro")
            assert runtime_url.set(username=owner_url.username) == owner_url
            app_engine = create_engine(runtime_url, connect_args={"options": "-c statement_timeout=10000 -c lock_timeout=5000"})
            app = FastAPI()
            app.include_router(ecritures.router)
            def db_runtime():
                garde()
                with Session(app_engine) as db:
                    assert db.scalar(text("SELECT current_user")) == "hisabpro"
                    yield db
            app.dependency_overrides[get_db] = db_runtime
            app.dependency_overrides[get_current_user] = lambda: user
            app.dependency_overrides[requiert_ecriture] = lambda: user
            with TestClient(app) as client:
                yield {"engine": app_engine, "client": client, "user": user,
                       "exercice_id": exercice_id, "garde": garde}
        finally:
            if app_engine is not None:
                app_engine.dispose()
            owner.dispose()
    assert not cluster["directory"].exists()


def test_runtime_est_connexion_login_reelle_non_privilegiee_non_proprietaire(runtime):
    with runtime["engine"].connect() as connection:
        assert connection.execute(text("SELECT current_user,session_user")).one() == ("hisabpro", "hisabpro")
        role = connection.execute(text("SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls "
                                       "FROM pg_roles WHERE rolname=current_user")).one()
        assert role == (True, False, False, False, False, False)
        assert not connection.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
        assert not connection.scalar(text("SELECT has_schema_privilege(current_user,'public','CREATE')"))
        assert connection.scalar(text("SELECT count(*) FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner "
                                      "WHERE r.rolname=current_user AND c.relnamespace='public'::regnamespace")) == 0
        assert connection.scalar(text("SELECT count(*) FROM pg_proc p JOIN pg_roles r ON r.oid=p.proowner "
                                      "WHERE r.rolname=current_user AND p.pronamespace='public'::regnamespace")) == 0
        for table in TABLES_PROTEGEES:
            for permission in ("UPDATE", "DELETE", "TRUNCATE"):
                assert not connection.scalar(text("SELECT has_table_privilege(current_user,:table,:permission)"),
                                             {"table": table, "permission": permission})


@pytest.fixture(scope="module")
def ecriture_validee(runtime):
    client = runtime["client"]
    creation = reponse_ok(client.post("/api/ecritures", json={"date": "2025-05-01", "journal": "OD",
        "reference": "RUNTIME-01", "libelle": "Apport synthétique isolé", "lignes": [
            {"compte": "5141", "debit": 1000}, {"compte": "1111", "credit": 1000}]}), 201)
    assert not creation["est_validee"] and creation["numero_ecriture"] is None
    validation = reponse_ok(client.post(f"/api/ecritures/{creation['id']}/valider"))
    assert validation["numero_ecriture"] == "OD-2025-0001"
    return creation


def test_api_runtime_cree_valide_audite_sans_droits_directs_sur_audit(runtime, ecriture_validee):
    creation = ecriture_validee
    with runtime["engine"].begin() as connection:
        events = connection.execute(text("SELECT action,acteur_id FROM audit_ecritures WHERE ecriture_id=:id"),
                                    {"id": creation["id"]}).all()
        assert len(events) >= 4 and ("validation", runtime["user"]["id"]) in events
        assert connection.scalar(text("SELECT dernier_numero FROM ecriture_sequences WHERE societe_id=:sid"),
                                 {"sid": runtime["user"]["societe_id"]}) == 1
        connection.execute(text("SELECT hisabpro_journaliser_action(:sid,:uid,'admin','POST',"
            "'/recette/runtime',200,true,'127.0.0.1','runtime-isole')"),
            {"sid": runtime["user"]["societe_id"], "uid": runtime["user"]["id"]})
        assert connection.scalar(text("SELECT count(*) FROM audit_actions WHERE request_id='runtime-isole'")) == 1
        connection.execute(text("INSERT INTO liasses_fiscales_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) "
            "VALUES(:sid,2025,1,'{}',:sha)"), {"sid": runtime["user"]["societe_id"], "sha": "a" * 64})
        connection.execute(text("INSERT INTO liasse_balances_preparation(societe_id,exercice,exercice_id,version,contenu,empreinte_sha256) "
            "VALUES(:sid,2025,:eid,1,'{}',:sha)"), {"sid": runtime["user"]["societe_id"], "eid": runtime["exercice_id"], "sha": "b" * 64})


def test_runtime_changement_periode_audite_par_trigger_definer(runtime):
    with runtime["engine"].begin() as connection:
        connection.execute(text("SELECT set_config('hisabpro.audit_actor_id',:acteur,true)"),
                           {"acteur": str(runtime["user"]["id"])})
        for statut in ("fermee", "ouverte"):
            connection.execute(text("UPDATE periodes_comptables SET statut=:statut WHERE exercice_id=:eid AND numero=10"),
                               {"statut": statut, "eid": runtime["exercice_id"]})
        traces = connection.execute(text("SELECT ancien_statut,nouveau_statut,acteur_id FROM audit_periodes_comptables "
                                         "WHERE exercice_id=:eid AND numero=10 ORDER BY id"),
                                    {"eid": runtime["exercice_id"]}).all()
        assert traces == [("ouverte", "fermee", runtime["user"]["id"]),
                          ("fermee", "ouverte", runtime["user"]["id"])]


INTERDITS = [(f"{operation} {table}", sql) for table in TABLES_PROTEGEES for operation, sql in [
    ("UPDATE", f"UPDATE {table} SET id=id"), ("DELETE", f"DELETE FROM {table}"),
    ("TRUNCATE", f"TRUNCATE {table}")]] + [
    ("INSERT audit écritures", "INSERT INTO audit_ecritures(societe_id,table_cible,action) VALUES(1,'test','test')"),
    ("INSERT audit actions", "INSERT INTO audit_actions(methode,chemin,statut_http) VALUES('POST','/test',200)"),
    ("INSERT audit périodes", "INSERT INTO audit_periodes_comptables(exercice_id,periode_id,numero,ancien_statut,nouveau_statut) VALUES(1,1,1,'ouverte','fermee')"),
    ("DDL table", "CREATE TABLE public.contournement_runtime(id integer)"),
    ("DDL désactivation trigger", "ALTER TABLE ecritures DISABLE TRIGGER ALL"),
    ("DDL suppression archive", "DROP TABLE liasses_fiscales_archives"),
    ("DDL remplacement audit", "CREATE OR REPLACE FUNCTION hisabpro_audit_actions_append_only() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END $$"),
    ("Droits compteurs", "UPDATE ecriture_sequences SET dernier_numero=0"),
    ("Droits rôle owner", "SET ROLE hisabpro_recette"),
]


@pytest.mark.parametrize("description,sql", INTERDITS, ids=[r[0] for r in INTERDITS])
def test_runtime_refuse_sql_direct_audit_archives_et_contournements(runtime, description, sql):
    runtime["garde"]()
    with runtime["engine"].connect() as connection:
        with pytest.raises(DBAPIError) as erreur:
            connection.execute(text(sql))
            connection.commit()
        assert erreur.value.orig.pgcode == "42501", (description, erreur.value)
        connection.rollback()


@pytest.mark.parametrize("sql", ["UPDATE ecritures SET libelle='interdit' WHERE reference='RUNTIME-01'",
                                "DELETE FROM ecritures WHERE reference='RUNTIME-01'",
                                "UPDATE lignes_ecriture SET debit=2000 WHERE debit=1000"])
def test_runtime_droits_metier_ne_contournent_pas_ecriture_definitive(runtime, ecriture_validee, sql):
    runtime["garde"]()
    with runtime["engine"].connect() as connection:
        with pytest.raises(DBAPIError) as erreur:
            connection.execute(text(sql))
            connection.commit()
        assert erreur.value.orig.pgcode == "23514"
        connection.rollback()
