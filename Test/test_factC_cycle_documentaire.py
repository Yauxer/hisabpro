from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


def read(path):
    return Path(path).read_text(encoding="utf-8")


def test_factC_acomptes_utilisent_sequence_atomique():
    src = read(BACK / "acomptes.py")
    sql = read(BACK / "041_factC_cycle_documentaire.sql")
    assert 'reserver_numero_commercial(db, societe_id, exercice, "acompte", "AC")' in src
    assert "COUNT()+1" in src  # commentaire explicitant le bug supprimé
    assert "'acompte'" in sql
    assert "uq_acomptes_societe_numero" in sql
    assert "FROM acomptes" in sql


def test_factC_annulation_acompte_est_automatique_et_tracee():
    src = read(BACK / "acomptes.py")
    models = read(BACK / "models.py")
    assert '@router.post("/{acompte_id}/annuler")' in src
    assert 'reference=f"ANN-{acompte.numero}"' in src
    assert "debit=l.credit" in src and "credit=l.debit" in src
    assert "date_annulation" in models
    assert "ecriture_annulation_id" in models
    assert "Un acompte numéroté ne se supprime pas" in src


def test_factC_avoir_peut_etre_emis_sur_exercice_ulterieur_ouvert():
    src = read(BACK / "avoirs.py")
    assert "un avoir de N peut parfaitement corriger en N+1" in src
    assert "jour.year != exercice_facture" not in src
    assert "exercice_avoir = _verifier_date_avoir" in src
    assert "exercice=exercice_avoir.annee" in src
    assert 'db, societe_id, exercice_avoir.annee, "avoir"' in src
    assert "La date de l'avoir ne peut pas précéder la facture d'origine" in src
    assert "Un avoir numéroté ne se supprime pas" in src


def test_factC_devis_accepte_ou_converti_est_fige():
    src = read(BACK / "routers" / "commercial.py")
    factures = read(BACK / "routers" / "factures.py")
    assert 'statut_actuel in {"accepte", "converti"}' in src
    assert "Un devis accepté ou converti est figé" in src
    assert "Un devis accepté ou converti ne peut plus être supprimé" in src
    assert "Seul un devis accepté peut être converti en bon de commande" in src
    assert "Seul un devis accepté peut être converti directement en facture" in factures


def test_factC_cloture_bloque_documents_metier_non_comptabilises():
    src = read(BACK / "routers" / "cloture.py")
    assert "def _documents_non_comptabilises" in src
    assert "models.Facture.est_validee == True" in src
    assert "models.Facture.est_comptabilisee == False" in src
    assert "models.Avoir.est_comptabilisee == False" in src
    assert "models.Reglement.est_comptabilisee == False" in src
    assert "models.Acompte.est_comptabilisee == False" in src
    assert "models.ImputationAcompte.est_comptabilisee == False" in src
    assert '"nb_documents_non_comptabilises"' in src
    assert "document(s) métier définitif(s) n'ont pas encore été comptabilisés" in src


def test_factC_frontend_utilise_annulations_tracees_sans_suppression_physique():
    acomptes = read(ROOT / "src" / "pages" / "Acomptes.jsx")
    avoirs = read(ROOT / "src" / "pages" / "Avoirs.jsx")
    assert "/api/acomptes/${a.id}/annuler" in acomptes
    assert "method: 'POST'" in acomptes
    assert "Supprimer définitivement l'acompte" not in acomptes
    assert "async function supprimer(avoir)" not in avoirs
    assert "Annuler l'avoir" in avoirs
