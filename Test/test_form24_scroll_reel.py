from pathlib import Path


def test_situation_cards_do_not_shrink_and_clip_rows():
    css = Path('src/pages/SituationFinanciere.module.css').read_text(encoding='utf-8')
    card = css.split('.card {', 1)[1].split('}', 1)[0]
    assert 'flex-shrink:0' in card.replace(' ', '')
    content = css.split('.content {', 1)[1].split('}', 1)[0]
    assert 'overflow-y:scroll' in content.replace(' ', '') or 'overflow-y:auto' in content.replace(' ', '')


def test_situation_filters_remain_fixed_size():
    css = Path('src/pages/SituationFinanciere.module.css').read_text(encoding='utf-8')
    filters = css.split('.filtersWrap {', 1)[1].split('}', 1)[0]
    assert 'flex-shrink:0' in filters.replace(' ', '')
