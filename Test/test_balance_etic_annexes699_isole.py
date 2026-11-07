"""Annexes699 : données documentaires strictes sur PostgreSQL natif jetable."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from decimal import Decimal
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from test_balance_etic_tables697_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier,joindre,path,
    notes,notes_url,flux,financement_url,tables,url as tables_url)
from test_balance_dossier689_isole import verifier_bundle
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/annexes-etic'


def annexes(v):
    def table(code,ligne=None):
        return {'code':code,'statut':'documente' if ligne else 'neant_declare',
                'justification':'Revue fictive699 '+code,'lignes':[] if ligne is None else [{**ligne,'reference_source':'Source fictive699 '+code}]}
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
        table('A2',{'indication':'Dérogation fictive699','justification':'Motif documentaire fictif','influence':'À évaluer, aucune estimation présumée'}),
        table('A3'),
        table('B10',{'bien':'Machine en crédit-bail fictif699','date_contrat':'2025-12-15','duree':'48 mois',
                      'valeur_estimee':'10000','redevances_exercice':'1200','redevances_restantes':'6400'}),
        table('C1',{'associe':'Associé fictif699','identifiant':'Identité de recette uniquement','titres':'100',
                     'nominal':'100','capital':'10000','pourcentage':'66.666666666667'}),
        table('C2',{'sens':'Affectation','nature':'Report à nouveau fictif','montant':'0','observation':'Sans décision réelle présumée'}),
        table('C4',{'devise':'EUR','achats':'2000','ventes':'0','creances':None,'dettes':None,
                     'observation':'Contre-valeurs MAD justifiées, aucun cours de conversion présumé'})]}


def test_699_initial_sources_exactes_versions_rejeu_et_catalogue(application):
    from services.etic_service import CATALOGUE_ETIC
    from services.balance_etic_annexes_service import presentation
    with closing(client(application)[0]) as api:
        v=creer(api);before=donnees_metier(application);vue=ok(api.get(url(v)))
        assert [t['code'] for t in vue['tables']]==['A2','A3','B10','C1','C2','C4']
        assert not vue['pret_a_deposer'] and all(not t['lignes'] and t['statut']=='a_completer' for t in vue['tables'])
        body=annexes(v);r=ok(api.post(url(v),json=body),201);assert r['version']==2
        assert ok(api.get(BASE+f'/{v["id"]}'))==v and ok(api.post(url(v),json=body),201)==r
        vue=ok(api.get(url(r)));assert vue['tables'][3]['lignes'][0]['titres']=='100'
        assert vue['tables'][3]['lignes'][0]['pourcentage']=='66.666666666667'
        assert vue['tables'][5]['lignes'][0]['creances'] is None
        assert vue['tables'][5]['lignes'][0]['ventes']=='0.00'
        assert vue['tables'][2]['lignes'][0]['date_contrat']=='2025-12-15'
        assert vue['parent']['empreinte_sha256']==v['empreinte_sha256'] and vue['auteur']['nom']
        body['tables'][2]['lignes'][0]['bien']='Autre';assert api.post(url(v),json=body).status_code==409
        after=donnees_metier(application);assert all(after[k]==value for k,value in before.items() if k!='liasse_balances_preparation')
        cat=next(r for r in CATALOGUE_ETIC if r['code']=='B10');ancien=deepcopy(cat)
        try:
            cat['titre']='Futur titre non conservé';cat['colonnes_saisie'][0]['label']='Futur champ'
            assert presentation(r)['tables'][2]['titre']==ancien['titre']
            assert presentation(r)['tables'][2]['colonnes_saisie'][0]['label']==ancien['colonnes_saisie'][0]['label']
        finally:cat.clear();cat.update(ancien)


@pytest.mark.parametrize('code,champ,valeur',[
    ('B10','date_contrat','2026-02-30'),('B10','date_contrat','20260101'),('B10','date_contrat',True),
    ('B10','valeur_estimee','NaN'),('B10','redevances_exercice','Infinity'),('B10','redevances_restantes','-1'),
    ('B10','redevances_exercice','1.001'),('B10','valeur_estimee','10000000000000'),
    ('C1','titres','1.5'),('C1','titres',True),('C1','titres','1000000000000000000'),
    ('C1','pourcentage','NaN'),('C1','pourcentage','100.000000000001'),('C1','pourcentage','-0.01'),
    ('C1','pourcentage','0.0000000000001'),('C1','pourcentage',{}),
    ('A2','indication',' '),('A2','influence',False),('C4','devise',' '),('C4','ventes','NaN'),
    ('C2','montant',[]),('B10','reference_source',' '),('C1','inconnue','refusée')],
    ids=['date_impossible','date_format','date_bool','montant_nan','montant_inf','montant_negatif','sous_centime','borne_mad',
         'titres_fraction','titres_bool','titres_borne','pct_nan','pct_sup100','pct_negatif','pct_precision','pct_objet',
         'identification_vide','texte_bool','devise_vide','devises_nan','montant_liste','source_vide','colonne_inconnue'])
def test_699_entrees_invalides_aucune_version(application,code,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);body=annexes(v);t=next(t for t in body['tables'] if t['code']==code)
        t['lignes'][0][champ]=valeur;before=donnees_metier(application)
        assert api.post(url(v),json=body).status_code==422
        assert donnees_metier(application)==before


def test_699_complements_inconnus_neant_et_alertes_preserves(application):
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(chemin(v),json=demande(v)),201)
        n=notes(v);n['lignes'].append({'code':'B10','statut':'non_applicable','justification':'Revue fictive antérieure à confronter'})
        v=ok(api.post(notes_url(v),json=n),201);v=ok(api.post(financement_url(v),json=flux(v)),201)
        v=ok(api.post(tables_url(v),json=tables(v)),201);piece=ok(joindre(api,v),201)
        r=ok(api.post(url(v),json=annexes(v)),201)
        assert all(r['contenu'][k]==value for k,value in v['contenu'].items())
        assert ok(api.get(path(r)))['documents']==[] and ok(api.get(path(v)))['documents'][0]['id']==piece['id']
        assert len(ok(api.get(url(r)))['alertes'])==1 and 'B10' in ok(api.get(url(r)))['alertes'][0]
        assert len(ok(api.get(tables_url(r)))['alertes'])==1
        body=annexes(r);body['tables'][2].update(statut='neant_declare',lignes=[])
        body['tables'][3].update(statut='a_completer',justification='',lignes=[{'capital':'0'}])
        r2=ok(api.post(url(r),json=body),201)
        row=ok(api.get(url(r2)))['tables'][3]['lignes'][0]
        assert row['capital']=='0.00' and row['titres'] is None and row['pourcentage'] is None
        assert ok(api.get(url(r)))['tables'][2]['lignes']
        r3=ok(api.post(tables_url(r2),json=tables(r2)),201)
        assert r3['contenu']['annexes_etic_documentaires']==r2['contenu']['annexes_etic_documentaires']


def test_699_permissions_societe_concurrence_doublons_et_hash(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=annexes(v)).status_code==404
        body=annexes(v);body['empreinte_parent']='0'*64;assert api.post(url(v),json=body).status_code==409
        body=annexes(v);body['tables'][1]['code']='A2';assert api.post(url(v),json=body).status_code==422
        body=annexes(v);body['tables'].pop();assert api.post(url(v),json=body).status_code==422
        body=annexes(v);body['tables'][2]['lignes']*=101;assert api.post(url(v),json=body).status_code==422
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        autre.headers['Authorization']='Bearer '+ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=annexes(v)).status_code==403
        body=annexes(v)
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=body),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}));assert api.post(url(v),json=annexes(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200


def test_699_exports_sources_unites_dates_et_precision_sans_formule(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=annexes(v);body['tables'][3]['lignes'][0]['titres']='999999999999999999'
        body['tables'][2]['lignes'][0]['bien']='=1+2\n<Machine fictive699 & source>'
        r=ok(api.post(url(v),json=body),201);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        before=donnees_metier(application);x=api.get(BASE+f'/{r["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));ws=wb['ETIC documentaire C1']
        assert ws['C2'].value=='999999999999999999' and ws['C2'].data_type=='s'
        assert ws['F2'].value=='66.666666666667' and ws['F2'].data_type=='s'
        assert wb['ETIC documentaire B10']['B2'].value=='2025-12-15'
        assert wb['ETIC documentaire B10']['A2'].data_type=='s'
        assert wb['ETIC documentaire C4']['D2'].value=='Indisponible'
        pdf=api.get(BASE+f'/{r["id"]}/pdf');assert pdf.status_code==200
        reader=PdfReader(BytesIO(pdf.content));t='\n'.join(p.extract_text() or '' for p in reader.pages)
        assert '66.666666666667 %' in t and '999999999999999999 titres' in t
        assert '<Machine fictive699 & source>' in t and '2025-12-15' in t and any(p.images for p in reader.pages)
        z=api.get(BASE+f'/{r["id"]}/zip');assert z.status_code==200;verifier_bundle(z.content,r)
        with ZipFile(BytesIO(z.content)) as zip:
            vue=json.loads(zip.read('annexes_etic_documentaires.json'))
            assert vue=={k:val for k,val in ok(api.get(url(r))).items() if k not in ('id','version','empreinte_sha256')}
        assert donnees_metier(application)==before
