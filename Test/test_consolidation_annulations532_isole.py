"""Annulations532 et qualification des règlements530, application nonce098."""
from pathlib import Path
import hashlib, importlib, json
import pytest
from test_consolidation_reglements530_isole import (
    application as application530, application528, application526, application524,
    application522, application520, application518, application514, application512,
    application510, application508, application506, application503, application501,
    application499, application497, application495, application493, application490,
    application098, application097, application093, application092, application091,
    application090, application089, application087, migration,
)

for nom in ('test_consolidation_reglements530_isole', 'test_reglement_annulation_source_isole'):
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            nom_test = 'test_annulation532_'+k[5:] if nom.endswith('source_isole') else k
            assert nom_test not in globals()
            globals()[nom_test] = v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application530):
    chemins=[ROOT/'hisabpro-backend/routers/commercial.py', Path(__file__),
        ROOT/'Test/test_reglement_annulation_source_isole.py']
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'erreur':None,'sources':avant}
    try:
        yield application530
        assert sources()==avant
        preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/annulations532_preuve.json').write_text(
            json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
