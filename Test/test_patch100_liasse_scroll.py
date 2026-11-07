from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'src/pages/LiasseFiscale.module.css').read_text(encoding='utf-8')


def test_liasse_uses_layout_as_single_vertical_scroll_owner():
    assert '.page{display:flex;flex-direction:column;min-height:100%}' in CSS
    assert 'height:100%;min-height:0' not in CSS
    assert '.content{padding:16px 24px 28px;display:flex;flex-direction:column;gap:14px;overflow:visible}' in CSS
    assert 'overflow-y:auto' not in CSS


def test_liasse_tables_only_own_horizontal_scroll():
    assert '.tableWrap{overflow-x:auto;overflow-y:visible;max-width:100%}' in CSS
    assert '.tableWrap{overflow:auto;' not in CSS
