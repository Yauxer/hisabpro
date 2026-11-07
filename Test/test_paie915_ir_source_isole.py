from pathlib import Path
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import json,pytest,httpx
from sqlalchemy import text
from test_paie913_frais_annuels_isole import (
    application as application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser,annee_prete,mois_unique,gain,demande as frais_demande,F)
from test_paie915_ir_source_unitaire import demande
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];I='/api/employes/personnel/fiscalite';S=I+'/depuis-frais-annuels'


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/122_paie_ir_sources_annuelles.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application121):
    a=application121;avant=empreintes_tables(a['engine']);installer(a);installer(a);apres=empreintes_tables(a['engine'])
    assert all(apres[t]==h for t,h in avant.items());yield a


def source_annuelle(eq):
    eid,rid,ps=annee_prete(eq);source=ok(eq['a'].post(F,json=frais_demande(eid,ps)),201)
    return eid,rid,source


def test_915_chaine_douze_mois_rni_arrondi_ir_et_famille(application,equipe):
    eq=equipe;eid,rid,source=source_annuelle(eq);avant=comptabilite(application,eq['sid']);d=demande(source['id']);r=ok(eq['a'].post(S,json=d),201);c=r['contenu']
    assert c['source_frais_annuels']['rni_avant_arrondis']=='83881.0200'
    assert c['source_frais_annuels']['base_annuelle_utilisee']=='83890.00'
    assert c['ir_avant_reduction']=='7167.0000' and c['reduction_appliquee']=='1200.0000' and c['ir_annuel_arithmetique']=='5967.0000'
    assert c['net_a_payer'] is None and c['retenue_mensuelle'] is None and c['ir_a_declarer'] is None
    assert ok(eq['a'].get(f'{I}/{r["id"]}'))['contenu']==c
    assert any(x.get('source_frais_id')==str(source['id']) for x in ok(eq['a'].get(I))['elements'])
    sans=ok(eq['a'].post(S,json=demande(source['id'],personnes_charge=None)),201)['contenu'];assert sans['ir_annuel_arithmetique'] is None and sans['ir_avant_reduction']=='7167.0000'
    non_confirme=ok(eq['a'].post(S,json=demande(source['id'],source_annuelle_confirmee=False)),201)['contenu'];assert non_confirme['ir_annuel_arithmetique'] is None
    assert comptabilite(application,eq['sid'])==avant
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant
    (R/'.codex-tests/paie915_chaine_preuve.json').write_text(json.dumps({'rni_source':c['source_frais_annuels'],'ir_avant_reduction':c['ir_avant_reduction'],'ir_annuel_arithmetique':c['ir_annuel_arithmetique'],'mois_reellement_prepares':12,'comptabilite_inchangee':True,'aucune_base_reelle':True},ensure_ascii=False,indent=2),encoding='utf8')


def test_915_source_incomplete_obsolete_et_snapshot_preserve(equipe):
    eq=equipe;eid,rid,ps=annee_prete(eq);part=ok(eq['a'].post(F,json=frais_demande(eid,[ps[0]])),201)
    assert eq['a'].post(S,json=demande(part['id'])).status_code==409
    source=ok(eq['a'].post(F,json=frais_demande(eid,ps)),201);d=demande(source['id']);r=ok(eq['a'].post(S,json=d),201)
    gain(eq,eid,rid,montant='100.00',source_reference='SOURCE-CHANGE-FICTIF915')
    assert eq['a'].post(S,json=demande(source['id'])).status_code==409
    assert ok(eq['a'].get(f'{I}/{r["id"]}'))['contenu']==r['contenu']
    reprise=ok(eq['a'].post(S,json=d),201);assert reprise['id']==r['id'] and reprise['reutilise']


def test_915_concurrence_et_cle_manuelle_distincte(application,equipe):
    eq=equipe;_,_,source=source_annuelle(eq);d=demande(source['id'])
    def calcul(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=40) as c:return ok(c.post(S,json=d),201)
    with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(calcul,range(2)))
    assert a['id']==b['id'] and a['reutilise']!=b['reutilise']
    assert eq['a'].post(S,json={**d,'personnes_charge':1}).status_code==409
    from test_paie901_ir_annuel_unitaire import demande as manuel
    assert eq['a'].post(I,json=manuel(cle_idempotence=d['cle_idempotence'])).status_code==409


def test_915_societes_profil_et_garde_native(application,equipe):
    eq=equipe;_,_,source=source_annuelle(eq);r=ok(eq['a'].post(S,json=demande(source['id'])),201)
    assert eq['l'].post(S,json=demande(source['id'])).status_code==403
    with closing(client(application)[0]) as autre:
        u=ok(autre.get('/api/auth/me'))
        for cap in CAPS:grant(autre,u['id'],cap)
        activer(autre);assert autre.get(f'{I}/{r["id"]}').status_code==404 and autre.post(S,json=demande(source['id'])).status_code==404
    role,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(role):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert role.post(S,json=demande(source['id'])).status_code==201 and role.get('/api/factures').status_code==403
    for moteur in [application['engine'],application['personnel_runtime']]:
        for sql in ['DELETE FROM paie_ir_sources_annuelles','TRUNCATE paie_ir_sources_annuelles','UPDATE paie_ir_sources_annuelles SET auteur_id=auteur_id']:
            refuser(application,sql,{},engine=moteur)
        refuser(application,'INSERT INTO paie_ir_sources_annuelles(ir_id,societe_id,frais_annuels_id,auteur_id) VALUES(:i,:s,:f,:u)',{'i':r['id'],'s':eq['sid'],'f':source['id']+100000,'u':eq['uid']},engine=moteur)


def test_915_aucun_rni_ni_taux_falsifiable(equipe):
    for kw in [{'revenu_net_imposable_annuel':'NaN'},{'taux':0},{'frais_annuels_id':True},{'annee':2025}]:
        r=equipe['a'].post(S,json=demande(**kw));assert r.status_code==422 and all('input' not in x for x in r.json()['detail'])


def test_915_migration_absente_preserve_ir_manuel(application,equipe):
    a=application;c=a['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);avant=empreintes_tables(a['engine'])
    try:
        with a['engine'].begin() as db:db.execute(text('ALTER TABLE paie_ir_sources_annuelles RENAME TO paie_ir_sources_annuelles_test915'))
        assert equipe['a'].post(S,json=demande()).status_code==503
        assert equipe['a'].get(I).status_code==200
    finally:
        with a['engine'].begin() as db:db.execute(text('ALTER TABLE paie_ir_sources_annuelles_test915 RENAME TO paie_ir_sources_annuelles'))
    apres=empreintes_tables(a['engine']);assert all(apres[t]==h for t,h in avant.items() if t!='audit_actions')
    assert apres['audit_actions']['nombre']>avant['audit_actions']['nombre'] # Le GET authentifié reste audité.
