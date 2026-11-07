"""Draft334 : sources inconnues du ledger, lecture seule PG nonce."""
from contextlib import closing
from types import SimpleNamespace
import json
import uuid

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from postgres_isole import verifier_cible_isolee
from services.stock_ledger_service import auditer_mouvements_article
from test_e2e_facturation_isole import application


def art(stock=6, cmup=100):
    return SimpleNamespace(id=1, code='TEST', designation='Test fictif', stock_actuel=stock, cmup=cmup)


def mvt(i, typ, qte, avant, apres, cout=100, cmup=100, source=None):
    return SimpleNamespace(id=i, type=typ, quantite=qte, stock_avant=avant,
        stock_apres=apres, cout_unitaire=cout, cmup_avant=None if source is None else 100,
        cmup_apres=cmup, source_type=source)


@pytest.mark.parametrize('stock,cmup', [(None,None),(None,100),(6,None),
    (float('nan'),100),(float('inf'),100),(6,float('inf'))])
def test_article_inconnu_ne_devient_pas_zero_ni_ok(stock, cmup):
    r = auditer_mouvements_article(art(stock, cmup), [])
    assert r['statut'] != 'ok'
    assert r['valeur_stock'] is None and not r['valorisation_complete']
    assert not r['audit_complet'] and r['anomalies']
    if stock is None or not isinstance(stock, (float,int)) or stock != stock or stock == float('inf'):
        assert r['stock_actuel'] is None
    json.dumps(r, allow_nan=False)


@pytest.mark.parametrize('champ', ['quantite','stock_avant','stock_apres','cout_unitaire','cmup_avant','cmup_apres'])
@pytest.mark.parametrize('valeur', [None,float('nan'),float('inf'),float('-inf')])
def test_mouvement_inconnu_diagnostique_sans_crash(champ, valeur):
    ligne = mvt(2, 'sortie', 4, 10, 6, source='facture')
    setattr(ligne, champ, valeur)
    r = auditer_mouvements_article(art(), [mvt(1,'entree',10,0,10),ligne])
    assert r['statut'] != 'ok' and not r['audit_complet']
    assert any(a['mouvement_id'] ==2 and champ in a['message'] for a in r['anomalies'])
    json.dumps(r, allow_nan=False)


def test_chaine_connue_et_cmup_avant_legacy_absent_preserves():
    lignes = [mvt(1,'entree',10,0,10),mvt(2,'sortie',4,10,6)]
    r = auditer_mouvements_article(art(), lignes)
    assert r['statut']=='ok' and r['audit_complet'] and r['valorisation_complete']
    assert (r['stock_actuel'],r['cmup_actuel'],r['valeur_stock'])==(6,100,600)


def test_zero_connu_et_stock_signe_ne_deviennent_pas_inconnus():
    zero = auditer_mouvements_article(art(0,0), [])
    assert (zero['stock_actuel'],zero['cmup_actuel'],zero['valeur_stock'])==(0,0,0)
    assert zero['valorisation_complete']
    signe = auditer_mouvements_article(art(-1,100), [])
    assert signe['stock_actuel']==-1 and signe['valeur_stock']==-100


def test_quantite_negative_ne_declenche_pas_division_zero():
    r = auditer_mouvements_article(art(), [mvt(1,'entree',10,0,10),mvt(2,'entree',-10,10,0)])
    assert any(a['code']=='quantite_invalide' for a in r['anomalies'])
    json.dumps(r, allow_nan=False)


def test_cmup_inconnu_ne_reprend_pas_une_valeur_ancienne_comme_source_certaine():
    r = auditer_mouvements_article(art(5,100), [mvt(1,'entree',10,0,10),
        mvt(2,'sortie',4,10,6,cmup=None),mvt(3,'sortie',1,6,5,cout=80,cmup=80)])
    assert not r['audit_complet']
    assert not any(a['code']=='cout_sortie_cmup' and a['mouvement_id']==3 for a in r['anomalies'])


def test_produit_non_representable_indetermine_sans_perdre_sources_finies():
    r = auditer_mouvements_article(art(1e308,1e308), [])
    assert r['stock_actuel']==1e308 and r['cmup_actuel']==1e308
    assert r['valeur_stock'] is None and not r['valorisation_complete']
    json.dumps(r, allow_nan=False)


@pytest.mark.parametrize('valeur', [True,False,'invalide'])
@pytest.mark.parametrize('champ', ['quantite','stock_avant','stock_apres','cout_unitaire','cmup_avant','cmup_apres'])
def test_source_non_numerique_ne_devient_pas_zero(champ, valeur):
    ligne=mvt(1,'entree',10,0,10,source='facture')
    setattr(ligne,champ,valeur)
    r=auditer_mouvements_article(art(10,100),[ligne])
    assert not r['audit_complet']
    assert any(a['champ']==champ and a['mouvement_id']==1 for a in r['nombres_diagnostics'])
    json.dumps(r,allow_nan=False)


def test_cmup_legacy_absent_tolere_mais_nonfini_present_signale():
    ligne=mvt(1,'entree',10,0,10)
    ligne.cmup_avant=float('nan')
    r=auditer_mouvements_article(art(10,100),[ligne])
    assert not r['audit_complet']
    assert any(a['champ']=='cmup_avant' for a in r['nombres_diagnostics'])


def test_stock_initial_historique_et_fraction_finie_preserves():
    r=auditer_mouvements_article(art(5.25,100),[mvt(1,'entree',0.25,5,5.25)])
    assert r['statut']=='ok' and r['audit_complet']
    assert r['valeur_stock']==525 and r['stock_actuel']==5.25


def test_source_inconnue_ne_masque_pas_controle_stock_independant():
    r=auditer_mouvements_article(art(6,100),[mvt(1,'entree',10,0,10,cmup=None),
        mvt(2,'sortie',4,9,5)])
    assert not r['audit_complet']
    assert any(a['code']=='rupture_continuite' and a['mouvement_id']==2 for a in r['anomalies'])
    assert any(a['code']=='stock_article_ecart' for a in r['anomalies'])


def ok(r, status=200):
    assert r.status_code==status,r.text
    return r.json()


def photo(application, sid):
    with application['engine'].connect() as db:
        resultat = {t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x '
            'WHERE societe_id=:sid ORDER BY id'), {'sid':sid}).scalars().all()
            for t in ('articles','mouvements_stock','ecritures')}
        resultat['lignes_ecriture'] = db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l '
            'JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:sid ORDER BY l.id'),
            {'sid':sid}).scalars().all()
        return resultat


@pytest.fixture
def dossier(application):
    c=application['cluster'];verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    suffix=uuid.uuid4().hex[:8];email='ledger-'+suffix+'@example.com';password='LedgerFictif2026!'
    with httpx.Client(base_url=application['api_url']) as api:
        token=ok(api.post('/api/auth/register',json={'nom':'Ledger fictif','email':email,
            'password':password,'raison_sociale':'Ledger '+suffix}))['access_token']
        api.headers['Authorization']='Bearer '+token
        sid=ok(api.get('/api/societe/moi'))['id']
        def creer(code):
            return ok(api.post('/api/articles',json={'code':code+'-'+suffix,
                'designation':code+' fictif '+suffix,'stock_actuel':0,'tva':20}),201)['id']
        aid=creer('SAIN');inconnu=creer('INCONNU');cout=creer('COUT');grand=creer('GRAND')
        with Session(application['engine']) as db:
            a=db.get(models.Article,aid);a.stock_actuel=6;a.cmup=100
            b=db.get(models.Article,cout);b.stock_actuel=1;b.cmup=100
            g=db.get(models.Article,grand);g.stock_actuel=1e308;g.cmup=1e308
            for article_id,typ,qte,av,ap in [(aid,'entree',10,0,10),(aid,'sortie',4,10,6),(cout,'entree',1,0,1)]:
                db.add(models.MouvementStock(societe_id=sid,article_id=article_id,type=typ,
                    quantite=qte,stock_avant=av,stock_apres=ap,cout_unitaire=100,
                    cmup_apres=100,cmup_avant=None,source_type=None))
            db.commit()
        with application['engine'].begin() as db:
            db.execute(text('UPDATE articles SET stock_actuel=NULL,cmup=NULL WHERE id=:id'),{'id':inconnu})
            db.execute(text('UPDATE mouvements_stock SET cout_unitaire=:v WHERE article_id=:id'),
                {'id':cout,'v':float('inf')})
        yield api,sid,suffix,email,password,{'sain':aid,'inconnu':inconnu,'cout':cout,'grand':grand}


def test_api_audit_nullable_filtre_compteurs_et_conservation(application,dossier):
    api,sid,suffix,email,password,ids=dossier
    avant=photo(application,sid)
    tout=ok(api.get('/api/inventaire/controle-mouvements'))
    assert tout['articles_controles']==4 and tout['mouvements_controles']==3
    assert not tout['audit_complet'] and not tout['valorisation_complete'] and tout['valeur_stock'] is None
    lignes={x['article_id']:x for x in tout['lignes']}
    assert lignes[ids['sain']]['statut']=='ok' and lignes[ids['sain']]['valeur_stock']==600
    assert lignes[ids['inconnu']]['stock_actuel'] is None and lignes[ids['inconnu']]['cmup_actuel'] is None
    assert lignes[ids['cout']]['anomalies'] and not lignes[ids['cout']]['audit_complet']
    assert lignes[ids['grand']]['stock_actuel']==1e308 and lignes[ids['grand']]['valeur_stock'] is None
    filtre=ok(api.get('/api/inventaire/controle-mouvements',params={'anomalies_uniquement':'true'}))
    assert {l['article_id'] for l in filtre['lignes']}==set(ids.values())-{ids['sain']}
    for cle in ('articles_controles','mouvements_controles','articles_ok','articles_warning','articles_erreur','valeur_stock'):
        assert filtre[cle]==tout[cle]
    assert photo(application,sid)==avant


def test_api_total_deborde_et_exclusion_services_archives(application,dossier):
    api,sid,suffix,email,password,ids=dossier
    service=ok(api.post('/api/articles',json={'code':'SERVICE-'+suffix,'designation':'Service fictif',
        'stock_actuel':0,'tva':20,'is_stockable':False}),201)['id']
    archive=ok(api.post('/api/articles',json={'code':'ARCHIVE-'+suffix,'designation':'Archive fictive',
        'stock_actuel':0,'tva':20}),201)['id']
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET actif=false WHERE id=:id'),{'id':archive})
        for aid in ids.values():
            db.execute(text('UPDATE articles SET stock_actuel=:q,cmup=1 WHERE id=:id'),{'q':1e308,'id':aid})
    avant=photo(application,sid)
    r=ok(api.get('/api/inventaire/controle-mouvements'))
    assert r['articles_controles']==4 and r['valeur_stock'] is None
    assert not r['valorisation_complete'] and r['nombres_diagnostics']['valeur_stock']
    assert all(l['valorisation_complete'] and l['valeur_stock']==1e308 for l in r['lignes'])
    assert service not in {l['article_id'] for l in r['lignes']}
    assert archive not in {l['article_id'] for l in r['lignes']}
    assert photo(application,sid)==avant
    with httpx.Client(base_url=application['api_url']) as autre:
        jeton=ok(autre.post('/api/auth/register',json={'nom':'Autre ledger','email':'autre-'+email,
            'password':password,'raison_sociale':'Autre ledger '+suffix}))['access_token']
        autre.headers['Authorization']='Bearer '+jeton
        vide=ok(autre.get('/api/inventaire/controle-mouvements'))
        assert vide['lignes']==[] and vide['articles_controles']==0
    assert photo(application,sid)==avant
