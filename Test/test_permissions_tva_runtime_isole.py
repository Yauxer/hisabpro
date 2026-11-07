"""Migration093 et API TVA, PostgreSQL nonce sous LOGIN non propriétaire."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from test_modeles_avances_runtime_isole import application as application092,application091,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from recette_installation_vierge import BACK
from recette_restauration_consolidee_084 import empreintes_tables,schema,verifier_schema
from test_restauration_runtime_acl_089 import catalogue_acl
from test_complements_structure_postgres import refuser
from test_e2e_tva_isole import (
    test_factures_paiements_partiels_periodes_et_parametres_tva_ui,
    test_lecture_consulte_et_imprime_sans_modifier_parametres_tva,
)

SQL='093_permissions_parametres_tva.sql'


def donnees_metier(app):
    return {k:v for k,v in empreintes_tables(app['engine']).items() if k!='audit_actions'}


def audit(app):
    with app['engine'].connect() as db:
        return db.execute(text('SELECT row_to_json(a)::text FROM audit_actions a ORDER BY id')).scalars().all()


def appliquer(app):
    raw=app['engine'].raw_connection()
    try:
        raw.autocommit=True
        with raw.cursor() as c:c.execute((BACK/SQL).read_text(encoding='utf-8'))
    finally:raw.close()


@pytest.fixture(scope='module')
def application(application092):
    app=application092
    with closing(client(app)[0]) as api:
        # Reproduction HTTP native, sans dépendre du CORS/timeout navigateur.
        r=api.put(f'/api/tva/parametres/{date.today().year}',json={'credit_ouverture':20,'prorata_deduction_pct':80})
        assert r.status_code==500,r.text
    avant=empreintes_tables(app['engine']);structure=schema(app['engine'])
    appliquer(app)
    assert empreintes_tables(app['engine'])==avant
    verifier_schema(schema(app['engine']),structure)
    droits=catalogue_acl(app['engine'])
    appliquer(app)
    assert catalogue_acl(app['engine'])==droits and empreintes_tables(app['engine'])==avant
    yield app


def test_creation_update_et_isolation_api(application):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        path=f'/api/tva/parametres/{date.today().year}'
        for credit,prorata in [(20,80),(30,85)]:
            data=ok(api.put(path,json={'credit_ouverture':credit,'prorata_deduction_pct':prorata}))
            assert data['credit_ouverture']==credit and data['prorata_deduction_pct']==prorata
        assert ok(autre.get(path))['credit_ouverture']==0
        assert ok(api.get(path))['credit_ouverture']==30
        avant=donnees_metier(application);trace=audit(application)
        assert api.put(path,json={'credit_ouverture':0,'prorata_deduction_pct':101}).status_code==422
        assert donnees_metier(application)==avant
        apres=audit(application);assert len(apres)==len(trace)+1 and apres[:-1]==trace


def test_droits_sql_colonnes_et_refus_identites_suppression(application):
    runtime=create_engine(make_url(application['cluster']['url']).set(username='hisabpro'))
    try:
        with runtime.connect() as db:
            for droit in ('SELECT','INSERT'):assert db.scalar(text("SELECT has_table_privilege(current_user,'public.tva_parametres_exercice',:d)"),{'d':droit})
            for droit in ('UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER'):
                assert not db.scalar(text("SELECT has_table_privilege(current_user,'public.tva_parametres_exercice',:d)"),{'d':droit})
            for colonne in ('credit_ouverture','prorata_deduction_pct','updated_at'):
                assert db.scalar(text("SELECT has_column_privilege(current_user,'public.tva_parametres_exercice',:c,'UPDATE')"),{'c':colonne})
            for droit in ('USAGE','SELECT'):
                assert db.scalar(text("SELECT has_sequence_privilege(current_user,pg_get_serial_sequence('public.tva_parametres_exercice','id'),:d)"),{'d':droit})
            assert not db.scalar(text("SELECT has_sequence_privilege(current_user,pg_get_serial_sequence('public.tva_parametres_exercice','id'),'UPDATE')"))
        for colonne in ('id','societe_id','exercice'):
            refuser(runtime,f'UPDATE tva_parametres_exercice SET {colonne}={colonne}','42501')
        refuser(runtime,'DELETE FROM tva_parametres_exercice','42501')
        refuser(runtime,'TRUNCATE tva_parametres_exercice','42501')
    finally:runtime.dispose()


def test_exercice_cloture_refuse_modification_sans_mutation(application):
    with closing(client(application)[0]) as api:
        societe=ok(api.get('/api/societe/moi'));ex=date.today().year
        path=f'/api/tva/parametres/{ex}'
        ok(api.put(path,json={'credit_ouverture':20,'prorata_deduction_pct':80}))
        with application['engine'].begin() as db:
            db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:sid AND annee=:e"),{'sid':societe['id'],'e':ex})
        avant=donnees_metier(application);trace=audit(application)
        r=api.put(path,json={'credit_ouverture':999,'prorata_deduction_pct':10})
        assert r.status_code==409,r.text
        assert donnees_metier(application)==avant
        apres=audit(application);assert len(apres)==len(trace)+1 and apres[:-1]==trace
        assert ok(api.get(path))['credit_ouverture']==20
