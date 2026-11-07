"""Migration073 : anciennes ACL et TRUNCATE, uniquement en PG éphémère."""
from contextlib import contextmanager
from datetime import datetime
import hashlib
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from postgres_isole import cluster_isole, verifier_cible_isolee

BACK = Path(__file__).resolve().parents[1] / "hisabpro-backend"
ARCHIVE = "liasses_fiscales_archives"


@contextmanager
def cible_archive(*, role_present=True):
    with cluster_isole() as cluster:
        def garde():
            assert verifier_cible_isolee(cluster["url"], cluster["directory"], cluster["nonce"])
        garde()
        owner = create_engine(cluster["url"])
        runtime = None
        def migration(nom):
            garde()
            raw = owner.raw_connection()
            try:
                raw.autocommit = True
                with raw.cursor() as cursor:
                    cursor.execute((BACK / nom).read_text(encoding="utf-8"))
            finally:
                raw.close()
        try:
            if role_present:
                garde()
                with owner.begin() as connection:
                    connection.execute(text("CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB "
                        "NOCREATEROLE NOREPLICATION NOBYPASSRLS"))
                    connection.execute(text("GRANT USAGE ON SCHEMA public TO hisabpro"))
            garde()
            models.Base.metadata.create_all(owner)
            migration("027_liasse_fiscale_archive.sql")
            garde()
            with Session(owner) as db:
                societe = models.Societe(raison_sociale="Archives fictives ACL isolées")
                db.add(societe)
                db.flush()
                sid = societe.id
                for version in (1, 2):
                    contenu = '{"recette_synthetique":true,"version":' + str(version) + '}'
                    db.add(models.LiasseFiscaleArchive(societe_id=sid, exercice=2025,
                        version=version, contenu_json=contenu,
                        empreinte_sha256=hashlib.sha256(contenu.encode()).hexdigest(),
                        date_finalisation=datetime(2026, 1, version, 12, 30)))
                db.commit()
            if role_present:
                owner_url = make_url(cluster["url"])
                runtime_url = owner_url.set(username="hisabpro")
                assert runtime_url.set(username=owner_url.username) == owner_url
                runtime = create_engine(runtime_url)
                with runtime.connect() as connection:
                    assert connection.execute(text("SELECT current_user,session_user")).one() == ("hisabpro", "hisabpro")
                    assert not connection.scalar(text("SELECT rolsuper FROM pg_roles WHERE rolname=current_user"))
                    assert not connection.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
            yield {"owner": owner, "runtime": runtime, "garde": garde, "migration": migration, "sid": sid}
        finally:
            if runtime is not None:
                runtime.dispose()
            owner.dispose()
    assert not cluster["directory"].exists()


def archives(engine):
    with engine.connect() as connection:
        return connection.execute(text("SELECT id,societe_id,exercice,version,contenu_json,empreinte_sha256,"
                                       "date_finalisation,finalisee_par FROM liasses_fiscales_archives ORDER BY id")).all()


def privilege(engine, permission):
    with engine.connect() as connection:
        return connection.scalar(text("SELECT has_table_privilege(current_user,:table,:permission)"),
                                 {"table": ARCHIVE, "permission": permission})


def refuser(engine, commande, sqlstate):
    with engine.connect() as connection:
        with pytest.raises(DBAPIError) as erreur:
            connection.execute(text(commande))
            connection.commit()
        assert erreur.value.orig.pgcode == sqlstate, erreur.value
        connection.rollback()


@pytest.mark.parametrize("origine", ["direct", "public", "groupe"])
def test_acl_historiques_TRUNCATE_reproduites_puis_bloquees_par073(origine):
    with cible_archive() as cible:
        owner, runtime = cible["owner"], cible["runtime"]
        initial = archives(owner)
        assert len(initial) == 2
        cible["garde"]()
        with owner.begin() as connection:
            if origine == "groupe":
                connection.execute(text("CREATE ROLE anciennes_archives NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE"))
                connection.execute(text("GRANT anciennes_archives TO hisabpro"))
            destinataire = {"direct": "hisabpro", "public": "PUBLIC", "groupe": "anciennes_archives"}[origine]
            connection.execute(text(f"GRANT UPDATE, DELETE, TRUNCATE ON {ARCHIVE} TO {destinataire}"))
        # Le rejeu historique ne corrige pas ces droits : démontrer le défaut
        # avant le correctif, puis rollback sans perdre les archives fictives.
        cible["migration"]("027_liasse_fiscale_archive.sql")
        assert privilege(runtime, "TRUNCATE") is True
        cible["garde"]()
        with runtime.connect() as connection:
            connection.execute(text(f"TRUNCATE {ARCHIVE}"))
            assert connection.scalar(text(f"SELECT count(*) FROM {ARCHIVE}")) == 0
            connection.rollback()
        assert archives(owner) == initial
        for _ in range(2):
            cible["migration"]("073_archives_fiscales_permissions.sql")
            assert archives(owner) == initial
        # Le REVOKE direct ne peut supprimer un droit reçu d'un groupe : le
        # trigger de statement doit aussi bloquer ce cas, code métier P0001.
        garde_heritee = origine == "groupe"
        for permission in ("UPDATE", "DELETE", "TRUNCATE"):
            assert privilege(runtime, permission) is garde_heritee
        for commande in (f"TRUNCATE {ARCHIVE}", f"UPDATE {ARCHIVE} SET contenu_json='interdit'",
                         f"DELETE FROM {ARCHIVE}"):
            cible["garde"]()
            refuser(runtime, commande, "P0001" if garde_heritee else "42501")
            assert archives(owner) == initial
        assert privilege(runtime, "SELECT") and privilege(runtime, "INSERT")
        cible["garde"]()
        contenu = '{"recette_synthetique":true,"version":3}'
        with runtime.begin() as connection:
            connection.execute(text("INSERT INTO liasses_fiscales_archives(societe_id,exercice,version,contenu_json,empreinte_sha256) "
                "VALUES(:sid,2025,3,:contenu,:sha)"), {"sid": cible["sid"], "contenu": contenu,
                "sha": hashlib.sha256(contenu.encode()).hexdigest()})
        final = archives(owner)
        assert final[:2] == initial and len(final) == 3


def test073_refuse_TRUNCATE_owner_sans_alteration_trigger_et_preserve_archives():
    with cible_archive() as cible:
        initial = archives(cible["owner"])
        cible["migration"]("073_archives_fiscales_permissions.sql")
        assert privilege(cible["owner"], "TRUNCATE")
        cible["garde"]()
        refuser(cible["owner"], f"TRUNCATE {ARCHIVE}", "P0001")
        assert archives(cible["owner"]) == initial
        with cible["owner"].connect() as connection:
            definition = connection.scalar(text("SELECT pg_get_triggerdef(oid) FROM pg_trigger "
                "WHERE tgname='trg_hisabpro_liasse_archive_truncate' AND tgenabled='O'"))
            assert "BEFORE TRUNCATE" in definition and "FOR EACH STATEMENT" in definition


def test073_rejouable_sans_role_applicatif_et_sans_modification_archives():
    with cible_archive(role_present=False) as cible:
        initial = archives(cible["owner"])
        for _ in range(2):
            cible["migration"]("073_archives_fiscales_permissions.sql")
            assert archives(cible["owner"]) == initial
        with cible["owner"].connect() as connection:
            assert not connection.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
        cible["garde"]()
        refuser(cible["owner"], f"TRUNCATE {ARCHIVE}", "P0001")
        assert archives(cible["owner"]) == initial
