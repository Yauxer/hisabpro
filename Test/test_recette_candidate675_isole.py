"""Candidate hors RH : campagne commune, témoins natifs et sources figées."""
from pathlib import Path
import importlib
import json
import pytest
import test_consolidation_ras_documents651_isole as precedent
from test_consolidation_ras_documents651_isole import (
    application102, application101, application100, application099, application098,
    application097, application093, application092, application091, application090,
    application089, application087, migration,
)
from test_e2e_facturation_isole import application as application_absente
from test_multi_societes_runtime_isole import (
    test090_creation_seconde_societe_et_switch_api,
    test090_invitation_changement_role_desactivation_et_suppression_secondaire,
    test090_creation_switch_et_plan_dans_edge,
)
from postgres_isole import verifier_cible_isolee


@pytest.fixture(scope='module')
def application(application102):
    root=Path(__file__).resolve().parents[1]
    chemin=root/'.codex-tests/consolidation651_preuve.json'
    ancienne=chemin.read_bytes() if chemin.exists() else None
    interdits={root/'.codex-tests/baseline645.json',root/'.codex-tests/cumul649_preuve.json'}
    lire=Path.read_text
    def lecture_portable(path,*args,**kwargs):
        if path.resolve() in interdits:
            raise FileNotFoundError('Une recette livrée doit fonctionner sans les baselines privées.')
        return lire(path,*args,**kwargs)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path,'read_text',lecture_portable)
        banc=precedent.application.__wrapped__(application102)
        demarre=False
        try:
            app=next(banc);demarre=True
            c=app['cluster']
            assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
            assert app['role_sql']=='hisabpro'
            yield app
        finally:
            try:
                banc.close()
                if demarre:
                    preuve=json.loads(chemin.read_text(encoding='utf8'))
                    preuve.update(lectures_baselines_privees_interdites=True,role_sql='hisabpro',
                        dossier_cluster=str(c['directory']),dossier_application=str(app['directory']))
                    (root/'.codex-tests/candidate675_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
            finally:
                if ancienne is not None:chemin.write_bytes(ancienne)


MODULES=(
    'test_consolidation_annulations661_isole',
    'test_e2e_listes_commerciales673_isole',
    'test_e2e_reglements_erreur663_isole','test_e2e_reglements_lecture665_isole',
    'test_e2e_receptions_lecture667_isole','test_e2e_entree_reception669_isole',
    'test_e2e_annee_connectee_isole','test_e2e_immobilisations_degressif_isole',
    'test_guide_actualisation671','test_installation_vierge_102',
)
vus={(f.__module__,f.__qualname__) for n,f in list(globals().items()) if n.startswith('test_') and callable(f)}
for i,nom in enumerate(MODULES):
    for cle,fonction in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(fonction):
            identite=fonction.__module__,fonction.__qualname__
            if identite not in vus:
                vus.add(identite)
                globals()[f'test_675_{i}_{cle[5:]}']=fonction
