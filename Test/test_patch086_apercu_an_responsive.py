"""086/087 — les quatre informations d'à-nouveaux restent accessibles sans défilement horizontal."""
from pathlib import Path
from browser_support import chromium_executable
import re
import pytest

ROOT = Path(__file__).resolve().parents[1]
JSX = (ROOT / 'src/pages/Cloture.jsx').read_text(encoding='utf-8')
CSS = (ROOT / 'src/pages/GrandLivre.module.css').read_text(encoding='utf-8')


def test_086_quatre_colonnes_a_nouveaux_sans_scroll_horizontal():
    bloc = JSX.split('Aperçu des à-nouveaux sur {annee + 1}', 1)[1].split('            <div style={{ display:', 1)[0]
    assert 'className={styles.apercuAnContenu}' in bloc
    assert 'className={styles.apercuAnTable}' in bloc
    assert 'overflowX: \'auto\'' not in bloc
    assert 'role="table"' in bloc and 'role="row"' in bloc
    assert all(f'role="columnheader">{name}' in bloc for name in ('Compte', 'Libellé', 'Débit', 'Crédit'))
    assert re.search(r'\.apercuAnRow\s*\{[^}]*display:\s*grid', CSS)
    assert 'overflow-wrap: anywhere' in CSS


def test_086_calculs_et_cloture_non_modifies():
    assert 'etat.apercu_a_nouveaux.map((l, i)' in JSX
    assert 'formatMAD(etat.total_an_debit)' in JSX
    assert 'formatMAD(etat.total_an_credit)' in JSX
    assert 'disabled={action || blocage}' in JSX
    assert 'cloturer}' in JSX


def _html():
    rows = [
        ('34552', 'État - TVA récupérable sur charges', '100,00', '—'),
        ('4455', 'État - TVA facturée', '—', '200,00'),
        ('5141', 'Banques (solde débiteur)', '500,00', '—'),
        ('5161', 'Caisses', '100,00', '—'),
        ('1191', "Résultat de l'exercice", '—', '500,00'),
        ('Total', '', '700,00', '700,00'),
    ]
    def row(account, label, debit, credit):
        klass = 'apercuAnRow apercuAnTotal' if account == 'Total' else 'apercuAnRow'
        return (f'<div class="{klass}" role="row">'
                f'<span class="apercuAnCompte" role="cell">{account}</span>'
                f'<span class="apercuAnLibelle" role="cell">{label}</span>'
                f'<span class="apercuAnDebit" role="cell"><span class="apercuAnMontantLabel">Débit</span>{debit}</span>'
                f'<span class="apercuAnCredit" role="cell"><span class="apercuAnMontantLabel">Crédit</span>{credit}</span>'
                '</div>')
    return ('''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1" />
    <style>*{box-sizing:border-box}body{margin:0}.layout{display:flex;max-width:100vw}
    .sidebar{width:var(--sidebar-size);flex:none}.main{flex:1;min-width:0;padding:16px;overflow-x:hidden}
    .closure{width:100%;max-width:780px;margin:auto}
    .preview{width:100%;border:1px solid #ddd;border-radius:12px;overflow:hidden}
    .preview summary{padding:12px 20px}:root{--border-light:#ddd;--bg-secondary:#f7f7f6;--text-tertiary:#777;--text-secondary:#555}
    ''' + CSS + '''</style></head><body><div class="layout"><aside class="sidebar"></aside><main class="main">
    <div class="closure"><details class="preview" open><summary>Aperçu des à-nouveaux sur 2027 (5 comptes)</summary>
    <div class="apercuAnContenu"><div class="apercuAnTable" role="table">
    <div role="rowgroup"><div class="apercuAnRow apercuAnHeader" role="row">
    <span role="columnheader">Compte</span><span role="columnheader">Libellé</span>
    <span role="columnheader">Débit</span><span role="columnheader">Crédit</span>
    </div></div><div role="rowgroup">''' + ''.join(row(*r) for r in rows) +
    '''</div></div></div></details></div></main></div></body></html>''')


@pytest.mark.parametrize('largeur', [1650, 1024, 768, 640, 390, 320])
def test_086_chromium_quatre_informations_visibles_sans_scroll(largeur):
    playwright = pytest.importorskip('playwright.sync_api')
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chromium_executable(), headless=True, args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 800})
            page.set_content(_html())
            page.evaluate('''(size) => document.documentElement.style.setProperty('--sidebar-size', size)''', '188px' if largeur > 768 else '0px')
            result = page.evaluate('''() => {
                const panel=document.querySelector('.preview').getBoundingClientRect();
                const visible=(el) => {
                    const r=el.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && r.left >= panel.left-1 && r.right <= panel.right+1;
                };
                return {
                    docWidth:document.documentElement.scrollWidth,
                    panelOverflow:document.querySelector('.preview').scrollWidth-document.querySelector('.preview').clientWidth,
                    cells:[...document.querySelectorAll('.apercuAnRow[role="row"]:not(.apercuAnHeader) [role="cell"]')].map(visible),
                    values:[...document.querySelectorAll('.apercuAnTotal [role="cell"]')].map(e => e.textContent.trim()),
                    headerVisible:visible(document.querySelector('.apercuAnHeader')),
                    mobileLabels:[...document.querySelectorAll('.apercuAnMontantLabel')].map(visible),
                };
            }''')
            assert result['docWidth'] <= largeur + 1, (largeur, result)
            assert result['panelOverflow'] <= 1, (largeur, result)
            assert all(result['cells']), (largeur, result)
            assert result['values'] == ['Total', '', 'Débit700,00', 'Crédit700,00']
            if largeur <= 640:
                assert all(result['mobileLabels']), (largeur, result)
            else:
                assert result['headerVisible'], (largeur, result)
        finally:
            browser.close()
