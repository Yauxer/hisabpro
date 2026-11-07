"""Contrepassation idempotente : original intact, une correction, PG nonce."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor,TimeoutError
from datetime import date,timedelta
import pytest
from sqlalchemy import text
from test_reconciliations_concurrentes_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_tva_calcul_cloture_isole import dossier
from test_stock_validation_journal_concurrente_isole import lignes,audit
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_tva_verrou_exercice_isole import attendre_verrou
from recette_restauration_consolidee_084 import empreintes_tables


def preparer(api,*,ferme=False,client_collectif=False,validee=True):
    p,_=dossier(api)
    if client_collectif:
        tid=ok(api.post('/api/tiers',json={'nom':'Client fictif528','type':'client'}),201)['id']
        ls=[{'compte':'3421','libelle':'Client fictif528','debit':1200,'tiers_id':tid},
            {'compte':'7111','libelle':'Vente fictive528','credit':1000},
            {'compte':'4455','libelle':'TVA hypothese fictive528','credit':200}]
    else:ls=[{'compte':'5141','libelle':'Debit fictif528','debit':100},
             {'compte':'4481','libelle':'Credit fictif528','credit':100}]
    eid=ok(api.post('/api/ecritures',json={'date':f"{p['a']}-12-31",'journal':'OD',
        'reference':'ORIGINAL-FICTIF528','libelle':'Original fictif528',
        'est_validee':validee,'lignes':ls}),201)['id']
    if ferme:ok(api.post('/api/cloture/cloturer',params={'exercice':p['a']}))
    p['cible']=p['a']+1 if ferme else p['a']
    p['jour']=f"{p['a']+1}-01-01" if ferme else f"{p['a']}-12-31"
    return p,eid


def contrepasser(api,eid,jour,motif='Correction fictive528 A'):
    return api.post(f'/api/ecritures/{eid}/contrepasser',json={'date_correction':jour,'motif':motif})


def original(app,eid):
    with app['engine'].connect() as c:
        return c.scalar(text('SELECT row_to_json(e)::text FROM ecritures e WHERE id=:i'),{'i':eid}),lignes(app,eid),audit(app,eid)


def compteur(app,p):
    with app['engine'].connect() as c:
        return c.scalar(text("SELECT dernier_numero FROM ecriture_sequences WHERE societe_id=:s AND exercice=:a AND journal='OD'"),{'s':p['s'],'a':p['cible']}) or 0


@pytest.mark.parametrize('ferme',[False,True])
@pytest.mark.parametrize('date_differente',[False,True])
def test_deux_contrepassations_retournent_meme_correction_sans_modifier_original(application,ferme,date_differente):
    with closing(client(application)[0]) as api:
        api.timeout=30;p,eid=preparer(api,ferme=ferme,client_collectif=not ferme)
        avant=original(application,eid);numero_avant=compteur(application,p)
        jour2=(date.fromisoformat(p['jour'])+timedelta(days=1)).isoformat() if date_differente else p['jour']
        db=application['engine'].connect();tx=db.begin();pool=ThreadPoolExecutor(2)
        try:
            db.execute(text('LOCK TABLE ecriture_sequences IN SHARE MODE'))
            f=pool.submit(contrepasser,api,eid,p['jour']);attendre_verrou(application,f,table='ecritures')
            g=pool.submit(contrepasser,api,eid,jour2,'Correction fictive528 B')
            try:r2=g.result(timeout=2)
            except TimeoutError:r2=None
            tx.rollback();r1=f.result(timeout=30)
            if r2 is None:r2=g.result(timeout=30)
            assert r1.status_code==r2.status_code==200,(r1.text,r2.text)
            x,y=r1.json(),r2.json()
            assert not x['deja_existante'] and y['deja_existante'],(x,y)
            assert x['id']==y['id'] and x['numero_ecriture']==y['numero_ecriture'] and x['date']==y['date']==p['jour']
        finally:
            if tx.is_active:tx.rollback()
            db.close();pool.shutdown(wait=True)
        assert original(application,eid)==avant
        assert compteur(application,p)==numero_avant+1
        with application['engine'].connect() as c:
            assert c.scalar(text('SELECT count(*) FROM ecritures WHERE contrepassation_de_id=:i'),{'i':eid})==1
            correction=c.execute(text('SELECT id,est_validee,exercice,motif_correction FROM ecritures WHERE contrepassation_de_id=:i'),{'i':eid}).one()
            assert correction==(x['id'],True,p['cible'],'Correction fictive528 A')
            colonnes='compte,debit,credit,tiers_id,nature_auxiliaire,compte_auxiliaire_snapshot,libelle_auxiliaire_snapshot'
            src=c.execute(text(f'SELECT {colonnes} FROM lignes_ecriture WHERE ecriture_id=:i ORDER BY compte'),{'i':eid}).all()
            dst=c.execute(text(f'SELECT {colonnes} FROM lignes_ecriture WHERE ecriture_id=:i ORDER BY compte'),{'i':x['id']}).all()
            assert dst==[(r[0],r[2],r[1],*r[3:]) for r in src]
            assert c.scalar(text("SELECT count(*) FROM audit_ecritures WHERE ecriture_id=:i AND ancien->>'est_validee'='false' AND nouveau->>'est_validee'='true'"),{'i':x['id']})==1
        assert api.get('/api/fec/export',params={'exercice':p['cible']}).status_code==200


def metier(app):return {k:v for k,v in empreintes_tables(app['engine']).items() if k!='audit_actions'}


def test_brouillon_refuse_puis_validation_et_contrepassation_possibles(application):
    with closing(client(application)[0]) as api:
        p,eid=preparer(api,validee=False);avant=metier(application)
        assert contrepasser(api,eid,p['jour']).status_code==409
        assert metier(application)==avant
        ok(api.post(f'/api/ecritures/{eid}/valider'))
        assert not ok(contrepasser(api,eid,p['jour']))['deja_existante']


def test_periode_originale_close_refusee_puis_reprise_suivante(application):
    with closing(client(application)[0]) as api:
        p,eid=preparer(api,ferme=True);avant=metier(application)
        assert contrepasser(api,eid,f"{p['a']}-12-31").status_code==423
        assert metier(application)==avant
        assert not ok(contrepasser(api,eid,p['jour']))['deja_existante']
