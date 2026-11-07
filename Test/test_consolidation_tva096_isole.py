"""Oracles existants inchangés, regroupés sous096 et LOGIN non propriétaire."""
from pathlib import Path
import hashlib
import importlib
import json
import pytest
from sqlalchemy import text
from test_tva_cloture_sql_concurrente_isole import (
    application as application096,application095,application093,application092,
    application091,application090,application089,application087,migration,
)
from test_restauration_runtime_acl_089 import catalogue_acl

MODULES=('test_tva_cloture_sql_concurrente_isole','test_protection_sql_tva_cloture_isole',
         'test_avances_salaries_isole','test_e2e_avances_acces_isole',
         'test_tva_parametres_creation_concurrente_isole','test_tva_parametres_montants')
for nom in MODULES:
    mod=importlib.import_module(nom)
    for k,v in vars(mod).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application096):
    app=application096
    paths=list((ROOT/'hisabpro-backend').glob('*.sql'))+[
        ROOT/'hisabpro-backend/routers/tva.py',Path(__file__),
        *(ROOT/'Test'/f'{m}.py' for m in MODULES)]
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    avant=sources();acl=catalogue_acl(app['engine'])
    with app['engine'].connect() as db:
        version=db.scalar(text('SHOW server_version'))
        isolation=db.scalar(text('SHOW transaction_isolation'))
        fonction=db.scalar(text("SELECT pg_get_functiondef('hisabpro_proteger_parametres_tva_clotures()'::regprocedure)"))
        assert 'FOR SHARE' in fonction and isolation=='read committed'
    preuve={'erreur':None,'version_postgresql':version,'isolation':isolation,'sources':avant}
    try:
        yield app
        with app['engine'].connect() as db:
            controles={
                'pieces_desequilibrees':db.scalar(text('SELECT count(*) FROM (SELECT ecriture_id FROM lignes_ecriture GROUP BY ecriture_id HAVING sum(debit)<>sum(credit)) q')),
                'montants_non_finis':db.scalar(text("SELECT count(*) FROM lignes_ecriture WHERE debit::text IN ('NaN','Infinity','-Infinity') OR credit::text IN ('NaN','Infinity','-Infinity')")),
                'definitives_sans_numero_date':db.scalar(text("SELECT count(*) FROM ecritures WHERE est_validee AND (numero_ecriture IS NULL OR date_validation IS NULL)")),
            }
            fonction_apres=db.scalar(text("SELECT pg_get_functiondef('hisabpro_proteger_parametres_tva_clotures()'::regprocedure)"))
        assert all(v==0 for v in controles.values()),controles
        assert sources()==avant and catalogue_acl(app['engine'])==acl and fonction_apres==fonction
        preuve.update(invariants=controles,source_acl_fonction_inchangees=True)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/consolidation485_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
