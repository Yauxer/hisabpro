from datetime import date
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "hisabpro-backend" / "services" / "fiscalite_acomptes_service.py"
PAGE = ROOT / "src" / "pages" / "FiscaliteIS.jsx"
CSS = ROOT / "src" / "pages" / "FiscaliteIS.module.css"


def _load_service():
    spec = spec_from_file_location("fiscalite_acomptes_service_patch093", SERVICE)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_acompte_partiel_en_retard_et_reste_a_couvrir():
    mod = _load_service()
    situation = mod.construire_acomptes(
        date_debut=date(2026, 1, 1),
        reference={
            "disponible": True,
            "non_applicable": False,
            "montant_annuel": 20000,
        },
        paiements=[{
            "numero": 2,
            "montant_verse": 2000,
            "date_versement": date(2026, 9, 27),
            "reference_paiement": "TEST-ACP-2026-02",
        }],
        date_reference=date(2026, 9, 27),
    )
    ligne2 = situation["acomptes"][1]
    assert ligne2["statut"] == "partiel_en_retard"
    assert str(ligne2["reste_a_couvrir"]) == "3000.00"


def test_frontend_affiche_statut_et_reste():
    page = PAGE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")
    assert "partiel_en_retard:'Partiel — en retard'" in page
    assert "Reste : {mad(a.reste_a_couvrir)}" in page
    assert ".acompte_partiel_en_retard" in css
    assert ".acompteReste" in css
