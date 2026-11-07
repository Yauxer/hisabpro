"""066 — non-régression : les lignes d'une facture/avoir restent visibles en consultation."""
from pathlib import Path
from browser_support import chromium_executable
import asyncio
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_detail_facture_et_avoir_affichent_toutes_les_valeurs():
    invoice = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
    credit = (ROOT / 'src/pages/Avoirs.jsx').read_text(encoding='utf-8')
    css = (ROOT / 'src/pages/Factures.module.css').read_text(encoding='utf-8')
    css_credit = (ROOT / 'src/pages/Avoirs.module.css').read_text(encoding='utf-8')
    assert 'className={styles.detailLignes} role="list"' in invoice
    assert 'className={styles.detailLigne} role="listitem"' in invoice
    for label in ('Description', 'Quantité', 'Prix unitaire HT', 'TVA', 'Montant HT'):
        assert f'>{label}</span>' in invoice
    assert 'className={styles.detailLignesAvoir} role="list"' in credit
    assert 'className={styles.detailLigneAvoir} role="listitem"' in credit
    for label in ('Article', 'Quantité', 'Montant TTC'):
        assert f'>{label}</span>' in credit
    assert '.detailLigne {' in css and 'repeat(2, minmax(0, 1fr))' in css
    assert '.detailLigneAvoir {' in css_credit
    assert '.detailLigneValeur' in css and 'overflow-wrap: anywhere' in css


def _fixture(kind):
    global_css = (ROOT / 'src/styles/global.css').read_text(encoding='utf-8')
    modal_css = (ROOT / 'src/components/Modal.module.css').read_text(encoding='utf-8')
    if kind == 'facture':
        css = (ROOT / 'src/pages/Factures.module.css').read_text(encoding='utf-8')
        content = '''<div class="detailMeta"><div><span class="metaLabel">Tiers</span><strong>ATLAS CONSEIL SARL</strong></div></div>
        <div class="detailLignes" role="list" aria-label="Lignes de la facture">
        <div class="detailLigne" role="listitem">
        <div class="detailLigneChamp detailLigneDescription"><span class="detailLigneLabel">Description</span><strong class="detailLigneValeur">Mission de conseil Novembre</strong></div>
        <div class="detailLigneChamp"><span class="detailLigneLabel">Quantité</span><span class="detailLigneValeur">1</span></div>
        <div class="detailLigneChamp"><span class="detailLigneLabel">Prix unitaire HT</span><span class="detailLigneValeur">10 000,00 MAD</span></div>
        <div class="detailLigneChamp"><span class="detailLigneLabel">TVA</span><span class="detailLigneValeur">20%</span></div>
        <div class="detailLigneChamp"><span class="detailLigneLabel">Montant HT</span><strong class="detailLigneValeur">10 000,00 MAD</strong></div>
        </div></div><div class="totauxFacture"><div class="totauxLigne"><span>Total HT</span><span>10 000,00 MAD</span></div><div class="totauxLigne totauxTTC"><span>Total TTC</span><span>12 000,00 MAD</span></div></div>'''
        return '<!doctype html><html lang="fr"><meta charset="utf-8"><style>'+global_css+modal_css+css+'</style><body><div class="overlay"><div class="modal md"><div class="header"><span class="titre">Facture FA-2025-001</span></div><div class="corps">'+content+'</div></div></div></body></html>'
    css = (ROOT / 'src/pages/Avoirs.module.css').read_text(encoding='utf-8')
    content = '''<div class="detailLignesAvoir" role="list"><div class="detailLigneAvoir" role="listitem">
    <div class="detailDescriptionAvoir"><span class="detailLabelAvoir">Article</span><strong>Produit de démonstration et retour de matériel</strong><small>Quantité / retour</small></div>
    <div class="detailValeurAvoir"><span class="detailLabelAvoir">Quantité</span>2</div>
    <div class="detailValeurAvoir"><span class="detailLabelAvoir">Montant TTC</span>12 000,00 MAD</div>
    </div></div>'''
    return '<!doctype html><html lang="fr"><meta charset="utf-8"><style>'+global_css+css+'</style><body><div style="max-width:360px;width:100%;padding:18px;background:white">'+content+'</div></body></html>'


async def _verify_in_chromium():
    from playwright.async_api import async_playwright
    chromium = chromium_executable()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=chromium, args=['--no-sandbox'])
        try:
            for kind in ('facture', 'avoir'):
                for width in (1440, 768, 620, 390, 320):
                    page = await browser.new_page(viewport={'width': width, 'height': 800})
                    try:
                        await page.set_content(_fixture(kind))
                        out = await page.evaluate('''() => {
                          const container = document.querySelector('.corps') || document.querySelector('body > div');
                          const visible = [...document.querySelectorAll('[role="listitem"]')].flatMap(row =>
                            [...row.querySelectorAll('*')].filter(n => n.childElementCount === 0 && n.textContent.trim())
                            .map(n => ({value:n.textContent.trim(), rect:n.getBoundingClientRect()})));
                          const bounds = container.getBoundingClientRect();
                          return { client:container.clientWidth,scroll:container.scrollWidth,
                            off:visible.filter(v=>v.rect.left < bounds.left-1 || v.rect.right>bounds.right+1)
                              .map(v=>({value:v.value,left:v.rect.left,right:v.rect.right,bounds:[bounds.left,bounds.right]})),
                            text:visible.map(v=>v.value).concat([...document.querySelectorAll('.detailValeurAvoir')].map(n=>n.textContent.trim())) };
                        }''')
                        assert out['scroll'] <= out['client'] + 1, (kind,width,out)
                        assert not out['off'], (kind,width,out)
                        for expected in (('Description','Quantité','Prix unitaire HT','TVA','Montant HT','10 000,00 MAD') if kind=='facture' else ('Article','Quantité','Montant TTC','12 000,00 MAD')):
                            assert any(expected in value for value in out['text']), (kind,width,out)
                    finally:
                        await page.close()
        finally:
            await browser.close()


def test_066_chromium_affiche_les_details_sans_scroll_lateral():
    pytest.importorskip('playwright.async_api')
    if not (chromium_executable()):
        pytest.skip('Chromium absent')
    asyncio.run(_verify_in_chromium())
