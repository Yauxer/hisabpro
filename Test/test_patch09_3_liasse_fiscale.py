# -*- coding: utf-8 -*-
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

sys.modules.setdefault("models", types.SimpleNamespace())
from services.liasse_service import calculer_cpc, calculer_bilan, empreinte_liasse, contenu_canonique
from services.liasse_pdf import generer_liasse_pdf


def test_cpc_patch09_3_resultat_net():
    soldes = {
        "7111": {"debit": 0, "credit": 100000},
        "6111": {"debit": 30000, "credit": 0},
        "6171": {"debit": 20000, "credit": 0},
        "6701": {"debit": 10000, "credit": 0},
    }
    cpc = calculer_cpc(soldes)
    assert cpc["XI"] == 50000.0
    assert cpc["XII"] == 10000.0
    assert cpc["resultat_net"] == 40000.0


def test_bilan_patch09_3_equilibre_avec_resultat_injecte():
    soldes = {
        "5141": {"debit": 140000, "credit": 0},
        "1111": {"debit": 0, "credit": 100000},
    }
    bilan = calculer_bilan(soldes, 40000)
    assert bilan["equilibre"] is True
    assert bilan["actif"]["total"]["net"] == 140000.0
    assert bilan["passif"]["total"] == 140000.0


def _dummy_liasse():
    return {
        "exercice": 2026,
        "statut": "prete",
        "societe": {"raison_sociale": "Test SARL", "identifiant_fiscal": "123", "ice": "001", "rc": "42", "devise": "MAD"},
        "exercice_comptable": {"date_debut": "2026-01-01", "date_fin": "2026-12-31"},
        "controles": {"items": [{"ok": True, "bloquant": True, "libelle": "Balance", "details": ""}]},
        "etats": {
            "bilan": {"actif": {"immobilise": [], "circulant": [], "tresorerie": []}, "passif": {"capitaux_propres": [], "financement_permanent": [], "passif_circulant": [], "tresorerie": []}},
            "cpc": {"lignes": []}, "esg": {"lignes": []},
            "tableau_financement": {"synthese": []},
        },
        "fiscal": {"passage_resultat_fiscal": [], "situation": {"liquidation": {}}},
        "etic": {"progression": {"completes": 0, "total": 0}, "sections": []},
        "archive": None,
    }


def test_empreinte_liasse_deterministe_et_archive_exclue():
    a = _dummy_liasse(); b = _dummy_liasse()
    b["archive"] = {"id": 99, "empreinte_sha256": "x" * 64}
    assert empreinte_liasse(a) == empreinte_liasse(b)
    assert '"statut":"finalisee"' in contenu_canonique(a)


def test_empreinte_change_si_chiffre_change():
    a = _dummy_liasse(); b = _dummy_liasse(); b["societe"]["ice"] = "002"
    assert empreinte_liasse(a) != empreinte_liasse(b)


def test_pdf_liasse_genere_un_vrai_pdf():
    pdf = generer_liasse_pdf(_dummy_liasse())
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_migration_027_archive_immutable_et_permissions():
    sql = (BACK / "027_liasse_fiscale_archive.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS liasses_fiscales_archives" in sql
    assert "BEFORE UPDATE OR DELETE" in sql
    assert "GRANT SELECT, INSERT" in sql
    assert "empreinte_sha256" in sql


def test_modele_archive_present():
    text = (BACK / "models.py").read_text(encoding="utf-8")
    assert "class LiasseFiscaleArchive" in text
    assert '__tablename__ = "liasses_fiscales_archives"' in text


def test_routes_liasse_presentes():
    text = (BACK / "routers" / "etats.py").read_text(encoding="utf-8")
    assert '@router.get("/liasse/{exercice}")' in text
    assert '@router.post("/liasse/{exercice}/finaliser")' in text
    assert '@router.get("/liasse/{exercice}/pdf")' in text
    assert '@router.get("/liasse/{exercice}/archive")' in text


def test_frontend_export_excel_pdf_et_edi_non_simule():
    page = (ROOT / "src" / "pages" / "LiasseFiscale.jsx").read_text(encoding="utf-8")
    assert "XLSX.writeFile" in page
    assert "telechargerLiassePDF" in page
    assert "EDI SIMPL-IS" in page
    assert "disabled title=" in page
    assert "Télédéclarer DGI" not in page


def test_api_frontend_liasse():
    api = (ROOT / "src" / "services" / "api.js").read_text(encoding="utf-8")
    assert "finaliserLiasse(exercice)" in api
    assert "telechargerLiassePDF(exercice" in api
    assert "downloadRequest" in api


def test_liasse_finalisee_est_relue_depuis_archive_immutable():
    text = (BACK / "routers" / "etats.py").read_text(encoding="utf-8")
    start = text.index('@router.get("/liasse/{exercice}")')
    end = text.index('@router.get("/liasse/{exercice}/archive")')
    bloc = text[start:end]
    assert "LiasseFiscaleArchive" in bloc
    assert "json.loads(rec.contenu_json)" in bloc
    assert 'data["statut"] = "finalisee"' in bloc


def test_export_excel_embarque_le_contenu_detaille_etic():
    page = (ROOT / "src" / "pages" / "LiasseFiscale.jsx").read_text(encoding="utf-8")
    assert "const eticRows" in page
    assert "auto.colonnes" in page
    assert "auto.lignes" in page
    assert "contenu.lignes" in page
    assert "Néant pour l’exercice" in page
