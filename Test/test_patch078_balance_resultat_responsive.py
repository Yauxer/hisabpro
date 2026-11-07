"""078 — Balance Résultat : aucun tableau ni montant tronqué sur écrans étroits."""
from pathlib import Path
from browser_support import chromium_executable
import re
import shutil
import subprocess
import pytest
from jsx_syntax import assert_jsx

ROOT = Path(__file__).resolve().parents[1]
JSX = (ROOT / 'src/pages/Balances.jsx').read_text(encoding='utf-8')
CSS = (ROOT / 'src/pages/Balances.module.css').read_text(encoding='utf-8')


def test_078_grille_intrinseque_et_deux_tableaux_responsives():
    resultat = JSX.split('function BalanceResultat(', 1)[1].split('// ── Onglet 5', 1)[0]
    assert 'className={styles.resultatGrille}' in resultat
    assert resultat.count('className={styles.resultatPanneau}') == 2
    assert resultat.count('styles.resultatTable') == 2
    assert 'className={styles.resultatKpis}' in resultat
    assert re.search(r'\.resultatGrille\s*\{[^}]*grid-template-columns:minmax\(0,1fr\)', CSS)
    assert re.search(r'\.resultatPanneau\s*\{[^}]*min-width:0', CSS)
    assert re.search(r'\.resultatTable\s*\{[^}]*table-layout:fixed', CSS)
    assert '@media (max-width:650px)' in CSS
    # Ne pas altérer les formules de l'état et le calcul de la TVA.
    assert 'const resultat      = totalProduits - totalCharges' in resultat
    assert 'Résultat comptable : bénéfice' in resultat
    assert 'Bénéfice net' not in resultat  # L’IS n’a pas encore été comptabilisé.


@pytest.mark.skipif(not shutil.which('node'), reason='Node absent')
def test_078_jsx_syntaxe():
    assert_jsx(['src/pages/Balances.jsx'])


def test_078_rendu_chromium_ordinateur_tablette_mobile():
    playwright = pytest.importorskip('playwright.sync_api')
    html = '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>*,*::before,*::after{box-sizing:border-box}body{margin:0}.page{display:flex;min-width:0}
    .side{width:188px;flex:none}.content{flex:1;min-width:0;padding:16px 24px;overflow-x:hidden}
    .card{overflow:hidden;padding:16px}.table{width:100%;border-collapse:collapse;font-size:12px}
    .table td,.table th{padding:8px 10px}.kpiCard{padding:14px 18px;border:1px solid #ddd}
    ''' + CSS + '''</style></head><body><div class="page"><div class="side"></div><main class="content">
    <div class="card"><div class="resultatKpis"><div class="kpiCard">500,00 MAD</div>
    <div class="kpiCard">1.000,00 MAD</div><div class="kpiCard">500,00 MAD</div></div>
    <div class="resultatGrille">
    <div class="resultatPanneau" data-panel="charges"><div class="sectionTitre">CHARGES</div>
    <table class="table resultatTable"><thead><tr><th>N° Compte</th><th>Intitulé</th><th>Montant</th></tr></thead>
    <tbody><tr><td>6126</td><td>Achats de travaux, études et prestations de service</td><td>500,00</td></tr></tbody>
    <tfoot><tr><td colspan="2">TOTAL CHARGES</td><td>500,00 MAD</td></tr></tfoot></table></div>
    <div class="resultatPanneau" data-panel="produits"><div class="sectionTitre">PRODUITS</div>
    <table class="table resultatTable"><thead><tr><th>N° Compte</th><th>Intitulé</th><th>Montant</th></tr></thead>
    <tbody><tr><td>7124</td><td>Ventes de services produits au Maroc</td><td>1.000,00</td></tr></tbody>
    <tfoot><tr><td colspan="2">TOTAL PRODUITS</td><td>1.000,00 MAD</td></tr></tfoot></table></div>
    </div></div></main></div></body></html>'''
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True, args=['--no-sandbox'])
        except Exception as exc:
            pytest.skip(f'Chromium non disponible : {exc}')
        try:
            for viewport in (1648, 1100, 1024, 768, 390):
                page = browser.new_page(viewport={'width': viewport, 'height': 900})
                page.set_content(html)
                result = page.evaluate('''() => {
                  const outer=document.querySelector('.card').getBoundingClientRect();
                  const panels=[...document.querySelectorAll('[data-panel]')].map(e=>e.getBoundingClientRect());
                  const montant=[...document.querySelectorAll('[data-panel] table th:last-child')].map(e=>e.getBoundingClientRect());
                  const tds=[...document.querySelectorAll('[data-panel] tbody td:last-child')].map(e=>e.getBoundingClientRect());
                  return { width:innerWidth, docWidth:document.documentElement.scrollWidth,
                    outer:[outer.left,outer.right],panels:panels.map(r=>[r.left,r.right,r.width]),
                    montant:montant.map(r=>[r.left,r.right,r.width]),
                    tds:tds.map(r=>[r.left,r.right,r.width]),
                    columns:getComputedStyle(document.querySelector('.resultatGrille')).gridTemplateColumns.split(' ').length }
                }''')
                assert result['docWidth'] <= viewport + 1, f'{viewport}px : scroll horizontal global {result}'
                assert all(r[0] >= result['outer'][0]-1 and r[1] <= result['outer'][1]+1 for r in result['panels']), f'{viewport}px : panneau rogné {result}'
                assert all(r[0] >= result['outer'][0]-1 and r[1] <= result['outer'][1]+1 and r[2] >= 65 for r in result['montant']+result['tds']), f'{viewport}px : montant tronqué {result}'
                assert result['columns'] == 1, f'{viewport}px : mauvaise disposition {result}'
                page.close()
        finally:
            browser.close()
