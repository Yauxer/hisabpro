from pathlib import Path

import pytest
from pydantic import ValidationError

import schemas

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_lignes_facture_refusent_valeurs_incoherentes():
    with pytest.raises(ValidationError):
        schemas.LigneFactureCreate(description="Produit", quantite=0, prix_unitaire=100, tva=20)
    with pytest.raises(ValidationError):
        schemas.LigneFactureCreate(description="Produit", quantite=1, prix_unitaire=-1, tva=20)
    with pytest.raises(ValidationError):
        schemas.LigneFactureCreate(description="Produit", quantite=1, prix_unitaire=100, tva=101)
    with pytest.raises(ValidationError):
        schemas.LigneFactureCreate(description="Produit", quantite=1, prix_unitaire=100, remise=101)
    with pytest.raises(ValidationError):
        schemas.LigneFactureCreate(description="   ", quantite=1, prix_unitaire=100)


def test_types_et_statuts_commerciaux_sont_bornes_par_schema():
    with pytest.raises(ValidationError):
        schemas.BonCommandeCreate(type="autre", date="2026-09-13", tiers="T", lignes=[])
    with pytest.raises(ValidationError):
        schemas.BonLivraisonUpdate(statut="nimporte_quoi")
    with pytest.raises(ValidationError):
        schemas.DevisUpdate(statut="archive")


def test_machine_etat_bl_interdit_retour_sans_livraison():
    src = read("hisabpro-backend/routers/commercial.py")
    assert '"en_preparation": {"en_preparation", "expedie"}' in src
    assert '"expedie": {"expedie", "livre"}' in src
    assert '"livre": {"livre", "retourne"}' in src
    assert '_verifier_transition("le bon logistique", statut_avant, payload["statut"], _TRANSITIONS_BL)' in src


def test_declencheurs_stock_sont_strictement_controles():
    src = read("hisabpro-backend/routers/societe.py")
    assert '@field_validator("stock_declencheur_vente")' in src
    assert 'v not in {"facture", "bl"}' in src
    assert '@field_validator("stock_declencheur_achat")' in src
    assert 'v not in {"facture", "br"}' in src


def test_facture_ne_peut_plus_forcer_son_statut_par_api():
    src = read("hisabpro-backend/routers/factures.py")
    assert "Une nouvelle facture doit être créée avec le statut 'en_attente'." in src
    assert 'statut="en_attente", notes=data.notes' in src
    assert "Le statut de la facture est calculé automatiquement" in src
    front = read("src/pages/Factures.jsx")
    assert 'value={statut} disabled title="Statut calculé automatiquement' in front


def test_sources_commerciales_sont_scopees_societe():
    src = read("hisabpro-backend/routers/commercial.py")
    assert "def _facture_societe" in src
    assert "def _devis_societe" in src
    assert "def _bc_societe" in src
    assert "models.Devis.societe_id == societe_id" in src
    assert "models.BonCommande.societe_id == societe_id" in src
    assert "_verifier_lignes_source_devis(db, societe_id, data.lignes, data.devis_id)" in src
    assert "_verifier_lignes_source_bc(db, societe_id, data.lignes, data.bon_commande_id)" in src
    factures = read("hisabpro-backend/routers/factures.py")
    assert "def _verifier_sources_facture_societe" in factures
    assert "_verifier_sources_facture_societe(db, societe_id, data.lignes)" in factures


def test_retour_bl_ne_cree_pas_entree_si_stock_pilote_par_facture():
    src = read("hisabpro-backend/routers/commercial.py")
    assert 'if declencheur == "bl":' in src
    assert "Ce bon n'a pas généré de sortie de stock active" in src
    assert 'source_type="bon_livraison"' in src


def test_statuts_devis_et_bc_ne_sont_plus_editables_librement_dans_formulaires():
    front = read("src/pages/Commercial.jsx")
    assert 'value={form.statut} disabled title="Le statut évolue via les actions du cycle du devis"' in front
    assert 'value={form.statut} disabled title="Le statut est piloté par les livraisons/réceptions et la facturation"' in front
