"""Provenance : identité canonique, métadonnées et diagnostics purs."""
from copy import deepcopy
import json

import pytest
from pydantic import ValidationError
from services.paie_referentiel_service import ConsignationPaie, SourcePaie, diagnostics_parametres, empreinte_parametres


def parametres():
    return {'bareme_ir': [], 'taux_cotisations': [], 'deductions_ir': []}


def test_empreinte_identite_annee_ordre_et_source_preserves():
    p = parametres()
    avant = deepcopy(p)
    empreinte = empreinte_parametres(1, 2026, p)
    assert empreinte != empreinte_parametres(2, 2026, p)
    assert empreinte != empreinte_parametres(1, 2025, p)
    assert empreinte == empreinte_parametres(1, 2026, dict(reversed(list(p.items()))))
    assert len(empreinte) == 64 and p == avant
    assert diagnostics_parametres(p) == []  # Une liste absente ne devient pas un taux inventé.


@pytest.mark.parametrize('valeur', ['NaN', 'Infinity', '-Infinity', -1, 1.5, True, None])
def test_diagnostics_taux_non_numeriques_et_bornes(valeur):
    p = parametres()
    p['taux_cotisations'] = [{'id': 7, 'taux_sal': valeur, 'taux_pat': 0, 'plafond': None}]
    avant = deepcopy(p)
    assert diagnostics_parametres(p)
    assert p == avant
    json.dumps(p, allow_nan=False)  # Marques historiques JSON sûres.


@pytest.mark.parametrize('url', ['http://example.com/a', 'file:///etc/passwd', 'https://u:p@example.com/a', 'https://example.com/a b'])
def test_sources_refusent_urls_dangereuses_sans_telechargement(url):
    with pytest.raises(ValidationError):
        SourcePaie(titre='Référence', url=url)


def test_contrat_ne_recoit_pas_taux_statut_ni_societe_du_client():
    corps = {'empreinte_attendue': 'a' * 64, 'sources': [{'titre': 'Source partielle', 'url': 'https://www.acaps.ma/'}]}
    data = ConsignationPaie(**corps)
    assert data.sources[0].date_effet is None
    for extra in ('parametres', 'statut', 'societe_id', 'version'):
        with pytest.raises(ValidationError):
            ConsignationPaie(**corps, **{extra: 1})
    with pytest.raises(ValidationError):
        ConsignationPaie(empreinte_attendue='a' * 64, sources=[corps['sources'][0]] * 21)


def test_metadonnees_facultatives_sans_dates_inventees():
    for url in (None, ''):
        source = SourcePaie(titre='Pièce consultée', url=url, date_effet='', date_consultation=None, article='')
        assert source.url is None
        assert source.date_effet is None and source.date_consultation is None
