from decimal import Decimal
from io import BytesIO
import os
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
from pypdf import PdfReader
from services import etic_service as etic
from services.liasse_pdf import generer_liasse_pdf
from test_patch09_3_liasse_fiscale import _dummy_liasse


def test_source_sur_subdivision_absente_reste_visible_sans_reclassement(monkeypatch):
    src = {"44110001": {"total_source": Decimal(960), "plus_un_an": Decimal(0),
                         "moins_un_an": Decimal(0), "echues": Decimal(0),
                         "anomalies_sources": [{"facture_id": 66, "numero": "FA-016", "motifs": ["Compte exact divergent"]}]}}
    monkeypatch.setattr(etic, "_ventilation_factures_par_compte", lambda *a: src)
    lignes = [{"compte": "4411", "montant": 1200}]
    etic._ajouter_echeances_auto(object(), 3, 2026, lignes, "achat")
    assert lignes[0]["montant"] == 1200
    assert "echeance_auto" not in lignes[0]
    assert "echeance_auto_partiel" not in lignes[0]
    hors = lignes[0]["echeance_auto_sources_hors_solde"][0]
    assert hors["compte"] == "44110001"
    assert hors["total_source"] == 960
    data = _dummy_liasse()
    data["etic"]["sections"] = [{"code": "B7", "automatique": {"lignes": lignes}}]
    texte = " ".join(" ".join(p.extract_text() for p in PdfReader(BytesIO(generer_liasse_pdf(data))).pages).split())
    assert "Compte source absent des soldes : 44110001" in texte
    assert "FA-016" in texte
