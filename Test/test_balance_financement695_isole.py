"""Financement documentaire sur PostgreSQL nonce et oracle arithmétique distinct."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from datetime import date
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_etic_notes693_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier,notes,url as notes_url)
from test_logo_societe import image_data


def creer(api,comparatif=True,technique=False):
    n=[{'compte':'1111','credit':'10000'},{'compte':'1481','credit':'5000'},
       {'compte':'1191' if technique else '7111','credit':'2000'},
       {'compte':'2332','debit':'4000'},{'compte':'3421','debit':'5000'},{'compte':'5141','debit':'8000'}]
    n1=[{'compte':'1111','credit':'6000'},{'compte':'3421','debit':'2000'},{'compte':'5141','debit':'4000'}]
    return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n,
        'lignes_n1':n1 if comparatif else None,'fichier_n':'Balance_fictive695_N.csv',
        'fichier_n1':'Balance_fictive695_N1.csv' if comparatif else None}),201)


def url(v):return BASE+f'/{v["id"]}/financement'


def flux(v,complet=True,n1=False):
    from services.balance_financement_service import CHAMPS
    valeurs={'augmentations_capitaux_propres':'4000','augmentations_dettes_financement':'5000',
             'acquisitions_immobilisations_corporelles':'4000'}
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'lignes':[
        {'code':k,'n':valeurs.get(k,'0') if complet or k=='augmentations_capitaux_propres' else None,
         'justification_n':'État de flux fictif695 N',
         'n1':('6000' if k=='augmentations_capitaux_propres' else '0') if n1 else None,
         'justification_n1':'État fictif695 N-1' if n1 else ''} for k,_ in CHAMPS]}


def test_695_initial_et_partiel_n_inconnus_jamais_zeros(application):
    with closing(client(application)[0]) as api:
        v=creer(api);vue=ok(api.get(url(v)))
        assert vue['flux_renseignes']=={'n':0,'n1':0} and vue['caf']=={'n':2000.0,'n1':0.0}
        assert all(r['n'] is None and r['n1'] is None for r in vue['lignes'])
        assert vue['tableau']['total_ressources'] is None and vue['tableau']['controle'] is None
        assert all(r['montant'] is None and r['n1'] is None for r in vue['tableau']['ressources'])
        before=donnees_metier(application);v2=ok(api.post(url(v),json=flux(v,False)),201)
        vue=ok(api.get(url(v2)));assert vue['flux_renseignes']=={'n':1,'n1':0}
        assert vue['tableau']['total_emplois'] is None and vue['tableau']['ecart_controle'] is None
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        after=donnees_metier(application)
        assert all(after[k]==rows for k,rows in before.items() if k!='liasse_balances_preparation')


def test_695_oracle_independant_flux_n_n1_controles_et_rejeu(application,monkeypatch):
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(notes_url(v),json=notes(v)),201);body=flux(v,n1=True)
        saved=ok(api.post(url(v),json=body),201);vue=ok(api.get(url(saved)));tf=vue['tableau']
        # Oracle : CAF2000 + capital4000 + emprunt5000 =11000 ; acquisition4000.
        # FRN=10000+5000+2000-4000=13000 ; FRN1=6000 => +7000.
        # BFG5000-2000=+3000 ; trésorerie8000-4000=+4000 ;7000-3000=4000.
        assert tf['total_ressources']==11000 and tf['total_emplois']==4000
        assert tf['total_ressources_n1']==6000 and tf['total_emplois_n1']==0 and tf['ecart_nul'] is True
        assert tf['variation_fonds_roulement']==7000 and tf['variation_bfg']==3000 and tf['variation_tresorerie']==4000
        assert tf['ecart_controle']==tf['ecart_total_general']==0 and tf['controle'] is True
        assert tf['total_general_ressources']==tf['total_general_emplois']==11000
        assert vue['calcul_disponible']=={'n':True,'n1':True} and not vue['pret_a_deposer']
        assert saved['contenu']['notes_etic_documentaires']==v['contenu']['notes_etic_documentaires']
        assert ok(api.post(url(v),json=body),201)==saved
        body['lignes'][0]['n']='1';assert api.post(url(v),json=body).status_code==409
        from services import balance_financement_service as service
        def interdit(*a,**kw):raise AssertionError('Ne pas recalculer une ancienne version')
        monkeypatch.setattr(service,'calculer_tableau_financement',interdit)
        snap=deepcopy(saved);assert service.presentation(snap)['tableau']==tf
        assert snap==saved


@pytest.mark.parametrize('champ,valeur',[
    ('n','NaN'),('n','Infinity'),('n','-Infinity'),('n',True),('n',{}),('n','-1'),
    ('n','0.001'),('n','10000000000000'),('justification_n',' '),('code','inconnu'),
    ('justification_n',True),('extra','refusé')],ids=['nan','inf','moinsinf','bool','objet','negatif','decimales','borne','justification','code','reference_bool','extra'])
def test_695_invalides_sans_mutation(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);body=flux(v);body['lignes'][0][champ]=valeur;avant=donnees_metier(application)
        assert api.post(url(v),json=body).status_code==422
        assert donnees_metier(application)==avant


def test_695_absence_n1_et_balance_apres_solde_technique(application):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif=False);body=flux(v)
        child=ok(api.post(url(v),json=body),201);vue=ok(api.get(url(child)))
        assert vue['tableau']['total_ressources']==11000 and vue['tableau']['total_emplois']==4000
        assert vue['tableau']['variation_fonds_roulement'] is None and vue['tableau']['ecart_controle'] is None
        assert all(r['n1'] is None for r in vue['tableau']['ressources'])
        body=flux(v,n1=True);assert api.post(url(v),json=body).status_code==422
        v=creer(api,technique=True);child=ok(api.post(url(v),json=flux(v)),201)
        vue=ok(api.get(url(child)));assert vue['caf']['n'] is None and not vue['calcul_disponible']['n']
        assert vue['tableau']['total_ressources'] is None and vue['tableau']['ecart_controle'] is None


def test_695_ecart_visible_sans_correction_et_exports_meme_snapshot(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=flux(v);body['lignes'][0]['n']='1000'
        body['lignes'][0]['justification_n']='=1+1 <source fictive & non exécutée>'
        v=ok(api.post(url(v),json=body),201);vue=ok(api.get(url(v)));assert vue['tableau']['ecart_controle']==-1000
        assert vue['tableau']['controle'] is False
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        r=api.get(BASE+f'/{v["id"]}/zip');assert r.status_code==200,r.text
        with ZipFile(BytesIO(r.content)) as z:
            assert z.testzip() is None
            d=json.loads(z.read('financement_documentaire.json'))
            assert d=={k:value for k,value in vue.items() if k not in ('id','version','empreinte_sha256')}
            m=json.loads(z.read('MANIFESTE_SHA256.json'))
            for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
            wb=load_workbook(BytesIO(z.read('preparation.xlsx')))
            assert 'Logo société' in wb.sheetnames and wb['Flux documentaires']['E2'].data_type=='s'
            assert wb['Flux documentaires']['E2'].value==body['lignes'][0]['justification_n']
            rows=dict(list(wb['Financement contrôle'].values)[1:]);assert rows['Écart de rapprochement']==-1000
            pdf=PdfReader(BytesIO(z.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert 'Financement documentaire' in t and '<source fictive & non exécutée>' in t and '-1 000,00' in t
            assert any(p.images for p in pdf.pages)
        assert donnees_metier(application)==avant


def test_695_permissions_doublons_devise_empreinte_et_concurrence(application):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre:
        v=creer(api);assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=flux(v)).status_code==404
        body=flux(v);body['empreinte_parent']='0'*64;assert api.post(url(v),json=body).status_code==409
        body=flux(v);body['lignes']*=2;assert api.post(url(v),json=body).status_code==422
        sid=ok(api.get('/api/auth/me'))['societe_id'];email2=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email2,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=flux(v)).status_code==403
        body=flux(v)
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=body),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=flux(v)).status_code==409


def test_695_borne_precision_conserve_details_exacts_sans_totaux_approximatifs(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=flux(v)
        for r in body['lignes']:r['n']='9999999999999.99'
        saved=ok(api.post(url(v),json=body),201);vue=ok(api.get(url(saved)))
        assert vue['tableau'] is None and vue['motif_precision'].startswith('Limite technique')
        assert all(r['n']=='9999999999999.99' for r in vue['lignes'])
        assert not vue['calcul_disponible']['n'] and vue['flux_renseignes']['n']==16
        x=api.get(BASE+f'/{saved["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));assert 'Financement contrôle' not in wb.sheetnames
        assert ('Limite technique',vue['motif_precision']) in list(wb['Origine financement'].values)
        p=api.get(BASE+f'/{saved["id"]}/pdf');assert p.status_code==200
        assert 'Limite technique' in '\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(p.content)).pages)


def test_695_ecart_de_cinquante_centimes_reste_visible(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=flux(v);body['lignes'][0]['n']='0.50'
        v=ok(api.post(url(v),json=body),201);tf=ok(api.get(url(v)))['tableau']
        assert tf['ecart_controle']==-0.5 and tf['ecart_nul'] is False
        # Le seuil historique du moteur n'est pas une conclusion d'écart nul.
        assert tf['controle'] is True
