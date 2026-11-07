# -*- coding: utf-8 -*-
"""Régression 062 — figer les lignes avant de rendre une facture immuable."""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "hisabpro-backend/routers/factures.py").read_text(encoding="utf-8")


def _fonction(nom):
    tree = ast.parse(SRC)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == nom)
    return ast.get_source_segment(SRC, node)


def test_062_validation_fixe_les_comptes_avant_est_validee_et_meme_transaction():
    bloc = _fonction("valider_facture")
    assert bloc.index("figer_comptes_facture(db, societe_id, facture)") < bloc.index("db.flush()")
    assert bloc.index("db.flush()") < bloc.index("facture.est_validee = True")
    assert bloc.index("facture.est_validee = True") < bloc.index("db.flush()", bloc.index("facture.est_validee = True"))
    assert bloc.index("facture.est_validee = True") < bloc.index("db.commit()")
    assert "DISABLE TRIGGER" not in bloc


def test_062_conversion_proforma_fixe_les_comptes_avant_transition_definitive():
    bloc = _fonction("convertir_proforma")
    pos_snapshot = bloc.index('figer_comptes_facture(db, current_user["societe_id"], facture)')
    pos_flush = bloc.index("db.flush()", pos_snapshot)
    pos_transition = bloc.index("facture.est_proforma = False")
    pos_validee = bloc.index("facture.est_validee = True")
    assert pos_snapshot < pos_flush < pos_transition < pos_validee
    assert "DISABLE TRIGGER" not in bloc


def test_062_recette_reelle_endpoints_avec_trigger_immuabilite_sqlite():
    # PostgreSQL n'est pas disponible dans l'environnement de test : on installe
    # ici sur les vraies tables ORM un trigger SQLite analogue au garde PostgreSQL.
    # La recette appelle les vrais endpoints pour une vente et une conversion proforma,
    # puis vérifie qu'une modification ultérieure de ligne reste interdite.
    script = r'''
import importlib.util
from datetime import date
from pathlib import Path
from sqlalchemy.exc import IntegrityError

p = Path('Test/recette_fact5_e2e.py').resolve()
spec = importlib.util.spec_from_file_location('recette_fact5_guard062', p)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
with r.fdb.engine.begin() as con:
    con.exec_driver_sql("""
        CREATE TRIGGER garde_ligne_062 BEFORE UPDATE ON lignes_facture
        WHEN (SELECT est_validee FROM factures WHERE id = NEW.facture_id) = 1
        AND COALESCE((SELECT est_proforma FROM factures WHERE id = NEW.facture_id),0) = 0
        BEGIN
          SELECT RAISE(ABORT, 'Facture validée : ses lignes sont immuables.');
        END;
    """)
r._installer_numerotation_test()
t = r.Recette()
t.setup()
creer = lambda proforma: r.schemas.FactureCreate(
    type='vente', date=date(2026, 9, 9), tiers=t.client.nom, tiers_id=t.client.id,
    est_proforma=proforma,
    lignes=[r.schemas.LigneFactureCreate(article_id=t.article.id,
          description='Regression snapshots 062', quantite=1, prix_unitaire=100, tva=20)]
)
normal = r.factures.creer_facture(creer(False), r.CU, t.db)
resultat = r.factures.valider_facture(normal['id'], r.CU, t.db)
assert resultat['est_validee'] is True
assert resultat['numero']
inv = t.db.get(r.models.Facture, normal['id'])
assert inv.lignes[0].compte_vente_snapshot == '7111'
assert inv.lignes[0].compte_achat_snapshot == '6111'

pro = r.factures.creer_facture(creer(True), r.CU, t.db)
converti = r.factures.convertir_proforma(
    pro['id'], r.schemas.ConvertirProformaIn(date=date(2026, 9, 9)), r.CU, t.db)
assert 'convertie en facture' in converti['message']
pro_inv = t.db.get(r.models.Facture, pro['id'])
assert pro_inv.est_validee and not pro_inv.est_proforma
assert pro_inv.lignes[0].compte_vente_snapshot == '7111'

inv.lignes[0].compte_vente_snapshot = '7999'
try:
    t.db.flush()
except IntegrityError as exc:
    assert 'Facture validée : ses lignes sont immuables.' in str(exc)
    t.db.rollback()
else:
    raise AssertionError('La mise à jour d’une ligne validée a été autorisée')
print('PASS vente, proforma et immuabilité des lignes sous trigger')
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT, capture_output=True, text=True, timeout=90,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "PASS vente, proforma et immuabilité des lignes sous trigger" in result.stdout
