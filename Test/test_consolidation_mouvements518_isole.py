"""Mouvements518, clôtures/fiscalité et commerce/logos sous rôle LOGIN098."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_deficits514_isole import (
    application as application514,application512,application510,application508,
    application506,application503,application501,application499,application497,
    application495,application493,application490,application098,application097,
    application093,application092,application091,application090,application089,
    application087,migration,
)

MODULES=('test_consolidation_deficits514_isole',
    'test_mouvements_stock_cloture_isole','test_commerce_logos_runtime516_isole')
for nom in MODULES:
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application514):
    chemins=[ROOT/'hisabpro-backend/services/stock_movement_service.py',
        ROOT/'hisabpro-backend/services/exercice_verrou_service.py',
        ROOT/'Test/test_mouvements_stock_cloture_isole.py',
        ROOT/'Test/test_commerce_logos_runtime516_isole.py',Path(__file__)]+[
        ROOT/'Test'/f'{m}.py' for m in (
            'test_e2e_cycle_commercial_isole','test_e2e_cycle_achat_isole',
            'test_e2e_logo_societe_isole','test_e2e_logos_xlsx_isole',
            'test_e2e_logos_impression_isole','test_stock_integrite_mouvements',
            'test_patch06c_stock_engine','test_patch06b_stock_ledger')]
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application514
        assert sources()==avant;preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/mouvements518_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
