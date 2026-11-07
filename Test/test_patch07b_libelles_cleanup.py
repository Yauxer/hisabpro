from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_formulaire_ne_contient_plus_anciens_prefixes_facture():
    text = (ROOT / 'src' / 'components' / 'FormulaireEcriture.jsx').read_text(encoding='utf-8')
    assert "texte: 'FN° '" not in text
    assert "texte: 'FA° '" not in text
    assert "texte: 'Facture fournisseur — '" in text
    assert "texte: 'Facture client — '" in text


def test_seed_modeles_ne_reintroduit_pas_anciens_prefixes():
    text = (ROOT / 'hisabpro-backend' / 'modeles_ecritures.sql').read_text(encoding='utf-8')
    assert "'FN°{ref} {tiers}'" not in text
    assert "'FA°{ref} {tiers}'" not in text
    assert "'Facture fournisseur — réf. {ref} — {tiers}'" in text
    assert "'Facture client — réf. {ref} — {tiers}'" in text


def test_migration_met_a_jour_modeles_sans_toucher_aux_ecritures():
    text = (ROOT / 'hisabpro-backend' / '016_libelles_justificatifs.sql').read_text(encoding='utf-8')
    assert 'UPDATE modeles_ecritures' in text
    assert 'UPDATE ecritures' not in text
    assert "FN°{ref} {tiers}" in text
    assert "FA°{ref} {tiers}" in text
