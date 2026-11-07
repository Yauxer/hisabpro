"""Recette regroupée451–458, mêmes oracles, source091 et LOGIN SQL communs.

La restauration conserve ses deux clusters propres ; les contrôles purement
monétaires Node/Python n'utilisent pas PostgreSQL. Aucun résultat humain prévalidé.
"""
from pathlib import Path
import hashlib
import json
import pytest
from sqlalchemy import text
from postgres_isole import verifier_cible_isolee
from test_restauration_runtime_acl_089 import catalogue_acl
from test_e2e_runtime_session_isole import (
    application as application091, application090, application089, application087, migration,
)

from test_justificatifs_modeles_runtime_isole import (
    test_modeles_lecture_sans_droits_de_modification,
    test_references_prioritaires_et_fichiers_definitifs_sans_reecrire_original,
    test_piece_brouillon_supprimable_et_refus_multisociete_lecture,
    test_refus_sql_suppression_conserve_fichier_et_trace,
    test_validation_concurrente_protege_la_piece_devenue_definitive,
    test_edge_refus_suppression_garde_la_piece_visible,
    test_edge_modele_validation_justificatif_et_telechargement,
)
from test_e2e_pieces_telechargement_refuse_isole import test_document_refuse_ne_devient_pas_un_faux_pdf
from test_e2e_modeles_journal_lettrage_isole import test_modeles_100_20_120_tiers_validation_lettrage_fec
from test_e2e_modeles_detection_isole import test_detection_conserve_ht_100_tva20_ttc120_et_permet_validation
from test_modeles_montants import test_montants_par_ligne_de_saisie, test_montants_non_determinables_ne_produisent_pas_nan
from test_e2e_instruments_runtime_isole import (
    test_runtime_encaissement_frais_rapprochement_lettrage,
    test_runtime_annee_frais_cloture_an_fec,
    test_runtime_cheque_impaye_remplacement_lettrage,
    test_runtime_refus_frais_demi_centime,
)
from test_e2e_journal_lecture_isole import test_commandes_journal_documents_et_controles_selon_role
from test_ecritures_capacite_runtime_isole import (
    test_depassement_fini_retourne422_et_preserve_journal,
    test_helper_refuse_depassement_apres_arrondi_existant,
    test_helper_conserve_limites_decimal_valides_et_arrondi,
    test_pg_confirme_precision_et_limite_valide_api,
)
from test_restauration_justificatifs_acl_isole import test_dump_restore_pieces_justificatifs_decision091_et_acl_natives

ROOT=Path(__file__).resolve().parents[1]
SOURCES=(
    'hisabpro-backend/attachments.py','hisabpro-backend/routers/ecritures.py',
    'src/components/PiecesJointes.jsx','src/components/FormulaireEcriture.jsx',
    'src/utils/montantsModeles.js','src/pages/Journal.jsx',
    'Test/test_justificatifs_modeles_runtime_isole.py',
    'Test/test_restauration_justificatifs_acl_isole.py',
    'Test/test_e2e_pieces_telechargement_refuse_isole.py',
    'Test/test_e2e_modeles_journal_lettrage_isole.py','Test/test_e2e_modeles_detection_isole.py',
    'Test/test_modeles_montants.py','Test/test_e2e_instruments_runtime_isole.py',
    'Test/test_e2e_journal_lecture_isole.py','Test/test_ecritures_capacite_runtime_isole.py',
    'Test/test_consolidation_reprise_20261015.py',
)


def empreintes():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}


@pytest.fixture(scope='module')
def application(application091):
    app=application091;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    avant=empreintes();droits=catalogue_acl(app['engine'])
    preuve={'statut':'en_cours','erreur':None,'sources':avant}
    chemin=ROOT/'.codex-tests/consolidation459_preuve.json'
    chemin.write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
    try:
        yield app
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        with app['engine'].connect() as db:
            comptes={t:db.scalar(text(f'SELECT count(*) FROM {t}')) for t in (
                'societes','ecritures','lignes_ecriture','clotures_exercice','lettrages_comptables','ecriture_justificatifs')}
            controles={
                'pieces_desequilibrees':db.scalar(text('SELECT count(*) FROM (SELECT ecriture_id '
                    'FROM lignes_ecriture GROUP BY ecriture_id HAVING sum(debit)<>sum(credit)) q')),
                'montants_non_finis':db.scalar(text("SELECT count(*) FROM lignes_ecriture WHERE "
                    "debit::text IN ('NaN','Infinity','-Infinity') OR credit::text IN ('NaN','Infinity','-Infinity')")),
                'definitives_sans_numero_ou_date':db.scalar(text("SELECT count(*) FROM ecritures WHERE est_validee "
                    "AND (NULLIF(btrim(numero_ecriture),'') IS NULL OR date_validation IS NULL)")),
            }
        assert all(v==0 for v in controles.values()),controles
        assert catalogue_acl(app['engine'])==droits,'Une injection de faute ne doit pas modifier les droits finaux.'
        assert empreintes()==avant,'Les sources testées doivent rester figées pendant la commande.'
        preuve.update(statut='invariants_valides',comptes=comptes,controles=controles,
            droits_inchanges=True,sources_inchangees=True,role_sql=app['role_sql'])
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        chemin.write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf-8')
