"""B11 : oracle exact, versions immuables et PostgreSQL natif jetable."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from sqlalchemy.orm import Session
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_capital701_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier)
from test_balance_financement695_isole import creer
from test_balance_etic_annexes699_isole import annexes,url as annexes_url
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/detail-cpc'
def body(v):return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256']}


def source():
    return {'contenu':{'sources':{'n':[
        {'compte':'6132','debit':'1200.10','credit':'0'},
        {'compte':'6193','debit':'0','credit':'200.01'},
        {'compte':'7111','debit':'0','credit':'2000.30'},
        {'compte':'7119','debit':'100.02','credit':'0'},
        {'compte':'6171','debit':'100','credit':'100'},
        {'compte':'5141','debit':'999','credit':'0'}], 'n1':None},
        'preparation':{'etats':{'cpc':{'I':1900.28,'II':1000.09,'IV':0,'V':0,'VIII':0,'IX':0,'XII':0,'resultat_net':900.19}},'etats_n1':None}}}


@pytest.mark.parametrize('cas',['normal','comparatif','legacy','technique','cpc_absent','aggregate_absent','ecart','grand','source_sans_charge','inverse_n1','source_incomplete'])
def test_703_oracle_exact_sources_inconnues_et_signes(cas):
    from services.balance_cpc_detail_service import calculer,presentation
    d=source()
    if cas=='comparatif':
        d['contenu']['sources']['n1']=deepcopy(d['contenu']['sources']['n'])
        d['contenu']['preparation']['etats_n1']=deepcopy(d['contenu']['preparation']['etats'])
    elif cas=='legacy':d['contenu']['sources']['n']=None
    elif cas=='technique':d['contenu']['preparation']['etats']['cpc']={'disponible':False,'motif':'Après solde technique 119'}
    elif cas=='source_incomplete':d['contenu']['sources']['n'][0].pop('debit')
    elif cas=='cpc_absent':d['contenu']['preparation']['etats']={}
    elif cas=='aggregate_absent':d['contenu']['preparation']['etats']['cpc'].pop('II')
    elif cas=='ecart':d['contenu']['preparation']['etats']['cpc']['resultat_net']=900.18
    elif cas=='grand':
        d['contenu']['sources']['n']=[{'compte':str(c),'debit':'9999999999999.99','credit':'0'} for c in (6111,6121)]
    elif cas=='source_sans_charge':d['contenu']['sources']['n']=[]
    elif cas=='inverse_n1':
        d['contenu']['sources']['n1']=[{'compte':'7111','debit':'30.09','credit':'0'}]
        d['contenu']['preparation']['etats_n1']=deepcopy(d['contenu']['preparation']['etats'])
    avant=deepcopy(d);v=calculer(d);assert d==avant and not v['pret_a_deposer']
    assert presentation(d)['vue'] is None # Une lecture ne fabrique jamais une archive.
    n=v['periodes']['n'];n1=v['periodes']['n1'];json.dumps(v,allow_nan=False)
    if cas in ('legacy','technique','cpc_absent','source_incomplete'):
        assert not n['disponible'] and n['charges'] is n['resultat'] is None and not n['lignes'] and n['motif']
    elif cas=='grand':assert n['charges']=='19999999999999.98' and n['ecart_charges']=='19999999998999.89'
    elif cas=='source_sans_charge':assert n['charges']==n['produits']==n['resultat']=='0.00'
    else:
        assert n['charges']=='1000.09' and n['produits']=='1900.28' and n['resultat']=='900.19'
        assert [r['montant'] for r in n['lignes']]==['1200.10','-200.01','2000.30','-100.02']
        assert all(r['intitule'] is None for r in n['lignes'])
        assert n['ecart_charges'] is None if cas=='aggregate_absent' else Decimal(n['ecart_charges'])==0
        assert Decimal(n['ecart_resultat'])==(Decimal('.01') if cas=='ecart' else 0)
    if cas=='comparatif':assert n1==n
    elif cas=='inverse_n1':assert n1['produits']=='-30.09' and n1['resultat']=='-30.09'
    else:assert not n1['disponible'] and n1['resultat'] is None


@pytest.mark.parametrize('valeur',['NaN','Infinity','-Infinity',True,'0.001','-1'])
def test_703_source_invalide_pas_de_total_fabrique(valeur):
    from services.balance_cpc_detail_service import calculer
    d=source();d['contenu']['sources']['n'][0]['debit']=valeur
    with pytest.raises(ValueError):calculer(d)


def test_703_snapshot_rejeu_sans_recalcul_et_complements(application,monkeypatch):
    from services import balance_cpc_detail_service as service
    from routers.etats import BalanceCpcDetailIn
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(annexes_url(v),json=annexes(v)),201)
        assert not ok(api.get(url(v)))['conserve'];avant=donnees_metier(application);b=body(v)
        saved=ok(api.post(url(v),json=b),201);assert saved['version']==3
        assert all(saved['contenu'][k]==val for k,val in v['contenu'].items())
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        vue=ok(api.get(url(saved)));assert vue['vue']['periodes']['n']['resultat']=='2000.00'
        assert vue['vue']['periodes']['n1']['resultat']=='0.00'
        assert Decimal(vue['vue']['periodes']['n']['ecart_resultat'])==0
        apres=donnees_metier(application);assert all(apres[k]==val for k,val in avant.items() if k!='liasse_balances_preparation')
        def interdit(*a,**kw):raise AssertionError('Recalcul interdit pendant lecture/rejeu')
        monkeypatch.setattr(service,'calculer',interdit)
        assert service.presentation(saved)['vue']==vue['vue']
        user=ok(api.get('/api/auth/me'))
        with Session(application['engine']) as db:
            assert service.conserver(db,user,v['id'],BalanceCpcDetailIn.model_validate(b))==saved
        assert ok(api.get(url(saved)))==vue
        b['empreinte_parent']=saved['empreinte_sha256']
        assert api.post(url(saved),json=b).status_code==409


def test_703_droits_intersociete_hash_strict_devise_et_concurrence(application):
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


@pytest.mark.parametrize('comparatif,technique',[(False,False),(True,True)])
def test_703_sources_n1_absentes_ou_soldees_conservees(application,comparatif,technique):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif=comparatif,technique=technique)
        r=ok(api.post(url(v),json=body(v)),201);vue=ok(api.get(url(r)))['vue']
        if technique:
            assert not vue['periodes']['n']['disponible']
            assert vue['periodes']['n']['resultat'] is None and not vue['periodes']['n']['lignes']
        if not comparatif:assert vue['periodes']['n1']['resultat'] is None


def test_703_exports_logo_manifestes_et_lecture_figee(application,monkeypatch):
    from services import balance_cpc_detail_service as service
    with closing(client(application)[0]) as api:
        v=creer(api);r=ok(api.post(url(v),json=body(v)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        avant=donnees_metier(application)
        def interdit(*a,**kw):raise AssertionError('Export ne recalcule pas B11')
        monkeypatch.setattr(service,'calculer',interdit)
        x=api.get(BASE+f'/{r["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));assert list(wb['Détail CPC N'].values)[1]==('7111','Libellé non conservé','Produit',2000)
        assert wb['Détail CPC N-1'].max_row==1 and wb['Rapprochement CPC N']['B4'].value==2000
        with ZipFile(BytesIO(x.content)) as z:assert any(n.startswith('xl/media/') for n in z.namelist())
        p=api.get(BASE+f'/{r["id"]}/pdf');assert p.status_code==200
        pdf=PdfReader(BytesIO(p.content));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert 'B11' in t and '7111' in t and 'Libellé non conservé' in t and any(p.images for p in pdf.pages)
        z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            vue=json.loads(zip.read('detail_cpc_documentaire.json'))
            assert vue['vue']==r['contenu']['detail_cpc_documentaire']['vue']
            m=json.loads(zip.read('MANIFESTE_SHA256.json'))
            assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
        assert donnees_metier(application)==avant



def test_703_import_reel_soldes_inverses_et_precision_excel(application):
    from datetime import date
    from services.balance_cpc_detail_service import calculer
    from services.balance_preparation_export_service import generer_preparation_xlsx
    with closing(client(application)[0]) as api:
        v=ok(api.post(BASE,json={'exercice':date.today().year,'fichier_n':'Fictif703.csv',
            'lignes_n':[{'compte':'1111','credit':'1000'},{'compte':'7111','credit':'2000.30'},
                {'compte':'6193','credit':'200.01'},{'compte':'6132','debit':'1200.10'},
                {'compte':'7119','debit':'100.02'},{'compte':'5141','debit':'1900.19'}]}),201)
        saved=ok(api.post(url(v),json=body(v)),201);n=ok(api.get(url(saved)))['vue']['periodes']['n']
        assert n['resultat']=='900.19' and Decimal(n['ecart_charges'])==Decimal(n['ecart_produits'])==0
        assert [r['montant'] for r in n['lignes']]==['1200.10','-200.01','2000.30','-100.02']
        # Export pur d'une variante chiffrée isolée, jamais enregistrée en comptabilité.
        variante=deepcopy(saved)
        variante['contenu']['sources']['n']=[{'compte':'6111','debit':'9999999999999.99','credit':'0'},
            {'compte':'6121','debit':'9999999999999.99','credit':'0'}]
        variante['contenu']['detail_cpc_documentaire']['vue']=calculer(variante)
        x=generer_preparation_xlsx(variante,{'raison_sociale':'Variante fictive de précision'})
        wb=load_workbook(BytesIO(x));cell=wb['Rapprochement CPC N']['B2']
        assert cell.value=='19999999999999.98' and cell.data_type=='s'
        assert wb['Rapprochement CPC N']['D2'].data_type=='s'


def test_703_ancienne_source_absente_nouvelle_version_explicite(application):
    import models
    from services.balance_import_service import lire_preparation,empreinte_preparation
    with closing(client(application)[0]) as api:
        v=creer(api);user=ok(api.get('/api/auth/me'));contenu=deepcopy(v['contenu'])
        contenu['sources']['n']=None
        with Session(application['engine']) as db:
            original=db.get(models.LiasseBalancePreparation,v['id'])
            row=models.LiasseBalancePreparation(societe_id=user['societe_id'],exercice=original.exercice,
                exercice_id=original.exercice_id,version=2,contenu=contenu,
                empreinte_sha256=empreinte_preparation(contenu),created_by=user['id'])
            db.add(row);db.commit();db.refresh(row);ancien=lire_preparation(row)
        assert ok(api.get(url(ancien)))['vue'] is None
        r=ok(api.post(url(ancien),json=body(ancien)),201);n=ok(api.get(url(r)))['vue']['periodes']['n']
        assert not n['disponible'] and n['resultat'] is None and 'absente' in n['motif']
        assert ok(api.get(BASE+f'/{ancien["id"]}'))==ancien
