"""B1 : montants exacts, absence de ventilation inventée, PostgreSQL jetable."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import json,hashlib
import pytest
from sqlalchemy.orm import Session
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_cpc703_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier,body,url as cpc_url)
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/non-valeurs'


def creer(api,comparatif=True,technique=False):
    n=[{'compte':'1111','credit':'10000'},{'compte':'2111','debit':'4000'},
       {'compte':'28111','credit':'1000'},{'compte':'5141','debit':'7100' if technique else '7000'}]
    if technique:n.append({'compte':'1191','credit':'100'})
    n1=[{'compte':'1111','credit':'10000'},{'compte':'2111','debit':'3000'},
        {'compte':'28111','credit':'500'},{'compte':'5141','debit':'7500'}]
    return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n,'lignes_n1':n1 if comparatif else None,
        'fichier_n':'Fictif705_N.csv','fichier_n1':'Fictif705_N1.csv' if comparatif else None}),201)


def source():
    return {'contenu':{'sources':{'n':[{'compte':'2111','debit':'4000.00','credit':'0.00'},
        {'compte':'28111','debit':'0.00','credit':'1000.00'}],'n1':None},
        'preparation':{'etats':{'bilan':{'actif':{'immobilise':[{'code':'21','brut':4000,'amort_prov':1000,'net':3000}]}}}}}}


@pytest.mark.parametrize('cas',['normal','n1','source_absente','incomplete','bilan_absent','ecart','inverses','grand','zero','technique'])
def test_705_oracle_exact_brut_amort_net_et_inconnus(cas):
    from services.balance_non_valeurs_service import calculer,presentation
    d=source();c=d['contenu']
    if cas=='n1':c['sources']['n1']=deepcopy(c['sources']['n']);c['preparation']['etats_n1']=deepcopy(c['preparation']['etats'])
    elif cas=='source_absente':c['sources']['n']=None
    elif cas=='incomplete':c['sources']['n'][0].pop('debit')
    elif cas=='bilan_absent':c['preparation']['etats']={}
    elif cas=='ecart':c['preparation']['etats']['bilan']['actif']['immobilise'][0]['net']=2999.99
    elif cas=='inverses':c['sources']['n']=[{'compte':'2111','debit':'0','credit':'20.01'},{'compte':'28111','debit':'5.02','credit':'0'}]
    elif cas=='grand':c['sources']['n']=[{'compte':c,'debit':'9999999999999.99','credit':'0'} for c in ('2111','2112')]
    elif cas=='zero':c['sources']['n']=[]
    elif cas=='technique':c['preparation']['etats']['cpc']={'disponible':False,'motif':'Solde technique119'}
    avant=deepcopy(d);v=calculer(d);assert d==avant and presentation(d)['vue'] is None and not v['pret_a_deposer']
    json.dumps(v,allow_nan=False);n=v['periodes']['n'];n1=v['periodes']['n1']
    if cas in ('source_absente','incomplete'):assert not n['disponible'] and n['net'] is None and not n['lignes']
    else:
        assert n['disponible'] and all(r['intitule'] is None and 'net' not in r for r in n['lignes'])
        if cas=='inverses':assert n['brut']=='-20.01' and n['amortissements']=='-5.02' and n['net']=='-14.99'
        elif cas=='grand':assert n['brut']=='19999999999999.98' and n['net']==n['brut']
        elif cas=='zero':assert n['brut']==n['amortissements']==n['net']=='0.00'
        else:
            assert n['brut']=='4000.00' and n['amortissements']=='1000.00' and n['net']=='3000.00'
            if cas=='bilan_absent':assert n['bilan_net'] is n['ecart_net'] is None
            else:assert Decimal(n['ecart_net'])==(Decimal('.01') if cas=='ecart' else 0)
    if cas=='n1':assert n1==n
    else:assert not n1['disponible'] and n1['net'] is None


@pytest.mark.parametrize('v',['NaN','Infinity','-1','0.001',True])
def test_705_montants_invalides_aucun_total(v):
    from services.balance_non_valeurs_service import calculer
    d=source();d['contenu']['sources']['n'][0]['debit']=v
    with pytest.raises(ValueError):calculer(d)


def test_705_snapshot_rejeu_complement_b11_et_inconnus(application,monkeypatch):
    from services import balance_non_valeurs_service as service
    from routers.etats import BalanceNonValeursIn
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(cpc_url(v),json=body(v)),201);avant=donnees_metier(application)
        assert not ok(api.get(url(v)))['conserve'];b=body(v);r=ok(api.post(url(v),json=b),201)
        assert r['version']==3 and all(r['contenu'][k]==x for k,x in v['contenu'].items())
        vue=ok(api.get(url(r)));n=vue['vue']['periodes']['n'];n1=vue['vue']['periodes']['n1']
        assert n['net']=='3000.00' and n1['net']=='2500.00' and Decimal(n['ecart_net'])==0
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
        def interdit(*a,**kw):raise AssertionError('Pas de recalcul lecture/rejeu')
        monkeypatch.setattr(service,'calculer',interdit)
        assert service.presentation(r)['vue']==vue['vue']
        with Session(application['engine']) as db:assert service.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceNonValeursIn.model_validate(b))==r
        assert ok(api.get(url(r)))==vue
        assert api.post(url(r),json={**b,'empreinte_parent':r['empreinte_sha256']}).status_code==409


def test_705_exports_logo_bilan_fige_sources_exactes(application):
    with closing(client(application)[0]) as api:
        v=creer(api);r=ok(api.post(url(v),json=body(v)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        x=api.get(BASE+f'/{r["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));assert wb['Non-valeurs N']['D2'].value==4000 and wb['Non-valeurs N']['D3'].value==1000
        assert wb['Contrôle non-valeurs N']['B4'].value==3000 and wb['Contrôle non-valeurs N-1']['B4'].value==2500
        with ZipFile(BytesIO(x.content)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
        p=api.get(BASE+f'/{r["id"]}/pdf');assert p.status_code==200
        pdf=PdfReader(BytesIO(p.content));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert 'B1' in t and '28111' in t and 'Amortissement groupé' in t and any(p.images for p in pdf.pages)
        z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert json.loads(zip.read('non_valeurs_documentaires.json'))['vue']==r['contenu']['non_valeurs_documentaires']['vue']
            m=json.loads(zip.read('MANIFESTE_SHA256.json'));assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
        assert donnees_metier(application)==avant


@pytest.mark.parametrize('comparatif,technique',[(False,False),(True,True)])
def test_705_comparatif_absent_technique_non_blocant(application,comparatif,technique):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif,technique);r=ok(api.post(url(v),json=body(v)),201);vue=ok(api.get(url(r)))['vue']
        assert vue['periodes']['n']['net']=='3000.00'
        if not comparatif:assert vue['periodes']['n1']['net'] is None
        if technique:assert r['contenu']['preparation']['etats']['cpc']['disponible'] is False


def test_705_droits_intersociete_hash_strict_devise_et_concurrence(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);b=body(v)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=b).status_code==404
        avant=donnees_metier(application)
        bad={**b,'empreinte_parent':'a'*64};assert api.post(url(v),json=bad).status_code==409
        for data in ({**b,'vue':{}},{**b,'cle':'non-uuid'},{'cle':str(uuid4())}):assert api.post(url(v),json=data).status_code==422
        assert donnees_metier(application)==avant
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}))
        assert api.post(url(v),json=body(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200

