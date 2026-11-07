from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_layout_has_scroll_fallback():
    css = read('src/components/Layout.module.css')
    assert 'overflow: auto;' in css
    assert 'scrollbar-gutter: stable;' in css
    assert 'overscroll-behavior: contain;' in css


def test_situation_financiere_scrolls_vertically():
    css = read('src/pages/SituationFinanciere.module.css')
    assert 'overflow-y:scroll' in css
    assert 'scrollbar-gutter:stable' in css
    assert 'position:sticky; top:0' in css


def test_heavy_tables_have_scrollable_panes():
    for rel in [
        'src/pages/Factures.module.css',
        'src/pages/Commercial.module.css',
        'src/pages/Journal.module.css',
        'src/pages/GrandLivre.module.css',
    ]:
        css = read(rel)
        assert 'overflow:auto' in css or 'overflow: auto' in css, rel
        assert 'scrollbar-gutter:stable' in css or 'scrollbar-gutter: stable' in css, rel


def test_global_scrollbars_are_visible_but_compact():
    css = read('src/index.css')
    assert 'scrollbar-width: thin;' in css
    assert '*::-webkit-scrollbar' in css
    assert 'width: 9px;' in css
