"""Régression du correctif 087 : ne pas simplement cacher les montants hors cadre."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSX = (ROOT / 'src/pages/Cloture.jsx').read_text(encoding='utf-8')
CSS = (ROOT / 'src/pages/GrandLivre.module.css').read_text(encoding='utf-8')


def test_087_tableau_ne_depend_plus_de_largeur_intrinseque_html():
    block = JSX.split('Aperçu des à-nouveaux sur {annee + 1}', 1)[1].split('</details>', 1)[0]
    assert '<table' not in block and '<colgroup>' not in block
    assert 'className={`${styles.apercuAnRow} ${styles.apercuAnHeader}`}' in block
    assert 'className={styles.apercuAnDebit}' in block
    assert 'className={styles.apercuAnCredit}' in block
    assert 'minmax(0, 43%)' in CSS
    assert 'grid-template-columns: minmax(0, 72px) minmax(0, 1fr)' in CSS


def test_087_totaux_et_metier_preserves():
    assert 'formatMAD(etat.total_an_debit)' in JSX
    assert 'formatMAD(etat.total_an_credit)' in JSX
    assert 'trouverCompte(l.compte)?.libelle' in JSX
    assert 'etat.apercu_a_nouveaux?.length > 0' in JSX
    assert 'disabled={action || blocage}' in JSX
    assert 'cloturer}' in JSX


def test_087_accessibilite_mobile_montants_identifies():
    assert 'role="table"' in JSX
    assert 'role="columnheader"' in JSX
    assert 'role="rowgroup"' in JSX
    assert JSX.count('className={styles.apercuAnMontantLabel}') >= 4
    assert '.apercuAnMontantLabel { display: block' in CSS
