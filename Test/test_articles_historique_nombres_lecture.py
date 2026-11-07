"""Projection des nombres historiques articles, API/PG nonce sans réparation."""
from contextlib import closing
from datetime import datetime
import json
import uuid
import pytest
from sqlalchemy import text
import schemas
from test_e2e_facturation_isole import application
from test_articles_stock_historique_lecture import dossier, photographie
from test_ras_lecture_conservation import client

CHAMPS=('prix_vente_ht','prix_achat_ht','frais_emballage','frais_transport','stock_min','tva','cmup')
BASE=dict(id=1,code='LEGACY',designation='Article fictif',actif=True,created_at=datetime(2026,10,10),stock_actuel=0)


@pytest.mark.parametrize('champ',CHAMPS)
@pytest.mark.parametrize('valeur',[None,float('nan'),float('inf'),float('-inf'),-1,True,False])
def test_sortie_historique_inconnue_nullable_diagnostique(champ,valeur):
    out=schemas.ArticleOut(**BASE,**{champ:valeur})
    assert getattr(out,champ) is None
    assert champ in out.nombres_diagnostics
    assert json.loads(out.model_dump_json())[champ] is None


@pytest.mark.parametrize('valeur',[0,0.125,1e308])
def test_valeurs_connues_conservees_sans_plafond_prix(valeur):
    data={champ:valeur for champ in CHAMPS};data['tva']=20
    out=schemas.ArticleOut(**BASE,**data)
    assert out.nombres_diagnostics=={} and out.stock_diagnostic is None
    assert all(getattr(out,c)==valeur for c in CHAMPS if c!='tva')
    assert out.tva==20


@pytest.mark.parametrize('valeur',[101,1e308])
def test_tva_historique_hors_intervalle_inconnue(valeur):
    out=schemas.ArticleOut(**BASE,tva=valeur)
    assert out.tva is None and 'tva' in out.nombres_diagnostics


def creer(api):
    r=api.post('/api/articles',json={'code':'LECTURE-'+uuid.uuid4().hex[:10],
        'designation':'Historique chiffré fictif','stock_actuel':0,'prix_vente_ht':10,'prix_achat_ht':8,'tva':20})
    assert r.status_code==201,r.text
    return r.json()['id']


@pytest.mark.parametrize('champ',CHAMPS)
@pytest.mark.parametrize('valeur',[None,float('nan'),float('inf'),float('-inf'),-1])
def test_api_nombres_historique_lisibles_sans_mutation(application,dossier,champ,valeur):
    api,sid=dossier;aid=creer(api)
    # Colonnes constantes de la liste CHAMPS uniquement ; cluster possédé.
    with application['engine'].begin() as db:
        db.execute(text(f'UPDATE articles SET {champ}=:v WHERE id=:id AND societe_id=:sid'),{'v':valeur,'id':aid,'sid':sid})
    avant=photographie(application)
    r=api.get('/api/articles')
    assert r.status_code==200,r.text
    row=next(x for x in r.json() if x['id']==aid)
    assert row[champ] is None and champ in row['nombres_diagnostics']
    assert row['stock_actuel']==0 and row['stock_diagnostic'] is None
    assert photographie(application)==avant


def test_api_tva_historique_hors_intervalle(application,dossier):
    api,sid=dossier;aid=creer(api)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET tva=101 WHERE id=:id'),{'id':aid})
    avant=photographie(application)
    row=next(x for x in api.get('/api/articles').json() if x['id']==aid)
    assert row['tva'] is None and 'tva' in row['nombres_diagnostics']
    assert photographie(application)==avant


def test_patch_texte_preserve_inconnus_et_correction_champ_explicit(application,dossier):
    api,sid=dossier;aid=creer(api)
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET '+','.join(c+'=NULL' for c in CHAMPS)+' WHERE id=:id'),{'id':aid})
    avant=photographie(application)
    r=api.patch(f'/api/articles/{aid}',json={'description':'Note explicite fictive'})
    assert r.status_code==200,r.text
    assert all(r.json()[c] is None for c in CHAMPS)
    with application['engine'].connect() as db:
        assert db.execute(text('SELECT '+','.join(CHAMPS)+' FROM articles WHERE id=:id'),{'id':aid}).one()==(None,)*len(CHAMPS)
    apres=photographie(application)
    assert apres['mouvements_stock']==avant['mouvements_stock'] and apres['ecritures']==avant['ecritures']
    r=api.patch(f'/api/articles/{aid}',json={'prix_vente_ht':0.125})
    assert r.status_code==200,r.text
    assert r.json()['prix_vente_ht']==0.125 and 'prix_vente_ht' not in r.json()['nombres_diagnostics']
    with application['engine'].connect() as db:
        assert db.execute(text('SELECT '+','.join(CHAMPS)+' FROM articles WHERE id=:id'),{'id':aid}).one()==(0.125,)+(None,)*(len(CHAMPS)-1)
    avant_iso=photographie(application)
    with closing(client(application)[0]) as autre:
        assert autre.get('/api/articles').json()==[]
        assert autre.patch(f'/api/articles/{aid}',json={'description':'Interdit'}).status_code==404
    assert photographie(application)==avant_iso


def test_api_zero_fraction_grand_prix_connus(application,dossier):
    api,sid=dossier
    for valeur in (0,0.125,1e308):
        aid=creer(api)
        r=api.patch(f'/api/articles/{aid}',json={c:valeur for c in CHAMPS if c not in ('tva','cmup')})
        assert r.status_code==200,r.text
        assert r.json()['nombres_diagnostics']=={}
        assert all(r.json()[c]==valeur for c in CHAMPS if c not in ('tva','cmup'))
