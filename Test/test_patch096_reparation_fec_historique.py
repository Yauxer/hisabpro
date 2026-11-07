from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "hisabpro-backend" / "067_reparation_fec_historique_sure.sql"


def _sql():
    return SQL.read_text(encoding="utf-8")


def test_migration_067_existe_et_est_transactionnelle():
    src = _sql()
    assert "BEGIN;" in src
    assert "COMMIT;" in src
    assert "_fec067_facture_match" in src
    assert "_fec067_reglement_match" in src


def test_ne_recrit_jamais_les_ecritures_definitives():
    src = _sql().lower()
    assert "update ecritures" not in src
    assert "delete from ecritures" not in src
    assert "set journal" not in src
    assert "set numero_ecriture" not in src


def test_reference_fec_est_ajoutee_en_append_only_sans_reference_inventee():
    src = _sql()
    assert "INSERT INTO ecriture_justificatifs" in src
    assert "COALESCE(NULLIF(BTRIM(r.reference), ''), NULLIF(BTRIM(r.numero), ''))" in src
    assert "REG-'" not in src
    assert "NOT EXISTS (" in src
    assert "NULLIF(BTRIM(m.reference_piece), '') IS NOT NULL" in src


def test_rapprochements_sont_uniquement_non_ambigus():
    src = _sql()
    assert "HAVING COUNT(DISTINCT c.facture_id) = 1" in src
    assert "HAVING COUNT(DISTINCT c.reglement_id) = 1" in src
    assert "RIGHT(LOWER(BTRIM(e.libelle))" in src
    assert "ABS(COALESCE(lx.debit, 0)::numeric" in src


def test_enrichissement_auxiliaire_est_limite_aux_comptes_collectifs():
    src = _sql()
    assert "l.compte LIKE '3421%'" in src
    assert "l.compte LIKE '4411%'" in src
    assert "compte_auxiliaire_snapshot" in src
    assert "libelle_auxiliaire_snapshot" in src


def test_piste_audit_reste_active_pendant_enrichissement_des_lignes():
    src = _sql()
    assert "DISABLE TRIGGER trg_hisabpro_proteger_lignes_definitives" in src
    assert "ENABLE TRIGGER trg_hisabpro_proteger_lignes_definitives" in src
    assert "DISABLE TRIGGER trg_hisabpro_audit_lignes_ecriture" not in src
    assert "hisabpro.audit_motif" in src


def test_migration_ne_tente_pas_de_masquer_anomalie_de_cloture_legacy():
    src = _sql()
    assert "ECRITURE_CLOTURE_HORS_JOURNAL_DEDIE" not in src
    assert "CLOTURE-" not in src
