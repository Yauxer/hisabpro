"""Cycles et logos existants avec le rôle LOGIN non propriétaire et schéma098."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_deficits514_isole import (
    application as application514, application512, application510, application508,
    application506, application503, application501, application499, application497,
    application495, application493, application490, application098, application097,
    application093, application092, application091, application090, application089,
    application087, migration,
)

MODULES=('test_e2e_cycle_commercial_isole','test_e2e_cycle_achat_isole',
    'test_e2e_logo_societe_isole','test_e2e_logos_xlsx_isole',
    'test_e2e_logos_impression_isole')
for nom in MODULES:
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            assert k not in globals()
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application514):
    fichiers=[ROOT/'Test'/f'{m}.py' for m in MODULES]+[Path(__file__),
        ROOT/'hisabpro-backend/routers/fiscalite.py',
        ROOT/'hisabpro-backend/routers/cloture.py',
        ROOT/'hisabpro-backend/services/exercice_verrou_service.py']
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in fichiers}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application514
        assert sources()==avant;preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/commerce516_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
