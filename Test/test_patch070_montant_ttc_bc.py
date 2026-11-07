"""070 — la liste des bons de commande expose HT et TTC déjà calculés côté API."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_070_liste_bc_affiche_ht_et_ttc_pour_ventes_et_achats():
    source = (ROOT / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
    bloc = source.split('function OngletBonsCommande(', 1)[1].split('function OngletBonsLivraison(', 1)[0]
    # Le même onglet sert aux commandes de vente et d'achat.
    assert 'typeForce = null' in source.split('function OngletBonsCommande(', 1)[1][:100]
    assert "b.type === typeForce" in bloc
    entete = bloc.split('<table className={styles.table}>', 1)[1].split('</thead>', 1)[0]
    lignes = bloc.split('<tbody>', 1)[1].split('</tbody>', 1)[0]
    assert entete.index('Total HT') < entete.index('Total TTC') < entete.index('Livraison')
    assert 'formatMAD(bc.total_ht)' in lignes
    assert 'formatMAD(bc.total_ttc)' in lignes
    assert lignes.index('formatMAD(bc.total_ht)') < lignes.index('formatMAD(bc.total_ttc)')
    # Les montants proviennent du modèle existant, sans recalcul côté navigateur.
    assert 'bc.total_ht + bc.total_tva' not in lignes


@pytest.mark.parametrize('taux,ttc_attendu', [(20, 2400.0), (0, 2000.0)])
def test_070_api_bc_fournit_le_total_ttc_reel(taux, ttc_attendu):
    path = ROOT / 'hisabpro-backend/routers/commercial.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    noms = ('_totaux_bc', '_fmt_bc')
    fonctions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in noms]
    assert len(fonctions) == len(noms)
    contexte = {
        '_net_ht_ligne': lambda l: l.quantite * l.prix_unitaire,
        '_taux_effectif_ligne': lambda l: l.tva,
        '_situation_cycle_bc': lambda db, sid, bc: {},
    }
    exec(compile(ast.Module(body=fonctions, type_ignores=[]), str(path), 'exec'), contexte)
    ligne = SimpleNamespace(id=1, quantite=2, prix_unitaire=1000.0, tva=taux)
    bc = SimpleNamespace(societe_id=1, lignes=[ligne])
    rendu = contexte['_fmt_bc'](bc)
    assert rendu['total_ht'] == 2000.0
    assert rendu['total_tva'] == ttc_attendu - 2000.0
    assert rendu['total_ttc'] == ttc_attendu


def test_070_devis_et_factures_conservent_leur_ttc():
    source = (ROOT / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
    devis = source.split('function OngletDevis(', 1)[1].split('function OngletBonsCommande(', 1)[0]
    assert 'formatMAD(d.total_ttc)' in devis
    assert 'formatMAD(f.total_ttc)' in source
