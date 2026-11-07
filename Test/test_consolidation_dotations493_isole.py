"""Courses et parcours immobilisations/factures/clôture sous LOGIN et schéma098."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_journal098_isole import (
    application as application490,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,
)

MODULES=('test_dotations_concurrentes_isole','test_e2e_immobilisations_isole',
 'test_e2e_immobilisations_sortie_isole','test_e2e_immobilisations_cession_differee_isole',
 'test_e2e_immobilisations_degressif_isole','test_e2e_cloture_isole','test_e2e_facturation_isole')
for nom in MODULES:
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v
ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application490):
    chemins=[ROOT/'hisabpro-backend/routers/immobilisations.py',Path(__file__),*(ROOT/'Test'/f'{m}.py' for m in MODULES)]
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();p={'erreur':None,'sources':avant}
    try:
        yield application490
        assert sources()==avant;p['sources_inchangees']=True
    except BaseException as exc:p['erreur']=repr(exc);raise
    finally:(ROOT/'.codex-tests/dotations493_preuve.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf8')
