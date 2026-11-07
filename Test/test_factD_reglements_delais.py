from pathlib import Path

import pytest
from pydantic import ValidationError

import schemas

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def ligne():
    return schemas.LigneFactureCreate(
        description="Prestation", quantite=1, prix_unitaire=100, tva=20
    )


def test_factD_modes_reglement_sont_bornes_et_effet_exige_echeance():
    with pytest.raises(ValidationError):
        schemas.ReglementCreate(
            date="2026-09-13", tiers="Client", montant=100, mode="crypto"
        )
    with pytest.raises(ValidationError):
        schemas.ReglementCreate(
            date="2026-09-13", tiers="Client", montant=100, mode="effet"
        )
    ok = schemas.ReglementCreate(
        date="2026-09-13", tiers="Client", montant=100, mode="effet",
        date_echeance="2026-10-13",
    )
    assert ok.mode == "effet"


def test_factD_montant_reglement_et_echeance_sont_coherents():
    with pytest.raises(ValidationError):
        schemas.ReglementCreate(
            date="2026-09-13", tiers="Client", montant=0, mode="virement"
        )
    with pytest.raises(ValidationError):
        schemas.ReglementCreate(
            date="2026-09-13", tiers="Client", montant=100, mode="cheque",
            date_echeance="2026-09-12",
        )


def test_factD_delai_facture_est_borne_sans_bloquer_les_delais_long_conventionnels():
    with pytest.raises(ValidationError):
        schemas.FactureCreate(
            type="vente", date="2026-09-13", tiers="Client", delai_paiement=-1,
            lignes=[ligne()],
        )
    with pytest.raises(ValidationError):
        schemas.FactureCreate(
            type="vente", date="2026-09-13", tiers="Client", delai_paiement=366,
            lignes=[ligne()],
        )
    # 180 jours reste techniquement accepté : HisabPro avertit, il ne bloque pas
    # une convention/dérogation sectorielle potentiellement valable.
    f = schemas.FactureCreate(
        type="vente", date="2026-09-13", tiers="Client", delai_paiement=180,
        mode_reglement_prevu="virement", lignes=[ligne()],
    )
    assert f.delai_paiement == 180


def test_factD_plafond_credit_reutilise_le_solde_unifie_et_exclut_rejets():
    src = read(BACK / "routers" / "factures.py")
    assert 'situation = _situation_paiement_facture(db, societe_id, f)' in src
    assert 'encours += situation["solde_restant"]' in src
    assert '.filter(models.Reglement.statut.notin_(["rejete", "annule"]))' in src


def test_factD_distingue_regle_et_reellement_encaisse():
    src = read(BACK / "routers" / "factures.py")
    assert '"total_encaisse": total_encaisse' in src
    assert '"total_reglement_en_cours": total_reglement_en_cours' in src
    front = read(ROOT / "src" / "pages" / "Factures.jsx")
    assert "Encaissement en cours" in front


def test_factD_frais_bancaires_sont_bornes():
    from routers.commercial import TransitionIn

    for frais in (-1, float('nan'), float('inf'), float('-inf'), True, 10.005):
        with pytest.raises(ValidationError):
            TransitionIn(action='encaisser', frais=frais)
    for frais in (None, 0, 0.01, 10.01, '10.01'):
        attendu = 0 if frais is None else float(frais)
        assert TransitionIn(action='encaisser', frais=frais).frais == attendu
    src = read(BACK / "routers" / "commercial.py")
    assert 'Les frais bancaires ne peuvent pas dépasser le montant du règlement.' in src
    front = read(ROOT / "src" / "pages" / "Effets.jsx")
    assert 'max={reglement.montant || undefined}' in front


def test_factD_conditions_reglement_sont_figees_et_imprimees():
    models = read(BACK / "models.py")
    schemas_src = read(BACK / "schemas.py")
    factures = read(BACK / "routers" / "factures.py")
    pdf = read(BACK / "services" / "document_pdf_service.py")
    sql = read(BACK / "042_factD_reglements_delais.sql")
    assert "mode_reglement_prevu = Column" in models
    assert "reference_reglement_prevue = Column" in models
    assert "mode_reglement_prevu: Optional[ModeReglement]" in schemas_src
    assert "reference_reglement_prevue" in factures
    assert "règlement prévu par" in pdf
    assert "NEW.mode_reglement_prevu IS DISTINCT FROM OLD.mode_reglement_prevu" in sql


def test_factD_delai_superieur_120_est_un_avertissement_non_bloquant():
    src = read(BACK / "routers" / "factures.py")
    front = read(ROOT / "src" / "pages" / "Factures.jsx")
    assert "def _alerte_delai_paiement" in src
    assert "jours > 120" in src
    assert "Délai supérieur à 120 jours" in front
    assert "loi 69-21" in src
