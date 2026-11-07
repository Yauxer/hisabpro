"""079 — La balance résultat présente charges puis produits en pleine largeur."""
from pathlib import Path
from browser_support import chromium_executable
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'src/pages/Balances.module.css').read_text(encoding='utf-8')
JSX = (ROOT / 'src/pages/Balances.jsx').read_text(encoding='utf-8')


def test_079_grille_une_colonne_et_logique_metier_preservee():
    assert re.search(r'\.resultatGrille\s*\{[^}]*grid-template-columns\s*:\s*minmax\(0,\s*1fr\)', CSS)
    assert 'repeat(2,minmax(0,1fr))' not in CSS.split('.resultatGrille {', 1)[1].split('}', 1)[0]
    resultat = JSX.split('function BalanceResultat(', 1)[1].split('// ── Onglet 5', 1)[0]
    assert resultat.count('className={styles.resultatPanneau}') == 2
    assert resultat.index('CHARGES (Classe 6)') < resultat.index('PRODUITS (Classe 7)')
    assert 'const resultat      = totalProduits - totalCharges' in resultat
    assert '{formatMAD(totalCharges)} MAD' in resultat
    assert '{formatMAD(totalProduits)} MAD' in resultat


def test_079_chromium_panneaux_empiles_et_montants_visibles():
    playwright = pytest.importorskip('playwright.sync_api')
    html = '''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>*,*::before,*::after{box-sizing:border-box}body{margin:0}
    .page{display:flex;min-width:0}.side{width:188px;flex:none}
    .content{flex:1;min-width:0;padding:16px 24px;overflow-x:hidden}
    .card{overflow:hidden;padding:16px}.table{width:100%;border-collapse:collapse;font-size:12px}
    .table td,.table th{padding:8px 10px}.kpiCard{padding:14px 18px;border:1px solid #ddd}
    ''' + CSS + '''</style></head><body><div class="page"><div class="side"></div>
    <main class="content"><div class="card"><div class="resultatKpis">
    <div class="kpiCard">500,00 MAD</div><div class="kpiCard">1.000,00 MAD</div>
    <div class="kpiCard">500,00 MAD</div></div><div class="resultatGrille">
    <section class="resultatPanneau" data-panel="charges"><div class="sectionTitre">CHARGES (Classe 6)</div>
    <table class="table resultatTable"><thead><tr><th>N° Compte</th><th>Intitulé</th><th>Montant</th></tr></thead>
    <tbody><tr><td>6126</td><td>Achats de travaux, études et prestations de service</td><td>500,00</td></tr></tbody>
    <tfoot><tr><td colspan="2">TOTAL CHARGES</td><td>500,00 MAD</td></tr></tfoot></table></section>
    <section class="resultatPanneau" data-panel="produits"><div class="sectionTitre">PRODUITS (Classe 7)</div>
    <table class="table resultatTable"><thead><tr><th>N° Compte</th><th>Intitulé</th><th>Montant</th></tr></thead>
    <tbody><tr><td>7124</td><td>Ventes de services produits au Maroc</td><td>1.000,00</td></tr></tbody>
    <tfoot><tr><td colspan="2">TOTAL PRODUITS</td><td>1.000,00 MAD</td></tr></tfoot></table>
    </section></div></div></main></div></body></html>'''
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True, args=['--no-sandbox'])
        except Exception as exc:
            pytest.skip(f'Chromium non disponible : {exc}')
        try:
            for width in (1648, 1366, 1100, 768, 390):
                # Mobile browsers hide the app sidebar; use the same layout constraint.
                document = html if width > 768 else html.replace('.side{width:188px;flex:none}', '.side{width:0;flex:none}')
                page = browser.new_page(viewport={'width': width, 'height': 900})
                page.set_content(document)
                metrics = page.evaluate('''() => {
                  const card=document.querySelector('.card').getBoundingClientRect();
                  const panels=[...document.querySelectorAll('[data-panel]')].map(e=>e.getBoundingClientRect());
                  const amounts=[...document.querySelectorAll('[data-panel] tr > :last-child')].map(e=>e.getBoundingClientRect());
                  return {docWidth:document.documentElement.scrollWidth,
                    card:[card.left,card.right],
                    panels:panels.map(r=>[r.left,r.right,r.top,r.bottom]),
                    amounts:amounts.map(r=>[r.left,r.right,r.width]),
                    columns:getComputedStyle(document.querySelector('.resultatGrille')).gridTemplateColumns.split(' ').length};
                }''')
                assert metrics['docWidth'] <= width + 1, (width, metrics)
                assert metrics['columns'] == 1, (width, metrics)
                first, second = metrics['panels']
                assert second[2] > first[3], (width, metrics)  # Produit sous Charges.
                for panel in metrics['panels']:
                    assert panel[0] >= metrics['card'][0]-1 and panel[1] <= metrics['card'][1]+1, (width, metrics)
                for amount in metrics['amounts']:
                    assert amount[0] >= second[0]-1 and amount[1] <= second[1]+1 and amount[2] >= 65, (width, metrics)
                page.close()
        finally:
            browser.close()
