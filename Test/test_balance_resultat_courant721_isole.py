"""B13 autonome : oracles indépendants, sources figées, PostgreSQL nonce."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from datetime import date
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib, json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_etic_notes693_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,BASE,donnees_metier,notes,url as notes_url)
from test_logo_societe import image_data


def url(v): return BASE + f'/{v["id"]}/resultat-courant'


def creer(api, comparatif=True, technique=False):
    # Courant 10000 - 3000 =7000 ; non courant 1000 ; impôt comptabilisé1600.
    # Net6400 ; banque16400 et capital10000. Aucun taux fiscal implicite.
    n = [{'compte':'1111','credit':'10000'}, {'compte':'5141','debit':'16400'}]
    n += ([{'compte':'1191','credit':'6400'}] if technique else [
        {'compte':'7111','credit':'10000'}, {'compte':'6132','debit':'3000'},
        {'compte':'7581','credit':'1000'}, {'compte':'6701','debit':'1600'}])
    n1 = [{'compte':'1111','credit':'10000'}, {'compte':'5141','debit':'13000'},
          {'compte':'7111','credit':'5000'}, {'compte':'6132','debit':'2000'}]
    return ok(api.post(BASE,json={'exercice':date.today().year,'lignes_n':n,
        'lignes_n1': n1 if comparatif else None, 'fichier_n':'Fictif721_N.csv',
        'fichier_n1': 'Fictif721_N1.csv' if comparatif else None}),201)


def body(v, n1=True, partiel=False):
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
        {'code':'B13-N','statut':'documente','justification':'Synthèse fictive721, sans taux fiscal calculé',
         'lignes':[{'nature':'Synthèse courante fictive N','reintegrations':'500',
                    'deductions':None if partiel else '200','impot_theorique':None if partiel else '1200',
                    'regime_avantages':'À vérifier sur justificatifs, aucun avantage déduit',
                    'reference_source':'NOTE FICTIVE721 N, postes courants seulement'}]},
        {'code':'B13-N1','statut':'documente' if n1 else 'a_completer',
         'justification':'Synthèse fictive N-1' if n1 else '',
         'lignes':[{'nature':'Synthèse courante N-1','reintegrations':'0','deductions':'0',
                    'impot_theorique':'0','reference_source':'NOTE FICTIVE721 N-1, zéros déclarés'}] if n1 else []}]}


def source():
    return {'contenu':{'sources':{'n':[
        {'compte':'7111','debit':'0','credit':'10000'}, {'compte':'6132','debit':'3000','credit':'0'},
        {'compte':'6701','debit':'1600','credit':'0'}, {'compte':'7581','debit':'0','credit':'1000'}],
        'n1':None},'preparation':{'etats':{'cpc':{'VII':7000,'I':10000,'II':3000,
            'IV':0,'V':0,'VIII':1000,'IX':0,'XII':1600,'resultat_net':6400}},'etats_n1':None}}}


@pytest.mark.parametrize('cas',['normal','partiel','zero','vide','n1','absent','incomplet','technique','technique_legacy',
    'cpc_absent','ref_absente','ecart','inverses','grand','sans_ligne','neant'])
def test_721_oracle_exact_courant_hypotheses_inconnues_et_67_distinct(cas):
    from services.balance_resultat_courant_service import calculer_controles,presentation
    d=source();q=body({'empreinte_sha256':'a'*64},n1=False)
    if cas=='partiel': q['tables'][0]['lignes'][0].update(deductions=None,impot_theorique=None)
    elif cas=='zero': q['tables'][0]['lignes'][0].update(reintegrations='0',deductions='0',impot_theorique='0')
    elif cas=='vide': d['contenu']['sources']['n']=[]
    elif cas=='n1':
        d['contenu']['sources']['n1']=deepcopy(d['contenu']['sources']['n'])
        d['contenu']['preparation']['etats_n1']=deepcopy(d['contenu']['preparation']['etats'])
    elif cas=='absent': d['contenu']['sources']['n']=None
    elif cas=='incomplet': d['contenu']['sources']['n'][0].pop('debit')
    elif cas=='technique': d['contenu']['preparation']['etats']['cpc']={'disponible':False,'motif':'119 soldé'}
    elif cas=='technique_legacy': d['contenu']['sources']['n']=[{'compte':'1191','debit':'0','credit':'6400'}]
    elif cas=='cpc_absent': d['contenu']['preparation']['etats']={}
    elif cas=='ref_absente': d['contenu']['preparation']['etats']['cpc'].pop('VII')
    elif cas=='ecart': d['contenu']['preparation']['etats']['cpc']['VII']=6999.99
    elif cas=='inverses': d['contenu']['sources']['n']=[{'compte':'7111','debit':'20.01','credit':'0'},
        {'compte':'6132','debit':'0','credit':'5.02'},{'compte':'6701','debit':'0','credit':'2.03'}]
    elif cas=='grand': d['contenu']['sources']['n']=[{'compte':c,'debit':'0','credit':'9999999999999.99'} for c in ('7111','7121')]
    elif cas in ('sans_ligne','neant'):
        q['tables'][0].update(lignes=[],statut='neant_declare' if cas=='neant' else 'a_completer')
    avant=deepcopy(d);v=calculer_controles(d,q);assert d==avant and not v['pret_a_deposer']
    assert presentation(d)['controle_resultat_courant'] is None
    json.dumps(v,allow_nan=False);n=v['periodes']['n'];n1=v['periodes']['n1']
    if cas in ('absent','incomplet','technique','technique_legacy','cpc_absent'):
        assert not n['disponible'] and n['resultat_courant'] is n['base_courante_documentaire'] is None
    else:
        assert n['disponible']
        if cas=='inverses': assert n['resultat_courant']=='-14.99' and n['impots_comptabilises_67']=='-2.03'
        elif cas=='grand': assert n['resultat_courant']=='19999999999999.98'
        elif cas=='vide': assert n['resultat_courant']=='0.00'
        else:
            assert n['resultat_courant']=='7000.00' and n['impots_comptabilises_67']=='1600.00'
            if cas=='partiel': assert n['base_courante_documentaire'] is n['courant_apres_impot_declare'] is None
            elif cas in ('sans_ligne','neant'): assert n['reintegrations'] is n['impot_theorique_declare'] is None
            elif cas=='zero': assert n['base_courante_documentaire']==n['courant_apres_impot_declare']=='7000.00'
            else: assert n['base_courante_documentaire']=='7300.00' and n['courant_apres_impot_declare']=='5800.00'
            if cas=='ref_absente': assert n['ecart_courant'] is None
            else: assert Decimal(n['ecart_courant'])==(Decimal('.01') if cas=='ecart' else 0)
        if cas=='neant': assert n['alertes']
    assert n1['disponible'] == (cas=='n1')
    assert n1['impot_theorique_declare'] is None


@pytest.mark.parametrize('valeur',['NaN','Infinity',True,'-1','0.001'])
def test_721_source_invalide(valeur):
    from services.balance_resultat_courant_service import calculer_controles
    d=source();d['contenu']['sources']['n'][0]['credit']=valeur
    with pytest.raises(ValueError): calculer_controles(d,body({'empreinte_sha256':'a'*64},False))


def test_721_note_contradictoire_visible_sans_corriger_la_source():
    from services.balance_resultat_courant_service import presentation,catalogue
    d=source();c=d['contenu'];c['notes_etic_documentaires']={'lignes':[{'code':'B13','statut':'non_applicable'}]}
    c['resultat_courant_documentaire']={'catalogue':catalogue(d),'tables':body({'empreinte_sha256':'a'*64},False)['tables']}
    avant=deepcopy(d);v=presentation(d)
    assert d==avant and any('note B13' in a for a in v['alertes']) and not v['pret_a_deposer']


def test_721_version_rejeu_sans_recalcul_et_metier_preserve(application,monkeypatch):
    from services import balance_resultat_courant_service as s
    from routers.etats import BalanceResultatCourantIn
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(notes_url(v),json=notes(v)),201)
        avant=donnees_metier(application);assert ok(api.get(url(v)))['controle_resultat_courant'] is None
        b=body(v);r=ok(api.post(url(v),json=b),201);vue=ok(api.get(url(r)))
        n=vue['controle_resultat_courant']['periodes']['n'];n1=vue['controle_resultat_courant']['periodes']['n1']
        assert n['resultat_courant']=='7000.00' and n['base_courante_documentaire']=='7300.00'
        assert n['impots_comptabilises_67']=='1600.00' and n['courant_apres_impot_declare']=='5800.00'
        assert n1['resultat_courant']==n1['courant_apres_impot_declare']=='3000.00'
        assert all(r['contenu'][k]==x for k,x in v['contenu'].items()) and ok(api.get(BASE+f'/{v["id"]}'))==v
        def interdit(*a,**kw): raise AssertionError('Lecture/rejeu/export sans calcul')
        monkeypatch.setattr(s,'calculer_controles',interdit);monkeypatch.setattr(s,'detail_cpc',interdit)
        with Session(application['engine']) as db:
            assert s.conserver(db,ok(api.get('/api/auth/me')),v['id'],BalanceResultatCourantIn.model_validate(b))==r
        assert ok(api.get(url(r)))==vue
        assert api.get(BASE+f'/{r["id"]}/zip').status_code==200
        apres=donnees_metier(application)
        assert all(apres[k]==x for k,x in avant.items() if k!='liasse_balances_preparation')


@pytest.mark.parametrize('cas',['nombre_nan','nombre_inf','negatif','precision','bool','ref','nature',
    'deux_lignes','doublon','omission','colonne','champ','n1_absent','technique'])
def test_721_rejets_sans_version_ni_mutation(application,cas):
    with closing(client(application)[0]) as api:
        v=creer(api,comparatif=cas!='n1_absent',technique=cas=='technique');b=body(v)
        row=b['tables'][0]['lignes'][0]
        if cas in ('nombre_nan','nombre_inf','negatif','precision','bool'):
            row['impot_theorique']={'nombre_nan':'NaN','nombre_inf':'Infinity','negatif':'-1','precision':'0.001','bool':True}[cas]
        elif cas=='ref':row['reference_source']=''
        elif cas=='nature':row['nature']=''
        elif cas=='deux_lignes':b['tables'][0]['lignes'].append(deepcopy(row))
        elif cas=='doublon':b['tables'][1]['code']='B13-N'
        elif cas=='omission':b['tables'].pop()
        elif cas=='colonne':row['taux_auto']='20'
        elif cas=='champ':b['controle_resultat_courant']={}
        avant=donnees_metier(application)
        assert api.post(url(v),json=b).status_code==422
        assert donnees_metier(application)==avant


def test_721_periode_absente_technique_et_partiel(application):
    with closing(client(application)[0]) as api:
        v=creer(api,False);r=ok(api.post(url(v),json=body(v,False,True)),201)
        n=ok(api.get(url(r)))['controle_resultat_courant']['periodes']
        assert n['n']['reintegrations']=='500.00' and n['n']['impot_theorique_declare'] is None
        assert n['n']['courant_apres_impot_declare'] is None and not n['n1']['disponible']
        v=creer(api,False,True);b=body(v,False);b['tables'][0].update(statut='a_completer',justification='',lignes=[])
        r=ok(api.post(url(v),json=b),201);n=ok(api.get(url(r)))['controle_resultat_courant']['periodes']['n']
        assert not n['disponible'] and n['resultat_courant'] is None


def test_721_exports_logo_inconnus_manifestes_precision_et_formules(application):
    from services.balance_resultat_courant_service import calculer_controles
    from services.balance_preparation_export_service import generer_preparation_xlsx
    with closing(client(application)[0]) as api:
        v=creer(api,False);b=body(v,False,True);b['tables'][0]['lignes'][0]['reference_source']='=SOURCE_FICTIVE721'
        r=ok(api.post(url(v),json=b),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));avant=donnees_metier(application)
        z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200
        with ZipFile(BytesIO(z.content)) as zip:
            assert zip.testzip() is None
            vue=json.loads(zip.read('resultat_courant_documentaire.json'))
            assert vue['controle_resultat_courant']==r['contenu']['resultat_courant_documentaire']['controle_resultat_courant']
            m=json.loads(zip.read('MANIFESTE_SHA256.json'))
            assert set(zip.namelist())==set(m['fichiers'])|{'MANIFESTE_SHA256.json'}
            for n,h in m['fichiers'].items():assert len(zip.read(n))==h['taille'] and hashlib.sha256(zip.read(n)).hexdigest()==h['sha256']
            wb=load_workbook(BytesIO(zip.read('preparation.xlsx')))
            assert wb['Contrôle B13 N']['B4'].value=='7000.00'
            assert wb['Contrôle B13 N']['B12'].value=='Indisponible'
            assert wb['Déclaration B13 N']['H2'].value=='=SOURCE_FICTIVE721' and wb['Déclaration B13 N']['H2'].data_type=='s'
            with ZipFile(BytesIO(zip.read('preparation.xlsx'))) as x:assert any(p.startswith('xl/media/') for p in x.namelist())
            pdf=PdfReader(BytesIO(zip.read('preparation.pdf')));t='\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert 'B13' in t and 'Impôts comptabilisés67 pour mémoire' in t and '=SOURCE_FICTIVE721' in t
            assert any(p.images for p in pdf.pages)
        assert donnees_metier(application)==avant
        variant=deepcopy(r);variant['contenu']['sources']['n']=[{'compte':c,'debit':'0','credit':'9999999999999.99'} for c in ('7111','7121')]
        variant['contenu']['resultat_courant_documentaire']['controle_resultat_courant']=calculer_controles(variant,b)
        w=load_workbook(BytesIO(generer_preparation_xlsx(variant,{'raison_sociale':'Fictif721'})))
        assert w['Contrôle B13 N']['B4'].value=='19999999999999.98' and w['Contrôle B13 N']['B4'].data_type=='s'


def test_721_droits_societes_hash_devise_concurrence(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);b=body(v)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=b).status_code==404
        assert api.post(url(v),json={**b,'empreinte_parent':'a'*64}).status_code==409
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=b).status_code==403
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=b),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        b['tables'][0]['lignes'][0]['impot_theorique']='1199.99'
        assert api.post(url(v),json=b).status_code==409
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}))
        assert api.post(url(v),json=body(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200
