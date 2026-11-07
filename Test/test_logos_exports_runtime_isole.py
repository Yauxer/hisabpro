"""Exports avec logos distincts : API réelle, PostgreSQL jetable091, LOGIN limité."""
from contextlib import closing
from datetime import date
from io import BytesIO
import hashlib
from pypdf import PdfReader
from openpyxl import load_workbook
from test_e2e_runtime_session_isole import application,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_justificatifs_modeles_runtime_isole import ecriture,original


def test_logos_sur_balances_et_ventes_pdf_excel_sans_modifier_ecritures(application):
    with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
        empreintes=[]
        for api,format in [(a,'PNG'),(b,'JPEG')]:
            ok(api.patch('/api/societe/moi',json={'logo_url':image_data(format)}))
            eid=ecriture(api);avant=original(application,eid)
            ex=date.today().year
            r=api.get('/api/ecritures/reporting/balance/pdf',params={'exercice':ex,'date_from':f'{ex}-01-01','date_to':f'{ex}-12-31'})
            assert r.status_code==200,r.text
            images=PdfReader(BytesIO(r.content)).pages[0].images
            assert len(images)==1
            empreintes.append(hashlib.sha256(images[0].data).hexdigest())
            data=ok(api.get(f'/api/etats/ventes/preparation/{ex}'))
            for fmt in ['pdf','xlsx']:
                r=api.get(f'/api/etats/ventes/preparation/{ex}/export/{fmt}',params={'empreinte':data['empreinte_sha256']})
                assert r.status_code==200,r.text
                if fmt=='pdf':
                    assert len(PdfReader(BytesIO(r.content)).pages[0].images)==1
                else:
                    wb=load_workbook(BytesIO(r.content))
                    assert wb.sheetnames==['Logo société','Synthèse','Sources','Comptabilité']
                    assert len(wb['Logo société']._images)==1
                    assert wb['Synthèse']['B12'].value==0
            liasse=ok(api.get(f'/api/etats/liasse/{ex}'))
            assert liasse['societe']['logo_url']==image_data(format)
            r=api.get(f'/api/etats/liasse/{ex}/pdf')
            assert r.status_code==200,r.text
            assert len(PdfReader(BytesIO(r.content)).pages[0].images)==1
            assert original(application,eid)==avant
        assert empreintes[0]!=empreintes[1], 'Les deux sociétés doivent garder leurs logos distincts.'
