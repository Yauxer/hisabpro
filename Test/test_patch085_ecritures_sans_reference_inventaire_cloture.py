"""085 — Les écritures validées sans référence externe comptent dans le livre et la clôture."""
import ast
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, create_engine, or_
from sqlalchemy.orm import Session, declarative_base, joinedload, relationship

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services import livre_inventaire_service as livre

Base = declarative_base()


class Ecriture(Base):
    __tablename__ = "ecritures_test085"
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer, nullable=False)
    exercice = Column(Integer, nullable=False)
    est_validee = Column(Boolean, nullable=False)
    reference = Column(String, nullable=True)
    lignes = relationship("Ligne", back_populates="ecriture")


class Ligne(Base):
    __tablename__ = "lignes_test085"
    id = Column(Integer, primary_key=True)
    ecriture_id = Column(Integer, ForeignKey("ecritures_test085.id"))
    compte = Column(String, nullable=False)
    debit = Column(Numeric(18, 2), default=0)
    credit = Column(Numeric(18, 2), default=0)
    ecriture = relationship("Ecriture", back_populates="lignes")


def ecriture(sid, annee, ref, mouvements, validee=True):
    return Ecriture(
        societe_id=sid, exercice=annee, reference=ref, est_validee=validee,
        lignes=[Ligne(compte=compte, debit=Decimal(str(debit)), credit=Decimal(str(credit)))
                for compte, debit, credit in mouvements],
    )


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setitem(sys.modules, "models", SimpleNamespace(Ecriture=Ecriture))
    with Session(engine) as session:
        # 5 pièces validées existantes dans la recette (total 6 000 par sens).
        session.add_all([
            ecriture(1, 2026, "FA-2026-001", [("3421", 2400, 0), ("7124", 0, 2000), ("4455", 0, 400)]),
            ecriture(1, 2026, "REG-42", [("5141", 1200, 0), ("3421", 0, 1200)]),
            ecriture(1, 2026, "AV-2026-001", [("7124", 1000, 0), ("4455", 200, 0), ("3421", 0, 1200)]),
            ecriture(1, 2026, "BETA-TEST-2026-001", [("6126", 500, 0), ("34552", 100, 0), ("4411", 0, 600)]),
            ecriture(1, 2026, "VIR-BETA-001", [("4411", 600, 0), ("5141", 0, 600)]),
            # OD sans référence : ne doit pas disparaître des soldes de clôture.
            ecriture(1, 2026, None, [("5161", 100, 0), ("5141", 0, 100)]),
            # La clôture technique reste exclue, y compris avec une autre pièce nulle.
            ecriture(1, 2026, "CLOTURE-2026", [("7124", 1000, 0), ("6126", 0, 500), ("1191", 0, 500)]),
            ecriture(1, 2026, "", [("5161", 3, 0), ("5141", 0, 3)], validee=False),
            ecriture(2, 2026, None, [("5161", 900, 0), ("5141", 0, 900)]),
            ecriture(1, 2025, None, [("5161", 800, 0), ("5141", 0, 800)]),
        ])
        session.flush()
        yield session
    engine.dispose()


def fonction_cloture():
    """Exécute la fonction de production avec le modèle SQLAlchemy de test."""
    path = BACK / "routers" / "cloture.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    method = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "_soldes_comptes")
    ns = {"Session": Session, "models": SimpleNamespace(Ecriture=Ecriture),
          "joinedload": joinedload, "or_": or_, "Decimal": Decimal, "money": livre.money}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), "exec"), ns)
    return ns["_soldes_comptes"]


def test_085_inventaire_compte_od_sans_reference_et_exclut_cloture(db):
    soldes, debit, credit, nb = livre._soldes_valides(db, 1, 2026)
    assert nb == 6, "La pièce OD sans justificatif doit être incluse."
    assert (debit, credit) == (Decimal("6100.00"), Decimal("6100.00"))
    assert soldes["5141"] == Decimal("500.00")
    assert soldes["5161"] == Decimal("100.00")
    assert soldes["34552"] == Decimal("100.00")
    assert soldes["4455"] == Decimal("-200.00")
    assert "1191" not in soldes, "La pièce technique CLOTURE doit rester exclue."
    bilan = livre.calculer_bilan(soldes, livre.calculer_cpc(soldes)["resultat_net"])
    assert bilan["total_actif"] == Decimal("700.00")
    assert bilan["total_passif"] == Decimal("700.00")


def test_085_cloture_conserve_od_sans_reference_en_filtrant_les_validees(db):
    soldes = fonction_cloture()(db, 1, 2026, exclure_cloture=True, validees_seulement=True)
    assert soldes["5141"] == Decimal("500.00")
    assert soldes["5161"] == Decimal("100.00")
    assert "1191" not in soldes


def test_085_cloture_peut_exclure_ou_inclure_les_ecritures_techniques(db):
    cloture = fonction_cloture()
    historique = cloture(db, 1, 2026, exclure_cloture=True, validees_seulement=True)
    avec_cloture = cloture(db, 1, 2026, exclure_cloture=False, validees_seulement=True)
    assert historique["7124"] == Decimal("-1000.00")
    assert avec_cloture["7124"] == Decimal("0.00")
    assert avec_cloture["1191"] == Decimal("-500.00")
    assert historique["5161"] == avec_cloture["5161"] == Decimal("100.00")


def test_085_ne_modifie_pas_la_regle_justificatif_facultatif():
    # Vérifie que l'unique modification SQL accepte explicitement NULL.
    for f in (BACK / "services" / "livre_inventaire_service.py", BACK / "routers" / "cloture.py"):
        text = f.read_text(encoding="utf-8")
        assert "models.Ecriture.reference.is_(None)" in text
        assert '~models.Ecriture.reference.like(f"CLOTURE-{exercice}%")' in text
