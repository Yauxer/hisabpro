"""084 — Inventaire : les montants visibles et aucun faux mouvement de stock futur."""
from pathlib import Path
from browser_support import chromium_executable
import importlib.util
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'src/pages/LivreInventaire.module.css').read_text(encoding='utf-8')
JSX = (ROOT / 'src/pages/LivreInventaire.jsx').read_text(encoding='utf-8')
SERVICE = ROOT / 'hisabpro-backend/services/livre_inventaire_service.py'


def _service():
    spec = importlib.util.spec_from_file_location('livre_inventaire_patch084', SERVICE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(('inventaire', 'nb_articles', 'attendu'), [
    (False, 0, False),  # Société ne vendant que des prestations : pas de fausse alerte.
    (False, 2, True),   # Articles stockables sans photographie de clôture : mise en garde.
    (True, 2, False),   # Inventaire de clôture disponible : photographie figée.
])
def test_084_avertissement_stock_depend_de_l_aperçu_et_non_de_mouvements_supposes(
    inventaire, nb_articles, attendu,
):
    service = _service()
    assert service.stock_apercu_historique_limite(inventaire, nb_articles) is attendu


def test_084_texte_ne_pretend_plus_avoir_detecte_des_mouvements_ulterieurs():
    assert 'Des mouvements de stock postérieurs à la fin de cet exercice existent.' not in JSX
    assert 'Sans inventaire physique de clôture validé' in JSX
    assert 'stock_apercu_historique_limite(bool(inv), len(lignes))' in SERVICE.read_text(encoding='utf-8')
    assert 'disabled={archivage || !ctrl.archivable}' in JSX  # Aucun contournement de l'archivage.


def test_084_bilan_et_cpc_sur_une_colonne_et_montant_reserve():
    assert re.search(r'\.grid2\s*\{[^}]*grid-template-columns\s*:\s*minmax\(0,1fr\)', CSS)
    assert re.search(r'\.grid2 \.tableau th:last-child\s*\{\s*width:150px', CSS)
    assert 'className={styles.grid2}' in JSX
    assert JSX.index('<h2>Bilan — Actif</h2>') < JSX.index('<h2>Bilan — Passif</h2>')
    assert 'styles.num}>{formatMAD(type === \'net\' ? r.net : r.montant)}' in JSX


def test_084_chromium_montants_visibles_sans_defilement_horizontal():
    playwright = pytest.importorskip('playwright.sync_api')
    html = '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>*,*::before,*::after{box-sizing:border-box}body{margin:0}
    .layout{display:flex;max-width:100vw}.sidebar{width:188px;flex:none}
    .main{flex:1;min-width:0;padding:16px;overflow-x:hidden}
    :root{--bg-secondary:#f6f6f6;--bg-primary:white;--text-primary:#222;
    --text-tertiary:#777;--text-secondary:#555;--border-light:#ddd}
    ''' + CSS + '''</style></head><body><div class="layout"><aside class="sidebar"></aside>
    <main class="main"><div class="page"><div class="grid2">
      <section class="card" id="actif"><h2>Bilan — Actif</h2>
       <table class="tableau"><thead><tr><th>Rubrique</th><th class="num">Montant (MAD)</th></tr></thead>
       <tbody><tr><td>Banques, trésorerie et disponibilités</td><td class="num">500,00</td></tr>
       <tr><td>TVA récupérable</td><td class="num">100,00</td></tr></tbody></table></section>
      <section class="card" id="passif"><h2>Bilan — Passif</h2>
       <table class="tableau"><thead><tr><th>Rubrique</th><th class="num">Montant (MAD)</th></tr></thead>
       <tbody><tr><td>Résultat de l'exercice</td><td class="num">500,00</td></tr>
       <tr><td>État créditeur</td><td class="num">200,00</td></tr></tbody></table></section>
      <section class="card large" id="cpc"><h2>CPC</h2>
       <table class="tableau"><thead><tr><th>Rubrique</th><th class="num">Montant (MAD)</th></tr></thead>
       <tbody><tr><td>Résultat</td><td class="num">500,00</td></tr></tbody></table></section>
    </div></div></main></div></body></html>'''
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True, args=['--no-sandbox'])
        except Exception as exc:
            pytest.skip(f'Chromium indisponible : {exc}')
        try:
            for width in (1650, 1024, 768, 390):
                page = browser.new_page(viewport={'width': width, 'height': 800})
                page.set_content(html if width > 768 else html.replace('.sidebar{width:188px;flex:none}', '.sidebar{width:0;flex:none}'))
                values = page.evaluate('''() => {
                  const main=document.querySelector('.main').getBoundingClientRect();
                  const cards=[...document.querySelectorAll('.grid2 > .card')].map(e=>e.getBoundingClientRect());
                  const nums=[...document.querySelectorAll('td.num')].map(e=>e.getBoundingClientRect());
                  return {width:document.documentElement.scrollWidth,main:[main.left,main.right],
                     cards:cards.map(e=>[e.left,e.right,e.top,e.bottom]),
                     nums:nums.map(e=>[e.left,e.right,e.width]),
                     cardOverflows:[...document.querySelectorAll('.grid2 > .card')].map(e=>e.scrollWidth-e.clientWidth)};
                }''')
                assert values['width'] <= width+1, (width, values)
                assert values['cards'][1][2] >= values['cards'][0][3]-1, (width, values)
                assert values['cards'][2][2] >= values['cards'][1][3]-1, (width, values)
                assert all(x <= 1 for x in values['cardOverflows']), (width, values)
                assert all(r[0] >= values['main'][0] and r[1] <= values['main'][1] and r[2] >= 90 for r in values['nums']), (width, values)
                page.close()
        finally:
            browser.close()
