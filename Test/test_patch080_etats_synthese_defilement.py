"""080 — Le CPC, le bilan, l'ESG et le tableau de financement restent déroulables."""
from pathlib import Path
from browser_support import chromium_executable
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'src/pages/Bilan.module.css').read_text(encoding='utf-8')
JSX = (ROOT / 'src/pages/Bilan.jsx').read_text(encoding='utf-8')


def test_080_zone_defilante_et_cartes_non_retrecies():
    assert re.search(r'\.page\s*\{[^}]*min-height:\s*0', CSS)
    assert re.search(r'\.content\s*\{[^}]*min-height:\s*0[^}]*overflow-y:\s*auto', CSS)
    assert re.search(r'\.card\s*\{[^}]*flex-shrink:\s*0', CSS)
    assert re.search(r'\.bilanColonne\s*\{[^}]*flex-shrink:\s*0', CSS)
    assert '<div className={styles.content}>' in JSX
    assert '<div className={styles.card}>' in JSX
    for onglet in ('cpc', 'bilan', 'esg', 'tf'):
        assert f"onglet === '{onglet}'" in JSX


@pytest.mark.parametrize('kind', ['cpc', 'bilan', 'esg', 'tf'])
def test_080_toutes_les_sections_accessibles_au_scroll(kind):
    playwright = pytest.importorskip('playwright.sync_api')
    rows = ''.join(
        f'<tr><td>Rubrique longue de test {index}</td><td>{index},00 MAD</td></tr>'
        for index in range(55)
    )
    table = f'<table class="table"><tbody>{rows}<tr id="last"><td>DERNIÈRE RUBRIQUE</td><td>500,00 MAD</td></tr></tbody></table>'
    # Même structure flex que Layout (viewport bloqué) et Bilan (page à 100 %, carte à overflow:hidden).
    block = f'<div class="card"><div class="cardHeader">{kind.upper()}</div>{table}</div>'
    if kind in ('bilan', 'esg', 'tf'):
        block = '<div class="bilanColonne">' + block + '<div class="card"><div class="cardHeader">Suite du document</div><p id="tail">FIN DE L’ÉTAT</p></div></div>'
    html = ('''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>*{box-sizing:border-box}body{margin:0}.shell{display:flex;height:100vh;overflow:hidden}
.sidebar{width:188px;flex:none}.main{display:flex;flex-direction:column;flex:1;min-width:0;height:100vh;overflow:hidden}
.nav{height:44px;flex:none}.shellContent{flex:1;min-width:0;min-height:0;overflow:auto}
''' + CSS + '''</style></head><body><div class="shell"><aside class="sidebar"></aside><div class="main">
<header class="nav">Sélection exercice</header><main class="shellContent"><div class="page"><header class="topbar">États de synthèse</header>
<div class="content"><div class="sourceMeta">5 écritures validées</div><div class="onglets">Bilan CPC ESG Tableau de financement</div>'''
        + block + '</div></div></main></div></div></body></html>')
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True, args=['--no-sandbox'])
        except Exception as exc:
            pytest.skip(f'Chromium indisponible : {exc}')
        try:
            for width in (1648, 1024, 768, 390):
                page = browser.new_page(viewport={'width': width, 'height': 900})
                page.set_content(html)
                start = page.evaluate('''() => {
                    const el = document.querySelector('.content');
                    const card = document.querySelector('.card');
                    return {client:el.clientHeight,scroll:el.scrollHeight,cardHeight:card.clientHeight,cardScroll:card.scrollHeight};
                }''')
                assert start['scroll'] > start['client'] + 100, f'{kind} {width}px : le contenu ne défile pas : {start}'
                assert start['cardHeight'] >= start['cardScroll'] - 2, f'{kind} {width}px : carte rognée : {start}'
                page.eval_on_selector('.content', 'el => {el.scrollTop = el.scrollHeight;}')
                end = page.evaluate('''() => {
                    const scroll = document.querySelector('.content');
                    const last = document.querySelector('#last').getBoundingClientRect();
                    const tail = document.querySelector('#tail')?.getBoundingClientRect();
                    const content = scroll.getBoundingClientRect();
                    return {top:scroll.scrollTop, lastBottom:last.bottom, tailBottom:tail?.bottom,
                            contentBottom:content.bottom, contentTop:content.top};
                }''')
                assert end['top'] > 100, f'{kind} {width}px : scrollTop bloqué : {end}'
                target = end['tailBottom'] if end['tailBottom'] is not None else end['lastBottom']
                assert end['contentTop'] < target <= end['contentBottom'] + 2, f'{kind} {width}px : bas inaccessible : {end}'
                page.close()
        finally:
            browser.close()
