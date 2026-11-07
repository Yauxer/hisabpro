from pathlib import Path
from zipfile import ZipFile
import importlib.util
import json
import xml.etree.ElementTree as ET
from openpyxl import load_workbook
from pypdf import PdfReader
import generer_annexe_reprises619 as g


def test_619_oracle_independant_et_cas_humains_non_prevalides():
    d=json.loads((g.DOSSIER/g.JSON_NOM).read_text(encoding='utf8'))
    assert d==json.loads(json.dumps({**g.jeu(),'cas':g.cas()}))
    o=d['oracle'];assert o['journal']=={'pieces':5,'lignes':10,'debit':'22000.00','credit':'22000.00'}
    assert o['resultat_avant_impot']=='-800.00' and o['actif']==o['passif']=='20000.00'
    assert o['provision_finale']=='800.00' and o['reprises_actives']=='200.00' and o['disponible_final']=='800.00'
    assert len(d['cas'])==len({t['id'] for t in d['cas']})==20
    for t in d['cas']:
        assert t['statut']=='Non testé'
        assert all(t[k]=='' for k in ('reel','anomalies','preuves'))
        assert all(t[k] for k,_ in g.CHAMPS if k not in ('reel','anomalies','preuves'))
    assert len(d['limites'])==2 and all(l['statut']=='Bloqué' for l in d['limites'])


def test_619_excel_dashboard_domaines_et_journal():
    w=load_workbook(g.DOSSIER/(g.NOM+'.xlsx'))
    assert set(w.sheetnames)=={'Synthèse','Préparation','Inventaire','Exports','Permissions','Négatifs','Technique',
        'Données','Oracle','Journal attendu','Balance attendue','Limites'}
    n=0
    for nom in ['Préparation','Inventaire','Exports','Permissions','Négatifs','Technique']:
        s=w[nom];assert s.freeze_panes=='A2' and s.data_validations.dataValidation
        for row in s.iter_rows(min_row=2):
            n+=1;assert row[10].value=='Non testé' and all(row[i].value is None for i in [11,12,14])
            assert s.row_dimensions[row[0].row].height>=250
    assert n==20
    s=w['Synthèse'];assert s['B4'].value=='=COUNTIF(\'Préparation\'!K2:K3,"Non testé")'
    assert s['G10'].value=='=IF(F10=0,0,C10/F10)' and s._charts and w.calculation.fullCalcOnLoad
    journal=w['Journal attendu'];assert journal.max_row==12
    assert sum(journal.cell(i,6).value for i in range(2,12))==22000
    assert sum(journal.cell(i,7).value for i in range(2,12))==22000
    assert journal['F12'].value==journal['G12'].value==22000


def test_619_word_pdf_champs_et_tous_les_cas():
    md=(g.DOSSIER/(g.NOM+'.md')).read_text(encoding='utf8')
    with ZipFile(g.DOSSIER/(g.NOM+'.docx')) as z:
        assert z.testzip() is None
        for n in z.namelist():
            if n.endswith(('.xml','.rels')):ET.fromstring(z.read(n))
        xml=ET.fromstring(z.read('word/document.xml'));texte='\n'.join(xml.itertext())
        assert g.TITRE in z.read('docProps/core.xml').decode()
        assert 'Recette des reprises de provisions' in z.read('word/header1.xml').decode()
    pdf=PdfReader(g.DOSSIER/(g.NOM+'.pdf'));ptexte='\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert len(pdf.pages)>=24 and g.TITRE in ' '.join(ptexte.split())
    for t in g.cas():assert t['id'] in texte and t['id'] in ptexte and t['id'] in md
    for champ in ['Données exactes','Résultat réel','Impacts fiscaux','Preuve attendue','Statut humain']:
        assert champ in texte and champ in ptexte
    assert '22000.00' in ptexte and '-800' in ptexte.replace('−','-') and 'Non testé' in ptexte


def test_619_generation_rejouable_sans_service_metier(tmp_path):
    g.generer(tmp_path)
    assert json.loads((tmp_path/g.JSON_NOM).read_text(encoding='utf8'))==json.loads((g.DOSSIER/g.JSON_NOM).read_text(encoding='utf8'))
    assert not any(p.suffix in {'.dump','.sql'} for p in tmp_path.iterdir())
