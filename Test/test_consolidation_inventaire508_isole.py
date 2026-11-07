"""Comptages/clôture508 et non-régressions précédentes, PostgreSQL nonce réel."""
from pathlib import Path
import hashlib, importlib, json
import pytest
from test_consolidation_deux_clotures506_isole import (
    application as application506, application503, application501, application499,
    application497, application495, application493, application490, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)

for nom in ('test_consolidation_deux_clotures506_isole',
            'test_inventaire_cloture_concurrente_isole',
            'test_e2e_inventaire_nombres_isole'):
    for k,v in vars(importlib.import_module(nom)).items():
        if k.startswith('test_') and callable(v):
            if k in globals():assert globals()[k] is v
            globals()[k]=v

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application506):
    chemins=[ROOT/f for f in ('hisabpro-backend/routers/inventaire.py',
        'hisabpro-backend/services/exercice_verrou_service.py',
        'Test/test_inventaire_cloture_concurrente_isole.py',
        'Test/test_e2e_inventaire_nombres_isole.py',
        'Test/test_inventaire_comptage_complet.py',
        'Test/test_inventaire_nombres_historique_postgres.py')]+[Path(__file__)]
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in chemins}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application506
        assert sources()==avant;preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/inventaire508_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
