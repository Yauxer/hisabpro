from pathlib import Path
from zipfile import ZipFile
import ast,json,xml.etree.ElementTree as E
from openpyxl import load_workbook
from pypdf import PdfReader
from pydantic import TypeAdapter,EmailStr
import generer_annexe_ras_documents649 as g


def test_649_oracle_chiffres_independants_et_tous_statuts_humains_vierges():
    d=json.loads((g.OUT/g.JSON_NOM).read_text(encoding='utf8'))
    assert d==json.loads(json.dumps({**g.jeu(),'cas':g.cas()}))
    o=d['oracle'];a=o['avant_annulation'];b=o['apres_annulation']
    assert (a['pieces'],a['lignes'],a['debit'],a['credit'],a['banque'],a['fournisseur'],a['actif'])==(4,9,'118000.00','118000.00','94750.00','6000.00','96750.00')
    assert (b['pieces'],b['lignes'],b['debit'],b['credit'],b['banque'],b['fournisseur'],b['actif'])==(6,13,'124000.00','124000.00','100000.00','12000.00','102000.00')
    assert a['resultat_avant_impot']==b['resultat_avant_impot']=='-10000.00'
    assert o['ajout_document']=={'pieces':0,'lignes':0,'debit':'0.00','credit':'0.00'}
    assert len(d['cas'])==len({x['id'] for x in d['cas']})==12
    for x in d['cas']:
        assert x['statut']=='Non testé' and all(x[k]=='' for k in ('reel','anomalies','preuves'))
        assert all(x[k] for k,_ in g.CHAMPS if k not in ('reel','anomalies','preuves'))
    for role in ('administrateur','comptable','lecteur'):assert TypeAdapter(EmailStr).validate_python(d[role]['email'])==d[role]['email']
    assert d['limites'][0]['statut']=='Bloqué' and d['limites'][1]['statut']=='Non testé'


def test_649_excel_statuts_formules_resultats_et_journal_attendu():
    w=load_workbook(g.OUT/(g.NOM+'.xlsx'))
    assert set(w.sheetnames)==set(g.DOMAINES)|{'Synthèse','Données','Journal attendu','Soldes attendus','Limites'}
    nb=0
    for n in g.DOMAINES:
        sh=w[n];assert sh.freeze_panes=='D2' and sh.data_validations.dataValidation
        for row in sh.iter_rows(min_row=2):
            nb+=1;assert row[10].value=='Non testé' and all(row[i].value is None for i in (11,12,14))
            assert sh.row_dimensions[row[0].row].height>=250
    assert nb==12 and w['Journal attendu'].max_row==14
    rows=list(w['Journal attendu'].iter_rows(min_row=2,values_only=True))
    assert sum(x[3] for x in rows)==sum(x[4] for x in rows)==124000
    assert sum(x[3] for x in rows[:9])==sum(x[4] for x in rows[:9])==118000
    assert w['Synthèse']['G7'].value=='=IF(F7=0,0,C7/F7)' and w['Synthèse']._charts and w.calculation.fullCalcOnLoad


def test_649_word_pdf_complets_lisibles_et_document_fictif_distinct():
    with ZipFile(g.OUT/(g.NOM+'.docx')) as z:
        assert z.testzip() is None
        for n in z.namelist():
            if n.endswith(('.xml','.rels')):E.fromstring(z.read(n))
        texte='\n'.join(E.fromstring(z.read('word/document.xml')).itertext())
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        grille=E.fromstring(z.read('word/document.xml')).find('.//w:tbl/w:tblGrid',ns)
        assert int(grille[0].get('{'+ns['w']+'}w'))>=2000
        assert g.TITRE in z.read('docProps/core.xml').decode()
        assert 'Documents des OD RAS' in z.read('word/header1.xml').decode()
        assert '19/10/2026' in z.read('word/footer1.xml').decode()
    pages=PdfReader(g.OUT/(g.NOM+'.pdf')).pages;pdf='\n'.join(p.extract_text() or '' for p in pages)
    assert len(pages)>=15 and g.TITRE in ' '.join(pdf.split())
    for t in g.cas():assert t['id'] in texte and t['id'] in pdf
    for label in ('Données exactes','Résultat réel','Impacts fiscaux','Preuve attendue','Statut humain'):assert label in texte and label in pdf
    for val in ('118000','124000','94750','96750','102000','Non testé','COMP-DOC649','Révision653'):assert val in pdf
    p=PdfReader(g.OUT/g.PREUVE);assert len(p.pages)==1 and 'ESSAI UNIQUEMENT' in p.pages[0].extract_text()


def test_649_oracle_ne_reutilise_pas_de_calcul_metier():
    arbre=ast.parse(Path(g.__file__).read_text(encoding='utf8'))
    modules=[x.module for x in ast.walk(arbre) if isinstance(x,ast.ImportFrom)]
    assert not any(x and x.split('.')[0] in {'models','routers','services','database'} for x in modules)
    o=g.oracle();assert len(o['pieces'])==6 and sum(len(p['lignes']) for p in o['pieces'])==13
    assert o['ras']=='750.00' and o['tresorerie']=='5250.00'


def test_653_cas_principal_au_dessus_des_petites_prestations_sans_cumul_invente():
    from decimal import Decimal
    d=g.jeu();f=d['facture'];ht=sum(Decimal(str(l['quantite']))*Decimal(str(l['prix_unitaire'])) for l in f['lignes'])
    assert ht==Decimal('10000') and ht*Decimal('1.20')==Decimal('12000')
    assert Decimal(d['simulation']['montant_paiement_ttc'])==Decimal('6000')>Decimal('5000')
    assert d['revision']['cumul_mensuel_externe_suppose'] is None
    assert d['simulation']['tva_paiement']=='1000.00' and f['tva_deductible_pct']==100
    assert '100%' in g.cas()[1]['donnees'] and '0,005' in g.cas()[10]['donnees']


def test_653_consignes_humaines_correspondent_aux_lignes_de_l_oracle():
    import re
    for indice,phases in [(1,('Capital','Achat')),(2,('Règlement','Capture RAS')),(7,('Annulation règlement','Annulation RAS'))]:
        texte=g.cas()[indice]['ecritures']
        valeurs=[(sens,compte,int(montant)) for sens,compte,montant in re.findall(r'\b([DC])\s*(\d{4,5})\s*=\s*(\d+)',texte)]
        attendu=[]
        for p in g.oracle()['pieces']:
            if p['phase'] in phases:
                for l in p['lignes']:
                    attendu.append(('D' if l['debit_cents'] else 'C',l['compte'],(l['debit_cents'] or l['credit_cents'])//100))
        assert sorted(valeurs)==sorted(attendu)
    assert 'banque 94750.' in g.cas()[2]['attendu'] and 'ouverte 6000.' in g.cas()[2]['attendu']
    assert '124000' in g.cas()[7]['ecritures']
