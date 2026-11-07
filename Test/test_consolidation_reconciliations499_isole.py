"""Oracles497 conservés et réconciliations499 sous PG nonce/LOGIN limité."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_registre497_isole import (
    application as application497,application495,application493,application490,application098,application097,
    application093,application092,application091,application090,application089,application087,migration,
)

MODULES=('test_consolidation_registre497_isole','test_reconciliations_concurrentes_isole')
for nom in MODULES:
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v
ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application497):
    chemins=[ROOT/'hisabpro-backend/routers/immobilisations.py',Path(__file__),ROOT/'Test/test_reconciliations_concurrentes_isole.py']
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();p={'erreur':None,'sources':avant}
    try:
        yield application497
        assert sources()==avant;p['sources_inchangees']=True
    except BaseException as exc:p['erreur']=repr(exc);raise
    finally:(ROOT/'.codex-tests/recon499_preuve.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
