from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import pytest,httpx
from sqlalchemy import text
from test_paie891_variables_isole import (
    application as application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,rubrique,envoyer,submit,choix,V,E,dec,contenu_rubrique,creation,W,decision,proposition,soumettre,approuver,refuser)
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];T='/api/employes/personnel/traitement'

@pytest.fixture(scope='module')
def application(application114):
    app=application114;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/115_paie_campagnes_brut.sql').read_text(encoding='utf8'))
        finally:raw.close()
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items())
    yield app

def salarie(eq,m='P893',entree='2025-12-15',periodicite='mensuelle'):
    e=ok(eq['a'].post(W,json=creation(m,nom='Salariée FICTIVE893',date_embauche=entree)),201);eid=e['employe_id'];soumettre(eq['a'],e['demande']['id'],0);approuver(eq,e['demande']['id'],0)
    c=proposition(eq,eid,1,'CONTRAT',{'type_contrat':'CDI','date_effet':'2026-01-01','date_debut':'2026-01-01','reference_justificatif':'CONTRAT-FICTIF893'})
    soumettre(eq['a'],c['id'],1);approuver(eq,c['id'],1);cid=ok(eq['a'].get(f'{W}/{eid}?au=2026-11-01'))['contrat']['id']
    r=proposition(eq,eid,2,'REMUNERATION',{'contrat_version_id':cid,'montant':'9000.10','date_effet':'2026-01-01','periodicite':periodicite,'reference_justificatif':'REM-FICTIVE893'})
    soumettre(eq['a'],r['id'],2);approuver(eq,r['id'],2);return eid,cid

def demande(ids,**kw):return {'periode':'2026-11-01','employe_ids':ids,'mois_complets_confirmes':True,'cle_idempotence':str(uuid4()),'motif':'Simulation entièrement fictive893',**kw}
def simuler(eq,ids,**kw):return ok(eq['a'].post(T+'/simulations',json=demande(ids,**kw)),201)
def codes(q):return {a['code'] for e in q['contenu']['employes'] for a in e['anomalies']}
def gain(eq,eid,rid,**kw):
    v=envoyer(eq,eid,rid,**kw);submit(eq,v['id']);ok(eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()));return v

def test_893_brut_exact_et_inconnues_sociales_sans_ecriture(application,equipe):
    eq=equipe;eid,_=salarie(eq);r=rubrique(eq);gain(eq,eid,r)
    r2=rubrique(eq,'QUANT_FICTIVE893',formule='QUANTITE_TAUX',periodicite='ponctuelle');gain(eq,eid,r2,mode='QUANTITE_TAUX',montant=None,quantite='3',taux='0.335',source_reference='QUANT-FICTIF893')
    avant=comptabilite(application,eq['sid']);q=simuler(eq,[eid]);c=q['contenu']
    assert c['totaux']['base']=='9000.10' and c['totaux']['gains']=='801.02' and c['totaux']['brut']=='9801.12'
    assert c['complet_pour_brut'] and not c['paie_definitive_autorisee']
    assert all(c['totaux'][k] is None for k in ['cotisations_salariales','cotisations_patronales','ir','net_a_payer','cout_employeur'])
    d=ok(eq['a'].get(f'{T}/simulations/{q["id"]}'));assert d['empreinte']==q['empreinte'] and d['contenu']==c
    assert comptabilite(application,eq['sid'])==avant and eq['a'].get(T).headers['cache-control']=='no-store'
    for sql in ["UPDATE paie_simulations_brut SET contenu='{}'::jsonb WHERE id=:i",'DELETE FROM paie_simulations_brut WHERE id=:i','TRUNCATE paie_simulations_brut']:
        refuser(application,sql,{'i':q['id']});refuser(application,sql,{'i':q['id']},engine=application['personnel_runtime'])

def test_893_anomalie_individuelle_ne_devient_pas_zero_ou_total_complet(equipe):
    eq=equipe;e1,_=salarie(eq,'P1');e2,_=salarie(eq,'P2',entree=None)
    q=simuler(eq,[e1,e2]);c=q['contenu'];assert not c['complet_pour_brut'] and c['totaux']['brut'] is None and 'ENTREE_INCONNUE' in codes(q)
    assert c['employes'][0]['brut']=='9000.10' and c['employes'][1]['brut'] is None

def test_893_variables_en_attente_recalcul_et_snapshot_stable(equipe):
    eq=equipe;eid,_=salarie(eq);rid=rubrique(eq);v=envoyer(eq,eid,rid)
    body=demande([eid]);a=ok(eq['a'].post(T+'/simulations',json=body),201);assert 'VARIABLES_EN_ATTENTE' in codes(a)
    submit(eq,v['id']);ok(eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()))
    replay=ok(eq['a'].post(T+'/simulations',json=body),201);assert replay['id']==a['id'] and replay['reutilise'] and replay['contenu']==a['contenu']
    b=simuler(eq,[eid]);assert b['numero']==2 and b['campagne_id']==a['campagne_id'] and b['contenu']['totaux']['brut']=='9800.11'
    assert ok(eq['a'].get(f'{T}/simulations/{a["id"]}'))['contenu']==a['contenu']
    hist=ok(eq['a'].get(f'{T}/campagnes/{a["campagne_id"]}/historique'));assert [x['numero'] for x in hist]==[2,1]
    assert eq['a'].post(T+'/simulations',json=dict(body,motif='Autre demande fictive')).status_code==409

def test_893_modifications_intramensuelles_et_retenues_non_supposees(equipe):
    eq=equipe;eid,cid=salarie(eq)
    r=proposition(eq,eid,3,'REMUNERATION',{'contrat_version_id':cid,'montant':'10000.00','date_effet':'2026-11-15','periodicite':'mensuelle','reference_justificatif':'MODIF-FICTIVE893'})
    soumettre(eq['a'],r['id'],3);approuver(eq,r['id'],3)
    q=simuler(eq,[eid]);assert 'SALAIRE_CHANGE' in codes(q) and q['contenu']['totaux']['brut'] is None
    e2,_=salarie(eq,'RET893');rid=rubrique(eq,nature='RETENUE');gain(eq,e2,rid,montant='100.00')
    q=simuler(eq,[e2]);assert 'IMPACT_A_QUALIFIER' in codes(q) and q['contenu']['totaux']['brut'] is None

def test_893_source_rubrique_future_ne_reecrit_pas_variable(equipe):
    eq=equipe;eid,_=salarie(eq);rid=rubrique(eq);v=gain(eq,eid,rid);ancien=ok(eq['a'].get(f'{V}/{v["id"]}'))
    version=ok(eq['a'].post(f'{E}/{rid}/versions',json={'version_attendue':1,'contenu':contenu_rubrique(date_debut='2026-11-10'),'motif':'Version future fictive893'}),201)
    ok(eq['b'].post(f'{E}/versions/{version["id"]}/approuver',json=dec()))
    q=simuler(eq,[eid]);assert 'SOURCE_VARIABLE_CHANGEE' in codes(q) and q['contenu']['totaux']['brut'] is None
    assert ok(eq['a'].get(f'{V}/{v["id"]}'))==ancien

def test_893_horaire_et_entree_intramensuelle_sont_explicites(equipe):
    eq=equipe;eid,_=salarie(eq,periodicite='horaire');q=simuler(eq,[eid]);assert 'BASE_NON_MENSUELLE' in codes(q)
    eid,_=salarie(eq,'ENT893',entree='2026-11-15');q=simuler(eq,[eid]);assert 'MOIS_INCOMPLET' in codes(q) and q['contenu']['totaux']['brut'] is None

def test_893_concurrence_meme_cle_une_seule_simulation(application,equipe):
    eq=equipe;eid,_=salarie(eq);body=demande([eid])
    def poster(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=30) as c:
            r=c.post(T+'/simulations',json=body);assert r.status_code==201,r.text;return r.json()
    with ThreadPoolExecutor(max_workers=2) as pool:q=list(pool.map(poster,range(2)))
    assert q[0]['id']==q[1]['id'] and sorted(x['reutilise'] for x in q)==[False,True]
    assert len(ok(eq['a'].get(f'{T}/campagnes/{q[0]["campagne_id"]}/historique')))==1

def test_893_societes_droits_et_rejeu_migration(application,equipe):
    eq=equipe;eid,_=salarie(eq);q=simuler(eq,[eid]);assert eq['l'].get(T).status_code==403
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre)
        assert autre.get(f'{T}/simulations/{q["id"]}').status_code==404 and autre.post(T+'/simulations',json=demande([eid])).status_code==404
        assert ok(autre.get(T))['total']==0
    avant=empreintes_tables(application['engine']);raw=application['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/115_paie_campagnes_brut.sql').read_text(encoding='utf8'))
    finally:raw.close()
    assert empreintes_tables(application['engine'])==avant
