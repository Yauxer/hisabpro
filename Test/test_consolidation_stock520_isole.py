"""Validation/régénération520 et tous les oracles518, PostgreSQL isolé098."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_mouvements518_isole import (
    application as application518,application514,application512,application510,
    application508,application506,application503,application501,application499,
    application497,application495,application493,application490,application098,
    application097,application093,application092,application091,application090,
    application089,application087,migration,
)

for nom in ('test_consolidation_mouvements518_isole','test_stock_validation_journal_concurrente_isole'):
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application518):
    chemins=[ROOT/f for f in ('hisabpro-backend/routers/ecritures.py',
        'hisabpro-backend/services/stock_service.py',
        'Test/test_stock_validation_journal_concurrente_isole.py',
        'Test/test_patch06_stock_cloture.py','Test/test_patch07c2_numero_validation.py')]+[Path(__file__)]
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application518
        assert sources()==avant;preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/stock520_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
