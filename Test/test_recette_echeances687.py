"""Documents livrés et oracle en centimes, sans calcul métier de l’application."""
from decimal import Decimal
from zipfile import ZipFile
import csv,json,xml.etree.ElementTree as E
from pypdf import PdfReader
from openpyxl import load_workbook
from generer_recette_echeances687 import OUT,NOM,jeu,cas


def test_687_recette_csv_et_oracle_independants():
    d=jeu()
    with (OUT/'BALANCE_FICTIVE_ECHEANCES687.csv').open(encoding='utf8',newline='') as f:
        rows=list(csv.DictReader(f,delimiter=';'))
    assert rows==d['lignes']
    debit=sum(Decimal(r['debit']) for r in rows);credit=sum(Decimal(r['credit']) for r in rows)
    assert debit==credit==Decimal(d['oracle']['debit'])==Decimal('9000')
    assert 800000-200000-100000==int(Decimal(d['oracle']['v2_B6_reliquat'])*100)
    assert 300000-100000*3==int(Decimal(d['oracle']['v3_B7_reliquat'])*100)
    publie=json.loads((OUT/'DONNEES_RECETTE_ECHEANCES687.json').read_text(encoding='utf8'))
    assert publie=={**d,'cas':cas()}


def test_687_recette_word_pdf_lisibles_et_ids_non_testes():
    with ZipFile(OUT/(NOM+'.docx')) as z:
        assert z.testzip() is None
        for n in z.namelist():
            if n.endswith('.xml'):E.fromstring(z.read(n))
        xml=E.fromstring(z.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    word=' '.join(x.text or '' for x in xml.findall('.//w:t',ns))
    pdf=PdfReader(OUT/(NOM+'.pdf'));texte=' '.join(p.extract_text() or '' for p in pdf.pages)
    for contenu in (word,texte):
        assert 'Version 1 du 21 octobre 2026' in contenu
        for row in cas():assert row[0] in contenu
        assert contenu.count('Statut humain : Non testé')==7
        assert 'BALANCE_FICTIVE_ECHEANCES687.csv' in contenu
        assert 'production non validée' in contenu.lower()


def test_687_recette_excel_suivi_humain_vierge():
    w=load_workbook(OUT/(NOM+'.xlsx'),data_only=False)
    assert w.sheetnames==['Synthèse','Recette','Oracle','Anomalies','Preuves']
    assert w.calculation.fullCalcOnLoad and 'COUNTIF' in w['Synthèse']['B2'].value
    ws=w['Recette'];assert ws.max_row==8 and ws.freeze_panes=='C2'
    assert len(ws.data_validations.dataValidation)==1
    for r in list(ws.values)[1:]:
        assert r[9]=='Non testé' and all(r[i] is None for i in (10,11,13,14))
    assert w['Anomalies'].max_row==1
    assert all(r[1] is None and r[2] is None for r in list(w['Preuves'].values)[1:])
