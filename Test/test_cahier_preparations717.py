"""Recette717 : encodage Windows, artefacts humains, données et navigation des guides."""
from pathlib import Path
from zipfile import ZipFile
from decimal import Decimal as D
import importlib.util,json,re,xml.etree.ElementTree as ET
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
H=ROOT/'docs/recette'
REG=[(707,'PARTICIPATIONS','Participations','P707'),(709,'EMETTEURS','Émetteurs','E709'),
 (711,'CESSIONS','Cessions','C711'),(713,'MOUVEMENTS','Mouvements','M713'),(715,'RACCORDS','Rattachements','R715')]
STEM=H/'CAHIER_PREPARATIONS_BALANCES_717'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def guide():
 spec=importlib.util.spec_from_file_location('test_guide717',ROOT/'docs/guide/generer_guide.py')
 g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);return g


def cas(lot,nom,prefixe):
 s=(ROOT/f'docs/LIASSE_BALANCES_{nom}_{lot}.md').read_text(encoding='utf-8-sig')
 return [[c.strip() for c in line.strip('|').split('|')] for line in s.splitlines() if line.startswith('|'+prefixe+'-')]


@pytest.mark.parametrize('encoding',['utf8','utf-8-sig'])
def test_717_titre_utf8_windows(encoding,tmp_path,monkeypatch):
 p=tmp_path/'guide.md';p.write_text('# Titre de recette fictif\n\nVersion 1 du 21 octobre 2026.\n\n## Parcours\nTexte.',encoding=encoding)
 g=guide();monkeypatch.setattr(g,'SOURCE',p)
 assert g.blocs()[0]==('title','Titre de recette fictif')
 assert g.date_document()=='21/10/2026'


def test_717_trente_cas_consolides_fideles_aux_sources():
 texte=STEM.with_suffix('.md').read_text(encoding='utf8');vus=[]
 for lot,nom,_,prefixe in REG:
  rows=cas(lot,nom,prefixe);assert len(rows)==6 and all(r[3]=='Non testé' for r in rows)
  for row in rows:
   assert '|'+ '|'.join(row)+'|' in texte
   vus.append(row[0])
 assert len(vus)==len(set(vus))==30
 assert 'Trois jeux de recette distincts' in texte and 'recette annuelle complète' in texte


def test_717_word_xml_titres_et_trente_ids():
 for stem in [STEM,*[H/f'MODE_EMPLOI_{nom}_{lot}' for lot,nom,_,_ in REG]]:
  with ZipFile(stem.with_suffix('.docx')) as z:
   assert z.testzip() is None
   for n in z.namelist():
    if n.endswith('.xml'):ET.fromstring(z.read(n))
   doc=ET.fromstring(z.read('word/document.xml'));p=doc.find('w:body/w:p',NS)
   assert p.find('w:pPr/w:pStyle',NS).attrib['{'+NS['w']+'}val']=='Title'
   titre=''.join(p.itertext());assert not titre.startswith(('\ufeff','#'))
   if stem==STEM:
    texte=''.join(doc.itertext())
    assert all(f'{prefixe}-0{i}' in texte for _,_,_,prefixe in REG for i in range(1,7))


def test_717_pdf_lisible_et_identifiants_exhaustifs():
 p=PdfReader(STEM.with_suffix('.pdf'));texte='\n'.join(x.extract_text() or '' for x in p.pages)
 ids=re.findall(r'(?:P707|E709|C711|M713|R715)-0[1-6]',texte)
 assert len(ids)==len(set(ids))==30 and len(p.pages)>5
 for lot,nom,_,prefixe in REG:
  r=PdfReader(H/f'MODE_EMPLOI_{nom}_{lot}.pdf');t='\n'.join(x.extract_text() or '' for x in r.pages)
  assert all(f'{prefixe}-0{i}' in t for i in range(1,7)) and '# MODE' not in t


def test_717_excel_neuf_feuilles_statuts_formules_et_preuves_vides():
 w=load_workbook(STEM.with_suffix('.xlsx'));assert len(w.sheetnames)==9 and w.calculation.fullCalcOnLoad
 tous=[]
 for no,(lot,nom,titre,prefixe) in enumerate(REG,2):
  ws=w[titre];rows=list(ws.values)[1:];attendus=cas(lot,nom,prefixe)
  assert len(rows)==6
  for r,a in zip(rows,attendus):
   assert list(r[:4])==a and all(v is None for v in r[4:7]);tous.append(r[0])
  assert str(ws.data_validations.dataValidation[0].sqref)=='D2:D7'
  assert ws.data_validations.dataValidation[0].formula1=='"Non testé,Réussi,Échoué,Bloqué"'
  assert w['Synthèse'].cell(no,2).value==f"=COUNTA('{titre}'!A2:A7)"
  assert w['Synthèse'].cell(no,3).value==f'=COUNTIF(\'{titre}\'!D2:D7,"Réussi")'
  assert w['Synthèse'].cell(no,7).value==f'=IF(B{no}=0,0,C{no}/B{no})'
 assert len(tous)==len(set(tous))==30 and w['Synthèse']['B7'].value=='=SUM(B2:B6)'
 preuves=list(w['Preuves'].values)[1:];assert len(preuves)==30 and all(all(v is None for v in r[1:]) for r in preuves)
 assert w['Anomalies'].max_row==1


def test_717_oracles_financiers_independants_des_trois_jeux():
 a=json.loads((H/'DONNEES_PARTICIPATIONS707.json').read_text(encoding='utf8'))
 for p in ('n','n1'):assert sum(D(r['debit']) for r in a[p])==sum(D(r['credit']) for r in a[p])
 em=json.loads((H/'DONNEES_EMETTEURS709.json').read_text(encoding='utf8'))
 assert sum(D(r['valeur_brute']) for r in em['tables'][0]['lignes'])==D('4000')
 assert em['tables'][0]['lignes'][1]['capital_emetteur'] is None and em['tables'][1]['lignes'][0]['produits_recus']=='0'
 c=json.loads((H/'DONNEES_CESSIONS711.json').read_text(encoding='utf8'))
 assert sum(D(r['prix_cession'])-D(r['vna']) for r in c['tables'][0]['lignes'])==D('-1000')
 m=json.loads((H/'DONNEES_MOUVEMENTS713.json').read_text(encoding='utf8'))
 for p in ('n','n1'):assert sum(D(r['debit']) for r in m[p])==sum(D(r['credit']) for r in m[p])
 for t in m['tables']:
  r=t['lignes'][0];assert D(r['debut'])+D(r['augmentations'])-D(r['diminutions'])==D(r['fin'])
 liens=json.loads((H/'DONNEES_RACCORDS715.json').read_text(encoding='utf8'))
 for t in liens['tables']:
  code=t['code'];compte=t['lignes'][0]['compte'];r=next(r for r in m['n'] if r['compte']==compte)
  solde=D(r['debit'])-D(r['credit']);solde=solde if code=='B2' else -solde
  assert solde==D(liens['attendus'][code]['solde_source'])
 assert D('10999.99')-D('11000')==D(liens['variante']['B2_ecart_apres_nouveau_raccord'])


def test_717_liens_locaux_des_guides_et_index():
 w=load_workbook(STEM.with_suffix('.xlsx'))
 for i,(_,nom,_,_) in enumerate(REG,2):
  for col in (8,9):
   cible=w['Synthèse'].cell(i,col).hyperlink.target
   assert not cible.startswith(('http:','https:')) and (H/cible).is_file()
 index=(H/'README.md').read_text(encoding='utf8')
 assert 'CAHIER_PREPARATIONS_BALANCES_717.docx' in index and 'CAHIER_PREPARATIONS_BALANCES_717.xlsx' in index
