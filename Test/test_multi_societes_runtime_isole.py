"""Création multi-société et accès secondaires, API/Edge sous LOGIN SQL limité."""
from datetime import date
from pathlib import Path
import json
import shutil
import uuid

import httpx
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import empreintes_tables
from test_complements_structure_postgres import refuser
from test_permissions_documents_commerciaux_postgres import acl
from test_e2e_runtime_annuel_isole import application as application089, application087, migration, annee_banque
from test_restauration_runtime_acl_089 import catalogue_acl, test089_restore_acl_colonnes_fonctions_annee_et_nouveau_cycle_api as scenario_restore
from test_ras_lecture_conservation import client
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable

ROOT=Path(__file__).resolve().parents[1]
SQL='090_permissions_multi_societes.sql'


@pytest.fixture(scope='module')
def application(application089):
    app=application089;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    app['avant090']=catalogue_acl(app['engine']),acl(app['engine'])
    if (BACK/SQL).is_file():
        for _ in range(2):
            raw=app['engine'].raw_connection()
            try:
                raw.autocommit=True
                with raw.cursor() as cur:cur.execute((BACK/SQL).read_text(encoding='utf-8'))
            finally:raw.close()
    try:
        yield app
    finally:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        (ROOT/'.codex-tests'/f"runtime447_api_{c['nonce']}.log").write_text(
            app['api_log'].read_text(encoding='utf-8',errors='replace'),encoding='utf-8')


def ok(r,status=200):
    assert r.status_code==status,r.text
    return r.json() if r.content else None


def photo_creation(application):
    with application['engine'].connect() as db:
        return {t:db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY 1')).scalars().all()
                for t in ('societes','utilisateurs_societes','modules_actifs','comptes_societe',
                          'exercices_comptables','periodes_comptables','ecritures','lignes_ecriture')}


def test090_creation_seconde_societe_et_switch_api(application):
    api,_,_=client(application)
    try:
        principal=ok(api.get('/api/auth/me'))['societe_id']
        before=photo_creation(application)
        r=api.post('/api/societes/nouvelle',json={'raison_sociale':'Seconde société fictive090'})
        if r.status_code!=201:
            assert photo_creation(application)==before  # Audit HTTP distinct de ces tables.
        nouvelle=ok(r,201)['id']
        token=ok(api.post(f'/api/societes/switcher/{nouvelle}'))['access_token']
        api.headers['Authorization']='Bearer '+token
        assert ok(api.get('/api/auth/me'))['societe_id']==nouvelle
        assert ok(api.get('/api/societe/moi'))['id']==nouvelle
        assert {s['id'] for s in ok(api.get('/api/societes/mes-societes'))}=={principal,nouvelle}
        exercices=ok(api.get('/api/exercices'))
        assert len(exercices)==1 and exercices[0]['annee']==date.today().year
        with application['engine'].connect() as db:
            comptes=set(db.execute(text('SELECT numero FROM comptes_societe WHERE societe_id=:sid'),{'sid':nouvelle}).scalars())
            assert {'1111','5141','3421','4411'}<=comptes
            assert db.scalar(text('SELECT count(*) FROM periodes_comptables p JOIN exercices_comptables e '
                'ON e.id=p.exercice_id WHERE e.societe_id=:sid'),{'sid':nouvelle})==12
    finally:api.close()


def test090_invitation_changement_role_desactivation_et_suppression_secondaire(application):
    a,_,_=client(application);b,email_b,_=client(application)
    try:
        ua=ok(a.get('/api/auth/me'));ub=ok(b.get('/api/auth/me'))
        sid=ua['societe_id'];uid=ub['id'];principal_b=b.headers['Authorization']
        ok(a.post(f'/api/societes/{sid}/inviter',params={'email':email_b,'role':'lecture'}))
        secondaire='Bearer '+ok(b.post(f'/api/societes/switcher/{sid}'))['access_token']
        b.headers['Authorization']=secondaire
        assert ok(b.get('/api/auth/me'))['role']=='lecture'
        piece={'date':date.today().isoformat(),'journal':'BQ','reference':'ACCES090',
            'libelle':'Pièce fictive accès secondaire','lignes':[
                {'compte':'5141','debit':10},{'compte':'1111','credit':10}]}
        assert b.post('/api/ecritures',json=piece).status_code==403
        ok(a.patch(f'/api/utilisateurs/{uid}',json={'role':'comptable'}))
        assert ok(b.get('/api/auth/me'))['role']=='comptable'  # Ancien JWT, droits relus.
        ok(b.post('/api/ecritures',json=piece),201)
        assert a.patch(f'/api/utilisateurs/{uid}',json={'nom':'Profil personnel interdit'}).status_code==403
        ok(a.patch(f'/api/utilisateurs/{uid}',json={'actif':False}))
        assert b.get('/api/auth/me').status_code in {401,403}
        b.headers['Authorization']=principal_b
        assert ok(b.get('/api/auth/me'))['societe_id']==ub['societe_id']
        assert ok(b.get('/api/ecritures',params={'exercice':date.today().year}))==[]
        assert b.post(f'/api/societes/{sid}/inviter',params={'email':email_b,'role':'admin'}).status_code==403
        ok(a.post(f'/api/societes/{sid}/inviter',params={'email':email_b,'role':'lecture'}))
        assert a.delete(f'/api/utilisateurs/{uid}').status_code==204
        assert ok(b.get('/api/auth/me'))['societe_id']==ub['societe_id']
        assert b.post(f'/api/societes/switcher/{sid}').status_code==403
        assert a.patch(f"/api/utilisateurs/{ua['id']}",json={'role':'lecture'}).status_code==400
        with application['engine'].connect() as db:
            assert db.scalar(text('SELECT actif FROM utilisateurs WHERE id=:id'),{'id':uid}) is True
            assert db.scalar(text('SELECT count(*) FROM utilisateurs_societes WHERE utilisateur_id=:uid AND societe_id=:sid'),
                             {'uid':uid,'sid':sid})==0
    finally:a.close();b.close()


def test090_creation_switch_et_plan_dans_edge(application):
    from playwright.sync_api import sync_playwright,expect
    api,email,password=client(application)
    try:
        nom=ok(api.get('/api/societe/moi'))['raison_sociale']
        seconde='Société Edge fictive090 '+uuid.uuid4().hex[:6]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':1365,'height':1000});page.set_default_timeout(20000)
                erreurs,serveurs=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.get_by_role('button',name=nom,exact=True).click()
                page.get_by_role('button',name='Nouvelle société',exact=True).click()
                page.get_by_placeholder('Raison sociale *').fill(seconde)
                with page.expect_response(lambda r:r.url.endswith('/api/societes/nouvelle') and r.request.method=='POST') as creation:
                    page.get_by_role('button',name='Créer',exact=True).click()
                assert creation.value.status==201,creation.value.text()
                expect(page.get_by_role('button',name=seconde,exact=True)).to_be_visible()
                page.goto(application['web_url']+'/plan-comptes')
                expect(page.get_by_text('Capital social',exact=True)).to_be_visible()
                page.reload()
                expect(page.get_by_role('button',name=seconde,exact=True)).to_be_visible()
                assert not erreurs and not serveurs,(erreurs,serveurs)
            finally:browser.close()
    finally:api.close()


def test090_acl_identite_protegee_rejeu_et_autres_droits_inchanges(application):
    app=application;c=app['cluster']
    before,(table_before,seq_before)=app['avant090']
    after=catalogue_acl(app['engine']);table_after,seq_after=acl(app['engine'])
    assert seq_after==seq_before
    assert all(table_before[t]==table_after[t] for t in table_before if t!='utilisateurs_societes')
    assert table_after['utilisateurs_societes']=={'SELECT':True,'INSERT':True,'UPDATE':False,'DELETE':True,'TRUNCATE':False}
    for k in ('fonctions','schemas','defauts'):assert before[k]==after[k]
    assert [r for r in before['relations'] if r[1]!='utilisateurs_societes']==[r for r in after['relations'] if r[1]!='utilisateurs_societes']
    assert [r for r in before['colonnes'] if r[0]!='utilisateurs_societes']==[r for r in after['colonnes'] if r[0]!='utilisateurs_societes']
    runtime=create_engine(make_url(c['url']).set(username='hisabpro'))
    try:
        with runtime.connect() as db:
            for col in ('role','actif'):
                assert db.scalar(text("SELECT has_column_privilege(current_user,'utilisateurs_societes',:col,'UPDATE')"),{'col':col})
        for col in ('id','societe_id','utilisateur_id','created_at'):
            refuser(runtime,f'UPDATE utilisateurs_societes SET {col}={col}','42501')
        refuser(runtime,'TRUNCATE utilisateurs_societes','42501')
        refuser(runtime,'DELETE FROM utilisateurs WHERE false','42501')
        rows=empreintes_tables(app['engine'])
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute((BACK/SQL).read_text(encoding='utf-8'))
        finally:raw.close()
        assert empreintes_tables(app['engine'])==rows and catalogue_acl(app['engine'])==after
    finally:runtime.dispose()


def test090_restauration_avec_acl_colonnes_et_nouveau_cycle(annee_banque):
    scenario_restore(annee_banque)
    preuve=ROOT/'.codex-tests/restauration446_preuve.json'
    data=json.loads(preuve.read_text(encoding='utf-8'))
    assert data['erreur'] is None and data['acl']['colonnes']['nombre']==26
    shutil.copyfile(preuve,ROOT/'.codex-tests/restauration447_preuve.json')


def test090_role_absent_aucun_objet_cree():
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine=create_engine(c['url'])
        try:
            for _ in range(2):
                raw=engine.raw_connection()
                try:
                    raw.autocommit=True
                    with raw.cursor() as cur:cur.execute((BACK/SQL).read_text(encoding='utf-8'))
                finally:raw.close()
            with engine.connect() as db:
                assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
                assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace"))
        finally:engine.dispose()


def test090_installation_vierge_ordre_acl_et_conservation(tmp_path):
    from test_installation_vierge_084 import lancer
    d=lancer(['Test/recette_installation_vierge_090.py','--rapport'],tmp_path/'090.md')
    assert d['statut']=='81_SQL_et_17_rejeux_valides_runtime_cible_partiel'
    assert len(d['appliquees'])==98 and len({r['fichier'] for r in d['appliquees']})==81
    assert len(d['zero_final'])==36 and not any(d['zero_final'].values())
    assert d['090_schema_donnees_sequences_inchanges'] and d['090_acl_hors_liaisons_inchangees']
    assert {k for k,v in d['090_update_colonnes'].items() if v}=={'role','actif'}
    assert [r['fichier'] for r in d['appliquees'][-2:]]==[SQL,SQL]
