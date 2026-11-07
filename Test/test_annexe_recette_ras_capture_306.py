"""Oracles capture/annulation indépendants et ouverture PDF/Excel réelle."""
from decimal import Decimal
from pathlib import Path
from generer_annexe_recette_ras_capture_306 import JEU, NOM, ORACLE_LABELS, SOURCES, cas, generer, oracle


def test_oracles_independants_lettrage_annulation():
    r=oracle()
    assert r=={k:Decimal(v) for k,v in {'ht':'1000','tva':'200','ttc':'1200','ras_estimee':'100',
        'cash1':'400','reste_apres_cash1':'800','ras1':'30','reste_apres_capture1':'770',
        'cash2':'700','reste_apres_cash2':'70','ras2':'70','reste_solde':'0',
        'total_debit_solde':'2400','total_credit_solde':'2400','reste_apres_annulation':'770',
        'ras_active':'30','total_debit_final':'3170','total_credit_final':'3170',
        'banque_vente':'400','banque_achat':'-400','retenue_vente':'30','retenue_achat':'-30',
        'collectif_vente':'770','collectif_achat':'-770'}.items()}
    assert r['cash1']+r['ras1']+r['cash2']+r['ras2']==r['ttc']
    assert r['total_debit_solde']==r['total_credit_solde']
    assert r['total_debit_final']==r['total_credit_final']
    assert r['banque_vente']+r['retenue_vente']+r['collectif_vente']==r['ttc']
    assert -(r['banque_achat']+r['retenue_achat']+r['collectif_achat'])==r['ttc']
    assert set(ORACLE_LABELS)==set(r)


def test_deux_cas_utilisateur_non_prevalides_et_sources_presentes():
    items=cas()
    assert [c['id'] for c in items]==['CAP-306-01','CAP-306-02']
    assert all(c['statut']=='Non testé' for c in items)
    assert all(c[k]=='' for c in items for k in ('resultat_reel','anomalies','preuves','observations'))
    assert all(len(c['actions'])==9 for c in items)
    assert 'Ne pas réutiliser' in JEU['Société achat']
    assert 'D = date réelle' in JEU['Date exacte du parcours']
    assert all('Préparer la RAS déclarée' in c['actions'][2] for c in items)
    assert all('Valider les brouillons' in c['actions'][4] for c in items)
    assert all('Lettrer 5 lignes' in c['actions'][5] for c in items)
    assert all('Délettrer le code AAA' in c['actions'][6] for c in items)
    assert all('Annuler par contrepassation' in c['actions'][7] for c in items)
    assert all('ne change pas les montants' in JEU['Preuves et comparaison'] for c in items)
    assert 'D3453/C3421' in items[0]['ecritures'] and 'D4411/C4457' in items[1]['ecritures']
    assert all((Path(__file__).resolve().parents[1]/p).is_file() for p in SOURCES)
    source=Path(__file__).with_name('generer_annexe_recette_ras_capture_306.py').read_text(encoding='utf-8')
    assert 'import models' not in source and 'DATABASE_URL' not in source and 'services.' not in source


def test_pdf_excel_markdown_ouverts_et_suivi_vierge(tmp_path):
    from openpyxl import load_workbook
    from pypdf import PdfReader
    generer(tmp_path)
    wb=load_workbook(tmp_path/(NOM+'.xlsx'))
    assert wb.sheetnames==['Synthèse','Recouvrement','Jeu de données']
    assert wb['Synthèse']['B4'].value==2
    assert wb['Synthèse']['C4'].value=='=COUNTIF(Recouvrement!K2:K3,"Réussi")'
    assert wb['Synthèse']['G4'].value=='=IF(B4=0,0,(C4+D4)/B4)'
    ws=wb['Recouvrement']; assert ws.freeze_panes=='A2' and ws.auto_filter.ref=='A1:Q3'
    assert ws.data_validations.count==1
    assert ws['N1'].value=='Preuves/captures' and ws['Q1'].value=='Preuves attendues'
    for row in (2,3):
        assert ws.cell(row,11).value=='Non testé'
        assert all(ws.cell(row,col).value is None for col in (12,13,14,15))
        assert ws.cell(row,17).value
    jeu=dict(wb['Jeu de données'].iter_rows(min_row=2,values_only=True))
    assert jeu['Oracle Total débit final']==3170 and jeu['Oracle Fournisseur final']==-770
    pdf=PdfReader(tmp_path/(NOM+'.pdf'))
    texte=' '.join(' '.join(p.extract_text() or '' for p in pdf.pages).split())
    assert len(pdf.pages)>=4
    assert all(c['id'] in texte for c in cas())
    assert 'Non testé' in texte and 'quinze lignes' in texte and '3 170' in texte
    assert 'Délettrer le code AAA' in texte and 'aucune obligation' in texte.lower()
    assert 'certifié' in texte and 'sans qualification obligatoire' in texte
    assert all(p.mediabox.width<600 for p in pdf.pages)
    md=(tmp_path/(NOM+'.md')).read_text(encoding='utf-8')
    assert md.count('**Statut** :\nNon testé')==2
    assert all('../../'+p in md for p in SOURCES)
    assert '5 lignes' in md and 'ne change pas les montants' in md
