from pathlib import Path
from zipfile import ZipFile
import json,xml.etree.ElementTree as E
from openpyxl import load_workbook
from pypdf import PdfReader
from pydantic import TypeAdapter,EmailStr
import generer_annexe_societes639 as g


def test_639_oracle_independant_et_statuts_humains():
    d=json.loads((g.OUT/g.JSON_NOM).read_text(encoding='utf8'))
    assert d==json.loads(json.dumps({**g.jeu(),'cas':g.cas()}))
    o=d['oracle'];assert (o['ht'],o['tva'],o['ttc'])==('500.00','100.00','600.00')
    for soc,bank,res,bilan in [('A','10600.00','500.00','10600.00'),('B','9400.00','-500.00','9500.00')]:
        x=o['societes'][soc]
        assert (x['banque'],x['resultat_avant_impot'],x['actif'],x['passif'])==(bank,res,bilan,bilan)
        assert x['pieces']==3 and x['lignes']==7 and x['debit']==x['credit']=='11200.00' and x['solde_tiers']=='0.00'
    assert len(d['cas'])==len({t['id'] for t in d['cas']})==20
    for t in d['cas']:
        assert t['statut']=='Non testé' and all(t[k]=='' for k in ('reel','anomalies','preuves'))
        assert all(t[k] for k,_ in g.CHAMPS if k not in ('reel','anomalies','preuves'))
    for k in ('administrateur','lecteur'):assert TypeAdapter(EmailStr).validate_python(d[k]['email'])==d[k]['email']
    assert len(d['limites'])==2 and all(l['statut']=='Bloqué' for l in d['limites'])


def test_639_excel_feuilles_resultats_vides_journal_et_dashboard():
    w=load_workbook(g.OUT/(g.NOM+'.xlsx'));assert set(w.sheetnames)==set(g.DOMAINES)|{'Synthèse','Données','Oracle','Journal attendu','Soldes attendus','Limites'}
    n=0
    for nom in g.DOMAINES:
        sh=w[nom];assert sh.freeze_panes=='A2' and sh.data_validations.dataValidation
        for row in sh.iter_rows(min_row=2):
            n+=1;assert row[10].value=='Non testé' and all(row[i].value is None for i in (11,12,14))
            assert sh.row_dimensions[row[0].row].height>=250
    assert n==20 and w['Journal attendu'].max_row==15
    for soc in ('A','B'):
        rows=[r for r in w['Journal attendu'].iter_rows(min_row=2,values_only=True) if r[0]==soc]
        assert len(rows)==7 and sum(r[5] for r in rows)==sum(r[6] for r in rows)==11200
    assert w['Synthèse']['G10'].value=='=IF(F10=0,0,C10/F10)' and w['Synthèse']._charts and w.calculation.fullCalcOnLoad
    assert w['Synthèse']['B4'].value=='=COUNTIF(\'Préparation\'!K2:K6,"Non testé")'


def test_639_word_pdf_tous_les_cas_et_champs():
    with ZipFile(g.OUT/(g.NOM+'.docx')) as z:
        assert z.testzip() is None
        for n in z.namelist():
            if n.endswith(('.xml','.rels')):E.fromstring(z.read(n))
        texte='\n'.join(E.fromstring(z.read('word/document.xml')).itertext())
        assert g.TITRE in z.read('docProps/core.xml').decode() and 'Recette des sociétés liées' in z.read('word/header1.xml').decode()
    pages=PdfReader(g.OUT/(g.NOM+'.pdf')).pages;pdf='\n'.join(p.extract_text() or '' for p in pages)
    assert len(pages)>=24 and g.TITRE in ' '.join(pdf.split())
    for t in g.cas():assert t['id'] in texte and t['id'] in pdf
    for label in ('Données exactes','Résultat réel','Impacts fiscaux','Preuve attendue','Statut humain'):
        assert label in texte and label in pdf
    for val in ('11200.00','10600.00','9500.00','Non testé','ATLAS-2026-001'):assert val in pdf


def test_639_oracle_sans_import_services_applicatifs():
    import ast
    arbre=ast.parse(Path(g.__file__).read_text(encoding='utf8'))
    imports=[x.module for x in ast.walk(arbre) if isinstance(x,ast.ImportFrom)]
    assert not any(x and x.split('.')[0] in {'models','routers','services','database'} for x in imports)
    assert len(g.oracle()['pieces'])==6 and sum(len(p['lignes']) for p in g.oracle()['pieces'])==14
