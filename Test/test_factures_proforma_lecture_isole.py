"""Le statut proforma stocké doit traverser les sorties API, sans heuristique."""
from contextlib import closing
from datetime import date
from io import BytesIO
import uuid
import pytest
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_reglement_comptabilisation_concurrente_isole import metier


@pytest.mark.parametrize('sens', ['vente','achat'])
def test_proforma_creation_liste_pdf_conversion_et_facture_ordinaire(application,sens):
    with closing(client(application)[0]) as api:
        tid=ok(api.post('/api/tiers',json={'nom':'Tiers proforma fictif541',
            'type':'client' if sens=='vente' else 'fournisseur'}),201)['id']
        docs=[]
        for proforma in (False,True):
            f=ok(api.post('/api/factures',json={'type':sens,'tiers_id':tid,
                'tiers':'Tiers proforma fictif541','date':date.today().isoformat(),
                'reference':'FICT541-'+uuid.uuid4().hex[:10],'est_proforma':proforma,
                'lignes':[{'description':'Service fictif541','quantite':1,
                    'prix_unitaire':100,'tva':20}]}),201)
            assert f.get('est_proforma') is proforma,f
            docs.append(f)
        avant=metier(application)
        rows=ok(api.get('/api/factures',params={'exercice':date.today().year}))
        assert {f['id']:f['est_proforma'] for f in rows}=={docs[0]['id']:False,docs[1]['id']:True}
        fid=docs[1]['id']
        pdf=api.get(f'/api/factures/{fid}/pdf')
        assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')
        from pypdf import PdfReader
        assert 'PROFORMA' in '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf.content)).pages)
        assert api.post(f'/api/factures/{fid}/valider',json={}).status_code==400
        assert api.post(f'/api/factures/{fid}/comptabiliser',json={}).status_code==400
        assert metier(application)==avant
        ancien=docs[1]['numero']
        conversion=ok(api.post(f'/api/factures/{fid}/convertir-definitive',json={}))
        assert conversion['numero']!=ancien
        rows=ok(api.get('/api/factures',params={'exercice':date.today().year}))
        f=next(x for x in rows if x['id']==fid)
        assert f['est_proforma'] is False and f['est_validee'] is True
        assert f['total_ttc']==120 and f['numero']==conversion['numero']
        avant=metier(application)
        assert api.post(f'/api/factures/{fid}/convertir-definitive',json={}).status_code==400
        assert metier(application)==avant
        eid=ok(api.post(f'/api/factures/{fid}/comptabiliser',json={}))['ecriture_id']
        ok(api.post(f'/api/ecritures/{eid}/valider',json={}))
        assert api.get('/api/fec/export',params={'exercice':date.today().year}).status_code==200
