"""C3 indépendant : oracles exacts, anciennes balances119 et versions isolées."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_etic_notes693_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier)
from test_balance_cpc703_isole import body
from test_logo_societe import image_data


def test_723_legacy119_b11_ne_fabrique_pas_un_resultat_nul():
    from services.balance_cpc_detail_service import calculer
    d={'contenu':{'sources':{'n':[{'compte':'1191','debit':'0','credit':'6400'}],'n1':None},
       'preparation':{'etats':{'cpc':{'I':0,'II':0,'IV':0,'V':0,'VIII':0,'IX':0,'XII':0,'resultat_net':0}}}}}
    avant=deepcopy(d);v=calculer(d)['periodes']['n']
    assert d==avant and not v['disponible'] and v['resultat'] is None and '119' in v['motif']


def url(v):return BASE+f'/{v["id"]}/indicateurs-c3'


def creer(api,comparatif=True,technique=False):
    n=[{'compte':'1111','credit':'10000'},{'compte':'2111','debit':'2000'},
       {'compte':'28111','credit':'500'},{'compte':'5141','debit':'14500'}]
    n+=([{'compte':'1191','credit':'6000'}] if technique else [
        {'compte':'7111','credit':'10000'},{'compte':'6132','debit':'3000'},
        {'compte':'7581','credit':'1000'},{'compte':'6701','debit':'1600'},{'compte':'6171','debit':'400'}])
    n1=[{'compte':'1111','credit':'10000'},{'compte':'2111','debit':'1000'},
        {'compte':'28111','credit':'200'},{'compte':'5141','debit':'12200'},
        {'compte':'7111','credit':'5000'},{'compte':'6132','debit':'2000'}]
    return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n,'lignes_n1':n1 if comparatif else None,
        'fichier_n':'Fictif723_N.csv','fichier_n1':'Fictif723_N1.csv' if comparatif else None}),201)


def source():
    rows=[{'compte':c,'debit':d,'credit':cr} for c,d,cr in [('1111','0','10000'),('2111','2000','0'),
        ('28111','0','500'),('5141','14500','0'),('7111','0','10000'),('6132','3000','0'),
        ('7581','0','1000'),('6701','1600','0'),('6171','400','0')]]
    return {'contenu':{'sources':{'n':rows,'n1':None},'preparation':{'etats':{
        'cpc':{'XI':7600,'XII':1600,'resultat_net':6000},'bilan':{
            'actif':{'immobilise':[{'code':'21','net':1500}]},'passif':{
                'capitaux_propres':[{'montant':10000},{'montant':6000}],
                'financement_permanent':[{'code':'131/135','montant':0}]}}},'etats_n1':None}}}


@pytest.mark.parametrize('cas',['normal','n1','n2_ignore','absent','incomplet','technique','legacy119',
    'cpc_absent','bilan_absent','ecart','inverses','grand','zero'])
def test_723_oracle_exact_situation_activite_inconnus_et_references(cas):
    from services.balance_indicateurs_service import calculer,presentation
    d=source();c=d['contenu']
    if cas=='n1':c['sources']['n1']=deepcopy(c['sources']['n']);c['preparation']['etats_n1']=deepcopy(c['preparation']['etats'])
    elif cas=='n2_ignore':c['sources']['n2']=deepcopy(c['sources']['n'])
    elif cas=='absent':c['sources']['n']=None
    elif cas=='incomplet':c['sources']['n'][0].pop('credit')
    elif cas in ('technique','legacy119'):
        c['sources']['n']=[r for r in c['sources']['n'] if not r['compte'].startswith(('6','7'))]+[{'compte':'1191','debit':'0','credit':'6000'}]
        c['preparation']['etats']['cpc']={'disponible':False,'motif':'119 soldé'} if cas=='technique' else {'XI':0,'XII':0,'resultat_net':0}
    elif cas=='cpc_absent':c['preparation']['etats'].pop('cpc')
    elif cas=='bilan_absent':c['preparation']['etats'].pop('bilan')
    elif cas=='ecart':c['preparation']['etats']['cpc']['resultat_net']=5999.99
    elif cas=='inverses':c['sources']['n']=[{'compte':'7111','debit':'20.01','credit':'0'},{'compte':'6132','debit':'0','credit':'5.02'}]
    elif cas=='grand':c['sources']['n']=[{'compte':n,'debit':'0','credit':'9999999999999.99'} for n in ('7111','7121')]
    elif cas=='zero':c['sources']['n']=[]
    avant=deepcopy(d);v=calculer(d);assert d==avant and not v['pret_a_deposer']
    assert presentation(d)['vue'] is None;json.dumps(v,allow_nan=False)
    n=v['periodes']['n'];n1=v['periodes']['n1'];n2=v['periodes']['n2']
    assert not n2['disponible'] and all(n2[k] is None for k in ('situation_nette','resultat_net','effectif_moyen'))
    assert n1['disponible']==(cas=='n1')
    if cas in ('absent','incomplet'):assert not n['disponible'] and n['situation_nette'] is None
    elif cas in ('technique','legacy119'):
        assert n['situation_nette']=='14500.00' and n['resultat_net'] is n['chiffre_affaires_ht'] is n['salaires_bruts'] is None
        assert n['avertissements'] and Decimal(n['ecart_situation_nette'])==0
    elif cas=='cpc_absent':assert n['disponible'] and n['situation_nette'] is n['resultat_net'] is None
    elif cas=='inverses':assert n['resultat_net']=='-14.99' and n['chiffre_affaires_ht']=='-20.01'
    elif cas=='grand':assert n['resultat_net']==n['situation_nette']=='19999999999999.98'
    elif cas=='zero':assert n['situation_nette']==n['resultat_net']==n['salaires_bruts']=='0.00'
    else:
        assert n['situation_nette']=='14500.00' and n['chiffre_affaires_ht']=='10000.00'
        assert n['resultat_avant_impots']=='7600.00' and n['impots_resultats']=='1600.00'
        assert n['resultat_net']=='6000.00' and n['salaires_bruts']=='400.00'
        assert Decimal(n['ecart_resultat_net'])==(Decimal('.01') if cas=='ecart' else 0)
        if cas=='bilan_absent':assert n['reference_situation_nette'] is n['ecart_situation_nette'] is None
        else:assert Decimal(n['ecart_situation_nette'])==0
    assert all(n[k] is None for k in ('effectif_moyen','benefices_distribues','resultat_par_titre','distribution_par_titre'))


@pytest.mark.parametrize('valeur',['NaN','Infinity',True,'-1','0.001'])
def test_723_source_invalide_sans_montant_fabrique(valeur):
    from services.balance_indicateurs_service import calculer
    d=source();d['contenu']['sources']['n'][0]['credit']=valeur
    with pytest.raises(ValueError):calculer(d)


def test_723_moteur_partage_exact_optionnel_sans_modifier_contrat_historique():
    from services.etic_service import _calcul_c3_depuis_soldes
    s={'7111':{'debit':'0','credit':'9999999999999.99'},'7121':{'debit':'0','credit':'9999999999999.99'}}
    v=_calcul_c3_depuis_soldes(s,decimal_exact=True)
    assert v['resultat_net']=='19999999999999.98' and all(isinstance(x,str) for x in v.values())
    assert all(isinstance(x,float) for x in _calcul_c3_depuis_soldes(s).values())


def test_723_snapshot_rejeu_exports_figes_et_temoins(application,monkeypatch):
    from services import balance_indicateurs_service as s
    from routers.etats import BalanceIndicateursIn
    with closing(client(application)[0]) as api:
        v=creer(api);avant=donnees_metier(application);b=body(v)
        assert not ok(api.get(url(v)))['conserve'];r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
        assert vue['vue']['periodes']['n']['situation_nette']=='14500.00'
        assert vue['vue']['periodes']['n1']['situation_nette']=='12200.00'
        assert all(r['contenu'][k]==x for k,x in v['contenu'].items()) and ok(api.get(BASE+f'/{v["id"]}'))==v
        def interdit(*a,**kw):raise AssertionError('Aucun calcul des anciennes versions, aucun Journal/RH')
        monkeypatch.setattr(s,'calculer',interdit);monkeypatch.setattr(s,'_calcul_c3_depuis_soldes',interdit)
        with Session(application['engine']) as db:assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceIndicateursIn.model_validate(b))==r
        assert ok(api.get(url(r)))==vue and api.get(BASE+f'/{r["id"]}/zip').status_code==200
        apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('comparatif,technique',[(False,False),(True,True)])
def test_723_sources_absentes_et_cloture_technique(application,comparatif,technique):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif,technique);r=ok(api.post(url(v),json=body(v)),201)
        n=ok(api.get(url(r)))['vue']['periodes']
        assert n['n']['situation_nette']=='14500.00'
        assert n['n']['resultat_net'] is None if technique else n['n']['resultat_net']=='6000.00'
        if not comparatif:assert not n['n1']['disponible'] and n['n1']['resultat_net'] is None


def test_723_exports_exactitude_logo_et_manifestes(application):
    from services.balance_indicateurs_service import calculer
    from services.balance_preparation_export_service import generer_preparation_xlsx
    with closing(client(application)[0]) as api:
        v=creer(api);r=ok(api.post(url(v),json=body(v)),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        rep=api.get(BASE+f'/{r["id"]}/zip');assert rep.status_code==200
        with ZipFile(BytesIO(rep.content)) as z:
            assert z.testzip() is None
            assert json.loads(z.read('indicateurs_comptables_documentaires.json'))['vue']==r['contenu']['indicateurs_comptables_documentaires']['vue']
            m=json.loads(z.read('MANIFESTE_SHA256.json'))
            for n,h in m['fichiers'].items():assert len(z.read(n))==h['taille'] and hashlib.sha256(z.read(n)).hexdigest()==h['sha256']
            w=load_workbook(BytesIO(z.read('preparation.xlsx')))
            assert w['Indicateurs C3 N']['B2'].value==14500 and w['Indicateurs C3 N']['B6'].value==6000
            assert w['Indicateurs C3 N-2']['B2'].value=='Indisponible'
            with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:assert any(n.startswith('xl/media/') for n in x.namelist())
            pdf=PdfReader(BytesIO(z.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert 'C3' in t and '14 500,00' in t and 'N-2 non fournie' in t and any(p.images for p in pdf.pages)
        assert donnees_metier(application)==avant
        variant=deepcopy(r);variant['contenu']['sources']['n']=[{'compte':c,'debit':'0','credit':'9999999999999.99'} for c in ('7111','7121')]
        variant['contenu']['indicateurs_comptables_documentaires']['vue']=calculer(variant)
        w=load_workbook(BytesIO(generer_preparation_xlsx(variant,{'raison_sociale':'Fictif723'})))
        assert w['Indicateurs C3 N']['B2'].value=='19999999999999.98' and w['Indicateurs C3 N']['B2'].data_type=='s'


def test_723_societes_droits_hash_strict_devise_et_concurrence(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);b=body(v)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=b).status_code==404
        assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
        for data in ({**b,'vue':{}},{**b,'cle':'invalide'},{'cle':str(uuid4())}):assert api.post(url(v),json=data).status_code==422
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        assert api.post(url(rs[0].json()),json={**b,'empreinte_parent':rs[0].json()['empreinte_sha256']}).status_code==409
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}))
        assert api.post(url(v),json=body(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200
