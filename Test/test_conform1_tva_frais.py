from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.tva_regles_service import taux_autorises, valider_tva
from services.tva_service import ventilation_facture, total_ventilation, ajouter_ventilation

ROOT = Path(__file__).resolve().parents[1]


def ligne(base, taux, qualification="taxable"):
    return SimpleNamespace(
        quantite=1,
        prix_unitaire=base,
        remise=0,
        remise2=0,
        rabais=0,
        tva=taux,
        qualification_tva=qualification,
    )


def facture(lignes, **kwargs):
    defaults = dict(
        lignes=lignes,
        frais_transport_ht=0,
        frais_transport_tva=20,
        frais_transport_mode="accessoire",
        frais_transport_qualification_tva="taxable",
        frais_emballage_ht=0,
        frais_emballage_tva=20,
        frais_emballage_mode="perdu",
        frais_emballage_qualification_tva="taxable",
        remise_globale=0,
        ristourne=0,
        escompte=0,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_catalogue_tva_est_date_et_2026_est_limite_aux_taux_generiques_10_20():
    assert taux_autorises(date(2023, 12, 31)) == (0, 7, 10, 14, 20)
    assert 13 in taux_autorises(date(2024, 6, 1))
    assert 18 in taux_autorises(date(2025, 6, 1))
    assert taux_autorises(date(2026, 1, 1)) == (0, 10, 20)


def test_tva_2026_refuse_zero_taxable_et_anciens_taux():
    with pytest.raises(ValueError):
        valider_tva(date(2026, 1, 1), 0, "taxable")
    with pytest.raises(ValueError):
        valider_tva(date(2026, 1, 1), 7, "taxable")
    with pytest.raises(ValueError):
        valider_tva(date(2026, 1, 1), 14, "taxable")
    assert valider_tva(date(2026, 1, 1), 10, "taxable") == 10
    assert valider_tva(date(2026, 1, 1), 20, "taxable") == 20


def test_zero_pourcent_exige_une_qualification_fiscale():
    assert valider_tva(date(2026, 1, 1), 0, "exonere_droit_deduction") == 0
    assert valider_tva(date(2026, 1, 1), 0, "exonere_sans_deduction") == 0
    assert valider_tva(date(2026, 1, 1), 0, "hors_champ") == 0
    assert valider_tva(date(2026, 1, 1), 0, "suspension") == 0
    with pytest.raises(ValueError):
        valider_tva(date(2026, 1, 1), 10, "hors_champ")


def test_transport_accessoire_suit_les_taux_des_lignes_sur_facture_mixte():
    f = facture([ligne(100, 10), ligne(100, 20)], frais_transport_ht=100, frais_transport_mode="accessoire")
    vent = ventilation_facture(f)
    assert vent[Decimal("10")]["base"] == Decimal("150.00")
    assert vent[Decimal("10")]["tva"] == Decimal("15.00")
    assert vent[Decimal("20")]["base"] == Decimal("150.00")
    assert vent[Decimal("20")]["tva"] == Decimal("30.00")
    assert total_ventilation(vent)["ttc"] == Decimal("345.00")


def test_emballage_perdu_suit_les_lignes_et_consigne_est_hors_tva():
    perdu = facture([ligne(100, 10), ligne(100, 20)], frais_emballage_ht=100, frais_emballage_mode="perdu")
    vent_perdu = ventilation_facture(perdu)
    assert total_ventilation(vent_perdu) == {"base": Decimal("300.00"), "tva": Decimal("45.00"), "ttc": Decimal("345.00")}

    consigne = facture([ligne(100, 20)], frais_emballage_ht=50, frais_emballage_mode="consigne")
    vent_consigne = ventilation_facture(consigne)
    assert total_ventilation(vent_consigne) == {"base": Decimal("150.00"), "tva": Decimal("20.00"), "ttc": Decimal("170.00")}
    declaration = {}
    ajouter_ventilation(declaration, vent_consigne)
    assert declaration == {"20": {"base": Decimal("100.00"), "tva": Decimal("20.00")}}


def test_escompte_ne_reduit_pas_une_consigne_remboursable():
    f = facture([ligne(100, 20)], frais_emballage_ht=50, frais_emballage_mode="consigne", escompte=10)
    total = total_ventilation(ventilation_facture(f))
    # 100 HT soumis à escompte -> 90 + 18 TVA, consigne 50 inchangée.
    assert total == {"base": Decimal("140.00"), "tva": Decimal("18.00"), "ttc": Decimal("158.00")}


def test_migration_protege_qualifications_et_backfill_lignes_validees():
    sql = (ROOT / "hisabpro-backend" / "033_conformite_tva_frais.sql").read_text(encoding="utf-8")
    assert "ck_lignes_facture_qualification_tva" in sql
    assert "ck_factures_transport_qualification_tva" in sql
    assert "ck_avoirs_rrr_sans_stock" in sql
    assert "DISABLE TRIGGER trg_hisabpro_guard_ligne_facture_validee" in sql
    assert "ENABLE TRIGGER trg_hisabpro_guard_ligne_facture_validee" in sql
    assert "trg_hisabpro_guard_conformite_facture_validee" in sql


def test_correctif_serialisation_bl_renvoie_id_et_ligne_bl_id():
    src = (ROOT / "hisabpro-backend" / "routers" / "commercial.py").read_text(encoding="utf-8")
    assert '"id": l.id' in src
    assert '"ligne_bl_id": l.id' in src


def test_avoirs_rrr_utilisent_les_comptes_cgnc_dedies_et_pas_le_stock():
    src = (ROOT / "hisabpro-backend" / "avoirs.py").read_text(encoding="utf-8")
    assert 'nature_avoir == "rrr"' in src
    assert '"7119" if compte.startswith("711") else "7129"' in src
    assert '"6119" if compte.startswith("611") else "6129"' in src


def test_frontend_utilise_catalogue_date_et_modes_transport_emballage():
    factures = (ROOT / "src" / "pages" / "Factures.jsx").read_text(encoding="utf-8")
    commercial = (ROOT / "src" / "pages" / "Commercial.jsx").read_text(encoding="utf-8")
    assert "tauxTVAAvecHistorique(date, l.tva)" in factures
    assert "Accessoire — TVA des lignes" in factures
    assert "Consigné / récupérable" in factures
    assert "qualification_tva" in factures
    assert "nature_avoir: natureAvoir" in factures
    assert "dateDoc={form.date}" in commercial
    assert "TAUX_TVA = [0, 7, 10, 14, 20]" not in commercial


def test_lettrage_reutilise_moteur_tva_unique():
    src = (ROOT / "hisabpro-backend" / "lettrage.py").read_text(encoding="utf-8")
    assert "ventilation_facture" in src
    assert "total_ventilation" in src
    assert "l.tva or 0" not in src


def test_acomptes_utilisent_qualification_et_validation_tva_datee():
    src = (ROOT / "hisabpro-backend" / "acomptes.py").read_text(encoding="utf-8")
    assert 'qualification_tva: str = "taxable"' in src
    assert 'valider_tva(date_ac, taux, qualification)' in src
    assert 'qualification_tva=qualification' in src
    assert 'tva_applicable=tva_applicable' in src


def test_immobilisations_acquisition_et_cession_utilisent_moteur_tva_central():
    src = (ROOT / "hisabpro-backend" / "routers" / "immobilisations.py").read_text(encoding="utf-8")
    assert 'valider_tva(data.date_acquisition, data.taux_tva, qualification_tva)' in src
    assert 'qualification_tva=qualification_tva' in src
    # La cession passe maintenant par le calcul partagé avec son aperçu927.
    # Vérifier le résultat et le refus métier, plutôt que le nom d'une variable.
    from fastapi import HTTPException
    from routers.immobilisations import _tva_sortie
    demande = SimpleNamespace(type_sortie='cession', prix_cession_ht=1000,
        date_sortie=date(2026, 1, 1), taux_tva_cession=20, qualification_tva_cession='taxable')
    assert _tva_sortie(demande) == (Decimal('1000.00'), Decimal('20'), 'taxable', Decimal('200.00'), Decimal('1200.00'))
    demande.taux_tva_cession = 14
    with pytest.raises(HTTPException) as refus:
        _tva_sortie(demande)
    assert refus.value.status_code == 400


def test_moteur_declaration_ignore_acomptes_et_immos_sans_tva():
    src = (ROOT / "hisabpro-backend" / "routers" / "tva.py").read_text(encoding="utf-8")
    assert 'est_sans_tva(getattr(a, "qualification_tva", "taxable"))' in src
    assert 'qualification_acquisition = getattr(immo, "qualification_tva", "taxable")' in src
    assert 'qualification_cession = getattr(immo, "qualification_tva_cession", "taxable")' in src


def test_frontend_acomptes_et_immobilisations_sont_date_aware():
    acomptes = (ROOT / "src" / "pages" / "Acomptes.jsx").read_text(encoding="utf-8")
    immos = (ROOT / "src" / "pages" / "Immobilisations.jsx").read_text(encoding="utf-8")
    assert 'QUALIFICATIONS_TVA' in acomptes
    assert 'tauxTVAPourDate(form.date)' in acomptes
    assert 'qualification_tva: form.qualification_tva' in acomptes
    assert 'tauxTVAAvecHistorique(form.date_acquisition, form.taux_tva)' in immos
    assert 'qualification_tva_cession' in immos
    assert 'tauxTVAPourDate(form.date_sortie)' in immos


def test_migration_conform1_verrouille_aussi_acomptes_immos_et_lignes_par_date():
    sql = (ROOT / "hisabpro-backend" / "033_conformite_tva_frais.sql").read_text(encoding="utf-8")
    assert "ALTER TABLE acomptes ADD COLUMN IF NOT EXISTS qualification_tva" in sql
    assert "ALTER TABLE immobilisations ADD COLUMN IF NOT EXISTS qualification_tva" in sql
    assert "qualification_tva_cession" in sql
    assert "hisabpro_tva_combinaison_valide" in sql
    assert "hisabpro_guard_ligne_tva_date" in sql
    assert "hisabpro_guard_frais_tva_date" in sql
    assert "NOT VALID" in sql
