from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List, Optional
from datetime import date as date_cls
import json
import math
from decimal import Decimal, DecimalException
from types import SimpleNamespace
from database import get_db
from auth import get_current_user, requiert_ecriture
import models, schemas
import valorisation
from routers.cloture import exercice_est_clos
from services.tva_service import D, ZERO, money, ventilation_facture, ventilation_avoir, total_ventilation
from services.tva_regles_service import valider_tva, qualification_valide
from services.facturation_numero_service import prefixe_facture, reserver_numero
from services.commercial_numero_service import reserver_numero_commercial
from services.compta_mapping_service import (
    figer_comptes_facture, compte_tiers_facture, groupes_facture_par_compte, repartir_par_poids,
)
from services.echeancier_service import (
    echeances_persistantes_ou_defaut, normaliser_echeances, remplacer_echeancier_db, supprimer_echeancier_db,
    repartition_fifo,
)
from services.exercices_service import verifier_date_ecriture, trouver_exercice_pour_date
from services.auxiliaire_service import rattacher_tiers_aux_lignes
from services.identifiants_maroc_service import normaliser_ice, normaliser_if, normaliser_tp
from services.mentions_identite_facture_service import mentions_identite_manquantes

router = APIRouter(prefix="/api/factures", tags=["factures"])

from services import factures_conservation_service as conservation


@router.get('/{facture_id}/copie-conservee')
def consulter_copie_conservee(facture_id:int,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    return conservation.consulter(db,current_user,facture_id)


@router.post('/{facture_id}/copie-conservee',status_code=201)
def conserver_copie_facture(facture_id:int,data:conservation.Conservation,current_user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    return conservation.conserver(db,current_user,facture_id,data,generer_pdf_facture)


@router.get('/{facture_id}/copie-conservee/pdf')
def telecharger_copie_conservee(facture_id:int,current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    return conservation.telecharger(db,current_user,facture_id)


_SOCIETE_SNAPSHOT_CHAMPS = (
    "raison_sociale", "identifiant_fiscal", "ice", "rc", "patente", "cnss_numero",
    "adresse", "ville", "pays", "telephone", "fax", "email", "site_web",
    "forme_juridique", "capital_social", "banque", "agence", "rib", "logo_url",
)


def _verifier_date_facture_finale(db, societe_id, facture):
    if facture.date > date_cls.today():
        raise HTTPException(422, "La date d'une facture définitive ne peut pas être future.")
    try:
        exercice = verifier_date_ecriture(db, societe_id, facture.date, "valider cette facture")
    except ValueError as exc:
        raise HTTPException(423, str(exc)) from exc
    facture.exercice = exercice.annee
    return exercice


def _figer_identites_facture(db, societe_id, facture, *, verifier_mentions=True):
    """Rafraîchit puis fige vendeur et tiers juste avant émission définitive."""
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    if not societe:
        raise HTTPException(404, "Société introuvable")

    est_vente = getattr(getattr(facture, "type", None), "value", getattr(facture, "type", None)) == "vente"
    # Les mentions d'identification manquantes sont signalées à l'utilisateur,
    # mais ne rendent plus impossible la validation d'une facture de recette.
    # Les valeurs réelles (même absentes) sont figées dans le PDF : jamais de
    # substitution fictive ; l'absence ne signifie pas conformité légale.
    avertissements_mentions = []

    try:
        societe_ice = normaliser_ice(societe.ice) if societe.ice else None
        societe_if = normaliser_if(societe.identifiant_fiscal) if societe.identifiant_fiscal else None
        societe_tp = normaliser_tp(societe.patente) if societe.patente else None
    except ValueError as exc:
        raise HTTPException(422, f"Identité société invalide : {exc}") from exc

    societe_snapshot = {k: getattr(societe, k, None) for k in _SOCIETE_SNAPSHOT_CHAMPS}
    societe_snapshot["ice"] = societe_ice
    societe_snapshot["identifiant_fiscal"] = societe_if
    societe_snapshot["patente"] = societe_tp
    facture.societe_snapshot_json = json.dumps(societe_snapshot, ensure_ascii=False, default=str)
    facture.notes_snapshot = facture.notes

    tiers = None
    if facture.tiers_id:
        tiers = db.query(models.Tiers).filter_by(id=facture.tiers_id, societe_id=societe_id, actif=True).first()
    if est_vente and not tiers:
        raise HTTPException(422, "Sélectionnez un client enregistré avant de valider la facture.")
    if tiers:
        categorie = (getattr(tiers, "categorie_fiscale", None) or "indetermine").lower()
        try:
            tiers_ice = normaliser_ice(tiers.ice) if tiers.ice else None
            tiers_if = normaliser_if(tiers.identifiant_fiscal) if tiers.identifiant_fiscal else None
        except ValueError as exc:
            raise HTTPException(422, f"Identité du tiers invalide : {exc}") from exc
        facture.tiers = tiers.nom
        facture.tiers_ice_snapshot = tiers_ice
        facture.tiers_if_snapshot = tiers_if
        facture.tiers_rc_snapshot = tiers.rc
        facture.tiers_adresse_snapshot = tiers.adresse
        facture.tiers_ville_snapshot = tiers.ville
        facture.tiers_telephone_snapshot = tiers.telephone
        facture.tiers_email_snapshot = tiers.email
        facture.tiers_categorie_snapshot = categorie
    if verifier_mentions:
        avertissements_mentions = mentions_identite_manquantes(
            societe, tiers, est_vente=est_vente
        )
    return avertissements_mentions


def _resoudre_tiers_facture(db, societe_id, tiers_id=None, nom=None, est_vente=True):
    type_attendu = "client" if est_vente else "fournisseur"
    if tiers_id:
        tiers = db.query(models.Tiers).filter_by(id=tiers_id, societe_id=societe_id, actif=True).first()
        if not tiers:
            raise HTTPException(422, "Le client/fournisseur sélectionné est introuvable pour cette société.")
        if tiers.type not in {type_attendu, "les_deux"}:
            raise HTTPException(422, f"Le tiers sélectionné n'est pas configuré comme {type_attendu}.")
        return tiers
    if nom:
        candidats = db.query(models.Tiers).filter(
            models.Tiers.societe_id == societe_id, models.Tiers.actif == True,
            models.Tiers.nom.ilike(nom.strip()),
        ).all()
        if len(candidats) == 1 and candidats[0].type in {type_attendu, "les_deux"}:
            return candidats[0]
    return None


def _article_facture(db, societe_id, article_id=None, description=None):
    if article_id:
        art = db.query(models.Article).filter_by(id=article_id, societe_id=societe_id, actif=True).first()
        if not art:
            raise HTTPException(422, "L'article sélectionné est introuvable pour cette société.")
        return art
    if description:
        candidats = db.query(models.Article).filter(
            models.Article.societe_id == societe_id, models.Article.actif == True,
            models.Article.designation.ilike(description.strip()),
        ).all()
        if len(candidats) == 1:
            return candidats[0]
    return None


def _statut_facture_actif(f):
    statut = getattr(getattr(f, "statut", None), "value", getattr(f, "statut", None))
    return statut != "annulee" and not bool(getattr(f, "est_proforma", False))


def _verifier_reliquats_sources(db, societe_id, lignes, exclure_facture_id=None):
    """Empêche toute surfacturation d'une ligne BC ou BL/BR.

    Les liens FACT.1 rendent le contrôle indépendant de la désignation texte.
    Une facture sans document source reste autorisée comme facture directe.
    """
    demandes_bc = {}
    demandes_bl = {}
    for l in lignes or []:
        qte = float(getattr(l, "quantite", 0) or 0)
        if qte <= 0:
            continue
        bc_id = getattr(l, "source_ligne_bc_id", None)
        bl_id = getattr(l, "source_ligne_bl_id", None)
        if bc_id:
            demandes_bc[bc_id] = demandes_bc.get(bc_id, 0.0) + qte
        if bl_id:
            demandes_bl[bl_id] = demandes_bl.get(bl_id, 0.0) + qte

    def deja_facture(source_field, source_id):
        rows = db.query(models.LigneFacture, models.Facture).join(
            models.Facture, models.Facture.id == models.LigneFacture.facture_id
        ).filter(getattr(models.LigneFacture, source_field) == source_id,
                 models.Facture.societe_id == societe_id).all()
        total = 0.0
        for lf, f in rows:
            if exclure_facture_id and f.id == exclure_facture_id:
                continue
            if _statut_facture_actif(f):
                total += float(lf.quantite or 0)
        return total

    for ligne_id, demandee in demandes_bl.items():
        ligne = db.query(models.LigneBonLivraison).join(
            models.BonLivraison, models.BonLivraison.id == models.LigneBonLivraison.bon_livraison_id
        ).filter(models.LigneBonLivraison.id == ligne_id,
                 models.BonLivraison.societe_id == societe_id).first()
        if not ligne:
            raise HTTPException(422, "Une ligne de bon de livraison/réception source est introuvable.")
        maximum = float(ligne.quantite_livree if ligne.quantite_livree is not None else (ligne.quantite_prevue or 0))
        deja = deja_facture("source_ligne_bl_id", ligne_id)
        if deja + demandee > maximum + 0.0001:
            raise HTTPException(409,
                f"{ligne.description} : quantité facturée {deja + demandee:g} supérieure à la quantité livrée/réceptionnée {maximum:g}.")

    for ligne_id, demandee in demandes_bc.items():
        ligne = db.query(models.LigneBonCommande).join(
            models.BonCommande, models.BonCommande.id == models.LigneBonCommande.bon_commande_id
        ).filter(models.LigneBonCommande.id == ligne_id,
                 models.BonCommande.societe_id == societe_id).first()
        if not ligne:
            raise HTTPException(422, "Une ligne de bon de commande source est introuvable.")
        maximum = float(ligne.quantite or 0)
        deja = deja_facture("source_ligne_bc_id", ligne_id)
        if deja + demandee > maximum + 0.0001:
            raise HTTPException(409,
                f"{ligne.description} : quantité facturée {deja + demandee:g} supérieure à la quantité commandée {maximum:g}.")


def _verifier_sources_facture_societe(db, societe_id, lignes):
    """FACT-A / F-031 — chaque identifiant source d'une ligne de facture doit
    appartenir à la société courante, même lorsqu'un autre lien source est aussi
    présent sur la même ligne.
    """
    for ligne in lignes or []:
        devis_id = getattr(ligne, "source_ligne_devis_id", None)
        if devis_id:
            ok = db.query(models.LigneDevis).join(
                models.Devis, models.Devis.id == models.LigneDevis.devis_id
            ).filter(
                models.LigneDevis.id == devis_id,
                models.Devis.societe_id == societe_id,
            ).first()
            if not ok:
                raise HTTPException(422, "Une ligne de devis source est introuvable pour cette société.")

        bc_id = getattr(ligne, "source_ligne_bc_id", None)
        if bc_id:
            ok = db.query(models.LigneBonCommande).join(
                models.BonCommande, models.BonCommande.id == models.LigneBonCommande.bon_commande_id
            ).filter(
                models.LigneBonCommande.id == bc_id,
                models.BonCommande.societe_id == societe_id,
            ).first()
            if not ok:
                raise HTTPException(422, "Une ligne de bon de commande source est introuvable pour cette société.")

        bl_id = getattr(ligne, "source_ligne_bl_id", None)
        if bl_id:
            ok = db.query(models.LigneBonLivraison).join(
                models.BonLivraison, models.BonLivraison.id == models.LigneBonLivraison.bon_livraison_id
            ).filter(
                models.LigneBonLivraison.id == bl_id,
                models.BonLivraison.societe_id == societe_id,
            ).first()
            if not ok:
                raise HTTPException(422, "Une ligne de bon de livraison/réception source est introuvable pour cette société.")


def _verifier_conversion_directe_devis(db, societe_id, lignes):
    """Protège la conversion directe Devis -> Facture contre les doublons.

    Une ligne qui possède déjà une source BC/BL suit le cycle normal BC/BL et
    n'est donc pas considérée comme une facturation directe du devis.
    """
    ids_lignes = {
        int(getattr(l, "source_ligne_devis_id"))
        for l in (lignes or [])
        if getattr(l, "source_ligne_devis_id", None)
        and not getattr(l, "source_ligne_bc_id", None)
        and not getattr(l, "source_ligne_bl_id", None)
    }
    if not ids_lignes:
        return

    lignes_sources = db.query(models.LigneDevis).join(
        models.Devis, models.Devis.id == models.LigneDevis.devis_id
    ).filter(
        models.LigneDevis.id.in_(ids_lignes),
        models.Devis.societe_id == societe_id,
    ).all()
    if len(lignes_sources) != len(ids_lignes):
        raise HTTPException(422, "Une ligne de devis source est introuvable.")

    devis_ids = {l.devis_id for l in lignes_sources}
    if len(devis_ids) != 1:
        raise HTTPException(422, "Une facture directe ne peut pas regrouper plusieurs devis sources.")
    devis_id = next(iter(devis_ids))

    # Verrou commun avec la conversion Devis -> BC : les deux chemins ne peuvent
    # pas créer simultanément des documents concurrents pour le même devis.
    devis = db.query(models.Devis).filter_by(
        id=devis_id, societe_id=societe_id
    ).with_for_update().first()
    if not devis:
        raise HTTPException(422, "Devis source introuvable.")
    if getattr(getattr(devis, "statut", None), "value", getattr(devis, "statut", None)) != "accepte":
        raise HTTPException(409, "Seul un devis accepté peut être converti directement en facture.")

    bc = db.query(models.BonCommande).filter_by(
        societe_id=societe_id, devis_id=devis_id
    ).first()
    if bc:
        raise HTTPException(
            409,
            f"Le devis a déjà généré le bon de commande {bc.numero}. "
            "Poursuivez la facturation depuis ce BC ou ses bons de livraison/réception."
        )

    facture_existante = db.query(models.Facture).join(
        models.LigneFacture, models.LigneFacture.facture_id == models.Facture.id
    ).join(
        models.LigneDevis, models.LigneDevis.id == models.LigneFacture.source_ligne_devis_id
    ).filter(
        models.Facture.societe_id == societe_id,
        models.LigneDevis.devis_id == devis_id,
        models.LigneFacture.source_ligne_bc_id.is_(None),
        models.LigneFacture.source_ligne_bl_id.is_(None),
    ).order_by(models.Facture.id.asc()).all()
    facture_existante = next((f for f in facture_existante if _statut_facture_actif(f)), None)
    if facture_existante:
        libelle = facture_existante.numero or f"brouillon #{facture_existante.id}"
        raise HTTPException(409, f"Une facture ({libelle}) existe déjà pour ce devis.")


def _calc_totaux(f):
    """Refuse une source inconnue plutôt que fabriquer un montant financier."""
    try:
        for champ in ("remise_globale", "ristourne", "escompte", "frais_transport_ht",
                      "frais_transport_tva", "frais_emballage_ht", "frais_emballage_tva"):
            valeur = getattr(f, champ, None)
            if valeur is not None:
                schemas._nombre_fini(valeur)
        for ligne in f.lignes or []:
            for champ in ("quantite", "prix_unitaire", "tva", "remise", "remise2", "rabais"):
                valeur = getattr(ligne, champ, None)
                if champ in {"quantite", "prix_unitaire", "tva"} or valeur is not None:
                    schemas._nombre_fini(valeur)
            if ligne.quantite <= 0 or ligne.prix_unitaire < 0:
                raise ValueError("Quantité ou prix historique invalide")
        valeurs = _calc_totaux_non_qualifies(f)
        montants = list(valeurs)
        for ligne in f.lignes or []:
            montants.extend(_montants_ligne_affichage(ligne))
        if not all(math.isfinite(v) for v in montants):
            raise OverflowError
        return valeurs
    except (DecimalException, OverflowError, ValueError, TypeError) as exc:
        raise HTTPException(422, "Montants historiques inconnus ou non représentables : vérifiez les données sources de la facture.") from exc


def _calc_totaux_non_qualifies(f):
    """Totaux facture cohérents avec le moteur TVA structuré.

    ``total_ht`` reste le net commercial avant escompte (utile pour la lecture
    comptable de la facture), tandis que la TVA et le TTC sont calculés sur le
    net financier après escompte de règlement.
    """
    avant_escompte = total_ventilation(
        ventilation_facture(f, appliquer_escompte=False)
    )
    apres_escompte = total_ventilation(
        ventilation_facture(f, appliquer_escompte=True)
    )
    remise_g = getattr(f, 'remise_globale', 0) or 0
    escompte = getattr(f, 'escompte', 0) or 0
    return (
        float(avant_escompte["base"]),
        float(apres_escompte["tva"]),
        float(apres_escompte["ttc"]),
        remise_g,
        escompte,
    )


def _verifier_montants_representables(facture):
    """Vérifie le moteur existant avant mutation, sans modifier ses calculs."""
    try:
        for champ in ("remise_globale", "ristourne", "escompte", "frais_transport_ht", "frais_emballage_ht"):
            valeur = getattr(facture, champ, None)
            if valeur is not None:
                schemas._nombre_fini(valeur)
        for ligne in facture.lignes or []:
            for champ in ("quantite", "prix_unitaire", "remise", "remise2", "rabais"):
                valeur = getattr(ligne, champ, None)
                if valeur is not None:
                    schemas._nombre_fini(valeur)
        valeurs = list(_calc_totaux(facture))
        for ligne in facture.lignes or []:
            valeurs.extend(_montants_ligne_affichage(ligne))
        if not all(math.isfinite(v) for v in valeurs):
            raise OverflowError
    except (DecimalException, OverflowError, ValueError) as exc:
        raise HTTPException(422, "Les montants calculés de la facture ne sont pas représentables par le moteur de calcul.") from exc


def _libelle_ecriture(db, societe_id, cle, numero="", tiers="", ref="", date_doc=None):
    """Construit le libellé d'une écriture selon le format paramétré par la société.

    Variables reconnues : {numero} {tiers} {ref} {date}
    cle : "vente" | "achat" | "avoir" | "banque"
    """
    DEFAUTS = {
        "vente":  "Facture {numero} {tiers}",
        "achat":  "Facture d'achat {numero} {tiers}",
        "avoir":  "Avoir {numero} {tiers}",
        "banque": "Règlement {tiers} {ref}",
    }
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    modele = getattr(societe, f"format_libelle_{cle}", None) or DEFAUTS.get(cle, "{numero} {tiers}")
    try:
        libelle = modele.format(
            numero=numero or "",
            tiers=tiers or "",
            ref=ref or "",
            date=date_doc.strftime("%d/%m/%Y") if date_doc else "",
        )
    except (KeyError, IndexError, ValueError):
        # Format invalide (variable inconnue, accolade orpheline) : on retombe sur le défaut
        libelle = DEFAUTS.get(cle, "{numero} {tiers}").format(
            numero=numero or "", tiers=tiers or "", ref=ref or "", date="")
    # Nettoie les espaces multiples laissés par une variable vide
    return " ".join(libelle.split()).strip()


def _encours_tiers(db, societe_id, nom_tiers, est_vente, exclure_facture_id=None):
    """Somme des factures ouvertes d'un tiers (créance client ou dette fournisseur)."""
    OUVERTES = ("en_attente", "partiellement_payee", "retard")
    q = db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.tiers == nom_tiers,
        models.Facture.type == ("vente" if est_vente else "achat"),
        models.Facture.statut.in_(OUVERTES),
        models.Facture.est_validee == True,
    )
    if exclure_facture_id:
        q = q.filter(models.Facture.id != exclure_facture_id)

    encours = 0.0
    for f in q.all():
        if getattr(f, "est_proforma", False):
            continue
        # FACT-D : l'encours crédit doit utiliser exactement le même calcul que
        # le solde facture. Les règlements rejetés ne réduisent donc jamais le
        # plafond, et les avoirs/acomptes/RAS sont pris en compte.
        situation = _situation_paiement_facture(db, societe_id, f)
        encours += situation["solde_restant"]
    return encours


def _controler_plafond_credit(db, societe_id, nom_tiers, est_vente, montant_ttc,
                              exclure_facture_id=None):
    """Bloque la facturation si l'encours dépasse le plafond de crédit du tiers.

    Un plafond à 0 (ou absent) signifie « pas de limite ».
    """
    tiers = db.query(models.Tiers).filter_by(
        societe_id=societe_id, nom=nom_tiers, actif=True).first()
    plafond = getattr(tiers, "plafond_credit", 0) or 0 if tiers else 0
    if plafond <= 0:
        return

    encours = _encours_tiers(db, societe_id, nom_tiers, est_vente, exclure_facture_id)
    nouveau = encours + (montant_ttc or 0)
    if nouveau > plafond + 0.01:
        raise HTTPException(400,
            f"Plafond de crédit dépassé pour {nom_tiers} : "
            f"encours actuel {encours:,.2f} MAD + {montant_ttc:,.2f} MAD = {nouveau:,.2f} MAD, "
            f"pour un plafond de {plafond:,.2f} MAD."
            .replace(",", " "))


def _stock_sur_facture(db, societe_id, est_vente):
    """True si le mouvement de stock se fait à la facturation (paramètre société).
    Sinon il se fera au passage du BL (vente) / BR (achat) au statut livré."""
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    if est_vente:
        return (getattr(societe, "stock_declencheur_vente", None) or "facture") == "facture"
    return (getattr(societe, "stock_declencheur_achat", None) or "facture") == "facture"


def _verifier_doublon_facture_fournisseur(db, societe_id, facture, exclure_id=None, seulement_validees=True):
    """Détecte un doublon de numéro de facture fournisseur sur le même exercice."""
    type_value = getattr(getattr(facture, "type", None), "value", getattr(facture, "type", None))
    if type_value != "achat" or getattr(facture, "est_proforma", False):
        return
    ref = (getattr(facture, "reference", None) or "").strip()
    if not ref or not getattr(facture, "tiers_id", None):
        return
    q = db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.type == "achat",
        models.Facture.est_proforma == False,
        models.Facture.tiers_id == facture.tiers_id,
        models.Facture.exercice == facture.exercice,
        models.Facture.reference.ilike(ref),
    )
    if seulement_validees:
        q = q.filter(models.Facture.est_validee == True)
    if exclure_id:
        q = q.filter(models.Facture.id != exclure_id)
    doublon = q.first()
    if doublon:
        lib = doublon.numero or f"Brouillon #{doublon.id}"
        raise HTTPException(409,
            f"Facture fournisseur en doublon : le numéro « {ref} » existe déjà "
            f"pour ce fournisseur sur l'exercice {facture.exercice} ({lib}).")


def _calculer_date_echeance(date_facture, delai_paiement=60, date_echeance=None):
    from datetime import timedelta
    delai = 60 if delai_paiement is None else int(delai_paiement)
    if delai < 0:
        raise HTTPException(422, "Le délai de paiement ne peut pas être négatif.")
    if delai > 365:
        raise HTTPException(422, "Le délai de paiement ne peut pas dépasser 365 jours.")
    if date_echeance:
        if date_echeance < date_facture:
            raise HTTPException(422, "L'échéance ne peut pas précéder la date de facture.")
        return date_echeance
    return date_facture + timedelta(days=delai)


def _alerte_delai_paiement(delai_paiement):
    """Avertissement non bloquant : au-delà de 120 jours, une convention ou
    dérogation sectorielle doit être vérifiée au regard de la loi 69-21."""
    try:
        jours = int(delai_paiement or 0)
    except (TypeError, ValueError):
        return None
    if jours > 120:
        return "Délai supérieur à 120 jours : vérifiez la convention ou la dérogation sectorielle applicable (loi 69-21)."
    return None


def _verifier_conformite_tva_facture(facture):
    """CONFORM.1 — contrôle date/taux/qualification avant validation/sauvegarde."""
    try:
        for ligne in getattr(facture, "lignes", []) or []:
            valider_tva(facture.date, getattr(ligne, "tva", 0), getattr(ligne, "qualification_tva", "taxable"))
        mode_t = (getattr(facture, "frais_transport_mode", None) or "accessoire").lower()
        if mode_t not in {"accessoire", "distinct"}:
            raise ValueError("Nature des frais de transport invalide.")
        if D(getattr(facture, "frais_transport_ht", 0)) > ZERO and mode_t == "distinct":
            valider_tva(facture.date, getattr(facture, "frais_transport_tva", 0), getattr(facture, "frais_transport_qualification_tva", "taxable"))
        mode_e = (getattr(facture, "frais_emballage_mode", None) or "perdu").lower()
        if mode_e not in {"perdu", "consigne", "vente_distincte"}:
            raise ValueError("Nature des frais d'emballage invalide.")
        if D(getattr(facture, "frais_emballage_ht", 0)) > ZERO and mode_e == "vente_distincte":
            valider_tva(facture.date, getattr(facture, "frais_emballage_tva", 0), getattr(facture, "frais_emballage_qualification_tva", "taxable"))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def _cout_entree_avec_frais(db, societe_id, facture, ligne):
    """Coût d'acquisition unitaire incluant les frais directement attribuables.

    Les frais de transport d'approvisionnement et l'emballage perdu sont répartis
    sur les seules lignes stockables, au prorata de leur coût commercial net.
    La consignation reste une créance et n'entre jamais dans le CMUP.
    """
    base_unitaire = D(valorisation.cout_net_ligne(ligne))
    qte = max(D(getattr(ligne, "quantite", 0)), ZERO)
    if qte <= ZERO:
        return float(base_unitaire)
    article = _article_facture(db, societe_id, getattr(ligne, "article_id", None), getattr(ligne, "description", None))
    if not article or not getattr(article, "is_stockable", False):
        return float(base_unitaire)
    frais = D(getattr(facture, "frais_transport_ht", 0))
    if (getattr(facture, "frais_emballage_mode", None) or "perdu") != "consigne":
        frais += D(getattr(facture, "frais_emballage_ht", 0))
    if frais <= ZERO:
        return float(base_unitaire)
    poids = {}
    total = ZERO
    for lf in getattr(facture, "lignes", []) or []:
        art = _article_facture(db, societe_id, getattr(lf, "article_id", None), getattr(lf, "description", None))
        if not art or not getattr(art, "is_stockable", False):
            continue
        p = D(valorisation.cout_net_ligne(lf)) * max(D(getattr(lf, "quantite", 0)), ZERO)
        if p > ZERO:
            poids[lf.id] = p
            total += p
    if total <= ZERO or getattr(ligne, "id", None) not in poids:
        return float(base_unitaire)
    part_ligne = frais * poids[ligne.id] / total
    return float((base_unitaire + part_ligne / qte).quantize(D("0.0001")))


def _montants_ligne_affichage(ligne):
    q = D(getattr(ligne, "quantite", 0)); pu = D(getattr(ligne, "prix_unitaire", 0))
    r1 = D(getattr(ligne, "remise", 0))/D(100); r2 = D(getattr(ligne, "remise2", 0))/D(100); rb = D(getattr(ligne, "rabais", 0))
    ht = max(q*pu*(D(1)-r1)*(D(1)-r2)-rb*q, ZERO)
    taux = D(getattr(ligne, "tva", 0)) if (getattr(ligne, "qualification_tva", "taxable") == "taxable") else ZERO
    tv = ht*taux/D(100)
    return float(money(ht)), float(money(tv)), float(money(ht) + money(tv))


def _mouvements_stock_validation_facture(db, societe_id, facture, user_id=None):
    """Applique le stock au moment où la facture devient définitive."""
    _verifier_conformite_tva_facture(facture)
    est_vente = facture.type == "vente"
    if not _stock_sur_facture(db, societe_id, est_vente):
        return
    for ligne in facture.lignes:
        article = _article_facture(db, societe_id, ligne.article_id, ligne.description)
        if article is None or not article.is_stockable:
            continue
        if est_vente and (article.stock_actuel or 0) + 1e-9 < float(ligne.quantite or 0):
            raise HTTPException(409,
                f"Stock insuffisant pour valider la facture : {ligne.description} — "
                f"disponible {article.stock_actuel or 0:g}, demandé {ligne.quantite or 0:g}.")
        try:
            valorisation.enregistrer_mouvement(
                db, societe_id, article,
                "sortie" if est_vente else "entree", ligne.quantite,
                reference=facture.numero,
                note=f"{'Vente' if est_vente else 'Achat'} — {facture.tiers}",
                facture_id=facture.id,
                cout_unitaire=(None if est_vente else _cout_entree_avec_frais(db, societe_id, facture, ligne)),
                date_mouvement=facture.date,
                source_type="facture", source_id=facture.id,
                source_ligne_id=ligne.id,
                cle_idempotence=f"facture:{facture.id}:ligne:{ligne.id}",
                user_id=user_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc))


def _montant_ras(f, total_ht):
    """Retenue à la source : assiette = total HT (prestations), taux porté par la facture."""
    taux = getattr(f, 'ras_taux', 0) or 0
    try:
        schemas._taux_ras_fini(taux)
    except ValueError as exc:
        raise HTTPException(409, "Taux RAS historique invalide : vérifier la facture avant tout calcul financier.") from exc
    return total_ht * taux / 100 if taux > 0 else 0


def _lecture_ras(f, total_ht, total_ttc):
    """Expose le calcul existant, ou son impossibilité sans réparer l'historique."""
    try:
        montant = _montant_ras(f, total_ht)
    except HTTPException as exc:
        return {"ras_taux": None, "montant_ras": None, "net_a_payer": None,
                "ras_anomalie": exc.detail}
    return {"ras_taux": getattr(f, "ras_taux", 0) or 0,
            "montant_ras": montant, "net_a_payer": total_ttc - montant,
            "ras_anomalie": None}


def _total_avoir_qualifie(avoir):
    """Même ventilation existante, avec refus explicite des sources inconnues."""
    try:
        for champ in ("remise_globale_snapshot", "ristourne_snapshot", "escompte_snapshot"):
            valeur = getattr(avoir, champ, None)
            if valeur is not None:
                schemas._nombre_fini(valeur)
        for ligne in avoir.lignes or []:
            force = getattr(ligne, "montant_ht_force", None)
            if force is not None:
                schemas._nombre_fini(force)
            for champ in ("quantite", "prix_unitaire", "tva", "remise", "remise2", "rabais"):
                valeur = getattr(ligne, champ, None)
                if valeur is not None or champ == "tva" or (force is None and champ in {"quantite", "prix_unitaire"}):
                    schemas._nombre_fini(valeur)
        total = float(total_ventilation(ventilation_avoir(avoir, appliquer_escompte=True))["ttc"])
        if not math.isfinite(total):
            raise OverflowError
        return total
    except (DecimalException, OverflowError, ValueError, TypeError) as exc:
        raise HTTPException(422, "Montants historiques de l'avoir lié à vérifier.") from exc


def _credit_facture(db, societe_id: int, facture, total_ttc: float):
    """Situation d'avoir dérivée, sans détourner le statut de paiement historique."""
    avoirs = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)) \
        .filter_by(facture_id=facture.id, societe_id=societe_id) \
        .filter(models.Avoir.statut != "annule").all()
    total_avoirs = sum(_total_avoir_qualifie(a) for a in avoirs)
    if total_avoirs <= 0.01:
        statut_credit = "aucun"
    elif total_avoirs >= float(total_ttc or 0) - 0.02:
        statut_credit = "totalement_creditee"
    else:
        statut_credit = "partiellement_creditee"
    return total_avoirs, statut_credit


def _lecture_facture(db, societe_id, f):
    """Projection JSON sans mutation ORM ; une pièce défaillante reste visible."""
    anomalies = []

    def nombre(valeur, libelle):
        if valeur is None:
            return None
        try:
            return schemas._nombre_fini(valeur)
        except ValueError:
            anomalies.append(f"{libelle} : valeur non finie ou non représentable.")
            return None

    row = dict(f.__dict__)
    row["date_prochaine_echeance"] = None
    for champ, valeur in list(row.items()):
        if isinstance(valeur, (float, Decimal)):
            if champ == "ras_taux":
                # La RAS possède déjà sa qualification propre, indépendante du TTC.
                try:
                    schemas._taux_ras_fini(valeur)
                except ValueError:
                    row[champ] = None
            else:
                row[champ] = nombre(valeur, champ)
    lignes = []
    for ligne in f.lignes:
        item = dict(ligne.__dict__)
        for champ in ("quantite", "prix_unitaire", "tva", "remise", "remise2", "rabais"):
            item[champ] = nombre(getattr(ligne, champ, None), f"Ligne {ligne.id}, {champ}")
        try:
            # Les données nécessaires sont contrôlées par le calcul facture.
            schemas.LigneFactureCreate.model_validate(item)
            montants = _montants_ligne_affichage(ligne)
            if not all(math.isfinite(v) for v in montants):
                raise ValueError
        except (DecimalException, OverflowError, ValueError, TypeError):
            anomalies.append(f"Ligne {ligne.id} : montants à vérifier dans la pièce source.")
            montants = (None, None, None)
        item.update(zip(("montant_ht", "montant_tva", "montant_ttc"), montants))
        lignes.append(item)
    echeances = []
    for e in f.echeances:
        echeances.append({"id": e.id, "ordre": e.ordre, "date_echeance": e.date_echeance,
                          "montant": nombre(e.montant, f"Échéance {e.id}"), "libelle": e.libelle})
        if e.montant is None:
            anomalies.append(f"Échéance {e.id} : montant manquant.")
    try:
        if anomalies:
            raise HTTPException(422, "Montants sources à vérifier.")
        total_ht, total_tva, total_net, remise_g, escompte = _calc_totaux(f)
        ras = _lecture_ras(f, total_ht, total_net)
        total_avoirs, statut_credit = _credit_facture(db, societe_id, f, total_net)
        situation = _situation_paiement_facture(db, societe_id, f, tolere_ras_invalide=True)
        finances = (total_avoirs, situation["total_encaisse"], situation["total_reglement_en_cours"])
        if not all(math.isfinite(v) for v in finances):
            raise ValueError("Situation de règlement non finie")
        if not echeances:
            echeances = echeances_persistantes_ou_defaut(f, total_net)
        if situation["total_effectif"] is not None and math.isfinite(situation["total_effectif"]):
            repartition = repartition_fifo(echeances, situation["total_effectif"])
            prochaine = repartition["prochaine_echeance"]
            row["date_prochaine_echeance"] = prochaine["date_echeance"] if prochaine else None
        row.update(total_ht=total_ht, total_tva=total_tva, total_ttc=total_net,
                   total_avoirs=total_avoirs, statut_credit=statut_credit,
                   total_encaisse=situation["total_encaisse"],
                   total_reglement_en_cours=situation["total_reglement_en_cours"],
                   remise_globale=remise_g, escompte=escompte, **ras)
    except (HTTPException, DecimalException, OverflowError, ValueError, TypeError) as exc:
        if isinstance(exc, HTTPException) and exc.status_code != 422:
            raise
        anomalies.append("Calcul financier indisponible : vérifier la facture et ses documents liés.")
        row.update({champ: None for champ in ("total_ht", "total_tva", "total_ttc", "total_avoirs",
                   "statut_credit", "total_encaisse", "total_reglement_en_cours", "montant_ras", "net_a_payer")})
        row["ras_anomalie"] = "Calcul RAS indisponible : montants sources à vérifier."
    row.update(lignes=lignes, echeances=echeances, montants_valides=not anomalies,
               anomalies_montants=list(dict.fromkeys(anomalies)),
               alerte_delai_paiement=_alerte_delai_paiement(f.delai_paiement))
    return row


@router.get("", response_model=List[schemas.FactureLectureOut])
def lister_factures(
    exercice: int           = Query(...),
    type:     Optional[str] = Query(None),
    statut:   Optional[str] = Query(None),
    recherche: Optional[str]= Query(None),
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Facture)
        .options(joinedload(models.Facture.lignes), joinedload(models.Facture.echeances))
        .filter_by(societe_id=current_user["societe_id"])
        .filter(models.Facture.exercice == exercice)
    )
    if type:
        q = q.filter(models.Facture.type == type)
    if statut:
        q = q.filter(models.Facture.statut == statut)
    if recherche:
        q = q.filter(
            models.Facture.numero.ilike(f"%{recherche}%") |
            models.Facture.tiers.ilike(f"%{recherche}%")
        )
    factures = q.order_by(models.Facture.created_at.desc().nullslast(), models.Facture.id.desc()).offset(skip).limit(limit).all()

    return [_lecture_facture(db, current_user["societe_id"], f) for f in factures]


@router.post("", response_model=schemas.FactureOut, status_code=201)
def creer_facture(
    data: schemas.FactureCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    resultat = creer_brouillon_facture(data, current_user, db)
    db.commit()
    return resultat


def creer_brouillon_facture(data, current_user, db):
    """Crée une facture en brouillon.

    FACT.4 : une facture définitive n'obtient son numéro qu'à la validation.
    Les proformas conservent une numérotation propre, attribuée atomiquement dès
    leur création puisqu'elles restent des documents commerciaux modifiables.
    """
    candidat = SimpleNamespace(**data.model_dump(exclude={"lignes"}), lignes=data.lignes)
    # Même valeur de repli que les snapshots créés ci-dessous.
    for champ in ("frais_transport_tva", "frais_emballage_tva"):
        if getattr(candidat, champ, None) is None:
            setattr(candidat, champ, 20)
    _verifier_montants_representables(candidat)
    societe_id = current_user["societe_id"]
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    est_vente = data.type == "vente"
    est_proforma = bool(getattr(data, "est_proforma", False))

    # FACT-A / F-005 — le statut initial n'est pas pilotable par le client API.
    statut_demande = getattr(getattr(data, "statut", None), "value", getattr(data, "statut", None))
    if statut_demande not in {None, "en_attente"}:
        raise HTTPException(status_code=422, detail="Une nouvelle facture doit être créée avec le statut 'en_attente'.")

    regime_tva_snapshot = (getattr(societe, "regime_tva", None) or "encaissement").lower()
    nature_tva_achat = (getattr(data, "nature_tva_achat", "charge") or "charge")
    if nature_tva_achat not in {"charge", "immobilisation", "non_deductible"}:
        raise HTTPException(status_code=400, detail="Nature TVA achat invalide")
    deductible_pct = float(getattr(data, "tva_deductible_pct", 100) or 0)
    if not 0 <= deductible_pct <= 100:
        raise HTTPException(status_code=400, detail="Le pourcentage de TVA déductible doit être compris entre 0 et 100")
    if nature_tva_achat == "non_deductible":
        deductible_pct = 0

    _verifier_sources_facture_societe(db, societe_id, data.lignes)
    _verifier_conversion_directe_devis(db, societe_id, data.lignes)
    _verifier_reliquats_sources(db, societe_id, data.lignes)
    tiers_obj = _resoudre_tiers_facture(db, societe_id, data.tiers_id, data.tiers, est_vente)

    try:
        exercice_obj = trouver_exercice_pour_date(db, societe_id, data.date)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    exercice_ref = exercice_obj.annee

    numero = None
    if est_proforma:
        numero = reserver_numero(db, societe_id, exercice_ref, "proforma", prefixe_facture(societe, True))

    facture = models.Facture(
        societe_id=societe_id, numero=numero, type=data.type,
        date=data.date, exercice=exercice_ref,
        tiers=(tiers_obj.nom if tiers_obj else data.tiers),
        tiers_id=(tiers_obj.id if tiers_obj else None),
        tiers_ice_snapshot=(tiers_obj.ice if tiers_obj else None),
        tiers_if_snapshot=(tiers_obj.identifiant_fiscal if tiers_obj else None),
        tiers_rc_snapshot=(tiers_obj.rc if tiers_obj else None),
        tiers_adresse_snapshot=(tiers_obj.adresse if tiers_obj else None),
        tiers_ville_snapshot=(tiers_obj.ville if tiers_obj else None),
        tiers_telephone_snapshot=(tiers_obj.telephone if tiers_obj else None),
        tiers_email_snapshot=(tiers_obj.email if tiers_obj else None),
        tiers_categorie_snapshot=(getattr(tiers_obj, "categorie_fiscale", None) if tiers_obj else None),
        reference=(data.reference.strip() if data.reference else None),
        statut="en_attente", notes=data.notes,
        delai_paiement=(60 if data.delai_paiement is None else data.delai_paiement),
        date_echeance=_calculer_date_echeance(data.date, (60 if data.delai_paiement is None else data.delai_paiement), data.date_echeance),
        mode_reglement_prevu=getattr(data, "mode_reglement_prevu", None),
        reference_reglement_prevue=(getattr(data, "reference_reglement_prevue", None) or None),
        est_validee=False,
        remise_globale=data.remise_globale or 0,
        ristourne=getattr(data, 'ristourne', 0) or 0,
        escompte=data.escompte or 0,
        frais_transport_ht=data.frais_transport_ht or 0,
        frais_transport_tva=data.frais_transport_tva if data.frais_transport_tva is not None else 20,
        frais_transport_mode=data.frais_transport_mode or "accessoire",
        frais_transport_qualification_tva=data.frais_transport_qualification_tva or "taxable",
        frais_emballage_ht=data.frais_emballage_ht or 0,
        frais_emballage_tva=data.frais_emballage_tva if data.frais_emballage_tva is not None else 20,
        frais_emballage_mode=data.frais_emballage_mode or "perdu",
        frais_emballage_qualification_tva=data.frais_emballage_qualification_tva or "taxable",
        ras_taux=data.ras_taux or 0, nature_tva_achat=nature_tva_achat,
        tva_deductible_pct=deductible_pct, est_proforma=est_proforma,
        regime_tva=regime_tva_snapshot,
    )
    db.add(facture); db.flush()

    # Alerte précoce : ne pas créer un nouveau brouillon si une facture fournisseur
    # définitive porte déjà le même numéro. La validation refait le contrôle.
    if not est_vente and facture.reference:
        _verifier_doublon_facture_fournisseur(db, societe_id, facture, exclure_id=facture.id)

    try:
        for l in data.lignes:
            valider_tva(facture.date, l.tva, getattr(l, "qualification_tva", "taxable") or "taxable")
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    for l in data.lignes:
        article = _article_facture(db, societe_id, l.article_id, l.description)
        db.add(models.LigneFacture(
            facture_id=facture.id, article_id=(article.id if article else None),
            source_ligne_devis_id=l.source_ligne_devis_id,
            source_ligne_bc_id=l.source_ligne_bc_id, source_ligne_bl_id=l.source_ligne_bl_id,
            description=l.description, quantite=l.quantite, prix_unitaire=l.prix_unitaire,
            tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable", remise=l.remise or 0, remise2=getattr(l, 'remise2', 0) or 0,
            rabais=getattr(l, 'rabais', 0) or 0,
        ))

    db.flush()
    db.expire(facture, ["lignes"])
    if data.echeances:
        _, _, total_ttc_ech, _, _ = _calc_totaux(facture)
        try:
            remplacer_echeancier_db(db, societe_id, facture, data.echeances, total_ttc_ech)
        except ValueError as exc:
            db.rollback()
            raise HTTPException(422, str(exc)) from exc

    _verifier_conformite_tva_facture(facture)

    # Aucun mouvement de stock, aucune consommation de plafond et aucune écriture
    # comptable tant que la facture n'est pas validée.
    db.flush(); db.refresh(facture)
    total_ht, total_tva, total_net, remise_g, escompte_v = _calc_totaux(facture)
    return {
        **facture.__dict__, "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_net,
        **_lecture_ras(facture, total_ht, total_net),
        "remise_globale": remise_g, "escompte": escompte_v,
        "echeances": echeances_persistantes_ou_defaut(facture, total_net),
        "lignes": [{
            **l.__dict__,
            "remise": l.remise or 0,
            "montant_ht": _montants_ligne_affichage(l)[0],
            "montant_tva": _montants_ligne_affichage(l)[1],
            "montant_ttc": _montants_ligne_affichage(l)[2],
        } for l in facture.lignes],
    }


@router.post("/{facture_id}/valider")
def valider_facture(
    facture_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    from datetime import datetime as dt
    societe_id = current_user["societe_id"]
    facture = db.query(models.Facture).options(
        joinedload(models.Facture.lignes), joinedload(models.Facture.echeances)
    ).filter_by(
        id=facture_id, societe_id=societe_id
    ).populate_existing().with_for_update(of=models.Facture).first()
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    if facture.est_proforma:
        raise HTTPException(400, "Une proforma doit être convertie en facture définitive.")
    if facture.est_validee:
        return {"message": "Facture déjà validée", "numero": facture.numero, "date_echeance": facture.date_echeance}
    _verifier_montants_representables(facture)
    _verifier_date_facture_finale(db, societe_id, facture)
    if not facture.lignes:
        raise HTTPException(422, "Impossible de valider une facture sans ligne.")

    est_vente = facture.type == "vente"
    if not est_vente:
        if not facture.tiers_id:
            raise HTTPException(422, "Sélectionnez un fournisseur enregistré avant de valider la facture.")
        if not (facture.reference or "").strip():
            raise HTTPException(422, "Le N° de facture fournisseur est obligatoire avant validation.")
        _verifier_doublon_facture_fournisseur(db, societe_id, facture, exclure_id=facture.id)

    avertissements_mentions = _figer_identites_facture(db, societe_id, facture, verifier_mentions=True)
    total_ht, total_tva, total_ttc, _, _ = _calc_totaux(facture)
    if facture.echeances:
        try:
            normaliser_echeances(facture.echeances, total_ttc, facture.date)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    _controler_plafond_credit(db, societe_id, facture.tiers, est_vente, total_ttc, exclure_facture_id=facture.id)

    # Tous les contrôles métier passent avant la réservation : un échec ne consomme
    # donc aucun numéro. La réservation elle-même est transactionnelle/atomique.
    if _stock_sur_facture(db, societe_id, est_vente):
        for l in facture.lignes:
            article = _article_facture(db, societe_id, l.article_id, l.description)
            if est_vente and article is not None and article.is_stockable and (article.stock_actuel or 0) + 1e-9 < float(l.quantite or 0):
                raise HTTPException(409,
                    f"Stock insuffisant : {l.description} — disponible {article.stock_actuel or 0:g}, demandé {l.quantite or 0:g}.")

    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    facture.numero = reserver_numero(db, societe_id, facture.exercice, "facture", prefixe_facture(societe, False))
    facture.date_echeance = _calculer_date_echeance(facture.date, facture.delai_paiement, facture.date_echeance)
    # COMPTA.1 — les comptes issus des formulaires sont figés à la validation.
    # Une modification ultérieure de la fiche tiers/article/famille ne peut donc
    # jamais changer la future écriture de cette facture.
    figer_comptes_facture(db, societe_id, facture)
    try:
        # Les lignes doivent être persistées tant que la facture est encore
        # brouillon : le trigger PostgreSQL bloque toute UPDATE d'une ligne
        # dès que la facture parente est validée. Les deux flush restent dans
        # la même transaction ; aucun état intermédiaire n'est commité.
        db.flush()
        facture.est_validee = True
        facture.date_validation = dt.utcnow()
        facture.validee_par = current_user.get("id")
        db.flush()
    except IntegrityError as exc:
        # Les index uniques de FACT.4B sont la protection concurrente finale.
        # On transforme leur violation en erreur métier au lieu d'une 500.
        contrainte = getattr(getattr(getattr(exc, "orig", None), "diag", None), "constraint_name", None)
        db.rollback()
        if contrainte == "uq_factures_fournisseur_reference_validee":
            raise HTTPException(
                409,
                "Facture fournisseur en doublon : ce numéro vient d'être utilisé "
                "pour ce fournisseur. Rechargez la liste des factures."
            )
        if contrainte == "uq_factures_societe_numero":
            raise HTTPException(
                409,
                "Conflit de numérotation : le numéro interne vient d'être réservé "
                "par une autre opération. Relancez la validation."
            )
        raise

    _mouvements_stock_validation_facture(db, societe_id, facture, user_id=current_user.get("id"))
    db.commit(); db.refresh(facture)
    return {
        "message": f"Facture {facture.numero} validée",
        "numero": facture.numero,
        "date_echeance": facture.date_echeance,
        "est_validee": True,
        "avertissements_mentions": avertissements_mentions,
    }


@router.patch("/{facture_id}", response_model=dict)
def mettre_a_jour_facture(
    facture_id: int,
    data: schemas.FactureUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    facture = db.query(models.Facture).options(joinedload(models.Facture.lignes)).filter_by(
        id=facture_id, societe_id=societe_id
    ).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    # FACT-A / F-005 — le statut est dérivé des règlements/avoirs.
    # Une saisie manuelle ne peut pas déclarer arbitrairement une facture payée ou annulée.
    if data.statut is not None:
        demande = getattr(data.statut, "value", data.statut)
        actuel = getattr(getattr(facture, "statut", None), "value", getattr(facture, "statut", None))
        if demande != actuel:
            raise HTTPException(
                status_code=409,
                detail="Le statut de la facture est calculé automatiquement à partir des règlements et avoirs ; il ne peut pas être modifié manuellement.",
            )

    # FACT.4 — après validation, la facture est une pièce définitive. Les règlements
    # mettent à jour son statut par le moteur dédié ; l'édition utilisateur ne peut
    # plus modifier les données de facturation. Seules les notes restent éditables.
    if facture.est_validee and not facture.est_proforma:
        champs_interdits = [
            data.numero, data.type, data.date, data.tiers, data.tiers_id, data.reference,
            data.statut, data.delai_paiement, data.date_echeance, data.mode_reglement_prevu,
            data.reference_reglement_prevue, data.remise_globale,
            data.ristourne, data.escompte, data.frais_transport_ht, data.frais_transport_tva,
            data.frais_transport_mode, data.frais_transport_qualification_tva,
            data.frais_emballage_ht, data.frais_emballage_tva, data.frais_emballage_mode,
            data.frais_emballage_qualification_tva, data.ras_taux,
            data.nature_tva_achat, data.tva_deductible_pct, data.est_proforma, data.lignes, data.echeances,
        ]
        if any(v is not None for v in champs_interdits):
            raise HTTPException(409,
                "Facture validée : les données de facturation sont figées. "
                "Utilisez un avoir ou un document correctif pour la corriger.")
        if data.notes is not None:
            facture.notes = data.notes
            db.commit()
        return {"message": "Notes de la facture mises à jour"}

    # Une facture déjà comptabilisée ne peut plus voir ses montants changer :
    # l'écriture générée ne serait plus le reflet de la facture. Il faut passer par un avoir.
    touche_montants = (
        data.lignes is not None
        or data.frais_transport_ht is not None
        or data.frais_emballage_ht is not None
        or data.ras_taux is not None
        or data.nature_tva_achat is not None
        or data.tva_deductible_pct is not None
    )
    if facture.est_comptabilisee and touche_montants:
        raise HTTPException(
            status_code=400,
            detail="Cette facture est déjà comptabilisée : impossible de modifier ses lignes ou ses frais. "
                   "Utilisez un avoir pour corriger une facture déjà comptabilisée."
        )

    # Le numéro définitif est attribué par PostgreSQL au moment de la validation.
    # Un brouillon ne peut pas réserver/manipuler son propre numéro.
    if data.numero is not None and data.numero != facture.numero:
        raise HTTPException(409, "Le N° de facture est attribué automatiquement à la validation.")

    champs_calcules = {
        "lignes", "remise_globale", "ristourne", "escompte",
        "frais_transport_ht", "frais_transport_tva", "frais_transport_mode",
        "frais_transport_qualification_tva", "frais_emballage_ht",
        "frais_emballage_tva", "frais_emballage_mode", "frais_emballage_qualification_tva",
    }
    if any(getattr(data, champ, None) is not None for champ in champs_calcules):
        valeurs = {champ: getattr(facture, champ, None) for champ in champs_calcules}
        valeurs.update({champ: getattr(data, champ) for champ in champs_calcules
                        if getattr(data, champ, None) is not None})
        _verifier_montants_representables(SimpleNamespace(**valeurs))

    # ── Champs simples ────────────────────────────────────────────────────────
    date_facture_modifiee = False
    if data.date is not None:
        from datetime import date as date_cls
        try:
            facture.date = date_cls.fromisoformat(data.date)
            facture.exercice = trouver_exercice_pour_date(db, societe_id, facture.date).annee
            date_facture_modifiee = True
        except ValueError:
            raise HTTPException(status_code=400, detail="Date invalide, format attendu AAAA-MM-JJ")
    if data.tiers is not None or data.tiers_id is not None:
        tiers_obj = _resoudre_tiers_facture(
            db, societe_id, data.tiers_id, data.tiers or facture.tiers, facture.type == "vente"
        )
        if tiers_obj:
            facture.tiers = tiers_obj.nom
            facture.tiers_id = tiers_obj.id
            facture.tiers_ice_snapshot = tiers_obj.ice
            facture.tiers_if_snapshot = tiers_obj.identifiant_fiscal
            facture.tiers_rc_snapshot = tiers_obj.rc
            facture.tiers_adresse_snapshot = tiers_obj.adresse
            facture.tiers_ville_snapshot = tiers_obj.ville
            facture.tiers_telephone_snapshot = tiers_obj.telephone
            facture.tiers_email_snapshot = tiers_obj.email
            facture.tiers_categorie_snapshot = getattr(tiers_obj, "categorie_fiscale", None)
        elif data.tiers is not None:
            facture.tiers = data.tiers
            facture.tiers_id = None
    if data.reference is not None:
        facture.reference = data.reference
    if data.statut is not None:
        facture.statut = data.statut
    if data.notes is not None:
        facture.notes = data.notes
    if data.delai_paiement is not None:
        facture.delai_paiement = data.delai_paiement
        if data.date_echeance is None:
            facture.date_echeance = _calculer_date_echeance(facture.date, facture.delai_paiement)
    elif date_facture_modifiee and data.date_echeance is None:
        # Si seule la date du brouillon change, l'échéance par défaut doit suivre
        # le nouveau point de départ contractuel.
        facture.date_echeance = _calculer_date_echeance(facture.date, facture.delai_paiement)
    if data.date_echeance is not None:
        from datetime import date as date_cls
        try:
            echeance = date_cls.fromisoformat(data.date_echeance)
        except ValueError:
            raise HTTPException(400, "Date d'échéance invalide, format attendu AAAA-MM-JJ")
        if echeance < facture.date:
            raise HTTPException(422, "La date d'échéance ne peut pas être antérieure à la date de facture.")
        facture.date_echeance = echeance
    if data.mode_reglement_prevu is not None:
        facture.mode_reglement_prevu = data.mode_reglement_prevu
    if data.reference_reglement_prevue is not None:
        facture.reference_reglement_prevue = data.reference_reglement_prevue.strip() or None
    if data.frais_transport_ht is not None:
        facture.frais_transport_ht = data.frais_transport_ht
    if data.frais_transport_tva is not None:
        facture.frais_transport_tva = data.frais_transport_tva
    if data.frais_transport_mode is not None:
        facture.frais_transport_mode = data.frais_transport_mode
    if data.frais_transport_qualification_tva is not None:
        facture.frais_transport_qualification_tva = data.frais_transport_qualification_tva
    if data.frais_emballage_ht is not None:
        facture.frais_emballage_ht = data.frais_emballage_ht
    if data.frais_emballage_tva is not None:
        facture.frais_emballage_tva = data.frais_emballage_tva
    if data.frais_emballage_mode is not None:
        facture.frais_emballage_mode = data.frais_emballage_mode
    if data.frais_emballage_qualification_tva is not None:
        facture.frais_emballage_qualification_tva = data.frais_emballage_qualification_tva
    if data.ras_taux is not None:
        facture.ras_taux = data.ras_taux
    if data.nature_tva_achat is not None:
        if data.nature_tva_achat not in {"charge", "immobilisation", "non_deductible"}:
            raise HTTPException(status_code=400, detail="Nature TVA achat invalide")
        facture.nature_tva_achat = data.nature_tva_achat
        if data.nature_tva_achat == "non_deductible":
            facture.tva_deductible_pct = 0
    if data.tva_deductible_pct is not None:
        if not 0 <= data.tva_deductible_pct <= 100:
            raise HTTPException(status_code=400, detail="Le pourcentage de TVA déductible doit être compris entre 0 et 100")
        facture.tva_deductible_pct = data.tva_deductible_pct

    # ── Remplacement des lignes : annuler puis réappliquer l'effet stock ────────
    if data.lignes is not None:
        _verifier_sources_facture_societe(db, societe_id, data.lignes)
        _verifier_reliquats_sources(db, societe_id, data.lignes, exclure_facture_id=facture.id)
        est_vente = facture.type == "vente"
        # Le stock n'est manipulé ici que s'il avait été mouvementé par la facture
        # (déclencheur 'facture' et pas une proforma).
        # FACT.5 — une facture brouillon ne doit JAMAIS déplacer le stock.
        # Les factures définitives sont déjà figées par le garde-fou ci-dessus ;
        # ce bloc d'édition ne concerne donc que les brouillons/proformas.
        stock_ici = (
            _stock_sur_facture(db, societe_id, est_vente)
            and bool(getattr(facture, "est_validee", False))
            and not getattr(facture, "est_proforma", False)
        )

        def _article(ligne):
            return _article_facture(db, societe_id, getattr(ligne, "article_id", None), ligne.description)

        # 1) Annuler l'effet stock par mouvements compensatoires. Les mouvements
        # historiques ne sont jamais supprimés ni réécrits.
        if stock_ici:
            try:
                valorisation.annuler_mouvements_source(
                    db,
                    societe_id,
                    source_type="facture",
                    source_id=facture.id,
                    fallback_facture_id=facture.id,
                    reference=facture.numero,
                    note=f"Annulation technique avant modification facture {facture.numero}",
                    date_mouvement=facture.date,
                    user_id=current_user.get("id"),
                )
            except ValueError as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail=str(exc))

        # 2) Vérifier le stock disponible pour les nouvelles lignes (vente uniquement)
        if est_vente and stock_ici:
            erreurs_stock = []
            for l in data.lignes:
                article = _article(l)
                if article is not None and article.is_stockable:
                    stock = article.stock_actuel or 0.0
                    if stock <= 0:
                        erreurs_stock.append(f'"{l.description}" en rupture de stock (stock: 0)')
                    elif l.quantite > stock:
                        erreurs_stock.append(f'"{l.description}" : stock disponible {stock}, demandé {l.quantite}')
            if erreurs_stock:
                db.rollback()
                raise HTTPException(status_code=422, detail=f"Stock insuffisant — {', '.join(erreurs_stock)}")

        # 3) Supprimer les anciennes lignes, créer les nouvelles + mouvements de stock
        for l in list(facture.lignes):
            db.delete(l)
        db.flush()

        for l in data.lignes:
            article = _article(l)
            ligne = models.LigneFacture(
                facture_id=facture.id, article_id=(article.id if article else None),
                source_ligne_devis_id=l.source_ligne_devis_id,
                source_ligne_bc_id=l.source_ligne_bc_id, source_ligne_bl_id=l.source_ligne_bl_id,
                description=l.description, quantite=l.quantite, prix_unitaire=l.prix_unitaire,
                tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable", remise=l.remise or 0,
                remise2=getattr(l, 'remise2', 0) or 0, rabais=getattr(l, 'rabais', 0) or 0,
            )
            db.add(ligne)
            db.flush()

            article = article if stock_ici else None
            if article is not None:
                type_mvt = "sortie" if est_vente else "entree"
                cout = None if est_vente else _cout_entree_avec_frais(db, societe_id, facture, l)
                try:
                    valorisation.enregistrer_mouvement(
                        db,
                        societe_id,
                        article,
                        type_mvt,
                        l.quantite,
                        reference=facture.numero,
                        note=f"Facture modifiée — {'Vente' if est_vente else 'Achat'} — {facture.tiers}",
                        facture_id=facture.id,
                        cout_unitaire=cout,
                        date_mouvement=facture.date,
                        source_type="facture",
                        source_id=facture.id,
                        source_ligne_id=ligne.id,
                        cle_idempotence=f"facture:{facture.id}:ligne:{ligne.id}",
                        user_id=current_user.get("id"),
                    )
                except ValueError as exc:
                    db.rollback()
                    raise HTTPException(status_code=409, detail=str(exc))

    if data.echeances is not None:
        db.flush()
        db.expire(facture, ["lignes"])
        if len(data.echeances) == 0:
            supprimer_echeancier_db(db, societe_id, facture)
        else:
            _, _, total_ttc_ech, _, _ = _calc_totaux(facture)
            try:
                remplacer_echeancier_db(db, societe_id, facture, data.echeances, total_ttc_ech)
            except ValueError as exc:
                db.rollback()
                raise HTTPException(422, str(exc)) from exc

    if facture.type == "achat" and not facture.est_proforma and facture.reference:
        _verifier_doublon_facture_fournisseur(db, societe_id, facture, exclure_id=facture.id)
    db.commit()
    return {"message": "Facture mise à jour"}


@router.delete("/{facture_id}", status_code=204)
def supprimer_facture(
    facture_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    facture = db.query(models.Facture).options(
        joinedload(models.Facture.lignes)
    ).filter_by(
        id=facture_id, societe_id=current_user["societe_id"]
    ).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    # ── Garde-fous comptables ─────────────────────────────────────────────────
    from services.factures_liees_service import verifier_suppression_correspondance
    verifier_suppression_correspondance(db, facture_id)
    if facture.est_validee and not facture.est_proforma:
        raise HTTPException(409,
            "Facture validée : suppression impossible. Utilisez un avoir ou un document correctif.")
    # Une facture comptabilisée ne se supprime pas : elle s'annule par un avoir.
    # Supprimer la pièce laisserait son écriture orpheline au journal.
    if facture.est_comptabilisee:
        raise HTTPException(status_code=400, detail=(
            "Facture comptabilisée : suppression impossible. "
            "Pour l'annuler, créez un avoir — l'écriture comptable doit rester traçable."))

    nb_reglements = db.query(models.Reglement).filter_by(
        facture_id=facture_id, societe_id=current_user["societe_id"]).count()
    if nb_reglements > 0:
        raise HTTPException(status_code=400, detail=(
            f"{nb_reglements} règlement(s) enregistré(s) sur cette facture : suppression impossible. "
            "Supprimez d'abord les règlements depuis la fiche de la facture."))

    nb_avoirs = db.query(models.Avoir).filter_by(
        facture_id=facture_id, societe_id=current_user["societe_id"]).count()
    if nb_avoirs > 0:
        raise HTTPException(status_code=400, detail=(
            f"{nb_avoirs} avoir(s) lié(s) à cette facture : suppression impossible."))

    nb_acomptes = db.query(models.ImputationAcompte).filter_by(
        facture_id=facture_id, societe_id=current_user["societe_id"]).count()
    if nb_acomptes > 0:
        raise HTTPException(status_code=400, detail=(
            f"{nb_acomptes} acompte(s) imputé(s) sur cette facture : suppression impossible."))

    # ── Délier TOUTES les FK vers cette facture avant suppression ───────────
    from sqlalchemy import text
    # Une facture brouillon ne doit pas dégrader l'état antérieur de sa source.
    # Les anciens frontends pouvaient forcer BC="facture" / devis="converti"
    # dès la création du brouillon ; on rétablit un état cohérent à sa suppression.
    db.execute(text("""
        UPDATE bons_commande
           SET facture_id = NULL,
               statut = CASE WHEN statut = 'facture' THEN 'confirme' ELSE statut END
         WHERE facture_id = :fid
    """), {"fid": facture_id})
    db.execute(text("UPDATE bons_livraison SET facture_id = NULL WHERE facture_id = :fid"), {"fid": facture_id})
    devis_lies = db.query(models.Devis).filter_by(
        societe_id=current_user["societe_id"], facture_id=facture_id
    ).all()
    for devis in devis_lies:
        devis.facture_id = None
        if getattr(devis, "statut", None) == "converti":
            bc_existant = db.query(models.BonCommande).filter_by(
                societe_id=current_user["societe_id"], devis_id=devis.id
            ).first()
            if not bc_existant:
                devis.statut = "accepte"
    db.execute(text("DELETE FROM reglements WHERE facture_id = :fid"), {"fid": facture_id})
    db.flush()

    # ── Annulation des mouvements de stock ────────────────────────────────────
    # Patch 06C : on conserve l'historique et on crée des mouvements
    # compensatoires. Une pièce suivie de mouvements ultérieurs ne peut pas être
    # supprimée silencieusement : le moteur la bloque pour préserver le CMUP.
    try:
        valorisation.annuler_mouvements_source(
            db,
            current_user["societe_id"],
            source_type="facture",
            source_id=facture.id,
            fallback_facture_id=facture.id,
            reference=facture.numero,
            note=f"Annulation avant suppression facture {facture.numero}",
            date_mouvement=facture.date,
            user_id=current_user.get("id"),
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc))

    # La FK facture_id doit être déliée avant suppression ; source_type/source_id,
    # référence et note conservent la piste d'audit de la pièce supprimée.
    db.query(models.MouvementStock).filter_by(
        societe_id=current_user["societe_id"], facture_id=facture_id
    ).update({"facture_id": None}, synchronize_session=False)

    db.delete(facture)
    db.commit()


def _situation_paiement_facture(db, societe_id: int, facture, exclure_reglement_id=None, *, tolere_ras_invalide=False):
    """Retourne la situation de règlement unifiée d'une facture.

    FACT.5 centralise ici le calcul du reste à payer afin que la fiche facture,
    la création/modification d'un règlement et le statut de la facture utilisent
    exactement les mêmes règles. Les règlements rejetés sont exclus ; les avoirs
    actifs, acomptes imputés et la RAS diminuent le montant réellement dû au tiers.
    """
    _, _, total_ttc, _, _ = _calc_totaux(facture)

    q_reglements = db.query(models.Reglement).filter_by(
        facture_id=facture.id, societe_id=societe_id
    ).filter(models.Reglement.statut.notin_(["rejete", "annule"]))
    if exclure_reglement_id is not None:
        q_reglements = q_reglements.filter(models.Reglement.id != exclure_reglement_id)
    reglements_actifs = q_reglements.all()
    for r in reglements_actifs:
        try:
            if r.montant is None:
                raise ValueError("Montant manquant")
            schemas._valider_montant_reglement(r.montant)
        except ValueError as exc:
            raise HTTPException(422, "Montant de règlement historique à vérifier.") from exc
    total_regle = sum(float(r.montant or 0) for r in reglements_actifs)
    total_encaisse = sum(
        float(r.montant or 0) for r in reglements_actifs
        if r.date_encaissement is not None or r.statut in {"complet", "encaisse", "paye"}
    )
    total_reglement_en_cours = max(0.0, total_regle - total_encaisse)

    avoirs_actifs = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)) \
        .filter_by(facture_id=facture.id, societe_id=societe_id) \
        .filter(models.Avoir.statut != "annule").all()
    total_avoirs = sum(_total_avoir_qualifie(a) for a in avoirs_actifs)
    total_acomptes = float(db.query(
        func.coalesce(func.sum(models.ImputationAcompte.montant), 0)
    ).filter_by(facture_id=facture.id, societe_id=societe_id, statut="active").scalar() or 0)
    # FACT-G : un crédit excédentaire d'un avoir peut être affecté à une autre
    # facture du même tiers. Ce lettrage métier réduit son reste à payer sans
    # générer une seconde écriture générale.
    total_avoirs_imputes = float(db.query(
        func.coalesce(func.sum(models.UtilisationAvoir.montant), 0)
    ).filter_by(
        facture_id=facture.id, societe_id=societe_id,
        type_utilisation="imputation", statut="active"
    ).scalar() or 0)
    total_avoirs += total_avoirs_imputes
    if not all(math.isfinite(v) for v in (total_regle, total_encaisse,
            total_reglement_en_cours, total_avoirs, total_acomptes)):
        raise HTTPException(422, "Situation financière historique non représentable : vérifier les documents liés.")

    total_ht_f, _, _, _, _ = _calc_totaux(facture)
    ras = _lecture_ras(facture, total_ht_f, total_ttc)
    if ras["ras_anomalie"] and not tolere_ras_invalide:
        raise HTTPException(409, ras["ras_anomalie"])
    from services.ras_paiement_service import lecture_ras_paiement
    from services.ras_reglement_service import montant_actif
    ras_paiement = lecture_ras_paiement(ras["montant_ras"], getattr(facture, 'ras_comptabilisee', False), montant_actif(db, societe_id, facture.id))
    montant_ras = ras_paiement["montant_ras_impute"]
    if montant_ras is None and not ras['ras_anomalie']:
        ras['ras_anomalie'] = 'Capture RAS incohérente : solde indéterminable'
        if not tolere_ras_invalide:
            raise HTTPException(409,ras['ras_anomalie'])
    total_effectif = None if montant_ras is None else total_regle + total_avoirs + total_acomptes + montant_ras
    brut = None if total_effectif is None else float(total_ttc) - total_effectif
    solde = None if brut is None else max(0.0, brut)
    credit_tiers = None if brut is None else max(0.0, -brut)
    return {
        "total_ttc": float(total_ttc),
        "total_regle": total_regle,
        "total_encaisse": total_encaisse,
        "total_reglement_en_cours": total_reglement_en_cours,
        "total_avoirs": total_avoirs,
        "total_acomptes": total_acomptes,
        "montant_ras": montant_ras,
        **ras_paiement,
        "total_effectif": total_effectif,
        "solde_restant": solde,
        "credit_tiers": credit_tiers,
        "est_solde": solde is not None and solde <= 0.01,
        "ras_anomalie": ras["ras_anomalie"],
    }


@router.get("/{facture_id}/reglements")
def reglements_facture(
    facture_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Liste tous les règlements d'une facture avec le solde restant."""
    facture = db.query(models.Facture).options(
        joinedload(models.Facture.lignes)
    ).filter_by(id=facture_id, societe_id=current_user["societe_id"]).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    reglements = db.query(models.Reglement).filter_by(
        facture_id=facture_id,
        societe_id=current_user["societe_id"],
    ).order_by(models.Reglement.date).all()

    situation = _situation_paiement_facture(
        db, current_user["societe_id"], facture, tolere_ras_invalide=True
    )

    return {
        "facture_id":   facture_id,
        "total_ttc":    situation["total_ttc"],
        "total_regle":  situation["total_regle"],
        "total_encaisse": situation["total_encaisse"],
        "total_reglement_en_cours": situation["total_reglement_en_cours"],
        "total_avoirs": situation["total_avoirs"],
        "total_acomptes": situation["total_acomptes"],
        "montant_ras":  situation["montant_ras"],
        "montant_ras_estime": situation["montant_ras_estime"],
        "montant_ras_impute": situation["montant_ras_impute"],
        "ras_origine": situation["ras_origine"],
        "solde_restant": situation["solde_restant"],
        "credit_tiers": situation["credit_tiers"],
        "est_solde":    situation["est_solde"],
        "ras_anomalie": situation["ras_anomalie"],
        "reglements":   [
            {
                "id": r.id, "date": str(r.date), "montant": r.montant,
                "mode": r.mode, "reference": r.reference, "banque": r.banque,
                "statut": r.statut,
            }
            for r in reglements
        ],
    }


@router.post("/{facture_id}/comptabiliser")
def comptabiliser_facture(
    facture_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    from datetime import datetime as dt
    societe_id = current_user["societe_id"]

    # Relire sous verrou avant les indicateurs : deux demandes simultanées
    # doivent observer le résultat du premier commit, sans générer de doublon.
    _f_proforma = db.query(models.Facture).filter_by(
        id=facture_id, societe_id=societe_id
    ).populate_existing().with_for_update().first()
    if _f_proforma and getattr(_f_proforma, "est_proforma", False):
        raise HTTPException(400,
            "Une facture proforma n'a pas de valeur comptable : convertissez-la d'abord en facture définitive.")
    if _f_proforma and not getattr(_f_proforma, "est_validee", False):
        raise HTTPException(409,
            "Cette facture est encore en brouillon : validez-la avant de la comptabiliser.")
    if _f_proforma and exercice_est_clos(db, societe_id, _f_proforma.exercice):
        raise HTTPException(423,
            f"Exercice {_f_proforma.exercice} clôturé : impossible de comptabiliser une facture sur cette période.")
    if _f_proforma and getattr(_f_proforma, "est_comptabilisee", False):
        raise HTTPException(409,
            f"La facture {_f_proforma.numero or facture_id} est déjà comptabilisée : "
            "une seconde comptabilisation créerait une écriture en doublon.")

    module = db.query(models.ModuleActif).filter_by(
        societe_id=societe_id, module="comptabilite", actif=True
    ).first()
    if not module:
        raise HTTPException(status_code=400, detail="Module Comptabilité inactif")

    facture = db.query(models.Facture).options(
        joinedload(models.Facture.lignes)
    ).filter_by(id=facture_id, societe_id=societe_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")

    _verifier_conformite_tva_facture(facture)

    # TVA : les réductions commerciales diminuent directement les comptes de
    # vente/achat. L'escompte de règlement est une réduction financière : il
    # diminue la base TVA mais reste isolé en 6386 (accordé) / 7386 (obtenu).
    ventilation_tva = ventilation_facture(facture, appliquer_escompte=True)
    ventilation_comptable = ventilation_facture(facture, appliquer_escompte=False)
    totaux_tva = total_ventilation(ventilation_tva)
    totaux_avant_escompte = total_ventilation(ventilation_comptable)

    total_base_tva = totaux_tva["base"]
    total_tva_globale = totaux_tva["tva"]
    total_ttc = totaux_tva["ttc"]
    total_ht_comptable = totaux_avant_escompte["base"]
    montant_escompte_ht = money(total_ht_comptable - total_base_tva)

    # Les frais accessoires gardent leur HT dans les comptes dédiés ; l'escompte
    # éventuel est enregistré séparément comme charge/produit financier.
    frais_transport_ht = money(D(getattr(facture, 'frais_transport_ht', 0) or 0))
    frais_emballage_ht = money(D(getattr(facture, 'frais_emballage_ht', 0) or 0))
    total_ht_hors_frais = money(total_ht_comptable - frais_transport_ht - frais_emballage_ht)

    est_vente = facture.type == "vente"
    journal   = "VT" if est_vente else "AC"
    # Libellé selon le format paramétré (Paramètres → Format des libellés d'écritures)
    libelle   = _libelle_ecriture(
        db, societe_id, "vente" if est_vente else "achat",
        numero=facture.numero, tiers=facture.tiers,
        ref=facture.reference, date_doc=facture.date)

    compte_tiers = compte_tiers_facture(db, societe_id, facture)

    if est_vente:
        # COMPTA.1 — ventilation du CA par compte article/famille, au lieu du
        # compte 71243 codé en dur. Le total est réconcilié au centime.
        groupes_ca = groupes_facture_par_compte(
            db, societe_id, facture, est_vente=True, cible=total_ht_hors_frais
        )
        lignes_ecriture = [
            models.LigneEcriture(compte=compte_tiers, libelle=facture.tiers or "Clients", debit=total_ttc, credit=0),
            models.LigneEcriture(compte="4455", libelle="État — TVA facturée", debit=0, credit=total_tva_globale),
        ]
        for compte, montant in sorted(groupes_ca.items()):
            lignes_ecriture.append(models.LigneEcriture(
                compte=compte, libelle="Ventes", debit=0, credit=montant
            ))
        if frais_transport_ht > 0:
            lignes_ecriture.append(models.LigneEcriture(compte="71276", libelle="Ports et frais accessoires facturés", debit=0, credit=frais_transport_ht))
        if frais_emballage_ht > 0:
            lignes_ecriture.append(models.LigneEcriture(compte=("4425" if (getattr(facture, "frais_emballage_mode", "perdu") == "consigne") else "71276"), libelle=("Emballages consignés" if (getattr(facture, "frais_emballage_mode", "perdu") == "consigne") else "Emballage facturé"), debit=0, credit=frais_emballage_ht))
        if montant_escompte_ht > 0:
            lignes_ecriture.append(models.LigneEcriture(compte="6386", libelle="Escompte accordé", debit=montant_escompte_ht, credit=0))
    else:
        nature_tva_achat = (getattr(facture, "nature_tva_achat", None) or "charge").lower()
        if nature_tva_achat == "immobilisation":
            raise HTTPException(400,
                "Une acquisition d'immobilisation doit être enregistrée depuis le module Immobilisations "
                "afin de choisir le compte d'actif, la date de mise en service et le plan d'amortissement. "
                "La TVA de l'acquisition directe y est suivie à la date de paiement.")

        # Déductibilité : pourcentage propre à la facture × prorata annuel de la société.
        deductible_pct = D(getattr(facture, "tva_deductible_pct", 100) or 0)
        if nature_tva_achat == "non_deductible":
            deductible_pct = ZERO
        param_tva = db.query(models.TVAParametreExercice).filter_by(
            societe_id=societe_id, exercice=facture.exercice).first()
        prorata_pct = D(getattr(param_tva, "prorata_deduction_pct", 100) if param_tva else 100)
        effective_pct = max(ZERO, min(D(100), deductible_pct)) * max(ZERO, min(D(100), prorata_pct)) / D(100)
        tva_deductible = money(total_tva_globale * effective_pct / D(100))
        tva_non_deductible = money(total_tva_globale - tva_deductible)

        # COMPTA.1 — ventilation des achats par compte article/famille.
        groupes_achats = groupes_facture_par_compte(
            db, societe_id, facture, est_vente=False, cible=total_ht_hors_frais
        )
        lignes_ecriture = []
        for compte, montant in sorted(groupes_achats.items()):
            lignes_ecriture.append(models.LigneEcriture(
                compte=compte, libelle="Achats", debit=montant, credit=0
            ))
        if frais_transport_ht > 0:
            lignes_ecriture.append(models.LigneEcriture(compte="6142", libelle="Transports", debit=frais_transport_ht, credit=0))
        if frais_emballage_ht > 0:
            lignes_ecriture.append(models.LigneEcriture(compte=("3413" if (getattr(facture, "frais_emballage_mode", "perdu") == "consigne") else "6123"), libelle=("Emballages à rendre" if (getattr(facture, "frais_emballage_mode", "perdu") == "consigne") else "Achats emballages"), debit=frais_emballage_ht, credit=0))
        if tva_deductible > 0:
            lignes_ecriture.append(models.LigneEcriture(
                compte="34552", libelle="État — TVA récupérable sur charges", debit=tva_deductible, credit=0))
        if tva_non_deductible > 0:
            # La TVA non déductible augmente le coût des mêmes achats ; elle est
            # donc répartie sur leurs comptes, pas envoyée arbitrairement en 6111.
            allocation_non_ded = repartir_par_poids(tva_non_deductible, groupes_achats)
            if allocation_non_ded:
                for compte, montant in sorted(allocation_non_ded.items()):
                    lignes_ecriture.append(models.LigneEcriture(
                        compte=compte, libelle="TVA non déductible incorporée au coût", debit=montant, credit=0
                    ))
            else:
                lignes_ecriture.append(models.LigneEcriture(
                    compte="6111", libelle="TVA non déductible incorporée au coût", debit=tva_non_deductible, credit=0))
        if montant_escompte_ht > 0:
            lignes_ecriture.append(models.LigneEcriture(compte="7386", libelle="Escompte obtenu", debit=0, credit=montant_escompte_ht))
        lignes_ecriture.append(models.LigneEcriture(
            compte=compte_tiers, libelle=facture.tiers or "Fournisseurs", debit=0, credit=total_ttc
        ))

    # COMPTA-AUX : le tiers est une dimension native de la ligne comptable et
    # son code/libellé auxiliaire sont figés avant validation/FEC.
    rattacher_tiers_aux_lignes(
        db, societe_id, lignes_ecriture,
        tiers_id=getattr(facture, "tiers_id", None),
        nature="client" if est_vente else "fournisseur",
    )

    # COMPTA.5 — la référence FEC doit pointer vers la pièce métier réelle :
    # pour une vente, le numéro HisabPro est la pièce émise ; pour un achat,
    # le numéro du fournisseur est la référence documentaire prioritaire.
    reference_piece = (facture.numero if est_vente else (facture.reference or facture.numero))
    ecriture = models.Ecriture(
        societe_id=societe_id,
        journal=journal,
        date=facture.date or dt.now().date(),
        date_piece=facture.date or dt.now().date(),
        libelle=libelle,
        reference=reference_piece,
        exercice=facture.exercice,
        source="facture",
        lignes=lignes_ecriture,
    )
    db.add(ecriture)
    facture.est_comptabilisee = True
    db.commit()

    return {"message": "Comptabilisée", "ecriture_id": ecriture.id}


@router.get("/{facture_id}/pdf")
def generer_pdf_facture(
    facture_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Génère le PDF de la facture (reportlab) : remises, frais, mentions légales,
    montant en lettres, échéance, RIB."""
    from fastapi.responses import Response
    from datetime import timedelta
    from pdf_generator import generer_document
    from services.document_pdf_service import tiers_infos, societe_pour_document, resume_tva_depuis_ventilation, mentions_tva_depuis_lignes, conditions_paiement

    facture = db.query(models.Facture).options(
        joinedload(models.Facture.lignes)
    ).filter_by(id=facture_id, societe_id=current_user["societe_id"]).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    if not facture.est_proforma and not getattr(facture, "est_validee", False):
        raise HTTPException(409,
            "Cette facture est encore en brouillon. Validez-la avant d'émettre le PDF définitif.")

    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    societe_pdf = societe_pour_document(societe, facture)
    total_ht, total_tva, total_ttc, _, escompte = _calc_totaux(facture)

    delai = 60 if facture.delai_paiement is None else int(facture.delai_paiement)
    date_echeance = facture.date_echeance or (facture.date + timedelta(days=delai) if facture.date else None)

    est_vente = facture.type == "vente"

    lignes_pdf, total_ht_lignes = [], 0
    for l in facture.lignes:
        remise = getattr(l, "remise", 0) or 0
        remise2 = getattr(l, "remise2", 0) or 0
        rabais = getattr(l, "rabais", 0) or 0
        ht, _, _ = _montants_ligne_affichage(l)
        total_ht_lignes += ht
        taux_affiche = l.tva if getattr(l, "qualification_tva", "taxable") == "taxable" else 0
        lignes_pdf.append({
            "description": l.description, "quantite": l.quantite,
            "prix_unitaire": l.prix_unitaire, "remise": remise,
            "tva": getattr(l, "tva", 0) or 0, "qualification_tva": getattr(l, "qualification_tva", "taxable") or "taxable",
            "total_ht": ht, "remise2": remise2, "rabais": rabais,
        })

    frais_t = getattr(facture, "frais_transport_ht", 0) or 0
    frais_e = getattr(facture, "frais_emballage_ht", 0) or 0
    remise_globale = float(getattr(facture, "remise_globale", 0) or 0)
    ristourne = float(getattr(facture, "ristourne", 0) or 0)
    montant_remise_globale = total_ht_lignes * remise_globale / 100
    base_apres_remise = total_ht_lignes - montant_remise_globale
    montant_ristourne = base_apres_remise * ristourne / 100

    totaux = [("Sous-total lignes", total_ht_lignes, False)]
    if remise_globale:
        totaux.append((f"Remise globale ({remise_globale:g}%)", -montant_remise_globale, False))
    if ristourne:
        totaux.append((f"Ristourne ({ristourne:g}%)", -montant_ristourne, False))
    if frais_t:
        mode_t = getattr(facture, "frais_transport_mode", "accessoire") or "accessoire"
        lib_t = "TVA héritée des lignes" if mode_t == "accessoire" else f"{getattr(facture, 'frais_transport_tva', 0):g}% TVA"
        totaux.append((f"Frais de transport ({lib_t})", frais_t, False))
    if frais_e:
        mode_e = getattr(facture, "frais_emballage_mode", "perdu") or "perdu"
        if mode_e == "consigne": lib_e = "consigne hors base TVA"
        elif mode_e == "perdu": lib_e = "TVA héritée des lignes"
        else: lib_e = f"{getattr(facture, 'frais_emballage_tva', 0):g}% TVA"
        totaux.append((f"Emballage ({lib_e})", frais_e, False))
    consigne_emballage = frais_e if (getattr(facture, "frais_emballage_mode", "perdu") == "consigne") else 0
    totaux.append(("Net commercial HT", total_ht, False))
    if escompte:
        base_apres_escompte = float(total_ventilation(ventilation_facture(facture, appliquer_escompte=True))["base"])
        montant_escompte_ht = max(total_ht - base_apres_escompte, 0)
        totaux.append((f"Escompte de règlement HT ({escompte:g}%)", -montant_escompte_ht, False))
        totaux.append(("Net HT après escompte", base_apres_escompte, False))
    totaux.append(("Total TVA", total_tva, False))
    totaux.append(("TOTAL TTC", total_ttc, True))
    montant_ras_pdf = _montant_ras(facture, total_ht)
    if montant_ras_pdf > 0:
        totaux.append((f"Retenue à la source ({facture.ras_taux:g}% du HT)", -montant_ras_pdf, False))
        totaux.append(("NET À PAYER", total_ttc - montant_ras_pdf, True))

    from datetime import date as _d
    meta = [("Échéance", f"{date_echeance.day:02d}/{date_echeance.month:02d}/{date_echeance.year}" if date_echeance else "—")]
    if facture.reference:
        meta.append(("N° facture fournisseur" if not est_vente else "Référence", facture.reference))
    if getattr(facture, "regime_tva", None):
        meta.append(("Régime TVA", str(facture.regime_tva).replace("_", " ").capitalize()))

    est_proforma = bool(getattr(facture, "est_proforma", False))
    ventilation_pdf = ventilation_facture(facture, appliquer_escompte=True)
    echeancier_pdf = echeances_persistantes_ou_defaut(facture, total_ttc)
    mentions_pdf = mentions_tva_depuis_lignes(lignes_pdf)
    if consigne_emballage > 0:
        mentions_pdf.append("Emballage consigné : montant hors base TVA, remboursable selon restitution.")
    pdf_bytes = generer_document(
        societe_pdf,
        titre=("FACTURE PROFORMA" if est_proforma
               else ("FACTURE" if est_vente else "FACTURE D'ACHAT")),
        numero=facture.numero,
        date_doc=facture.date,
        tiers=facture.tiers,
        tiers_infos=tiers_infos(db, models, current_user["societe_id"], facture),
        label_tiers="CLIENT" if est_vente else "FOURNISSEUR",
        meta=meta, lignes=lignes_pdf, colonnes="prix", totaux=totaux,
        resume_tva=resume_tva_depuis_ventilation(ventilation_pdf),
        echeancier=echeancier_pdf,
        conditions=conditions_paiement(facture.delai_paiement, date_echeance, getattr(facture, "mode_reglement_prevu", None), getattr(facture, "reference_reglement_prevue", None)),
        mentions=mentions_pdf,
        mention_lettres=(total_ttc - montant_ras_pdf) if montant_ras_pdf > 0 else total_ttc,
        rib=est_vente,
        statut="PROFORMA" if est_proforma else ("VALIDÉE" if getattr(facture, "est_validee", False) else "BROUILLON"),
        notes=(("Document proforma - sans valeur comptable ni fiscale. " + (facture.notes or "")).strip()
               if est_proforma else (facture.notes_snapshot if getattr(facture, "est_validee", False) else facture.notes)),
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="facture_{facture.numero}.pdf"'},
    )


@router.post("/{facture_id}/convertir-definitive")
def convertir_proforma(
    facture_id: int,
    data: schemas.ConvertirProformaIn = schemas.ConvertirProformaIn(),
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Convertit une proforma en facture définitive : nouveau numéro dans la
    séquence des factures, application des mouvements de stock."""
    facture = db.query(models.Facture).options(
        joinedload(models.Facture.lignes)
    ).filter_by(
        id=facture_id, societe_id=current_user["societe_id"]
    ).populate_existing().with_for_update(of=models.Facture).first()
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    if not facture.est_proforma:
        raise HTTPException(400, "Cette facture n'est pas une proforma")

    _verifier_montants_representables(facture)
    est_vente = facture.type == "vente"
    facture.date = data.date or date_cls.today()
    _verifier_date_facture_finale(db, current_user["societe_id"], facture)

    # Contrôle de stock (comme une création normale de vente)
    if est_vente and _stock_sur_facture(db, current_user["societe_id"], True):
        erreurs = []
        for l in facture.lignes:
            article = _article_facture(db, current_user["societe_id"], l.article_id, l.description)
            if article is not None and article.is_stockable and (article.stock_actuel or 0) < l.quantite:
                erreurs.append(f"{l.description} (stock : {article.stock_actuel or 0:g}, demandé : {l.quantite:g})")
        if erreurs:
            raise HTTPException(400, "Stock insuffisant pour convertir : " + " ; ".join(erreurs))

    _verifier_conformite_tva_facture(facture)

    # Conversion = validation définitive : la séquence facture est réservée
    # atomiquement et la pièce devient immédiatement immuable.
    from datetime import datetime as dt
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    ancien_numero = facture.numero
    if facture.type == "achat":
        if not facture.tiers_id:
            raise HTTPException(422, "Sélectionnez un fournisseur enregistré avant conversion.")
        if not (facture.reference or "").strip():
            raise HTTPException(422, "Le N° de facture fournisseur est obligatoire avant conversion.")
        _verifier_doublon_facture_fournisseur(db, current_user["societe_id"], facture, exclure_id=facture.id)
    avertissements_mentions = _figer_identites_facture(
        db, current_user["societe_id"], facture, verifier_mentions=True
    )
    figer_comptes_facture(db, current_user["societe_id"], facture)
    # Même invariant pour les proformas : figer les lignes pendant que la
    # facture parente est encore proforma, avant son passage en définitive.
    db.flush()
    facture.numero = reserver_numero(
        db, current_user["societe_id"], facture.exercice, "facture", prefixe_facture(societe, False)
    )
    facture.est_proforma = False
    facture.est_validee = True
    facture.date_validation = dt.utcnow()
    facture.validee_par = current_user.get("id")
    facture.date_echeance = _calculer_date_echeance(facture.date, facture.delai_paiement, None)
    facture.reference = facture.reference or f"Proforma {ancien_numero}"
    db.flush()

    # Mouvements de stock (comme à la création d'une facture normale),
    # uniquement si le déclencheur est la facture.
    if not _stock_sur_facture(db, current_user["societe_id"], est_vente):
        db.commit()
        return {"message": f"Proforma {ancien_numero} convertie en facture {facture.numero}",
                "numero": facture.numero, "avertissements_mentions": avertissements_mentions}
    for l in facture.lignes:
        article = _article_facture(db, current_user["societe_id"], l.article_id, l.description)
        if article is not None:
            type_mvt = "sortie" if est_vente else "entree"
            cout = None if est_vente else _cout_entree_avec_frais(db, current_user["societe_id"], facture, l)
            try:
                valorisation.enregistrer_mouvement(
                    db,
                    current_user["societe_id"],
                    article,
                    type_mvt,
                    l.quantite,
                    reference=facture.numero,
                    note=f"Conversion proforma {ancien_numero} — {facture.tiers}",
                    facture_id=facture.id,
                    cout_unitaire=cout,
                    date_mouvement=facture.date,
                    source_type="facture",
                    source_id=facture.id,
                    source_ligne_id=l.id,
                    cle_idempotence=f"facture:{facture.id}:ligne:{l.id}",
                    user_id=current_user.get("id"),
                )
            except ValueError as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail=str(exc))

    db.commit()
    return {"message": f"Proforma {ancien_numero} convertie en facture {facture.numero}",
            "numero": facture.numero, "avertissements_mentions": avertissements_mentions}


# ── Conversion facture → bon de livraison (sans BC) ──────────────────────────
@router.post("/{facture_id}/convertir-bl", response_model=schemas.BonLivraisonOut)
def convertir_facture_en_bl(
    facture_id: int,
    data: schemas.ConvertirBLIn = schemas.ConvertirBLIn(),
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Convertit directement une facture en bon de livraison, sans passer par un BC.
    Utile pour les factures issues d'une conversion directe devis → facture.
    La date de livraison est paramétrable ; par défaut, la date du jour."""
    facture = db.query(models.Facture).options(joinedload(models.Facture.lignes)) \
        .filter_by(id=facture_id, societe_id=current_user["societe_id"]).first()
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    if facture.est_proforma:
        raise HTTPException(409, "Une proforma doit être convertie avant de créer un bon de livraison.")
    if not getattr(facture, "est_validee", False):
        raise HTTPException(409, "Cette facture est encore en brouillon : validez-la avant de créer un bon de livraison.")

    # Bloquer si un BL existe déjà pour cette facture
    bl_existant = db.query(models.BonLivraison).filter_by(facture_id=facture_id).first()
    if bl_existant:
        raise HTTPException(400, f"Un bon de livraison ({bl_existant.numero}) existe déjà pour cette facture.")

    date_bl = data.date or date_cls.today().isoformat()
    try:
        date_bl = date_cls.fromisoformat(date_bl[:10]) if isinstance(date_bl, str) else date_bl
    except (TypeError, ValueError):
        raise HTTPException(422, "Date de livraison invalide, format attendu AAAA-MM-JJ")
    # Le document est créé en préparation : il peut être préparé pour une date
    # future. La période sera contrôlée lorsqu'il devient effectivement livré/reçu.
    try:
        exercice_bl_annee = trouver_exercice_pour_date(db, current_user["societe_id"], date_bl).annee
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    est_achat = facture.type == "achat"
    prefixe_bl = "BR" if est_achat else (getattr(societe, "prefixe_bl", None) or "BL")
    numero_bl = reserver_numero_commercial(
        db,
        current_user["societe_id"],
        exercice_bl_annee,
        "br" if est_achat else "bl",
        prefixe_bl,
    )

    bl = models.BonLivraison(
        societe_id=current_user["societe_id"],
        bon_commande_id=None,
        facture_id=facture.id,
        numero=numero_bl,
        type=facture.type,
        date=date_bl,
        exercice=exercice_bl_annee,
        tiers=facture.tiers, tiers_id=facture.tiers_id,
        statut="en_preparation",
    )
    db.add(bl); db.flush()
    for l in facture.lignes:
        db.add(models.LigneBonLivraison(
            bon_livraison_id=bl.id,
            description=l.description,
            quantite_prevue=l.quantite,
            quantite_livree=l.quantite,
        ))
    db.commit(); db.refresh(bl)
    return db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)).filter_by(id=bl.id).first()
