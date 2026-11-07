"""Oracles indépendants et ouverture des trois livrables utilisateur, sans DB."""
from decimal import Decimal
from pathlib import Path
from generer_annexe_recette_achats_partiels_284 import JEU, NOM, SOURCES, cas, generer, oracle


def test_oracle_arithmetique_independant():
    r=oracle()
    assert r == {k:Decimal(v) for k,v in {
        'quantite_br1':'1','quantite_br2':'3','ht_facture1':'500','ht_facture2':'1500',
        'tva_facture1':'100','tva_facture2':'300','ttc_facture1':'600','ttc_facture2':'1800',
        'stock_final':'4','solde_6111':'2000','solde_34552':'400','solde_4411':'0',
        'solde_5141':'-2400','total_debit':'4800','total_credit':'4800'}.items()}
    assert r['total_debit']==r['total_credit']
    assert r['ht_facture1']+r['tva_facture1']==r['ttc_facture1']
    assert r['ht_facture2']+r['tva_facture2']==r['ttc_facture2']
    assert sum(r[k] for k in ('solde_6111','solde_34552','solde_4411','solde_5141'))==0


def test_deux_cas_non_prevalides_et_actions_executables():
    items=cas()
    assert [c['id'] for c in items]==['ACH-284-01','ACH-284-02']
    assert all(c['statut']=='Non testé' for c in items)
    assert all(c[k]=='' for c in items for k in ('resultat_reel','anomalies','observations'))
    assert all(c[k] for c in items for k in ('prerequis','donnees','actions','attendu','ecritures','fiscal','controles','preuves'))
    assert len(items[0]['actions'])==7 and len(items[1]['actions'])==4
    assert 'sans les exiger' in items[1]['controles']
    assert 'solde comptable final crédit 2 400' in JEU['Banque']
    assert 'sans champ de compte comptable' in JEU['Banque']
    assert 'reste 3' in items[0]['actions'][1] and 'reste 0' in items[0]['actions'][3]
    assert '5141' in items[0]['actions'][4] and 'Valider' in items[0]['actions'][4]
    assert all((Path(__file__).resolve().parents[1]/p).is_file() for p in SOURCES)


def test_pdf_excel_markdown_reellement_ouverts(tmp_path):
    from openpyxl import load_workbook
    from pypdf import PdfReader
    generer(tmp_path)
    wb=load_workbook(tmp_path/(NOM+'.xlsx'))
    assert wb.sheetnames==['Synthèse','Achats','Jeu de données']
    assert wb['Synthèse']['B4'].value==2
    assert wb['Synthèse']['C4'].value=='=COUNTIF(Achats!K2:K3,"Réussi")'
    assert wb['Synthèse']['G4'].value=='=IF(B4=0,0,(C4+D4)/B4)'
    assert wb['Synthèse']['G4'].number_format=='0%'
    ws=wb['Achats']; assert ws.freeze_panes=='A2' and ws.auto_filter.ref=='A1:P3'
    assert ws.data_validations.count==1
    assert ws['L1'].value=='Résultat réel' and ws['M1'].value=='Anomalies' and ws['N1'].value=='Preuves/captures'
    for r in (2,3):
        assert ws.cell(r,11).value=='Non testé'
        assert all(ws.cell(r,c).value is None for c in (12,13,15))
        assert ws.cell(r,14).value
    jeu=dict(wb['Jeu de données'].iter_rows(min_row=2,values_only=True))
    assert jeu['Oracle total_debit']==4800 and jeu['Oracle solde_5141']==-2400
    assert all(c.data_type=='n' for row in wb['Jeu de données'] if str(row[0].value).startswith('Oracle ') for c in row[1:])
    pdf=PdfReader(tmp_path/(NOM+'.pdf'))
    texte=' '.join(' '.join(p.extract_text() or '' for p in pdf.pages).split())
    assert len(pdf.pages)>=4
    assert all(c['id'] in texte for c in cas())
    assert 'FR284-001' in texte and 'VIR284-002' in texte
    assert 'Non testé' in texte and 'dix lignes' in texte and '4 800' in texte
    assert 'sans les exiger du lecteur utilisateur' in texte
    assert all(p.mediabox.width<600 for p in pdf.pages)
    md=(tmp_path/(NOM+'.md')).read_text(encoding='utf-8')
    assert md.count('**Statut** :\nNon testé')==2
    assert all('../../'+p in md for p in SOURCES)
    assert 'Lettrer 4 lignes' in md and 'deux entrées' in md
