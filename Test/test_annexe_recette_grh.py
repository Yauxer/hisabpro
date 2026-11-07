from generer_annexe_recette_grh import cas, generer


def test_cas_grh_complets_sans_recette_prevalidee():
    items = cas()
    assert len(items) == 26
    assert len({c['id'] for c in items}) == 26
    assert sum(c['statut'] == 'Bloqué' for c in items) == 3
    assert all(c['statut'] in ('Non testé', 'Bloqué') for c in items)
    assert all(c['donnees'] and c['actions'] and c['attendu'] and c['ecritures'] and c['fiscal'] for c in items)
    assert all(not c['resultat_reel'] and not c['anomalies'] for c in items)


def test_pdf_excel_reellement_ouverts_et_formules_statuts(tmp_path):
    from openpyxl import load_workbook
    from pypdf import PdfReader
    generer(tmp_path)
    wb = load_workbook(tmp_path / 'ANNEXE_RECETTE_PAIE_GRH.xlsx')
    assert wb.sheetnames == ['Synthèse', 'Dossiers', 'Sécurité', 'Préparation', 'Congés et absences', 'Traçabilité', 'Jeu de données']
    assert wb['Synthèse']['C4'].value.startswith('=COUNTIF(')
    assert all(ws.data_validations.count == 1 for ws in wb if ws.title not in ('Synthèse', 'Jeu de données'))
    rows = [row for ws in wb if ws.title not in ('Synthèse', 'Jeu de données') for row in ws.iter_rows(min_row=2, values_only=True)]
    assert len(rows) == 26 and {r[10] for r in rows} == {'Non testé', 'Bloqué'}
    text = '\n'.join(p.extract_text() for p in PdfReader(tmp_path / 'ANNEXE_RECETTE_PAIE_GRH.pdf').pages)
    text = ' '.join(text.split())
    assert all(c['id'] in text for c in cas())
    assert 'Aucun résultat utilisateur prévalidé' in text
    assert 'Pas de formulaire UI dédié' in text
    assert all(c['objectif'] in text for c in cas() if c['module'] == 'Traçabilité')
    for row in wb['Traçabilité'].iter_rows(min_row=2, values_only=True):
        assert row[11] is None and row[12] is None
    md = (tmp_path / 'ANNEXE_RECETTE_PAIE_GRH.md').read_text(encoding='utf-8')
    assert '26 cas' in md
