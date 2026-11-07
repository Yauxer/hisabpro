"""07B.3 + 07C.2 — tests PostgreSQL réels de la numérotation définitive.

Depuis 07C.2, les brouillons ne sont plus numérotés à l'INSERT. Les tests de
concurrence portent donc sur la VALIDATION, qui est désormais l'événement
réservant le numéro définitif.

Le banc d'essai crée un schéma PostgreSQL jetable et ne touche jamais aux
écritures métier HisabPro.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse
import os
import re
import uuid

import pytest


def _project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "hisabpro-backend").is_dir():
            return candidate
        if candidate.name == "hisabpro-backend":
            return candidate.parent
    raise RuntimeError("Racine HisabPro introuvable depuis le dossier Test.")


ROOT = _project_root()
BACKEND = ROOT / "hisabpro-backend"


def _read_database_url() -> str | None:
    for key in ("HISABPRO_TEST_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key)
        if value:
            return value.strip()
    env_file = BACKEND / ".env"
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DATABASE_URL":
                return value.strip().strip('"').strip("'")
    return None


def _driver():
    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError:
        pytest.skip("psycopg2 absent : pip install psycopg2-binary")
    return psycopg2, sql


def _safe_local_database_url() -> str:
    url = _read_database_url()
    if not url:
        pytest.skip("DATABASE_URL introuvable (.env backend ou variable d'environnement).")
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in {"localhost", "127.0.0.1", "::1", ""} and os.getenv("HISABPRO_ALLOW_REMOTE_PG_TESTS") != "1":
        pytest.skip("Les tests PostgreSQL destructifs temporaires sont limités à une base locale par défaut.")
    return url


@contextmanager
def _connection(autocommit: bool = False):
    psycopg2, _ = _driver()
    conn = psycopg2.connect(_safe_local_database_url())
    conn.autocommit = autocommit
    try:
        yield conn
    finally:
        conn.close()


def _function_def(cur, signature: str) -> str:
    cur.execute("SELECT pg_get_functiondef(%s::regprocedure)", (signature,))
    row = cur.fetchone()
    if not row or not row[0]:
        pytest.fail(f"Fonction {signature} introuvable. Exécute 018_numero_ecriture_a_validation.sql.")
    return row[0]


def _clone(definition: str, function_name: str, schema: str) -> str:
    # Remplace uniquement la qualification du nom de fonction créé.
    definition = re.sub(
        rf"(CREATE\s+OR\s+REPLACE\s+FUNCTION\s+)(?:public\.)?{re.escape(function_name)}",
        rf'\1"{schema}".{function_name}', definition, count=1, flags=re.IGNORECASE,
    )
    # Les fonctions SECURITY DEFINER utilisent public, pg_temp en production.
    definition = re.sub(
        r"SET\s+search_path\s+(?:=|TO)\s+(?:'public'|public)\s*,\s*(?:'pg_temp'|pg_temp)",
        f'SET search_path = "{schema}", pg_temp', definition, flags=re.IGNORECASE,
    )
    return definition


@pytest.fixture(scope="module")
def pg_lab():
    _, sql = _driver()
    schema = f"hisabpro_07c2_test_{uuid.uuid4().hex[:10]}"

    with _connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            reserve = _function_def(cur, "public.hisabpro_reserver_numero_ecriture(integer,integer,text,date)")
            insert_fn = _function_def(cur, "public.hisabpro_attribuer_numero_ecriture()")
            validate_fn = _function_def(cur, "public.hisabpro_numero_a_la_validation()")
            protect_fn = _function_def(cur, "public.hisabpro_proteger_numero_ecriture()")
            delete_fn = _function_def(cur, "public.hisabpro_interdire_suppression_numero()")

            cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            cur.execute(sql.SQL("""
                CREATE TABLE {}.ecriture_sequences (
                    societe_id INTEGER NOT NULL,
                    exercice INTEGER NOT NULL,
                    journal VARCHAR(10) NOT NULL,
                    dernier_numero INTEGER NOT NULL DEFAULT 0,
                    derniere_date DATE,
                    PRIMARY KEY (societe_id, exercice, journal),
                    CHECK (dernier_numero >= 0)
                )
            """).format(sql.Identifier(schema)))
            cur.execute(sql.SQL("""
                CREATE TABLE {}.ecritures (
                    id BIGSERIAL PRIMARY KEY,
                    societe_id INTEGER NOT NULL,
                    date DATE NOT NULL,
                    journal VARCHAR(10) NOT NULL,
                    libelle VARCHAR(300) NOT NULL,
                    numero_ecriture VARCHAR(40),
                    reference VARCHAR(100),
                    date_piece DATE,
                    exercice INTEGER NOT NULL,
                    est_validee BOOLEAN NOT NULL DEFAULT FALSE
                )
            """).format(sql.Identifier(schema)))
            cur.execute(sql.SQL("CREATE UNIQUE INDEX ux_test_num ON {}.ecritures (societe_id, numero_ecriture)").format(sql.Identifier(schema)))

            for definition, name in [
                (reserve, "hisabpro_reserver_numero_ecriture"),
                (insert_fn, "hisabpro_attribuer_numero_ecriture"),
                (validate_fn, "hisabpro_numero_a_la_validation"),
                (protect_fn, "hisabpro_proteger_numero_ecriture"),
                (delete_fn, "hisabpro_interdire_suppression_numero"),
            ]:
                cur.execute(_clone(definition, name, schema))

            cur.execute(sql.SQL("""
                CREATE TRIGGER trg_00_insert BEFORE INSERT ON {}.ecritures
                FOR EACH ROW EXECUTE FUNCTION {}.hisabpro_attribuer_numero_ecriture()
            """).format(sql.Identifier(schema), sql.Identifier(schema)))
            cur.execute(sql.SQL("""
                CREATE TRIGGER trg_00_validation BEFORE UPDATE OF est_validee ON {}.ecritures
                FOR EACH ROW EXECUTE FUNCTION {}.hisabpro_numero_a_la_validation()
            """).format(sql.Identifier(schema), sql.Identifier(schema)))
            cur.execute(sql.SQL("""
                CREATE TRIGGER trg_protect BEFORE UPDATE OF numero_ecriture, societe_id, exercice, journal, date ON {}.ecritures
                FOR EACH ROW EXECUTE FUNCTION {}.hisabpro_proteger_numero_ecriture()
            """).format(sql.Identifier(schema), sql.Identifier(schema)))
            cur.execute(sql.SQL("""
                CREATE TRIGGER trg_delete BEFORE DELETE ON {}.ecritures
                FOR EACH ROW EXECUTE FUNCTION {}.hisabpro_interdire_suppression_numero()
            """).format(sql.Identifier(schema), sql.Identifier(schema)))
    try:
        yield schema
    finally:
        with _connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


def _draft(schema: str, societe: int, exercice: int, journal: str, day: int = 2) -> int:
    _, sql = _driver()
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                INSERT INTO {}.ecritures (societe_id, date, journal, libelle, exercice)
                VALUES (%s, %s, %s, 'test', %s)
                RETURNING id, numero_ecriture
            """).format(sql.Identifier(schema)), (societe, f"{exercice}-01-{day:02d}", journal, exercice))
            eid, numero = cur.fetchone()
            assert numero is None
        conn.commit()
    return eid


def _validate(schema: str, eid: int) -> str:
    _, sql = _driver()
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                UPDATE {}.ecritures SET est_validee = TRUE WHERE id = %s
                RETURNING numero_ecriture
            """).format(sql.Identifier(schema)), (eid,))
            numero = cur.fetchone()[0]
        conn.commit()
    return numero


def _suffix(numero: str) -> int:
    return int(numero.rsplit("-", 1)[1])


def test_018_est_installe_en_production(pg_lab):
    del pg_lab
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT is_nullable FROM information_schema.columns
                 WHERE table_schema='public' AND table_name='ecritures' AND column_name='numero_ecriture'
            """)
            assert cur.fetchone()[0] == "YES"
            cur.execute("""
                SELECT 1 FROM information_schema.columns
                 WHERE table_schema='public' AND table_name='ecriture_sequences' AND column_name='derniere_date'
            """)
            assert cur.fetchone() is not None


def test_brouillon_ne_consomme_aucun_numero_et_peut_etre_supprime(pg_lab):
    _, sql = _driver()
    eid1 = _draft(pg_lab, 81001, 2091, "BQ")
    eid2 = _draft(pg_lab, 81001, 2091, "BQ")
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("DELETE FROM {}.ecritures WHERE id=%s").format(sql.Identifier(pg_lab)), (eid1,))
        conn.commit()
    assert _validate(pg_lab, eid2) == "BQ-2091-0001"


def test_brouillon_peut_changer_journal_et_date_avant_validation(pg_lab):
    _, sql = _driver()
    eid = _draft(pg_lab, 82001, 2092, "AC")
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                UPDATE {}.ecritures SET journal='VT', date='2092-02-03' WHERE id=%s
                RETURNING numero_ecriture
            """).format(sql.Identifier(pg_lab)), (eid,))
            assert cur.fetchone()[0] is None
        conn.commit()
    assert _validate(pg_lab, eid) == "VT-2092-0001"


def test_concurrence_de_validation_sans_doublon(pg_lab):
    ids = [_draft(pg_lab, 83001, 2093, "OD", day=2) for _ in range(24)]
    with ThreadPoolExecutor(max_workers=24) as pool:
        numeros = list(pool.map(lambda eid: _validate(pg_lab, eid), ids))
    assert len(set(numeros)) == 24
    assert sorted(_suffix(n) for n in numeros) == list(range(1, 25))


def test_sequences_independantes_par_scope(pg_lab):
    assert _validate(pg_lab, _draft(pg_lab, 84001, 2094, "AC")) == "AC-2094-0001"
    assert _validate(pg_lab, _draft(pg_lab, 84001, 2094, "VT")) == "VT-2094-0001"
    assert _validate(pg_lab, _draft(pg_lab, 84001, 2095, "AC")) == "AC-2095-0001"
    assert _validate(pg_lab, _draft(pg_lab, 84002, 2094, "AC")) == "AC-2094-0001"


def test_rollback_de_validation_ne_consomme_pas_numero(pg_lab):
    _, sql = _driver()
    eid = _draft(pg_lab, 85001, 2095, "CA")
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("UPDATE {}.ecritures SET est_validee=TRUE WHERE id=%s RETURNING numero_ecriture").format(sql.Identifier(pg_lab)), (eid,))
            assert cur.fetchone()[0] == "CA-2095-0001"
        conn.rollback()
    assert _validate(pg_lab, eid) == "CA-2095-0001"


def test_suppression_numero_definitif_est_interdite(pg_lab):
    psycopg2, sql = _driver()
    eid = _draft(pg_lab, 86001, 2096, "BQ")
    numero = _validate(pg_lab, eid)
    with _connection() as conn:
        with conn.cursor() as cur:
            with pytest.raises(psycopg2.Error) as exc:
                cur.execute(sql.SQL("DELETE FROM {}.ecritures WHERE id=%s").format(sql.Identifier(pg_lab)), (eid,))
            assert exc.value.pgcode == "23514"
        conn.rollback()
    assert numero == "BQ-2096-0001"


def test_frontiere_9999_10000_sans_troncature(pg_lab):
    _, sql = _driver()
    with _connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                INSERT INTO {}.ecriture_sequences
                    (societe_id, exercice, journal, dernier_numero, derniere_date)
                VALUES (87001, 2097, 'OD', 9998, '2097-01-01')
            """).format(sql.Identifier(pg_lab)))
        conn.commit()
    assert _validate(pg_lab, _draft(pg_lab, 87001, 2097, "OD")) == "OD-2097-9999"
    assert _validate(pg_lab, _draft(pg_lab, 87001, 2097, "OD")) == "OD-2097-10000"


def test_numero_scope_et_date_sont_immuables_apres_validation(pg_lab):
    psycopg2, sql = _driver()
    eid = _draft(pg_lab, 88001, 2098, "AC")
    numero = _validate(pg_lab, eid)
    mutations = [
        ("numero_ecriture", "AC-2098-9999"),
        ("journal", "VT"),
        ("exercice", 2099),
        ("societe_id", 88002),
        ("date", "2098-01-03"),
    ]
    for column, value in mutations:
        with _connection() as conn:
            with conn.cursor() as cur:
                with pytest.raises(psycopg2.Error) as exc:
                    cur.execute(
                        sql.SQL("UPDATE {}.ecritures SET {}=%s WHERE id=%s").format(sql.Identifier(pg_lab), sql.Identifier(column)),
                        (value, eid),
                    )
                assert exc.value.pgcode == "23514"
            conn.rollback()
    assert numero == "AC-2098-0001"


def test_validation_antidatee_est_refusee(pg_lab):
    psycopg2 = _driver()[0]
    recent = _draft(pg_lab, 89001, 2099, "VT", day=10)
    ancien = _draft(pg_lab, 89001, 2099, "VT", day=5)
    assert _validate(pg_lab, recent) == "VT-2099-0001"
    with pytest.raises(psycopg2.Error) as exc:
        _validate(pg_lab, ancien)
    assert exc.value.pgcode == "23514"
