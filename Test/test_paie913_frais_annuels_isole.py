from pathlib import Path
from contextlib import closing
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import json,pytest,httpx
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_paie909_bases_isole import (
    application as application120,application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser,preparer,calcul_fiscal,gain,brut)
from test_paie899_social_isole import calculer as social
from test_paie913_frais_annuels_unitaire import demande as entree
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];F='/api/employes/personnel/fiscalite/frais-annuels'


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/121_paie_frais_annuels.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application120):
    a=application120;avant=empreintes_tables(a['engine']);installer(a);installer(a);apres=empreintes_tables(a['engine'])
    assert all(apres[t]==h for t,h in avant.items());yield a


def mois_unique(eq):
    eid,rid,q,s,bs=preparer(eq);p=calcul_fiscal(eq,eid,s)
    return eid,rid,q,s,p


def annee_prete(eq):
    eid,rid,q,s,p=mois_unique(eq);preparations=[p]
    for m in range(1,13):
        if m==11:continue
        gain(eq,eid,rid,periode=f'2026-{m:02d}-01',date_effet=f'2026-{m:02d}-15',source_reference=f'GAIN-ANNUEL-FICTIF913-{m:02d}')
        q=brut(eq,[eid],periode=f'2026-{m:02d}-01');s=social(eq,eid,q,regime='REGIME_FISC909');preparations.append(calcul_fiscal(eq,eid,s))
    return eid,rid,sorted(preparations,key=lambda x:x['contenu']['periode'])


def demande(eid,preparations,**kw):return entree(employe_id=eid,preparation_ids=[p['id'] for p in preparations],**kw)


def test_913_douze_mois_connectes_oracle_et_inconnues(application,equipe):
    eq=equipe;eid,rid,ps=annee_prete(eq);avant=comptabilite(application,eq['sid']);d=demande(eid,ps);r=ok(eq['a'].post(F,json=d),201);c=r['contenu']
    assert c['nombre_mois']==12 and c['complet_pour_rni_arithmetique']
    assert c['cumuls']['brut_imposable']=='111601.32' and c['cumuls']['base_frais_professionnels']=='108001.20'
    assert c['cumuls']['cotisations_salariales_deductibles']=='720.00' and c['frais_professionnels_annuels_arithmetiques']=='27000.3000'
    assert c['rni_annuel_arithmetique_avant_arrondis']=='83881.0200' and c['ir'] is None and c['net_a_payer'] is None
    assert [x['preparation_id'] for x in c['sources']]==[p['id'] for p in ps]
    for mutation in [{'autres_deductions_annuelles':None},{'cadre_frais_general_confirme':False},{'correspondance_revenus_annee_confirmee':False}]:
        n=ok(eq['a'].post(F,json=demande(eid,ps,**mutation)),201)['contenu'];assert n['rni_annuel_arithmetique_avant_arrondis'] is None and n['anomalies']
    assert ok(eq['a'].get(f'{F}/{r["id"]}'))['contenu']==c and eq['a'].get(F).headers['cache-control']=='no-store'
    assert comptabilite(application,eq['sid'])==avant
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant
    (R/'.codex-tests/paie913_annee_preuve.json').write_text(json.dumps({'mois_reellement_prepares':12,'ids':[p['id'] for p in ps],'cumuls':c['cumuls'],'frais':c['frais_professionnels_annuels_arithmetiques'],'rni':c['rni_annuel_arithmetique_avant_arrondis'],'aucune_base_reelle':True},ensure_ascii=False,indent=2),encoding='utf8')


def test_913_mois_partiel_et_versions_doubles_sans_extrapoler(equipe):
    eq=equipe;eid,_,q,s,p=mois_unique(eq);r=ok(eq['a'].post(F,json=demande(eid,[p])),201)['contenu']
    assert r['nombre_mois']==1 and r['cumuls']['brut_imposable']=='9300.11' and r['frais_professionnels_annuels_arithmetiques'] is None
    autre=calcul_fiscal(eq,eid,s)
    assert eq['a'].post(F,json=demande(eid,[p,autre])).status_code==400
    o=ok(eq['a'].get(F+'/options',params={'employe_id':eid}));assert len(o['preparations'])==2 and len(o['employes'])==1


def test_913_sources_modifiees_ancien_cumul_et_reprise_preserves(application,equipe):
    eq=equipe;eid,rid,q,s,p=mois_unique(eq);d=demande(eid,[p]);r=ok(eq['a'].post(F,json=d),201)
    gain(eq,eid,rid,montant='100.00',source_reference='EXTRA-ANNUEL-FICTIF913')
    assert eq['a'].post(F,json=demande(eid,[p])).status_code==409
    assert ok(eq['a'].get(f'{F}/{r["id"]}'))['contenu']==r['contenu']
    reprise=ok(eq['a'].post(F,json=d),201);assert reprise['reutilise'] and reprise['id']==r['id']


def test_913_concurrence_reprise_et_conflit(application,equipe):
    eq=equipe;eid,_,_,_,p=mois_unique(eq);d=demande(eid,[p])
    def calcul(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=30) as c:return ok(c.post(F,json=d),201)
    with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(calcul,range(2)))
    assert a['id']==b['id'] and a['reutilise']!=b['reutilise'];d['autres_deductions_annuelles']='1.00'
    assert eq['a'].post(F,json=d).status_code==409


def test_913_societes_profil_fk_et_immutabilite(application,equipe):
    eq=equipe;eid,_,_,s,p=mois_unique(eq);r=ok(eq['a'].post(F,json=demande(eid,[p])),201);assert eq['l'].get(F).status_code==403
    non_choisie=calcul_fiscal(eq,eid,s)
    for moteur in [application['engine'],application['personnel_runtime']]:
        with pytest.raises(DBAPIError,match='Source annuelle non prévue ou incohérente') as erreur:
            with moteur.begin() as db:db.execute(text("INSERT INTO paie_controle_frais_sources(controle_id,societe_id,preparation_id,periode,auteur_id) VALUES(:i,:s,:p,'2026-11-01',:u)"),{'i':r['id'],'s':eq['sid'],'p':non_choisie['id'],'u':eq['uid']})
        assert erreur.value.orig.pgcode=='23514'
    with closing(client(application)[0]) as autre:
        identite=ok(autre.get('/api/auth/me'));uid=identite['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre);assert autre.get(f'{F}/{r["id"]}').status_code==404 and autre.post(F,json=demande(eid,[p])).status_code==404
        sql="INSERT INTO paie_controles_frais_annuels(societe_id,employe_id,annee,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:e,2026,:k,:h,CAST(:c AS jsonb),:h,:u,'FICTIF913')"
        with pytest.raises(DBAPIError) as erreur:
            with application['engine'].begin() as db:db.execute(text(sql),{'s':identite['societe_id'],'e':eid,'k':str(uuid4()),'h':'a'*64,'c':json.dumps(r['contenu']),'u':uid})
        assert erreur.value.orig.pgcode=='23503'
    role,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(role):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert role.get(F).status_code==200 and role.get(F+'/options').status_code==200 and role.post(F,json=demande(eid,[p])).status_code==201
        assert role.get('/api/factures').status_code==403
    for table in ['paie_controles_frais_annuels','paie_controle_frais_sources']:
        for sql in [f'DELETE FROM {table}',f'TRUNCATE {table} CASCADE',f'UPDATE {table} SET auteur_id=auteur_id']:
            for moteur in [application['engine'],application['personnel_runtime']]:refuser(application,sql,{},engine=moteur)


@pytest.mark.parametrize('valeur',['NaN','Infinity',True])
def test_913_montants_http_invalides_sans_reecho(equipe,valeur):
    r=equipe['a'].post(F,json=entree(autres_deductions_annuelles=valeur));assert r.status_code==422 and 'input' not in r.text


def test_913_migration_absente_ne_casse_pas_controle_annuel_precedent(application,equipe):
    c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);avant=empreintes_tables(application['engine'])
    try:
        with application['engine'].begin() as db:db.execute(text('ALTER TABLE public.paie_controles_frais_annuels RENAME TO paie_controles_frais_annuels_test913'))
        r=equipe['a'].get(F);assert r.status_code==503 and '121' in r.text
        assert equipe['a'].get('/api/employes/personnel/fiscalite').status_code==200
    finally:
        with application['engine'].begin() as db:db.execute(text('ALTER TABLE public.paie_controles_frais_annuels_test913 RENAME TO paie_controles_frais_annuels'))
    assert empreintes_tables(application['engine'])==avant
