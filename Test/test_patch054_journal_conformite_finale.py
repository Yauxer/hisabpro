# -*- coding: utf-8 -*-
"""Patch 054 — Journal exhaustif et derniers garde-fous de conformité."""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
import ast
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

# Les tests FEC purs n'ont pas besoin du mapping ORM complet.
sys.modules.setdefault("models", types.SimpleNamespace())
from services.fec_service import controler_fec  # noqa: E402


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ligne(compte, debit=0, credit=0, **kwargs):
    base = dict(
        compte=compte,
        debit=Decimal(str(debit)),
        credit=Decimal(str(credit)),
        libelle="Ligne",
        tiers_id=None,
        compte_auxiliaire_snapshot=None,
        libelle_auxiliaire_snapshot=None,
        code_lettrage=None,
        date_lettrage=None,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _ecriture(lignes):
    return SimpleNamespace(
        id=1, numero_ecriture="VT-2027-0001", journal="VT", exercice=2027,
        date=date(2027, 1, 10), date_piece=date(2027, 1, 10), reference="FAC-1",
        libelle="Facture", source="facture", est_validee=True,
        date_validation=datetime(2027, 1, 10, 12, 0), created_at=datetime(2027, 1, 10, 11, 0),
        justificatifs=[], lignes=lignes,
    )


def _exercice():
    return SimpleNamespace(date_debut=date(2027, 1, 1), date_fin=date(2027, 12, 31), statut="ouvert")


def test_journal_backend_n_a_plus_de_plafond_implicite_200():
    src = read(BACK / "routers" / "ecritures.py")
    ast.parse(src)
    bloc = src[src.index("def lister_ecritures"):src.index("def _lignes_reporting")]
    assert "limit: Optional[int] = Query(None" in bloc
    assert "limit: int = 200" not in bloc
    assert "if limit is not None:" in bloc
    assert "models.Ecriture.id.desc()" in bloc


def test_client_ne_force_plus_skip_limit_et_contexte_transmet_le_tiers():
    api = read(ROOT / "src" / "services" / "api.js")
    ctx = read(ROOT / "src" / "data" / "EcrituresContext.jsx")
    assert "limit = null" in api
    assert "if (limit !== null && limit !== undefined)" in api
    assert ctx.count("tiers_id: l.tiers_id || null") == 2


def test_export_csv_journal_utilise_la_signature_commune_et_les_auxiliaires():
    journal = read(ROOT / "src" / "pages" / "Journal.jsx")
    assert "exporterCSV(`journal_${annee}`, [" in journal
    assert "Compte auxiliaire" in journal
    assert "Libellé auxiliaire" in journal
    assert "exporterCSV(lignes, `journal_${annee}`)" not in journal


def test_journal_est_imprimable_avec_metadonnees_logiciel_et_periode():
    journal = read(ROOT / "src" / "pages" / "Journal.jsx")
    css = read(ROOT / "src" / "pages" / "Journal.module.css")
    assert "window.print()" in journal
    assert "HisabPro v{APP_VERSION}" in journal
    assert "Période :" in journal
    assert "@media print" in css
    assert "display: table-header-group" in css
    assert "overflow: visible !important" in css


def test_etic_est_verrouillee_des_que_la_liasse_est_finalisee_backend_et_ui():
    api = read(BACK / "routers" / "etats.py")
    ui = read(ROOT / "src" / "pages" / "Etic.jsx")
    assert "def _verifier_etic_modifiable" in api
    assert api.count("_verifier_etic_modifiable(db, current_user") >= 2
    assert 'data["verrouillee"] = bool(archive)' in api
    assert "&& !verrouillee" in ui
    assert "data.motif_verrouillage" in ui


def test_pdf_financiers_sont_recalcules_serveur_et_non_fournis_par_le_navigateur():
    api = read(BACK / "routers" / "etats.py")
    service = read(BACK / "services" / "etats_pdf_service.py")
    bilan = read(ROOT / "src" / "pages" / "Bilan.jsx")
    assert '@router.get("/pdf-officiel/{etat}/{exercice}")' in api
    assert "construire_etat_pdf_officiel" in api
    # Route historique : data.lignes n'alimente plus le générateur PDF.
    bloc = api[api.index('@router.post("/pdf")'):api.index("# ── Patch 09.3")]
    assert 'lignes=officiel["lignes"]' in bloc
    assert "[l.model_dump() for l in data.lignes]" not in bloc
    assert "construire_liasse" in service
    assert "/api/etats/pdf-officiel/" in bilan
    assert "body: JSON.stringify(payload)" not in bilan


def test_etats_pdf_portent_date_version_periode_et_pagination():
    pdf = read(BACK / "pdf_generator.py")
    liasse = read(BACK / "services" / "liasse_pdf.py")
    assert 'HISABPRO_VERSION = os.getenv("HISABPRO_VERSION", "0.1.0")' in pdf
    assert "Édité le {date_edition} — HisabPro v{version}" in pdf
    assert "Période : {periode_debut" in pdf
    assert 'f"Page {doc.page}"' in pdf
    assert 'os.getenv("HISABPRO_VERSION","0.1.0")' in liasse
    assert 'f"Page {doc_obj.page}"' in liasse
    assert "onFirstPage=on_page,onLaterPages=on_page" in liasse


def test_fec_controle_explicitement_egalite_auxiliaires_collectifs():
    ec = _ecriture([
        _ligne("3421", debit=120, tiers_id=7,
               compte_auxiliaire_snapshot="C00000007", libelle_auxiliaire_snapshot="ACME"),
        _ligne("7111", credit=120),
    ])
    controle = controler_fec([ec], 2027, _exercice())
    aux = controle["controle_auxiliaires"]["3421"]
    assert aux["conforme"] is True
    assert aux["collectif_debit"] == 120.0
    assert aux["auxiliaires_debit"] == 120.0
    assert "AUXILIAIRES_COLLECTIF_DESEQUILIBRES" not in {x["code"] for x in controle["bloquants"]}


def test_fec_detecte_explicitement_un_ecart_auxiliaire_collectif():
    ec = _ecriture([
        _ligne("3421", debit=120),
        _ligne("7111", credit=120),
    ])
    controle = controler_fec([ec], 2027, _exercice())
    codes = {x["code"] for x in controle["bloquants"]}
    assert "AUXILIAIRE_MANQUANT" in codes
    assert "AUXILIAIRES_COLLECTIF_DESEQUILIBRES" in codes


def test_documentation_systeme_comptable_est_livree():
    doc = read(ROOT / "docs" / "MANUEL_SYSTEME_COMPTABLE_HISABPRO.md")
    for token in ("Avis n°24", "Loi n° 9-88", "FEC", "irréversibilité", "sauvegarde", "documentation"):
        assert token in doc
