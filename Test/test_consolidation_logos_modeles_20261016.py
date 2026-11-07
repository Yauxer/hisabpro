"""Recette commune092 : oracles451–458 + logos/modèles + facturation/TVA réelles.

Les tests sont réutilisés tels quels. Le seul scénario452 remplacé est repris
avec ses assertions intégrales dans468, en y ajoutant logos/catalogue092.
"""
import importlib
import hashlib,json
from pathlib import Path
import pytest
from sqlalchemy import text
from postgres_isole import verifier_cible_isolee
from test_restauration_runtime_acl_089 import catalogue_acl
from test_permissions_tva_runtime_isole import (
    application as application093,application092,application091,application090,application089,application087,migration,
)

MODULES=(
    'test_consolidation_reprise_20261015',
    'test_logos_exports_pdf','test_logos_exports_runtime_isole','test_logos_xlsx_navigateur',
    'test_e2e_logos_xlsx_isole','test_modeles_avances_runtime_isole','test_modeles_changement_taux',
    'test_e2e_modeles_taux_isole','test_e2e_logos_impression_isole','test_pdf_textes_litteraux',
    'test_restauration_logos_modeles_isole','test_e2e_facturation_isole','test_e2e_tva_isole',
    'test_permissions_tva_runtime_isole','test_e2e_effets_date_locale_isole',
)
for nom in MODULES:
    module=importlib.import_module(nom)
    for nom_test,fonction in vars(module).items():
        if nom_test.startswith('test_') and callable(fonction):
            if nom_test=='test_dump_restore_pieces_justificatifs_decision091_et_acl_natives':continue
            if nom_test in globals():assert globals()[nom_test] is fonction,nom_test
            globals()[nom_test]=fonction

ROOT=Path(__file__).resolve().parents[1]
SOURCES=(
    'hisabpro-backend/pdf_generator.py','hisabpro-backend/schemas.py','hisabpro-backend/routers/etats.py',
    'hisabpro-backend/services/logo_export_service.py','hisabpro-backend/services/balance_pdf_service.py',
    'hisabpro-backend/services/balance_preparation_pdf.py','hisabpro-backend/services/liasse_pdf.py',
    'hisabpro-backend/services/liasse_service.py','hisabpro-backend/services/livre_inventaire_pdf.py',
    'hisabpro-backend/services/ventes_preparation_export_service.py',
    'src/services/exportXlsxLogo.js','src/services/exportBalances.js','src/utils/montantsModeles.js',
    'src/components/LogoDocument.jsx','src/components/LogoSociete.jsx',
    'src/components/ImportBalanceLiasse.jsx','src/components/FormulaireEcriture.jsx',
    'src/pages/Balances.jsx','src/pages/LiasseFiscale.jsx','src/pages/Journal.jsx','src/pages/DeclarationTVA.jsx',
    'src/pages/Effets.jsx','hisabpro-backend/routers/tva.py','hisabpro-backend/routers/ecritures.py',
    'Test/test_e2e_pieces_telechargement_refuse_isole.py',
)
def empreintes():
    fichiers=list((ROOT/'hisabpro-backend').glob('*.sql'))
    fichiers += [ROOT/'Test'/f'{m}.py' for m in MODULES]
    fichiers += [Path(__file__)]
    fichiers += [ROOT/p for p in SOURCES]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in fichiers}


@pytest.fixture(scope='module')
def application(application093):
    app=application093;c=app['cluster'];chemin=ROOT/'.codex-tests/consolidation469_preuve.json'
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    sources=empreintes();droits=catalogue_acl(app['engine'])
    preuve={'statut':'en_cours','erreur':None,'sources':sources}
    try:
        yield app
        with app['engine'].connect() as db:
            controles={
                'pieces_desequilibrees':db.scalar(text('SELECT count(*) FROM (SELECT ecriture_id FROM lignes_ecriture GROUP BY ecriture_id HAVING sum(debit)<>sum(credit)) q')),
                'montants_non_finis':db.scalar(text("SELECT count(*) FROM lignes_ecriture WHERE debit::text IN ('NaN','Infinity','-Infinity') OR credit::text IN ('NaN','Infinity','-Infinity')")),
                'definitives_sans_numero_date':db.scalar(text("SELECT count(*) FROM ecritures WHERE est_validee AND (NULLIF(btrim(numero_ecriture),'') IS NULL OR date_validation IS NULL)")),
            }
            comptes={t:db.scalar(text(f'SELECT count(*) FROM {t}')) for t in (
                'societes','ecritures','lignes_ecriture','clotures_exercice','lettrages_comptables','modeles_ecritures','lignes_modele')}
        assert all(v==0 for v in controles.values()),controles
        assert comptes['modeles_ecritures']==64
        assert catalogue_acl(app['engine'])==droits
        assert empreintes()==sources
        preuve.update(statut='invariants_valides',controles=controles,comptes=comptes,
            droits_inchanges=True,sources_inchangees=True,role_sql=app['role_sql'])
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:chemin.write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
