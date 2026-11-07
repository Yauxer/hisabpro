"""Fabrique partagée sous102, correspondance témoin non vide et inchangée."""
from contextlib import contextmanager
import importlib
import hashlib,json
from pathlib import Path
import pytest
from test_factures_liees635_isole import (
    application as application102,application101,application100,application099,application098,application097,application093,
    application092,application091,application090,application089,application087,migration,vente,demande,chemin,PATH)
from test_multi_societes_runtime_isole import ok
from sqlalchemy import text


@pytest.fixture(scope='module')
def application(application102):
    app=application102;a,b,ids=vente(app)
    try:
        s=ok(a.post(chemin(ids),json=demande(a,ids)),201)
        def photos():
            with app['engine'].connect() as db:
                return {t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x WHERE '+('facture_id' if t=='lignes_facture' else 'id')+' IN (:v,:a) ORDER BY 1'),{'v':ids['fid'],'a':s['facture_achat_id']}).scalars().all() for t in ('factures','lignes_facture')}
        avant=photos()
        root=Path(__file__).resolve().parents[1]
        chemins=('hisabpro-backend/routers/factures.py','hisabpro-backend/services/factures_liees_service.py',
            'hisabpro-backend/routers/factures_liees.py','hisabpro-backend/102_factures_correspondantes.sql',
            'src/components/FactureLiee.jsx','src/pages/Factures.jsx','src/services/api.js')
        def sources():return {f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in chemins}
        hashes=sources()
        yield app
        assert ok(a.get(f'{PATH}/factures/{ids["fid"]}/correspondance'))==s
        assert photos()==avant
        assert sources()==hashes
        (root/'.codex-tests/compat635_preuve.json').write_text(json.dumps({'sources_inchangees':True,'temoin_non_vide_inchange':True,'sources':hashes},indent=2),encoding='utf8')
    finally:a.close();b.close()


modules=('test_finalisation_facture_concurrente_isole','test_facture_comptabilisation_concurrente_isole',
    'test_e2e_facturation_isole','test_e2e_facture_achat_tva_edition_isole',
    'test_factures_proforma_lecture_isole','test_e2e_factures_lecture_isole',
    'test_reglements_par_tiers_isole','test_e2e_acompte_imputation_isole',
    'test_e2e_acompte_fournisseur_isole','test_journal_liberation_facture_source_isole')
vus=set()
for i,nom in enumerate(modules):
    for cle,f in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(f):
            identite=f.__module__,f.__qualname__
            if identite not in vus:vus.add(identite);globals()[f'test_compat635_{i}_{cle[5:]}']=f
