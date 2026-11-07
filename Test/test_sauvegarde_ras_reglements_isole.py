"""Sauvegarde/restauration083 : deux clusters nonce, API réelle et traces exactes."""
from contextlib import closing
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_acompte_fournisseur_isole import ok
from test_ras_capture_reglement_postgres import appliquer, preparer, paiement, payload, SQL

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops.postgres_sauvegarde import sauvegarder, restaurer_isole

TABLES = ('societes', 'utilisateurs', 'utilisateurs_societes', 'tiers',
    'factures', 'lignes_facture', 'reglements', 'ecritures', 'lignes_ecriture',
    'ras_reglement_captures', 'ras_reglement_annulations')


def instantane(engine):
    with engine.connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM public.{t} t ORDER BY id')).scalars().all()
            for t in TABLES}


def refuse(engine, sql, code):
    with engine.connect() as db:
        with pytest.raises(DBAPIError) as erreur:
            db.execute(text(sql))
        assert erreur.value.orig.pgcode == code
        db.rollback()


def rejouer083(engine):
    raw = engine.raw_connection()
    try:
        with raw.cursor() as cur:
            cur.execute(SQL.read_text(encoding='utf-8'))
        raw.commit()
    finally:
        raw.close()


def test_dump_restore_captures_annulation_ledger_et_acl_runtime(application):
    source = application['cluster']
    assert verifier_cible_isolee(source['url'], source['directory'], source['nonce'])
    assert 'ras_reglement_captures' not in models.Base.metadata.tables
    assert 'ras_reglement_annulations' not in models.Base.metadata.tables
    appliquer(application)
    with closing(client(application)[0]) as api:
        f = preparer(api, 'vente')
        compta = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        ok(api.post(f"/api/ecritures/{compta['ecriture_id']}/valider"))
        r1 = paiement(api, f, 400)
        ok(api.post(f"/api/ecritures/{r1['ecriture_id']}/valider"))
        c1 = ok(api.post(f"/api/reglements/{r1['id']}/ras", json=payload(30, 'vente')))
        ok(api.post(f"/api/ecritures/{c1['ecriture_id']}/valider"))
        r2 = paiement(api, f, 700)
        ok(api.post(f"/api/ecritures/{r2['ecriture_id']}/valider"))
        c2 = ok(api.post(f"/api/reglements/{r2['id']}/ras", json=payload(70, 'vente', 'CAPTURE-RESTORE-70')))
        ok(api.post(f"/api/ecritures/{c2['ecriture_id']}/valider"))
        assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant'] == 0
        annule = ok(api.post(f"/api/reglements/{r2['id']}/annuler", json={'motif': 'Erreur fictive sauvegarde'}))
        ok(api.post(f"/api/ecritures/{annule['ecriture_annulation_id']}/valider"))
        captures = ok(api.get(f"/api/reglements/{r2['id']}/ras"))['captures']
        inverse_id = captures[0]['ecriture_annulation_id']
        ok(api.post(f'/api/ecritures/{inverse_id}/valider'))
        situation = ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert situation['solde_restant'] == 770 and situation['montant_ras_impute'] == 30
    # Les clients capables de muter sont fermés avant le dump. Aucune autre
    # interaction n'est lancée avec cette application nonce pendant la fenêtre.
    avant = instantane(application['engine'])
    with application['engine'].connect() as db:
        sid = db.scalar(text('SELECT societe_id FROM factures WHERE id=:id'), {'id': f['id']})
        assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid'), {'sid':sid}) == 7
        assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid AND est_validee'), {'sid':sid}) == 7
        assert db.execute(text('SELECT sum(l.debit),sum(l.credit) FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid'), {'sid':sid}).one() == (3170,3170)
    with cluster_isole() as cible:
        def garde():
            for c in (source, cible):
                assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        garde()
        assert source['nonce'] != cible['nonce'] and source['url'] != cible['url']
        archive = sauvegarder(source['url'], source['directory']/'ras083.dump', source['bin'])
        assert archive.is_file() and archive.stat().st_size > 0
        garde()
        restaurer_isole(cible['url'], archive, cible['bin'], cible['directory'], cible['nonce'])
        restauree = create_engine(cible['url']); runtime = None
        try:
            assert instantane(restauree) == avant == instantane(application['engine'])
            with Session(restauree) as db:
                from routers.factures import _situation_paiement_facture
                from services.ras_reglement_service import captures_facture
                restored = _situation_paiement_facture(db, sid, db.get(models.Facture, f['id']))
                assert restored['solde_restant'] == 770 and restored['montant_ras_impute'] == 30
                traces = captures_facture(db, sid, f['id'])
                assert len(traces) == 2 and sum(c['annulation_id'] is not None for c in traces) == 1
                assert all(c['ecriture_est_validee'] for c in traces)
                assert next(c for c in traces if c['annulation_id'])['annulation_est_validee']
            with restauree.connect() as db:
                triggers = db.execute(text("SELECT tgname,tgenabled FROM pg_trigger WHERE NOT tgisinternal AND tgname IN ('trg_ras_immutable','trg_ras_truncate','trg_ras_liens','trg_ras_ledger_lie','trg_ras_ligne_liee')")).all()
                assert len(triggers) == 8 and {r[1] for r in triggers} == {'O'}
                assert db.scalar(text('SELECT count(*) FROM ras_reglement_captures')) == 2
                assert db.scalar(text('SELECT count(*) FROM ras_reglement_annulations')) == 1
                assert db.scalar(text('SELECT count(*) FROM lignes_ecriture')) == 15
            for table in ('ras_reglement_captures','ras_reglement_annulations'):
                for operation in (f'UPDATE {table} SET id=id', f'DELETE FROM {table}'):
                    garde(); refuse(restauree, operation, '23514')
            refuse(restauree, 'TRUNCATE ras_reglement_captures,ras_reglement_annulations', '23514')
            assert instantane(restauree) == avant
            # pg_dump --no-privileges ne transporte pas les ACL ni les rôles.
            with restauree.begin() as db:
                db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                assert not db.scalar(text("SELECT has_table_privilege('hisabpro','ras_reglement_captures','SELECT')"))
            garde(); rejouer083(restauree)
            assert instantane(restauree) == avant
            runtime = create_engine(make_url(cible['url']).set(username='hisabpro'))
            with runtime.connect() as db:
                assert db.scalar(text('SELECT current_user')) == 'hisabpro'
                assert db.scalar(text('SELECT count(*) FROM ras_reglement_captures')) == 2
                assert db.scalar(text('SELECT count(*) FROM ras_reglement_annulations')) == 1
                for table in ('ras_reglement_captures','ras_reglement_annulations'):
                    for privilege in ('SELECT','INSERT'):
                        assert db.scalar(text('SELECT has_table_privilege(current_user,:table,:privilege)'), {'table':table,'privilege':privilege})
                    for privilege in ('USAGE','SELECT'):
                        assert db.scalar(text('SELECT has_sequence_privilege(current_user,:sequence,:privilege)'), {'sequence':table+'_id_seq','privilege':privilege})
            for table in ('ras_reglement_captures','ras_reglement_annulations'):
                for operation in (f'UPDATE {table} SET id=id', f'DELETE FROM {table}', f'TRUNCATE {table}'):
                    garde(); refuse(runtime, operation, '42501')
            with pytest.raises(ValueError, match='doit être vide'):
                garde(); restaurer_isole(cible['url'], archive, cible['bin'], cible['directory'], cible['nonce'])
            assert instantane(restauree) == avant == instantane(application['engine'])
            assert 'ras_reglement_captures' not in models.Base.metadata.tables
        finally:
            if runtime is not None: runtime.dispose()
            restauree.dispose()
    assert not cible['directory'].exists()
