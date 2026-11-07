from contextlib import closing
from io import BytesIO
import uuid
import httpx
from pypdf import PdfReader
from test_journal_cloture_concurrente_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_prorata_inventaire import faits
from test_ajustements_inventaire_isole import exercice
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data

BASE='/api/cloture/ajustements/calcul-prorata?exercice='
PDF='/api/cloture/ajustements/calcul-prorata/pdf?exercice='


def test_595_calcul_pdf_logo_empreinte_et_absence_mutation(application,tmp_path):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        exercice(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        avant=donnees_metier(application);data=faits();d=ok(api.post(BASE+'2025',json=data))
        assert d['montant_reporte']=='5934.07' and d['montant_non_reporte']=='6065.93'
        r=api.post(PDF+'2025',json={**data,'empreinte':d['empreinte_sha256']})
        assert r.status_code==200 and 'calcul_prorata_2025_cca.pdf' in r.headers['content-disposition']
        pdf=PdfReader(BytesIO(r.content));texte='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert any(p.images for p in pdf.pages) and d['empreinte_sha256'] in texte
        assert '5934.07' in texte and '90 / 182' in texte and 'CONTRAT-FICTIF595' in texte
        (tmp_path/'prorata595_fictif.pdf').write_bytes(r.content)
        assert api.post(BASE+'2024',json=data).status_code==404
        assert autre.post(BASE+'2025',json=data).status_code==404
        assert api.post(BASE+'2025',json=faits(date_fin='2025-01-01')).status_code==400
        assert api.post(BASE+'0',json=data).status_code==422
        assert donnees_metier(application)==avant
        ok(api.patch('/api/societe/moi',json={'raison_sociale':'Identité fictive modifiée595'}))
        assert api.post(PDF+'2025',json={**data,'empreinte':d['empreinte_sha256']}).status_code==409
        nouveau=ok(api.post(BASE+'2025',json=data))
        assert nouveau['empreinte_sha256']!=d['empreinte_sha256']


def test_595_calendrier_decale_pas_de_creation_exercice_suivant(application):
    with closing(client(application)[0]) as api:
        exercice(api,'2024-07-01','2025-06-30')
        avant=donnees_metier(application)
        d=ok(api.post(BASE+'2025',json=faits(date_debut='2025-04-01',date_fin='2025-09-30')))
        assert (d['date_fin_exercice'],d['jours_total'],d['jours_apres_cloture'],d['montant_reporte'])==('2025-06-30',183,92,'6032.79')
        assert donnees_metier(application)==avant


def test_595_lecteur_autorise_et_anonyme_refuse(application):
    with closing(client(application)[0]) as api:
        exercice(api);email='lecture595-'+uuid.uuid4().hex[:8]+'@example.com';password='Fictif595!Lecture'
        ok(api.post('/api/utilisateurs',json={'nom':'Lecture595','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            assert lecteur.post(BASE+'2025',json=faits()).status_code==401
            token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
            lecteur.headers['Authorization']='Bearer '+token;avant=donnees_metier(application)
            d=ok(lecteur.post(BASE+'2025',json=faits()))
            assert lecteur.post(PDF+'2025',json={**faits(),'empreinte':d['empreinte_sha256']}).status_code==200
            assert donnees_metier(application)==avant
