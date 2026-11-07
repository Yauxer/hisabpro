"""Passage de minuit entre collecte et exécution, ORM mémoire exclusivement."""
import datetime
import pytest
import test_effets_dates_operations as scenario
from test_effets_dates_operations import db


@pytest.mark.parametrize('action', ['remettre', 'rejeter'])
def test_refus_futur_reste_un_vrai_futur_apres_collecte(db, monkeypatch, action):
    test = scenario.test_date_avant_reception_ou_future_refusee_sans_mutation
    cases = next(mark.args[1] for mark in test.pytestmark
                 if mark.name == 'parametrize' and mark.args[0] == 'jour')
    future = cases[1]
    # Ancien banc : la date future calculée à l'import devient aujourd'hui.
    # Banc corrigé : identifiant « demain », résolu au moment du test.
    today = future if isinstance(future, datetime.date) else datetime.date(2026, 10, 11)
    original_datetime = datetime.datetime

    class DateApresMinuit(datetime.date):
        @classmethod
        def today(cls):
            return today

    class HorlogeApresMinuit(original_datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(today.year, today.month, today.day, 0, 1, tzinfo=tz)

    monkeypatch.setattr(scenario, 'date', DateApresMinuit)
    monkeypatch.setattr(datetime, 'datetime', HorlogeApresMinuit)
    test(db, action, future)
