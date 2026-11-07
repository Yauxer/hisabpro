# -*- coding: utf-8 -*-
"""Récupération déterministe des métadonnées FEC depuis les factures sources.

Patch 099 : certaines écritures historiques ont été créées avant le rattachement
natif des auxiliaires et avant la conservation systématique de la référence de
pièce. Lorsqu'une facture source encore présente dans HisabPro peut être
identifiée sans ambiguïté, on complète uniquement les tables append-only FEC ;
les écritures et lignes définitives ne sont jamais réécrites.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Optional

from services.fec_service import auxiliaire_fec, nettoyer, piece_fec
from services.tva_service import ventilation_facture, total_ventilation

CENTIME = Decimal("0.01")


def _enum_value(value) -> str:
    return str(getattr(value, "value", value) or "").strip()


def _money(value) -> Decimal:
    try:
        return Decimal(str(value or 0)).quantize(CENTIME, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def _facture_ttc(facture) -> Decimal:
    total = total_ventilation(ventilation_facture(facture, appliquer_escompte=True))["ttc"]
    return _money(total)


def _journal_facture(facture) -> str:
    return "VT" if _enum_value(getattr(facture, "type", None)) == "vente" else "AC"


def _montant_collectif_ecriture(ecriture) -> Decimal:
    journal = _enum_value(getattr(ecriture, "journal", None))
    prefixe = "3421" if journal == "VT" else "4411" if journal == "AC" else None
    if not prefixe:
        return Decimal("0.00")
    total = Decimal("0.00")
    for ligne in getattr(ecriture, "lignes", None) or []:
        if not str(getattr(ligne, "compte", "") or "").strip().startswith(prefixe):
            continue
        if journal == "VT":
            total += _money(getattr(ligne, "debit", 0)) - _money(getattr(ligne, "credit", 0))
        else:
            total += _money(getattr(ligne, "credit", 0)) - _money(getattr(ligne, "debit", 0))
    return _money(total)


def _reference_facture_source(facture) -> str:
    est_vente = _enum_value(getattr(facture, "type", None)) == "vente"
    if est_vente:
        return nettoyer(getattr(facture, "numero", None))
    return nettoyer(getattr(facture, "reference", None)) or nettoyer(getattr(facture, "numero", None))


def choisir_candidat_facture_exact(ecriture, candidats: Iterable) -> Optional[object]:
    """Départage les candidats date + TTC sans score ni conversion numérique.

    Une référence documentaire exacte prime sur tout indice dans le libellé.
    Plusieurs références identiques restent ambiguës. Sans référence d'écriture,
    un identifiant entier dans le libellé peut départager les candidats ; les
    frontières empêchent notamment « 02 » de correspondre à « 002 ».
    """
    candidats = list(candidats)
    ref = piece_fec(ecriture)[0].casefold()

    def references(facture):
        return {
            nettoyer(getattr(facture, champ, None)).casefold()
            for champ in ("numero", "reference")
            if nettoyer(getattr(facture, champ, None))
        }

    if ref:
        exacts = [f for f in candidats if ref in references(f)]
        # Une référence explicite incompatible ne constitue pas un match fiable.
        return exacts[0] if len(exacts) == 1 else None

    if len(candidats) == 1:
        return candidats[0]
    libelle = nettoyer(getattr(ecriture, "libelle", None)).casefold()
    explicites = [
        f for f in candidats
        if any(re.search(r"(?<!\w)" + re.escape(ref) + r"(?!\w)", libelle)
               for ref in references(f))
    ]
    return explicites[0] if len(explicites) == 1 else None


def tiers_collectif_compatible_facture(ecriture, facture, type_facture=None) -> bool:
    """Refuse une contradiction avec un tiers natif ou un complément FEC.

    Sans tiers technique de facture, ETIC peut utiliser une pièce exacte, mais
    aucun tiers n'en est déduit. La récupération FEC exige ce tiers séparément.
    """
    tiers = getattr(facture, "tiers_id", None)
    if tiers is None:
        return True
    type_facture = type_facture or _enum_value(getattr(facture, "type", None))
    prefixe = "3421" if type_facture == "vente" else "4411"
    for ligne in getattr(ecriture, "lignes", None) or []:
        if str(getattr(ligne, "compte", "") or "").strip().startswith(prefixe):
            tiers_ligne = auxiliaire_fec(ligne)[0]
            if tiers_ligne is not None and tiers_ligne != tiers:
                return False
    return True


def _metadonnees_facture_compatibles(ecriture, facture) -> bool:
    if getattr(facture, "tiers_id", None) is None or not tiers_collectif_compatible_facture(ecriture, facture):
        return False
    snapshot = nettoyer(getattr(facture, "compte_tiers_snapshot", None))
    if snapshot:
        est_vente = _enum_value(getattr(facture, "type", None)) == "vente"
        net = sum(((_money(getattr(l, "debit", 0)) - _money(getattr(l, "credit", 0)))
                   * (1 if est_vente else -1)
                   for l in getattr(ecriture, "lignes", None) or []
                   if nettoyer(getattr(l, "compte", None)) == snapshot), Decimal("0.00"))
        if _money(net) != _facture_ttc(facture):
            return False
    return True


def choisir_facture_source(ecriture, factures: Iterable, *, verifier_metadonnees=True) -> Optional[object]:
    """Retourne une facture source uniquement si le rapprochement est non ambigu."""
    journal = _enum_value(getattr(ecriture, "journal", None))
    if journal not in {"VT", "AC"}:
        return None

    montant_collectif = _montant_collectif_ecriture(ecriture)
    if montant_collectif <= 0:
        return None

    candidats = []
    for facture in factures:
        if _journal_facture(facture) != journal:
            continue
        if getattr(facture, "date", None) != getattr(ecriture, "date", None):
            continue
        if _facture_ttc(facture) != montant_collectif:
            continue
        candidats.append(facture)

    facture = choisir_candidat_facture_exact(ecriture, candidats)
    # Le FEC exige un tiers exploitable, mais son absence ne doit jamais faire
    # disparaître un candidat concurrent ou détourner une référence exacte.
    return facture if facture is not None and (not verifier_metadonnees or _metadonnees_facture_compatibles(ecriture, facture)) else None


def _ligne_collective_manquante(ligne, journal: str) -> bool:
    compte = str(getattr(ligne, "compte", "") or "").strip()
    attendu = compte.startswith("3421") if journal == "VT" else compte.startswith("4411")
    if not attendu:
        return False
    tiers_id, _nature, num_aux, lib_aux = auxiliaire_fec(ligne)
    return not (tiers_id and num_aux and lib_aux)


def recuperer_depuis_factures(db, societe_id: int, exercice: int, *, created_by=None) -> dict:
    """Complète les métadonnées FEC récupérables depuis des factures existantes.

    Aucun rapprochement ambigu n'est appliqué. Les écritures définitives restent
    inchangées ; seules ``ligne_auxiliaire_complements`` et
    ``ecriture_justificatifs`` reçoivent de nouvelles lignes append-only.
    """
    import models
    from sqlalchemy.orm import joinedload

    ecritures = (
        db.query(models.Ecriture)
        .options(
            joinedload(models.Ecriture.lignes).joinedload(models.LigneEcriture.auxiliaire_complements),
            joinedload(models.Ecriture.justificatifs),
        )
        .filter(
            models.Ecriture.societe_id == societe_id,
            models.Ecriture.exercice == int(exercice),
            models.Ecriture.est_validee.is_(True),
        )
        .order_by(models.Ecriture.date.asc(), models.Ecriture.id.asc())
        .all()
    )
    factures = (
        db.query(models.Facture)
        .options(joinedload(models.Facture.lignes))
        .filter(
            models.Facture.societe_id == societe_id,
            models.Facture.exercice == int(exercice),
        )
        .all()
    )

    tiers_ids = {int(f.tiers_id) for f in factures if getattr(f, "tiers_id", None)}
    tiers_par_id = {
        int(t.id): t
        for t in db.query(models.Tiers).filter(
            models.Tiers.societe_id == societe_id,
            models.Tiers.id.in_(tiers_ids) if tiers_ids else False,
        ).all()
    } if tiers_ids else {}

    nb_aux = 0
    nb_refs = 0
    ecritures_sourcees = set()
    non_resolus = []
    rapprochements = []
    usages_facture = {}

    # Première passe : identifier toutes les sources sans écrire. Une même facture
    # ne peut alimenter qu'une seule écriture principale VT/AC ; si elle ressort
    # sur plusieurs écritures, on considère le rapprochement comme ambigu.
    for ecriture in ecritures:
        journal = _enum_value(getattr(ecriture, "journal", None))
        if journal not in {"VT", "AC"}:
            continue

        # L'unicité porte aussi sur les écritures déjà documentées, sinon une
        # seconde écriture incomplète pourrait réutiliser leur facture source.
        facture = choisir_facture_source(ecriture, factures, verifier_metadonnees=False)
        if facture is not None:
            usages_facture[facture.id] = usages_facture.get(facture.id, 0) + 1

        lignes_manquantes = [
            ligne for ligne in (getattr(ecriture, "lignes", None) or [])
            if _ligne_collective_manquante(ligne, journal)
        ]
        ref_actuelle, _date_piece = piece_fec(ecriture)
        reference_manquante = not nettoyer(ref_actuelle)
        if not lignes_manquantes and not reference_manquante:
            continue

        if facture is None or not _metadonnees_facture_compatibles(ecriture, facture):
            non_resolus.append({
                "ecriture_id": getattr(ecriture, "id", None),
                "numero_ecriture": nettoyer(getattr(ecriture, "numero_ecriture", None)),
                "raison": "Aucune facture source unique et compatible avec le tiers/compte sur journal + date + montant TTC.",
            })
            continue
        rapprochements.append((ecriture, journal, lignes_manquantes, reference_manquante, facture))

    for ecriture, journal, lignes_manquantes, reference_manquante, facture in rapprochements:
        if usages_facture.get(facture.id, 0) != 1:
            non_resolus.append({
                "ecriture_id": getattr(ecriture, "id", None),
                "numero_ecriture": nettoyer(getattr(ecriture, "numero_ecriture", None)),
                "raison": "La même facture source correspond à plusieurs écritures ; aucune association automatique n'est appliquée.",
            })
            continue

        tiers = tiers_par_id.get(int(facture.tiers_id))
        if tiers is None:
            non_resolus.append({
                "ecriture_id": getattr(ecriture, "id", None),
                "numero_ecriture": nettoyer(getattr(ecriture, "numero_ecriture", None)),
                "raison": "Tiers de la facture source introuvable.",
            })
            continue

        nature = "client" if journal == "VT" else "fournisseur"
        for ligne in lignes_manquantes:
            # Idempotence : un appel répété ne crée pas de doublon source/ligne.
            existe = any(
                getattr(c, "source_type", None) == "facture_source_auto"
                and getattr(c, "source_id", None) == facture.id
                for c in (getattr(ligne, "auxiliaire_complements", None) or [])
            )
            if existe:
                continue
            champ_code = "code_aux_client" if nature == "client" else "code_aux_fournisseur"
            code_aux = nettoyer(getattr(tiers, champ_code, None)) or (("C" if nature == "client" else "F") + f"{int(tiers.id):08d}")
            lib_aux = nettoyer(getattr(tiers, "nom", None))
            if not code_aux or not lib_aux:
                continue
            db.add(models.LigneAuxiliaireComplement(
                societe_id=societe_id,
                ligne_ecriture_id=ligne.id,
                tiers_id=tiers.id,
                nature_auxiliaire=nature,
                compte_auxiliaire_snapshot=code_aux,
                libelle_auxiliaire_snapshot=lib_aux,
                source_type="facture_source_auto",
                source_id=facture.id,
                motif="Patch 099 : auxiliaire récupéré automatiquement depuis la facture source exacte.",
                created_by=created_by,
            ))
            nb_aux += 1
            ecritures_sourcees.add(ecriture.id)

        if reference_manquante:
            reference = _reference_facture_source(facture)
            if reference:
                existe_ref = any(
                    getattr(j, "source_type", None) == "facture_source_auto"
                    and getattr(j, "source_id", None) == facture.id
                    and nettoyer(getattr(j, "reference", None)) == reference
                    for j in (getattr(ecriture, "justificatifs", None) or [])
                )
                if not existe_ref:
                    db.add(models.EcritureJustificatif(
                        societe_id=societe_id,
                        ecriture_id=ecriture.id,
                        reference=reference,
                        date_piece=getattr(facture, "date", None) or getattr(ecriture, "date", None),
                        source_type="facture_source_auto",
                        source_id=facture.id,
                        prioritaire=True,
                        motif="Patch 099 : référence récupérée automatiquement depuis la facture source exacte.",
                        created_by=created_by,
                    ))
                    nb_refs += 1
                    ecritures_sourcees.add(ecriture.id)

    if nb_aux or nb_refs:
        db.commit()

    return {
        "exercice": int(exercice),
        "nb_ecritures_sourcees": len(ecritures_sourcees),
        "nb_auxiliaires_ajoutes": nb_aux,
        "nb_references_ajoutees": nb_refs,
        "nb_non_resolus": len(non_resolus),
        "non_resolus": non_resolus,
    }
