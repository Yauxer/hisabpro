"""L'empreinte du registre JSON est conservée dans les trois exports réels."""
from contextlib import closing
from datetime import date
from io import BytesIO
import csv
from openpyxl import load_workbook
from pypdf import PdfReader
from test_ras_tva_capture_isole import (
    application, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    preparer, capturer,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier


def test_585_empreinte_donnees_identique_dans_exports_et_json(application):
    with closing(client(application)[0]) as api:
        _, r = preparer(api);capturer(api, r)
        base = f'/api/tva/ras/registre/{date.today().year}'
        d = ok(api.get(base));empreinte = d['empreinte_sha256']
        assert len(empreinte) == 64
        avant = donnees_metier(application)
        sorties = {}
        for fmt in ('csv','xlsx','pdf'):
            reponse = api.get(base + '/export/' + fmt, params={'empreinte':empreinte})
            assert reponse.status_code == 200,reponse.text[:200]
            sorties[fmt] = reponse.content
        lignes = list(csv.reader(sorties['csv'].decode('utf-8-sig').splitlines(), delimiter=';'))
        assert ['Empreinte des données SHA-256',empreinte] in lignes
        w = load_workbook(BytesIO(sorties['xlsx']))
        assert w['Synthèse']['A6'].value == 'Empreinte des données SHA-256'
        assert w['Synthèse']['B6'].value == empreinte and w['Synthèse']['B6'].data_type == 's'
        texte = '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(sorties['pdf'])).pages)
        assert empreinte in ''.join(texte.split())
        assert donnees_metier(application) == avant
