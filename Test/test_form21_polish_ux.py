from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_tiers_picker_is_reusable_and_searches_business_keys():
    src = read('src/components/TiersPicker.jsx')
    assert "export default function TiersPicker" in src
    for key in ['t.nom', 't.ice', 't.compte_client', 't.compte_fournisseur', 't.ville']:
        assert key in src
    assert "ArrowDown" in src and "ArrowUp" in src and "Escape" in src
    assert 'role="combobox"' in src and 'role="listbox"' in src


def test_tiers_picker_is_used_in_core_commercial_forms():
    for rel in ['src/pages/Commercial.jsx', 'src/pages/Factures.jsx', 'src/pages/Acomptes.jsx']:
        src = read(rel)
        assert "components/TiersPicker.jsx" in src
        assert '<TiersPicker' in src


def test_facture_search_is_unified_not_split_by_account_toggle():
    src = read('src/pages/Factures.jsx')
    assert 'rechercheCompte' not in src
    assert 'Recherche par nom, ICE, compte comptable ou ville.' in src


def test_devis_transform_actions_have_clear_hierarchy():
    src = read('src/pages/Commercial.jsx')
    css = read('src/pages/Commercial.module.css')
    assert 'Créer BC' in src
    assert 'Créer facture' in src
    assert 'btnTransformSecondary' in src
    assert 'btnTransformPrimary' in src
    assert "background: 'var(--green)'" not in src
    assert '.btnTransformPrimary' in css
    assert '.btnTransformSecondary' in css


def test_picker_styles_are_global_and_readable():
    css = read('src/styles/forms.css')
    for cls in [
        '.hp-tiers-picker__menu', '.hp-tiers-picker__item',
        '.hp-tiers-picker__identity', '.hp-tiers-picker__badge',
        '.hp-tiers-picker__create'
    ]:
        assert cls in css
