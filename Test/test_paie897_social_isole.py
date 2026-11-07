"""API HTTP et PostgreSQL éphémère natif : aucun accès à une base utilisateur."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
import pytest,httpx
from sqlalchemy import text
from test_paie893_campagnes_isole import (
    application as application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser)
from test_paie897_social_unitaire import contenu,qualifie
from test_paie889_catalogue_isole import dec
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];S='/api/employes/personnel/social'


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/116_paie_referentiel_social.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application115):
    app=application115;avant=empreintes_tables(app['engine']);installer(app);installer(app)
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items())
    with app['engine'].connect() as db:assert db.scalar(text('SELECT count(*) FROM paie_branches_sociales'))==0
    yield app


def creer(eq,code='BRANCHE_FICTIVE',regime='REGIME_FICTIF',**kw):
    return ok(eq['a'].post(S,json={'code':code,'regime':regime,'contenu':contenu(**kw),'motif':'Création FICTIVE897'}),201)


def approuver(eq,v):return eq['b'].post(f'{S}/versions/{v["id"]}/approuver',json=dec())


def version(eq,v,c):return ok(eq['a'].post(f'{S}/{v["branche_id"]}/versions',json={'version_attendue':v['numero'],'contenu':c,'motif':'Version FICTIVE897'}),201)


def test_897_dates_versions_immutables_et_absence_ecriture(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid']);v=creer(eq);rid=v['branche_id']
    assert eq['a'].post(f'{S}/versions/{v["id"]}/approuver',json=dec()).status_code==403
    ok(approuver(eq,v));ancien=ok(eq['a'].get(f'{S}/{rid}'))['versions'][0]
    n=version(eq,v,contenu(date_debut='2027-01-01',taux_salarial='1.5'));ok(approuver(eq,n))
    assert eq['a'].post(f'{S}/{rid}/versions',json={'version_attendue':1,'contenu':contenu(),'motif':'Périmé FICTIF'}).status_code==409
    assert ok(eq['a'].get(S,params={'au':'2026-12-31'}))['elements'][0]['courante_id']==v['id']
    assert ok(eq['a'].get(S,params={'au':'2027-01-01'}))['elements'][0]['courante_id']==n['id']
    assert ok(eq['a'].get(f'{S}/{rid}'))['versions'][1]==ancien and eq['a'].get(S).headers['cache-control']=='no-store'
    assert comptabilite(application,eq['sid'])==avant


def test_897_double_comptage_ipe_meme_regime_bloque_sql_et_api(application,equipe):
    eq=equipe;v=creer(eq,composants=['COURT_TERME','IPE']);ok(approuver(eq,v))
    n=creer(eq,'IPE_SEPARE',composants=['IPE']);assert approuver(eq,n).status_code==409
    sql="UPDATE paie_branche_sociale_versions SET statut='APPROUVEE',decision_par=:u,decision_at=clock_timestamp(),motif_decision='FICTIF',reference_controle='FICTIF' WHERE id=:i"
    for engine in [application['engine'],application['personnel_runtime']]:refuser(application,sql,{'u':eq['bid'],'i':n['id']},engine=engine)
    autre=creer(eq,'IPE_SEPARE','AUTRE_REGIME',composants=['IPE']);ok(approuver(eq,autre))
    assert ok(eq['a'].get(S,params={'regime':'AUTRE_REGIME'}))['total']==1


def test_897_intervalles_pas_seulement_date_debut_et_relais(equipe):
    eq=equipe;v=creer(eq,composants=['IPE'],date_debut='2026-01-01');ok(approuver(eq,v))
    n=version(eq,v,contenu(composants=['COURT_TERME'],date_debut='2027-02-01'));ok(approuver(eq,n))
    conflit=creer(eq,'IPE_CONFLIT',composants=['IPE'],date_debut='2027-01-01',date_fin='2027-02-01');assert approuver(eq,conflit).status_code==409
    relais=creer(eq,'IPE_RELAIS',composants=['IPE'],date_debut='2027-02-01');ok(approuver(eq,relais))


def test_897_qualification_source_habilitation_et_confirmation(application,equipe):
    eq=equipe;v=ok(eq['a'].post(S,json={'code':'QUALIFIE_FICTIF','regime':'FICTIF','contenu':qualifie(),'motif':'Test FICTIF897'}),201)
    assert approuver(eq,v).status_code==403
    grant(eq['a'],eq['bid'],'personnel.valider_regles_paie');assert approuver(eq,v).status_code==400
    ok(eq['b'].post(f'{S}/versions/{v["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)))
    d=ok(eq['a'].get(f'{S}/{v["branche_id"]}'))['versions'][0];assert d['verification_reglementaire_confirmee'] and d['decision_par']==eq['bid']


def test_897_isolation_profil_personnel_et_immutabilite(application,equipe):
    eq=equipe;v=creer(eq);rid=v['branche_id'];assert eq['l'].get(S).status_code==403
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre);assert autre.get(f'{S}/{rid}').status_code==404
        assert autre.post(f'{S}/versions/{v["id"]}/rejeter',json=dec()).status_code==404
    p,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(p):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert p.get(S).status_code==200 and p.get('/api/factures').status_code==403
        assert p.get(S+'/1/autre').status_code==404 and p.post(S+'/1',json={}).status_code==405
    for sql in ["UPDATE paie_branches_sociales SET regime='AUTRE' WHERE id=:r", "UPDATE paie_branche_sociale_versions SET contenu='{}' WHERE id=:i", 'DELETE FROM paie_branche_sociale_versions WHERE id=:i','TRUNCATE paie_branche_sociale_versions']:
        for engine in [application['engine'],application['personnel_runtime']]:refuser(application,sql,{'i':v['id'],'r':rid},engine=engine)


def test_897_concurrence_double_decision_et_doublon(equipe,application):
    eq=equipe;v=creer(eq)
    assert eq['a'].post(S,json={'code':'BRANCHE_FICTIVE','regime':'REGIME_FICTIF','contenu':contenu(),'motif':'Doublon FICTIF'}).status_code==409
    def decider(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['b'].headers),timeout=30) as c:return c.post(f'{S}/versions/{v["id"]}/approuver',json=dec()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(decider,range(2)))
    assert sorted(r)==[200,409]


def test_897_expiration_rejet_et_rejeu_avec_donnees(application,equipe):
    eq=equipe;v=creer(eq,date_fin='2026-12-31');ok(approuver(eq,v))
    assert ok(eq['a'].get(S,params={'au':'2027-01-01'}))['elements'][0]['courante_id'] is None
    n=version(eq,v,contenu(date_debut=date.today().isoformat()));assert approuver(eq,n).status_code==409
    ok(eq['b'].post(f'{S}/versions/{n["id"]}/rejeter',json=dec()));avant=empreintes_tables(application['engine']);installer(application)
    assert empreintes_tables(application['engine'])==avant
