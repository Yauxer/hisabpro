"""Cessions711 documentaires : oracles, snapshots, export et sécurité native."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
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
    application089,application087,migration,client,ok,creer,BASE)
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/cessions'


def body(v):
    return {'empreinte_parent':v['empreinte_sha256'],'cle':str(uuid4()),'tables':[
      {'code':'B3','statut':'documente','justification':'Registre fictif711 et pièces de sortie',
       'lignes':[{'designation':'Machine Atlas fictive','date_sortie':'2026-06-30','type_sortie':'cession',
          'valeur_entree':'10000','vna':'6000','prix_cession':'5000','reference_source':'Acte fictif711 A'},
         {'designation':'Matériel Rif fictif','date_sortie':'2026-09-15','type_sortie':'retrait',
          'valeur_entree':'3000','vna':'0','prix_cession':'0','reference_source':'PV fictif711 B'}]}]}


@pytest.mark.parametrize('cas',['connus','inconnu','zero','positif','centime','grand','neant','alertes'])
def test_711_oracles_independants(cas):
    from services.balance_cessions_service import normaliser,calculer_controles,presentation
    from routers.etats import BalanceCessionsIn
    d={'contenu':{'periode':{'debut':'2026-01-01','fin':'2026-12-31'}}};q=body({'empreinte_sha256':'a'*64});r=q['tables'][0]['lignes'][0]
    if cas=='inconnu':r['prix_cession']=None
    elif cas=='zero':r.update(vna='0',prix_cession='0')
    elif cas=='positif':r['prix_cession']='7000'
    elif cas=='centime':r['prix_cession']='5999.99'
    elif cas=='grand':r.update(vna='9999999999999.99',prix_cession='0')
    elif cas=='neant':q['tables'][0].update(statut='neant_declare',lignes=[])
    elif cas=='alertes':r.update(vna='10001',date_sortie='2025-12-31')
    avant=deepcopy(d);tables=normaliser(d,BalanceCessionsIn.model_validate(q).tables)
    c=calculer_controles(d,{'tables':tables});assert d==avant and presentation(d)['controle_cessions'] is None
    attendu={'connus':'-1000.00','inconnu':None,'zero':'0.00','positif':'1000.00','centime':'-0.01',
       'grand':'-9999999999999.99','neant':None,'alertes':'-5001.00'}[cas]
    assert c['total_difference_prix_vna']==attendu
    assert len(c['alertes'])==(2 if cas=='alertes' else 1 if cas=='grand' else 0)
    json.dumps(c,allow_nan=False)


@pytest.mark.parametrize('champ,valeur',[
    ('designation',' '),('reference_source',''),('date_sortie','2026-02-30'),('date_sortie','30/06/2026'),
    ('type_sortie','invente'),('vna','NaN'),('vna','Infinity'),('vna',True),('vna','-1'),
    ('prix_cession','0.001'),('prix_cession','10000000000000'),('valeur_entree','-1'),('inconnu','interdit')])
def test_711_invalides_sans_mutation(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
        assert api.post(url(v),json=q).status_code==422
        assert donnees_metier(application)==avant


def test_711_snapshot_rejeu_et_dates_facultatives(application,monkeypatch):
    from services import balance_cessions_service as service
    from routers.etats import BalanceCessionsIn
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0].update(date_sortie='',type_sortie='',valeur_entree=None)
        avant=donnees_metier(application);r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
        assert all(r['contenu'][k]==x for k,x in v['contenu'].items())
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        assert vue['controle_cessions']['total_difference_prix_vna']=='-1000.00'
        apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
        def interdit(*a,**k):raise AssertionError('Recalcul ancien/rejeu interdit')
        monkeypatch.setattr(service,'calculer_controles',interdit)
        with Session(application['engine']) as db:
            user=ok(api.get('/api/auth/me'));assert service.conserver(db,user,v['id'],BalanceCessionsIn.model_validate(q))==r
        assert service.presentation(r)['controle_cessions']==vue['controle_cessions']


def test_711_exports_exactitude_logo_et_manifestes(application):
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0].update(designation='=1+2\n<Machine fictive & preuve>',prix_cession='5999.99')
        r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
        with ZipFile(BytesIO(rep.content)) as z:
            assert z.testzip() is None
            assert json.loads(z.read('cessions_documentaires.json'))=={k:v for k,v in vue.items() if k not in ('id','version','empreinte_sha256')}
            w=load_workbook(BytesIO(z.read('preparation.xlsx')))
            assert w['Cessions déclarées N']['A2'].data_type=='s' and w['Cessions déclarées N']['A2'].value.startswith('=1+2')
            assert w['Contrôle cessions']['B2'].value==-0.01 and w['Contrôle cessions']['B4'].value==-0.01
            p=PdfReader(BytesIO(z.read('preparation.pdf')));txt='\n'.join(x.extract_text() or '' for x in p.pages)
            assert '<Machine fictive & preuve>' in txt and any(list(x.images) for x in p.pages)
            m=json.loads(z.read('MANIFESTE_SHA256.json'))
            for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
        assert donnees_metier(application)==avant


def test_711_droits_empreintes_concurrence_et_neant(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);q=body(v)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=q).status_code==404
        mauvais=deepcopy(q);mauvais['empreinte_parent']='0'*64;assert api.post(url(v),json=mauvais).status_code==409
        for k,val in [('cle','invalide'),('controle_cessions',{})]:
            mauvais=deepcopy(q);mauvais[k]=val;assert api.post(url(v),json=mauvais).status_code==422
        mauvais=deepcopy(q);mauvais['tables']=[];assert api.post(url(v),json=mauvais).status_code==422
        with ThreadPoolExecutor(max_workers=2) as ex:
            reps=list(ex.map(lambda _:api.post(url(v),json=q),range(2)))
        assert all(r.status_code==201 for r in reps) and reps[0].json()==reps[1].json()
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=q).status_code==403
        q=body(v);q['tables'][0].update(statut='neant_declare',lignes=[])
        r=ok(api.post(url(v),json=q),201);assert ok(api.get(url(r)))['controle_cessions']['total_difference_prix_vna'] is None
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
