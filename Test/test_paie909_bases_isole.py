from pathlib import Path
from contextlib import closing
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest,httpx
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
import json
from test_paie907_qualification_ir_isole import (
    application as application119,application118,application117,application116,application115,application114,application113,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite,refuser,preuve,E,S,dec,contenu_rubrique)
from test_paie893_campagnes_isole import salarie,gain,simuler as brut,envoyer,submit,choix,V
from test_paie897_social_isole import creer,version,contenu
from test_paie899_social_isole import calculer,C
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];F='/api/employes/personnel/fiscalite/preparations'


def installer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/120_paie_preparations_fiscales.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application119):
    app=application119;avant=empreintes_tables(app['engine']);installer(app);installer(app);apres=empreintes_tables(app['engine'])
    assert all(apres[t]==h for t,h in avant.items())
    yield app


def preparer(eq,qualifications=True):
    eid,_=salarie(eq,m='P909');grant(eq.get('admin',eq['a']),eq['bid'],'personnel.valider_regles_paie')
    c=contenu_rubrique(periodicite='ponctuelle')
    if qualifications:
        c['regles']['IR'].update(statut_reglementaire='VALIDE',texte_reference='Texte FICTIF909',article='FICTIF909',url_source='https://www.finances.gov.ma/',empreinte_preuve='a'*64)
        c['frais_professionnels']=preuve('EXCLUS')
    v=ok(eq['a'].post(E,json={'code':'GAIN_FICTIF909','contenu':c,'motif':'Création FICTIVE909'}),201)
    ok(eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)))
    rid=v['rubrique_id'];gain(eq,eid,rid);q=brut(eq,[eid]);bs=[]
    for code,traitement,taux,pat,assiette,plafond,composants in [('B1_FICTIF909','DEDUCTIBLE','1','2','CNSS','6000.00',['B1']),('B2_FICTIF909','NON_DEDUCTIBLE','3','4','AMO',None,['B2'])]:
        kw={'taux_salarial':taux,'taux_patronal':pat,'assiette':assiette,'plafond_mode':'SANS' if plafond is None else 'MONTANT','plafond':plafond,'composants':composants}
        if qualifications:kw['deductibilite_ir']=preuve(traitement)
        b=creer(eq,code,'REGIME_FISC909',**kw);ok(eq['b'].post(f'{S}/versions/{b["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)));bs.append(b)
    social=calculer(eq,eid,q,regime='REGIME_FISC909')
    return eid,rid,q,social,bs


def demande(eid,social,**kw):return {'social_id':social['id'],'declarations':[{'employe_id':eid,'base_imposable':'9000.10','base_frais':'9000.10','conditions_confirmees':True,'deductibilite_integrale_confirmee':True,'reference_controle':'CTRL-FICTIF909'}],
    'mode_pedagogique_confirme':True,'cle_idempotence':str(uuid4()),'motif':'Préparation FICTIVE909',**kw}


def calcul_fiscal(eq,eid,social,**kw):return ok(eq['a'].post(F,json=demande(eid,social,**kw)),201)


def test_909_bases_exactes_sources_historique_et_absence_ecriture(application,equipe):
    eq=equipe;eid,rid,q,s,bs=preparer(eq);avant=comptabilite(application,eq['sid']);r=calcul_fiscal(eq,eid,s);c=r['contenu'];t=c['totaux']
    assert c['complet_pour_bases'] and t['brut_imposable']=='9300.11' and t['base_frais_professionnels']=='9000.10'
    assert t['cotisations_salariales_deductibles']=='60.00' and t['cotisations_salariales_non_deductibles']=='294.00'
    assert t['revenu_avant_frais_autres_deductions']=='9240.11'
    assert all(t[k] is None for k in ['frais_professionnels','revenu_net_imposable','ir','net_a_payer']) and not c['paie_definitive_autorisee']
    assert c['social_empreinte']==s['empreinte'] and c['brut_empreinte']==q['empreinte']
    assert c['employes'][0]['variables_sources'][0]['rubrique_id']==rid
    assert [b['version_id'] for b in c['employes'][0]['cotisations']]==[b['id'] for b in bs]
    assert ok(eq['a'].get(f'{F}/{r["id"]}'))['contenu']==c and ok(eq['a'].get(F))['elements'][0]['id']==r['id']
    assert eq['a'].get(F).headers['cache-control']=='no-store' and comptabilite(application,eq['sid'])==avant
    opt=ok(eq['a'].get(F+'/options',params={'social_id':s['id']}));assert opt['brut']['id']==q['id']


@pytest.mark.parametrize('mutation',[{'base_imposable':None},{'base_frais':None},{'conditions_confirmees':False},{'deductibilite_integrale_confirmee':False},{'base_imposable':'9800.11'}])
def test_909_inconnus_et_limites_deduction_explicites(equipe,mutation):
    eq=equipe;eid,_,_,s,_=preparer(eq);d=demande(eid,s);d['declarations'][0].update(mutation)
    c=ok(eq['a'].post(F,json=d),201)['contenu'];assert not c['complet_pour_bases'] and c['employes'][0]['anomalies']
    assert c['totaux']['revenu_net_imposable'] is None
    if mutation=={'base_frais':None}:assert c['totaux']['brut_imposable']=='9300.11'


def test_909_ancien_parametrage_non_qualifie_sans_deduction_automatique(equipe):
    eq=equipe;eid,_,_,s,_=preparer(eq,qualifications=False);c=calcul_fiscal(eq,eid,s)['contenu']
    assert not c['complet_pour_bases'] and c['totaux']['cotisations_salariales_deductibles'] is None and c['totaux']['brut_imposable'] is None


def test_909_source_changee_et_snapshot_fiscal_initial_intact(equipe):
    eq=equipe;eid,rid,q,s,_=preparer(eq);r=calcul_fiscal(eq,eid,s)
    gain(eq,eid,rid,montant='100.00',source_reference='EXTRA-FICTIF909')
    n=calcul_fiscal(eq,eid,s)['contenu'];assert not n['complet_pour_bases'] and n['totaux']['brut_imposable'] is None
    assert 'SOURCE_SOCIALE_CHANGEE' in {a['code'] for a in n['employes'][0]['anomalies']}
    assert ok(eq['a'].get(f'{F}/{r["id"]}'))['contenu']==r['contenu']


def test_909_qualification_sociale_changee_dans_mois_bloquante(equipe):
    eq=equipe;eid,_,_,s,bs=preparer(eq);c=contenu(date_debut='2026-11-15',taux_salarial='1',taux_patronal='2',plafond='6000.00',composants=['B1'],deductibilite_ir=preuve('NON_DEDUCTIBLE'))
    n=version(eq,bs[0],c);ok(eq['b'].post(f'{S}/versions/{n["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)))
    r=calcul_fiscal(eq,eid,s)['contenu'];assert not r['complet_pour_bases'] and r['totaux']['brut_imposable'] is None


def test_909_concurrence_et_conflit_idempotence(application,equipe):
    eq=equipe;eid,_,_,s,_=preparer(eq);d=demande(eid,s)
    def calcul(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=30) as c:return ok(c.post(F,json=d),201)
    with ThreadPoolExecutor(max_workers=2) as pool:a,b=list(pool.map(calcul,range(2)))
    assert a['id']==b['id'] and a['reutilise']!=b['reutilise'];d['declarations'][0]['base_frais']='8000.00'
    assert eq['a'].post(F,json=d).status_code==409


def test_909_droits_profil_selection_immutabilite_et_rejeu(application,equipe):
    eq=equipe;eid,_,_,s,_=preparer(eq);r=calcul_fiscal(eq,eid,s);assert eq['l'].get(F).status_code==403
    d=demande(eid,s);d['declarations'][0]['employe_id']+=10000;assert eq['a'].post(F,json=d).status_code==400
    with closing(client(application)[0]) as autre:
        identite=ok(autre.get('/api/auth/me'));uid=identite['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre);assert autre.get(f'{F}/{r["id"]}').status_code==404 and autre.post(F,json=demande(eid,s)).status_code==404
        sql="INSERT INTO paie_preparations_fiscales(societe_id,social_id,numero,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:i,999,:k,:h,CAST(:c AS jsonb),:h,:u,'FICTIF909')"
        with pytest.raises(DBAPIError) as erreur:
            with application['engine'].begin() as db:db.execute(text(sql),{'s':identite['societe_id'],'i':s['id'],'k':str(uuid4()),'h':'a'*64,'c':json.dumps(r['contenu']),'u':uid})
        assert erreur.value.orig.pgcode=='23503'
    p,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(p):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert p.get(F).status_code==200 and p.get(F+'/options',params={'social_id':s['id']}).status_code==200
        assert p.post(F,json=demande(eid,s)).status_code==201 and p.get('/api/factures').status_code==403
        assert p.get(F+'/1/autre').status_code==404 and p.put(f'{F}/{r["id"]}',json={}).status_code==405
    for sql in ["UPDATE paie_preparations_fiscales SET contenu='{}' WHERE id=:i",'DELETE FROM paie_preparations_fiscales WHERE id=:i','TRUNCATE paie_preparations_fiscales']:
        for engine in [application['engine'],application['personnel_runtime']]:refuser(application,sql,{'i':r['id']},engine=engine)
    avant=empreintes_tables(application['engine']);installer(application);assert empreintes_tables(application['engine'])==avant


@pytest.mark.parametrize('valeur',['NaN','Infinity',True])
def test_909_erreur_http_sans_reecho_sensible(equipe,valeur):
    d=demande(1,{'id':1});d['declarations'][0]['base_imposable']=valeur
    r=equipe['a'].post(F,json=d);assert r.status_code==422 and 'input' not in r.text


def test_909_installation_manquante_explicite_et_table_preservee(application,equipe):
    c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']);avant=empreintes_tables(application['engine'])
    try:
        with application['engine'].begin() as db:db.execute(text('ALTER TABLE public.paie_preparations_fiscales RENAME TO paie_preparations_fiscales_test909'))
        r=equipe['a'].get(F);assert r.status_code==503 and '120' in r.text
    finally:
        with application['engine'].begin() as db:db.execute(text('ALTER TABLE public.paie_preparations_fiscales_test909 RENAME TO paie_preparations_fiscales'))
    assert empreintes_tables(application['engine'])==avant
