"""Vecteurs de format documentaire uniquement ; aucun résultat fiscal simulé."""
from copy import deepcopy
from io import BytesIO
from openpyxl import load_workbook
from pypdf import PdfReader
from services.ras_tva_registre_export_service import csv_bytes,xlsx_bytes,pdf_bytes
from test_ras_tva_registre_precision import donnees_format


def test_647_documents_multipages_sans_troncature_et_sans_modifier_entree():
    d=donnees_format();r=d['lignes'][0]
    r['documents_od']=[{'id':i,'reference':f'P647-{i:04d} '+'x'*85,
        'date_piece':'2026-10-19','source_type':'fichier','fichier_nom':f'piece647_{i:04d}.pdf',
        'created_at':'2026-10-19T12:00:00','prioritaire':False} for i in range(1,101)]
    r['documents_annulation']=[];avant=deepcopy(d)
    w=load_workbook(BytesIO(xlsx_bytes(d,{})))
    assert w['Documents liés'].max_row==101
    assert w['Documents liés']['E101'].value==r['documents_od'][-1]['reference']
    assert w['Documents liés'].row_dimensions[101].height>=40
    pdf=PdfReader(BytesIO(pdf_bytes(d,{})));assert len(pdf.pages)>2
    texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
    for i in range(1,101):assert texte.count(f'P647-{i:04d}')==1
    assert texte.count('Documents liés')>=1 and 'piece647_0100.pdf' in texte
    assert d==avant


def test_647_reference_sans_fichier_ou_date_ne_devient_pas_une_piece_presumee():
    d=donnees_format();r=d['lignes'][0]
    r['documents_od']=[{'id':1,'reference':'=REF647','date_piece':None,'source_type':'manuel',
        'fichier_nom':None,'created_at':None,'prioritaire':True}];r['documents_annulation']=[]
    w=load_workbook(BytesIO(xlsx_bytes(d,{})));ws=w['Documents liés']
    assert ws['E2'].value=='=REF647' and ws['E2'].data_type=='s'
    assert ws['F2'].value is None and ws['H2'].value is None and ws['I2'].value is None
    assert "'=REF647" in csv_bytes(d).decode('utf-8-sig')
    texte=' '.join('\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf_bytes(d,{}))).pages).split())
    assert 'Référence sans fichier' in texte and 'Non renseignée' in texte
    assert d['lignes'][0]['documents_od'][0]['date_piece'] is None
