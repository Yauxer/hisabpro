from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest,httpx
from sqlalchemy import text
from test_paie889_catalogue_isole import (
    application as application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,creer as creer_rubrique,contenu as contenu_rubrique,dec,E,refuser)
from test_personnel_workflow877_isole import avec_salaire,actif,proposition,soumettre,approuver,creation,W,decision
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];V=E+'/variables'

@pytest.fixture(scope='module')
def application(application113):
    app=application113;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/114_paie_variables.sql').read_text(encoding='utf8'))
        finally:raw.close()
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items())
    yield app

def rubrique(eq,code='PRIME_FICTIVE891',**kw):
    r=creer_rubrique(eq,code,**kw);ok(eq['b'].post(f'{E}/versions/{r["id"]}/approuver',json=dec()));return r['rubrique_id']
def entree(eid,rid,**kw):
    return {'employe_id':eid,'rubrique_id':rid,'periode':'2026-11-01','date_effet':'2026-11-15','mode':'MONTANT','montant':'800.01',
      'source_reference':'VARIABLE-FICTIVE891','justificatifs':{'ATTESTATION_FICTIVE':'PIECE-FICTIVE891'},'motif':'Proposition entièrement fictive891',**kw}
def envoyer(eq,eid,rid,**kw):return ok(eq['a'].post(V,json=entree(eid,rid,**kw)),201)
def choix(**kw):return {'motif':'Décision fictive891','reference_controle':'CTRL-FICTIF891','independance_confirmee':True,'justificatifs_verifies':True,**kw}
def submit(eq,i):return ok(eq['a'].post(f'{V}/{i}/soumettre',json={'motif':'Soumission fictive891'}))

def test_891_variable_exacte_sources_approbation_et_absence_ecriture(application,equipe):
    eq=equipe;eid,cid=avec_salaire(eq);rid=rubrique(eq);avant=comptabilite(application,eq['sid'])
    var=envoyer(eq,eid,rid);i=var['id'];assert var['montant']=='800.01'
    d=ok(eq['a'].get(f'{V}/{i}'));assert d['instantane']['remuneration']['montant']=='9000.10' and d['statut']=='BROUILLON'
    assert eq['b'].post(f'{V}/{i}/soumettre',json={'motif':'Tentative fictive'}).status_code==403
    submit(eq,i)
    assert eq['a'].post(f'{V}/{i}/approuver',json=choix()).status_code==403
    assert eq['b'].post(f'{V}/{i}/approuver',json=choix(justificatifs_verifies=False)).status_code==400
    ok(eq['b'].post(f'{V}/{i}/approuver',json=choix()))
    d=ok(eq['a'].get(f'{V}/{i}'));assert d['statut']=='APPROUVE' and [x['statut'] for x in d['evenements']]==['BROUILLON','SOUMIS','APPROUVE']
    assert d['instantane']['contrat_id']==cid and d['justificatifs_verifies'] and not d['paie_definitive_autorisee']
    assert comptabilite(application,eq['sid'])==avant and eq['a'].get(V).headers['cache-control']=='no-store'
    for sql in ['UPDATE paie_variables SET montant=1 WHERE id=:i','DELETE FROM paie_variables WHERE id=:i','TRUNCATE paie_variables_evenements',"UPDATE paie_variables_evenements SET motif='FAUX' WHERE variable_id=:i"]:
        refuser(application,sql,{'i':i});refuser(application,sql,{'i':i},engine=application['personnel_runtime'])

def test_891_quantite_taux_arrondi_documente_et_references_manquantes(equipe):
    eq=equipe;eid,_=avec_salaire(eq);rid=rubrique(eq,formule='QUANTITE_TAUX')
    body=entree(eid,rid,mode='QUANTITE_TAUX',montant=None,quantite='3',taux='0.335')
    body['justificatifs']={};assert eq['a'].post(V,json=body).status_code==400
    body['justificatifs']={'ATTESTATION_FICTIVE':'SOURCE-FICTIVE891'}
    q=ok(eq['a'].post(V,json=body),201);assert q['montant']=='1.01'
    d=ok(eq['a'].get(f'{V}/{q["id"]}'));assert d['donnees']['taux']=='0.335' and 'ROUND_HALF_UP' in d['instantane']['arrondi']

@pytest.mark.parametrize('mutation',[{'montant':'NaN'},{'montant':'Infinity'},{'montant':True},{'montant':1.5},{'montant':'0.001'},{'montant':'-1'},{'date_effet':'2026-12-01'},{'periode':'2026-11-02'},{'employe_id':True}],ids=['nan','infini','booleen','float','precision','negatif','mois','premier','id_booleen'])
def test_891_erreurs_refusees_sans_reecho(equipe,mutation):
    eq=equipe;eid,_=avec_salaire(eq);rid=rubrique(eq);r=eq['a'].post(V,json=entree(eid,rid,**mutation))
    assert r.status_code==422 and 'input' not in r.text

def test_891_doublons_recurrences_annulation_et_incompatibilites(equipe):
    eq=equipe;eid,_=avec_salaire(eq);rid=rubrique(eq);a=envoyer(eq,eid,rid)
    assert eq['a'].post(V,json=entree(eid,rid,source_reference='AUTRE-FICTIVE891')).status_code==409
    ok(eq['a'].post(f'{V}/{a["id"]}/annuler',json={'motif':'Correction de brouillon fictive891'}))
    b=envoyer(eq,eid,rid);assert b['id']!=a['id']
    rid2=rubrique(eq,'INCOMPAT_FICTIVE891',incompatibilites=['PRIME_FICTIVE891'])
    assert eq['a'].post(V,json=entree(eid,rid2)).status_code==409
    envoyer(eq,eid,rid,periode='2026-12-01',date_effet='2026-12-15')
    ra=rubrique(eq,'ANNUELLE_FICTIVE891',periodicite='annuelle');envoyer(eq,eid,ra)
    assert eq['a'].post(V,json=entree(eid,ra,periode='2026-12-01',date_effet='2026-12-15',source_reference='AUTRE-ANNUELLE')).status_code==409
    rp=rubrique(eq,'PONCTUELLE_FICTIVE891',periodicite='ponctuelle');envoyer(eq,eid,rp);envoyer(eq,eid,rp,source_reference='AUTRE-PONCTUELLE')

def test_891_salaire_manquant_et_sources_changees_ne_sont_pas_supposes(equipe):
    eq=equipe;rid=rubrique(eq);incomplet=actif(eq)
    assert eq['a'].post(V,json=entree(incomplet,rid)).status_code==409
    eid,cid=avec_salaire(eq,m='AUTRE891');v=envoyer(eq,eid,rid);submit(eq,v['id'])
    p=proposition(eq,eid,3,'REMUNERATION',{'contrat_version_id':cid,'montant':'10000.00','date_effet':'2026-10-01','periodicite':'mensuelle','reference_justificatif':'NOUVEAU-FICTIF891'})
    soumettre(eq['a'],p['id'],3);approuver(eq,p['id'],3)
    assert eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()).status_code==409
    d=ok(eq['a'].get(f'{V}/{v["id"]}'));assert d['instantane']['remuneration']['montant']=='9000.10' and d['statut']=='SOUMIS'
    ok(eq['b'].post(f'{V}/{v["id"]}/rejeter',json=choix()))

def test_891_societes_capacites_et_options_personnel_seul(application,equipe):
    eq=equipe;eid,_=avec_salaire(eq);rid=rubrique(eq);v=envoyer(eq,eid,rid)
    assert eq['l'].get(V).status_code==403 and eq['l'].get(V+'/options').status_code==403
    grant(eq['a'],eq['lid'],'personnel.lire_remuneration')
    masque=ok(eq['l'].get(f'{V}/{v["id"]}'));assert masque['historique_masque'] and masque['source_reference'] is None and masque['donnees']['justificatifs'] is None and not masque['evenements']
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre)
        assert autre.get(f'{V}/{v["id"]}').status_code==404 and autre.post(V,json=entree(eid,rid)).status_code==404
    p,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(p):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        o=ok(p.get(V+'/options',params={'au':'2026-11-15'}));assert o['salaries'][0]['remuneration']['montant']=='9000.10'
        assert o['rubriques'][0]['version_id'] and p.get('/api/factures').status_code==403

def test_891_decisions_concurrentes_une_seule_application(application,equipe):
    eq=equipe;eid,_=avec_salaire(eq);rid=rubrique(eq);v=envoyer(eq,eid,rid);submit(eq,v['id'])
    def envoyer_decision(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['b'].headers),timeout=30) as c:return c.post(f'{V}/{v["id"]}/approuver',json=choix()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(envoyer_decision,range(2)))
    assert sorted(r)==[200,409]
    d=ok(eq['a'].get(f'{V}/{v["id"]}'));assert len(d['evenements'])==3

def test_891_beneficiaire_ne_valide_pas_sa_variable(application,equipe):
    eq=equipe;c,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(c):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        ceq=dict(eq,b=c,bid=u['id'])
        e=ok(eq['a'].post(W,json=creation('BEN-FICTIF891',utilisateur_beneficiaire_id=eq['bid'],beneficiaire_sans_compte_confirme=False)),201)
        eid=e['employe_id'];soumettre(eq['a'],e['demande']['id'],0);ok(c.post(f'{W}/demandes/{e["demande"]["id"]}/approuver',json=decision(0)))
        p=proposition(ceq,eid,1,'CONTRAT',{'type_contrat':'CDI','date_effet':'2026-01-01','date_debut':'2026-01-01','reference_justificatif':'CONTRAT-FICTIF891'})
        soumettre(eq['a'],p['id'],1);approuver(ceq,p['id'],1);cid=ok(eq['a'].get(f'{W}/{eid}?au=2026-11-15'))['contrat']['id']
        p=proposition(ceq,eid,2,'REMUNERATION',{'contrat_version_id':cid,'montant':'9000.10','date_effet':'2026-01-01','periodicite':'mensuelle','reference_justificatif':'BASE-FICTIVE891'})
        soumettre(eq['a'],p['id'],2);approuver(ceq,p['id'],2)
        rid=rubrique(ceq);v=envoyer(eq,eid,rid);submit(eq,v['id'])
        assert eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()).status_code==403
        ok(c.post(f'{V}/{v["id"]}/approuver',json=choix()))

def test_891_preparateur_inactif_rejet_trace_et_migration_rejouee(application,equipe):
    eq=equipe;eid,_=avec_salaire(eq);rid=rubrique(eq);c,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(c):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        ceq=dict(eq,a=c,uid=u['id']);v=envoyer(ceq,eid,rid);submit(ceq,v['id'])
        ok(eq['a'].patch('/api/utilisateurs/'+str(u['id']),json={'actif':False}))
        assert eq['b'].post(f'{V}/{v["id"]}/approuver',json=choix()).status_code==409
        ok(eq['b'].post(f'{V}/{v["id"]}/rejeter',json=choix()))
        d=ok(eq['a'].get(f'{V}/{v["id"]}'));assert d['prepare_par']==u['id'] and d['statut']=='REJETE'
    avant=empreintes_tables(application['engine']);raw=application['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/114_paie_variables.sql').read_text(encoding='utf8'))
    finally:raw.close()
    assert empreintes_tables(application['engine'])==avant
