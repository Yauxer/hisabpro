from pathlib import Path

import pytest
from pydantic import ValidationError

import schemas

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
SRC = ROOT / "src"


def txt(path):
    return path.read_text(encoding="utf-8")


def test_tiers_preserve_paiement_comptant_et_valide_les_champs():
    route = txt(BACK / "routers" / "tiers.py")
    front = txt(SRC / "pages" / "Tiers.jsx")
    assert "plafond_credit:" in route
    assert '@field_validator("ice")' in route
    assert '@field_validator("email")' in route
    assert '@field_validator("delai_paiement")' in route
    assert '@field_validator("plafond_credit")' in route
    assert "entierOuDefaut(form.delai_paiement, 60)" in front
    assert "value={form.delai_paiement ?? 60}" in front
    assert "Paiement comptant" in front
    assert "|| 60" not in front


def test_article_preserve_tva_zero_et_refuse_valeurs_negatives():
    article = schemas.ArticleCreate(code="EXO", designation="Article exonéré", tva=0)
    assert article.tva == 0
    with pytest.raises(ValidationError):
        schemas.ArticleCreate(code="NEG", designation="Invalide", prix_vente_ht=-1)


def test_lignes_commerciales_refusent_quantite_nulle_et_tva_invalide():
    with pytest.raises(ValidationError):
        schemas.LigneDevisCreate(description="A", quantite=0, prix_unitaire=10, tva=20)
    with pytest.raises(ValidationError):
        schemas.LigneBCCreate(description="A", quantite=1, prix_unitaire=10, tva=120)
    with pytest.raises(ValidationError):
        schemas.LigneBLCreate(description="A", quantite_prevue=1, quantite_livree=-1)


def test_creation_documents_peut_laisser_numero_au_serveur():
    assert schemas.DevisCreate(numero=None, date="2026-09-09", tiers="C", lignes=[{"description":"A"}]).numero is None
    assert schemas.BonCommandeCreate(numero=None, date="2026-09-09", tiers="C", lignes=[{"description":"A"}]).numero is None
    assert schemas.BonLivraisonCreate(numero=None, date="2026-09-09", tiers="C", lignes=[{"description":"A"}]).numero is None


def test_articles_stock_actuel_n_est_plus_patchable_depuis_le_formulaire():
    front = txt(SRC / "pages" / "Articles.jsx")
    route = txt(BACK / "routers" / "articles.py")
    assert "!article?.id && setForm" in front
    assert 'if "stock_actuel" in updates:' in route
    assert "corriger_stock_cible" in route
    assert "stock_initial:article:" in route


def test_facture_recherche_compte_et_valeurs_zero_safe():
    front = txt(SRC / "pages" / "Factures.jsx")
    assert "TiersPicker" in front
    assert "Recherche par nom, ICE, compte comptable ou ville." in front
    assert "tiersSelectionne" in front
    assert "entierOuDefaut(delaiPaiement, 60)" in front
    assert "nombreOuDefaut(l.tva, 20)" in front
    assert "delaiTiers ? delaiTiers" not in front
    assert "parseFloat(tvafamille) || 20" not in front


def test_dates_de_formulaire_n_utilisent_plus_utc_sur_les_ecrans_critiques():
    for rel in ["pages/Factures.jsx", "pages/Commercial.jsx", "pages/Acomptes.jsx"]:
        contenu = txt(SRC / rel)
        assert "new Date().toISOString().split('T')[0]" not in contenu
        assert "dateLocaleISO" in contenu


def test_reglement_affiche_et_utilise_le_reste_a_payer():
    front = txt(SRC / "pages" / "Commercial.jsx")
    assert "/reglements`)" in front
    assert "data.solde_restant" in front
    assert "Reste à payer" in front
    assert "Le règlement dépasse le reste à payer" in front


def test_acompte_selectionne_un_tiers_par_id_et_affiche_solde_facture():
    front = txt(SRC / "pages" / "Acomptes.jsx")
    assert "form.tiers_id" in front
    assert "<datalist" not in front
    assert "situation.solde_restant" in front
    assert "Acomptes déjà imputés" in front


def test_numerotation_nouveaux_documents_est_reservee_cote_serveur():
    route = txt(BACK / "routers" / "commercial.py")
    front = txt(SRC / "pages" / "Commercial.jsx")
    assert 'reserver_numero_commercial(db, societe_id, _exercice_ref(db, societe_id, data.date), "devis", prefixe)' in route
    assert 'reserver_numero_commercial(db, societe_id, _exercice_ref(db, societe_id, data.date), "bc", prefixe)' in route
    assert '"br" if est_achat else "bl"' in route
    assert front.count("numero: null") >= 2
    assert "`/api/bons-commande/${bc.id}/convertir-bl`" in front
    assert "réservation définitive côté serveur" in front
