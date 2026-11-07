"""Mouvements713 déclarés : sources explicites et contrôle arithmétique figé."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date
from io import BytesIO
from zipfile import ZipFile
from uuid import uuid4
import hashlib,json
import pytest
from sqlalchemy.orm import Session
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_emetteurs709_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE)
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/mouvements'


def creer(api):
    n=[{'compte':'1111','credit':'10000'},{'compte':'2340','debit':'11000'},{'compte':'2834','credit':'4500'},
       {'compte':'1511','credit':'700'},{'compte':'5141','debit':'4200'}]
    n1=[{'compte':'1111','credit':'10000'},{'compte':'2340','debit':'10000'},{'compte':'2834','credit':'4000'},
        {'compte':'1511','credit':'500'},{'compte':'5141','debit':'4500'}]
    return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n,'lignes_n1':n1,
        'fichier_n':'Fictif713_N.csv','fichier_n1':'Fictif713_N1.csv'}),201)


def body(v):
    tables=[]
    for code,nature,debut,aug,dim,fin in [('B2','Matériel de transport fictif','10000','2000','1000','11000'),
       ('B2bis','Amortissements transport fictifs','4000','1000','500','4500'),
       ('B5','Litige fictif','500','300','100','700')]:
        tables.append({'code':code,'statut':'documente','justification':'Registre fictif713 '+code,
           'lignes':[{'nature':nature,'debut':debut,'augmentations':aug,'diminutions':dim,'fin':fin,
              'reference_source':'Pièce fictive713 '+code}]})
    return {'empreinte_parent':v['empreinte_sha256'],'cle':str(uuid4()),'tables':tables}


@pytest.mark.parametrize('cas',['connus','inconnu','inverse','centime','grand','zero','neant','positif'])
def test_713_oracles_independants(cas):
    from services.balance_mouvements_service import normaliser,calculer_controles,presentation
    from routers.etats import BalanceMouvementsIn
    d={'contenu':{}};q=body({'empreinte_sha256':'a'*64});r=q['tables'][0]['lignes'][0]
    if cas=='inconnu':r['augmentations']=None
    elif cas=='inverse':r.update(debut='-100',augmentations='0',diminutions='0',fin='-100')
    elif cas=='centime':r['fin']='10999.99'
    elif cas=='grand':r.update(debut='9999999999999.99',augmentations='9999999999999.99',diminutions='0',fin=None)
    elif cas=='zero':r.update(debut='0',augmentations='0',diminutions='0',fin='0')
    elif cas=='neant':q['tables'][0].update(statut='neant_declare',lignes=[])
    elif cas=='positif':r['fin']='11000.01'
    avant=deepcopy(d);tables=normaliser(d,BalanceMouvementsIn.model_validate(q).tables);c=calculer_controles(d,{'tables':tables})
    assert d==avant and presentation(d)['controle_mouvements'] is None
    ecart={'connus':'0.00','inconnu':None,'inverse':'0.00','centime':'-0.01','grand':None,'zero':'0.00','neant':None,'positif':'0.01'}[cas]
    assert c['tableaux']['B2']['totaux']['ecart_fin']==ecart
    assert c['tableaux']['B2bis']['totaux']['fin_reconstituee']=='4500.00'
    assert c['tableaux']['B5']['totaux']['fin_reconstituee']=='700.00'
    if cas=='grand':assert c['tableaux']['B2']['totaux']['fin_reconstituee']=='19999999999999.98'
    json.dumps(c,allow_nan=False)


@pytest.mark.parametrize('champ,valeur',[
 ('nature',' '),('reference_source',''),('debut','NaN'),('debut','Infinity'),('debut',True),('debut','0.001'),
 ('augmentations','-1'),('augmentations','NaN'),('diminutions','-1'),('fin','Infinity'),
 ('fin','10000000000000'),('inconnu','interdit'),('augmentations',True),('diminutions','0.001')])
def test_713_invalides_sans_mutation(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
        assert api.post(url(v),json=q).status_code==422
        assert donnees_metier(application)==avant


def test_713_snapshot_rejeu_et_inconnus(application,monkeypatch):
    from services import balance_mouvements_service as service
    from routers.etats import BalanceMouvementsIn
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0]['augmentations']=None
        avant=donnees_metier(application);r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
        assert all(r['contenu'][k]==x for k,x in v['contenu'].items()) and ok(api.get(BASE+f'/{v["id"]}'))==v
        assert vue['controle_mouvements']['tableaux']['B2']['totaux']['ecart_fin'] is None
        apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
        def interdit(*a,**k):raise AssertionError('Recalcul ancien/rejeu interdit')
        monkeypatch.setattr(service,'calculer_controles',interdit)
        with Session(application['engine']) as db:assert service.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceMouvementsIn.model_validate(q))==r
        assert service.presentation(r)['controle_mouvements']==vue['controle_mouvements']


def test_713_exports_exactitude_logo_et_manifestes(application):
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0].update(nature='=1+2\n<Transport fictif & preuve>',fin='10999.99')
        r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
        with ZipFile(BytesIO(rep.content)) as z:
            assert z.testzip() is None and json.loads(z.read('mouvements_documentaires.json'))=={k:v for k,v in vue.items() if k not in ('id','version','empreinte_sha256')}
            w=load_workbook(BytesIO(z.read('preparation.xlsx')))
            assert w['Mouvements B2']['A2'].data_type=='s' and w['Mouvements B2']['A2'].value.startswith('=1+2')
            assert w['Contrôle MV B2']['D2'].value==-0.01 and w['Contrôle MV B2bis']['B2'].value==4500 and w['Contrôle MV B5']['B2'].value==700
            p=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(x.extract_text() or '' for x in p.pages)
            assert '<Transport fictif & preuve>' in txt and any(list(x.images) for x in p.pages)
            m=json.loads(z.read('MANIFESTE_SHA256.json'))
            for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
        assert donnees_metier(application)==avant
        q=body(r);q['tables'][0]['lignes'][0].update(debut='9999999999999.99',augmentations='9999999999999.99',diminutions='0',fin=None)
        grand=ok(api.post(url(r),json=q),201);rep=api.get(BASE+f'/{grand["id"]}/xlsx');assert rep.status_code==200
        w=load_workbook(BytesIO(rep.content));assert w['Contrôle MV B2']['B2'].value=='19999999999999.98' and w['Contrôle MV B2']['B2'].data_type=='s'


def test_713_droits_empreintes_concurrence_et_neant(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);q=body(v)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=q).status_code==404
        mauvais=deepcopy(q);mauvais['empreinte_parent']='0'*64;assert api.post(url(v),json=mauvais).status_code==409
        for k,val in [('cle','invalide'),('controle_mouvements',{}),('tables',q['tables'][:2])]:
            mauvais=deepcopy(q);mauvais[k]=val;assert api.post(url(v),json=mauvais).status_code==422
        mauvais=deepcopy(q);mauvais['tables'][2]['code']='B2';assert api.post(url(v),json=mauvais).status_code==422
        with ThreadPoolExecutor(max_workers=2) as ex:reps=list(ex.map(lambda _:api.post(url(v),json=q),range(2)))
        assert all(r.status_code==201 for r in reps) and reps[0].json()==reps[1].json()
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=q).status_code==403
        q=body(v);q['tables'][0].update(statut='neant_declare',lignes=[])
        r=ok(api.post(url(v),json=q),201);assert ok(api.get(url(r)))['controle_mouvements']['tableaux']['B2']['totaux']['ecart_fin'] is None
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
