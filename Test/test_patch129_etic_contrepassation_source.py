from datetime import date, datetime
from types import SimpleNamespace
import pytest
from services import etic_service as etic


@pytest.mark.parametrize('jour', [date(2026, 12, 31), date(2027, 1, 1)])
@pytest.mark.parametrize('origine', [2, 99, None])
def test_date_annulation_ne_masque_pas_un_lien_incompatible(jour, origine):
    row = SimpleNamespace(statut='annule', ecriture_id=2, ecriture_annulation_id=3,
                          date_annulation=datetime(2027, 2, 1))
    inverse = SimpleNamespace(date=jour, contrepassation_de_id=origine)
    active, motif = etic._source_active_a_cloture_etic(row, date(2026, 12, 31), {3: inverse})
    if origine == 2:
        assert active == (jour.year == 2027)
        assert motif is None
    else:
        assert not active
        assert "écriture d'origine" in motif
