"""Catalogue réel HTTP/PostgreSQL natif nonce,aucune base utilisateur."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import copy,json
import pytest,httpx
from sqlalchemy import text
from test_personnel887_banque_isole import (
    application as application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    equipe,client,ok,role_client,grant,activer,CAPS,comptabilite)
from test_personnel_dossiers875_isole import refuser
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];E='/api/employes/personnel/elements'

@pytest.fixture(scope='module')
def application(application112):
    app=application112;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/113_paie_catalogue.sql').read_text(encoding='utf8'))
        finally:raw.close()
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items())
    with app['engine'].connect() as db:assert db.scalar(text('SELECT count(*) FROM paie_rubriques'))==0
    yield app

def regle(traitement='A_VERIFIER',plafond=None,**kw):
    return {'traitement':traitement,'statut_reglementaire':'A_VERIFIER','plafond':plafond,'unite':'operation','conditions':'Hypothèse entièrement fictive de recette889',**kw}

def contenu(**kw):
    return {'libelle':'Prime FICTIVE de recette','nature':'GAIN','periodicite':'mensuelle','formule':'MONTANT','date_debut':'2026-01-01',
      'justificatifs':['ATTESTATION_FICTIVE'],'incompatibilites':[],
      'regles':{'IR':regle('PLAFOND_MONTANT','500.00'),'CNSS':regle('PLAFOND_MONTANT','300.00'),'AMO':regle('SOUMIS')},**kw}

def creer(eq,code='PRIME_FICTIVE',**kw):return ok(eq['a'].post(E,json={'code':code,'contenu':contenu(**kw),'motif':'Création fictive889'}),201)
def dec(**kw):return {'motif':'Contrôle fictif889','independance_confirmee':True,'reference_controle':'CTRL-FICTIF889',**kw}

def test_889_catalogue_vide_versionnement_et_absence_ecriture(application,equipe):
    eq=equipe;a=eq['a'];b=eq['b'];avant=comptabilite(application,eq['sid']);v=creer(eq);rid=v['rubrique_id']
    q=ok(a.get(E));assert q['elements'][0]['id']==rid and q['elements'][0]['courante_id'] is None
    assert a.post(f'{E}/versions/{v["id"]}/approuver',json=dec()).status_code==403
    ok(b.post(f'{E}/versions/{v["id"]}/approuver',json=dec()))
    ancien=ok(a.get(f'{E}/{rid}'))['versions'][0]
    c=contenu(date_debut='2027-01-01',libelle='Prime FICTIVE future')
    n=ok(a.post(f'{E}/{rid}/versions',json={'version_attendue':1,'contenu':c,'motif':'Version future fictive'}),201)
    assert a.post(f'{E}/{rid}/versions',json={'version_attendue':1,'contenu':c,'motif':'Concurrence fictive'}).status_code==409
    ok(b.post(f'{E}/versions/{n["id"]}/approuver',json=dec()))
    assert ok(a.get(E,params={'au':'2026-12-31'}))['elements'][0]['courante_id']==v['id']
    assert ok(a.get(E,params={'au':'2027-01-01'}))['elements'][0]['courante_id']==n['id']
    d=ok(a.get(f'{E}/{rid}'));assert d['versions'][1]==ancien
    assert a.get(E).headers['cache-control']=='no-store'
    assert comptabilite(application,eq['sid'])==avant

def test_889_ventilation_ir_cnss_separee_sans_inventer_cumul(equipe):
    eq=equipe;v=creer(eq)
    for montant,ir,cnss in [('0.00','0.00','0.00'),('300.00','0.00','0.00'),('500.00','0.00','200.00'),('800.01','300.01','500.01')]:
        q=ok(eq['a'].post(f'{E}/versions/{v["id"]}/apercu',json={'montant':montant}))
        assert q['regimes']['IR']['soumis']==ir and q['regimes']['CNSS']['soumis']==cnss
        assert q['regimes']['AMO']['soumis']==montant and not q['utilisable_paie_definitive']
    c=contenu();c['regles']['IR']['unite']='annuel';c['regles']['CNSS']=regle()
    n=creer(eq,'AUTRE_FICTIVE',regles=c['regles'])
    q=ok(eq['a'].post(f'{E}/versions/{n["id"]}/apercu',json={'montant':'800.00'}))
    assert q['regimes']['IR']['soumis'] is None and q['regimes']['CNSS']['soumis'] is None

@pytest.mark.parametrize('montant',['NaN','Infinity','-1','0.001',True,12.3],ids=['nan','infini','negatif','precision','booleen','float'])
def test_889_montants_invalides_refuses(equipe,montant):
    v=creer(equipe);r=equipe['a'].post(f'{E}/versions/{v["id"]}/apercu',json={'montant':montant})
    assert r.status_code==422 and 'input' not in r.text

def test_889_validation_reglementaire_explicite_et_preuves(application,equipe):
    eq=equipe;c=contenu();c['regles']['IR']['statut_reglementaire']='VALIDE'
    body={'code':'REGLE_FICTIVE','contenu':c,'motif':'Test fictif889'}
    assert eq['a'].post(E,json=body).status_code==422
    c['regles']['IR'].update(texte_reference='RÉFÉRENCE FICTIVE,ne valide aucune exonération',article='Article FICTIF',url_source='https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf',empreinte_preuve='a'*64)
    v=ok(eq['a'].post(E,json=body),201)
    assert eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)).status_code==403
    refuser(application,"UPDATE paie_rubrique_versions SET statut='APPROUVEE',decision_par=:u,decision_at=clock_timestamp(),motif_decision='FICTIF',reference_controle='FICTIF',verification_reglementaire_confirmee=true WHERE id=:i",{'i':v['id'],'u':eq['bid']})
    cap=grant(eq['a'],eq['bid'],'personnel.valider_regles_paie')['id']
    assert eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec()).status_code==400
    ok(eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)))
    d=ok(eq['a'].get(f'{E}/{v["rubrique_id"]}'))['versions'][0]
    assert d['verification_reglementaire_confirmee'] and d['decision_par']==eq['bid'] and d['decision_at']
    c['date_debut']='2027-01-01'
    n=ok(eq['a'].post(f'{E}/{v["rubrique_id"]}/versions',json={'version_attendue':1,'contenu':c,'motif':'Suite fictive889'}),201)
    ok(eq['a'].post('/api/employes/securite/habilitations/'+str(cap)+'/revoquer',json={'motif':'Fin délégation fictive889'}))
    assert eq['b'].post(f'{E}/versions/{n["id"]}/approuver',json=dec(verification_reglementaire_confirmee=True)).status_code==403
    assert ok(eq['a'].get(f'{E}/{v["rubrique_id"]}'))['versions'][0]['statut']=='PROPOSEE'

def test_889_doublon_incompatibilites_et_mapping_inconnus(equipe):
    eq=equipe;v=creer(eq)
    assert eq['a'].post(E,json={'code':'PRIME_FICTIVE','contenu':contenu(),'motif':'Doublon fictif'}).status_code==409
    for kw in [{'incompatibilites':['INCONNUE']},{'incompatibilites':['AUTRE_FICTIVE']},{'compte_charge':'9999999999'}]:
        r=eq['a'].post(E,json={'code':'AUTRE_FICTIVE','contenu':contenu(**kw),'motif':'Test fictif889'});assert r.status_code==400
    d=ok(eq['a'].get(E));assert d['total']==1

def test_889_isolation_droits_personnel_seul_et_sql_immuable(application,equipe):
    eq=equipe;v=creer(eq);rid=v['rubrique_id']
    assert eq['l'].get(E).status_code==403
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        activer(autre)
        assert autre.get(f'{E}/{rid}').status_code==404
        assert autre.post(f'{E}/versions/{v["id"]}/apercu',json={'montant':'100.00'}).status_code==404
        assert autre.post(f'{E}/versions/{v["id"]}/approuver',json=dec()).status_code==404
    p,u,_,_=role_client(application,eq['a'],'personnel')
    with closing(p):
        for cap in CAPS:grant(eq['a'],u['id'],cap)
        assert p.get(E).status_code==200 and p.get('/api/factures').status_code==403
        assert p.get(E+'/1/autre').status_code==404 and p.post(E+'/1',json={}).status_code==405
    ok(eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec()))
    for commande in ['UPDATE paie_rubrique_versions SET contenu=\'{}\'::jsonb WHERE id=:i','DELETE FROM paie_rubrique_versions WHERE id=:i','TRUNCATE paie_rubrique_versions',"UPDATE paie_rubriques SET code='FAUX' WHERE id=:r"]:
        for engine in [None,application['personnel_runtime']]:refuser(application,commande,{'i':v['id'],'r':rid},**({'engine':engine} if engine else {}))

def test_889_concurrence_une_seule_decision_et_rejet_trace(application,equipe):
    eq=equipe;v=creer(eq)
    def approuver(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['b'].headers),timeout=30) as c:return c.post(f'{E}/versions/{v["id"]}/approuver',json=dec()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(approuver,range(2)))
    assert sorted(r)==[200,409]
    n=creer(eq,'REJET_FICTIF');ok(eq['b'].post(f'{E}/versions/{n["id"]}/rejeter',json=dec()))
    assert ok(eq['a'].get(f'{E}/{n["rubrique_id"]}'))['versions'][0]['statut']=='REJETEE'

def test_889_periode_expiree_ne_reactive_pas_version_precedente(equipe):
    eq=equipe;v=creer(eq,date_fin='2026-12-31');ok(eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec()))
    assert ok(eq['a'].get(E,params={'au':'2027-01-01'}))['elements'][0]['courante_id'] is None

def test_889_refus_requalification_passee_et_migration_rejouee_avec_donnees(application,equipe):
    from datetime import date
    eq=equipe;v=creer(eq);ok(eq['b'].post(f'{E}/versions/{v["id"]}/approuver',json=dec()))
    n=ok(eq['a'].post(f'{E}/{v["rubrique_id"]}/versions',json={'version_attendue':1,'contenu':contenu(date_debut=date.today().isoformat()),'motif':'Requalification rétroactive fictive'}),201)
    assert eq['b'].post(f'{E}/versions/{n["id"]}/approuver',json=dec()).status_code==409
    cap=grant(eq['a'],eq['bid'],'personnel.valider_regles_paie')['id'];avant=empreintes_tables(application['engine'])
    raw=application['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/113_paie_catalogue.sql').read_text(encoding='utf8'))
    finally:raw.close()
    assert empreintes_tables(application['engine'])==avant
    assert 'personnel.valider_regles_paie' in ok(eq['b'].get('/api/employes/securite/acces'))['capacites']
