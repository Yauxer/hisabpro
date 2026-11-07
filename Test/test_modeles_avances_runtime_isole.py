"""Catalogue092 : vrais SQL/API/Edge, aucun bulletin ou donnée réelle."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright,expect
from test_e2e_runtime_session_isole import application as application091,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion,observer
from test_e2e_facturation_isole import champ
from browser_support import chromium_executable
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import empreintes_tables
from test_restauration_runtime_acl_089 import catalogue_acl
import models,schemas

SQL='092_modeles_avances_personnel.sql'
CODES=['paie_avance_banque','paie_avance_especes','paie_recuperation_avance',
       'paie_remboursement_avance_banque','paie_remboursement_avance_especes']
ATTENDUS=[('BQ',[('3431','debit'),('5141','credit')]),('CA',[('3431','debit'),('5161','credit')]),
          ('SA',[('4432','debit'),('3431','credit')]),('BQ',[('3431','credit'),('5141','debit')]),
          ('CA',[('3431','credit'),('5161','debit')])]


def test_api_accepte_les_journaux_saisissables_et_conserve_cl_reserve():
    assert {j.value for j in schemas.JournalEnum}=={j.value for j in models.JournalEnum}-{'CL'}
    assert schemas.JournalEnum('SA').value=='SA'


def appliquer(app):
    raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as c:c.execute((BACK/SQL).read_text(encoding='utf-8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application091):
    app=application091
    avant=empreintes_tables(app['engine']);droits=catalogue_acl(app['engine'])
    with app['engine'].connect() as db:
        anciens=db.execute(text('SELECT row_to_json(m)::text FROM modeles_ecritures m ORDER BY id')).scalars().all()
    assert len(anciens)==59
    appliquer(app)
    apres=empreintes_tables(app['engine'])
    assert {k:v for k,v in avant.items() if k not in {'modeles_ecritures','lignes_modele'}}=={
        k:v for k,v in apres.items() if k not in {'modeles_ecritures','lignes_modele'}}
    assert catalogue_acl(app['engine'])==droits
    with app['engine'].connect() as db:
        assert db.execute(text("SELECT row_to_json(m)::text FROM modeles_ecritures m WHERE code NOT LIKE 'paie_avance_%' AND code NOT LIKE 'paie_recuperation_%' AND code NOT LIKE 'paie_remboursement_%' ORDER BY id")).scalars().all()==anciens
    yield app


def test_migration_rejouee_catalogue_sequences_droits_inchanges(application):
    engine=application['engine'];avant=empreintes_tables(engine);droits=catalogue_acl(engine)
    def sequences():
        with engine.connect() as db:return db.execute(text("SELECT sequencename,last_value FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename")).all()
    seq=sequences()
    appliquer(application);appliquer(application)
    assert empreintes_tables(engine)==avant and sequences()==seq
    assert catalogue_acl(engine)==droits
    with engine.begin() as db:
        db.execute(text("UPDATE modeles_ecritures SET libelle='Personnalisé fictif',actif=FALSE WHERE code=:c"),{'c':CODES[0]})
    try:
        avant=empreintes_tables(engine);appliquer(application)
        assert empreintes_tables(engine)==avant
    finally:
        with engine.begin() as db:db.execute(text("UPDATE modeles_ecritures SET libelle='Avance au personnel — versement bancaire',actif=TRUE WHERE code=:c"),{'c':CODES[0]})


@pytest.mark.parametrize('index',range(5))
def test_cinq_modeles_complets_sans_tva_et_accessibles_au_runtime(application,index):
    with closing(client(application)[0]) as api:
        modeles={m['code']:m for m in ok(api.get('/api/modeles'))}
        assert len(modeles)==64
        m=modeles[CODES[index]];journal,lignes=ATTENDUS[index]
        assert m['journal']==journal
        assert [(l['compte'],l['sens']) for l in m['lignes']]==lignes
        assert sum(bool(l['est_principal']) for l in m['lignes'])==1
        assert all(not l['est_tva'] and l['taux_tva'] is None for l in m['lignes'])
        propositions=ok(api.get('/api/modeles/par-compte/'+m['compte_declencheur']))
        assert m['code'] in [p['code'] for p in propositions]


@pytest.mark.parametrize('largeur',[1440,390])
def test_detection_3431_choix_explicite_versement_et_remboursement(application,largeur):
    api,email,password=client(application)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
                errors,server_errors=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                for index,code in enumerate([CODES[0],CODES[3]]):
                    page.goto(application['web_url']+'/journal')
                    page.get_by_role('button',name='Nouvelle écriture',exact=True).click()
                    modal=page.get_by_role('dialog');rows=modal.locator('tbody tr')
                    with page.expect_response(lambda r:r.url.endswith('/api/modeles/par-compte/3431')):
                        rows.nth(0).get_by_placeholder('Ex: 6111').fill('3431')
                    expect(modal.get_by_text('Plusieurs modèles possibles',exact=True)).to_be_visible()
                    expect(modal.get_by_role('button',name='Appliquer',exact=True)).to_be_disabled()
                    select=modal.get_by_label('Opération comptable proposée')
                    expect(select).to_have_value('')
                    m=next(m for m in ok(api.get('/api/modeles')) if m['code']==code)
                    assert select.locator('option').count()==5
                    select.select_option(str(m['id']))
                    rows.nth(0).locator('td[data-label="Débit (MAD)"] input').fill('1000')
                    modal.get_by_role('button',name='Appliquer',exact=True).click()
                    expect(rows).to_have_count(3)
                    side='Débit' if index==0 else 'Crédit'
                    expect(rows.nth(0).locator(f'td[data-label="{side} (MAD)"] input')).to_have_value('1000.00')
                    champ(modal,'Référence du justificatif').fill(f'AVANCE-FICTIVE464-{index}')
                    modal.get_by_label('Valider immédiatement',exact=False).check()
                    with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/api/ecritures')) as saved:
                        modal.get_by_role('button',name="Enregistrer l'écriture",exact=True).click()
                    assert saved.value.status==201,saved.value.text()
                data=ok(api.get('/api/ecritures',params={'exercice':date.today().year}))
                lignes=[l for e in data for l in e['lignes']]
                assert len(data)==2 and len(lignes)==4
                assert sum(l['debit'] for l in lignes)==sum(l['credit'] for l in lignes)==2000
                assert sum(l['debit']-l['credit'] for l in lignes if l['compte']=='3431')==0
                assert sum(l['debit']-l['credit'] for l in lignes if l['compte']=='5141')==0
                assert all(e['est_validee'] for e in data)
                assert not errors,errors
                assert not server_errors,server_errors
            finally:browser.close()
    finally:api.close()


def test_cinq_schemas_dans_un_cycle_journal_solde_et_fec(application):
    with closing(client(application)[0]) as api:
        modeles={m['code']:m for m in ok(api.get('/api/modeles'))}
        def saisir(journal,lignes,ref):
            return ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':journal,
                'reference':ref,'libelle':'Recette fictive464 — aucun bulletin calculé','est_validee':True,
                'lignes':lignes}),201)
        # Soldes initiaux purement fictifs :13k banque,10k capital,3k rémunération
        # déjà due. Ceci n'est pas un calcul de salaire brut/net ni de cotisations.
        saisir('OD',[{'compte':'5141','debit':13000},{'compte':'1111','credit':10000},
                     {'compte':'4432','credit':3000}],'OUVERTURE-FICTIVE464')
        saisir('BQ',[{'compte':'5161','debit':1000},{'compte':'5141','credit':1000}],'CAISSE-FICTIVE464')
        for code,montant in zip(CODES,[1200,800,1500,200,300]):
            m=modeles[code]
            saisir(m['journal'],[{'compte':l['compte'],l['sens']:montant} for l in m['lignes']],code)
        m=modeles['virement_salaires']
        saisir(m['journal'],[{'compte':l['compte'],l['sens']:1500} for l in m['lignes']],'SOLDE-FICTIF464')
        data=ok(api.get('/api/ecritures',params={'exercice':date.today().year}))
        lignes=[l for e in data for l in e['lignes']]
        assert len(data)==8 and len(lignes)==17
        assert sum(l['debit'] for l in lignes)==sum(l['credit'] for l in lignes)==19500
        soldes={c:sum(l['debit']-l['credit'] for l in lignes if l['compte']==c) for c in ['3431','4432','5141','5161','1111']}
        assert soldes=={'3431':0,'4432':0,'5141':9500,'5161':500,'1111':-10000}
        assert not any(l['compte'].startswith(('6','7')) for l in lignes)
        r=api.get('/api/fec/export',params={'exercice':date.today().year})
        assert r.status_code==200,r.text
        assert len(r.text.splitlines())==18
