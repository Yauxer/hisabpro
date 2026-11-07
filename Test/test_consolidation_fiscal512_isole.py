"""Fiscalité512 et non-régressions précédentes sur PostgreSQL nonce."""
from pathlib import Path
import hashlib, importlib, json
import pytest
from test_consolidation_stock510_isole import (
    application as application510, application508, application506, application503,
    application501, application499, application497, application495, application493,
    application490, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)

for nom in ('test_consolidation_stock510_isole', 'test_fiscalite_concurrence_cloture_isole'):
    for k, v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():
                assert globals()[k] is v
            globals()[k] = v

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application510):
    chemins = [ROOT/'hisabpro-backend/routers/fiscalite.py',
        ROOT/'hisabpro-backend/services/exercice_verrou_service.py',
        ROOT/'Test/test_fiscalite_concurrence_cloture_isole.py', Path(__file__)]
    def sources():
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant = sources()
    preuve = {'sources': avant, 'erreur': None}
    try:
        yield application510
        assert sources() == avant
        preuve['sources_inchangees'] = True
    except BaseException as exc:
        preuve['erreur'] = repr(exc)
        raise
    finally:
        (ROOT/'.codex-tests/fiscal512_preuve.json').write_text(json.dumps(preuve, ensure_ascii=False, indent=2), encoding='utf8')
