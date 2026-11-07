"""Banque privée dans le circuit existant,PG natif et vrais appels HTTP."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import pytest,httpx
from sqlalchemy import text
from test_personnel885_coffre_isole import (
    application as application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,
    cles_coffre885,client,ok,role_client,grant,activer,CAPS,W,P,C,equipe,identite,config,depot,PDF,comptabilite)
from test_personnel_workflow877_isole import decision,soumettre,proposition,creation
from postgres_isole import verifier_cible_isolee
from recette_restauration_consolidee_084 import empreintes_tables

R=Path(__file__).resolve().parents[1];SECRET='FICTIF-COORDONNEES-887-1122'

@pytest.fixture(scope='module')
def application(application111):
    app=application111;c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes_tables(app['engine'])
    for _ in range(2):
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((R/'hisabpro-backend/112_personnel_banque_chiffree.sql').read_text(encoding='utf8'))
        finally:raw.close()
    apres=empreintes_tables(app['engine']);assert all(apres[t]==h for t,h in avant.items())
    yield app

def preparer(eq):
    eid=identite(eq)
    for uid in [eq['uid'],eq['bid']]:grant(eq['a'],uid,'personnel.lire_identifiants_sensibles')
    config(eq['a']);return eid

def banque(eq,eid,revision=1,secret=SECRET,effet='2026-01-01',**kwargs):
    contenu={'date_effet':effet,'rib_iban':secret,'banque':'Banque FICTIVE887','titulaire':'Titulaire FICTIF887','reference_justificatif':'JUSTIFICATIF-FICTIF887',**kwargs}
    return eq['a'].post(f'{W}/{eid}/modifications',json={'nature':'BANQUE','revision_attendue':revision,'motif':'Proposition bancaire fictive887','contenu':contenu})

def approuver_banque(eq,eid,ident,revision):
    q=eq['b'].get(f'{C}/{eid}/banque/{ident}/reveler');assert q.status_code==200 and q.headers['cache-control']=='no-store'
    return ok(eq['b'].post(f'{W}/demandes/{ident}/approuver',json=decision(revision,verification_bancaire_confirmee=True)))

def test_887_banque_chiffree_sans_ecriture_avec_controle_independant(application,equipe):
    eq=equipe;eid=preparer(eq);a=eq['a'];b=eq['b'];avant=comptabilite(application,eq['sid'])
    piece=ok(depot(a,eid,categorie='banque'),201)['id'];p=ok(banque(eq,eid,piece_id=piece),201);i=p['id']
    assert ok(a.get(f'{W}/{eid}?au=2026-12-31'))['banque'] is None
    assert SECRET not in a.get(f'{W}/demandes/{i}').text
    soumettre(a,i,1)
    assert a.post(f'{W}/demandes/{i}/approuver',json=decision(1,verification_bancaire_confirmee=True)).status_code==403
    assert b.post(f'{W}/demandes/{i}/approuver',json=decision(1)).status_code==400
    assert b.post(f'{W}/demandes/{i}/approuver',json=decision(1,verification_bancaire_confirmee=True)).status_code==409
    approuver_banque(eq,eid,i,1)
    d=ok(a.get(f'{W}/{eid}?au=2026-12-31'));assert d['banque']['masque']=='•••• 1122' and SECRET not in json.dumps(d)
    assert ok(a.get(f'{C}/{eid}/banque/{i}/reveler'))['rib_iban']==SECRET
    with application['engine'].connect() as db:
        for table in ['personnel_demandes','personnel_demandes_details','personnel_evenements','personnel_banque_versions','audit_actions']:
            assert SECRET not in db.scalar(text(f"SELECT coalesce(string_agg(to_jsonb(t)::text,''),'') FROM {table} t WHERE societe_id=:s"),{'s':eq['sid']})
        assert db.scalar(text('SELECT verification_confirmee FROM personnel_banque_versions WHERE demande_id=:i'),{'i':i})
    assert comptabilite(application,eq['sid'])==avant

def test_887_effet_futur_immutabilite_masques_et_isolation(application,equipe):
    eq=equipe;eid=preparer(eq);a=eq['a'];i=ok(banque(eq,eid),201)['id'];soumettre(a,i,1);approuver_banque(eq,eid,i,1)
    with application['engine'].connect() as db:ancien=db.scalar(text('SELECT to_jsonb(v) FROM personnel_banque_versions v WHERE demande_id=:i'),{'i':i})
    futur=ok(banque(eq,eid,revision=2,secret='FICTIF-COORDONNEES-887-3344',effet='2027-01-01'),201)['id']
    soumettre(a,futur,2);approuver_banque(eq,eid,futur,2)
    assert ok(a.get(f'{W}/{eid}?au=2026-12-31'))['banque']['demande_id']==i
    assert ok(a.get(f'{W}/{eid}?au=2027-01-01'))['banque']['demande_id']==futur
    grant(a,eq['lid'],'personnel.audit_lire')
    for path in [W,f'{W}/{eid}',W+'/demandes',f'{W}/demandes/{i}',f'{W}/{eid}/historique']:
        r=eq['l'].get(path);assert r.status_code==200 and '1122' not in r.text and SECRET not in r.text
    assert eq['l'].get(f'{C}/{eid}/banque/{i}/reveler').status_code==403
    with closing(client(application)[0]) as autre:
        uid=ok(autre.get('/api/auth/me'))['id']
        for cap in CAPS:grant(autre,uid,cap)
        grant(autre,uid,'personnel.lire_identifiants_sensibles');activer(autre)
        assert autre.get(f'{C}/{eid}/banque/{i}/reveler').status_code==404
    from test_personnel_dossiers875_isole import refuser
    for sql in ["UPDATE personnel_banque_versions SET masque='FAUX' WHERE demande_id=:i",'DELETE FROM personnel_banque_versions WHERE demande_id=:i']:
        refuser(application,sql,{'i':i});refuser(application,sql,{'i':i},engine=application['personnel_runtime'])
    with application['engine'].connect() as db:assert db.scalar(text('SELECT to_jsonb(v) FROM personnel_banque_versions v WHERE demande_id=:i'),{'i':i})==ancien

@pytest.mark.parametrize('modification',[{'rib_iban':'•••• 1122'},{'banque':'X'*121},{'piece_id':True},{'date_effet':123}],ids=['masque','texte_trop_long','identifiant_booleen','date_nombre'])
def test_887_erreurs_validation_sans_reecho_de_coordonnees(equipe,modification):
    eq=equipe;eid=preparer(eq);r=banque(eq,eid,**modification) if 'rib_iban' not in modification and 'date_effet' not in modification else None
    if r is None:
        c={'date_effet':'2026-01-01','rib_iban':SECRET,'reference_justificatif':'JUSTIF-FICTIF887',**modification}
        r=eq['a'].post(f'{W}/{eid}/modifications',json={'nature':'BANQUE','revision_attendue':1,'motif':'Test validation fictif887','contenu':c})
    assert r.status_code==422 and SECRET not in r.text and 'input' not in r.text

def test_887_coordonnees_pas_dans_notes_ni_pieces_etrangeres(equipe):
    eq=equipe;eid=preparer(eq);a=eq['a']
    r=a.post(f'{W}/{eid}/modifications',json={'nature':'BANQUE','revision_attendue':1,'motif':'Copie '+SECRET,'contenu':{'date_effet':'2026-01-01','rib_iban':SECRET,'reference_justificatif':'REF-FICTIVE887'}})
    assert r.status_code==400 and SECRET not in r.text
    assert banque(eq,eid,piece_id=999999).status_code==404
    p=ok(banque(eq,eid),201)['id']
    assert a.post(f'{W}/demandes/{p}/soumettre',json={'revision_attendue':1,'motif':SECRET}).status_code==400
    assert ok(a.get(f'{W}/demandes/{p}'))['statut']=='BROUILLON'
    for corps in [{'nature':SECRET,'contenu':{},'revision_attendue':1,'motif':'Test fictif'},
      {'nature':'BANQUE','revision_attendue':1,'motif':'Test fictif','contenu':{'rib_iban':SECRET,'date_effet':'2026-01-01','reference_justificatif':'FICTIF',SECRET:'champ interdit'}}]:
        r=a.post(f'{W}/{eid}/modifications',json=corps);assert r.status_code==422 and SECRET not in r.text

def test_887_approbations_concurrentes_une_seule_decision(application,equipe):
    eq=equipe;eid=preparer(eq);i=ok(banque(eq,eid),201)['id'];soumettre(eq['a'],i,1)
    ok(eq['b'].get(f'{C}/{eid}/banque/{i}/reveler'))
    def valider(_):
        with httpx.Client(base_url=application['api_url'],headers=dict(eq['b'].headers),timeout=30) as c:
            return c.post(f'{W}/demandes/{i}/approuver',json=decision(1,verification_bancaire_confirmee=True)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:resultats=list(pool.map(valider,range(2)))
    assert sorted(resultats)==[200,409]
    assert ok(eq['a'].get(f'{W}/{eid}'))['revision']==2

def test_887_rejet_auteur_desactive_et_date_apres_sortie(application,equipe):
    eq=equipe;eid=preparer(eq);a=eq['a']
    c,u,_,_=role_client(application,a,'comptable')
    with closing(c):
        for cap in CAPS:grant(a,u['id'],cap)
        grant(a,u['id'],'personnel.lire_identifiants_sensibles')
        ceq=dict(eq,a=c);i=ok(banque(ceq,eid),201)['id'];soumettre(c,i,1)
        ok(a.patch(f'/api/utilisateurs/{u["id"]}',json={'actif':False}))
        ok(eq['b'].get(f'{C}/{eid}/banque/{i}/reveler'))
        assert eq['b'].post(f'{W}/demandes/{i}/approuver',json=decision(1,verification_bancaire_confirmee=True)).status_code==409
        ok(eq['b'].post(f'{W}/demandes/{i}/rejeter',json=decision(1)))
        assert ok(a.get(f'{W}/demandes/{i}'))['prepare_par']==u['id']
    sortie=proposition(eq,eid,2,'SORTIE',{'date_sortie':'2027-06-30','reference_justificatif':'SORTIE-FICTIVE887'})
    soumettre(a,sortie['id'],2);ok(eq['b'].post(f'{W}/demandes/{sortie["id"]}/approuver',json=decision(2)))
    assert banque(eq,eid,revision=3,effet='2027-07-01').status_code==409
