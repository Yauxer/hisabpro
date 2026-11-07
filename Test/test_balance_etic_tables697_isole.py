"""B8/B9 documentaires697 : PostgreSQL natif nonce, aucune donnée réelle."""
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
from test_balance_etic_notes693_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier,joindre,path,
    notes,url as notes_url)
from test_balance_financement695_isole import creer,flux,url as financement_url
from test_balance_dossier689_isole import verifier_bundle
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/tables-etic'


def tables(v):
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
        {'code':'B8','statut':'documente','justification':'Contrat fictif697 — sûreté déclarée, sans qualification officielle',
         'lignes':[{'nature':'Hypothèque fictive697','objet':'Immeuble fictif — hors bilan importé',
                    'tiers':'Banque fictive697','montant_couvert':'12345.67','valeur_nette':None,
                    'inscription':'Lieu et date à confirmer','reference_source':'Annexe fictive697 A'}]},
        {'code':'B9','statut':'documente','justification':'Relevé fictif697 des engagements',
         'lignes':[{'sens':'Donné','nature':'Caution fictive697','montant':'2000.00','montant_n1':'0',
                    'observation':'=HYPERLINK("https://example.invalid")','reference_source':'Annexe fictive697 B'}]}]}


def test_697_initial_inconnu_conservation_rejeu_sources_et_catalogue_figes(application):
    from services.etic_service import CATALOGUE_ETIC
    from services.balance_etic_tables_service import presentation
    with closing(client(application)[0]) as api:
        v=creer(api);before=donnees_metier(application);vue=ok(api.get(url(v)))
        assert not vue['pret_a_deposer'] and vue['auteur'] is None
        assert [r['code'] for r in vue['tables']]==['B8','B9']
        assert all(r['statut']=='a_completer' and not r['lignes'] for r in vue['tables'])
        body=tables(v);r=ok(api.post(url(v),json=body),201);assert r['version']==2 and r['id']!=v['id']
        assert ok(api.get(BASE+f'/{v["id"]}'))==v
        assert all(r['contenu'][k]==value for k,value in v['contenu'].items())
        assert ok(api.post(url(v),json=body),201)==r
        vue=ok(api.get(url(r)));assert vue['tables'][0]['lignes'][0]['valeur_nette'] is None
        assert vue['tables'][1]['lignes'][0]['montant_n1']=='0.00'
        assert vue['parent']['empreinte_sha256']==v['empreinte_sha256'] and vue['auteur']['nom']
        body['tables'][0]['lignes'][0]['nature']='Autre';assert api.post(url(v),json=body).status_code==409
        after=donnees_metier(application)
        assert all(after[k]==value for k,value in before.items() if k!='liasse_balances_preparation')
        cat=next(r for r in CATALOGUE_ETIC if r['code']=='B8');ancien=deepcopy(cat)
        try:
            cat['titre']='Titre futur';cat['colonnes_saisie'][0]['label']='Colonne future'
            assert presentation(r)['tables'][0]['titre']==ancien['titre']
            assert presentation(r)['tables'][0]['colonnes_saisie']==ancien['colonnes_saisie']
        finally:cat.clear();cat.update(ancien)


@pytest.mark.parametrize('champ,valeur',[
    ('montant_couvert','NaN'),('montant_couvert','Infinity'),('montant_couvert','-1'),
    ('montant_couvert',True),('montant_couvert',{}),('montant_couvert','1.001'),
    ('montant_couvert','10000000000000'),('nature',True),('nature','a'*2001),
    ('reference_source',' '),('nature',' '),('inconnue','refusée')],
    ids=['nan','infini','negatif','booleen','objet','sous_centime','borne','texte_bool','texte_long','source_vide','nature_vide','colonne_inconnue'])
def test_697_entrees_refusees_sans_mutation(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);body=tables(v);body['tables'][0]['lignes'][0][champ]=valeur
        before=donnees_metier(application);assert api.post(url(v),json=body).status_code==422
        assert donnees_metier(application)==before


def test_697_brouillon_neant_explicite_et_retrait_trace(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=tables(v);body['tables'][0].update(statut='a_completer',justification='',lignes=[{'montant_couvert':'0'}])
        body['tables'][1].update(statut='a_completer',justification='',lignes=[])
        v2=ok(api.post(url(v),json=body),201);ligne=ok(api.get(url(v2)))['tables'][0]['lignes'][0]
        assert ligne['montant_couvert']=='0.00' and ligne['valeur_nette'] is None and ligne['nature']==''
        body=tables(v2);body['tables'][0]['statut']='neant_declare'
        assert api.post(url(v2),json=body).status_code==422
        body['tables'][0]['lignes']=[];body['tables'][0]['justification']='Revue fictive, aucun engagement retenu'
        v3=ok(api.post(url(v2),json=body),201)
        assert ok(api.get(url(v3)))['tables'][0]['statut']=='neant_declare'
        assert len(ok(api.get(url(v2)))['tables'][0]['lignes'])==1
        body=tables(v3);body['tables'][1]['lignes']=[];assert api.post(url(v3),json=body).status_code==422
        body=tables(v3);body['tables'][0]['justification']=' ';assert api.post(url(v3),json=body).status_code==422
        body=tables(v3);body['tables']*=2;assert api.post(url(v3),json=body).status_code==422
        body=tables(v3);body['tables'][1]['code']='B8';assert api.post(url(v3),json=body).status_code==422
        body=tables(v3);body['tables'][0]['lignes']*=101;assert api.post(url(v3),json=body).status_code==422


def test_697_complements_pieces_et_contradiction_non_masquee(application):
    with closing(client(application)[0]) as api:
        v=creer(api);v=ok(api.post(chemin(v),json=demande(v)),201)
        v=ok(api.post(notes_url(v),json=notes(v)),201)
        v=ok(api.post(financement_url(v),json=flux(v)),201)
        piece=ok(joindre(api,v),201);r=ok(api.post(url(v),json=tables(v)),201)
        assert all(r['contenu'][k]==value for k,value in v['contenu'].items())
        assert ok(api.get(path(v)))['documents'][0]['id']==piece['id'] and ok(api.get(path(r)))['documents']==[]
        vue=ok(api.get(url(r)));assert len(vue['alertes'])==1 and 'B8' in vue['alertes'][0]
        # Une édition ultérieure de notes conserve les tableaux et leur contradiction visible.
        r2=ok(api.post(notes_url(r),json=notes(r)),201)
        assert r2['contenu']['tables_etic_documentaires']==r['contenu']['tables_etic_documentaires']
        assert ok(api.get(url(r2)))['alertes']==vue['alertes']


def test_697_societes_roles_empreinte_concurrence_et_devise(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        v=creer(api);assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=tables(v)).status_code==404
        body=tables(v);body['empreinte_parent']='0'*64;assert api.post(url(v),json=body).status_code==409
        sid=ok(api.get('/api/auth/me'))['societe_id'];email=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':email,'role':'lecture'}))
        token=ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token'];autre.headers['Authorization']='Bearer '+token
        assert autre.get(url(v)).status_code==200 and autre.post(url(v),json=tables(v)).status_code==403
        body=tables(v)
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(lambda _:api.post(url(v),json=body),range(2)))
        assert [r.status_code for r in rs]==[201,201] and rs[0].json()==rs[1].json()
        ok(api.patch('/api/societe/moi',json={'devise':'EUR'}))
        assert api.post(url(v),json=tables(v)).status_code==422
        assert api.get(url(rs[0].json())).status_code==200


def test_697_exports_exactitude_textes_logo_inconnus_et_manifestes(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=tables(v);body['tables'][0]['lignes'][0]['tiers']='=1+2\n<tiers fictif697 & source>'
        body['tables'][0]['lignes'][0]['montant_couvert']='9999999999999.99'
        v=ok(api.post(url(v),json=body),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));before=donnees_metier(application)
        x=api.get(BASE+f'/{v["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));ws=wb['ETIC documentaire B8']
        assert Decimal(str(ws['D2'].value))==Decimal('9999999999999.99') and ws['D2'].data_type=='n'
        assert ws['E2'].value=='Indisponible' and ws['C2'].data_type=='s'
        assert wb['ETIC documentaire B9']['D2'].value==0 and 'Logo société' in wb.sheetnames
        pdf=api.get(BASE+f'/{v["id"]}/pdf');assert pdf.status_code==200
        reader=PdfReader(BytesIO(pdf.content));t='\n'.join(p.extract_text() or '' for p in reader.pages)
        assert '<tiers fictif697 & source>' in t and '9 999 999 999 999,99 MAD' in t
        assert 'Valeur nette comptable : Indisponible MAD' in t and any(p.images for p in reader.pages)
        z=api.get(BASE+f'/{v["id"]}/zip');assert z.status_code==200;verifier_bundle(z.content,v)
        with ZipFile(BytesIO(z.content)) as archive:
            vue=json.loads(archive.read('tables_etic_documentaires.json'))
            assert vue=={k:value for k,value in ok(api.get(url(v))).items() if k not in ('id','version','empreinte_sha256')}
            assert vue['tables'][1]['lignes'][0]['montant_n1']=='0.00'
        assert donnees_metier(application)==before
