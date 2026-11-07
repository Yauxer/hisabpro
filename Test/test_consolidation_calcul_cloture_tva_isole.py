"""Oracles097 conservés et trois courses pendant le calcul réel de clôture."""
from pathlib import Path
import hashlib,importlib,json
import pytest
from test_consolidation_tva097_isole import (
    application as application487,application097,application093,application092,
    application091,application090,application089,application087,migration,
)

MODULES=('test_consolidation_tva097_isole','test_tva_calcul_cloture_isole')
for nom in MODULES:
    mod=importlib.import_module(nom)
    for k,v in vars(mod).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application487):
    app=application487
    paths=[ROOT/'hisabpro-backend/routers/cloture.py',Path(__file__),ROOT/'Test/test_tva_calcul_cloture_isole.py',ROOT/'Test/test_restauration_tva097_isole.py']
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    avant=sources();preuve={'erreur':None,'sources':avant}
    try:
        yield app
        assert sources()==avant
        preuve['sources_inchangees']=True
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:(ROOT/'.codex-tests/calcul488_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
