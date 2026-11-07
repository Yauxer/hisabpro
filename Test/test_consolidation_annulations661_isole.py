"""Consolidation portable : lectures des baselines privées explicitement interdites."""
from pathlib import Path
import importlib,json
import pytest
import test_consolidation_ras_documents651_isole as precedent
from test_consolidation_ras_documents651_isole import (
    application102, application101, application100, application099, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)
from test_e2e_facturation_isole import application as application_absente


@pytest.fixture(scope='module')
def application(application102):
    root = Path(__file__).resolve().parents[1]
    interdits = {root/'.codex-tests/baseline645.json', root/'.codex-tests/cumul649_preuve.json'}
    lire = Path.read_text
    def lecture_sans_prives(path, *args, **kwargs):
        if path.resolve() in interdits:
            raise FileNotFoundError('Le banc livré doit fonctionner sans baselines privées : '+path.name)
        return lire(path, *args, **kwargs)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, 'read_text', lecture_sans_prives)
        banc = precedent.application.__wrapped__(application102)
        demarre = False
        try:
            app = next(banc)
            demarre = True
            yield app
        finally:
            banc.close()
            if demarre:
                preuve = json.loads((root/'.codex-tests/consolidation651_preuve.json').read_text(encoding='utf8'))
                preuve['lectures_baselines_privees_interdites'] = True
                (root/'.codex-tests/consolidation661_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')


MODULES = (
    'test_consolidation_ras_documents651_isole',
    'test_annulation_ventilation_isole', 'test_e2e_annulation_contexte_isole',
    'test_reglements_par_tiers_isole', 'test_e2e_reglements_par_tiers_isole',
    'test_e2e_annulation_date655_isole', 'test_e2e_reglement_edition_isole',
    'test_e2e_ras_capture_isole',
)
vus = set()
for i, nom in enumerate(MODULES):
    for cle, fonction in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(fonction):
            identite = fonction.__module__, fonction.__qualname__
            if identite not in vus:
                vus.add(identite)
                globals()[f'test_661_{i}_{cle[5:]}'] = fonction
