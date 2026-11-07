"""HP-SEC-004 — navigation complète facturation/comptabilité, ordinateur et mobile (959).

Chaque écran MVP est ouvert sur une société fictive alimentée : aucun débordement horizontal
de la page, un titre visible, aucune erreur JavaScript ni réponse API 5xx. Les tableaux
larges restent défilables dans leur propre conteneur. Personnel/Paie et CNSS sont hors MVP.
"""
from datetime import date
import json
from pathlib import Path

import pytest

from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application  # noqa: F401
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok

ROOT = Path(__file__).resolve().parents[1]
ECRANS = ['dashboard', 'journal', 'plan-comptes', 'factures', 'avoirs', 'acomptes', 'effets', 'tiers',
          'inventaire', 'articles', 'commercial', 'delais-paiement', 'declaration-tva', 'liasse-fiscale',
          'fiscalite-is', 'grand-livre', 'bilan', 'cpc', 'etic', 'rapprochement', 'lettrage', 'balances',
          'situation', 'immobilisations', 'cloture', 'livre-inventaire', 'parametres']

MESURE = """() => {
  const doc = document.documentElement;
  const titre = [...document.querySelectorAll('h1, h2')].find(h => h.offsetParent !== null && h.textContent.trim());
  return {debordement: doc.scrollWidth - window.innerWidth, titre: titre ? titre.textContent.trim().slice(0, 80) : null};
}"""


def _alimenter(api):
    jour = date.today().isoformat()
    tiers = ok(api.post('/api/tiers', json={'nom': 'Client navigation fictif', 'type': 'client'}), 201)
    f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'date': jour,
        'ras_taux': 0, 'lignes': [{'description': 'Prestation fictive au libellé volontairement long pour tester les colonnes',
                                   'quantite': 3, 'prix_unitaire': 1234.56, 'tva': 20}]}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    e = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
    ok(api.post(f"/api/ecritures/{e['ecriture_id']}/valider"))
    ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': tiers['nom'], 'date': jour,
        'montant': 1000, 'mode': 'cheque', 'reference': 'CHQ-NAV-959', 'comptabiliser': True}), 201)


@pytest.mark.parametrize('largeur,hauteur', [(1366, 768), (390, 844)])
def test_959_navigation_complete_sans_debordement_ni_erreur(application, largeur, hauteur):
    api, email, password = client(application)
    try:
        _alimenter(api)
    finally:
        api.close()
    pw = pytest.importorskip('playwright.sync_api')
    resultats, anomalies = {}, []
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True)
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': hauteur}); page.set_default_timeout(20000)
            page.on('dialog', lambda d: d.dismiss())
            erreurs, serveur = observer(page, application['api_url'])
            connexion(page, application['web_url'], email, password)
            for ecran in ECRANS:
                nb_err, nb_srv = len(erreurs), len(serveur)
                page.goto(f"{application['web_url']}/{ecran}", wait_until='domcontentloaded')
                page.get_by_role('main').wait_for()
                page.wait_for_load_state('networkidle')
                m = page.evaluate(MESURE)
                m.update(erreurs_js=erreurs[nb_err:], erreurs_api=serveur[nb_srv:])
                resultats[ecran] = m
                if m['debordement'] > 1 or not m['titre'] or m['erreurs_js'] or m['erreurs_api']:
                    anomalies.append((ecran, m))
        finally:
            browser.close()
    (ROOT / f'.codex-tests/navigation959_{largeur}.json').write_text(
        json.dumps(resultats, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    assert not anomalies, anomalies
