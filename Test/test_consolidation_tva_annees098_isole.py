"""Oracles098 et bornes calendaires TVA, même application PG nonce."""
from pathlib import Path
import hashlib
import importlib
import json
import pytest
from test_consolidation_journal098_isole import (
    application as application490, application098, application097, application093,
    application092, application091, application090, application089, application087, migration,
)

MODULES=('test_consolidation_journal098_isole','test_tva_annees_isole')
for nom in MODULES:
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals(): assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application490):
    chemins=[ROOT/'hisabpro-backend/routers/tva.py',ROOT/'Test/test_tva_annees_isole.py',Path(__file__)]
    def sources():return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'erreur':None,'sources':avant}
    try:
        yield application490
        assert sources()==avant
        preuve['sources_inchangees']=True
    except BaseException as exc:preuve['erreur']=repr(exc);raise
    finally:(ROOT/'.codex-tests/tva491_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
