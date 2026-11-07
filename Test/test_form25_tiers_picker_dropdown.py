from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_form_section_does_not_clip_tiers_picker():
    css = (ROOT / 'src/styles/forms.css').read_text(encoding='utf-8')
    section = css.split('.hp-form-section {', 1)[1].split('}', 1)[0]
    assert 'overflow: visible' in section
    assert ':has(.hp-tiers-picker.is-open)' in css


def test_tiers_picker_exposes_open_state_on_root():
    src = (ROOT / 'src/components/TiersPicker.jsx').read_text(encoding='utf-8')
    assert "hp-tiers-picker ${ouvert ? 'is-open' : ''}" in src
