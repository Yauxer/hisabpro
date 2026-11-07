"""Oracles499 et correction de clôture501 sur même schéma098 et PG nonce."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_reconciliations499_isole import (
    application as application499,application497,application495,application493,application490,application098,application097,
    application093,application092,application091,application090,application089,application087,migration,
)

MODULES=('test_consolidation_reconciliations499_isole','test_cloture_correction_amortissement_isole')
for nom in MODULES:
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v
ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application499):
    chemins=[ROOT/'hisabpro-backend/routers/cloture.py',Path(__file__),ROOT/'Test/test_cloture_correction_amortissement_isole.py']
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();p={'erreur':None,'sources':avant}
    try:
        yield application499
        assert sources()==avant;p['sources_inchangees']=True
    except BaseException as exc:p['erreur']=repr(exc);raise
    finally:(ROOT/'.codex-tests/cloture501_preuve.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
