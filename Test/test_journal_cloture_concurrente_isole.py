"""Journal/clôture : transactions PostgreSQL nonce et API réelle, aucun mock métier."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_tva_trace_concurrente_isole import (
    application as application097, application093, application092, application091,
    application090, application089, application087, migration, moteur,
)
from test_avances_salaries_isole import appliquer, originaux
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_restauration_runtime_acl_089 import catalogue_acl
from recette_restauration_consolidee_084 import empreintes_tables
from recette_installation_vierge import BACK
from test_tva_verrou_exercice_isole import attendre_verrou
from test_tva_calcul_cloture_isole import dossier

SQL = '098_verrou_journal_cloture.sql'
VERROU = 'SELECT public.hisabpro_verrou_tva_cloture(:s,:a,true)'


@pytest.fixture(scope='module')
def application(application097):
    app = application097
    if (BACK / SQL).exists():
        avant = empreintes_tables(app['engine']); acl = catalogue_acl(app['engine'])
        appliquer(app, SQL)
        assert empreintes_tables(app['engine']) == avant
        apres = catalogue_acl(app['engine'])
        assert all(all(v in apres[k] for v in vs) for k, vs in acl.items())
        appliquer(app, SQL)
        assert empreintes_tables(app['engine']) == avant and catalogue_acl(app['engine']) == apres
    yield app


def piece(api, annee=None, valide=False):
    return ok(api.post('/api/ecritures', json=donnees(annee, valide)), 201)


def donnees(annee=None, valide=False):
    return {'date':f'{annee or date.today().year}-12-31', 'journal':'OD',
            'libelle':'Écriture fictive concurrence490', 'reference':'FICTIF490',
            'est_validee':valide,
            'lignes':[{'compte':'5141','debit':10}, {'compte':'1111','credit':10}]}


MUTATIONS = {
    'creation_entete':"INSERT INTO ecritures(societe_id,exercice,date,journal,libelle,est_validee) VALUES(:s,:a,make_date(:a,12,31),'OD','Création fictive490',false)",
    'entete':"UPDATE ecritures SET libelle='Mutation fictive490' WHERE id=:id",
    'suppression':'DELETE FROM ecritures WHERE id=:id',
    'validation':"UPDATE ecritures SET est_validee=true,date_validation=now() WHERE id=:id",
    'ajout_ligne':"INSERT INTO lignes_ecriture(ecriture_id,compte,debit,credit) VALUES(:id,'5141',1,0)",
    'modification_ligne':"UPDATE lignes_ecriture SET libelle='Mutation fictive490' WHERE id=:ligne",
    'suppression_ligne':'DELETE FROM lignes_ecriture WHERE id=:ligne',
}


def executer_annule(engine, sql, valeurs):
    """Même une opération autorisée dans le banc ne laisse aucune mutation."""
    with engine.connect() as db:
        tx = db.begin()
        try:
            db.execute(text(sql), valeurs)
            return 'ok'
        except DBAPIError as exc:
            return exc.orig.pgcode
        finally:
            tx.rollback()


@pytest.mark.parametrize('operation', list(MUTATIONS))
def test_cloture_en_cours_refuse_mutations_sql_du_journal(application, operation):
    with closing(client(application)[0]) as api:
        e = piece(api); p = {'s':ok(api.get('/api/societe/moi'))['id'], 'a':date.today().year,
                             'id':e['id'], 'ligne':e['lignes'][0]['id']}
        avant = originaux(application, p['s']); engine = moteur(application)
        try:
            with application['engine'].connect() as db:
                tx = db.begin()
                try:
                    db.execute(text(VERROU), p)
                    assert executer_annule(engine, MUTATIONS[operation], p) == '40001'
                finally: tx.rollback()
            assert executer_annule(engine, MUTATIONS[operation], p) == 'ok'
            assert originaux(application, p['s']) == avant
        finally: engine.dispose()


@pytest.mark.parametrize('operation', ['creation','validation','modification','suppression'])
def test_cloture_en_cours_refuse_api409_et_reprise(application, operation):
    with closing(client(application)[0]) as api:
        e = piece(api); sid = ok(api.get('/api/societe/moi'))['id']
        avant = originaux(application, sid)
        def appel():
            if operation == 'creation': return api.post('/api/ecritures', json=donnees())
            if operation == 'validation': return api.post(f"/api/ecritures/{e['id']}/valider")
            if operation == 'modification': return api.patch(f"/api/ecritures/{e['id']}", json={'libelle':'Modification fictive490'})
            return api.delete(f"/api/ecritures/{e['id']}")
        with application['engine'].connect() as db:
            tx = db.begin()
            try:
                db.execute(text(VERROU), {'s':sid, 'a':date.today().year})
                r = appel(); assert r.status_code == 409, r.text
                assert originaux(application, sid) == avant
            finally: tx.rollback()
        r = appel(); assert r.status_code == {'creation':201,'validation':200,'modification':200,'suppression':204}[operation], r.text


@pytest.mark.parametrize('operation', list(MUTATIONS))
def test_mutation_en_cours_refuse_trace_et_cloture_api(application, operation):
    with closing(client(application)[0]) as api:
        e = piece(api); p = {'s':ok(api.get('/api/societe/moi'))['id'], 'a':date.today().year,
                             'id':e['id'], 'ligne':e['lignes'][0]['id']}
        engine = moteur(application)
        try:
            with engine.connect() as db:
                tx = db.begin()
                try:
                    db.execute(text(MUTATIONS[operation]), p)
                    assert executer_annule(application['engine'], VERROU, p) == '40001'
                    r = api.post(f"/api/cloture/cloturer?exercice={p['a']}")
                    assert r.status_code == 409, r.text
                finally: tx.rollback()
            assert executer_annule(application['engine'], VERROU, p) == 'ok'
        finally: engine.dispose()


def test_calcul_reel_cloture_refuse_creation_journal_puis_termine(application):
    with closing(client(application)[0]) as api:
        api.timeout = 20; p, _ = dossier(api); avant = originaux(application, p['s'])
        db = application['engine'].connect(); tx = db.begin(); pool = ThreadPoolExecutor(1)
        try:
            db.execute(text('LOCK TABLE immobilisations IN ACCESS EXCLUSIVE MODE'))
            f = pool.submit(api.post, f"/api/cloture/cloturer?exercice={p['a']}")
            attendre_verrou(application, f, table='immobilisations')
            r = api.post('/api/ecritures', json=donnees(p['a'], True))
            assert r.status_code == 409, r.text
            tx.rollback(); r = f.result(timeout=20)
            assert r.status_code == 200 and r.json()['resultat_net'] == -3000, r.text
        finally:
            if tx.is_active: tx.rollback()
            db.close(); pool.shutdown(wait=True)
        apres = originaux(application, p['s'])
        for table, lignes in avant.items(): assert all(l in apres[table] for l in lignes)
        assert api.get('/api/fec/export', params={'exercice':p['a']}).status_code == 200


@pytest.mark.parametrize('mouvement', ['entete_exercice','entete_societe','ligne_exercice','ligne_societe'])
@pytest.mark.parametrize('cote', ['ancien','nouveau'])
def test_deplacement_protege_les_deux_perimetres(application, mouvement, cote):
    with closing(client(application)[0]) as a, closing(client(application)[0]) as b:
        annee = date.today().year
        ok(a.post('/api/exercices', json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-12-31'}), 201)
        e = piece(a)
        cible = b if mouvement.endswith('societe') else a
        nouvelle_annee = annee if cible is b else annee-1
        autre = piece(cible, nouvelle_annee)
        sid = ok(a.get('/api/societe/moi'))['id']; sid_cible = ok(cible.get('/api/societe/moi'))['id']
        p = {'s':sid if cote=='ancien' else sid_cible, 'a':annee if cote=='ancien' else nouvelle_annee,
             'id':e['id'], 'ligne':e['lignes'][0]['id'], 'cible':autre['id'], 'sid':sid_cible,
             'annee':nouvelle_annee, 'jour':date(nouvelle_annee,12,31)}
        sql = ('UPDATE ecritures SET societe_id=:sid,exercice=:annee,date=:jour WHERE id=:id'
               if mouvement.startswith('entete') else 'UPDATE lignes_ecriture SET ecriture_id=:cible WHERE id=:ligne')
        engine = moteur(application)
        try:
            with application['engine'].connect() as db:
                tx = db.begin()
                try:
                    db.execute(text(VERROU), p)
                    assert executer_annule(engine, sql, p) == '40001'
                finally: tx.rollback()
            assert executer_annule(engine, sql, p) == 'ok'
        finally: engine.dispose()


def test_perimetres_independants_et_definitives_intangibles(application):
    with closing(client(application)[0]) as a, closing(client(application)[0]) as b:
        annee = date.today().year; e = piece(a, valide=True)
        sid = ok(a.get('/api/societe/moi'))['id']; avant = originaux(application, sid)
        ok(a.post('/api/exercices', json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-12-31'}), 201)
        with application['engine'].connect() as db:
            tx = db.begin()
            try:
                db.execute(text(VERROU), {'s':sid,'a':annee})
                piece(b); piece(a, annee-1)
            finally: tx.rollback()
        # Le nouveau verrou ne remplace ni les protections072 ni l'intangibilité.
        p = {'id':e['id'],'ligne':e['lignes'][0]['id']}
        engine = moteur(application)
        try:
            for nom, sql in MUTATIONS.items():
                if nom!='creation_entete': assert executer_annule(engine, sql, p) == '23514'
        finally: engine.dispose()
        apres = originaux(application, sid)
        for table, lignes in avant.items(): assert all(l in apres[table] for l in lignes)


@pytest.mark.parametrize('present', [False,True])
def test_trace_confirmee_verrouille_journal_meme_sans_exercice(application, present):
    with closing(client(application)[0]) as api:
        annee = date.today().year-(0 if present else 2)
        p = {'s':ok(api.get('/api/societe/moi'))['id'],'a':annee,'d':date(annee,12,31)}
        sql = "INSERT INTO ecritures(societe_id,exercice,date,journal,libelle,est_validee) VALUES(:s,:a,:d,'OD','Fictif490',false)"
        engine = moteur(application)
        try:
            assert executer_annule(engine, sql, p) == 'ok'
            with application['engine'].begin() as db:
                db.execute(text('INSERT INTO clotures_exercice(societe_id,exercice,resultat_net) VALUES(:s,:a,0)'), p)
            assert executer_annule(engine, sql, p) == '23514'
            if not present:
                with application['engine'].connect() as db:
                    assert db.scalar(text('SELECT count(*) FROM exercices_comptables WHERE societe_id=:s AND annee=:a'),p)==0
        finally: engine.dispose()


def test_droits_fonctions_sans_elevation_et_sans_truncate(application):
    with application['engine'].connect() as db:
        lignes = db.execute(text("SELECT proname,prosecdef,proconfig,has_function_privilege('hisabpro',oid,'EXECUTE') FROM pg_proc WHERE proname IN ('hisabpro_verifier_journal_ouvert','hisabpro_verrou_entete_journal','hisabpro_verrou_lignes_journal')")).all()
        assert len(lignes)==3
        assert all(not defin and config==['search_path=pg_catalog, public, pg_temp'] and droit for _,defin,config,droit in lignes)
        for table in ['ecritures','lignes_ecriture']:
            assert not db.scalar(text("SELECT has_table_privilege('hisabpro',:t,'TRUNCATE')"),{'t':table})
