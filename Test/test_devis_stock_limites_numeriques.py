"""Bornes de représentation numérique, API/JWT sur PostgreSQL nonce."""
import json
from decimal import Decimal

import pytest
from test_devis_stock_diagnostic import application, dossier, etat, diagnostic


@pytest.mark.parametrize('quantite', ['1e1000000', '1e-1000000', True, False, 'NaN', 'Infinity', '-Infinity', -1])
def test_quantite_non_representable_refusee_api_sans_mutation(application, dossier, quantite):
    api, sid, article, service, ids = dossier
    avant = etat(application)
    r = api.post('/api/devis/diagnostic-stock', content=json.dumps({'lignes': [
        {'article_id': article['id'], 'quantite': quantite}]}), headers={'Content-Type': 'application/json'})
    assert r.status_code == 422, r.text
    assert etat(application) == avant


@pytest.mark.parametrize('quantite', [0, '0e-1000000', '1e308', '5e-324'])
def test_quantite_float_finie_ou_zero_canonique_acceptee(application, dossier, quantite):
    api, sid, article, service, ids = dossier
    avant = etat(application)
    sortie = diagnostic(api, [{'article_id': article['id'], 'quantite': quantite}])['articles'][0]
    assert Decimal(str(sortie['quantite_demandee'])) == Decimal(str(float(quantite)))
    assert etat(application) == avant


def test_cumul_extreme_decimal_exact_conserve(application, dossier):
    api, sid, article, service, ids = dossier
    avant = etat(application)
    sortie = diagnostic(api, [{'article_id': article['id'], 'quantite': '1e308'},
                             {'article_id': article['id'], 'quantite': '1e308'}])['articles'][0]
    assert isinstance(sortie['quantite_demandee'], str)
    assert Decimal(sortie['quantite_demandee']) == Decimal('2e308')
    assert Decimal(sortie['quantite_manquante']) == Decimal(2 * 10**308 - 5)
    assert sortie['statut'] == 'a_approvisionner'
    assert etat(application) == avant
