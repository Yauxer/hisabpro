"""Déclarations B4 : sources certaines, décimales exactes et snapshots isolés."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
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
from test_balance_participations707_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier,creer,url as b4_url,source)
from test_balance_etic_notes693_isole import notes,url as notes_url
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/emetteurs'


def body(v,comparatif=True):
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
        {'code':'B4-N','statut':'documente','justification':'Relevé fictif709 N','lignes':[
            {'compte':'2510','emetteur':'Atlas Industrie fictive','identifiant':'FICTIF-A','valeur_brute':'2500',
             'capital_emetteur':'500000','quote_part':'20','produits_recus':None,'reference_source':'Attestation fictive A'},
            {'compte':'2510','emetteur':'Rif Services fictive','valeur_brute':'1500',
             'capital_emetteur':None,'quote_part':None,'produits_recus':'100','reference_source':'Attestation fictive B'}]},
        {'code':'B4-N1','statut':'documente' if comparatif else 'a_completer','justification':'Relevé fictif709 N-1' if comparatif else '',
         'lignes':[{'compte':'2510','emetteur':'Atlas Industrie fictive','valeur_brute':'3000','capital_emetteur':'500000',
                    'quote_part':'20','produits_recus':'0','reference_source':'Attestation fictive N-1'}] if comparatif else []}]}


@pytest.mark.parametrize('cas',['connus','inconnu','inverse','zero','neant','sansn1','grand','ecart'])
def test_709_oracle_controles_sans_deductions(cas):
    from routers.etats import BalanceEmetteursIn
    from services.balance_emetteurs_service import normaliser,calculer_controles,presentation
    d=source();d['contenu']['sources']['n1']=deepcopy(d['contenu']['sources']['n'])
    q=body({'empreinte_sha256':'a'*64});r=q['tables'][0]['lignes'][0]
    if cas=='inconnu':r['valeur_brute']=None
    elif cas=='inverse':d['contenu']['sources']['n'][0].update(debit='0',credit='20');r['valeur_brute']='-1520'
    elif cas=='zero':r['valeur_brute']='0'
    elif cas=='neant':q['tables'][0].update(statut='neant_declare',lignes=[])
    elif cas=='sansn1':d['contenu']['sources']['n1']=None;q=body({'empreinte_sha256':'a'*64},False)
    elif cas=='grand':r['valeur_brute']='9999999999999.99';q['tables'][0]['lignes'][1]['valeur_brute']='9999999999999.99'
    elif cas=='ecart':r['valeur_brute']='2499.99'
    avant=deepcopy(d);tables=normaliser(d,BalanceEmetteursIn.model_validate(q).tables);c=calculer_controles(d,{'tables':tables})
    assert d==avant and presentation(d)['controle_emetteurs'] is None
    n=c['periodes']['n']['comptes'][0];json.dumps(c,allow_nan=False)
    assert tables[0]['lignes'][0]['capital_emetteur']=='500000.00' if cas!='neant' else not tables[0]['lignes']
    if cas in ('inconnu','neant'):assert n['somme_brute_declaree'] is n['ecart_brut'] is None
    elif cas=='inverse':assert n['somme_brute_declaree']=='-20.00' and n['ecart_brut']=='0.00'
    elif cas=='zero':assert n['somme_brute_declaree']=='1500.00' and n['ecart_brut']=='-2500.00'
    elif cas=='grand':assert n['somme_brute_declaree']=='19999999999999.98'
    elif cas=='ecart':assert n['ecart_brut']=='-0.01'
    else:assert n['somme_brute_declaree']=='4000.00' and n['ecart_brut']=='0.00'
    if cas=='neant':assert c['periodes']['n']['alertes']
    if cas=='sansn1':assert not c['periodes']['n1']['disponible'] and not c['periodes']['n1']['comptes']
    if cas!='neant':assert tables[0]['lignes'][1]['quote_part'] is None and tables[0]['lignes'][0]['produits_recus'] is None


@pytest.mark.parametrize('champ,valeur',[
    ('compte','2411'),('compte','25199'),('compte',''),('emetteur',' '),('reference_source',''),
    ('valeur_brute','NaN'),('valeur_brute','Infinity'),('valeur_brute',True),('valeur_brute','0.001'),('valeur_brute','10000000000000'),
    ('capital_emetteur','-1'),('quote_part','100.000000000001'),('quote_part','0.0000000000001'),('quote_part','NaN'),
    ('produits_recus','Infinity'),('inconnu','refusé')])
def test_709_entrees_invalides_aucune_mutation(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);q['tables'][0]['lignes'][0][champ]=valeur;avant=donnees_metier(application)
        assert api.post(url(v),json=q).status_code==422
        assert donnees_metier(application)==avant


def test_709_snapshot_source_rejeu_controles_et_contradiction(application,monkeypatch):
    from services import balance_emetteurs_service as service
    from routers.etats import BalanceEmetteursIn
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(b4_url(v),json={'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256']}),201)
        n=notes(v);n['lignes'].append({'code':'B4','statut':'non_applicable','justification':'Déclaration fictive à confronter'})
        v=ok(api.post(notes_url(v),json=n),201);q=body(v);avant=donnees_metier(application)
        r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
        assert all(r['contenu'][k]==x for k,x in v['contenu'].items()) and vue['alertes']
        assert vue['controle_emetteurs']['periodes']['n']['comptes'][0]['ecart_brut']=='0.00'
        assert vue['tables'][0]['lignes'][0]['quote_part']=='20' and vue['tables'][0]['lignes'][1]['capital_emetteur'] is None
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        apres=donnees_metier(application);assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')
        def interdit(*a,**kw):raise AssertionError('Recalcul contrôle ancien/rejeu interdit')
        monkeypatch.setattr(service,'calculer_controles',interdit)
        assert service.presentation(r)['controle_emetteurs']==vue['controle_emetteurs']
        with Session(application['engine']) as db:assert service.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceEmetteursIn.model_validate(q))==r
        assert ok(api.get(url(r)))==vue
        assert api.post(url(r),json={**q,'empreinte_parent':r['empreinte_sha256']}).status_code==409


def test_709_n1_absente_neant_source_et_capital_non_infere(application):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif=False);q=body(v,False);r=ok(api.post(url(v),json=q),201);vue=ok(api.get(url(r)))
        assert not vue['sources']['n1']['disponible'] and not vue['controle_emetteurs']['periodes']['n1']['disponible']
        assert api.post(url(v),json=body(v,True)).status_code==422
        q=body(r,False);q['tables'][0].update(statut='neant_declare',lignes=[])
        r2=ok(api.post(url(r),json=q),201);c=ok(api.get(url(r2)))['controle_emetteurs']['periodes']['n']
        assert c['alertes'] and c['comptes'][0]['somme_brute_declaree'] is None


def test_709_exports_unites_signes_logo_et_precision(application):
    with closing(client(application)[0]) as api:
        v=creer(api);q=body(v);row=q['tables'][0]['lignes'][0]
        row.update(emetteur='=1+2\n<Titre fictif & source>',quote_part='66.666666666667',valeur_brute='2499.99',produits_recus='-10.01')
        r=ok(api.post(url(v),json=q),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        avant=donnees_metier(application);x=api.get(BASE+f'/{r["id"]}/xlsx');assert x.status_code==200
        w=load_workbook(BytesIO(x.content));assert w['Émetteurs N']['B2'].data_type=='s'
        assert w['Émetteurs N']['F2'].value=='66.666666666667' and w['Émetteurs N']['F2'].data_type=='s'
        assert w['Émetteurs N']['G2'].value==-10.01 and w['Contrôle émetteurs N']['D2'].value==-0.01
        p=api.get(BASE+f'/{r["id"]}/pdf');assert p.status_code==200
        pdf=PdfReader(BytesIO(p.content));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
        assert '<Titre fictif & source>' in t and '66.666666666667 %' in t and any(p.images for p in pdf.pages)
        z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert json.loads(zip.read('declarations_emetteurs.json'))['controle_emetteurs']==ok(api.get(url(r)))['controle_emetteurs']
            m=json.loads(zip.read('MANIFESTE_SHA256.json'));assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
        assert donnees_metier(application)==avant


def test_709_droits_empreinte_tables_devise_et_concurrence(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);q=body(v)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=q).status_code==404
        assert api.post(url(v),json={**q,'empreinte_parent':'a'*64}).status_code==409
        for bad in [{**q,'controle':{}},{**q,'cle':'non-uuid'},{**q,'tables':q['tables'][:1]}]:assert api.post(url(v),json=bad).status_code==422
        bad=body(v);bad['tables'][1]['code']='B4-N';assert api.post(url(v),json=bad).status_code==422
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=q).status_code==403
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=q),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=body(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200
