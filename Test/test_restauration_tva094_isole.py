"""Recette froide452 inchangée, source enrichie jusqu'à la protection094."""
from pathlib import Path
import json,hashlib
import test_restauration_justificatifs_acl_isole as recette
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_restauration094_schema_acl_parametres_pieces_et_fec(monkeypatch,tmp_path):
    origine=recette.preparer091;migrations=[]
    def preparer094(engine,cluster):
        assert verifier_cible_isolee(cluster['url'],cluster['directory'],cluster['nonce'])
        origine(engine,cluster)
        raw=engine.raw_connection()
        try:
            raw.autocommit=True
            with raw.cursor() as cur:
                for nom in ('092_modeles_avances_personnel.sql','093_permissions_parametres_tva.sql','094_protection_parametres_tva_clotures.sql'):
                    p=recette.BACK/nom;cur.execute(p.read_text(encoding='utf8'))
                    migrations.append({'fichier':nom,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        finally:raw.close()
    monkeypatch.setattr(recette,'preparer091',preparer094)
    # Toutes les assertions de452 restent actives :arrêt API source, copie
    # native sur cible vide marquée, schéma/ACL/73tables/séquences puis reprise.
    recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
    assert len(migrations)==3
    preuve=json.loads((ROOT/'.codex-tests/restauration452_preuve.json').read_text(encoding='utf8'))
    preuve.update(extension094=True,migrations=migrations)
    (ROOT/'.codex-tests/restauration480_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
