"""Dossier de préparation : ZIP vérifié, exports réels et droits sur PostgreSQL nonce."""
from contextlib import closing
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import BytesIO,StringIO
from types import SimpleNamespace
from zipfile import ZipFile
import csv,hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_echeances687_isole import (
    application,application102,application101,application100,application099,application098,
    application097,application093,application092,application091,application090,application089,
    application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier)
from test_logo_societe import image_data


def verifier_bundle(raw,dossier,logo=True):
    with ZipFile(BytesIO(raw)) as z:
        assert z.testzip() is None
        noms=z.namelist();assert len(noms)==len(set(noms))
        assert all('/' not in n and '\\' not in n and not n.startswith('.') for n in noms)
        manifeste=json.loads(z.read('MANIFESTE_SHA256.json'))
        assert set(noms)==set(manifeste['fichiers'])|{'MANIFESTE_SHA256.json'}
        assert manifeste['pret_a_deposer'] is False and manifeste['type']=='preparation_interne_balances'
        assert manifeste['preparation']=={k:dossier[k] for k in ('id','exercice','version','empreinte_sha256')}
        for n,v in manifeste['fichiers'].items():
            assert len(z.read(n))==v['taille'] and hashlib.sha256(z.read(n)).hexdigest()==v['sha256']
        original=json.loads(z.read('preparation.json'));assert original==dossier
        canon=json.dumps(original['contenu'],sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
        assert hashlib.sha256(canon).hexdigest()==dossier['empreinte_sha256']
        sources=dossier['contenu']['sources']
        for k,n in [('n','balance_N.csv'),('n1','balance_N1.csv')]:
            if sources.get(k) is None:
                assert n not in noms and k in manifeste['sources_absentes']
            else:
                assert list(csv.DictReader(StringIO(z.read(n).decode('utf8')),delimiter=';'))==sources[k]
        assert ('echeances_documentaires.json' in noms)==bool(dossier['contenu'].get('echeances_documentaires'))
        wb=load_workbook(BytesIO(z.read('preparation.xlsx')))
        assert ('Empreinte des données normalisées',dossier['empreinte_sha256']) in list(wb['Dossier'].values)
        pdf=PdfReader(BytesIO(z.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert dossier['empreinte_sha256'] in t
        assert any(p.images for p in pdf.pages)==logo
        assert ('Logo société' in wb.sheetnames)==logo
        assert json.loads(z.read('identite_export.json'))['logo_valide_integre_aux_pdf_xlsx']==logo
        notice=z.read('LIRE_MOI.txt').decode('utf8')
        assert 'ni une liasse complète prête à déposer' in notice and 'pas une signature' in notice
        return manifeste


@pytest.mark.parametrize('comparatif,complement',[(False,False),(True,False),(True,True)])
def test_689_zip_sources_exports_complements_et_anciennes_versions(application,comparatif,complement):
    with closing(client(application)[0]) as api:
        v=creer(api)
        if comparatif:
            v=ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':v['contenu']['sources']['n'],
                'lignes_n1':[{k:(format(Decimal(value)/2,'.2f') if k!='compte' else value) for k,value in r.items()} for r in v['contenu']['sources']['n']],
                'fichier_n':'../../ne_pas_extraire.xlsx','fichier_n1':'=FORMULE.xlsx'}),201)
        source=deepcopy(v)
        if complement:v=ok(api.post(chemin(v),json=demande(v)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        avant=donnees_metier(application)
        r=api.get(BASE+f'/{v["id"]}/zip')
        assert r.status_code==200,r.text
        assert r.headers['Content-Type']=='application/zip' and r.headers['Cache-Control']=='no-store'
        assert f'_v{v["version"]}.zip' in r.headers['Content-Disposition']
        verifier_bundle(r.content,v)
        assert ok(api.get(BASE+f'/{source["id"]}'))==source
        assert donnees_metier(application)==avant


def test_689_lecteur_autorise_autre_societe_refusee(application):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as lecteur:
        v=creer(api);sid=ok(api.get('/api/auth/me'))['societe_id']
        assert lecteur.get(BASE+f'/{v["id"]}/zip').status_code==404
        lemail=ok(lecteur.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':lemail,'role':'lecture'}))
        token=ok(lecteur.post(f'/api/societes/switcher/{sid}'))['access_token'];lecteur.headers['Authorization']='Bearer '+token
        avant=donnees_metier(application);r=lecteur.get(BASE+f'/{v["id"]}/zip')
        assert r.status_code==200,r.text
        verifier_bundle(r.content,v,False)
        assert donnees_metier(application)==avant


def test_689_ancien_snapshot_sources_absentes_et_logo_historique_incompatible(application):
    from services.balance_preparation_dossier_service import generer_dossier
    from services.balance_import_service import empreinte_preparation
    with closing(client(application)[0]) as api:
        v=creer(api)
    ancien=deepcopy(v);ancien['contenu']['sources']['n']=None
    ancien['empreinte_sha256']=empreinte_preparation(ancien['contenu'])
    societe=SimpleNamespace(raison_sociale='Société fictive historique689',logo_url='https://ne-jamais-ouvrir.invalid/logo.png')
    raw=generer_dossier(ancien,societe);manifeste=verifier_bundle(raw,ancien,False)
    assert manifeste['sources_absentes']==['n','n1']
    ancien['contenu']['preparation']['pret_a_deposer']=True
    with pytest.raises(ValueError,match='Empreinte'):generer_dossier(ancien,societe)
