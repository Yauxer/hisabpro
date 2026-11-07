"""Schéma consolidé084 restauré sans toucher une connexion existante."""
import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text

from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_restauration_consolidee_084 import schema, verifier_schema

from test_installation_vierge_084 import ROOT, lancer, rapport_data


def test_restauration_consolidee_schema_donnees_droits_et_protections(tmp_path):
    data = lancer(['Test/recette_restauration_consolidee_084.py','--rapport'], tmp_path/'restauration084.md')
    assert data['statut'] == 'installation_084_restauree_schema_donnees_acl_limitees_valides'
    assert len(data['appliquees']) == 86 and len(data['zero_final']) == 25
    preuve = data['restauration']
    assert preuve['erreur'] is None and preuve['cible_supprimee'] and preuve['clusters_distincts']
    assert preuve['schema_et_donnees_identiques'] and preuve['source_et_cible_inchangees']
    assert preuve['taille_dump'] > 0 and len(preuve['sha256_dump']) == 64
    assert len(preuve['tables']) >= data['nombre_tables_orm']
    assert all(preuve['tables'][t]['nombre'] == 0 for t in data['zero_final'])
    assert set(preuve['schema']) == {'colonnes','contraintes','index','triggers','fonctions','sequences','etats_sequences'}
    assert [r[:2] for r in preuve['normalisation_checks_source']] == [r[:2] for r in preuve['normalisation_checks_cible']]
    assert all(v['nombre'] > 0 and len(v['sha256']) == 64 for v in preuve['schema'].values())
    assert not any(preuve['droits_absents_avant_rejeu'].values())
    assert preuve['droits_083_084_restitues'] and preuve['cible_non_vide_refusee']
    assert len(preuve['refus']) == 6
    assert preuve['role_runtime'] == ['hisabpro','hisabpro',True,False,False,False,False,False]


def test_assertion_sans_message_arrete_le_banc_et_renvoie_echec(tmp_path):
    rapport = tmp_path/'assertion-vide.md'
    script = "import sys;from pathlib import Path;sys.path.insert(0,'Test');" \
        "from recette_installation_vierge_consolidee import executer;" \
        "raise SystemExit(executer(rapport=Path(sys.argv[1])," \
        "controle_complementaire=lambda *args: (_ for _ in ()).throw(AssertionError())))"
    r = subprocess.run([sys.executable,'-X','utf8','-c',script,str(rapport)],
        cwd=ROOT, env=dict(os.environ, PYTHON_DOTENV_DISABLED='1',PYTHONUTF8='1'),
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    assert r.returncode == 1, (r.stdout[-3000:], r.stderr[-3000:])
    data = rapport_data(rapport)
    assert data['statut'] == 'echec_arret_premier_controle'
    assert data['erreur'] == 'AssertionError()' and data['cluster_supprime'] is True


def test_normalisation_check_conserve_predicat_et_statut_validation():
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'],cible['directory'],cible['nonce'])
        engine = create_engine(cible['url'])
        try:
            with engine.begin() as db:
                db.execute(text("CREATE TABLE normalisation(mode varchar(20), "
                    "CONSTRAINT ck_mode CHECK(mode IN ('a','b')), "
                    "CONSTRAINT ck_percent CHECK(mode NOT LIKE '%z%'))"))
            avant = schema(engine)
            with engine.begin() as db:
                db.execute(text('ALTER TABLE normalisation DROP CONSTRAINT ck_mode'))
                db.execute(text("ALTER TABLE normalisation ADD CONSTRAINT ck_mode "
                    "CHECK(mode::text = ANY(ARRAY['a'::varchar::text,'b'::varchar::text]))"))
            verifier_schema(schema(engine),avant)
            for sql in ("CHECK(mode IN ('a','c'))", "CHECK(mode IN ('a','b')) NOT VALID"):
                with engine.begin() as db:
                    db.execute(text('ALTER TABLE normalisation DROP CONSTRAINT ck_mode'))
                    db.execute(text('ALTER TABLE normalisation ADD CONSTRAINT ck_mode '+sql))
                with pytest.raises(AssertionError, match='contraintes'):
                    verifier_schema(schema(engine),avant)
        finally:
            engine.dispose()
    assert not cible['directory'].exists()
