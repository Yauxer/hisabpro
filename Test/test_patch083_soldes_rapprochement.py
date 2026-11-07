"""Régression 083 : reprise bancaire indépendante des écritures comptables."""
import ast
import math
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import Column, Date, Integer, Numeric, String, create_engine
from sqlalchemy.orm import Session, declarative_base

ROOT = Path(__file__).resolve().parents[1]
ROUTE = ROOT / 'hisabpro-backend' / 'routers' / 'rapprochement.py'
PAGE = ROOT / 'src' / 'pages' / 'RapprochementBancaire.jsx'

Base = declarative_base()


class Etat(Base):
    __tablename__ = 'rapprochement_etats_test083'
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer)
    compte = Column(String)
    date_debut = Column(Date)
    date_fin = Column(Date)
    solde_initial = Column(Numeric(18, 2))
    solde_final = Column(Numeric(18, 2))
    solde_releve = Column(Numeric(18, 2))


class Ligne(Base):
    __tablename__ = 'rapprochement_lignes_test083'
    id = Column(Integer, primary_key=True)
    societe_id = Column(Integer)
    compte = Column(String)
    date = Column(Date)
    sens = Column(String)
    montant = Column(Numeric(18, 2))


def calcul(db, sid, compte, debut):
    """Exécute la véritable fonction du routeur sans importer le pilote PostgreSQL."""
    module = ast.parse(ROUTE.read_text(encoding='utf-8'))
    func = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == '_solde_initial_periode_suivante')
    func.returns = None
    func.args.args[0].annotation = None
    qualification = next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == '_montant_releve_exploitable')
    ns = {'Session': Session, 'Decimal': Decimal, 'timedelta': timedelta, 'date': date,
          'math': math,
          'models': SimpleNamespace(RapprochementEtat=Etat, RapprochementLigne=Ligne)}
    exec(compile(ast.Module(body=[qualification, func], type_ignores=[]), str(ROUTE), 'exec'), ns)
    return ns['_solde_initial_periode_suivante'](db, sid, compte, debut)


def db_test():
    engine = create_engine('sqlite+pysqlite:///:memory:')
    Base.metadata.create_all(engine)
    return Session(engine)


def etat(db, societe=1, compte='5141', debut=date(2026, 9, 1), fin=date(2026, 9, 30), initial=0, final=None):
    db.add(Etat(societe_id=societe, compte=compte, date_debut=debut, date_fin=fin,
                solde_initial=initial, solde_final=final, solde_releve=None))
    db.flush()


def ligne(db, sens, montant, societe=1, compte='5141', d=date(2026, 9, 20)):
    db.add(Ligne(societe_id=societe, compte=compte, date=d, sens=sens, montant=montant))
    db.flush()


def test_reprise_debut_octobre_calculee_sur_lignes_releve_uniquement():
    with db_test() as db:
        etat(db)
        for sens, montant in [('credit', 1200), ('debit', 600), ('debit', 100)]:
            ligne(db, sens, montant)
        assert calcul(db, 1, '5141', date(2026, 10, 1)) == Decimal('500.00')


def test_solde_bancaire_declare_prime_sur_solde_reconstitue():
    with db_test() as db:
        etat(db, final=Decimal('480.00'))
        ligne(db, 'credit', 1200)
        assert calcul(db, 1, '5141', date(2026, 10, 1)) == Decimal('480.00')


def test_pas_de_reprise_sans_solde_initial_ou_periode_adjacent():
    with db_test() as db:
        etat(db, initial=None)
        ligne(db, 'credit', 1200)
        assert calcul(db, 1, '5141', date(2026, 10, 1)) is None
        assert calcul(db, 1, '5141', date(2026, 11, 1)) is None


def test_pas_de_reprise_autre_societe_ou_compte():
    with db_test() as db:
        etat(db)
        ligne(db, 'credit', 1200)
        assert calcul(db, 2, '5141', date(2026, 10, 1)) is None
        assert calcul(db, 1, '5142', date(2026, 10, 1)) is None


def test_releve_annuel_reconstitue_solde_octobre_sans_utiliser_cloture_decembre():
    with db_test() as db:
        etat(db, debut=date(2026, 1, 1), fin=date(2026, 12, 31), final=999)
        for sens, montant in [('credit', 1200), ('debit', 600), ('debit', 100)]:
            ligne(db, sens, montant)
        ligne(db, 'debit', 200, d=date(2026, 10, 15))
        assert calcul(db, 1, '5141', date(2026, 10, 1)) == Decimal('500.00')


def test_releve_annuel_sans_solde_initial_ne_devine_pas_ouverture():
    with db_test() as db:
        etat(db, debut=date(2026, 1, 1), fin=date(2026, 12, 31), initial=None, final=500)
        assert calcul(db, 1, '5141', date(2026, 10, 1)) is None


def test_affichage_protege_controle_independant_et_donnees_existantes():
    js = PAGE.read_text(encoding='utf-8')
    assert 'data.solde_initial == null ? data.solde_initial_suggere' in js
    assert 'Math.round((Number(soldeInitial) + mouvementReleve) * 100) / 100' in js
    assert "soldeFinal === '' ? null : soldeComptableFinal - Number(soldeFinal)" in js
    assert "solde_final: soldeFinal === '' ? null : Number(soldeFinal)" in js
    assert 'Solde final calculé automatiquement' in js
    assert 'contrôle indépendant' in js
    assert 'await rapprochementAPI.importer(compteSelectionne, lignesImport)' in js
    assert 'solde_initial: Number(soldeInitial)' in js
    assert 'soldeFinalCalcule' in js
