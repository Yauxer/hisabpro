"""Deux demandes de finalisation d'une facture, un seul mouvement de stock."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import closing
from datetime import date
import uuid
import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from test_reglement_comptabilisation_concurrente_isole import metier


def doubler(app,api,chemin):
    db=app['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
    try:
        db.execute(text('LOCK TABLE lignes_facture IN SHARE MODE'))
        f=pool.submit(api.post,chemin,json={})
        attendre_verrou(app,f,table='lignes_facture')
        g=pool.submit(api.post,chemin,json={})
        try:r2=g.result(timeout=2)
        except TimeoutError:r2=None
        tx.rollback()
        r1=f.result(timeout=30)
        r2=r2 if r2 is not None else g.result(timeout=30)
        return r1,r2
    finally:
        if tx.is_active:tx.rollback()
        db.close();pool.shutdown(wait=True)


@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('document',['brouillon','proforma'])
def test_finalisation_concurrente_un_numero_un_stock_et_comptabilisation(application,sens,document):
    with closing(client(application)[0]) as api:
        api.timeout=30
        ok(api.patch('/api/societe/moi',json={'stock_declencheur_vente':'facture','stock_declencheur_achat':'facture'}))
        suffix=uuid.uuid4().hex[:8]
        tid=ok(api.post('/api/tiers',json={'nom':'Tiers finalisation fictif543 '+suffix,
            'type':'client' if sens=='vente' else 'fournisseur'}),201)['id']
        aid=ok(api.post('/api/articles',json={'code':'FICT543-'+suffix,'designation':'Article fictif543 '+suffix,
            'stock_actuel':2,'is_stockable':True,'prix_achat_ht':100,'prix_vente_ht':100,
            'compte_achat':'6111','compte_vente':'71243','tva':20}),201)['id']
        f=ok(api.post('/api/factures',json={'type':sens,'date':date.today().isoformat(),
            'tiers_id':tid,'tiers':'Tiers finalisation fictif543 '+suffix,
            'reference':'FICT543-'+suffix,'est_proforma':document=='proforma','lignes':[
                {'article_id':aid,'description':'Article fictif543 '+suffix,'quantite':1,'prix_unitaire':100,'tva':20}]}),201)
        assert f['est_proforma'] is (document=='proforma') and not f['est_validee']
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:i'),{'i':aid})==2
            assert db.scalar(text('SELECT count(*) FROM mouvements_stock WHERE facture_id=:i'),{'i':f['id']})==0
        action='convertir-definitive' if document=='proforma' else 'valider'
        chemin=f"/api/factures/{f['id']}/{action}"
        r1,r2=doubler(application,api,chemin)
        attendu=400 if document=='proforma' else 200
        if (r1.status_code,r2.status_code)!=(200,attendu):
            print(application['api_log'].read_text(encoding='utf8')[-6500:])
        assert (r1.status_code,r2.status_code)==(200,attendu),(r1.text,r2.text)
        if document=='brouillon':assert r1.json()['numero']==r2.json()['numero']
        rows=ok(api.get('/api/factures',params={'exercice':date.today().year}))
        fin=next(x for x in rows if x['id']==f['id'])
        assert fin['est_validee'] and fin['est_proforma'] is False and fin['total_ttc']==120
        assert fin['numero']==r1.json()['numero']
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:i'),{'i':aid})==(1 if sens=='vente' else 3)
            assert db.scalar(text('SELECT count(*) FROM mouvements_stock WHERE facture_id=:i'),{'i':f['id']})==1
        avant=metier(application)
        assert api.post(chemin,json={}).status_code==attendu
        assert metier(application)==avant
        eid=ok(api.post(f"/api/factures/{f['id']}/comptabiliser",json={}))['ecriture_id']
        ok(api.post(f'/api/ecritures/{eid}/valider',json={}))
        assert api.get('/api/fec/export',params={'exercice':date.today().year}).status_code==200
