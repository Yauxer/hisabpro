"""Formats d'export exacts ; vecteur de format, pas scénario comptable intégré."""
from io import BytesIO
from copy import deepcopy
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from services.ras_tva_registre_export_service import COLONNES, xlsx_bytes, csv_bytes, pdf_bytes


def donnees_format():
    r={cle:None for cle,_ in COLONNES}
    r.update(capture_id=1,nature='vente',date_paiement='2026-10-18',numero_facture='FORMAT-FICTIF',tiers='Tiers fictif',
        quote_part_ttc='9999999999999999.99',quote_part_tva='1000000000000000.01',retenue_tva='750000000000000.01',
        net_reglement='9249999999999999.98',reference='FORMAT-FICTIF',compte_destination='3453',ecriture_id=1,
        od_validee=False,annulation_id=None,diagnostics=[],justification_quote_part='Test de format uniquement',reference_attestation='')
    t={k:{'montant':'0.00'} for k in ('declarees','actives','actives_validees','annulees','annulations_annee')}
    v={k:{'montant':r['retenue_tva'] if k in ('declarees','actives') else '0.00'} for k in t}
    d={'annee':2026,'societe':{'raison_sociale':'Test de format fictif','ice':'','identifiant_fiscal':''},
        'note':'Formats exacts uniquement, aucun scénario fiscal intégré.', 'lignes':[r],'totaux':{'achat':t,'vente':v}}
    return d


def test_579_exports_ne_convertissent_pas_les_grands_centimes_en_flottants():
    d=donnees_format();r=d['lignes'][0]
    w=load_workbook(BytesIO(xlsx_bytes(d,{})))
    for colonne,cle in [('F','quote_part_ttc'),('G','quote_part_tva'),('H','retenue_tva'),('I','net_reglement')]:
        c=w['Captures'][colonne+'2']
        assert c.value==r[cle] and c.data_type=='s'
    assert w['Synthèse']['C9'].value==r['retenue_tva']
    assert r['net_reglement'] in csv_bytes(d).decode('utf-8-sig')
    pdf=PdfReader(BytesIO(pdf_bytes(d,{})))
    texte=''.join(p.extract_text() or '' for p in pdf.pages).replace('\n','').replace(' ','')
    assert r['net_reglement'].replace('.',',') in texte


def test_579_pdf_multipage_et_excel_ne_tronquent_pas_les_references():
    fitz=pytest.importorskip('pymupdf')
    d=donnees_format();prototype=d['lignes'][0];rows=[]
    for i in range(1,61):
        r=deepcopy(prototype)
        r.update(capture_id=i,nature='achat' if i%2 else 'vente',numero_facture=f'DOC-FICTIF-{i:03d}',
            quote_part_ttc='600.00',quote_part_tva='100.00',retenue_tva='75.00',net_reglement='525.00',
            reference=f'PIECE-RAS-{i:03d}',justification_quote_part='a'*200,reference_attestation='b'*200,
            mois_reversement_prevu='2026-11')
        rows.append(r)
    d['lignes']=rows
    d['totaux']={nature:{k:{'montant':'2250.00' if k in ('declarees','actives') else '0.00'} for k in d['totaux']['vente']} for nature in ('achat','vente')}
    avant=deepcopy(d)
    w=load_workbook(BytesIO(xlsx_bytes(d,{})))
    assert w['Captures'].max_row==61 and w['Captures'].row_dimensions[2].height>=120
    with fitz.open(stream=pdf_bytes(d,{}),filetype='pdf') as doc:
        assert len(doc)>1
        texte='\n'.join(p.get_text() for p in doc)
        for i in range(1,61):assert texte.count(f'PIECE-RAS-{i:03d}')==1
        for page in doc:
            assert 'Références déclarées' in page.get_text()
            for bloc in page.get_text('dict')['blocks']:
                for ligne in bloc.get('lines',[]):
                    for span in ligne['spans']:
                        x0,y0,x1,y1=span['bbox']
                        assert 0<=x0<x1<=page.rect.width and 0<=y0<y1<=page.rect.height
    assert d==avant
