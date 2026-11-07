from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def txt(path):
    return path.read_text(encoding="utf-8")


def test_design_system_formulaire_charge_globalement():
    main = txt(SRC / "main.jsx")
    css = txt(SRC / "styles" / "forms.css")
    assert "./styles/forms.css" in main
    assert ".hp-form-section" in css
    assert ".hp-action-bar" in css
    assert ".hp-advanced" in css
    assert "[data-form-surface]" in css
    assert "[data-form-page]" in css


def test_modales_exposent_un_scope_de_formulaire_accessible():
    modal = txt(SRC / "components" / "Modal.jsx")
    assert 'role="dialog"' in modal
    assert 'aria-modal="true"' in modal
    assert "data-form-surface" in modal


def test_formulaires_critiques_utilisent_la_nouvelle_ux():
    for name in ["Tiers.jsx", "Articles.jsx", "Factures.jsx", "Commercial.jsx", "Acomptes.jsx"]:
        content = txt(SRC / "pages" / name)
        assert "FormSection" in content, name
        assert "ActionBar" in content, name


def test_facture_est_reellement_restructuree():
    jsx = txt(SRC / "pages" / "Factures.jsx")
    assert 'title="Document & tiers"' in jsx
    assert 'title="Lignes de facturation"' in jsx
    assert 'title="Montants & options"' in jsx
    assert 'title="Options commerciales & fiscales"' in jsx
    assert "Enregistrer en brouillon" in jsx
    assert "Valider & comptabiliser immédiatement" in jsx


def test_toutes_les_pages_de_saisie_sont_dans_un_scope_ux():
    # Une page comportant des champs doit soit vivre dans une Modal (scope automatique),
    # soit être explicitement annotée data-form-page. Cela évite les écrans oubliés.
    ignores = set()
    for path in (SRC / "pages").glob("*.jsx"):
        content = txt(path)
        if not re.search(r"<(input|select|textarea)\b", content):
            continue
        assert "data-form-page" in content or "<Modal" in content, path.name
