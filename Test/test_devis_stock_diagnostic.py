"""Diagnostic indicatif de stock : API/JWT et PostgreSQL isolés réels."""
import json
import math
import uuid
from types import SimpleNamespace
import httpx
import pytest
from sqlalchemy.orm import Session
import models
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application


def ok(r, status=200):
    assert r.status_code==status,r.text
    return r.json()


@pytest.fixture(scope='module')
def dossier(application):
    cible=application['cluster']
    assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
    api=httpx.Client(base_url=application['api_url'])
    suffix=uuid.uuid4().hex[:8]
    auth=ok(api.post('/api/auth/register',json={'nom':'Admin fictif','email':suffix+'@example.com',
         'password':'DiagnosticStock2026!','raison_sociale':'Diagnostic fictif '+suffix}))
    api.headers['Authorization']='Bearer '+auth['access_token']
    sid=ok(api.get('/api/societe/moi'))['id']
    a=ok(api.post('/api/articles',json={'code':'PHYS-'+suffix,'designation':'Article physique fictif',
         'stock_actuel':5,'is_stockable':True,'prix_vente_ht':100,'tva':20}),201)
    service=ok(api.post('/api/articles',json={'code':'SERV-'+suffix,'designation':'Service fictif',
         'stock_actuel':0,'is_stockable':False,'prix_vente_ht':100,'tva':20}),201)
    with Session(application['engine']) as db:
        autre=models.Societe(raison_sociale='Autre société laboratoire')
        db.add(autre);db.flush()
        etranger=models.Article(societe_id=autre.id,code='SECRET',designation='Nom confidentiel laboratoire',stock_actuel=77)
        archive=models.Article(societe_id=sid,code='ARCHIVE',designation='Article inactif fictif',stock_actuel=8,actif=False)
        db.add_all([etranger,archive]);db.flush();ids=(etranger.id,archive.id);db.commit()
    yield api,sid,a,service,ids
    api.close()


def etat(application):
    with Session(application['engine']) as db:
        return {modele.__tablename__:[repr(tuple(getattr(r,c.name) for c in modele.__table__.columns))
            for r in db.query(modele).order_by(modele.id).all()]
            for modele in (models.Article,models.MouvementStock,models.Devis,models.LigneDevis,models.Ecriture)}


def diagnostic(api,lignes):
    r=api.post('/api/devis/diagnostic-stock',json={'lignes':lignes})
    sortie=ok(r)
    assert sortie['devis_autorise'] is True
    assert sortie['source']=='Article.stock_actuel' and sortie['perimetre']=='stock_physique_societe'
    assert sortie['constate_le']
    return sortie


@pytest.mark.parametrize('quantite,statut,manquant',[(0,'disponible',0),(5,'disponible',0),(6,'a_approvisionner',1)])
def test_stock_physique_indicatif_sans_mutation(application,dossier,quantite,statut,manquant):
    api,sid,a,service,ids=dossier;avant=etat(application)
    r=diagnostic(api,[{'article_id':a['id'],'quantite':quantite}])['articles'][0]
    assert r['statut']==statut and r['stock_disponible']==5 and r['quantite_manquante']==manquant
    assert etat(application)==avant


def test_cumul_lignes_services_libres_et_huge_quantity(application,dossier):
    api,sid,a,service,ids=dossier;avant=etat(application)
    r=diagnostic(api,[{'article_id':a['id'],'quantite':3},{'article_id':a['id'],'quantite':3},
                      {'article_id':service['id'],'quantite':100},{'article_id':None,'quantite':20}])
    physique=next(t for t in r['articles'] if t['article_id']==a['id'])
    assert physique['quantite_demandee']==6 and physique['indices_lignes']==[0,1]
    assert physique['statut']=='a_approvisionner' and physique['quantite_manquante']==1
    prestation=next(t for t in r['articles'] if t['article_id']==service['id'])
    assert prestation['statut']=='non_stockable' and prestation['quantite_manquante'] is None
    assert r['lignes_non_rattachees']==[3]
    enorme=diagnostic(api,[{'article_id':a['id'],'quantite':1e308},{'article_id':a['id'],'quantite':1e308}])['articles'][0]
    from decimal import Decimal
    assert Decimal(str(enorme['quantite_demandee']))==Decimal('2e308')
    assert Decimal(str(enorme['quantite_manquante']))==Decimal(2*10**308-5)
    assert enorme['statut']=='a_approvisionner'
    assert enorme['diagnostics'] and isinstance(enorme['quantite_demandee'],str)
    assert etat(application)==avant


@pytest.mark.parametrize('stock',[None,float('nan'),float('inf'),float('-inf'),-1])
def test_stock_historique_inconnu_jamais_zero(application,dossier,stock):
    api,sid,a,service,ids=dossier
    with Session(application['engine']) as db:
        article=models.Article(societe_id=sid,code='LEG-'+uuid.uuid4().hex[:8],designation='Stock historique fictif',is_stockable=True)
        db.add(article);db.flush();article.stock_actuel=stock;aid=article.id;db.commit()
    avant=etat(application)
    r=diagnostic(api,[{'article_id':aid,'quantite':2}])['articles'][0]
    assert r['statut']=='inconnu' and r['stock_disponible'] is None and r['quantite_manquante'] is None
    assert r['diagnostics']
    assert etat(application)==avant


def test_article_etranger_archive_absent_et_aucune_ligne(application,dossier):
    api,sid,a,service,ids=dossier;avant=etat(application)
    for aid in (*ids,2147483647):
        r=diagnostic(api,[{'article_id':aid,'quantite':1}])['articles'][0]
        assert r['statut']=='inconnu' and r['designation'] is None and r['stock_disponible'] is None
    assert diagnostic(api,[])['articles']==[]
    assert etat(application)==avant


@pytest.mark.parametrize('q',[-1,True,False,float('nan'),float('inf'),float('-inf'),'NaN',{},[]])
def test_quantite_invalide_refusee_sans_mutation(application,dossier,q):
    api,sid,a,service,ids=dossier;avant=etat(application)
    r=api.post('/api/devis/diagnostic-stock',content=json.dumps({'lignes':[{'article_id':a['id'],'quantite':q}]}),
               headers={'Content-Type':'application/json'})
    assert r.status_code==422,r.text
    assert etat(application)==avant


def test_lecture_autorisee_sans_droit_ecriture_et_auth_obligatoire(application,dossier):
    api,sid,a,service,ids=dossier;avant=etat(application)
    email=uuid.uuid4().hex[:8]+'@example.com';password='StockLecture2026!'
    ok(api.post('/api/utilisateurs',json={'nom':'Lecteur fictif','email':email,'mot_de_passe':password,'role':'lecture'}),201)
    with httpx.Client(base_url=application['api_url']) as lecteur:
        token=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))
        lecteur.headers['Authorization']='Bearer '+token['access_token']
        assert diagnostic(lecteur,[{'article_id':a['id'],'quantite':6}])['articles'][0]['statut']=='a_approvisionner'
        lecteur.headers.pop('Authorization')
        assert lecteur.post('/api/devis/diagnostic-stock',json={'lignes':[]}).status_code==401
    assert etat(application)==avant


def test_service_cumul_decimal_et_une_seule_requete():
    from services.devis_stock_service import diagnostic_stock_devis
    article=SimpleNamespace(id=1,designation='Fixture',unite='unité',is_stockable=True,stock_actuel=.3)
    class Requete:
        def filter(self,*args):return self
        def all(self):return [article]
    class Base:
        appels=0
        def query(self,*args):self.appels+=1;return Requete()
    db=Base()
    sortie=diagnostic_stock_devis(db,1,[SimpleNamespace(article_id=1,quantite=.1),SimpleNamespace(article_id=1,quantite=.2)])
    assert db.appels==1
    assert sortie['articles'][0]['quantite_demandee']==.3
    assert sortie['articles'][0]['statut']=='disponible'


def test_stock_relit_mouvement_reel_et_devis_rupture_reste_autorise(application,dossier):
    from datetime import date
    api,sid,a,service,ids=dossier
    article=ok(api.post('/api/articles',json={'code':'FRESH-'+uuid.uuid4().hex[:8],
        'designation':'Article fraîcheur fictif','stock_actuel':5,'is_stockable':True,
        'prix_vente_ht':100,'tva':20}),201)
    assert diagnostic(api,[{'article_id':article['id'],'quantite':1}])['articles'][0]['stock_disponible']==5
    ok(api.patch(f"/api/articles/{article['id']}/stock",json={'stock_actuel':0,'reference':'Inventaire fictif fraîcheur'}))
    avant=etat(application)
    stock=diagnostic(api,[{'article_id':article['id'],'quantite':1}])['articles'][0]
    assert stock['stock_disponible']==0 and stock['statut']=='a_approvisionner'
    assert etat(application)==avant
    tiers=ok(api.post('/api/tiers',json={'nom':'Client devis rupture fictif','type':'client'}),201)
    devis=ok(api.post('/api/devis',json={'date':date.today().isoformat(),'tiers':tiers['nom'],
        'tiers_id':tiers['id'],'lignes':[{'article_id':article['id'],'description':article['designation'],
            'quantite':1,'prix_unitaire':100,'tva':20}]}),201)
    assert devis['lignes'][0]['article_id']==article['id']
    with Session(application['engine']) as db:
        assert db.get(models.Article,article['id']).stock_actuel==0
