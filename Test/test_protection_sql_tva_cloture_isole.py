"""Paramètres TVA clôturés : refus SQL natifs, sans réparer les données."""
from contextlib import closing,contextmanager
from datetime import date
from pathlib import Path
import hashlib,json
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from test_permissions_tva_runtime_isole import (
    application as application093,application092,application091,application090,application089,application087,migration,
    donnees_metier,
    test_creation_update_et_isolation_api,test_droits_sql_colonnes_et_refus_identites_suppression,
    test_exercice_cloture_refuse_modification_sans_mutation,
    test_factures_paiements_partiels_periodes_et_parametres_tva_ui,
    test_lecture_consulte_et_imprime_sans_modifier_parametres_tva,
)
from test_tva_verrou_exercice_isole import (
    test_parametres_attendent_confirmation_ou_annulation_du_statut,
    test_statut_attend_fin_de_sauvegarde_parametres_deja_en_cours,
)
from test_e2e_cloture_isole import test_cloture_controles_AN_auxiliaires_et_verrouillage_ui_reels
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from recette_restauration_consolidee_084 import empreintes_tables,schema,verifier_schema
from test_restauration_runtime_acl_089 import catalogue_acl

ROOT=Path(__file__).resolve().parents[1]
SQL=ROOT/'hisabpro-backend/094_protection_parametres_tva_clotures.sql'


@pytest.fixture(scope='module')
def application(application093):
    app=application093;avant=empreintes_tables(app['engine']);avant_droits=catalogue_acl(app['engine'])
    empreinte=hashlib.sha256(SQL.read_bytes()).hexdigest()
    def appliquer():
        raw=app['engine'].raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:cur.execute(SQL.read_text(encoding='utf8'))
        finally:raw.close()
    appliquer()
    assert empreintes_tables(app['engine'])==avant
    droits=catalogue_acl(app['engine']);structure=schema(app['engine'])
    # Aucun ancien objet/ACL n'est remplacé : deux fonctions et un trigger nouveaux.
    for categorie,items in avant_droits.items():
        assert all(item in droits[categorie] for item in items),categorie
    appliquer()
    assert empreintes_tables(app['engine'])==avant and catalogue_acl(app['engine'])==droits
    verifier_schema(schema(app['engine']),structure)
    preuve={'migration_sha256':empreinte,'donnees_initiales_et_rejeu_inchanges':True,
            'anciennes_acl_conservees':True,'rejeu_schema_acl_stable':True}
    try:
        yield app
        assert catalogue_acl(app['engine'])==droits
        assert hashlib.sha256(SQL.read_bytes()).hexdigest()==empreinte
        preuve['acl_apres_tests_inchangees']=True
    finally:
        (ROOT/'.codex-tests/protection480_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')


@contextmanager
def moteur(app,role):
    engine=app['engine'] if role=='proprietaire' else create_engine(make_url(app['cluster']['url']).set(username='hisabpro'))
    try:yield engine
    finally:
        if role!='proprietaire':engine.dispose()


def societe(app,api,*,parametres=True,cloture=True):
    sid=ok(api.get('/api/societe/moi'))['id'];annee=date.today().year
    if parametres:ok(api.put(f'/api/tva/parametres/{annee}',json={'credit_ouverture':20,'prorata_deduction_pct':80}))
    if cloture:
        with app['engine'].begin() as db:
            assert db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:s AND annee=:e"),{'s':sid,'e':annee}).rowcount==1
    return {'s':sid,'e':annee}


def refuser_sql(app,engine,sql,params):
    avant=donnees_metier(app)
    with pytest.raises(DBAPIError) as erreur:
        with engine.begin() as db:db.execute(text(sql),params)
    assert erreur.value.orig.pgcode=='23514'
    assert erreur.value.orig.diag.constraint_name=='ck_tva_parametres_exercice_ouvert'
    assert donnees_metier(app)==avant


@pytest.mark.parametrize('role',['runtime','proprietaire'])
@pytest.mark.parametrize('colonne',['credit_ouverture','prorata_deduction_pct'])
def test_sql_update_cloture_refuse_et_original_conserve(application,role,colonne):
    with closing(client(application)[0]) as api,moteur(application,role) as engine:
        p=societe(application,api)
        refuser_sql(application,engine,f'UPDATE tva_parametres_exercice SET {colonne}=10 WHERE societe_id=:s AND exercice=:e',p)


@pytest.mark.parametrize('role',['runtime','proprietaire'])
def test_sql_insert_cloture_refuse(application,role):
    with closing(client(application)[0]) as api,moteur(application,role) as engine:
        p=societe(application,api,parametres=False)
        refuser_sql(application,engine,'INSERT INTO tva_parametres_exercice(societe_id,exercice,credit_ouverture,prorata_deduction_pct) VALUES(:s,:e,20,80)',p)


@pytest.mark.parametrize('direction',['depuis_cloture','vers_cloture'])
def test_sql_deplacement_ligne_cloturee_refuse(application,direction):
    with closing(client(application)[0]) as ferme,closing(client(application)[0]) as ouvert:
        f=societe(application,ferme);o=societe(application,ouvert,parametres=False,cloture=False)
        if direction=='vers_cloture':
            # Le compte source reste ouvert ; c'est la destination clôturée qui bloque.
            with application['engine'].begin() as db:
                db.execute(text('INSERT INTO tva_parametres_exercice(societe_id,exercice,credit_ouverture,prorata_deduction_pct) VALUES(:s,:e,20,80)'),o)
            # Autre exercice clôturé sans ligne TVA, pour éviter le doublon UNIQUE.
            cible=f['e']-1
            with application['engine'].begin() as db:
                db.execute(text("INSERT INTO exercices_comptables(societe_id,annee,date_debut,date_fin,statut) VALUES(:s,:e,:d,:f,'cloture')"),
                           {'s':f['s'],'e':cible,'d':date(cible,1,1),'f':date(cible,12,31)})
            params={'s':o['s'],'e':o['e'],'cible':f['s'],'annee':cible}
        else:params={**f,'cible':o['s'],'annee':o['e']}
        refuser_sql(application,application['engine'],
            'UPDATE tva_parametres_exercice SET societe_id=:cible,exercice=:annee WHERE societe_id=:s AND exercice=:e',params)


def test_sql_delete_cloture_refuse_meme_proprietaire(application):
    with closing(client(application)[0]) as api:
        p=societe(application,api)
        refuser_sql(application,application['engine'],'DELETE FROM tva_parametres_exercice WHERE societe_id=:s AND exercice=:e',p)


@pytest.mark.parametrize('role',['runtime','proprietaire'])
def test_sql_exercice_ouvert_reste_modifiable(application,role):
    with closing(client(application)[0]) as api,moteur(application,role) as engine:
        p=societe(application,api,cloture=False)
        with engine.begin() as db:
            assert db.execute(text('UPDATE tva_parametres_exercice SET credit_ouverture=30,prorata_deduction_pct=85 WHERE societe_id=:s AND exercice=:e'),p).rowcount==1
        valeurs=ok(api.get(f'/api/tva/parametres/{p["e"]}'))
        assert (valeurs['credit_ouverture'],valeurs['prorata_deduction_pct'])==(30,85)


def test_sql_trace_cloture_seule_sans_exercice_comptable(application):
    with closing(client(application)[0]) as api,moteur(application,'runtime') as engine:
        sid=ok(api.get('/api/societe/moi'))['id'];annee=date.today().year-1
        with application['engine'].begin() as db:
            assert db.scalar(text('SELECT count(*) FROM exercices_comptables WHERE societe_id=:s AND annee=:e'),{'s':sid,'e':annee})==0
            # Simulation explicite d'une trace historique dans le laboratoire,
            # sans fabriquer d'écriture ni désactiver une contrainte.
            db.execute(text('INSERT INTO clotures_exercice(societe_id,exercice,resultat_net) VALUES(:s,:e,0)'),{'s':sid,'e':annee})
        refuser_sql(application,engine,
            'INSERT INTO tva_parametres_exercice(societe_id,exercice,credit_ouverture,prorata_deduction_pct) VALUES(:s,:e,20,80)',
            {'s':sid,'e':annee})


def test_sql_fonctions_invoker_et_execution_explicitement_accordee(application):
    with application['engine'].connect() as db:
        for nom in ('hisabpro_tva_exercice_clos','hisabpro_proteger_parametres_tva_clotures'):
            assert db.scalar(text("SELECT count(*) FROM information_schema.routine_privileges WHERE routine_schema='public' AND routine_name=:n AND grantee='hisabpro' AND privilege_type='EXECUTE'"),{'n':nom})==1
            assert db.scalar(text("SELECT p.prosecdef FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname=:nom"),{'nom':nom}) is False
