"""Notes ETIC : PostgreSQL natif nonce, versions, rôles et exports réels."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib,json
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text
from test_balance_documents691_isole import (
    application,application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,ok,creer,demande,chemin,BASE,donnees_metier,joindre,path)
from test_balance_dossier689_isole import verifier_bundle
from test_logo_societe import image_data


def url(v):return BASE+f'/{v["id"]}/notes-etic'


def notes(v,**valeurs):
    return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'lignes':[
        {'code':'A1','statut':'renseigne','texte':'Note fictive693 : méthode à vérifier <sans certification>.',
         'justification':'Annexe de travail fictive693',**valeurs},
        {'code':'C5','statut':'a_completer','texte':'Revue des événements encore en attente.'},
        {'code':'B8','statut':'non_applicable','justification':'Déclaration fictive signée à obtenir — pas de donnée réelle.'}]}


def test_693_initial_inconnu_version_rejeu_et_sources_preservees(application):
    from services.etic_service import CATALOGUE_ETIC
    with closing(client(application)[0]) as api:
        v=creer(api);before=donnees_metier(application);vue=ok(api.get(url(v)))
        assert len(vue['lignes'])==len(CATALOGUE_ETIC) and not vue['pret_a_deposer']
        assert vue['comptage_notes']=={'a_completer':len(CATALOGUE_ETIC),'renseigne':0,'non_applicable':0}
        assert vue['auteur'] is None and all(r['texte']==r['justification']=='' for r in vue['lignes'])
        body=notes(v);r=ok(api.post(url(v),json=body),201);snapshot=deepcopy(r)
        assert r['id']!=v['id'] and r['version']==2 and ok(api.get(BASE+f'/{v["id"]}'))==v
        assert all(r['contenu'][k]==value for k,value in v['contenu'].items())
        vue=ok(api.get(url(r)));assert vue['comptage_notes']['a_completer']==len(CATALOGUE_ETIC)-2
        assert vue['comptage_notes']['renseigne']==vue['comptage_notes']['non_applicable']==1
        assert vue['parent']['empreinte_sha256']==v['empreinte_sha256']
        assert vue['auteur']['id']==ok(api.get('/api/auth/me'))['id'] and vue['auteur']['nom']
        assert ok(api.post(url(v),json=body),201)==r
        body['lignes'][0]['texte']='Autre texte';assert api.post(url(v),json=body).status_code==409
        after=donnees_metier(application)
        assert all(after[k]==value for k,value in before.items() if k!='liasse_balances_preparation')
        # Un changement futur du catalogue ne réécrit pas les titres archivés.
        from services.balance_etic_notes_service import presentation
        ancien=CATALOGUE_ETIC[0]['titre']
        try:
            CATALOGUE_ETIC[0]['titre']='Titre FUTUR non conservé'
            assert presentation(snapshot)['lignes'][0]['titre']==ancien
        finally:CATALOGUE_ETIC[0]['titre']=ancien


@pytest.mark.parametrize('champ,valeur',[
    ('code','T999'),('statut','valide'),('texte',' '),('texte',True),('texte',100),
    ('texte','a'*10001),('justification',' '),('justification','a'*2001),('extra','refusé')],
    ids=['code','statut','vide','booleen','nombre','texte_long','justification_vide','reference_longue','champ_inconnu'])
def test_693_entrees_refusees_sans_version(application,champ,valeur):
    with closing(client(application)[0]) as api:
        v=creer(api);body=notes(v,**{champ:valeur});before=donnees_metier(application)
        assert api.post(url(v),json=body).status_code==422
        assert donnees_metier(application)==before


def test_693_permissions_societe_empreinte_et_doublons(application):
    api,email,password=client(application)
    with closing(api),closing(client(application)[0]) as autre:
        v=creer(api)
        assert autre.get(url(v)).status_code==404 and autre.post(url(v),json=notes(v)).status_code==404
        body=notes(v);body['empreinte_parent']='0'*64;assert api.post(url(v),json=body).status_code==409
        body=notes(v);body['lignes']*=2;assert api.post(url(v),json=body).status_code==422
        body=notes(v);body['lignes'][2]['justification']=' ';assert api.post(url(v),json=body).status_code==422
        sid=ok(api.get('/api/auth/me'))['societe_id'];lemail=ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter',params={'email':lemail,'role':'lecture'}))
        switched=ok(autre.post(f'/api/societes/switcher/{sid}'))
        autre.headers['Authorization']='Bearer '+switched['access_token']
        assert autre.get(url(v)).status_code==200
        assert autre.post(url(v),json=notes(v)).status_code==403


def test_693_complements_preserves_retrait_nouvelle_version_et_pieces_par_version(application):
    with closing(client(application)[0]) as api:
        v=creer(api);v2=ok(api.post(chemin(v),json=demande(v)),201)
        piece=ok(joindre(api,v2),201);v3=ok(api.post(url(v2),json=notes(v2)),201)
        assert v3['contenu']['echeances_documentaires']==v2['contenu']['echeances_documentaires']
        assert ok(api.get(path(v2)))['documents'][0]['id']==piece['id']
        assert ok(api.get(path(v3)))['documents']==[]
        n=notes(v3);n['lignes']=[{'code':'A1','statut':'a_completer','texte':'','justification':''}]
        v4=ok(api.post(url(v3),json=n),201)
        vue=ok(api.get(url(v4)));assert all(r['statut']=='a_completer' for r in vue['lignes'])
        assert ok(api.get(url(v3)))['comptage_notes']['renseigne']==1
        # Les ventilations restent conservées après les éditions de notes.
        assert v4['contenu']['echeances_documentaires']==v2['contenu']['echeances_documentaires']


def test_693_exports_meme_version_logo_texte_non_interprete_et_manifeste(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=notes(v,texte='=HYPERLINK("https://example.invalid")\n<note & justificatif fictif693>')
        v=ok(api.post(url(v),json=body),201)
        ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}));before=donnees_metier(application)
        x=api.get(BASE+f'/{v["id"]}/xlsx');assert x.status_code==200
        wb=load_workbook(BytesIO(x.content));rows=list(wb['Notes ETIC documentaires'].values)
        assert rows[1][0]=='A1' and rows[1][3]==body['lignes'][0]['texte']
        assert wb['Notes ETIC documentaires']['D2'].data_type=='s' and 'Logo société' in wb.sheetnames
        pdf=api.get(BASE+f'/{v["id"]}/pdf');assert pdf.status_code==200
        reader=PdfReader(BytesIO(pdf.content));t='\n'.join(p.extract_text() or '' for p in reader.pages)
        assert '<note & justificatif fictif693>' in t and 'Notes documentaires ETIC' in t
        assert any(p.images for p in reader.pages)
        z=api.get(BASE+f'/{v["id"]}/zip');assert z.status_code==200
        verifier_bundle(z.content,v)
        with ZipFile(BytesIO(z.content)) as archive:
            vue=json.loads(archive.read('notes_etic_documentaires.json'))
            api_vue=ok(api.get(url(v)))
            assert vue=={k:value for k,value in api_vue.items() if k not in ('id','version','empreinte_sha256')}
            assert vue['pret_a_deposer'] is False
            assert vue['lignes'][0]['texte']==body['lignes'][0]['texte']
            m=json.loads(archive.read('MANIFESTE_SHA256.json'))
            assert m['fichiers']['notes_etic_documentaires.json']['sha256']==hashlib.sha256(archive.read('notes_etic_documentaires.json')).hexdigest()
        assert donnees_metier(application)==before


def test_693_concurrence_et_aucune_modification_des_versions_existantes(application):
    with closing(client(application)[0]) as api:
        v=creer(api);body=notes(v)
        def envoyer(_):return api.post(url(v),json=body)
        with ThreadPoolExecutor(max_workers=2) as pool:rs=list(pool.map(envoyer,range(2)))
        assert [r.status_code for r in rs]==[201,201]
        assert rs[0].json()==rs[1].json()
        with application['engine'].begin() as db:
            with pytest.raises(Exception):
                db.execute(text('UPDATE liasse_balances_preparation SET contenu=contenu WHERE id=:id'),{'id':v['id']})
