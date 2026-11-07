"""Workflow HTTP + PostgreSQL natif nonce, rôle LOGIN non propriétaire."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
import json,time
import pytest
import httpx
from sqlalchemy import text
from test_personnel_dossiers875_isole import (
    application as application875, application873,application093,application092,application091,
    application090,application089,application087,migration,preparer,contrat,remuneration,
    exec_owner,refuser,client,ok,role_client,grant,activer,originaux,P,IDENTITE,AUDIT)
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1]
W='/api/employes/personnel'
CAPS=[IDENTITE,'personnel.lire_remuneration',AUDIT,'personnel.proposer','personnel.soumettre','personnel.approuver']


def appliquer(app):
    c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/107_personnel_workflow.sql').read_text(encoding='utf8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application875):
    app=application875
    with closing(client(app)[0]) as api:
        p=preparer(app,api);c=contrat(app,p);remuneration(app,p,c)
    vieux={}
    for t,cle in [('personnel_dossiers','employe_id'),('personnel_demandes','id')]:
        with app['engine'].connect() as db:vieux[t]=db.execute(text(f'SELECT to_jsonb(t) FROM {t} t ORDER BY {cle}')).scalars().all()
    exec_owner(app,'ALTER TABLE personnel_habilitations ADD CONSTRAINT ck_personnel_capacite_locale877 CHECK(length(capacite)>0)')
    avant=empreintes_tables(app['engine']);appliquer(app);appliquer(app);apres=empreintes_tables(app['engine'])
    assert all(apres[t]==h for t,h in avant.items() if t not in vieux)
    assert exec_owner(app,"SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='personnel_habilitations'::regclass AND conname='ck_personnel_capacite_locale877')")
    for t,cle in [('personnel_dossiers','employe_id'),('personnel_demandes','id')]:
        with app['engine'].connect() as db:rows=db.execute(text(f'SELECT to_jsonb(t) FROM {t} t ORDER BY {cle}')).scalars().all()
        assert [{k:v for k,v in r.items() if k in vieux[t][0]} for r in rows]==vieux[t]
    app=dict(app,ancien877=p)
    yield app


@pytest.fixture
def equipe(application):
    with closing(client(application)[0]) as a:
        b,u,_,_=role_client(application,a,'comptable');l,lu,_,_=role_client(application,a)
        with closing(b),closing(l):
            me=ok(a.get('/api/auth/me'))
            for uid in [me['id'],u['id']]:
                for cap in CAPS:grant(a,uid,cap)
            grant(a,lu['id'],IDENTITE);activer(a)
            yield {'a':a,'b':b,'l':l,'uid':me['id'],'bid':u['id'],'lid':lu['id'],'sid':me['societe_id']}


def creation(m='002',**kw):
    return dict({'matricule':m,'nom':'Salariée fictive877','poste':'Poste fictif','beneficiaire_sans_compte_confirme':True,
        'reference_beneficiaire':'Attestation fictive877','motif':'Création fictive877'},**kw)


def decision(rev,**kw):
    return dict({'revision_attendue':rev,'motif':'Décision fictive877','independance_confirmee':True,'reference_independance':'Contrôle fictif877'},**kw)


def creer(eq,m='002',**kw):return ok(eq['a'].post(W,json=creation(m,**kw)),201)


def soumettre(a,i,rev,status=200):
    return ok(a.post(f'{W}/demandes/{i}/soumettre',json={'revision_attendue':rev,'motif':'Soumission fictive877'}),status)


def approuver(eq,i,rev,status=200):return ok(eq['b'].post(f'{W}/demandes/{i}/approuver',json=decision(rev)),status)


def actif(eq,m='002'):
    e=creer(eq,m);i=e['demande']['id'];soumettre(eq['a'],i,0);approuver(eq,i,0)
    return e['employe_id']


def proposition(eq,eid,rev,nature,contenu,status=201):
    return ok(eq['a'].post(f'{W}/{eid}/modifications',json={'revision_attendue':rev,'motif':'Proposition fictive877','nature':nature,'contenu':contenu}),status)


def avec_salaire(eq,m='002'):
    eid=actif(eq,m)
    c=proposition(eq,eid,1,'CONTRAT',{'type_contrat':'CDI','date_effet':'2026-01-01','date_debut':'2026-01-01','reference_justificatif':'Contrat fictif877'})
    soumettre(eq['a'],c['id'],1);approuver(eq,c['id'],1)
    cid=ok(eq['a'].get(f'{W}/{eid}?au=2026-12-31'))['contrat']['id']
    r=proposition(eq,eid,2,'REMUNERATION',{'contrat_version_id':cid,'montant':'9000.10','date_effet':'2026-01-01',
        'periodicite':'mensuelle','reference_justificatif':'Rémunération fictive877'})
    soumettre(eq['a'],r['id'],2);approuver(eq,r['id'],2)
    return eid,cid


def comptabilite(app,sid):
    with app['engine'].connect() as db:
        return {t:db.execute(text(f'SELECT to_jsonb(t) FROM {t} t WHERE societe_id=:s ORDER BY id'),{'s':sid}).scalars().all()
                for t in ['ecritures','factures','reglements']}


def test_877_creation_trois_salaries_sans_fauxzero_et_sans_ecriture(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid'])
    ids=[creer(eq,m)['employe_id'] for m in ['002','02','2']]
    r=eq['a'].get(W);q=ok(r);assert r.headers['cache-control']=='no-store' and q['total']==3
    assert [x['employe_id'] for x in q['elements']]==list(reversed(ids))
    assert all(x['statut']=='BROUILLON' and x['remuneration'] is None and not x['paie_definitive_autorisee'] for x in q['elements'])
    with application['engine'].connect() as db:
        rows=db.execute(text('SELECT id,salaire_brut,actif FROM employes WHERE societe_id=:s ORDER BY id'),{'s':eq['sid']}).all()
        assert rows==[(i,None,False) for i in ids]
    assert eq['a'].post(W,json=creation(' 002 ')).status_code==409
    assert ok(eq['a'].get(W+'?limite=1&decalage=1'))['elements'][0]['employe_id']==ids[1]
    assert ok(eq['a'].get(W+'?recherche=002'))['total']==1
    assert comptabilite(application,eq['sid'])==avant


def test_877_salaire_futur_exact_non_ecrase_masque_et_ancienne_api(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid']);eid,cid=avec_salaire(eq)
    p=proposition(eq,eid,3,'REMUNERATION',{'contrat_version_id':cid,'montant':'9876.54','date_effet':'2027-01-01',
        'periodicite':'mensuelle','reference_justificatif':'Avenant fictif877'})
    assert ok(eq['a'].get(f'{W}/{eid}?au=2027-01-01'))['remuneration']['montant']=='9000.10'
    soumettre(eq['a'],p['id'],3);approuver(eq,p['id'],3)
    for au,mt in [('2026-12-31','9000.10'),('2027-01-01','9876.54')]:
        r=ok(eq['a'].get(f'{W}/{eid}?au={au}'));assert r['remuneration']['montant']==mt and r['dossier_complet_a_date']
    assert ok(eq['l'].get(f'{W}/{eid}?au=2027-01-01'))['remuneration'] is None
    r=eq['l'].get(f'{W}/demandes/{p["id"]}');assert r.status_code==200 and '9876.54' not in r.text and r.json()['contenu'] is None
    grant(eq['a'],eq['lid'],AUDIT)
    hist=ok(eq['l'].get(f'{W}/{eid}/historique'));assert all(x['motif'] is None for x in hist['elements'] if x['nature_demande']=='REMUNERATION')
    assert eq['a'].put(f'/api/employes/{eid}',json={'nom':'FAUX','salaire_brut':1}).status_code==409
    assert eq['a'].delete(f'/api/employes/{eid}').status_code==409
    assert comptabilite(application,eq['sid'])==avant


def test_877_auteur_et_beneficiaire_refuses_memes_admin(equipe):
    eq=equipe
    e=creer(eq,utilisateur_beneficiaire_id=eq['bid'],beneficiaire_sans_compte_confirme=False);i=e['demande']['id']
    soumettre(eq['a'],i,0)
    assert eq['a'].post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code==403
    assert eq['b'].post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code==403
    assert ok(eq['a'].get(f'{W}/demandes/{i}'))['statut']=='SOUMIS'


def test_877_rejet_puis_nouvelle_proposition_sans_effacement(equipe):
    eq=equipe;e=creer(eq);eid=e['employe_id'];i=e['demande']['id'];soumettre(eq['a'],i,0)
    r=ok(eq['b'].post(f'{W}/demandes/{i}/rejeter',json=decision(0)));assert r['revision']==1
    assert ok(eq['a'].get(f'{W}/{eid}'))['statut']=='BROUILLON'
    p=proposition(eq,eid,1,'DOSSIER',{'nom':'Identité corrigée fictive','poste':None})
    soumettre(eq['a'],p['id'],1);approuver(eq,p['id'],1)
    assert ok(eq['a'].get(f'{W}/{eid}'))['nom']=='Identité corrigée fictive'
    assert ok(eq['a'].get(f'{W}/demandes/{i}'))['statut']=='REJETE'
    assert eq['b'].post(f'{W}/demandes/{i}/approuver',json=decision(2)).status_code==409


def test_877_conflit_revision_et_rejet_demande_perimee(equipe):
    eq=equipe;eid=actif(eq)
    a=proposition(eq,eid,1,'DOSSIER',{'nom':'Premier changement fictif','poste':None})
    b=proposition(eq,eid,1,'DOSSIER',{'nom':'Second changement fictif','poste':None})
    soumettre(eq['a'],a['id'],1);soumettre(eq['a'],b['id'],1);approuver(eq,a['id'],1)
    assert eq['b'].post(f'{W}/demandes/{b["id"]}/approuver',json=decision(2)).status_code==409
    r=ok(eq['b'].post(f'{W}/demandes/{b["id"]}/rejeter',json=decision(2)));assert r['revision']==3
    assert ok(eq['a'].get(f'{W}/{eid}'))['nom']=='Premier changement fictif'
    proposition(eq,eid,2,'DOSSIER',{'nom':'Périmé','poste':None},409)


def test_877_double_approbation_concurrente_un_seul_evenement(application,equipe):
    eq=equipe;e=creer(eq);i=e['demande']['id'];soumettre(eq['a'],i,0)
    def envoyer(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['b'].headers),timeout=30) as b:
            return b.post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(envoyer,range(2)))==[200,409]
    with application['engine'].connect() as db:
        assert db.scalar(text("SELECT count(*) FROM personnel_evenements WHERE demande_id=:i AND nature='DEMANDE_APPROUVEE'"),{'i':i})==1
    assert ok(eq['a'].get(f'{W}/{e["employe_id"]}'))['revision']==1


def test_877_societe_etrangere_et_roles_lecture(application,equipe):
    eq=equipe;e=creer(eq);eid=e['employe_id'];i=e['demande']['id']
    for path in [W,W+f'/{eid}',W+f'/demandes/{i}',W+f'/{eid}/historique']:
        with httpx.Client(base_url=application['api_url']) as anon:assert anon.get(path).status_code==401
    assert eq['l'].post(W,json=creation('X')).status_code==403
    grant(eq['a'],eq['lid'],'personnel.proposer');assert eq['l'].post(W,json=creation('X')).status_code==403
    with closing(client(application)[0]) as autre:
        me=ok(autre.get('/api/auth/me'))
        for cap in CAPS:grant(autre,me['id'],cap)
        activer(autre)
        assert ok(autre.get(W))['total']==0
        assert autre.get(f'{W}/{eid}').status_code==404
        assert autre.get(f'{W}/demandes/{i}').status_code==404
        assert autre.post(f'{W}/demandes/{i}/soumettre',json={'revision_attendue':0,'motif':'Refus'}).status_code==404
        assert autre.post(W,json=creation('002')).status_code==201
    ok(eq['a'].patch('/api/societe/modules',json={'module':'paie_grh','actif':False}))
    assert eq['a'].get(W).status_code==403


def test_877_revocation_et_privilege_financier_necessaire(application,equipe):
    eq=equipe;eid,cid=avec_salaire(eq)
    rows=ok(eq['a'].get(P+'/habilitations'))
    h=next(x for x in rows if x['utilisateur_id']==eq['uid'] and x['capacite']=='personnel.proposer')
    ok(eq['a'].post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif'}))
    assert eq['a'].post(W,json=creation('NOUVEAU')).status_code==403
    h=next(x for x in rows if x['utilisateur_id']==eq['uid'] and x['capacite']=='personnel.lire_remuneration')
    ok(eq['a'].post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif'}))
    r=eq['a'].get(f'{W}/{eid}?au=2026-12-31');assert r.status_code==200 and '9000.10' not in r.text


def test_877_sortie_future_statut_a_date_et_historique(application,equipe):
    eq=equipe;avant=comptabilite(application,eq['sid']);eid,cid=avec_salaire(eq)
    p=proposition(eq,eid,3,'SORTIE',{'date_sortie':'2027-06-30','reference_justificatif':'Pièce sortie fictive'})
    soumettre(eq['a'],p['id'],3);approuver(eq,p['id'],3)
    assert ok(eq['a'].get(f'{W}/{eid}?au=2027-06-29'))['statut']=='ACTIF'
    r=ok(eq['a'].get(f'{W}/{eid}?au=2027-06-30'));assert r['statut']=='SORTI' and not r['dossier_complet_a_date']
    assert ok(eq['a'].get(W+'?au=2027-07-01&statut=SORTI'))['total']==1
    proposition(eq,eid,4,'REMUNERATION',{'contrat_version_id':cid,'date_effet':'2027-07-01','montant':'1.00','periodicite':'mensuelle','reference_justificatif':'Refus'},409)
    assert comptabilite(application,eq['sid'])==avant


def test_877_reprise_explicite_sans_attester_salaire_historique(application):
    from test_paie_grh_postgres import dossier as ancien
    with closing(client(application)[0]) as a:
        e=ok(a.post('/api/employes',json=ancien()),201);me=ok(a.get('/api/auth/me'));avant=originaux(application,me['societe_id'])
        for cap in CAPS:grant(a,me['id'],cap)
        activer(a)
        r=ok(a.post(W+'/reprises',json={'employe_id':e['id'],'beneficiaire_sans_compte_confirme':True,
            'reference_beneficiaire':'Pièce fictive','motif':'Reprise contrôlée'}),201)
        assert r['statut']=='BROUILLON'
        assert originaux(application,me['societe_id'])==avant
        assert ok(a.get(f'{W}/{e["id"]}'))['remuneration'] is None
        assert a.get('/api/employes').json()[0]['salaire_brut'] is None
        assert a.get('/api/employes/cotisations?annee=2026').status_code==409
        assert a.post(W+'/reprises',json={'employe_id':e['id'],'beneficiaire_sans_compte_confirme':True,'reference_beneficiaire':'Pièce fictive','motif':'Doublon'}).status_code==409


def test_877_immutabilite_details_versions_et_rejeu_popule(application,equipe):
    eq=equipe;eid,cid=avec_salaire(eq)
    refuser(application,'UPDATE personnel_demandes_details SET contenu=\'{"nom":"Faux"}\'::jsonb WHERE employe_id=:e',{'e':eid},engine=application['personnel_runtime'])
    refuser(application,'DELETE FROM personnel_evenements WHERE employe_id=:e',{'e':eid},engine=application['personnel_runtime'])
    refuser(application,'UPDATE personnel_remunerations_versions SET montant=1 WHERE employe_id=:e',{'e':eid},engine=application['personnel_runtime'])
    avant=empreintes_tables(application['engine']);appliquer(application);appliquer(application)
    assert empreintes_tables(application['engine'])==avant


def test_877_conflit_version_rollback_decision_et_liste_demandes(application,equipe):
    eq=equipe;eid,cid=avec_salaire(eq);avant=comptabilite(application,eq['sid'])
    p=proposition(eq,eid,3,'REMUNERATION',{'contrat_version_id':cid,'montant':'11111.11','date_effet':'2026-01-01',
        'periodicite':'mensuelle','reference_justificatif':'Conflit fictif877'})
    soumettre(eq['a'],p['id'],3)
    q=ok(eq['b'].get(W+f'/demandes?statut=SOUMIS&employe_id={eid}'));assert q['total']==1 and q['elements'][0]['id']==p['id']
    assert eq['b'].post(f'{W}/demandes/{p["id"]}/approuver',json=decision(3)).status_code==409
    r=ok(eq['a'].get(f'{W}/demandes/{p["id"]}'))
    assert r['statut']=='SOUMIS' and r['decision_at'] is None and not r['independance_confirmee']
    d=ok(eq['a'].get(f'{W}/{eid}?au=2026-12-31'));assert d['revision']==3 and d['remuneration']['montant']=='9000.10'
    assert '11111.11' not in eq['l'].get(W+'/demandes').text
    assert comptabilite(application,eq['sid'])==avant


def test_877_creation_concurrente_matricule_et_pagination(application,equipe):
    eq=equipe
    def envoyer(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['a'].headers),timeout=30) as a:
            return a.post(W,json=creation('UNIQUE877')).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:assert sorted(pool.map(envoyer,range(2)))==[201,409]
    assert ok(eq['a'].get(W))['total']==1 and ok(eq['a'].get(W+'/demandes'))['total']==1
    for path in [W+'?limite=101',W+'/demandes?decalage=-1',W+'/demandes?statut=INVALIDE']:
        assert eq['a'].get(path).status_code==422


def test_877_droits_retirees_et_soumission_seulement_preparateur(equipe):
    eq=equipe;e=creer(eq);i=e['demande']['id']
    assert eq['b'].post(f'{W}/demandes/{i}/soumettre',json={'revision_attendue':0,'motif':'Autre auteur'}).status_code==403
    rows=ok(eq['a'].get(P+'/habilitations'))
    h=next(x for x in rows if x['utilisateur_id']==eq['uid'] and x['capacite']=='personnel.soumettre')
    ok(eq['a'].post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif'}))
    assert eq['a'].post(f'{W}/demandes/{i}/soumettre',json={'revision_attendue':0,'motif':'Refus'}).status_code==403
    grant(eq['a'],eq['uid'],'personnel.soumettre');soumettre(eq['a'],i,0)
    h=next(x for x in rows if x['utilisateur_id']==eq['bid'] and x['capacite']=='personnel.approuver')
    ok(eq['a'].post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif'}))
    assert eq['b'].post(f'{W}/demandes/{i}/approuver',json=decision(0)).status_code==403
    assert ok(eq['a'].get(f'{W}/demandes/{i}'))['statut']=='SOUMIS'


def test_877_contrat_non_applicable_et_sortie_conflictuelle(application,equipe):
    eq=equipe;eid,cid=avec_salaire(eq)
    p=proposition(eq,eid,3,'REMUNERATION',{'contrat_version_id':cid,'montant':'9876.54','date_effet':'2027-01-01',
        'periodicite':'mensuelle','reference_justificatif':'Futur fictif'})
    soumettre(eq['a'],p['id'],3);approuver(eq,p['id'],3)
    proposition(eq,eid,4,'SORTIE',{'date_sortie':'2026-12-31','reference_justificatif':'Conflit départ'},409)
    proposition(eq,eid,4,'REMUNERATION',{'contrat_version_id':999999,'montant':'1.00','date_effet':'2027-01-01',
        'periodicite':'mensuelle','reference_justificatif':'Contrat absent'},404)


def test_877_confirmation_explicite_aucune_reprise_automatique(application,equipe):
    eq=equipe;e=creer(eq);i=e['demande']['id'];soumettre(eq['a'],i,0)
    for v in [False,1,'true',None]:
        assert eq['b'].post(f'{W}/demandes/{i}/approuver',json=decision(0,independance_confirmee=v)).status_code==422
    assert eq['a'].post(W,json=creation('X',utilisateur_beneficiaire_id=999999,beneficiaire_sans_compte_confirme=False)).status_code==404
    assert eq['a'].post(W,json=creation('X',societe_id=999999)).status_code==422
    p=application['ancien877']
    with application['engine'].connect() as db:
        r=db.execute(text('SELECT origine,beneficiaire_sans_compte_confirme,reference_beneficiaire FROM personnel_dossiers WHERE employe_id=:e'),p).one()
        assert r==('historique_a_confirmer',False,None)


def test_877_ecriture_definitive_existante_conservee(application,equipe):
    eq=equipe
    e=ok(eq['a'].post('/api/ecritures',json={'date':'2026-01-05','journal':'BQ','libelle':'Capital fictif conservation877',
        'lignes':[{'compte':'5141','libelle':'Banque fictive','debit':1000,'credit':0},
                  {'compte':'1111','libelle':'Capital fictif','debit':0,'credit':1000}]}),201)
    ok(eq['a'].post(f'/api/ecritures/{e["id"]}/valider'))
    avant=comptabilite(application,eq['sid'])
    with application['engine'].connect() as db:
        lignes=db.execute(text('SELECT to_jsonb(l) FROM lignes_ecriture l WHERE ecriture_id=:i ORDER BY id'),{'i':e['id']}).scalars().all()
    eid,_=avec_salaire(eq)
    assert ok(eq['a'].get(f'{W}/{eid}?au=2026-12-31'))['remuneration']['montant']=='9000.10'
    assert comptabilite(application,eq['sid'])==avant
    with application['engine'].connect() as db:
        assert db.execute(text('SELECT to_jsonb(l) FROM lignes_ecriture l WHERE ecriture_id=:i ORDER BY id'),{'i':e['id']}).scalars().all()==lignes
