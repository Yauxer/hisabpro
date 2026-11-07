"""Registre 128 et application contrôlée des migrations, sur cluster nonce uniquement."""
from pathlib import Path
import shutil
import sys

import pytest
from sqlalchemy import create_engine, text

from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ops'))
import migrations_hisabpro as mh  # noqa: E402


def test_957_registre_base_existante_constat_puis_suivantes(tmp_path, monkeypatch, capsys):
    dossier = tmp_path / 'sql'
    # 131+ supposent le schéma paie complet : testés par leurs propres tests isolés (968).
    shutil.copytree(ROOT / 'hisabpro-backend', dossier,
                    ignore=lambda d, n: [x for x in n if not mh.MOTIF.match(x) or int(x[:3]) > 130])
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        engine = create_engine(c['url'])
        try:
            base = engine.connect().execute(text('SELECT current_database()')).scalar()
            with engine.begin() as db:  # base « existante » minimale et fictive
                db.execute(text('CREATE TABLE factures(id int primary key)'))
                db.execute(text('CREATE TABLE reglements(id int primary key, statut text, date date)'))
                db.execute(text('CREATE TABLE utilisations_avoirs(id int primary key, type_utilisation text, '
                                'date_utilisation date, reference text)'))
                db.execute(text("INSERT INTO reglements VALUES (1,'complet','2025-01-20')"))
                db.execute(text('CREATE TABLE societes(id int primary key)'))
                db.execute(text('CREATE TABLE utilisateurs(id int primary key)'))
                db.execute(text('CREATE TABLE lignes_ecriture(id int primary key, debit numeric, credit numeric)'))
                db.execute(text('CREATE TABLE lettrages_comptables(id int primary key, societe_id int, '
                                'ligne_ecriture_id int, code varchar(10), actif boolean)'))
            monkeypatch.setenv('URL957', c['url'])
            run = lambda *a: mh.main(['--url-env', 'URL957', '--dossier', str(dossier), *a])
            with pytest.raises(SystemExit, match='différente'):
                run('etat', '--base-attendue', 'autre')
            with pytest.raises(SystemExit, match='réservé à une base vierge'):
                run('appliquer', '--base-attendue', base, '--jusqua', '127')
            with pytest.raises(SystemExit, match='Registre vide'):
                run('appliquer', '--base-attendue', base, '--suivantes')
            assert run('constater', '--base-attendue', base, '--jusqua', '125') == 0
            capsys.readouterr()
            run('etat', '--base-attendue', base)
            etat = dict(l.split('\t') for l in capsys.readouterr().out.strip().splitlines())
            assert etat['126_avoirs_compensations_tva.sql'] == 'en_attente'
            assert etat['065_reparation_liquidations_is_reference_acomptes.sql'].startswith('en_attente (réparation')
            assert etat['100_reprises_provisions.sql'] == 'constatee'
            assert run('appliquer', '--base-attendue', base, '--suivantes') == 0
            out = capsys.readouterr().out
            for nom in ('126_avoirs_compensations_tva.sql', '127_reglements_annulation_effective.sql',
                        '129_declarations_tva_deposees.sql', '130_lettrage_partiel.sql'):
                assert nom in out
            assert run('appliquer', '--base-attendue', base, '--suivantes') == 0
            assert 'exécutée' not in capsys.readouterr().out
            with engine.connect() as db:
                assert db.scalar(text("SELECT count(*) FROM hisabpro_migrations WHERE mode='executee'")) == 5
                assert db.scalar(text("SELECT to_regclass('public.declarations_tva_deposees') IS NOT NULL"))
                assert db.scalar(text("SELECT count(*) FROM hisabpro_migrations WHERE fichier LIKE '065%'")) == 0
                assert db.scalar(text('SELECT date_rejet_effective IS NULL FROM reglements WHERE id=1'))
            (dossier / '127_reglements_annulation_effective.sql').write_text('-- modifié\n', encoding='utf-8')
            with pytest.raises(SystemExit, match='Empreinte modifiée'):
                run('appliquer', '--base-attendue', base, '--suivantes')
        finally:
            engine.dispose()
