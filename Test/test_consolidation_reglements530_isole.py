"""Règlements530, annulations, RAS et banque sous PostgreSQL nonce098."""
from pathlib import Path
import hashlib
import importlib
import json

import pytest
from test_consolidation_contre528_isole import (
    application as application528, application526, application524, application522,
    application520, application518, application514, application512, application510,
    application508, application506, application503, application501, application499,
    application497, application495, application493, application490, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)
from test_restauration_runtime_acl_089 import catalogue_acl

for nom in ('test_consolidation_contre528_isole',):
    for k, v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            globals()[k] = v

MODULES = (
    'test_reglement_comptabilisation_concurrente_isole',
    'test_reglements_par_tiers_isole',
    'test_rapprochement_ventilation_isole',
    'test_ras_capture_reglement_postgres',
    'test_annulation_ventilation_isole',
    'test_e2e_annulation_rapprochement_ventilation_isole',
)
for index, nom in enumerate(MODULES):
    for k, v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            globals()[f'test_recette530_{index}_{k[5:]}'] = v

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application528):
    chemins = [ROOT/'hisabpro-backend/routers/commercial.py',
        ROOT/'hisabpro-backend/services/ras_reglement_service.py', Path(__file__),
        *(ROOT/'Test'/f'{nom}.py' for nom in MODULES)]
    def sources():
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in chemins}
    avant = sources()
    acl = catalogue_acl(application528['engine'])
    preuve = {'erreur': None, 'sources': avant}
    try:
        yield application528
        assert sources() == avant
        assert catalogue_acl(application528['engine']) == acl
        preuve['sources_et_acl_inchangees'] = True
    except BaseException as exc:
        preuve['erreur'] = repr(exc)
        raise
    finally:
        (ROOT/'.codex-tests/reglements530_preuve.json').write_text(
            json.dumps(preuve, ensure_ascii=False, indent=2), encoding='utf8')
