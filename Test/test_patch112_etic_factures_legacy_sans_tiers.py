from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "services"))

import services.etic_service as service


def _ligne(compte, debit=0, credit=0):
    return SimpleNamespace(compte=compte, debit=Decimal(str(debit)), credit=Decimal(str(credit)))


def _facture(fid, d, numero, reference, montant, tiers_id=None):
    f = SimpleNamespace(
        id=fid,
        date=d,
        numero=numero,
        reference=reference,
        tiers_id=tiers_id,
        lignes=[],
    )
    f._ttc_test = Decimal(str(montant))
    return f


def test_match_etic_accepte_facture_legacy_sans_tiers_id(monkeypatch):
    d = date(2026, 5, 8)
    e = SimpleNamespace(date=d, reference="0001", lignes=[_ligne("4411", credit=6000)])
    f = _facture(1, d, "ACH-1", "0001", 6000, tiers_id=None)
    monkeypatch.setattr(service, "_ttc_facture_etic", lambda facture: facture._ttc_test)
    assert service._choisir_facture_historique_etic(e, [f], "achat") is f


def test_match_etic_desambigue_meme_date_meme_montant_par_reference(monkeypatch):
    d = date(2026, 5, 22)
    e = SimpleNamespace(date=d, reference="87", lignes=[_ligne("4411", credit=1200)])
    f1 = _facture(1, d, "ACH-A", "87", 1200)
    f2 = _facture(2, d, "ACH-B", "88", 1200)
    monkeypatch.setattr(service, "_ttc_facture_etic", lambda facture: facture._ttc_test)
    assert service._choisir_facture_historique_etic(e, [f1, f2], "achat") is f1


def test_match_etic_refuse_deux_factures_ambiguës_sans_reference(monkeypatch):
    d = date(2026, 5, 22)
    e = SimpleNamespace(date=d, reference=None, lignes=[_ligne("4411", credit=1200)])
    f1 = _facture(1, d, "ACH-A", None, 1200)
    f2 = _facture(2, d, "ACH-B", None, 1200)
    monkeypatch.setattr(service, "_ttc_facture_etic", lambda facture: facture._ttc_test)
    assert service._choisir_facture_historique_etic(e, [f1, f2], "achat") is None


def test_factures_modernes_restent_exigees_validees_et_comptabilisees():
    code = (BACKEND / "services" / "etic_service.py").read_text(encoding="utf-8")
    assert 'bool(getattr(f, "est_validee", False))' in code
    assert 'bool(getattr(f, "est_comptabilisee", False))' in code
    assert "_choisir_facture_historique_etic(ecriture, candidates, type_facture)" in code
