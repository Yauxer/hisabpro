from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest,httpx
from sqlalchemy import text
from test_paie899_social_isole import (
    application as application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser)
from test_paie901_ir_annuel_unitaire import demande
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];F='/api/employes/personnel/fiscalite'


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/118_paie_controles_ir_annuels.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application117):
    app=application117;avant=empreintes_tables(app['engine']);installer(app);installer(app);apres=empreintes_tables(app['engine'])
    assert all(apres[t]==h for t,h in avant.items());yield app


def test_901_ir_annuel_exact_reference_historique_et_comptabilite(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid']);a=ok(eq['a'].post(F,json=demande()),201)
    assert a['contenu']['ir_avant_reduction']=='46600.0000' and a['contenu']['ir_annuel_arithmetique']=='45400.0000'
    assert a['contenu']['ir_a_declarer'] is None and not a['contenu']['paie_definitive_autorisee']
    b=ok(eq['a'].post(F,json=demande(personnes_charge=6)),201);assert b['contenu']['ir_annuel_arithmetique']=='43000.0000'
    assert ok(eq['a'].get(f'{F}/{a["id"]}'))['contenu']==a['contenu']
    assert ok(eq['a'].get(F))['elements'][0]['id']==b['id'] and eq['a'].get(F).headers['cache-control']=='no-store'
    ref=ok(eq['a'].get(F+'/referentiel'));assert ref['empreinte']==a['contenu']['referentiel_sha256']
    assert comptabilite(application,eq['sid'])==avant


@pytest.mark.parametrize('kw',[{'personnes_charge':None},{'revenu_net_imposable_annuel':None},{'cadre_general_confirme':False}])
def test_901_inconnues_visibles_en_http(equipe,kw):
    r=ok(equipe['a'].post(F,json=demande(**kw)),201)['contenu'];assert r['ir_annuel_arithmetique'] is None and r['anomalies']


@pytest.mark.parametrize('kw',[{'annee':2025},{'revenu_net_imposable_annuel':'NaN'},{'personnes_charge':True}])
def test_901_refus_api_sans_reecho_sensible(equipe,kw):
    r=equipe['a'].post(F,json=demande(**kw));assert r.status_code==422 and 'input' not in r.text


def test_901_idempotence_concurrente(application,equipe):
    eq=equipe;d=demande()
    def calcul(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=30) as c:return ok(c.post(F,json=d),201)
    with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(calcul,range(2)))
    assert a['id']==b['id'] and a['reutilise']!=b['reutilise'];d['personnes_charge']=3
    assert eq['a'].post(F,json=d).status_code==409


def test_901_isolation_profil_habilitations_immutabilite_et_rejeu(application,equipe):
    eq=equipe;r=ok(eq['a'].post(F,json=demande()),201);assert eq['l'].get(F).status_code==403
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre);assert autre.get(f'{F}/{r["id"]}').status_code==404
    p,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(p):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert p.get(F).status_code==200 and p.get(F+'/referentiel').status_code==200 and p.get('/api/factures').status_code==403
        assert p.post(F,json=demande()).status_code==201
    for sql in ["UPDATE paie_controles_ir_annuels SET contenu='{}' WHERE id=:i",'DELETE FROM paie_controles_ir_annuels WHERE id=:i','TRUNCATE paie_controles_ir_annuels']:
        for engine in [application['engine'],application['personnel_runtime']]:refuser(application,sql,{'i':r['id']},engine=engine)
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant
