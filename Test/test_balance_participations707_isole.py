"""B4 : oracle exact, périmètre251 distinct du24/25, snapshots isolés."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
import json,hashlib
import pytest
from sqlalchemy.orm import Session
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_non_valeurs705_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier,body,cpc_url,url as nv_url)
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/participations'


def creer(api,comparatif=True,technique=False):
    n=[{'compte':'1111','credit':'10000'},{'compte':'2510','debit':'4000'},
       {'compte':'2411','debit':'2000'},{'compte':'5141','debit':'4100' if technique else '4000'}]
    if technique:n.append({'compte':'1191','credit':'100'})
    n1=[{'compte':'1111','credit':'10000'},{'compte':'2510','debit':'3000'},
        {'compte':'2411','debit':'1000'},{'compte':'5141','debit':'6000'}]
    return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n,'lignes_n1':n1 if comparatif else None,
        'fichier_n':'Fictif707_N.csv','fichier_n1':'Fictif707_N1.csv' if comparatif else None}),201)


def source():
    return {'contenu':{'sources':{'n':[{'compte':'2510','debit':'4000.00','credit':'0.00'},
        {'compte':'2411','debit':'2000.00','credit':'0.00'}],'n1':None},
        'preparation':{'etats':{'bilan':{'actif':{'immobilise':[{'code':'24/25','brut':6000,'amort_prov':0,'net':6000}]}}}}}}


@pytest.mark.parametrize('cas',['normal','n1','source_absente','incomplete','bilan_absent','ecart','inverses','grand','zero','technique','sans251','duplique'])
def test_707_oracle_perimetre_exact_et_informations_inconnues(cas):
    from services.balance_participations_service import calculer,presentation
    d=source();c=d['contenu']
    if cas=='n1':c['sources']['n1']=deepcopy(c['sources']['n']);c['preparation']['etats_n1']=deepcopy(c['preparation']['etats'])
    elif cas=='source_absente':c['sources']['n']=None
    elif cas=='incomplete':c['sources']['n'][0].pop('debit')
    elif cas=='bilan_absent':c['preparation']['etats']={}
    elif cas=='ecart':c['preparation']['etats']['bilan']['actif']['immobilise'][0]['brut']=5999.99
    elif cas=='inverses':c['sources']['n']=[{'compte':'2510','debit':'0','credit':'20.01'},{'compte':'2411','debit':'5.02','credit':'0'}]
    elif cas=='grand':c['sources']['n']=[{'compte':c,'debit':'9999999999999.99','credit':'0'} for c in ('2510','25101')]
    elif cas=='zero':c['sources']['n']=[]
    elif cas=='sans251':c['sources']['n']=c['sources']['n'][1:]
    elif cas=='technique':c['preparation']['etats']['cpc']={'disponible':False,'motif':'Solde technique119'}
    elif cas=='duplique':c['sources']['n'].append({'compte':'2510','debit':'0.01','credit':'0.01'})
    avant=deepcopy(d);v=calculer(d);assert d==avant and presentation(d)['vue'] is None and not v['pret_a_deposer']
    json.dumps(v,allow_nan=False);n=v['periodes']['n'];n1=v['periodes']['n1']
    assert len(v['informations_a_completer'])==4
    if cas in ('source_absente','incomplete'):assert not n['disponible'] and n['participations'] is None and not n['lignes']
    else:
        assert n['disponible'] and all(all(r[k] is None for k in ('intitule','emetteur','capital_emetteur','quote_part','produits_recus')) for r in n['lignes'])
        assert 'ecart_participations' not in n and 'bilan_participations' not in n
        if cas=='inverses':assert n['participations']=='-20.01' and n['financieres_brut']=='-14.99'
        elif cas=='grand':assert n['participations']==n['financieres_brut']=='19999999999999.98'
        elif cas=='zero':assert n['participations']==n['autres_financieres']==n['financieres_brut']=='0.00'
        elif cas=='sans251':assert n['participations']=='0.00' and n['financieres_brut']=='2000.00' and not n['lignes']
        else:
            assert n['participations']=='4000.00' and n['autres_financieres']=='2000.00' and n['financieres_brut']=='6000.00'
            if cas=='bilan_absent':assert n['bilan_financieres_brut'] is n['ecart_financieres_brut'] is None
            else:assert Decimal(n['ecart_financieres_brut'])==(Decimal('.01') if cas=='ecart' else 0)
    if cas=='n1':assert n1==n
    else:assert not n1['disponible'] and n1['participations'] is None


@pytest.mark.parametrize('v',['NaN','Infinity','-1','0.001',True])
def test_707_montants_invalides_aucun_total(v):
    from services.balance_participations_service import calculer
    d=source();d['contenu']['sources']['n'][0]['debit']=v
    with pytest.raises(ValueError):calculer(d)


def test_707_snapshot_rejeu_b1_b11_preserves(application,monkeypatch):
    from services import balance_participations_service as service
    from routers.etats import BalanceParticipationsIn
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(cpc_url(v),json=body(v)),201);v=ok(api.post(nv_url(v),json=body(v)),201)
        avant=donnees_metier(application);assert not ok(api.get(url(v)))['conserve'];b=body(v);r=ok(api.post(url(v),json=b),201)
        assert r['version']==4 and all(r['contenu'][k]==x for k,x in v['contenu'].items())
        vue=ok(api.get(url(r)));assert vue['vue']['periodes']['n']['participations']=='4000.00'
        assert vue['vue']['periodes']['n1']['participations']=='3000.00' and Decimal(vue['vue']['periodes']['n']['ecart_financieres_brut'])==0
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
        def interdit(*a,**kw):raise AssertionError('Pas de recalcul lecture/rejeu')
        monkeypatch.setattr(service,'calculer',interdit)
        assert service.presentation(r)['vue']==vue['vue']
        with Session(application['engine']) as db:assert service.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceParticipationsIn.model_validate(b))==r
        assert ok(api.get(url(r)))==vue
        assert api.post(url(r),json={**b,'empreinte_parent':r['empreinte_sha256']}).status_code==409


def test_707_exports_inconnus_logo_precision_et_manifestes(application):
    from services.balance_participations_service import calculer
    from services.balance_preparation_export_service import generer_preparation_xlsx
    with closing(client(application)[0]) as api:
        v=creer(api);r=ok(api.post(url(v),json=body(v)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        x=api.get(BASE+f'/{r["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));assert wb['Participations N']['C2'].value==4000
        assert all(wb['Participations N'].cell(2,i).value=='Indisponible' for i in range(4,8))
        assert wb['Contrôle financier N']['B4'].value==6000 and Decimal(wb['Contrôle financier N']['D4'].value)==0 and wb['Contrôle financier N']['D4'].data_type=='s'
        assert wb['Contrôle financier N']['D2'].value=='Non comparable au24/25'
        with ZipFile(BytesIO(x.content)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
        p=api.get(BASE+f'/{r["id"]}/pdf');assert p.status_code==200
        pdf=PdfReader(BytesIO(p.content));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert 'B4' in t and '2510' in t and 'Émetteur, capital, quote-part' in t and any(p.images for p in pdf.pages)
        z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert json.loads(zip.read('participations_documentaires.json'))['vue']==r['contenu']['participations_documentaires']['vue']
            m=json.loads(zip.read('MANIFESTE_SHA256.json'));assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
        assert donnees_metier(application)==avant
        variant=deepcopy(r);variant['contenu']['sources']['n']=[{'compte':c,'debit':'9999999999999.99','credit':'0'} for c in ('2510','25101')]
        variant['contenu']['participations_documentaires']['vue']=calculer(variant)
        w=load_workbook(BytesIO(generer_preparation_xlsx(variant,{'raison_sociale':'Fictif précision707'})))
        assert w['Contrôle financier N']['B2'].value=='19999999999999.98' and w['Contrôle financier N']['B2'].data_type=='s'


@pytest.mark.parametrize('comparatif,technique',[(False,False),(True,True)])
def test_707_comparatif_absent_technique_non_blocant(application,comparatif,technique):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif,technique);r=ok(api.post(url(v),json=body(v)),201);vue=ok(api.get(url(r)))['vue']
        assert vue['periodes']['n']['participations']=='4000.00'
        if not comparatif:assert vue['periodes']['n1']['participations'] is None
        if technique:assert r['contenu']['preparation']['etats']['cpc']['disponible'] is False


def test_707_droits_intersociete_hash_strict_devise_et_concurrence(application):
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

