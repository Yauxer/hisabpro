# Test autonome Patch 04B — ne nécessite pas PostgreSQL.
from datetime import date
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.exercices_utils import generer_periodes_dates


def main():
    p = generer_periodes_dates(date(2026, 1, 1), date(2026, 12, 31))
    assert len(p) == 12
    assert p[0]["date_debut"] == date(2026, 1, 1)
    assert p[-1]["date_fin"] == date(2026, 12, 31)

    court = generer_periodes_dates(date(2026, 7, 15), date(2026, 12, 31))
    assert len(court) == 6
    assert court[0]["date_debut"] == date(2026, 7, 15)
    assert court[0]["date_fin"] == date(2026, 7, 31)

    fev = generer_periodes_dates(date(2024, 2, 1), date(2024, 2, 29))
    assert fev[0]["date_fin"] == date(2024, 2, 29)

    try:
        generer_periodes_dates(date(2026, 12, 31), date(2026, 1, 1))
        raise AssertionError("dates inversées acceptées")
    except ValueError:
        pass

    print("OK — 4 tests Exercices/Périodes Patch 04B")


if __name__ == '__main__':
    main()
