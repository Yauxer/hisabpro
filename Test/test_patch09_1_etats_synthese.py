from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "hisabpro-backend"


def _txt(path):
    return path.read_text(encoding="utf-8")


def test_source_etats_est_postgresql_complete_et_validee():
    service = _txt(BACKEND / "services" / "etats_synthese_service.py")
    assert "func.sum(models.LigneEcriture.debit)" in service
    assert "func.sum(models.LigneEcriture.credit)" in service
    assert "models.Ecriture.est_validee.is_(True)" in service
    assert ".group_by(models.LigneEcriture.compte)" in service
    # Les états ne doivent pas dépendre de la limite 200 du Journal.
    assert ".limit(" not in service


def test_cloture_technique_exclue_mais_an_conserve():
    service = _txt(BACKEND / "services" / "etats_synthese_service.py")
    assert "models.JournalEnum.CL" in service
    assert 'like("CLOTURE-%")' in service
    # Ne jamais exclure globalement source='cloture' : les AN sont eux aussi
    # créés par le moteur de clôture et constituent le bilan d'ouverture N+1.
    assert 'source == "cloture"' not in service
    assert "models.Ecriture.source ==" not in service


def test_brouillons_sont_exclus_et_signales():
    service = _txt(BACKEND / "services" / "etats_synthese_service.py")
    page = _txt(ROOT / "src" / "pages" / "Bilan.jsx")
    assert "brouillons_exclus" in service
    assert "écriture(s) brouillon sont exclues" in service
    assert "controle.avertissements" in page
    assert "écriture(s) validée(s)" in page


def test_endpoint_et_frontend_utilisent_source_etats():
    router = _txt(BACKEND / "routers" / "etats.py")
    api = _txt(ROOT / "src" / "services" / "api.js")
    moteur = _txt(ROOT / "src" / "data" / "etatsSynthese.js")
    assert '@router.get("/source/{exercice}")' in router
    assert "source_etats_synthese" in router
    assert "export const etatsAPI" in api
    assert "/api/etats/source/${exercice}" in api
    assert "etatsAPI.source(exercice)" in moteur
    assert "ecrituresAPI.lister" not in moteur


def test_modele_normal_conserve_et_eligibilite_simplifiee_signalee():
    service = _txt(BACKEND / "services" / "etats_synthese_service.py")
    page = _txt(ROOT / "src" / "pages" / "Bilan.jsx")
    assert '"eligible_modele_simplifie"' in service
    assert 'Decimal("10000000.00")' in service
    assert '"modele_utilise": "normal"' in service
    assert "Éligible au modèle simplifié" in page


def test_les_quatre_etats_quantitatifs_du_modele_normal_restent_disponibles():
    moteur = _txt(ROOT / "src" / "data" / "etatsSynthese.js")
    page = _txt(ROOT / "src" / "pages" / "Bilan.jsx")
    for fn in ("calculerBilan", "calculerCPC", "calculerESG", "calculerTableauFinancement"):
        assert f"function {fn}" in moteur
    for label in ("Bilan", "CPC", "ESG", "Tableau de financement"):
        assert label in page
