"""Régressions501, reprises503 et historiques504 sur même schéma PG isolé."""
from pathlib import Path
import hashlib, importlib, json
import pytest
from test_consolidation_correction501_isole import (
    application as application501, application499, application497, application495,
    application493, application490, application098, application097, application093,
    application092, application091, application090, application089, application087,
    migration,
)

for nom in ('test_consolidation_correction501_isole',
            'test_reprise_ouverture_immobilisations_isole',
            'test_immobilisations_historiques_partiels_isole'):
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application501):
    chemins=[ROOT/f for f in (
        'hisabpro-backend/services/immobilisations_reconciliation_service.py',
        'hisabpro-backend/services/livre_inventaire_service.py',
        'hisabpro-backend/routers/cloture.py',
        'Test/test_reprise_ouverture_immobilisations_isole.py',
        'Test/test_immobilisations_historiques_partiels_isole.py',
    )]+[Path(__file__)]
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application501
        assert sources()==avant;preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/reprises503_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
