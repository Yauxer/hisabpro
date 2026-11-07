# -*- coding: utf-8 -*-
"""Régressions ciblées du patch 057, sans connexion PostgreSQL."""
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from services.premiers_exercices_service import periodes_a_preparer  # noqa: E402


def _source(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_selection_2025_prepare_2025_sans_recreer_2026():
    first = SimpleNamespace(annee=2026, date_debut=date(2026, 1, 1))
    assert periodes_a_preparer(2025, first) == [
        (2025, date(2025, 1, 1), date(2025, 12, 31)),
    ]
    assert periodes_a_preparer(2025, SimpleNamespace(annee=2025, date_debut=date(2025, 1, 1))) == []


def test_exercice_court_precedant_exercice_decale():
    first = SimpleNamespace(annee=2027, date_debut=date(2026, 7, 1))
    assert periodes_a_preparer(2025, first) == [
        (2025, date(2025, 1, 1), date(2025, 12, 31)),
        (2026, date(2026, 1, 1), date(2026, 6, 30)),
    ]


def test_premier_exercice_2026_cree_sur_nouvelle_societe():
    assert periodes_a_preparer(2026, annee_courante=2026) == [
        (2026, date(2026, 1, 1), date(2026, 12, 31)),
    ]


def test_refuse_de_decaler_premier_exercice_apres_historique():
    first = SimpleNamespace(annee=2025, date_debut=date(2025, 1, 1))
    with pytest.raises(ValueError, match="Impossible d’avancer"):
        periodes_a_preparer(2026, first)


def test_limite_preparation_et_bornes_de_reference():
    with pytest.raises(ValueError, match="40 exercices"):
        periodes_a_preparer(1950, annee_courante=2026)
    with pytest.raises(ValueError, match="comprise entre"):
        periodes_a_preparer(1800, annee_courante=2026)


def test_endpoint_parametres_cree_les_exercices_transactionnellement():
    src = _source("hisabpro-backend/routers/societe.py")
    bloc = src[src.index("def modifier_ma_societe"):src.index('@router.get("/modules")')]
    assert "periodes_a_preparer(debut_demande, plus_ancien)" in bloc
    assert "verifier_chevauchement(db, societe.id, debut, fin)" in bloc
    assert "ensure_exercice(db, societe.id, annee, debut, fin)" in bloc
    assert bloc.index("ensure_exercice(db, societe.id, annee, debut, fin)") < bloc.index("db.commit()")
    assert 'raise HTTPException(409' in bloc


def test_nouvelle_societe_cree_modules_plan_et_exercice_meme_transaction():
    src = _source("hisabpro-backend/routers/multi_societes.py")
    bloc = src[src.index("def creer_societe"):src.index('@router.post("/{societe_id}/inviter")')]
    assert 'current_user = Depends(requiert_ecriture)' in src
    assert 'exercice_debut=date.today().year' in bloc
    assert 'assurer_plan_societe(db, societe.id)' in bloc
    assert 'ensure_exercice(db, societe.id, date.today().year)' in bloc
    assert bloc.index('db.add(liaison)') < bloc.index('assurer_plan_societe') < bloc.index('db.commit()')
    assert '"role":         role' in src


def test_frontend_synchronise_annee_et_traite_erreurs_creation_changement():
    selecteur = _source("src/components/SelecteurSociete.jsx")
    params = _source("src/pages/Parametres.jsx")
    ex = _source("src/data/ExerciceContext.jsx")
    modules = _source("src/data/ModulesContext.jsx")
    for fragment in ('role="alert"', 'formatErreurAPI(body.detail)',
                     "localStorage.removeItem('hisabpro_exercice')",
                     'setRole(data.role)', 'await switcher(data.id)'):
        assert fragment in selecteur
    assert 'await rechargerExercices(nouveauDebut)' in params
    assert 'type="number" min="1900" max="2200"' in params
    assert 'setAnneeState(ancienne =>' in ex
    assert 'throw new Error(formatErreurAPI(error.detail))' in modules
