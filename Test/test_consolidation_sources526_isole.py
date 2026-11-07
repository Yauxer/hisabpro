"""Sources stock526 et oracles stock/Journal/clôture précédents, PG nonce."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_stock524_isole import (
    application as application524,application522,application520,application518,
    application514,application512,application510,application508,application506,
    application503,application501,application499,application497,application495,
    application493,application490,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,
)

for nom in ('test_consolidation_stock524_isole','test_stock_source_exercice_isole'):
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application524):
    chemins=[ROOT/'hisabpro-backend/services/stock_service.py',
        ROOT/'Test/test_stock_source_exercice_isole.py',Path(__file__)]
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application524
        assert sources()==avant;preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/sources526_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
