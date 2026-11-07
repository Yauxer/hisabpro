"""Oracles095/096 et nouveaux conflits097, même PostgreSQL nonce limité."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from sqlalchemy import text
from test_tva_trace_concurrente_isole import (
    application as application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_restauration_runtime_acl_089 import catalogue_acl

MODULES=('test_consolidation_tva096_isole','test_tva_trace_concurrente_isole','test_conflits_tva_dependance_db')
for nom in MODULES:
    mod=importlib.import_module(nom)
    for k,v in vars(mod).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v
ROOT=Path(__file__).resolve().parents[1]
FONCTIONS=('hisabpro_proteger_parametres_tva_clotures','hisabpro_verrou_tva_cloture',
           'hisabpro_verrou_trace_tva','hisabpro_verrou_statut_tva')


def fonctions(engine):
    with engine.connect() as db:
        return db.execute(text('SELECT proname,pg_get_functiondef(oid) FROM pg_proc WHERE proname=ANY(:noms) ORDER BY proname'),{'noms':list(FONCTIONS)}).all()


@pytest.fixture(scope='module')
def application(application097):
    app=application097
    anciens=importlib.import_module('test_consolidation_tva096_isole').MODULES
    paths=list((ROOT/'hisabpro-backend').glob('*.sql'))+[
        ROOT/'hisabpro-backend/database.py',ROOT/'hisabpro-backend/routers/tva.py',Path(__file__),
        *(ROOT/'Test'/f'{m}.py' for m in (*MODULES,*anciens))]
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    avant=sources();acl=catalogue_acl(app['engine']);defs=fonctions(app['engine']);assert len(defs)==4
    with app['engine'].connect() as db:
        version=db.scalar(text('SHOW server_version'));isolation=db.scalar(text('SHOW transaction_isolation'))
        assert isolation=='read committed'
    preuve={'erreur':None,'sources':avant,'postgresql':version,'isolation':isolation}
    try:
        yield app
        with app['engine'].connect() as db:
            controles={
                'pieces_desequilibrees':db.scalar(text('SELECT count(*) FROM (SELECT ecriture_id FROM lignes_ecriture GROUP BY ecriture_id HAVING sum(debit)<>sum(credit)) q')),
                'montants_non_finis':db.scalar(text("SELECT count(*) FROM lignes_ecriture WHERE debit::text IN ('NaN','Infinity','-Infinity') OR credit::text IN ('NaN','Infinity','-Infinity')")),
                'definitives_sans_numero_date':db.scalar(text("SELECT count(*) FROM ecritures WHERE est_validee AND (numero_ecriture IS NULL OR date_validation IS NULL)")),
            }
        assert all(v==0 for v in controles.values())
        assert sources()==avant and catalogue_acl(app['engine'])==acl and fonctions(app['engine'])==defs
        preuve.update(invariants=controles,sources_acl_fonctions_inchangees=True)
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:(ROOT/'.codex-tests/consolidation487_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
