from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4
import copy
import pytest,httpx
from sqlalchemy import text
from test_paie897_social_isole import (
    application as application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser,creer,approuver,version,contenu,S)
from test_paie893_campagnes_isole import salarie,rubrique,gain,simuler as brut,envoyer,submit,choix,V,T
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];C=S+'/simulations'


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/117_paie_simulations_sociales.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application116):
    app=application116;avant=empreintes_tables(app['engine']);installer(app);installer(app);apres=empreintes_tables(app['engine'])
    assert all(apres[t]==h for t,h in avant.items());yield app


def preparer(eq):
    eid,_=salarie(eq,m='P899');rid=rubrique(eq);gain(eq,eid,rid);q=brut(eq,[eid])
    b1=creer(eq,'B1_FICTIF','REGIME_SOC899',taux_salarial='1',taux_patronal='2',plafond='6000.00',composants=['GARANTIE_B1']);ok(approuver(eq,b1))
    b2=creer(eq,'B2_FICTIF','REGIME_SOC899',assiette='AMO',taux_salarial='3',taux_patronal='4',plafond_mode='SANS',plafond=None,composants=['GARANTIE_B2']);ok(approuver(eq,b2))
    return eid,rid,q,b1,b2


def demande(eid,q,**kw):return {'brut_id':q['id'],'regime':'REGIME_SOC899','declarations':[{'employe_id':eid,'base_cnss':'9000.10','base_amo':'9000.10','conditions_confirmees':True,'reference_controle':'CTRL-FICTIF899'}],'mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'Simulation FICTIVE899',**kw}
def calculer(eq,eid,q,**kw):return ok(eq['a'].post(C,json=demande(eid,q,**kw)),201)


def test_899_social_connecte_exact_sources_et_absence_ecriture(application,equipe):
    eq=equipe;eid,rid,q,b1,b2=preparer(eq);avant=comptabilite(application,eq['sid']);r=calculer(eq,eid,q);c=r['contenu'];e=c['employes'][0]
    assert c['complet_pour_social'] and c['totaux']['cotisations_salariales']=='354.00' and c['totaux']['cotisations_patronales']=='512.00'
    assert e['assiettes']['CNSS']['montant']=='9500.11' and e['assiettes']['AMO']['montant']=='9800.11'
    assert [x['version_id'] for x in e['branches']]==[b1['id'],b2['id']]
    assert c['brut_empreinte']==q['empreinte'] and c['totaux']['ir'] is None and c['totaux']['net_a_payer'] is None and not c['paie_definitive_autorisee']
    assert c['statut_reglementaire']=='NON_VALIDE_JURIDIQUEMENT' and comptabilite(application,eq['sid'])==avant
    assert ok(eq['a'].get(f'{C}/{r["id"]}'))['contenu']==c and eq['a'].get(C).headers['cache-control']=='no-store'
    assert ok(eq['a'].get(C+'/options',params={'brut_id':q['id']}))['regimes']==['REGIME_SOC899']


def test_899_sources_changees_brut_ancien_intact_et_nouveau_recalcul(equipe):
    eq=equipe;eid,rid,q,_,_=preparer(eq);ancien=calculer(eq,eid,q)
    extra=rubrique(eq,'EXTRA_FICTIVE899',periodicite='ponctuelle');variable=envoyer(eq,eid,extra,montant='100.00',source_reference='EXTRA-FICTIF899')
    r=calculer(eq,eid,q);assert not r['contenu']['complet_pour_social']
    assert 'SOURCE_BRUT_CHANGEE' in {a['code'] for a in r['contenu']['employes'][0]['anomalies']}
    submit(eq,variable['id']);ok(eq['b'].post(f'{V}/{variable["id"]}/approuver',json=choix()))
    nouveau=brut(eq,[eid]);s=calculer(eq,eid,nouveau)
    assert s['contenu']['totaux']['cotisations_salariales']=='357.00' and s['contenu']['totaux']['cotisations_patronales']=='516.00'
    assert ok(eq['a'].get(f'{C}/{ancien["id"]}'))['contenu']==ancien['contenu']
    assert ok(eq['a'].get(f'{T}/simulations/{q["id"]}'))['contenu']==q['contenu']


@pytest.mark.parametrize('mutation',[{'base_cnss':None},{'conditions_confirmees':False},{'reference_controle':None},{'base_cnss':'9800.11'}])
def test_899_faits_manquants_ou_base_globale_pas_de_zero(equipe,mutation):
    eq=equipe;eid,rid,q,_,_=preparer(eq);d=demande(eid,q);d['declarations'][0].update(mutation)
    r=ok(eq['a'].post(C,json=d),201)['contenu'];assert r['totaux']['cotisations_salariales'] is None and not r['complet_pour_social']
    if mutation=={'base_cnss':None}:
        e=r['employes'][0];assert e['branches'][1]['salarial']=='294.00' and r['totaux']['cotisations_patronales'] is None


def test_899_regime_vide_branche_inconnue_et_periode_changee(equipe):
    eq=equipe;eid,rid,q,b1,b2=preparer(eq)
    r=calculer(eq,eid,q,regime='INCONNU')['contenu'];assert r['totaux']['cotisations_salariales'] is None
    autre=creer(eq,'A_QUALIFIER','REGIME_SOC899',applicabilite='A_VERIFIER',composants=['AUTRE_FICTIF']);ok(approuver(eq,autre))
    r=calculer(eq,eid,q)['contenu'];assert r['totaux']['cotisations_salariales'] is None
    assert r['employes'][0]['branches'][0]['salarial']=='60.00' #partie connue visible, total indisponible
    n=version(eq,b1,contenu(date_debut='2026-11-15',taux_salarial='1',taux_patronal='2',plafond='6000.00',composants=['GARANTIE_B1']));ok(approuver(eq,n))
    r=calculer(eq,eid,q)['contenu'];assert r['branches_sources'][0]['anomalies'][0]['code']=='BRANCHE_CHANGE_DANS_MOIS'


def test_899_idempotence_concurrence_et_selection_exacte(application,equipe):
    eq=equipe;eid,rid,q,_,_=preparer(eq);body=demande(eid,q)
    def calcul(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=30) as c:return ok(c.post(C,json=body),201)
    with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(calcul,range(2)))
    assert a['id']==b['id'] and a['reutilise']!=b['reutilise']
    body['motif']='Autre demande FICTIVE';assert eq['a'].post(C,json=body).status_code==409
    d=demande(eid,q);d['declarations'][0]['employe_id']=eid+999;assert eq['a'].post(C,json=d).status_code==400


def test_899_isolation_droits_profil_et_immutabilite(application,equipe):
    eq=equipe;eid,rid,q,_,_=preparer(eq);r=calculer(eq,eid,q)
    assert eq['l'].get(C).status_code==403
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre)
        assert autre.get(f'{C}/{r["id"]}').status_code==404 and autre.get(C+'/options',params={'brut_id':q['id']}).status_code==404
        assert autre.post(C,json=demande(eid,q)).status_code==404
    p,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(p):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert p.get(C).status_code==200 and p.get('/api/factures').status_code==403
        assert p.get(f'{C}/{r["id"]}').status_code==200
    for sql in ["UPDATE paie_simulations_sociales SET contenu='{}' WHERE id=:i",'DELETE FROM paie_simulations_sociales WHERE id=:i','TRUNCATE paie_simulations_sociales']:
        for engine in [application['engine'],application['personnel_runtime']]:refuser(application,sql,{'i':r['id']},engine=engine)
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant


def test_899_changement_taux_futur_preserve_anciennes_simulations(equipe):
    eq=equipe;eid,rid,q,b1,b2=preparer(eq);r=calculer(eq,eid,q)
    n=version(eq,b1,contenu(date_debut='2027-01-01',taux_salarial='2',taux_patronal='3',plafond='6000.00',composants=['GARANTIE_B1']));ok(approuver(eq,n))
    assert calculer(eq,eid,q)['contenu']['totaux']['cotisations_salariales']=='354.00'
    assert ok(eq['a'].get(f'{C}/{r["id"]}'))['contenu']==r['contenu']


def test_899_rubrique_non_qualifiee_bloque_son_assiette_seulement(equipe):
    eq=equipe;eid,rid,q,_,_=preparer(eq)
    extra=rubrique(eq,'INCONNUE_FICTIVE899',periodicite='ponctuelle',regles={k:{'traitement':'A_VERIFIER','statut_reglementaire':'A_VERIFIER','unite':'operation','conditions':'Hypothèse fictive inconnue'} for k in ['IR','CNSS','AMO']})
    gain(eq,eid,extra,montant='1.00',source_reference='INCONNUE-FICTIVE899');q2=brut(eq,[eid]);r=calculer(eq,eid,q2)['contenu']
    assert r['totaux']['cotisations_salariales'] is None and r['employes'][0]['assiettes']['CNSS']['montant'] is None


def test_899_plafond_exoneration_mensuelle_sur_toutes_variables(equipe):
    eq=equipe;eid,rid,q,_,_=preparer(eq)
    def regle(t):return {'traitement':t,'statut_reglementaire':'A_VERIFIER','unite':'mensuel','conditions':'Hypothèse FICTIVE mensuelle899',**({'plafond':'300.00'} if t=='PLAFOND_MONTANT' else {})}
    r=rubrique(eq,'CUMUL_FICTIF899',periodicite='ponctuelle',regles={'IR':regle('A_VERIFIER'),'CNSS':regle('PLAFOND_MONTANT'),'AMO':regle('SOUMIS')})
    for i in range(2):gain(eq,eid,r,montant='400.00',source_reference='CUMUL-FICTIF899-'+str(i))
    q2=brut(eq,[eid]);c=calculer(eq,eid,q2)['contenu']
    assert c['employes'][0]['assiettes']['CNSS']['montant']=='10000.11'
    assert c['employes'][0]['assiettes']['AMO']['montant']=='10600.11'
    assert c['totaux']['cotisations_salariales']=='378.00' and c['totaux']['cotisations_patronales']=='544.00'


def test_899_forfait_et_non_applicabilite_documentes(equipe):
    eq=equipe;eid,rid,q,_,_=preparer(eq)
    v=creer(eq,'FORFAIT_FICTIF899','REGIME_SOC899',calcul_mode='FORFAIT',assiette='A_QUALIFIER',plafond_mode='SANS',plafond=None,taux_salarial=None,taux_patronal=None,forfait_salarial='25.00',forfait_patronal='50.00',composants=['FORFAIT_FICTIF']);ok(approuver(eq,v))
    v=creer(eq,'NON_APPLICABLE_FICTIF899','REGIME_SOC899',applicabilite='NON_APPLICABLE',calcul_mode='A_QUALIFIER',assiette='A_QUALIFIER',plafond_mode='A_VERIFIER',plafond=None,taux_salarial=None,taux_patronal=None,composants=[]);ok(approuver(eq,v))
    c=calculer(eq,eid,q)['contenu'];assert c['totaux']['cotisations_salariales']=='379.00' and c['totaux']['cotisations_patronales']=='562.00'
    assert c['employes'][0]['branches'][-1]['salarial']=='0.00' and c['employes'][0]['branches'][-1]['assiette_retenue'] is None
