"""Deux scénarios RAS non prévalidés ; oracles indépendants et vrais documents ouverts."""
from decimal import Decimal
from pathlib import Path

from generer_annexe_recette_ras_298 import JEU, NOM, SOURCES, cas, generer, oracle


def test_oracle_ras_estimation_sans_imputation():
    r=oracle()
    assert r=={k:Decimal(v) for k,v in {'ht':'1000','tva':'200','ttc':'1200','ras_estimee':'100',
        'net_estime':'1100','solde_avant':'1200','cash1':'1100','reste_apres_cash1':'100',
        'cash2':'100','solde_final':'0','ras_imputee':'0','banque_vente':'1200',
        'banque_achat':'-1200','total_debit':'2400','total_credit':'2400'}.items()}
    assert r['total_debit']==r['total_credit']
    assert r['ht']+r['tva']==r['ttc']
    assert r['cash1']+r['cash2']==r['ttc']
    assert r['banque_vente']+r['banque_achat']==0


def test_deux_societes_parcours_non_developpeur_non_prevalides():
    items=cas()
    assert [c['id'] for c in items]==['RAS-298-01','RAS-298-02']
    assert all(c['statut']=='Non testé' for c in items)
    assert all(c[k]=='' for c in items for k in ('resultat_reel','anomalies','preuves','observations'))
    assert all(c[k] for c in items for k in ('prerequis','donnees','actions','attendu','ecritures','fiscal','controles','preuves_attendues'))
    assert all(len(c['actions'])==6 for c in items)
    assert all('Lettrer 3 lignes' in c['actions'][4] for c in items)
    assert 'Encaisser le client' in items[0]['actions'][1]
    assert 'Payer le fournisseur' in items[1]['actions'][1]
    assert 'D3421=1 200' in items[0]['ecritures'] and 'C4411=1 200' in items[1]['ecritures']
    assert 'ne pas réutiliser' in JEU['Société achat'].lower()
    assert all((Path(__file__).resolve().parents[1]/p).is_file() for p in SOURCES)
    source=Path(__file__).with_name('generer_annexe_recette_ras_298.py').read_text(encoding='utf-8')
    assert 'import models' not in source and 'services.' not in source and 'DATABASE_URL' not in source
    assert all('SQL' not in action and 'NaN' not in action for c in items for action in c['actions'])


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
    assert ws['L1'].value=='Résultat réel' and ws['N1'].value=='Preuves/captures' and ws['Q1'].value=='Preuves attendues'
    for row in (2,3):
        assert ws.cell(row,11).value=='Non testé'
        assert all(ws.cell(row,col).value is None for col in (12,13,14,15))
        assert ws.cell(row,17).value
    jeu=dict(wb['Jeu de données'].iter_rows(min_row=2,values_only=True))
    assert jeu['Oracle total_debit']==2400 and jeu['Oracle banque_achat']==-1200
    pdf=PdfReader(tmp_path/(NOM+'.pdf'))
    texte=' '.join(' '.join(p.extract_text() or '' for p in pdf.pages).split())
    assert len(pdf.pages)>=4
    assert all(c['id'] in texte for c in cas())
    assert 'Non testé' in texte and 'sept lignes' in texte and '2 400' in texte
    assert 'aucune retenue' in texte.lower() and 'aucune attestation' in texte.lower()
    assert all(p.mediabox.width<600 for p in pdf.pages)
    md=(tmp_path/(NOM+'.md')).read_text(encoding='utf-8')
    assert md.count('**Statut** :\nNon testé')==2
    assert all('../../'+p in md for p in SOURCES)
    assert 'Lettrer 3 lignes' in md and 'fictive' in md.lower()
