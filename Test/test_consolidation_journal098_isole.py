"""Oracles TVA, avances, ventes/achats et clôture inchangés sous098."""
from pathlib import Path
import hashlib
import importlib
import json
import pytest
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application as application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)
from test_restauration_runtime_acl_089 import catalogue_acl

MODULES = ('test_consolidation_calcul_cloture_tva_isole',
           'test_journal_cloture_concurrente_isole',
           'test_e2e_facturation_isole', 'test_e2e_cloture_isole')
for nom in MODULES:
    for k, v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals(): assert globals()[k] is v
            globals()[k] = v

ROOT = Path(__file__).resolve().parents[1]
NOMS = ['hisabpro_verifier_journal_ouvert', 'hisabpro_verrou_entete_journal', 'hisabpro_verrou_lignes_journal']


def fonctions098(engine):
    with engine.connect() as db:
        return db.execute(text('SELECT proname,pg_get_functiondef(oid) FROM pg_proc WHERE proname=ANY(:noms) ORDER BY proname'), {'noms':NOMS}).all()


@pytest.fixture(scope='module')
def application(application098):
    app = application098
    chemins = list((ROOT/'hisabpro-backend').glob('*.sql')) + [
        ROOT/'hisabpro-backend/database.py', ROOT/'hisabpro-backend/routers/cloture.py',
        ROOT/'hisabpro-backend/routers/ecritures.py', Path(__file__),
        *(ROOT/'Test'/f'{n}.py' for n in MODULES)]
    def sources(): return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant = sources(); acl = catalogue_acl(app['engine']); fonctions = fonctions098(app['engine'])
    assert len(fonctions)==3
    with app['engine'].connect() as db:
        version = db.scalar(text('SHOW server_version')); isolation = db.scalar(text('SHOW transaction_isolation'))
        assert isolation=='read committed'
    preuve = {'erreur':None,'sources':avant,'postgresql':version,'isolation':isolation}
    try:
        yield app
        with app['engine'].connect() as db:
            controles = {
                'pieces_desequilibrees':db.scalar(text('SELECT count(*) FROM (SELECT ecriture_id FROM lignes_ecriture GROUP BY ecriture_id HAVING sum(debit)<>sum(credit)) q')),
                'montants_non_finis':db.scalar(text("SELECT count(*) FROM lignes_ecriture WHERE debit::text IN ('NaN','Infinity','-Infinity') OR credit::text IN ('NaN','Infinity','-Infinity')")),
                'definitives_sans_numero_date':db.scalar(text('SELECT count(*) FROM ecritures WHERE est_validee AND (numero_ecriture IS NULL OR date_validation IS NULL)')),
            }
        assert all(v==0 for v in controles.values()), controles
        assert sources()==avant and catalogue_acl(app['engine'])==acl and fonctions098(app['engine'])==fonctions
        preuve.update(invariants=controles,sources_acl_fonctions_inchangees=True)
    except BaseException as exc: preuve['erreur']=repr(exc); raise
    finally: (ROOT/'.codex-tests/consolidation490_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
