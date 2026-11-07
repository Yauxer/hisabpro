from pathlib import Path
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import json,pytest,httpx
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_paie919_rattachement_isole import (
    application as application123,application122,application121,application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite)
import test_paie909_bases_isole as fiscale
from test_paie921_mensuel_unitaire import demande
from test_paie919_rattachement_unitaire import declaration
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];M='/api/employes/personnel/fiscalite/mensuel'
def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/124_paie_controles_mensuels.sql').read_text(encoding='utf8'))
    finally:raw.close()

@pytest.fixture(scope='module')
def application(application123):
    a=application123;avant=empreintes_tables(a['engine']);installer(a);installer(a);apres=empreintes_tables(a['engine']);assert all(apres[t]==h for t,h in avant.items());yield a

def preparation(eq,meta=None,periodicite='mensuelle'):
    with pytest.MonkeyPatch.context() as patch:
        ancien=fiscale.gain
        ancien_contenu=fiscale.contenu_rubrique
        patch.setattr(fiscale,'contenu_rubrique',lambda **kw:ancien_contenu(**{**kw,'periodicite':periodicite}))
        if meta is not None:patch.setattr(fiscale,'gain',lambda *a,**kw:ancien(*a,**kw,rattachement_revenus=meta))
        eid,rid,q,s,bs=fiscale.preparer(eq)
    p=fiscale.calcul_fiscal(eq,eid,s);return eid,rid,p

def test_921_chaine_source_rni_equivalence_et_inconnues(application,equipe):
    eq=equipe;eid,_,p=preparation(eq);avant=comptabilite(application,eq['sid']);r=ok(eq['a'].post(M,json=demande(p['id'],eid)),201);c=r['contenu']
    assert c['rni_arithmetique']=='6990.08' and c['ir_mensuel_arithmetique']=='497.0240' and c['source_preparation']['empreinte']==p['empreinte']
    assert c['retenue_a_operer'] is None and c['versement'] is None and c['net_a_payer'] is None and not c['paie_definitive_autorisee']
    assert ok(eq['a'].get(f'{M}/{r["id"]}'))['contenu']==c and eq['a'].get(M).headers['cache-control']=='no-store'
    for kw in [{'frais_professionnels_declares':None},{'personnes_charge':None},{'deductions_confirmees':False}]:
        a=ok(eq['a'].post(M,json=demande(p['id'],eid,**kw)),201)['contenu'];assert a['ir_mensuel_arithmetique'] is None and a['anomalies']
    assert comptabilite(application,eq['sid'])==avant
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant
    (R/'.codex-tests/paie921_chaine_preuve.json').write_text(json.dumps({'rni':c['rni_arithmetique'],'equivalence_ir':c['ir_mensuel_arithmetique'],'fractions_exactes':c['fractions_exactes'],'source':c['source_preparation'],'aucune_retenue_a_operer':c['retenue_a_operer'] is None,'aucune_base_reelle':True},ensure_ascii=False,indent=2),encoding='utf8')

def test_921_rappel_documente_non_taxe_automatiquement(equipe):
    eq=equipe;eid,_,p=preparation(eq,meta=declaration());r=ok(eq['a'].post(M,json=demande(p['id'],eid)),201)['contenu']
    assert r['rni_arithmetique'] is None and any(a['code']=='RATTACHEMENT_SPECIFIQUE' for a in r['anomalies'])
    assert r['variables_documentaires'][0]['rattachement_revenus']['reference_debut']=='2025-01-01' and 'PRIME-ANNUELLE-FICTIVE919' not in json.dumps(r)

def test_921_prime_ponctuelle_sans_rattachement_reste_a_qualifier(equipe):
    eq=equipe;eid,_,p=preparation(eq,periodicite='ponctuelle');r=ok(eq['a'].post(M,json=demande(p['id'],eid)),201)['contenu']
    assert r['rni_arithmetique'] is None and any(a['code']=='RATTACHEMENT_SPECIFIQUE' for a in r['anomalies'])

def test_921_date_versement_source_autre_millesime_reste_visible(equipe):
    eq=equipe;meta=declaration(reference_debut=None,reference_fin=None,reference_justification=None,versement_date='2025-12-05')
    eid,_,p=preparation(eq,meta=meta);r=ok(eq['a'].post(M,json=demande(p['id'],eid)),201)['contenu']
    assert r['rni_arithmetique'] is None and r['declaration']['date_versement_declaree'] is None and any(a['code']=='VERSEMENT_SOURCE_AUTRE_ANNEE' for a in r['anomalies'])

def test_921_sources_changees_reprise_et_historique(equipe):
    eq=equipe;eid,rid,p=preparation(eq);d=demande(p['id'],eid);r=ok(eq['a'].post(M,json=d),201)
    from test_paie891_variables_isole import rubrique
    extra=rubrique(eq,'EXTRA_MENSUEL_FICTIF921',periodicite='ponctuelle')
    fiscale.gain(eq,eid,extra,montant='100.00',source_reference='APRES-CONTROLE-FICTIF921')
    assert eq['a'].post(M,json=demande(p['id'],eid)).status_code==409
    assert ok(eq['a'].get(f'{M}/{r["id"]}'))['contenu']==r['contenu'] and ok(eq['a'].post(M,json=d),201)['reutilise']

def test_921_concurrence_cle_et_montants_non_forcables(application,equipe):
    eq=equipe;eid,_,p=preparation(eq);d=demande(p['id'],eid)
    def calcul(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=40) as c:return ok(c.post(M,json=d),201)
    with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(calcul,range(2)))
    assert a['id']==b['id'] and a['reutilise']!=b['reutilise']
    assert eq['a'].post(M,json={**d,'frais_professionnels_declares':'1.00'}).status_code==409
    for kw in [{'frais_professionnels_declares':'NaN'},{'frais_professionnels_declares':True},{'taux':'20'},{'rni':'1.00'}]:
        n=eq['a'].post(M,json=demande(p['id'],eid,**kw));assert n.status_code==422 and all('input' not in e for e in n.json()['detail'])

def test_921_societes_profil_source_et_immutabilite(application,equipe):
    eq=equipe;eid,_,p=preparation(eq);r=ok(eq['a'].post(M,json=demande(p['id'],eid)),201);assert eq['l'].get(M).status_code==403
    with closing(client(application)[0]) as autre:
        u=ok(autre.get('/api/auth/me'))
        for cap in CAPS:grant(autre,u['id'],cap)
        activer(autre);assert autre.get(f'{M}/{r["id"]}').status_code==404 and autre.post(M,json=demande(p['id'],eid)).status_code==404
    role,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(role):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert role.get(M).status_code==200 and role.post(M,json=demande(p['id'],eid)).status_code==201 and role.get('/api/factures').status_code==403
    for engine in [application['engine'],application['personnel_runtime']]:
        for commande in ['DELETE FROM paie_controles_mensuels','TRUNCATE paie_controles_mensuels','UPDATE paie_controles_mensuels SET motif=motif']:
            with pytest.raises(DBAPIError) as er:
                with engine.begin() as db:db.execute(text(commande))
            assert er.value.orig.pgcode in {'23514','42501'}
        falsifie={**r['contenu'],'source_preparation':{**r['contenu']['source_preparation'],'empreinte':'a'*64}}
        with pytest.raises(DBAPIError,match='Provenance du contrôle mensuel incohérente') as er:
            with engine.begin() as db:db.execute(text('INSERT INTO paie_controles_mensuels(societe_id,employe_id,preparation_id,periode,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:e,:p,\'2026-11-01\',:k,:h,CAST(:c AS jsonb),:h,:u,\'FICTIF921\')'),{'s':eq['sid'],'e':eid,'p':p['id'],'k':str(uuid4()),'h':'a'*64,'c':json.dumps(falsifie),'u':eq['uid']})
        assert er.value.orig.pgcode=='23514'

def test_921_migration_absente_preserve_controles_annuels(application,equipe):
    a=application;c=a['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    try:
        with a['engine'].begin() as db:db.execute(text('ALTER TABLE paie_controles_mensuels RENAME TO paie_controles_mensuels_test921'))
        assert equipe['a'].get(M).status_code==503 and equipe['a'].get('/api/employes/personnel/fiscalite').status_code==200
    finally:
        with a['engine'].begin() as db:db.execute(text('ALTER TABLE paie_controles_mensuels_test921 RENAME TO paie_controles_mensuels'))
