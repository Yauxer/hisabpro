from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Literal
from datetime import date as _date, timedelta
import json
import math
import hashlib
import re
from uuid import UUID
from sqlalchemy import text
from pydantic import BaseModel, field_validator
from decimal import Decimal, InvalidOperation
from services.devis_stock_service import diagnostic_stock_devis
from database import get_db
from auth import get_current_user, requiert_ecriture
import models, schemas
import valorisation
from routers.factures import _libelle_ecriture
from services.commercial_numero_service import reserver_numero_commercial
from services.compta_mapping_service import compte_tiers, compte_tiers_facture, compte_tresorerie
from services.tresorerie_service import verifier_sortie as verifier_sortie_caisse
from services.auxiliaire_service import rattacher_tiers_aux_lignes
from services.tva_regles_service import valider_tva
from services.exercices_service import trouver_exercice_pour_date

router_devis = APIRouter(prefix="/api/devis",          tags=["commercial"])
router_bc    = APIRouter(prefix="/api/bons-commande",  tags=["commercial"])
router_bl    = APIRouter(prefix="/api/bons-livraison", tags=["commercial"])
router_regl  = APIRouter(prefix="/api/reglements",     tags=["commercial"])


class LigneDiagnosticStockDevis(BaseModel):
    article_id: Optional[int] = None
    quantite: float

    @field_validator('article_id', mode='before')
    @classmethod
    def identifiant_article(cls, valeur):
        if isinstance(valeur, bool):
            raise ValueError('Identifiant article invalide')
        return valeur

    @field_validator('quantite', mode='before')
    @classmethod
    def quantite_finie_positive_ou_nulle(cls, valeur):
        if isinstance(valeur, bool):
            raise ValueError('La quantité doit être un nombre fini positif ou nul')
        try:
            nombre = Decimal(str(valeur))
        except (InvalidOperation, ValueError, TypeError):
            raise ValueError('La quantité doit être un nombre fini positif ou nul') from None
        if not nombre.is_finite() or nombre < 0:
            raise ValueError('La quantité doit être un nombre fini positif ou nul')
        # Même représentation individuelle que les lignes commerciales ; le
        # service conserve un cumul Decimal exact, éventuellement rendu en texte.
        flottant = float(nombre)
        if not math.isfinite(flottant) or (nombre != 0 and flottant == 0):
            raise ValueError('La quantité doit être représentable par un nombre fini sans perte vers zéro')
        return 0.0 if nombre == 0 else flottant


class DiagnosticStockDevisIn(BaseModel):
    lignes: List[LigneDiagnosticStockDevis]


@router_devis.post('/diagnostic-stock')
def diagnostic_stock_devis_endpoint(data: DiagnosticStockDevisIn,
    current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    """Photographie indicative du stock actuel : devis toujours autorisé."""
    return diagnostic_stock_devis(db, current_user['societe_id'], data.lignes)

_SNAPSHOT_SOCIETE_DOC = (
    "raison_sociale", "identifiant_fiscal", "ice", "rc", "patente", "cnss_numero",
    "adresse", "ville", "pays", "telephone", "fax", "email", "site_web",
    "forme_juridique", "capital_social", "banque", "agence", "rib", "logo_url",
)

def _figer_document_commercial(db, societe_id, piece):
    """Fige vendeur, tiers et notes lorsqu'une pièce sort de son état préparatoire."""
    if getattr(piece, "societe_snapshot_json", None) and getattr(piece, "tiers_snapshot_json", None):
        if getattr(piece, "notes_snapshot", None) is None:
            piece.notes_snapshot = getattr(piece, "notes", None)
        return
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    if societe and not getattr(piece, "societe_snapshot_json", None):
        piece.societe_snapshot_json = json.dumps(
            {k: getattr(societe, k, None) for k in _SNAPSHOT_SOCIETE_DOC},
            ensure_ascii=False, default=str,
        )
    if not getattr(piece, "tiers_snapshot_json", None):
        tiers = None
        if getattr(piece, "tiers_id", None):
            tiers = db.query(models.Tiers).filter_by(
                id=piece.tiers_id, societe_id=societe_id
            ).first()
        piece.tiers_snapshot_json = json.dumps({
            "nom": getattr(tiers, "nom", None) or getattr(piece, "tiers", None),
            "ice": getattr(tiers, "ice", None),
            "if": getattr(tiers, "identifiant_fiscal", None),
            "rc": getattr(tiers, "rc", None),
            "adresse": getattr(tiers, "adresse", None),
            "ville": getattr(tiers, "ville", None),
            "telephone": getattr(tiers, "telephone", None),
            "email": getattr(tiers, "email", None),
            "categorie_fiscale": getattr(tiers, "categorie_fiscale", None),
        }, ensure_ascii=False, default=str)
    piece.notes_snapshot = getattr(piece, "notes", None)

def _resoudre_tiers(db, societe_id, tiers_id=None, nom=None, type_attendu=None):
    """Retourne le tiers lié au document sans jamais accepter un tiers d'une autre société.

    ``tiers_id`` est prioritaire. Pour les anciens clients qui n'envoient encore que
    le nom, on fait un rapprochement exact uniquement s'il est non ambigu.
    """
    tiers = None
    if tiers_id:
        tiers = db.query(models.Tiers).filter_by(id=tiers_id, societe_id=societe_id, actif=True).first()
        if not tiers:
            raise HTTPException(422, "Le client/fournisseur sélectionné est introuvable pour cette société.")
    elif nom:
        candidats = db.query(models.Tiers).filter(
            models.Tiers.societe_id == societe_id,
            models.Tiers.actif == True,
            models.Tiers.nom.ilike(nom.strip()),
        ).all()
        if len(candidats) == 1:
            tiers = candidats[0]
    if tiers and type_attendu:
        type_ok = tiers.type in {type_attendu, 'les_deux'}
        if not type_ok:
            lib = 'client' if type_attendu == 'client' else 'fournisseur'
            raise HTTPException(422, f"Le tiers sélectionné n'est pas configuré comme {lib}.")
    return tiers


def _delai_paiement_tiers(tiers):
    """Durée de paiement du tiers lié ; 60 j seulement si non renseignée.

    Un délai de 0 jour est une condition comptant valide : ne pas utiliser `or 60`.
    """
    delai = getattr(tiers, "delai_paiement", None)
    return 60 if delai is None else delai


def _article_ligne(db, societe_id, article_id=None, description=None):
    """Résout l'article par ID ; fallback texte uniquement pour les anciens documents."""
    if article_id:
        article = db.query(models.Article).filter_by(id=article_id, societe_id=societe_id, actif=True).first()
        if not article:
            raise HTTPException(422, "L'article sélectionné est introuvable pour cette société.")
        return article
    if description:
        candidats = db.query(models.Article).filter(
            models.Article.societe_id == societe_id,
            models.Article.actif == True,
            models.Article.designation.ilike(description.strip()),
        ).all()
        if len(candidats) == 1:
            return candidats[0]
    return None


def _net_ht_ligne(ligne, quantite=None):
    qte = float(quantite if quantite is not None else (getattr(ligne, 'quantite', 0) or 0))
    pu = float(getattr(ligne, 'prix_unitaire', 0) or 0)
    r1 = float(getattr(ligne, 'remise', 0) or 0)
    r2 = float(getattr(ligne, 'remise2', 0) or 0)
    rabais = float(getattr(ligne, 'rabais', 0) or 0)
    net = qte * pu * (1 - r1 / 100) * (1 - r2 / 100) - rabais * qte
    return max(net, 0.0)


def _taux_effectif_ligne(ligne):
    return float(getattr(ligne, "tva", 0) or 0) if (getattr(ligne, "qualification_tva", "taxable") == "taxable") else 0.0


def _verifier_lignes_tva(date_doc, lignes):
    try:
        for ligne in lignes or []:
            valider_tva(date_doc, getattr(ligne, "tva", 0), getattr(ligne, "qualification_tva", "taxable"))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def _valeur_enum(v):
    return getattr(v, "value", v)


def _exercice_ref(db, societe_id: int, d: _date) -> int:
    try:
        return trouver_exercice_pour_date(db, societe_id, d).annee
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


# FACT-A — machines d'état explicites. Les transitions internes effectuées par
# les fonctions de conversion restent possibles directement côté serveur ; ces
# règles protègent les PATCH exposés aux clients API.
_TRANSITIONS_DEVIS = {
    "brouillon": {"brouillon", "envoye", "accepte", "refuse", "expire"},
    "envoye": {"envoye", "accepte", "refuse", "expire"},
    "accepte": {"accepte", "converti"},
    "converti": {"converti"},
    "refuse": {"refuse"},
    "expire": {"expire"},
}
_TRANSITIONS_BC = {
    "en_attente": {"en_attente", "confirme", "facture", "annule"},
    "confirme": {"confirme", "facture", "annule"},
    "partiel": {"partiel"},
    "livre": {"livre"},
    "facture": {"facture"},
    "annule": {"annule"},
}
_TRANSITIONS_BL = {
    "en_preparation": {"en_preparation", "expedie"},
    "expedie": {"expedie", "livre"},
    "livre": {"livre", "retourne"},
    "retourne": {"retourne"},
}


def _verifier_transition(document, actuel, demande, transitions):
    actuel = _valeur_enum(actuel)
    demande = _valeur_enum(demande)
    if demande is None or demande == actuel:
        return
    if demande not in transitions.get(actuel, set()):
        raise HTTPException(409, f"Transition de statut interdite pour {document} : {actuel} → {demande}.")


def _facture_societe(db, societe_id, facture_id):
    if not facture_id:
        return None
    facture = db.query(models.Facture).filter_by(id=facture_id, societe_id=societe_id).first()
    if not facture:
        raise HTTPException(422, "La facture liée est introuvable pour cette société.")
    return facture


def _devis_societe(db, societe_id, devis_id):
    if not devis_id:
        return None
    devis = db.query(models.Devis).filter_by(id=devis_id, societe_id=societe_id).first()
    if not devis:
        raise HTTPException(422, "Le devis source est introuvable pour cette société.")
    return devis


def _bc_societe(db, societe_id, bc_id):
    if not bc_id:
        return None
    bc = db.query(models.BonCommande).filter_by(id=bc_id, societe_id=societe_id).first()
    if not bc:
        raise HTTPException(422, "Le bon de commande source est introuvable pour cette société.")
    return bc


def _verifier_lignes_source_devis(db, societe_id, lignes, devis_id=None):
    for ligne in lignes or []:
        ligne_id = getattr(ligne, "source_ligne_devis_id", None)
        if not ligne_id and isinstance(ligne, dict):
            ligne_id = ligne.get("source_ligne_devis_id")
        if not ligne_id:
            continue
        q = db.query(models.LigneDevis).join(models.Devis, models.Devis.id == models.LigneDevis.devis_id).filter(
            models.LigneDevis.id == ligne_id, models.Devis.societe_id == societe_id
        )
        if devis_id:
            q = q.filter(models.LigneDevis.devis_id == devis_id)
        if not q.first():
            raise HTTPException(422, "Une ligne de devis source est introuvable pour cette société ou ne correspond pas au devis indiqué.")


def _verifier_lignes_source_bc(db, societe_id, lignes, bc_id=None):
    for ligne in lignes or []:
        ligne_id = getattr(ligne, "source_ligne_bc_id", None)
        if not ligne_id and isinstance(ligne, dict):
            ligne_id = ligne.get("source_ligne_bc_id")
        if not ligne_id:
            continue
        q = db.query(models.LigneBonCommande).join(
            models.BonCommande, models.BonCommande.id == models.LigneBonCommande.bon_commande_id
        ).filter(models.LigneBonCommande.id == ligne_id, models.BonCommande.societe_id == societe_id)
        if bc_id:
            q = q.filter(models.LigneBonCommande.bon_commande_id == bc_id)
        if not q.first():
            raise HTTPException(422, "Une ligne de bon de commande source est introuvable pour cette société ou ne correspond pas au BC indiqué.")


def _verifier_date_operation_ouverte(db, societe_id, date_operation, libelle="opération"):
    """FACT-B — valide la vraie période cible, pas seulement l'année du document source."""
    if not date_operation:
        return None
    if isinstance(date_operation, str):
        try:
            date_operation = _date.fromisoformat(date_operation[:10])
        except ValueError as exc:
            raise HTTPException(422, "Date invalide, format attendu AAAA-MM-JJ") from exc
    if date_operation > _date.today():
        raise HTTPException(422, f"La date de {libelle} ne peut pas être future.")
    from services.exercices_service import verifier_date_ecriture
    try:
        return verifier_date_ecriture(db, societe_id, date_operation, f"enregistrer {libelle}")
    except ValueError as exc:
        raise HTTPException(423, str(exc)) from exc


def _facture_active(facture):
    return (
        bool(facture)
        and _valeur_enum(getattr(facture, "statut", None)) != "annulee"
        and not bool(getattr(facture, "est_proforma", False))
    )


def _facture_validee_active(facture):
    """Facture définitive prise en compte dans le réalisé du cycle.

    Un brouillon réserve le reliquat afin d'éviter une double facturation, mais
    il ne doit pas être affiché comme du chiffre effectivement facturé.
    """
    return _facture_active(facture) and bool(getattr(facture, "est_validee", False))


def _deja_facture_par_ligne(db, societe_id, bc):
    """Quantités déjà facturées par ligne de BC via les liens FACT.1."""
    ids = [l.id for l in bc.lignes]
    cumul = {i: 0.0 for i in ids}
    factures_ids = set()
    if ids:
        rows = db.query(models.LigneFacture, models.Facture).join(
            models.Facture, models.Facture.id == models.LigneFacture.facture_id
        ).filter(
            models.Facture.societe_id == societe_id,
            models.LigneFacture.source_ligne_bc_id.in_(ids),
        ).all()
        for lf, facture in rows:
            if not _facture_active(facture):
                continue
            cumul[lf.source_ligne_bc_id] = cumul.get(lf.source_ligne_bc_id, 0.0) + float(lf.quantite or 0)
            factures_ids.add(facture.id)

    # Legacy : une facture directe liée au BC sans liens de lignes couvre tout le bon.
    if bc.facture_id and not factures_ids:
        facture = db.query(models.Facture).filter_by(id=bc.facture_id, societe_id=societe_id).first()
        if _facture_active(facture):
            factures_ids.add(facture.id)
            for l in bc.lignes:
                cumul[l.id] = float(l.quantite or 0)
    return cumul, factures_ids


def _deja_facture_validee_par_ligne(db, societe_id, bc):
    """Quantités définitivement facturées par ligne de BC (hors brouillons)."""
    ids = [l.id for l in bc.lignes]
    cumul = {i: 0.0 for i in ids}
    factures_ids = set()
    if ids:
        rows = db.query(models.LigneFacture, models.Facture).join(
            models.Facture, models.Facture.id == models.LigneFacture.facture_id
        ).filter(
            models.Facture.societe_id == societe_id,
            models.LigneFacture.source_ligne_bc_id.in_(ids),
        ).all()
        for lf, facture in rows:
            if not _facture_validee_active(facture):
                continue
            cumul[lf.source_ligne_bc_id] = cumul.get(lf.source_ligne_bc_id, 0.0) + float(lf.quantite or 0)
            factures_ids.add(facture.id)

    if bc.facture_id and not factures_ids:
        facture = db.query(models.Facture).filter_by(id=bc.facture_id, societe_id=societe_id).first()
        if _facture_validee_active(facture):
            factures_ids.add(facture.id)
            for l in bc.lignes:
                cumul[l.id] = float(l.quantite or 0)
    return cumul, factures_ids


def _facturation_par_ligne_bl(db, societe_id, bl):
    """Quantités déjà facturées pour chaque ligne de BL/BR.

    Le lien ``source_ligne_bl_id`` permet plusieurs factures successives sans
    dépendre du champ legacy ``bon_livraison.facture_id``.
    """
    ids = [l.id for l in bl.lignes]
    cumul = {i: 0.0 for i in ids}
    factures = {}
    if not ids:
        return cumul, factures
    rows = db.query(models.LigneFacture, models.Facture).join(
        models.Facture, models.Facture.id == models.LigneFacture.facture_id
    ).filter(
        models.Facture.societe_id == societe_id,
        models.LigneFacture.source_ligne_bl_id.in_(ids),
    ).all()
    for lf, facture in rows:
        if not _facture_active(facture):
            continue
        cumul[lf.source_ligne_bl_id] = cumul.get(lf.source_ligne_bl_id, 0.0) + float(lf.quantite or 0)
        factures[facture.id] = facture.numero
    return cumul, factures


def _facturation_validee_par_ligne_bl(db, societe_id, bl):
    """Quantités de BL/BR portées sur des factures définitivement validées."""
    ids = [l.id for l in bl.lignes]
    cumul = {i: 0.0 for i in ids}
    factures = {}
    if not ids:
        return cumul, factures
    rows = db.query(models.LigneFacture, models.Facture).join(
        models.Facture, models.Facture.id == models.LigneFacture.facture_id
    ).filter(
        models.Facture.societe_id == societe_id,
        models.LigneFacture.source_ligne_bl_id.in_(ids),
    ).all()
    for lf, facture in rows:
        if not _facture_validee_active(facture):
            continue
        cumul[lf.source_ligne_bl_id] = cumul.get(lf.source_ligne_bl_id, 0.0) + float(lf.quantite or 0)
        factures[facture.id] = facture.numero
    return cumul, factures


def _situation_facturation_bl(db, societe_id, bl):
    """Situation facturable exacte d'un BL/BR, ligne par ligne."""
    reserve, factures_reservees = _facturation_par_ligne_bl(db, societe_id, bl)
    valide, factures_validees = _facturation_validee_par_ligne_bl(db, societe_id, bl)
    lignes = []
    total_ht = reserve_ht = valide_ht = 0.0
    q_total = q_reserve = q_valide = 0.0
    for l in bl.lignes:
        qte_physique = float(l.quantite_livree if l.quantite_livree is not None else (l.quantite_prevue or 0))
        qte_reservee = min(float(reserve.get(l.id, 0) or 0), qte_physique)
        qte_validee = min(float(valide.get(l.id, 0) or 0), qte_physique)
        reste = max(qte_physique - qte_reservee, 0.0)
        valeur = _net_ht_ligne(l, quantite=qte_physique)
        unitaire_net = valeur / qte_physique if qte_physique else 0.0
        total_ht += valeur
        reserve_ht += unitaire_net * qte_reservee
        valide_ht += unitaire_net * qte_validee
        q_total += qte_physique
        q_reserve += qte_reservee
        q_valide += qte_validee
        lignes.append({
            "id": l.id,
            "ligne_bl_id": l.id,
            "source_ligne_bc_id": l.source_ligne_bc_id,
            "article_id": l.article_id,
            "description": l.description,
            "quantite_livree": round(qte_physique, 4),
            "quantite_facturee": round(qte_validee, 4),
            "quantite_brouillon": round(max(qte_reservee - qte_validee, 0.0), 4),
            "quantite_reservee_facturation": round(qte_reservee, 4),
            "reste_a_facturer": round(reste, 4),
            "prix_unitaire": float(l.prix_unitaire or 0),
            "tva": float(l.tva or 0),
            "qualification_tva": getattr(l, "qualification_tva", "taxable") or "taxable",
            "remise": float(l.remise or 0),
            "remise2": float(l.remise2 or 0),
            "rabais": float(l.rabais or 0),
        })
    def _pct(montant, qte):
        if total_ht > 0.0001:
            return min(100.0, max(0.0, montant / total_ht * 100))
        if q_total > 0.0001:
            return min(100.0, max(0.0, qte / q_total * 100))
        return 100.0

    pct_valide = _pct(valide_ht, q_valide)
    pct_reserve = _pct(reserve_ht, q_reserve)
    return {
        "facturation_pct": round(pct_valide, 1),
        "facturation_reservee_pct": round(pct_reserve, 1),
        "montant_a_facturer_ht": round(total_ht, 2),
        "montant_facture_ht": round(valide_ht, 2),
        "montant_brouillon_ht": round(max(reserve_ht - valide_ht, 0.0), 2),
        "reste_a_facturer_ht": round(max(total_ht - reserve_ht, 0.0), 2),
        "nb_factures": len(factures_validees),
        "nb_brouillons": len(set(factures_reservees) - set(factures_validees)),
        "facture_numeros": [n for n in factures_validees.values() if n],
        "solde": all(x["reste_a_facturer"] <= 0.0001 for x in lignes),
        "lignes": lignes,
    }


def _situation_lignes_bc(db, societe_id, bc):
    """Commandé / livré / facturé / reliquats par ligne de bon de commande."""
    livraisons, _ = reliquat_bon_commande(db, societe_id, bc)
    par_livraison = {x["ligne_bc_id"]: x for x in livraisons}
    deja_reserve, _ = _deja_facture_par_ligne(db, societe_id, bc)
    deja_facture, _ = _deja_facture_validee_par_ligne(db, societe_id, bc)
    resultat = {}
    for l in bc.lignes:
        qcmd = float(l.quantite or 0)
        qliv = min(float(par_livraison.get(l.id, {}).get("quantite_livree", 0) or 0), qcmd)
        qreserve = min(float(deja_reserve.get(l.id, 0) or 0), qcmd)
        qfac = min(float(deja_facture.get(l.id, 0) or 0), qcmd)
        resultat[l.id] = {
            "quantite_commandee": round(qcmd, 4),
            "quantite_livree": round(qliv, 4),
            "quantite_facturee": round(qfac, 4),
            "quantite_brouillon": round(max(qreserve - qfac, 0.0), 4),
            "quantite_reservee_facturation": round(qreserve, 4),
            "reste_a_livrer": round(max(qcmd - qliv, 0.0), 4),
            "reste_a_facturer": round(max(qcmd - qreserve, 0.0), 4),
            "livre_non_facture": round(max(qliv - qfac, 0.0), 4),
        }
    return resultat


def _situation_cycle_bc(db, societe_id, bc):
    """Commandé / livré / facturé, pondéré par la valeur HT nette."""
    livraison, _ = reliquat_bon_commande(db, societe_id, bc)
    reserve_par_ligne, factures_reservees_ids = _deja_facture_par_ligne(db, societe_id, bc)
    facture_par_ligne, factures_ids = _deja_facture_validee_par_ligne(db, societe_id, bc)
    par_ligne_liv = {x["ligne_bc_id"]: x for x in livraison}

    total_ht = livre_ht = facture_ht = reserve_ht = 0.0
    qte_commandee = qte_livree = qte_facturee = qte_reservee = 0.0
    for l in bc.lignes:
        qcmd = float(l.quantite or 0)
        qliv = min(float(par_ligne_liv.get(l.id, {}).get("quantite_livree", 0) or 0), qcmd)
        qres = min(float(reserve_par_ligne.get(l.id, 0) or 0), qcmd)
        qfac = min(float(facture_par_ligne.get(l.id, 0) or 0), qcmd)
        valeur = _net_ht_ligne(l)
        unitaire_net = (valeur / qcmd) if qcmd else 0.0
        total_ht += valeur
        livre_ht += unitaire_net * qliv
        reserve_ht += unitaire_net * qres
        facture_ht += unitaire_net * qfac
        qte_commandee += qcmd
        qte_livree += qliv
        qte_reservee += qres
        qte_facturee += qfac

    def _pct(valeur, qte):
        if total_ht > 0.0001:
            return round(min(100.0, max(0.0, valeur / total_ht * 100)), 1)
        if qte_commandee > 0.0001:
            return round(min(100.0, max(0.0, qte / qte_commandee * 100)), 1)
        return 100.0

    liv_pct = _pct(livre_ht, qte_livree)
    fac_pct = _pct(facture_ht, qte_facturee)
    reserve_pct = _pct(reserve_ht, qte_reservee)
    nb_bons = db.query(models.BonLivraison).filter(
        models.BonLivraison.societe_id == societe_id,
        models.BonLivraison.bon_commande_id == bc.id,
        models.BonLivraison.statut != "annule",
    ).count()
    if _valeur_enum(getattr(bc, "statut", None)) == "annule":
        etat = "annule"
    elif liv_pct >= 99.95 and fac_pct >= 99.95:
        etat = "termine"
    elif fac_pct >= 99.95:
        etat = "facture"
    elif liv_pct >= 99.95:
        etat = "livre"
    elif liv_pct > 0 or fac_pct > 0:
        etat = "partiel"
    else:
        etat = "a_traiter"

    return {
        "statut_cycle": etat,
        "livraison_pct": liv_pct,
        "facturation_pct": fac_pct,
        "facturation_reservee_pct": reserve_pct,
        "montant_commande_ht": round(total_ht, 2),
        "montant_livre_ht": round(livre_ht, 2),
        "montant_facture_ht": round(facture_ht, 2),
        "montant_brouillon_ht": round(max(reserve_ht - facture_ht, 0), 2),
        "reste_a_livrer_ht": round(max(total_ht - livre_ht, 0), 2),
        "reste_a_facturer_ht": round(max(total_ht - reserve_ht, 0), 2),
        "nb_bons_logistiques": nb_bons,
        "nb_factures": len(factures_ids),
        "nb_brouillons": len(factures_reservees_ids - factures_ids),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _totaux_devis(lignes):
    ht = tva = 0
    for l in lignes:
        h = l.quantite * l.prix_unitaire
        ht += h; tva += h * (_taux_effectif_ligne(l) / 100)
    return ht, tva

def _facture_directe_du_devis(db, societe_id, devis_id):
    """Retourne la première facture active issue directement des lignes du devis.

    Le lien ``devis.facture_id`` est conservé pour compatibilité, mais la source de
    vérité est la traçabilité ligne-à-ligne. Ainsi l'UI reste correcte même si un
    ancien client n'a pas renseigné le lien de tête après création de la facture.
    """
    return db.query(models.Facture).join(
        models.LigneFacture, models.LigneFacture.facture_id == models.Facture.id
    ).join(
        models.LigneDevis, models.LigneDevis.id == models.LigneFacture.source_ligne_devis_id
    ).filter(
        models.Facture.societe_id == societe_id,
        models.LigneDevis.devis_id == devis_id,
        models.Facture.est_proforma == False,
        models.Facture.statut != models.StatutFactureEnum.annulee,
    ).order_by(models.Facture.id.asc()).first()


def _fmt_devis(d, db=None):
    ht, tva = _totaux_devis(d.lignes)
    facture_id  = getattr(d, 'facture_id', None)
    facture_num = None
    bc_id = None
    bc_num = None
    if db is not None:
        f = None
        if facture_id:
            f = db.query(models.Facture).filter_by(id=facture_id, societe_id=d.societe_id).first()
            if f and (bool(getattr(f, 'est_proforma', False)) or getattr(f, 'statut', None) == models.StatutFactureEnum.annulee):
                f = None
        if not f:
            f = _facture_directe_du_devis(db, d.societe_id, d.id)
        if f:
            facture_id = f.id
            facture_num = f.numero

        # L'existence réelle d'un BC est la source de vérité pour les actions UI.
        # On ne se fie pas uniquement au statut du devis, qui peut être historique.
        bc = db.query(models.BonCommande).filter_by(
            societe_id=d.societe_id, devis_id=d.id
        ).order_by(models.BonCommande.id.asc()).first()
        if bc:
            bc_id = bc.id
            bc_num = bc.numero
    return {
        **d.__dict__,
        "total_ht":   ht, "total_tva": tva, "total_ttc": ht + tva,
        "facture_id": facture_id,
        "facture_numero": facture_num,
        "bon_commande_id": bc_id,
        "bon_commande_numero": bc_num,
        "statut": "converti" if (facture_id or bc_id) else d.statut,
        "lignes": [{
            **l.__dict__,
            "montant_ht":  l.quantite * l.prix_unitaire,
            "montant_tva": l.quantite * l.prix_unitaire * (_taux_effectif_ligne(l) / 100),
            "montant_ttc": l.quantite * l.prix_unitaire * (1 + _taux_effectif_ligne(l) / 100),
        } for l in d.lignes]
    }

def _totaux_bc(lignes):
    ht = tva = 0.0
    for l in lignes:
        h = _net_ht_ligne(l)
        ht += h
        tva += h * (_taux_effectif_ligne(l) / 100)
    return ht, tva

def _fmt_bc(bc, db=None):
    ht, tva = _totaux_bc(bc.lignes)
    situation_lignes = _situation_lignes_bc(db, bc.societe_id, bc) if db is not None else {}
    lignes = []
    for l in bc.lignes:
        h = _net_ht_ligne(l)
        tv = h * (_taux_effectif_ligne(l) / 100)
        lignes.append({
            **l.__dict__,
            "montant_ht": h, "montant_tva": tv, "montant_ttc": h + tv,
            **situation_lignes.get(l.id, {
                "quantite_commandee": float(l.quantite or 0),
                "quantite_livree": 0.0, "quantite_facturee": 0.0,
                "reste_a_livrer": float(l.quantite or 0),
                "reste_a_facturer": float(l.quantite or 0),
                "livre_non_facture": 0.0,
            }),
        })
    cycle = _situation_cycle_bc(db, bc.societe_id, bc) if db is not None else {}
    return {
        **bc.__dict__,
        "total_ht": ht, "total_tva": tva, "total_ttc": ht + tva,
        "lignes": lignes,
        **cycle,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DEVIS
# ═══════════════════════════════════════════════════════════════════════════════

@router_devis.get("", response_model=List[schemas.DevisOut])
def lister_devis(
    exercice:  int           = Query(...),
    statut:    Optional[str] = Query(None),
    recherche: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(models.Devis).options(joinedload(models.Devis.lignes)) \
        .filter_by(societe_id=current_user["societe_id"]) \
        .filter(models.Devis.exercice == exercice)
    if statut:    q = q.filter(models.Devis.statut == statut)
    if recherche: q = q.filter(models.Devis.tiers.ilike(f"%{recherche}%") | models.Devis.numero.ilike(f"%{recherche}%"))
    return [_fmt_devis(d, db) for d in q.order_by(models.Devis.created_at.desc().nullslast(), models.Devis.id.desc()).all()]


@router_devis.post("", response_model=schemas.DevisOut, status_code=201)
def creer_devis(
    data: schemas.DevisCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_lignes_tva(data.date, data.lignes)
    numero = (data.numero or "").strip()
    if numero:
        existant = db.query(models.Devis).filter_by(societe_id=societe_id, numero=numero).first()
        if existant:
            raise HTTPException(409, f"Numéro de devis '{numero}' déjà utilisé")
    else:
        societe = db.query(models.Societe).filter_by(id=societe_id).first()
        prefixe = (getattr(societe, "prefixe_devis", None) or "DV").strip() or "DV"
        numero = reserver_numero_commercial(db, societe_id, _exercice_ref(db, societe_id, data.date), "devis", prefixe)

    tiers_obj = _resoudre_tiers(db, societe_id, data.tiers_id, data.tiers, "client")
    devis = models.Devis(
        societe_id=societe_id,
        numero=numero, date=data.date,
        exercice=_exercice_ref(db, societe_id, data.date), tiers=(tiers_obj.nom if tiers_obj else data.tiers),
        tiers_id=(tiers_obj.id if tiers_obj else None),
        reference=data.reference, validite_jours=data.validite_jours,
        notes=data.notes, statut="brouillon",
    )
    db.add(devis); db.flush()
    for l in data.lignes:
        article = _article_ligne(db, societe_id, l.article_id, l.description)
        db.add(models.LigneDevis(
            devis_id=devis.id, article_id=(article.id if article else None),
            description=l.description, quantite=l.quantite,
            prix_unitaire=l.prix_unitaire, tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable",
        ))
    db.commit(); db.refresh(devis)
    return _fmt_devis(db.query(models.Devis).options(joinedload(models.Devis.lignes)).filter_by(id=devis.id).first(), db)


@router_devis.patch("/{devis_id}", response_model=schemas.DevisOut)
def modifier_devis(
    devis_id: int,
    data: schemas.DevisUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    devis = db.query(models.Devis).filter_by(id=devis_id, societe_id=current_user["societe_id"]).first()
    if not devis: raise HTTPException(404, "Devis introuvable")

    payload = data.model_dump(exclude_none=True)
    lignes = payload.pop("lignes", None)

    # FACT-C / F-014 — une offre acceptée constitue la base de l'engagement
    # commercial : ses éléments économiques sont figés. Après conversion, seule
    # une note interne peut encore être enrichie.
    statut_actuel = _valeur_enum(devis.statut)
    champs_impactants = {"numero", "date", "tiers", "tiers_id", "reference", "validite_jours", "facture_id"}
    if statut_actuel in {"accepte", "converti"}:
        demandes_impactantes = champs_impactants.intersection(payload.keys())
        if lignes is not None or demandes_impactantes:
            raise HTTPException(409,
                "Un devis accepté ou converti est figé. Créez un nouveau devis/document correctif ; seules les notes restent modifiables.")

    if "facture_id" in payload:
        _facture_societe(db, current_user["societe_id"], payload.get("facture_id"))
    if "statut" in payload:
        _verifier_transition("le devis", devis.statut, payload["statut"], _TRANSITIONS_DEVIS)
        if payload["statut"] == "converti":
            facture_liee = payload.get("facture_id") or getattr(devis, "facture_id", None)
            bc_lie = db.query(models.BonCommande).filter_by(
                societe_id=current_user["societe_id"], devis_id=devis.id
            ).first()
            if not facture_liee and not bc_lie:
                raise HTTPException(409, "Un devis ne peut passer à 'converti' que lorsqu'un document aval existe.")

    if lignes is not None:
        _verifier_lignes_tva(payload.get("date") or devis.date, [schemas.LigneDevisCreate(**l) if isinstance(l, dict) else l for l in lignes])
    if "tiers" in payload or "tiers_id" in payload:
        tiers_obj = _resoudre_tiers(
            db, current_user["societe_id"], payload.get("tiers_id"),
            payload.get("tiers", devis.tiers), "client"
        )
        if tiers_obj:
            payload["tiers"] = tiers_obj.nom
            payload["tiers_id"] = tiers_obj.id
    for k, v in payload.items():
        setattr(devis, k, v)

    if lignes is not None:
        db.query(models.LigneDevis).filter_by(devis_id=devis_id).delete()
        for l in lignes:
            article = _article_ligne(db, current_user["societe_id"], l.get("article_id"), l.get("description"))
            db.add(models.LigneDevis(
                devis_id=devis_id, article_id=(article.id if article else None),
                description=l["description"], quantite=l.get("quantite", 1),
                prix_unitaire=l.get("prix_unitaire", 0), tva=l.get("tva", 20), qualification_tva=l.get("qualification_tva", "taxable"),
            ))

    if _valeur_enum(devis.statut) != "brouillon":
        _figer_document_commercial(db, current_user["societe_id"], devis)

    db.commit()
    return _fmt_devis(db.query(models.Devis).options(joinedload(models.Devis.lignes)).filter_by(id=devis_id).first(), db)


@router_devis.delete("/{devis_id}", status_code=204)
def supprimer_devis(
    devis_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    devis = db.query(models.Devis).filter_by(id=devis_id, societe_id=current_user["societe_id"]).first()
    if not devis: raise HTTPException(404, "Devis introuvable")

    if _valeur_enum(devis.statut) in {"accepte", "converti"}:
        raise HTTPException(409,
            "Un devis accepté ou converti ne peut plus être supprimé afin de conserver l'historique commercial.")

    # Vérifier qu'il n'y a pas de document aval lié.
    bc_lie = db.query(models.BonCommande).filter_by(
        societe_id=current_user["societe_id"], devis_id=devis_id
    ).first()
    if bc_lie:
        raise HTTPException(409, f"Impossible de supprimer ce devis — un bon de commande ({bc_lie.numero}) en dépend.")
    facture_liee = _facture_directe_du_devis(db, current_user["societe_id"], devis_id)
    if facture_liee:
        libelle = facture_liee.numero or f"brouillon #{facture_liee.id}"
        raise HTTPException(409, f"Impossible de supprimer ce devis — une facture ({libelle}) en dépend.")

    db.delete(devis); db.commit()


@router_devis.post("/{devis_id}/convertir-bc", response_model=schemas.BonCommandeOut)
def convertir_devis_en_bc(
    devis_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Convertit un devis accepté en bon de commande."""
    # Verrouiller le devis pendant la conversion : deux utilisateurs ne peuvent
    # pas créer simultanément deux documents aval depuis le même devis.
    devis = db.query(models.Devis).filter_by(
        id=devis_id, societe_id=current_user["societe_id"]
    ).with_for_update().first()
    if not devis: raise HTTPException(404, "Devis introuvable")
    if _valeur_enum(devis.statut) != "accepte":
        raise HTTPException(409, "Seul un devis accepté peut être converti en bon de commande.")

    # Bloquer si un document aval existe déjà pour ce devis.
    bc_existant = db.query(models.BonCommande).filter_by(
        societe_id=current_user["societe_id"], devis_id=devis_id
    ).first()
    if bc_existant:
        raise HTTPException(409, f"Un bon de commande ({bc_existant.numero}) existe déjà pour ce devis.")
    facture_existante = _facture_directe_du_devis(db, current_user["societe_id"], devis_id)
    if facture_existante:
        libelle = facture_existante.numero or f"brouillon #{facture_existante.id}"
        raise HTTPException(409, f"Une facture ({libelle}) existe déjà pour ce devis.")

    # Numérotation atomique : deux conversions simultanées ne peuvent pas
    # réserver le même numéro de BC.
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    prefixe_bc = (getattr(societe, "prefixe_bc", None) or "BC").strip() or "BC"
    date_bc = _date.today()
    numero_bc = reserver_numero_commercial(
        db, current_user["societe_id"], _exercice_ref(db, current_user["societe_id"], date_bc), "bc", prefixe_bc
    )

    bc = models.BonCommande(
        societe_id=current_user["societe_id"],
        devis_id=devis.id, numero=numero_bc,
        type="vente", date=date_bc,
        exercice=_exercice_ref(db, current_user["societe_id"], date_bc), tiers=devis.tiers, tiers_id=devis.tiers_id,
        reference=devis.reference, statut="en_attente",
    )
    db.add(bc); db.flush()
    for l in devis.lignes:
        db.add(models.LigneBonCommande(
            bon_commande_id=bc.id,
            article_id=l.article_id, source_ligne_devis_id=l.id,
            description=l.description, quantite=l.quantite,
            prix_unitaire=l.prix_unitaire, tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable",
            remise=0, remise2=0, rabais=0,
        ))
    # Dès que le BC existe réellement, le devis est converti. La source de vérité
    # reste toutefois le lien BonCommande.devis_id exposé par _fmt_devis.
    devis.statut = "converti"
    _figer_document_commercial(db, current_user["societe_id"], devis)
    db.commit(); db.refresh(bc)
    return _fmt_bc(db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)).filter_by(id=bc.id).first(), db)


# ═══════════════════════════════════════════════════════════════════════════════
# BON DE COMMANDE
# ═══════════════════════════════════════════════════════════════════════════════

@router_bc.get("", response_model=List[schemas.BonCommandeOut])
def lister_bc(
    exercice:  int           = Query(...),
    type:      Optional[str] = Query(None),
    statut:    Optional[str] = Query(None),
    recherche: Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
        .filter_by(societe_id=current_user["societe_id"]) \
        .filter(models.BonCommande.exercice == exercice)
    if type:      q = q.filter(models.BonCommande.type == type)
    if statut:    q = q.filter(models.BonCommande.statut == statut)
    if recherche: q = q.filter(models.BonCommande.tiers.ilike(f"%{recherche}%") | models.BonCommande.numero.ilike(f"%{recherche}%"))
    return [_fmt_bc(bc, db) for bc in q.order_by(models.BonCommande.created_at.desc().nullslast(), models.BonCommande.id.desc()).all()]


@router_bc.post("", response_model=schemas.BonCommandeOut, status_code=201)
def creer_bc(
    data: schemas.BonCommandeCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_lignes_tva(data.date, data.lignes)
    numero = (data.numero or "").strip()
    if numero:
        existant = db.query(models.BonCommande).filter_by(societe_id=societe_id, numero=numero).first()
        if existant:
            raise HTTPException(409, f"Numéro BC '{numero}' déjà utilisé")
    else:
        societe = db.query(models.Societe).filter_by(id=societe_id).first()
        prefixe = (getattr(societe, "prefixe_bc", None) or "BC").strip() or "BC"
        numero = reserver_numero_commercial(db, societe_id, _exercice_ref(db, societe_id, data.date), "bc", prefixe)

    # FACT-A / F-031 — toutes les références amont doivent appartenir à la société courante.
    if data.devis_id:
        _devis_societe(db, societe_id, data.devis_id)
        if data.type != "vente":
            raise HTTPException(422, "Un devis client ne peut alimenter qu'un bon de commande de vente.")
        bc_devis = db.query(models.BonCommande).filter_by(
            societe_id=societe_id, devis_id=data.devis_id
        ).first()
        if bc_devis:
            raise HTTPException(400, f"Un bon de commande ({bc_devis.numero}) existe déjà pour ce devis.")
    _verifier_lignes_source_devis(db, societe_id, data.lignes, data.devis_id)

    type_tiers = "fournisseur" if data.type == "achat" else "client"
    tiers_obj = _resoudre_tiers(db, societe_id, data.tiers_id, data.tiers, type_tiers)
    payload = data.model_dump(exclude={"lignes", "tiers_id"})
    payload["numero"] = numero
    payload["tiers"] = tiers_obj.nom if tiers_obj else data.tiers
    bc = models.BonCommande(
        societe_id=societe_id, tiers_id=(tiers_obj.id if tiers_obj else None), **payload
    )
    bc.exercice = _exercice_ref(db, societe_id, data.date)
    db.add(bc); db.flush()
    for l in data.lignes:
        article = _article_ligne(db, societe_id, l.article_id, l.description)
        db.add(models.LigneBonCommande(
            bon_commande_id=bc.id, article_id=(article.id if article else None),
            source_ligne_devis_id=l.source_ligne_devis_id,
            description=l.description, quantite=l.quantite, prix_unitaire=l.prix_unitaire,
            tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable", remise=l.remise, remise2=l.remise2, rabais=l.rabais,
        ))
    db.commit(); db.refresh(bc)
    return _fmt_bc(db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)).filter_by(id=bc.id).first(), db)


@router_bc.patch("/{bc_id}", response_model=schemas.BonCommandeOut)
def modifier_bc(
    bc_id: int,
    data: schemas.BonCommandeUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    bc = db.query(models.BonCommande).filter_by(id=bc_id, societe_id=current_user["societe_id"]).first()
    if not bc: raise HTTPException(404, "Bon de commande introuvable")

    payload = data.model_dump(exclude_none=True)
    lignes  = payload.pop('lignes', None)
    if lignes is not None:
        _verifier_lignes_tva(bc.date, [schemas.LigneBCCreate(**l) if isinstance(l, dict) else l for l in lignes])
    a_bons = db.query(models.BonLivraison).filter_by(
        societe_id=current_user["societe_id"], bon_commande_id=bc_id
    ).count() > 0
    deja_facture, _ = _deja_facture_par_ligne(db, current_user["societe_id"], bc)
    a_facture = bool(bc.facture_id) or any(v > 0.0001 for v in deja_facture.values())

    if lignes is not None:
        _verifier_lignes_source_devis(db, current_user["societe_id"], lignes, bc.devis_id)
    if "facture_id" in payload:
        _facture_societe(db, current_user["societe_id"], payload.get("facture_id"))
    if "statut" in payload:
        _verifier_transition("le bon de commande", bc.statut, payload["statut"], _TRANSITIONS_BC)
        if payload["statut"] == "facture" and not (payload.get("facture_id") or bc.facture_id):
            raise HTTPException(409, "Le statut 'facture' nécessite une facture liée appartenant à cette société.")
        if payload["statut"] == "annule" and (a_bons or a_facture):
            raise HTTPException(409, "Ce bon de commande a déjà généré un document en aval et ne peut plus être annulé directement.")

    champs_structurels = {"numero", "tiers", "tiers_id", "type"}
    veut_structure = lignes is not None or any(k in payload for k in champs_structurels)
    if (a_bons or a_facture) and veut_structure:
        raise HTTPException(409,
            "Ce bon de commande a déjà généré un document en aval. Son tiers, son numéro, "
            "son type et ses lignes sont désormais figés ; seules les notes et la date de "
            "livraison promise peuvent être ajustées.")
    if "tiers" in payload or "tiers_id" in payload:
        type_tiers = "fournisseur" if payload.get("type", bc.type) == "achat" else "client"
        tiers_obj = _resoudre_tiers(
            db, current_user["societe_id"], payload.get("tiers_id"),
            payload.get("tiers", bc.tiers), type_tiers
        )
        if tiers_obj:
            payload["tiers"] = tiers_obj.nom
            payload["tiers_id"] = tiers_obj.id

    for k, v in payload.items():
        setattr(bc, k, v)

    if lignes is not None:
        db.query(models.LigneBonCommande).filter_by(bon_commande_id=bc_id).delete()
        for l in lignes:
            article = _article_ligne(db, current_user["societe_id"], l.get("article_id"), l.get("description"))
            db.add(models.LigneBonCommande(
                bon_commande_id=bc_id, article_id=(article.id if article else None),
                source_ligne_devis_id=l.get("source_ligne_devis_id"),
                description=l['description'], quantite=l['quantite'], prix_unitaire=l['prix_unitaire'],
                tva=l.get('tva', 20), qualification_tva=l.get('qualification_tva', 'taxable'), remise=l.get('remise', 0),
                remise2=l.get('remise2', 0), rabais=l.get('rabais', 0),
            ))

    if _valeur_enum(bc.statut) != "en_attente":
        _figer_document_commercial(db, current_user["societe_id"], bc)
    db.commit()
    return _fmt_bc(db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)).filter_by(id=bc_id).first(), db)


@router_bc.delete("/{bc_id}", status_code=204)
def supprimer_bc(
    bc_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    bc = db.query(models.BonCommande).filter_by(id=bc_id, societe_id=current_user["societe_id"]).first()
    if not bc: raise HTTPException(404, "Bon de commande introuvable")

    nb_bons = db.query(models.BonLivraison).filter_by(
        societe_id=current_user["societe_id"], bon_commande_id=bc_id
    ).count()
    deja_facture, _ = _deja_facture_par_ligne(db, current_user["societe_id"], bc)
    if nb_bons or bc.facture_id or any(v > 0.0001 for v in deja_facture.values()):
        raise HTTPException(409,
            "Ce bon de commande a déjà généré une livraison/réception ou une facture. "
            "Il ne peut plus être supprimé ; utilisez un document correctif si nécessaire.")

    # Si ce BC vient d'un devis → remettre le devis en 'accepte'
    if bc.devis_id:
        devis = db.query(models.Devis).filter_by(id=bc.devis_id).first()
        if devis and devis.statut == 'converti':
            devis.statut = 'accepte'

    db.delete(bc); db.commit()


@router_bc.post("/{bc_id}/convertir-facture", response_model=schemas.FactureOut)
def convertir_bc_en_facture(
    bc_id: int,
    data: schemas.ConvertirBCFactureIn = schemas.ConvertirBCFactureIn(),
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Convertit un BC en facture, en respectant le type du BC (vente ou achat)."""
    bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
        .filter_by(id=bc_id, societe_id=current_user["societe_id"]).first()
    if not bc: raise HTTPException(404, "Bon de commande introuvable")

    deja_facture, _ = _deja_facture_par_ligne(db, current_user["societe_id"], bc)
    if bc.facture_id or any(v > 0.0001 for v in deja_facture.values()):
        raise HTTPException(409,
            "Ce bon de commande est déjà facturé, au moins partiellement. "
            "Facturez les bons de livraison/réception restants au lieu de créer une facture directe du BC.")
    date_facture = data.date or _date.today()
    exercice_facture = _verifier_date_operation_ouverte(db, current_user["societe_id"], date_facture, "facture")

    est_achat = bc.type == "achat"
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    # FACT.4 : la conversion crée un brouillon. Le N° définitif sera attribué
    # atomiquement lorsque l'utilisateur validera la facture.
    numero_f = None

    tiers_obj = _resoudre_tiers(
        db, current_user["societe_id"], bc.tiers_id, bc.tiers,
        "fournisseur" if est_achat else "client"
    )
    facture = models.Facture(
        societe_id=current_user["societe_id"],
        numero=numero_f, type=("achat" if est_achat else "vente"),
        date=date_facture, exercice=exercice_facture.annee,
        tiers=(tiers_obj.nom if tiers_obj else bc.tiers),
        tiers_id=(tiers_obj.id if tiers_obj else bc.tiers_id),
        tiers_ice_snapshot=(tiers_obj.ice if tiers_obj else None),
        tiers_if_snapshot=(tiers_obj.identifiant_fiscal if tiers_obj else None),
        tiers_rc_snapshot=(tiers_obj.rc if tiers_obj else None),
        tiers_adresse_snapshot=(tiers_obj.adresse if tiers_obj else None),
        tiers_ville_snapshot=(tiers_obj.ville if tiers_obj else None),
        tiers_telephone_snapshot=(tiers_obj.telephone if tiers_obj else None),
        tiers_email_snapshot=(tiers_obj.email if tiers_obj else None),
        tiers_categorie_snapshot=(getattr(tiers_obj, "categorie_fiscale", None) if tiers_obj else None),
        reference=(None if est_achat else bc.reference), statut="en_attente",
        delai_paiement=_delai_paiement_tiers(tiers_obj),
        date_echeance=date_facture + timedelta(days=_delai_paiement_tiers(tiers_obj)), est_validee=False,
        regime_tva=(getattr(societe, "regime_tva", None) or "encaissement"),
    )
    db.add(facture); db.flush()

    total_ht = total_tva = 0
    for l in bc.lignes:
        ligne = models.LigneFacture(
            facture_id=facture.id, article_id=l.article_id,
            source_ligne_devis_id=l.source_ligne_devis_id, source_ligne_bc_id=l.id,
            description=l.description, quantite=l.quantite, prix_unitaire=l.prix_unitaire,
            tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable", remise=l.remise, remise2=l.remise2, rabais=l.rabais,
        )
        db.add(ligne)
        ht = _net_ht_ligne(l)
        total_ht += ht; total_tva += ht * (_taux_effectif_ligne(l) / 100)

    bc.statut = "confirme"
    bc.facture_id = facture.id
    _figer_document_commercial(db, current_user["societe_id"], bc)
    db.commit(); db.refresh(facture)

    return {
        **facture.__dict__,
        "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ht + total_tva,
        "lignes": [{
            **l.__dict__,
            "montant_ht":  l.quantite * l.prix_unitaire,
            "montant_tva": l.quantite * l.prix_unitaire * (_taux_effectif_ligne(l) / 100),
            "montant_ttc": l.quantite * l.prix_unitaire * (1 + _taux_effectif_ligne(l) / 100),
        } for l in facture.lignes]
    }


@router_bc.get("/{bc_id}/reliquat")
def consulter_reliquat(
    bc_id: int,
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    """Reste à livrer d'un bon de commande, ligne par ligne."""
    bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
        .filter_by(id=bc_id, societe_id=current_user["societe_id"]).first()
    if not bc:
        raise HTTPException(404, "Bon de commande introuvable")

    lignes, solde = reliquat_bon_commande(db, current_user["societe_id"], bc)
    bons = db.query(models.BonLivraison).filter_by(
        societe_id=current_user["societe_id"], bon_commande_id=bc_id).all()

    return {
        "bon_commande": bc.numero,
        "type": bc.type,
        "statut": bc.statut,
        "solde": solde,
        "nb_livraisons": len(bons),
        "livraisons": [{"numero": b.numero, "date": str(b.date), "statut": b.statut} for b in bons],
        "lignes": lignes,
        "total_commande": round(sum(l["quantite_commandee"] for l in lignes), 4),
        "total_livre": round(sum(l["quantite_livree"] for l in lignes), 4),
        "total_reliquat": round(sum(l["reliquat"] for l in lignes), 4),
    }


@router_bc.post("/{bc_id}/convertir-bl", response_model=schemas.BonLivraisonOut)
def convertir_bc_en_bl(
    bc_id: int,
    data: schemas.ConvertirBLIn = schemas.ConvertirBLIn(),
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Convertit un BC en bon de livraison (vente) ou de réception (achat), selon
    le type du BC. La date est paramétrable ; par défaut, la date du jour."""
    bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
        .filter_by(id=bc_id, societe_id=current_user["societe_id"]).first()
    if not bc: raise HTTPException(404, "Bon de commande introuvable")

    est_achat = bc.type == "achat"
    doc = "bon de réception" if est_achat else "bon de livraison"

    # Livraisons partielles autorisées : on refuse seulement si tout est déjà livré.
    lignes_reliquat, tout_livre = reliquat_bon_commande(db, current_user["societe_id"], bc)
    if tout_livre:
        raise HTTPException(400,
            f"Ce bon de commande est entièrement livré : il n'y a plus de reliquat à porter sur un {doc}.")

    from datetime import date as date_cls
    date_bl = data.date or date_cls.today().isoformat()
    if isinstance(date_bl, str):
        try:
            date_bl = date_cls.fromisoformat(date_bl[:10])
        except ValueError as exc:
            raise HTTPException(422, "Date de livraison/réception invalide, format attendu AAAA-MM-JJ") from exc
    # Le BL/BR est encore un brouillon logistique à ce stade : une date future
    # peut être préparée. La période est contrôlée au passage effectif en livré.
    exercice_bl_annee = _exercice_ref(db, current_user["societe_id"], date_bl)

    # FACT-E : une demande supérieure au reliquat est une erreur métier. On ne
    # réduit plus silencieusement la quantité, car cela ferait croire à l'appelant
    # que la totalité demandée a été enregistrée.
    if data.lignes:
        par_id = {r["ligne_bc_id"]: r for r in lignes_reliquat}
        par_desc = {}
        for r in lignes_reliquat:
            par_desc.setdefault((r.get("description") or "").strip(), []).append(r)
        demandes = {}
        for x in data.lignes:
            info = None
            if x.ligne_bc_id is not None:
                info = par_id.get(x.ligne_bc_id)
                if not info:
                    raise HTTPException(422, f"La ligne de commande #{x.ligne_bc_id} n'appartient pas à ce bon de commande.")
            else:
                correspondances = par_desc.get((x.description or "").strip(), [])
                if len(correspondances) != 1:
                    raise HTTPException(422,
                        "La ligne à livrer doit être identifiée de façon unique par ligne_bc_id.")
                info = correspondances[0]
            cle = info["ligne_bc_id"]
            demandes[cle] = demandes.get(cle, 0.0) + float(x.quantite or 0)
        for ligne_id, qte in demandes.items():
            reste = float(par_id[ligne_id]["reliquat"] or 0)
            if qte > reste + 0.0001:
                raise HTTPException(400,
                    f"{par_id[ligne_id]['description']} : quantité demandée {qte:g} supérieure au reliquat {reste:g}.")

    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    prefixe_bl = "BR" if est_achat else (getattr(societe, "prefixe_bl", None) or "BL")
    # Numérotation atomique par type logistique et exercice.
    numero_bl = reserver_numero_commercial(
        db,
        current_user["societe_id"],
        exercice_bl_annee,
        "br" if est_achat else "bl",
        prefixe_bl,
    )

    bl = models.BonLivraison(
        societe_id=current_user["societe_id"],
        bon_commande_id=bc.id,
        facture_id=bc.facture_id,
        numero=numero_bl,
        type=bc.type,
        date=date_bl,
        exercice=exercice_bl_annee,
        tiers=bc.tiers, tiers_id=bc.tiers_id,
        statut="en_preparation",
    )
    db.add(bl); db.flush()

    # Quantités à porter sur ce bon : celles demandées (livraison partielle),
    # sinon la totalité du reliquat.
    demande_ids, demande_desc = {}, {}
    if data.lignes:
        for x in data.lignes:
            if x.ligne_bc_id:
                demande_ids[x.ligne_bc_id] = demande_ids.get(x.ligne_bc_id, 0) + (x.quantite or 0)
            else:
                demande_desc[x.description] = demande_desc.get(x.description, 0) + (x.quantite or 0)

    nb_lignes = 0
    for r in lignes_reliquat:
        reste = r["reliquat"]
        if reste <= 0.0001:
            continue
        if data.lignes:
            qte = demande_ids.get(r["ligne_bc_id"], demande_desc.get(r["description"], 0))
        else:
            qte = reste
        # Les dépassements ont été refusés en amont : aucune réduction silencieuse.
        if qte <= 0.0001:
            continue
        db.add(models.LigneBonLivraison(
            bon_livraison_id=bl.id, article_id=r.get("article_id"),
            source_ligne_bc_id=r["ligne_bc_id"], description=r["description"],
            quantite_prevue=qte, quantite_livree=qte,
            prix_unitaire=r.get("prix_unitaire", 0), tva=r.get("tva", 20), qualification_tva=r.get("qualification_tva", "taxable"),
            remise=r.get("remise", 0), remise2=r.get("remise2", 0), rabais=r.get("rabais", 0),
        ))
        nb_lignes += 1

    if nb_lignes == 0:
        db.rollback()
        raise HTTPException(400, "Aucune quantité à livrer : le reliquat est nul.")

    db.flush()
    # Statut du BC selon l'avancement : soldé si plus rien à livrer, sinon partiel.
    _, solde = reliquat_bon_commande(db, current_user["societe_id"], bc)
    bc.statut = "livre" if solde else "partiel"

    _figer_document_commercial(db, current_user["societe_id"], bc)
    db.commit(); db.refresh(bl)
    return db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)).filter_by(id=bl.id).first()


# ═══════════════════════════════════════════════════════════════════════════════
# BON DE LIVRAISON
# ═══════════════════════════════════════════════════════════════════════════════

def _fmt_bl(bl, db=None):
    situation = _situation_facturation_bl(db, bl.societe_id, bl) if db is not None else {}
    return {
        **bl.__dict__,
        "bon_commande_numero": bl.bon_commande.numero if bl.bon_commande is not None else None,
        "lignes": [{**l.__dict__} for l in bl.lignes],
        **situation,
    }

@router_bl.get("", response_model=List[schemas.BonLivraisonOut])
def lister_bl(
    exercice:  int           = Query(...),
    type:      Optional[str] = Query(None),
    statut:    Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(models.BonLivraison).options(
        joinedload(models.BonLivraison.lignes),
        joinedload(models.BonLivraison.bon_commande),
    ).filter_by(societe_id=current_user["societe_id"]) \
        .filter(models.BonLivraison.exercice == exercice)
    if type:   q = q.filter(models.BonLivraison.type == type)
    if statut: q = q.filter(models.BonLivraison.statut == statut)
    return [_fmt_bl(bl, db) for bl in q.order_by(models.BonLivraison.created_at.desc().nullslast(), models.BonLivraison.id.desc()).all()]


@router_bl.post("", response_model=schemas.BonLivraisonOut, status_code=201)
def creer_bl(
    data: schemas.BonLivraisonCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    _verifier_lignes_tva(data.date, data.lignes)

    bc_source = _bc_societe(db, societe_id, data.bon_commande_id) if data.bon_commande_id else None
    facture_source = _facture_societe(db, societe_id, data.facture_id) if data.facture_id else None
    if bc_source and bc_source.type != data.type:
        raise HTTPException(422, "Le type du bon logistique doit correspondre au bon de commande source.")
    if facture_source and _valeur_enum(facture_source.type) != data.type:
        raise HTTPException(422, "Le type du bon logistique doit correspondre à la facture source.")
    _verifier_lignes_source_bc(db, societe_id, data.lignes, data.bon_commande_id)

    type_tiers = "fournisseur" if data.type == "achat" else "client"
    tiers_obj = _resoudre_tiers(db, societe_id, data.tiers_id, data.tiers, type_tiers)
    numero = (data.numero or "").strip()
    if numero:
        existant = db.query(models.BonLivraison).filter_by(societe_id=societe_id, numero=numero).first()
        if existant:
            raise HTTPException(409, f"Numéro de bon '{numero}' déjà utilisé")
    else:
        societe = db.query(models.Societe).filter_by(id=societe_id).first()
        est_achat = data.type == "achat"
        prefixe = "BR" if est_achat else ((getattr(societe, "prefixe_bl", None) or "BL").strip() or "BL")
        numero = reserver_numero_commercial(db, societe_id, _exercice_ref(db, societe_id, data.date), "br" if est_achat else "bl", prefixe)
    payload = data.model_dump(exclude={"lignes", "tiers_id"})
    payload["numero"] = numero
    payload["tiers"] = tiers_obj.nom if tiers_obj else data.tiers
    bl = models.BonLivraison(
        societe_id=societe_id, tiers_id=(tiers_obj.id if tiers_obj else None), **payload
    )
    bl.exercice = _exercice_ref(db, societe_id, data.date)
    db.add(bl); db.flush()
    for l in data.lignes:
        article = _article_ligne(db, societe_id, l.article_id, l.description)
        db.add(models.LigneBonLivraison(
            bon_livraison_id=bl.id, article_id=(article.id if article else None),
            source_ligne_bc_id=l.source_ligne_bc_id, description=l.description,
            quantite_prevue=l.quantite_prevue, quantite_livree=l.quantite_livree,
            prix_unitaire=l.prix_unitaire, tva=l.tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable", remise=l.remise,
            remise2=l.remise2, rabais=l.rabais,
        ))
    db.commit(); db.refresh(bl)
    return db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)).filter_by(id=bl.id).first()


def _deja_livre_par_ligne(db, societe_id, bc_id):
    """Quantités déjà livrées par ID de ligne BC.

    Les anciens BL sans ``source_ligne_bc_id`` gardent un fallback par désignation
    afin de rester lisibles après migration, mais tous les nouveaux flux utilisent
    l'identifiant stable de la ligne.
    """
    cumul_ids, cumul_desc = {}, {}
    bls = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)) \
        .filter_by(societe_id=societe_id, bon_commande_id=bc_id).all()
    for b in bls:
        if (b.statut or "") == "annule":
            continue
        for l in b.lignes:
            qte = l.quantite_livree if l.quantite_livree is not None else l.quantite_prevue
            if l.source_ligne_bc_id:
                cumul_ids[l.source_ligne_bc_id] = cumul_ids.get(l.source_ligne_bc_id, 0) + (qte or 0)
            else:
                cumul_desc[l.description] = cumul_desc.get(l.description, 0) + (qte or 0)
    return cumul_ids, cumul_desc


def reliquat_bon_commande(db, societe_id, bc):
    """Détail du reste à livrer d'un bon de commande, ligne par ligne."""
    deja_ids, deja_desc = _deja_livre_par_ligne(db, societe_id, bc.id)
    lignes, tout_livre = [], True
    for l in bc.lignes:
        commande = l.quantite or 0
        livre = deja_ids.get(l.id, deja_desc.get(l.description, 0))
        reste = round(commande - livre, 4)
        if reste > 0.0001:
            tout_livre = False
        lignes.append({
            "ligne_bc_id": l.id, "article_id": l.article_id,
            "description": l.description, "prix_unitaire": l.prix_unitaire or 0,
            "tva": l.tva or 0, "qualification_tva": getattr(l, "qualification_tva", "taxable") or "taxable", "remise": l.remise or 0,
            "remise2": l.remise2 or 0, "rabais": l.rabais or 0,
            "quantite_commandee": commande, "quantite_livree": round(livre, 4),
            "reliquat": max(reste, 0),
        })
    return lignes, tout_livre


def _mouvement_stock_bon_livre(db, societe_id, bl, statut_avant, user_id=None):
    """Mouvement stock au BL/BR via le moteur unique 06C."""
    if bl.statut != "livre" or statut_avant == "livre":
        return
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    est_achat = bl.type == "achat"
    declencheur = (getattr(societe, "stock_declencheur_achat" if est_achat else "stock_declencheur_vente", None) or "facture")
    if declencheur != ("br" if est_achat else "bl"):
        return
    # Contrôle de rupture pour les sorties (vente)
    if not est_achat:
        erreurs = []
        for l in bl.lignes:
            article = _article_ligne(db, societe_id, l.article_id, l.description)
            qte = l.quantite_livree or l.quantite_prevue or 0
            if article is not None and article.is_stockable and (article.stock_actuel or 0) < qte:
                erreurs.append(f"{l.description} (stock : {article.stock_actuel or 0:g}, à livrer : {qte:g})")
        if erreurs:
            raise HTTPException(400, "Stock insuffisant pour livrer : " + " ; ".join(erreurs))
    prix_bc = {}
    if est_achat and bl.bon_commande_id:
        bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
            .filter_by(id=bl.bon_commande_id, societe_id=societe_id).first()
        if bc:
            prix_bc = {x.id: (x.prix_unitaire or 0) for x in bc.lignes}

    for l in bl.lignes:
        article = _article_ligne(db, societe_id, l.article_id, l.description)
        qte = l.quantite_livree or l.quantite_prevue or 0
        if article is not None and article.is_stockable and qte > 0:
            type_mvt = "entree" if est_achat else "sortie"
            try:
                cout = None
                if est_achat:
                    cout = prix_bc.get(l.source_ligne_bc_id) or l.prix_unitaire or valorisation.cout_entree_par_defaut(article)
                valorisation.enregistrer_mouvement(
                    db,
                    societe_id,
                    article,
                    type_mvt,
                    qte,
                    reference=bl.numero,
                    note=f"{'Réception BR' if est_achat else 'Livraison BL'} {bl.numero} — {bl.tiers}",
                    facture_id=bl.facture_id,
                    cout_unitaire=cout,
                    date_mouvement=bl.date,
                    source_type="bon_reception" if est_achat else "bon_livraison",
                    source_id=bl.id,
                    source_ligne_id=l.id,
                    cle_idempotence=f"bl:{bl.id}:livre:{l.id}",
                    user_id=user_id,
                )
            except ValueError as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail=str(exc))


@router_bl.patch("/{bl_id}", response_model=schemas.BonLivraisonOut)
def modifier_bl(
    bl_id: int,
    data: schemas.BonLivraisonUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    bl = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)) \
        .filter_by(id=bl_id, societe_id=societe_id).first()
    if not bl: raise HTTPException(404, "Bon de livraison introuvable")

    statut_avant = bl.statut
    payload = data.model_dump(exclude_none=True)
    if "statut" in payload:
        _verifier_transition("le bon logistique", statut_avant, payload["statut"], _TRANSITIONS_BL)
    for k, v in payload.items():
        setattr(bl, k, v)

    if bl.statut in {"livre", "retourne"} and bl.statut != statut_avant:
        _verifier_date_operation_ouverte(db, societe_id, bl.date,
            "réception" if bl.type == "achat" else "livraison")

    # Patch 06C : une fois qu'un BL/BR a effectivement mouvementé le stock,
    # on n'autorise pas un retour arrière de statut qui laisserait le ledger
    # orphelin. Le passage livraison -> retour reste autorisé et tracé ci-dessous.
    if statut_avant == "livre" and bl.statut not in {"livre", "retourne"}:
        type_source = "bon_reception" if bl.type == "achat" else "bon_livraison"
        if valorisation.mouvements_actifs_source(db, societe_id, source_type=type_source, source_id=bl.id):
            db.rollback()
            raise HTTPException(409,
                "Ce bon a déjà mouvementé le stock. Impossible de revenir à un statut antérieur ; "
                "utilisez un document correctif/retour.")
    if statut_avant == "retourne" and bl.statut != "retourne":
        if valorisation.mouvements_actifs_source(db, societe_id, source_type="retour_client", source_id=bl.id):
            db.rollback()
            raise HTTPException(409,
                "Ce retour a déjà réintégré le stock. Impossible d'annuler le statut sans document correctif.")

    # ── Mode "stock au BL/BR" : mouvement au passage en statut livré ──────────
    _mouvement_stock_bon_livre(db, societe_id, bl, statut_avant, current_user.get("id"))

    # ── Retour client : remise en stock uniquement si le BL est lui-même le
    # déclencheur du stock. Lorsque le stock est piloté par la facture, le retour
    # physique est traité par l'avoir afin de ne jamais réintégrer une quantité
    # qui n'aurait pas encore été sortie (FACT-A / F-008).
    if bl.type != "achat" and bl.statut == "retourne" and statut_avant != "retourne":
        societe = db.query(models.Societe).filter_by(id=societe_id).first()
        declencheur = (getattr(societe, "stock_declencheur_vente", None) or "facture")
        if declencheur == "bl":
            mouvements_sortie = valorisation.mouvements_actifs_source(
                db, societe_id, source_type="bon_livraison", source_id=bl.id
            )
            if not mouvements_sortie:
                raise HTTPException(409,
                    "Ce bon n'a pas généré de sortie de stock active ; le retour ne peut pas créer une entrée de stock.")
            for l in bl.lignes:
                article = _article_ligne(db, societe_id, l.article_id, l.description)
                if article is not None and (l.quantite_livree or 0) > 0:
                    try:
                        valorisation.enregistrer_mouvement(
                            db,
                            societe_id,
                            article,
                            "entree",
                            l.quantite_livree or 0,
                            reference=bl.numero,
                            note=f"Retour client — BL {bl.numero} — {bl.tiers}",
                            facture_id=bl.facture_id,
                            cout_unitaire=valorisation.cout_sortie(article),
                            date_mouvement=bl.date,
                            source_type="retour_client",
                            source_id=bl.id,
                            source_ligne_id=l.id,
                            cle_idempotence=f"bl:{bl.id}:retour:{l.id}",
                            user_id=current_user.get("id"),
                        )
                    except ValueError as exc:
                        db.rollback()
                        raise HTTPException(status_code=409, detail=str(exc))

    if bl.statut != "en_preparation":
        _figer_document_commercial(db, societe_id, bl)
    db.commit()
    return db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)).filter_by(id=bl_id).first()


@router_bl.delete("/{bl_id}", status_code=204)
def supprimer_bl(
    bl_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    bl = db.query(models.BonLivraison).filter_by(id=bl_id, societe_id=current_user["societe_id"]).first()
    if not bl: raise HTTPException(404, "Bon de livraison introuvable")

    # Un bon qui a déjà eu un effet physique ne se supprime pas : cela détruirait
    # la pièce source du sous-ledger. Il faut conserver la trace et passer par un
    # retour/document correctif.
    sid = current_user["societe_id"]
    sources = ["bon_reception" if bl.type == "achat" else "bon_livraison", "retour_client"]
    if any(valorisation.mouvements_actifs_source(db, sid, source_type=t, source_id=bl.id) for t in sources):
        raise HTTPException(409,
            "Ce bon a déjà mouvementé le stock : suppression impossible. "
            "Utilisez un retour ou un document correctif afin de préserver l'historique.")

    bc_id = bl.bon_commande_id
    # Délier les références avant suppression
    bl.bon_commande_id = None
    bl.facture_id = None
    db.flush()
    db.delete(bl)
    db.flush()

    if bc_id:
        bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)).filter_by(
            id=bc_id, societe_id=sid).first()
        if bc:
            lignes_rel, solde = reliquat_bon_commande(db, sid, bc)
            a_livre = any(x["quantite_livree"] > 0.0001 for x in lignes_rel)
            deja_facture, _ = _deja_facture_par_ligne(db, sid, bc)
            a_facture = any(v > 0.0001 for v in deja_facture.values()) or bool(bc.facture_id)
            if solde:
                bc.statut = "livre"
            elif a_livre:
                bc.statut = "partiel"
            elif a_facture:
                bc.statut = "facture"
            else:
                bc.statut = "en_attente"
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# RÈGLEMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def _verifier_montant_reglement_historique(reglement):
    """Même règle que la saisie ; aucune mutation d'une source non qualifiée."""
    try:
        if reglement.montant is None:
            raise ValueError("Montant manquant")
        schemas._valider_montant_reglement(reglement.montant)
    except (ValueError, TypeError, OverflowError):
        raise HTTPException(422, "Montant historique du règlement à vérifier : aucune opération financière possible.")


def _lecture_reglement(reglement, facture=None):
    valeurs = {nom: getattr(reglement, nom) for nom in schemas.ReglementLectureOut.model_fields
               if hasattr(reglement, nom)}
    try:
        _verifier_montant_reglement_historique(reglement)
    except HTTPException as erreur:
        valeurs.update(montant_valide=False, montant_anomalie=erreur.detail)
    montant = reglement.montant
    if montant is None or not math.isfinite(float(montant)):
        valeurs['montant'] = None
    if facture is not None:
        valeurs.update(facture_type=facture['type'], facture_numero=facture['numero'],
                       facture_exercice=facture['exercice'], facture_statut=facture['statut'],
                       facture_montants_valides=facture['montants_valides'])
    return valeurs


@router_regl.get("", response_model=List[schemas.ReglementLectureOut])
def lister_reglements(
    exercice:   int           = Query(...),
    facture_id: Optional[int] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    from sqlalchemy import extract
    q = db.query(models.Reglement) \
        .filter_by(societe_id=current_user["societe_id"]) \
        .filter(extract('year', models.Reglement.date) == exercice)
    if facture_id: q = q.filter(models.Reglement.facture_id == facture_id)
    reglements = q.order_by(models.Reglement.created_at.desc().nullslast(), models.Reglement.id.desc()).all()
    # L'année du paiement ne détermine pas celle de la pièce réglée. Résoudre
    # uniquement les liens natifs de la société, sans recherche par nom/date.
    ids_factures = {r.facture_id for r in reglements if r.facture_id}
    from routers.factures import _lecture_facture
    factures = db.query(models.Facture).options(
        joinedload(models.Facture.lignes), joinedload(models.Facture.echeances)
    ).filter(models.Facture.societe_id == current_user['societe_id'],
             models.Facture.id.in_(ids_factures)).all() if ids_factures else []
    projections = {f.id: _lecture_facture(db, current_user['societe_id'], f) for f in factures}
    return [_lecture_reglement(r, projections.get(r.facture_id)) for r in reglements]


def _maj_statut_facture(db, societe_id, facture_id):
    """Recalcule le statut de la facture selon les règlements NON rejetés,
    les avoirs actifs et les acomptes imputés, avec les vrais totaux
    (remises, frais transport/emballage, escompte)."""
    # La session est configurée avec autoflush=False : les modifications en attente
    # (ex: statut d'un règlement qui vient de passer à "rejete") doivent être
    # flushées pour que les requêtes ci-dessous les voient.
    db.flush()
    from routers.factures import _calc_totaux
    from sqlalchemy.orm import joinedload as _jl
    facture = db.query(models.Facture).options(_jl(models.Facture.lignes)) \
        .filter_by(id=facture_id, societe_id=societe_id).first()
    if not facture:
        return
    from routers.factures import _situation_paiement_facture
    situation = _situation_paiement_facture(db, societe_id, facture)

    if situation["est_solde"]:
        facture.statut = "payee"
    elif situation["total_effectif"] > 0:
        facture.statut = "partiellement_payee"
    else:
        facture.statut = "en_attente"


def _compte_attente_reglement(reglement, est_vente):
    """Compte où 'vit' le règlement selon son statut courant (cycle chèque/effet)."""
    if reglement.mode == "cheque":
        return "51112" if reglement.statut == "encaissement" else "51111"
    if reglement.mode == "effet":
        return "51132" if reglement.statut == "encaissement" else "3425"
    return None


def _libelle_treso(mode, encaissement, reference=""):
    """Libellé de la ligne de trésorerie, explicite sur la nature du mouvement.

    « Trésorerie » ne renseigne pas le comptable qui relit son journal :
    il veut savoir comment l'argent est entré ou sorti.
    """
    ref = f" {reference}".rstrip() if reference else ""
    if encaissement:
        libelles = {
            "virement": "Virement reçu",
            "especes":  "Encaissement en espèces",
            "cheque":   "Chèque encaissé",
            "effet":    "Effet encaissé",
            "carte":    "Paiement par carte reçu",
            "prelevement": "Prélèvement encaissé",
        }
        defaut = "Encaissement"
    else:
        libelles = {
            "virement": "Virement émis",
            "especes":  "Règlement en espèces",
            "cheque":   "Chèque émis",
            "effet":    "Effet payé",
            "carte":    "Paiement par carte",
            "prelevement": "Prélèvement émis",
        }
        defaut = "Décaissement"
    return (libelles.get(mode, defaut) + ref).strip()


def _ecriture_reception_reglement(db, societe_id, reglement, facture):
    """Écriture à la réception du règlement, selon le mode.

    COMPTA.1 : le compte tiers vient de la facture/fiche tiers et le compte de
    banque vient du compte bancaire sélectionné dans le formulaire.
    """
    est_vente = (facture.type == "vente") if facture else True
    tiers_compte = (
        compte_tiers_facture(db, societe_id, facture)
        if facture else
        compte_tiers(db, societe_id, est_vente=est_vente, nom=reglement.tiers)
    )
    # La référence bancaire/chèque est plus utile comme pièce FEC que le numéro
    # technique du règlement. Un identifiant stable est généré en dernier recours.
    ref = reglement.reference or reglement.numero or f"REG-{reglement.id}"
    if est_vente:
        if reglement.mode == "cheque":
            lignes = [
                models.LigneEcriture(compte="51111", libelle=f"Chèque en portefeuille {reglement.reference or ''}".strip(), debit=reglement.montant, credit=0),
                models.LigneEcriture(compte=tiers_compte, libelle=reglement.tiers, debit=0, credit=reglement.montant),
            ]
            journal, libelle = "AE", f"Réception chèque — {reglement.tiers}"
        elif reglement.mode == "effet":
            lignes = [
                models.LigneEcriture(compte="3425", libelle=f"Effet à recevoir {reglement.reference or ''}".strip(), debit=reglement.montant, credit=0),
                models.LigneEcriture(compte=tiers_compte, libelle=reglement.tiers, debit=0, credit=reglement.montant),
            ]
            journal, libelle = "AE", f"Acceptation effet — {reglement.tiers}"
        else:
            treso = compte_tresorerie(
                db, societe_id, mode=reglement.mode, banque=reglement.banque
            )
            lignes = [
                models.LigneEcriture(compte=treso,
                    libelle=_libelle_treso(reglement.mode, True, reglement.reference),
                    debit=reglement.montant, credit=0),
                models.LigneEcriture(compte=tiers_compte, libelle=reglement.tiers, debit=0, credit=reglement.montant),
            ]
            journal = "CA" if reglement.mode == "especes" else "BQ"
            libelle = _libelle_ecriture(db, societe_id, "banque",
                numero=reglement.numero or "", tiers=reglement.tiers,
                ref=reglement.reference, date_doc=reglement.date)
    else:
        if reglement.mode == "effet":
            lignes = [
                models.LigneEcriture(compte=tiers_compte, libelle=reglement.tiers, debit=reglement.montant, credit=0),
                models.LigneEcriture(compte="4415", libelle=f"Effet à payer {reglement.reference or ''}".strip(), debit=0, credit=reglement.montant),
            ]
            journal, libelle = "AE", f"Effet à payer — {reglement.tiers}"
        else:
            treso = compte_tresorerie(
                db, societe_id, mode=reglement.mode, banque=reglement.banque
            )
            # Lot 977 : une caisse ne peut pas devenir créditrice.
            verifier_sortie_caisse(db, societe_id, treso, reglement.montant, reglement.date,
                                   exclure=getattr(reglement, 'ecriture_id', None))
            lignes = [
                models.LigneEcriture(compte=tiers_compte, libelle=reglement.tiers, debit=reglement.montant, credit=0),
                models.LigneEcriture(compte=treso,
                    libelle=_libelle_treso(reglement.mode, False, reglement.reference),
                    debit=0, credit=reglement.montant),
            ]
            journal = "CA" if reglement.mode == "especes" else "BQ"
            libelle = _libelle_ecriture(db, societe_id, "banque",
                numero=reglement.numero or "", tiers=reglement.tiers,
                ref=reglement.reference, date_doc=reglement.date)

    # COMPTA-AUX : le tiers lié à la facture/règlement devient la source de
    # vérité des comptes auxiliaires, y compris effets clients/fournisseurs.
    rattacher_tiers_aux_lignes(
        db, societe_id, lignes,
        tiers_id=(getattr(reglement, "tiers_id", None) or getattr(facture, "tiers_id", None)),
        nature=("client" if est_vente else "fournisseur"),
    )
    ecriture = models.Ecriture(
        societe_id=societe_id, journal=journal, date=reglement.date,
        date_piece=reglement.date, libelle=libelle, reference=ref,
        exercice=_exercice_ref(db, societe_id, reglement.date), source="reglement", lignes=lignes,
    )
    db.add(ecriture)
    db.flush()
    reglement.ecriture_id = ecriture.id
    reglement.est_comptabilisee = True


def _etat_initial_reglement(mode, est_vente, date_reglement):
    """État et date effective communs à la création et à l'édition initiale."""
    if est_vente and mode in ('cheque', 'effet'):
        return 'portefeuille', None
    if not est_vente and mode == 'effet':
        return 'a_payer', None
    return 'complet', date_reglement


@router_regl.post("", response_model=schemas.ReglementOut, status_code=201)
def creer_reglement(
    data: schemas.ReglementCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    if re.fullmatch(r'VT-[a-f0-9]{32}-\d{2}', (data.numero or '').strip()):
        raise HTTPException(422,
            "Ce format de numéro est réservé aux règlements ventilés. "
            "Utilisez un numéro commercial ou le paiement par client/fournisseur.")
    reglement = _creer_reglement_sans_commit(data, current_user, db)
    db.commit(); db.refresh(reglement)
    return reglement


def _creer_reglement_sans_commit(data, current_user, db):
    """Même flux métier, transaction finalisée uniquement par l'appelant."""
    societe_id = current_user["societe_id"]

    facture = None
    if not data.facture_id:
        raise HTTPException(422,
            "Un règlement doit être rattaché à une facture. Pour un paiement antérieur à la facture, "
            "utilisez Acomptes ; pour une opération de trésorerie hors facture, utilisez le Journal comptable.")
    if data.facture_id:
        # Verrouille la facture pendant le contrôle du solde : un règlement et
        # une imputation d'acompte concurrents ne peuvent pas tous deux consommer
        # le même reliquat (FACT.8).
        facture = db.query(models.Facture).filter_by(
            id=data.facture_id, societe_id=societe_id).with_for_update().first()
        if not facture:
            raise HTTPException(404, "Facture introuvable")
        if getattr(facture, "est_proforma", False):
            raise HTTPException(409, "Une proforma ne peut pas recevoir de règlement.")
        if not getattr(facture, "est_validee", False):
            raise HTTPException(409, "Cette facture est encore en brouillon : validez-la avant d'enregistrer un règlement.")

    est_vente = (facture.type == "vente") if facture else True

    _verifier_date_operation_ouverte(db, societe_id, data.date, "règlement")
    if facture and data.date < facture.date:
        raise HTTPException(409,
            f"La date du règlement ({data.date.strftime('%d/%m/%Y')}) est antérieure à la facture "
            f"{facture.numero} ({facture.date.strftime('%d/%m/%Y')}). "
            "Pour un paiement antérieur à la facturation, utilisez le module Acomptes.")

    if float(data.montant or 0) <= 0:
        raise HTTPException(422, "Le montant du règlement doit être strictement positif.")
    if facture:
        from routers.factures import _situation_paiement_facture
        situation = _situation_paiement_facture(db, societe_id, facture)
        if situation["est_solde"]:
            raise HTTPException(409,
                f"La facture {facture.numero} est déjà soldée : aucun règlement supplémentaire n'est autorisé.")
        if round(float(data.montant), 2) > round(situation["solde_restant"], 2):
            raise HTTPException(409,
                f"Sur-règlement impossible : reste à payer {situation['solde_restant']:.2f} MAD, "
                f"montant saisi {float(data.montant):.2f} MAD.")

    # Statut initial : les chèques et effets clients entrent en portefeuille
    # (ils ne valent encaissement définitif qu'après le cycle remise → encaissé).
    payload = data.model_dump(exclude={"comptabiliser"})
    # Le règlement hérite toujours du tiers natif de sa facture. Cela évite
    # qu'un nom libre divergent ne casse la comptabilité auxiliaire/FEC.
    tiers_reglement = None
    if getattr(facture, "tiers_id", None):
        tiers_reglement = _resoudre_tiers(
            db, societe_id, tiers_id=facture.tiers_id,
            type_attendu=("client" if est_vente else "fournisseur"),
        )
    else:
        # Compatibilité des factures historiques : rapprochement exact et non
        # ambigu uniquement. Aucun tiers n'est deviné à partir d'un texte partiel.
        tiers_reglement = _resoudre_tiers(
            db, societe_id, tiers_id=data.tiers_id, nom=facture.tiers,
            type_attendu=("client" if est_vente else "fournisseur"),
        )
    payload["tiers_id"] = getattr(tiers_reglement, "id", None)
    payload["tiers"] = getattr(facture, "tiers", None) or data.tiers
    # Date fiscale de paiement : les moyens immédiats sont réputés encaissés à
    # la date du règlement. Les chèques/effets CLIENT n'acquièrent une date
    # d'encaissement qu'à la transition « encaisser ». Côté fournisseur, le
    # chèque est actuellement traité comme un paiement direct par le module.
    statut_initial, date_encaissement = _etat_initial_reglement(data.mode, est_vente, data.date)

    reglement = models.Reglement(
        societe_id=societe_id, statut=statut_initial,
        date_encaissement=date_encaissement, **payload
    )
    db.add(reglement)
    db.flush()

    if data.comptabiliser:
        module = db.query(models.ModuleActif).filter_by(
            societe_id=societe_id, module="comptabilite", actif=True).first()
        if module:
            _ecriture_reception_reglement(db, societe_id, reglement, facture)

            # Une estimation documentaire ne constitue pas une retenue operee.

    if data.facture_id:
        _maj_statut_facture(db, societe_id, data.facture_id)

    return reglement


@router_regl.post('/par-tiers', response_model=List[schemas.ReglementOut], status_code=201)
def creer_reglements_par_tiers(
    data: schemas.ReglementParTiersCreate,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    """Ventilation explicite, atomique et rejouable d'un paiement immédiat.

    Aucun regroupement artificiel des anciens règlements : chaque ligne conserve
    son lien facture et son écriture. Chèques/effets restent des instruments
    individuels gérés par leur cycle dédié.
    """
    sid = current_user['societe_id']
    prefixe = 'VT-' + data.operation_id.hex + '-'
    cle = int.from_bytes(hashlib.sha256(f'{sid}:{data.operation_id}'.encode()).digest()[:4], 'big', signed=True)
    db.execute(text('SELECT pg_advisory_xact_lock(726882, :cle)'), {'cle': cle})
    tiers = _resoudre_tiers(db, sid, tiers_id=data.tiers_id)
    ids = sorted(v.facture_id for v in data.ventilations)
    factures = db.query(models.Facture).filter(
        models.Facture.societe_id == sid, models.Facture.id.in_(ids)
    ).order_by(models.Facture.id).with_for_update().all()
    if len(factures) != len(ids):
        raise HTTPException(404, 'Une facture de la ventilation est introuvable pour cette société.')
    sens = factures[0].type
    if any(f.type != sens or f.tiers_id != tiers.id for f in factures):
        raise HTTPException(409, 'Les factures doivent appartenir au même tiers et au même cycle achat/vente.')
    module = db.query(models.ModuleActif).filter_by(societe_id=sid, module='comptabilite', actif=True).first()
    comptabilisee = bool(data.comptabiliser and module)
    lignes = sorted(data.ventilations, key=lambda v: v.facture_id)
    reference = data.reference or prefixe[:-1]
    existants = db.query(models.Reglement).filter(
        models.Reglement.societe_id == sid, models.Reglement.numero.startswith(prefixe)
    ).order_by(models.Reglement.numero).all()
    if existants:
        conforme = len(existants) == len(lignes) and all(
            r.numero == f'{prefixe}{i:02d}' and r.facture_id == v.facture_id
            and r.tiers_id == data.tiers_id and Decimal(str(r.montant)) == Decimal(str(v.montant))
            and r.date == data.date and r.mode == data.mode and r.reference == reference
            and r.banque == data.banque and r.notes == data.notes
            and r.est_comptabilisee == comptabilisee and r.statut == 'complet'
            for i, (r, v) in enumerate(zip(existants, lignes), 1)
        )
        if not conforme:
            raise HTTPException(409, 'Cette opération a déjà été enregistrée avec une ventilation ou un état différent.')
        return existants
    try:
        result = []
        from routers.factures import _situation_paiement_facture
        par_id = {f.id: f for f in factures}
        for i, v in enumerate(lignes, 1):
            situation = _situation_paiement_facture(db, sid, par_id[v.facture_id])
            if Decimal(str(v.montant)) > Decimal(str(situation['solde_restant'])):
                raise HTTPException(409, 'Une ventilation dépasse le solde de sa facture.')
            paiement = schemas.ReglementCreate(
                facture_id=v.facture_id, tiers_id=tiers.id, tiers=tiers.nom,
                numero=f'{prefixe}{i:02d}', date=data.date, montant=v.montant,
                mode=data.mode, reference=reference, banque=data.banque,
                notes=data.notes, comptabiliser=data.comptabiliser,
            )
            result.append(_creer_reglement_sans_commit(paiement, current_user, db))
        db.commit()
        for r in result:
            db.refresh(r)
        return result
    except Exception:
        db.rollback()
        raise


class TransitionIn(BaseModel):
    action: Literal["remettre", "encaisser", "rejeter", "payer"]                    # remettre | encaisser | rejeter | payer
    frais:  Optional[float] = 0.0  # frais bancaires (rejet ou encaissement)
    # Date réelle de remise, rejet, encaissement ou paiement. Si l'UI ne la
    # fournit pas, le backend utilise la date du jour pour compatibilité.
    date_effective: Optional[_date] = None

    @field_validator("frais", mode="before")
    @classmethod
    def frais_valides(cls, v):
        if v is None:
            return 0.0
        if isinstance(v, bool):
            raise ValueError("Les frais bancaires ne peuvent pas être un booléen")
        try:
            n = Decimal(str(v))
            if not n.is_finite() or n < 0:
                raise ValueError("Les frais bancaires doivent être finis et non négatifs")
            if n != n.quantize(Decimal('0.01')) or Decimal(str(float(n))) != n:
                raise ValueError("Les frais bancaires doivent être représentables au centime")
        except (InvalidOperation, TypeError, OverflowError) as exc:
            raise ValueError("Les frais bancaires doivent être représentables au centime") from exc
        return float(n)


@router_regl.post("/{reglement_id}/transition", response_model=schemas.ReglementOut)
def transition_reglement(
    reglement_id: int,
    data: TransitionIn,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Fait avancer un chèque/effet dans son cycle de vie :
    - remettre  : portefeuille → encaissement (remise en banque)
    - encaisser : encaissement → encaisse (avis de crédit reçu)
    - rejeter   : portefeuille|encaissement|encaisse → rejete (impayé : la créance client est ré-ouverte)
    - payer     : a_payer → paye (effet fournisseur réglé à l'échéance)
    """
    societe_id = current_user["societe_id"]
    r = db.query(models.Reglement).filter_by(id=reglement_id, societe_id=societe_id).populate_existing().with_for_update().first()
    if not r:
        raise HTTPException(404, "Règlement introuvable")
    _verifier_montant_reglement_historique(r)

    facture = db.query(models.Facture).filter_by(id=r.facture_id, societe_id=societe_id).first() if r.facture_id else None
    est_vente = (facture.type == "vente") if facture else True
    from datetime import datetime as _dt
    aujourdhui = _dt.now().date()
    frais = Decimal(str(data.frais or 0))
    montant = Decimal(str(r.montant))
    try:
        if montant != montant.quantize(Decimal('0.01')):
            raise InvalidOperation()
    except InvalidOperation as exc:
        raise HTTPException(422, "Le montant historique du règlement n'est pas représentable au centime.") from exc
    if data.action in {'remettre', 'payer'} and frais:
        raise HTTPException(422, "Cette opération ne traite pas de frais. Enregistrez les frais séparément dans le journal.")
    if frais > montant:
        raise HTTPException(422, "Les frais bancaires ne peuvent pas dépasser le montant du règlement.")

    # La date effective est la date réelle de l'opération bancaire.
    # Elle ne doit jamais être future. Les anciennes UI restent compatibles grâce
    # au fallback sur aujourd'hui, mais les nouvelles UI l'envoient explicitement.
    date_effective = data.date_effective or aujourdhui
    if date_effective > aujourdhui:
        raise HTTPException(400, "La date effective de l'opération ne peut pas être future.")
    if r.date and date_effective < r.date:
        raise HTTPException(400, "La date effective de l'opération ne peut pas précéder la réception du règlement.")

    date_operation = date_effective
    _verifier_date_operation_ouverte(db, societe_id, date_operation, "opération de règlement")

    def _ajouter_ecriture(journal, libelle, lignes, date_ecriture=None):
        d = date_ecriture or date_operation
        rattacher_tiers_aux_lignes(
            db, societe_id, lignes,
            tiers_id=(getattr(r, "tiers_id", None) or getattr(facture, "tiers_id", None)),
            nature=("client" if est_vente else "fournisseur"),
        )
        db.add(models.Ecriture(
            societe_id=societe_id, journal=journal, date=d, date_piece=d,
            libelle=libelle, reference=r.reference or r.numero or f"REG-{r.id}",
            exercice=_exercice_ref(db, societe_id, d), source="reglement", lignes=lignes,
        ))

    if data.action == "remettre":
        if not est_vente or r.mode not in ("cheque", "effet") or r.statut != "portefeuille":
            raise HTTPException(400, "Remise impossible : le règlement doit être un chèque/effet client en portefeuille")
        src = "51111" if r.mode == "cheque" else "3425"
        dst = "51112" if r.mode == "cheque" else "51132"
        _ajouter_ecriture("AE", f"Remise à l'encaissement {r.mode} — {r.tiers}", [
            models.LigneEcriture(compte=dst, libelle=f"{'Chèque' if r.mode == 'cheque' else 'Effet'} à l'encaissement", debit=r.montant, credit=0),
            models.LigneEcriture(compte=src, libelle=f"{'Chèque en portefeuille' if r.mode == 'cheque' else 'Effet à recevoir'}", debit=0, credit=r.montant),
        ])
        r.statut = "encaissement"

    elif data.action == "encaisser":
        # Un effet ne peut pas être constaté encaissé avant sa date d'échéance :
        # la banque ne crédite qu'à l'échéance (l'escompte est un autre mécanisme).
        if r.mode == "effet" and r.date_echeance and date_effective < r.date_echeance:
            raise HTTPException(400,
                f"Cet effet arrive à échéance le {r.date_echeance.strftime('%d/%m/%Y')} : "
                "l'encaissement ne peut pas être constaté avant cette date.")
        if not est_vente or r.statut not in ("portefeuille", "encaissement"):
            raise HTTPException(400, "Encaissement impossible : statut incompatible")
        src = _compte_attente_reglement(r, est_vente)
        compte_banque = compte_tresorerie(db, societe_id, mode=r.mode, banque=r.banque)
        lignes = [models.LigneEcriture(compte=compte_banque,
            libelle=_libelle_treso(r.mode, True, r.reference),
            debit=montant - frais, credit=0)]
        if frais > 0:
            lignes.append(models.LigneEcriture(compte="61472", libelle="Frais sur effets de commerce", debit=frais, credit=0))
        lignes.append(models.LigneEcriture(compte=src, libelle="Valeurs à l'encaissement", debit=0, credit=montant))
        _ajouter_ecriture("BQ", f"Encaissement {r.mode} — {r.tiers}", lignes, date_effective)
        r.date_encaissement = date_effective
        r.statut = "encaisse"

    elif data.action == "rejeter":
        apres_encaissement = r.statut == "encaisse"
        if not est_vente or r.mode not in ("cheque", "effet") or r.statut not in ("portefeuille", "encaissement", "encaisse"):
            raise HTTPException(400, "Rejet impossible : statut incompatible")
        if apres_encaissement and (not r.date_encaissement or date_effective < r.date_encaissement):
            raise HTTPException(400, "Le rejet ne peut pas précéder l'encaissement constaté.")
        # Contre-passation : la créance client est ré-ouverte, majorée des frais de rejet refacturés
        compte_client = (
            compte_tiers_facture(db, societe_id, facture) if facture else
            compte_tiers(db, societe_id, est_vente=True, nom=r.tiers)
        )
        lignes = [models.LigneEcriture(compte=compte_client, libelle=f"{r.tiers} — impayé", debit=montant + frais, credit=0)]
        if apres_encaissement:
            # Valeur créditée « sauf bonne fin » puis débitée par la banque avec ses frais.
            compte_banque = compte_tresorerie(db, societe_id, mode=r.mode, banque=r.banque)
            lignes.append(models.LigneEcriture(compte=compte_banque, libelle="Impayé débité par la banque", debit=0, credit=montant + frais))
            if frais > 0:
                lignes.append(models.LigneEcriture(compte="6147", libelle="Frais bancaires sur impayé", debit=frais, credit=0))
        else:
            src = _compte_attente_reglement(r, est_vente)
            lignes.append(models.LigneEcriture(compte=src, libelle="Valeur impayée", debit=0, credit=montant))
        if frais > 0:
            lignes.append(models.LigneEcriture(compte="7127", libelle="Frais de rejet refacturés", debit=0, credit=frais))
        _ajouter_ecriture("BQ" if apres_encaissement else "OD", f"Impayé {r.mode} — {r.tiers}", lignes)
        r.statut = "rejete"
        r.date_rejet_effective = date_effective
        if not apres_encaissement:
            r.date_encaissement = None

    elif data.action == "payer":
        if r.mode == "effet" and r.date_echeance and date_effective < r.date_echeance:
            raise HTTPException(400,
                f"Cet effet arrive à échéance le {r.date_echeance.strftime('%d/%m/%Y')} : "
                "le paiement ne peut pas être constaté avant cette date.")
        if est_vente or r.mode != "effet" or r.statut != "a_payer":
            raise HTTPException(400, "Paiement impossible : le règlement doit être un effet fournisseur à payer")
        _ajouter_ecriture("BQ", f"Paiement effet — {r.tiers}", [
            models.LigneEcriture(compte="4415", libelle="Effet à payer", debit=r.montant, credit=0),
            models.LigneEcriture(compte=compte_tresorerie(db, societe_id, mode=r.mode, banque=r.banque),
                libelle=_libelle_treso(r.mode, False, r.reference),
                debit=0, credit=r.montant),
        ], date_effective)
        r.date_encaissement = date_effective
        r.statut = "paye"

    else:
        raise HTTPException(400, f"Action inconnue : {data.action}")

    # Invariant métier : un règlement définitivement encaissé/payé doit toujours
    # porter sa date effective. Cette garde complète la contrainte PostgreSQL.
    if r.statut in ("encaisse", "paye") and not r.date_encaissement:
        raise HTTPException(500,
            "Incohérence règlement : un statut encaissé/payé exige une date effective.")

    if r.facture_id:
        _maj_statut_facture(db, societe_id, r.facture_id)

    db.commit(); db.refresh(r)
    return r


class AnnulerReglementIn(BaseModel):
    date_annulation: Optional[_date] = None
    motif: Optional[str] = None


@router_regl.post("/{reglement_id}/annuler", response_model=schemas.ReglementOut)
def annuler_reglement(
    reglement_id: int,
    data: AnnulerReglementIn,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    r = _annuler_reglement_sans_commit(reglement_id, data, current_user, db)
    db.commit()
    db.refresh(r)
    return r


@router_regl.get('/par-tiers/{operation_id}', response_model=List[schemas.ReglementLectureOut])
def lire_ventilation(operation_id: UUID, current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    prefixe = 'VT-' + operation_id.hex + '-'
    rows = db.query(models.Reglement).filter(
        models.Reglement.societe_id == current_user['societe_id'],
        models.Reglement.numero.startswith(prefixe),
    ).order_by(models.Reglement.numero).all()
    if not rows:
        raise HTTPException(404, 'Ventilation introuvable pour cette société.')
    return [_lecture_reglement(r) for r in rows]


@router_regl.post('/par-tiers/{operation_id}/annuler', response_model=List[schemas.ReglementOut])
def annuler_ventilation(
    operation_id: UUID,
    data: AnnulerReglementIn,
    current_user=Depends(requiert_ecriture),
    db: Session=Depends(get_db),
):
    """Contrepasser un lot natif entier ; aucune déduction depuis une référence libre."""
    sid = current_user['societe_id']
    prefixe = 'VT-' + operation_id.hex + '-'
    cle = int.from_bytes(hashlib.sha256(f'{sid}:{operation_id}'.encode()).digest()[:4], 'big', signed=True)
    try:
        db.execute(text('SELECT pg_advisory_xact_lock(726882, :cle)'), {'cle': cle})
        rows = db.query(models.Reglement).filter(
            models.Reglement.societe_id == sid,
            models.Reglement.numero.startswith(prefixe),
        ).order_by(models.Reglement.numero).with_for_update().all()
        if not rows:
            raise HTTPException(404, 'Ventilation introuvable pour cette société.')
        if len(rows) > 50 or any(r.numero != f'{prefixe}{i:02d}' for i, r in enumerate(rows, 1)):
            raise HTTPException(409, 'Numérotation du lot incomplète ou incohérente : annulation collective bloquée.')
        ids = sorted(r.facture_id for r in rows if r.facture_id is not None)
        factures = db.query(models.Facture).filter(
            models.Facture.societe_id == sid, models.Facture.id.in_(ids),
        ).order_by(models.Facture.id).with_for_update().all()
        if len(set(ids)) != len(rows) or len(factures) != len(rows):
            raise HTTPException(409, 'Liens facture du lot incomplets ou ambigus.')
        tiers = rows[0].tiers_id
        if tiers is None or any(r.tiers_id != tiers or r.mode not in {'virement', 'especes', 'carte', 'prelevement', 'autre'} for r in rows):
            raise HTTPException(409, 'Cette ventilation ne peut pas être annulée collectivement.')
        if any(f.tiers_id != tiers or f.type != factures[0].type for f in factures):
            raise HTTPException(409, 'Les factures du lot doivent relever du même tiers et du même cycle.')
        for r in rows:
            _verifier_montant_reglement_historique(r)
        if all(r.statut == 'annule' for r in rows):
            db.commit()
            return rows
        if any(r.statut != 'complet' for r in rows):
            raise HTTPException(409, 'Lot partiellement annulé ou cycle engagé : vérifier chaque règlement individuellement.')
        result = [_annuler_reglement_sans_commit(r.id, data, current_user, db) for r in rows]
        db.commit()
        for r in result:
            db.refresh(r)
        return result
    except Exception:
        db.rollback()
        raise


def _annuler_reglement_sans_commit(reglement_id, data, current_user, db):
    """Annule un règlement erroné par contrepassation, sans effacer l'historique.

    Les règlements dont le cycle bancaire est déjà engagé/dénoué utilisent leurs
    transitions dédiées. L'annulation administrative couvre les règlements
    immédiats, chèques/effets encore en portefeuille et effets fournisseur à payer.
    """
    societe_id = current_user["societe_id"]
    r = db.query(models.Reglement).filter_by(id=reglement_id, societe_id=societe_id).populate_existing().with_for_update().first()
    if not r:
        raise HTTPException(404, "Règlement introuvable")
    _verifier_montant_reglement_historique(r)
    if r.statut == "annule":
        return r
    if r.statut in {"encaissement", "encaisse", "paye", "rejete"}:
        raise HTTPException(409,
            "Ce règlement a déjà engagé son cycle bancaire. Utilisez l'action métier correspondante "
            "(encaissement/rejet/paiement) ou une OD comptable si une régularisation exceptionnelle est nécessaire.")
    if r.statut not in {"complet", "portefeuille", "a_payer"}:
        raise HTTPException(409, f"Annulation impossible depuis le statut {r.statut}.")

    jour = data.date_annulation or _date.today()
    _verifier_date_operation_ouverte(db, societe_id, jour, "annulation de règlement")

    # Résoudre la RAS historique avant toute écriture ou changement d'état.
    # La dernière annulation ne peut effacer un flag sans OD certaine.
    ras_orig = None
    if r.facture_id:
        facture_ras = db.query(models.Facture).filter_by(
            id=r.facture_id, societe_id=societe_id).with_for_update().first()
        if facture_ras and getattr(facture_ras, 'ras_comptabilisee', False):
            autres_ras = db.query(models.Reglement).filter(
                models.Reglement.societe_id == societe_id,
                models.Reglement.facture_id == facture_ras.id,
                models.Reglement.id != r.id,
                models.Reglement.statut.notin_(['rejete', 'annule']),
            ).count()
            if autres_ras == 0:
                from routers.factures import _situation_paiement_facture
                from services.ras_paiement_service import resoudre_od_ras_historique
                situation_ras = _situation_paiement_facture(db, societe_id, facture_ras)
                ras_orig = resoudre_od_ras_historique(
                    db, societe_id, facture_ras, situation_ras['montant_ras_impute'])
                if ras_orig is None:
                    raise HTTPException(409,
                        'OD de RAS historique absente, ambiguë, incohérente ou déjà contrepassée : '
                        "annulation bloquée pour préserver la piste d'audit.")

    original = None
    from sqlalchemy.exc import DBAPIError
    try:
        if getattr(r, "ecriture_id", None):
            original = db.query(models.Ecriture).filter_by(
                id=r.ecriture_id, societe_id=societe_id
            ).populate_existing().with_for_update(nowait=True).first()
            if original is None and r.est_comptabilisee:
                raise HTTPException(409,
                    "Lien vers l'écriture d'origine incohérent : annulation automatique bloquée.")
        elif r.est_comptabilisee:
            ref = r.reference or r.numero or f"REG-{r.id}"
            candidats = db.query(models.Ecriture).filter(
                models.Ecriture.societe_id == societe_id,
                models.Ecriture.source == "reglement",
                models.Ecriture.reference == ref,
                models.Ecriture.date == r.date,
            ).order_by(models.Ecriture.id.asc()).populate_existing().with_for_update(nowait=True).all()
            if len(candidats) == 1:
                original = candidats[0]
                r.ecriture_id = original.id
            elif len(candidats) > 1:
                raise HTTPException(409,
                    "Plusieurs écritures historiques correspondent à ce règlement : annulation automatique ambiguë. "
                    "Passez une OD de régularisation.")
    except DBAPIError as exc:
        if getattr(exc.orig, 'pgcode', None) == '55P03':
            # Le Journal verrouille la pièce avant de libérer son document.
            # Ne pas attendre ici en détenant déjà le verrou du règlement.
            raise HTTPException(409,
                "L'écriture d'origine est en cours de modification. Réessayez après la fin de l'opération.") from exc
        raise

    if r.est_comptabilisee:
        if not original:
            raise HTTPException(409,
                "Écriture comptable d'origine introuvable : l'annulation automatique est bloquée pour préserver la piste d'audit.")
        if original.source != "reglement" or original.date != r.date or original.contrepassation_de_id:
            raise HTTPException(409,
                "Origine ou date de l'écriture incompatible avec ce règlement : annulation automatique bloquée.")
        autre_reglement = db.query(models.Reglement.id).filter(
            models.Reglement.societe_id == societe_id,
            models.Reglement.ecriture_id == original.id,
            models.Reglement.id != r.id,
        ).first()
        if autre_reglement:
            raise HTTPException(409,
                "L'écriture d'origine est liée à un autre règlement : annulation automatique ambiguë.")
        debit = sum((Decimal(str(l.debit or 0)) for l in original.lignes), Decimal(0))
        credit = sum((Decimal(str(l.credit or 0)) for l in original.lignes), Decimal(0))
        if not debit.is_finite() or not credit.is_finite() or debit != credit or debit != Decimal(str(r.montant)):
            raise HTTPException(409,
                "Les montants de l'écriture d'origine ne correspondent pas au règlement : vérification nécessaire.")
        if db.query(models.Ecriture.id).filter_by(
            societe_id=societe_id, contrepassation_de_id=original.id
        ).first():
            raise HTTPException(409,
                "L'écriture d'origine est déjà contrepassée : vérifiez le règlement avant son annulation.")
        inverse = models.Ecriture(
            societe_id=societe_id, journal=original.journal, date=jour, date_piece=jour,
            libelle=f"Annulation règlement {r.numero or r.reference or r.id} — {r.tiers}",
            reference=(f"ANN-{r.reference or r.numero or r.id}")[:100], exercice=_exercice_ref(db, societe_id, jour),
            source="reglement", contrepassation_de_id=original.id,
            motif_correction=(data.motif or "Annulation d'un règlement erroné")[:500],
            lignes=[models.LigneEcriture(
                compte=l.compte, libelle=f"Annulation {l.libelle or ''}".strip(),
                debit=l.credit, credit=l.debit,
                tiers_id=getattr(l, "tiers_id", None),
                nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
            ) for l in original.lignes],
        )
        db.add(inverse)
        db.flush()
        r.ecriture_annulation_id = inverse.id

    from services.ras_reglement_service import annuler_capture
    if r.facture_id:
        db.query(models.Facture).filter_by(id=r.facture_id, societe_id=societe_id).with_for_update().first()
    r.statut = 'annule'
    db.flush()
    annuler_capture(db, societe_id, r, jour, current_user['id'],
        (data.motif or 'Annulation du règlement associé à la capture RAS')[:500], _exercice_ref(db, societe_id, jour))
    r.statut = "annule"
    r.date_annulation = __import__("datetime").datetime.now()
    r.date_annulation_effective = jour
    r.annulee_par = current_user.get("id")
    r.date_encaissement = None
    if r.facture_id:
        facture = db.query(models.Facture).filter_by(id=r.facture_id, societe_id=societe_id).first()
        # Si ce règlement était le seul paiement ayant déclenché la RAS,
        # l'annulation doit également remettre cette constatation à zéro.
        if facture and getattr(facture, "ras_comptabilisee", False):
            autres = db.query(models.Reglement).filter(
                models.Reglement.societe_id == societe_id,
                models.Reglement.facture_id == facture.id,
                models.Reglement.id != r.id,
                models.Reglement.statut.notin_(["rejete", "annule"]),
            ).count()
            if autres == 0:
                if ras_orig is not None:
                    db.add(models.Ecriture(
                        societe_id=societe_id, journal=ras_orig.journal, date=jour, date_piece=jour,
                        libelle=f"Annulation RAS — {facture.numero}",
                        reference=(f"ANN-RAS-{facture.numero}")[:100], exercice=_exercice_ref(db, societe_id, jour),
                        source="reglement", contrepassation_de_id=ras_orig.id,
                        motif_correction="Annulation du règlement ayant déclenché la RAS",
                        lignes=[models.LigneEcriture(
                            compte=l.compte, libelle=f"Annulation {l.libelle or 'RAS'}",
                            debit=l.credit, credit=l.debit,
                            tiers_id=getattr(l, "tiers_id", None),
                            nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                            compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                            libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
                        ) for l in ras_orig.lignes],
                    ))
                facture.ras_comptabilisee = False
        _maj_statut_facture(db, societe_id, r.facture_id)
    return r


@router_regl.patch("/{reglement_id}", response_model=schemas.ReglementOut)
def modifier_reglement(
    reglement_id: int,
    data: schemas.ReglementUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Modifie un règlement encore non comptabilisé.

    Une fois comptabilisé, seules les notes restent éditables ; les données financières
    doivent être corrigées par annulation/contrepassation afin de préserver l'historique.
    """
    from datetime import datetime as _dt
    from routers.cloture import exercice_est_clos
    societe_id = current_user["societe_id"]
    r = db.query(models.Reglement).filter_by(id=reglement_id, societe_id=societe_id).populate_existing().with_for_update().first()
    if not r:
        raise HTTPException(404, "Règlement introuvable")
    _verifier_montant_reglement_historique(r)

    impactants = {
        "date": data.date, "montant": data.montant, "mode": data.mode,
        "reference": data.reference, "banque": data.banque,
        "date_echeance": data.date_echeance,
    }
    if r.statut == "annule" and any(v is not None for v in impactants.values()):
        raise HTTPException(409,
            "Ce règlement est annulé : ses données financières sont définitivement figées. "
            "Les notes restent modifiables.")

    if getattr(r, "est_comptabilisee", False):
        if any(v is not None for v in impactants.values()):
            raise HTTPException(409,
                "Ce règlement est déjà comptabilisé : ses données financières sont figées. "
                "Une correction doit passer par une annulation/contrepassation afin de préserver l'historique. "
                "Les notes restent modifiables.")

    if r.statut in {'encaissement', 'encaisse', 'paye', 'rejete'} and any(v is not None for v in impactants.values()):
        raise HTTPException(409,
            "Ce règlement a déjà engagé son cycle bancaire : ses données financières sont figées. "
            "Utilisez l'action métier correspondante. Les notes restent modifiables.")

    def _vers_date(v):
        if not v:
            return None
        if isinstance(v, str):
            try:
                return _dt.strptime(v[:10], "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(422, "Date invalide : format attendu AAAA-MM-JJ.")
        return v

    if data.date is not None:
        d = _vers_date(data.date)
        if d:
            ex_ref = _exercice_ref(db, societe_id, d)
            if exercice_est_clos(db, societe_id, ex_ref):
                raise HTTPException(423,
                    f"Exercice {ex_ref} clôturé : impossible d'y déplacer ce règlement.")
            r.date = d
    if data.montant is not None:
        if float(data.montant or 0) <= 0:
            raise HTTPException(422, "Le montant du règlement doit être strictement positif.")
        if r.facture_id and r.statut not in ("rejete", "annule"):
            facture = db.query(models.Facture).filter_by(
                id=r.facture_id, societe_id=societe_id).first()
            if facture:
                from routers.factures import _situation_paiement_facture
                situation = _situation_paiement_facture(
                    db, societe_id, facture, exclure_reglement_id=r.id
                )
                if round(float(data.montant), 2) > round(situation["solde_restant"], 2):
                    raise HTTPException(409,
                        f"Sur-règlement impossible : reste disponible {situation['solde_restant']:.2f} MAD, "
                        f"montant saisi {float(data.montant):.2f} MAD.")
        r.montant = data.montant
    if data.mode      is not None: r.mode      = data.mode
    if data.reference is not None: r.reference = data.reference
    if data.banque    is not None: r.banque    = data.banque
    if data.notes     is not None: r.notes     = data.notes
    # L'échéance est validée AVANT d'être écrite : un contrôle qui échoue après
    # l'affectation laisserait l'objet en mémoire dans un état incohérent.
    nouvelle_echeance = _vers_date(data.date_echeance) if data.date_echeance is not None else r.date_echeance
    if (r.mode or "") == "effet" and not nouvelle_echeance:
        raise HTTPException(400, "Une date d'échéance est obligatoire pour un effet de commerce.")
    if data.date_echeance is not None:
        r.date_echeance = nouvelle_echeance

    if any(v is not None for v in impactants.values()) and r.statut in {'complet', 'portefeuille', 'a_payer'}:
        facture_source = db.query(models.Facture).filter_by(
            id=r.facture_id, societe_id=societe_id).first()
        if facture_source is None:
            raise HTTPException(409, "Facture source introuvable : état du règlement non déterminable.")
        r.statut, r.date_encaissement = _etat_initial_reglement(
            r.mode, facture_source.type == 'vente', r.date)

    db.flush()
    # Le solde de la facture dépend du montant réglé
    if r.facture_id:
        _maj_statut_facture(db, societe_id, r.facture_id)
    db.commit(); db.refresh(r)
    return r


@router_regl.delete("/{reglement_id}", status_code=204)
def supprimer_reglement(
    reglement_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    r = db.query(models.Reglement).filter_by(id=reglement_id, societe_id=current_user["societe_id"]).populate_existing().with_for_update().first()
    if not r: raise HTTPException(404, "Règlement introuvable")
    _verifier_montant_reglement_historique(r)
    if getattr(r, "est_comptabilisee", False):
        raise HTTPException(409,
            "Ce règlement est comptabilisé et ne peut plus être supprimé. "
            "Utilisez une annulation/contrepassation pour conserver une piste d'audit complète.")

    facture_id = r.facture_id
    db.delete(r)
    db.flush()

    # Recalculer le statut de la facture après suppression (calcul unifié)
    if facture_id:
        _maj_statut_facture(db, current_user["societe_id"], facture_id)

    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# BON DE RÉCEPTION (achat) — utilise la même table bons_livraison, type='achat'
# ═══════════════════════════════════════════════════════════════════════════════

router_br = APIRouter(prefix="/api/bons-reception", tags=["commercial"])


@router_br.get("", response_model=List[schemas.BonLivraisonOut])
def lister_br(
    exercice:  int           = Query(...),
    statut:    Optional[str] = Query(None),
    current_user = Depends(get_current_user),
    db: Session  = Depends(get_db),
):
    q = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)) \
        .filter_by(societe_id=current_user["societe_id"], type="achat") \
        .filter(models.BonLivraison.exercice == exercice)
    if statut: q = q.filter(models.BonLivraison.statut == statut)
    return q.order_by(models.BonLivraison.created_at.desc().nullslast(), models.BonLivraison.id.desc()).all()


@router_br.post("", response_model=schemas.BonLivraisonOut, status_code=201)
def creer_br(
    data: schemas.BonLivraisonCreate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    if data.type != "achat":
        raise HTTPException(422, "Un bon de réception doit être de type achat.")
    _verifier_lignes_tva(data.date, data.lignes)
    bc_source = _bc_societe(db, societe_id, data.bon_commande_id) if data.bon_commande_id else None
    facture_source = _facture_societe(db, societe_id, data.facture_id) if data.facture_id else None
    if bc_source and bc_source.type != "achat":
        raise HTTPException(422, "Le bon de commande source n'est pas un achat.")
    if facture_source and _valeur_enum(facture_source.type) != "achat":
        raise HTTPException(422, "La facture source n'est pas une facture d'achat.")
    _verifier_lignes_source_bc(db, societe_id, data.lignes, data.bon_commande_id)
    tiers_obj = _resoudre_tiers(db, societe_id, data.tiers_id, data.tiers, "fournisseur")
    numero = (data.numero or "").strip()
    if numero:
        existant = db.query(models.BonLivraison).filter_by(societe_id=societe_id, numero=numero).first()
        if existant:
            raise HTTPException(409, f"Numéro de bon '{numero}' déjà utilisé")
    else:
        numero = reserver_numero_commercial(db, societe_id, _exercice_ref(db, societe_id, data.date), "br", "BR")
    payload = data.model_dump(exclude={"lignes", "type", "tiers_id"})
    payload["numero"] = numero
    payload["tiers"] = tiers_obj.nom if tiers_obj else data.tiers
    br = models.BonLivraison(
        societe_id=societe_id, tiers_id=(tiers_obj.id if tiers_obj else None),
        type="achat", **payload
    )
    br.exercice = _exercice_ref(db, societe_id, data.date)
    db.add(br); db.flush()
    for l in data.lignes:
        db.add(models.LigneBonLivraison(bon_livraison_id=br.id, **l.model_dump()))
    db.commit(); db.refresh(br)
    return db.query(models.BonLivraison).options(
        joinedload(models.BonLivraison.lignes)
    ).filter_by(id=br.id).first()


@router_br.patch("/{br_id}", response_model=schemas.BonLivraisonOut)
def modifier_br(
    br_id: int,
    data: schemas.BonLivraisonUpdate,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    br = db.query(models.BonLivraison).filter_by(
        id=br_id, societe_id=current_user["societe_id"], type="achat"
    ).first()
    if not br: raise HTTPException(404, "Bon de réception introuvable")
    statut_avant = br.statut
    payload = data.model_dump(exclude_none=True)
    if "statut" in payload:
        _verifier_transition("le bon de réception", statut_avant, payload["statut"], _TRANSITIONS_BL)
    for k, v in payload.items():
        setattr(br, k, v)

    if br.statut in {"livre", "retourne"} and br.statut != statut_avant:
        _verifier_date_operation_ouverte(db, current_user["societe_id"], br.date, "réception")

    _mouvement_stock_bon_livre(db, current_user["societe_id"], br, statut_avant, current_user.get("id"))
    if br.statut != "en_preparation":
        _figer_document_commercial(db, current_user["societe_id"], br)
    db.commit()
    return db.query(models.BonLivraison).options(
        joinedload(models.BonLivraison.lignes)
    ).filter_by(id=br_id).first()


@router_br.delete("/{br_id}", status_code=204)
def supprimer_br(
    br_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    br = db.query(models.BonLivraison).filter_by(
        id=br_id, societe_id=current_user["societe_id"], type="achat"
    ).first()
    if not br: raise HTTPException(404, "Bon de réception introuvable")

    sid = current_user["societe_id"]
    if valorisation.mouvements_actifs_source(db, sid, source_type="bon_reception", source_id=br.id):
        raise HTTPException(409,
            "Ce bon de réception a déjà mouvementé le stock : suppression impossible. "
            "Utilisez un document correctif afin de préserver l'historique.")

    # Délier les références avant suppression
    br.bon_commande_id = None
    br.facture_id = None
    db.flush()

    db.delete(br); db.commit()


# ═══ Génération PDF (devis + bon de livraison) ════════════════════════════════

@router_devis.get("/{devis_id}/pdf")
def generer_pdf_devis(
    devis_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PDF FACT.9 du devis : identité légale, détail TVA et conditions de validité."""
    from fastapi.responses import Response
    from datetime import timedelta
    from pdf_generator import generer_document
    from services.document_pdf_service import tiers_infos, societe_pour_document, resume_tva_depuis_lignes, mentions_tva_depuis_lignes

    devis = db.query(models.Devis).options(joinedload(models.Devis.lignes)) \
        .filter_by(id=devis_id, societe_id=current_user["societe_id"]).first()
    if not devis:
        raise HTTPException(404, "Devis introuvable")
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()

    lignes_pdf, total_ht, total_tva = [], 0.0, 0.0
    for l in devis.lignes:
        ht = _net_ht_ligne(l); taux = _taux_effectif_ligne(l)
        total_ht += ht; total_tva += ht * (taux / 100)
        lignes_pdf.append({
            "description": l.description, "quantite": l.quantite, "prix_unitaire": l.prix_unitaire,
            "remise": getattr(l, "remise", 0) or 0, "remise2": getattr(l, "remise2", 0) or 0,
            "rabais": getattr(l, "rabais", 0) or 0, "tva": getattr(l, "tva", 0) or 0,
            "qualification_tva": getattr(l, "qualification_tva", "taxable") or "taxable", "total_ht": ht,
        })
    total_ttc = total_ht + total_tva
    validite = devis.validite_jours or 30
    expiration = devis.date + timedelta(days=validite) if devis.date else None
    meta = [("Validité", f"{validite} jours" + (f" - jusqu'au {expiration:%d/%m/%Y}" if expiration else ""))]
    if devis.reference: meta.append(("Référence", devis.reference))
    pdf_bytes = generer_document(
        societe_pour_document(societe, devis), titre="DEVIS", numero=devis.numero, date_doc=devis.date,
        tiers=devis.tiers, tiers_infos=tiers_infos(db, models, current_user["societe_id"], devis), label_tiers="CLIENT",
        meta=meta, lignes=lignes_pdf, colonnes="prix",
        totaux=[("Total HT", total_ht, False), ("Total TVA", total_tva, False), ("TOTAL TTC", total_ttc, True)],
        resume_tva=resume_tva_depuis_lignes(lignes_pdf), mention_lettres=total_ttc,
        mentions=mentions_tva_depuis_lignes(lignes_pdf), notes=(devis.notes_snapshot if getattr(devis, "societe_snapshot_json", None) else devis.notes),
        conditions=f"Offre valable {validite} jours à compter de la date du devis.", statut=(devis.statut or "").upper(),
    )
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="devis_{devis.numero}.pdf"'})


@router_bc.get("/{bc_id}/pdf")
def generer_pdf_bc(
    bc_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PDF FACT.9 d'un bon de commande client ou fournisseur."""
    from fastapi.responses import Response
    from pdf_generator import generer_document
    from services.document_pdf_service import tiers_infos, societe_pour_document, resume_tva_depuis_lignes, mentions_tva_depuis_lignes

    bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
        .filter_by(id=bc_id, societe_id=current_user["societe_id"]).first()
    if not bc:
        raise HTTPException(404, "Bon de commande introuvable")
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    est_vente = bc.type != "achat"
    lignes_pdf, total_ht, total_tva = [], 0.0, 0.0
    for l in bc.lignes:
        ht = _net_ht_ligne(l); taux = _taux_effectif_ligne(l)
        total_ht += ht; total_tva += ht * (taux / 100)
        lignes_pdf.append({
            "description": l.description, "quantite": l.quantite, "prix_unitaire": l.prix_unitaire,
            "remise": l.remise or 0, "remise2": l.remise2 or 0, "rabais": l.rabais or 0,
            "tva": l.tva or 0, "qualification_tva": l.qualification_tva or "taxable", "total_ht": ht,
        })
    meta = []
    if bc.reference: meta.append(("Référence", bc.reference))
    if bc.date_livraison: meta.append(("Livraison souhaitée", bc.date_livraison.strftime("%d/%m/%Y")))
    if bc.devis_id:
        dnum = db.query(models.Devis.numero).filter_by(id=bc.devis_id, societe_id=current_user["societe_id"]).scalar()
        if dnum: meta.append(("Devis d'origine", dnum))
    total_ttc = total_ht + total_tva
    titre = "BON DE COMMANDE CLIENT" if est_vente else "BON DE COMMANDE FOURNISSEUR"
    pdf_bytes = generer_document(
        societe_pour_document(societe, bc), titre=titre, numero=bc.numero, date_doc=bc.date, tiers=bc.tiers,
        tiers_infos=tiers_infos(db, models, current_user["societe_id"], bc),
        label_tiers="CLIENT" if est_vente else "FOURNISSEUR", meta=meta,
        lignes=lignes_pdf, colonnes="prix",
        totaux=[("Total HT", total_ht, False), ("Total TVA", total_tva, False), ("TOTAL TTC", total_ttc, True)],
        resume_tva=resume_tva_depuis_lignes(lignes_pdf), mention_lettres=total_ttc,
        mentions=mentions_tva_depuis_lignes(lignes_pdf), notes=(bc.notes_snapshot if getattr(bc, "societe_snapshot_json", None) else bc.notes), statut=(bc.statut or "").upper(),
        signature_labels=("Bon pour accord", "Signature / cachet") if est_vente else ("Émis par", "Validation fournisseur"),
    )
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="bc_{bc.numero}.pdf"'})


def _generer_pdf_bl_br_document(bl, societe, db, societe_id: int, *, exemplaires: int = 2):
    from pdf_generator import generer_document
    from services.document_pdf_service import tiers_infos, societe_pour_document

    est_vente = bl.type != "achat"
    lignes_pdf = [{
        "description": l.description,
        "quantite_prevue": l.quantite_prevue or 0,
        "quantite_livree": l.quantite_livree or 0,
    } for l in bl.lignes]
    meta = []
    if bl.transporteur: meta.append(("Transporteur", bl.transporteur))
    if bl.facture_id:
        fact = db.query(models.Facture.numero).filter_by(id=bl.facture_id, societe_id=societe_id).scalar()
        if fact: meta.append(("Facture", fact))
    if bl.bon_commande_id:
        bc = db.query(models.BonCommande.numero).filter_by(id=bl.bon_commande_id, societe_id=societe_id).scalar()
        if bc: meta.append(("Bon de commande", bc))
    nb = max(1, min(int(exemplaires or 1), 2))
    if est_vente:
        ex = ["EXEMPLAIRE CLIENT", "EXEMPLAIRE ARCHIVE"][:nb]
        titre = "BON DE LIVRAISON"; labels=("Qté commandée", "Qté livrée")
        signatures=("Livré par", "Reçu par - nom, signature et cachet")
        label_tiers="CLIENT"
    else:
        ex = ["EXEMPLAIRE RÉCEPTION", "EXEMPLAIRE ARCHIVE"][:nb]
        titre = "BON DE RÉCEPTION"; labels=("Qté commandée", "Qté reçue")
        signatures=("Réceptionné par", "Livreur / fournisseur")
        label_tiers="FOURNISSEUR"
    return generer_document(
        societe_pour_document(societe, bl), titre=titre, numero=bl.numero, date_doc=bl.date, tiers=bl.tiers,
        tiers_infos=tiers_infos(db, models, societe_id, bl), label_tiers=label_tiers,
        meta=meta, lignes=lignes_pdf, colonnes="livraison", notes=(bl.notes_snapshot if getattr(bl, "societe_snapshot_json", None) else bl.notes), exemplaires=ex,
        libelles_livraison=labels, signature_labels=signatures, statut=(bl.statut or "").upper(),
    )


@router_bl.get("/{bl_id}/pdf")
def generer_pdf_bl(
    bl_id: int,
    exemplaires: int = 2,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response
    bl = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)).filter_by(
        id=bl_id, societe_id=current_user["societe_id"], type="vente"
    ).first()
    if not bl: raise HTTPException(404, "Bon de livraison introuvable")
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    pdf_bytes = _generer_pdf_bl_br_document(bl, societe, db, current_user["societe_id"], exemplaires=exemplaires)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="bl_{bl.numero}.pdf"'})


@router_br.get("/{br_id}/pdf")
def generer_pdf_br(
    br_id: int,
    exemplaires: int = 2,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response
    br = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)).filter_by(
        id=br_id, societe_id=current_user["societe_id"], type="achat"
    ).first()
    if not br: raise HTTPException(404, "Bon de réception introuvable")
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()
    pdf_bytes = _generer_pdf_bl_br_document(br, societe, db, current_user["societe_id"], exemplaires=exemplaires)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="br_{br.numero}.pdf"'})


@router_bl.get("/{bl_id}/reliquat-facturation")
def consulter_reliquat_facturation_bl(
    bl_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reste à facturer d'un BL/BR, ligne par ligne."""
    societe_id = current_user["societe_id"]
    bl = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)) \
        .filter_by(id=bl_id, societe_id=societe_id).first()
    if not bl:
        raise HTTPException(404, "Bon de livraison introuvable")
    situation = _situation_facturation_bl(db, societe_id, bl)
    return {
        "bon": bl.numero,
        "type": bl.type,
        **situation,
    }


@router_bl.post("/{bl_id}/convertir-facture", response_model=schemas.FactureOut)
def convertir_bl_en_facture(
    bl_id: int,
    data: schemas.ConvertirBLFactureIn = schemas.ConvertirBLFactureIn(),
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Facture tout ou partie d'un bon de livraison/réception.

    FACT.3 : un même BL/BR peut alimenter plusieurs factures. Les quantités
    déjà facturées sont calculées via ``source_ligne_bl_id`` et ne peuvent
    jamais dépasser les quantités réellement livrées/réceptionnées.
    """
    societe_id = current_user["societe_id"]
    bl = db.query(models.BonLivraison).options(joinedload(models.BonLivraison.lignes)) \
        .filter_by(id=bl_id, societe_id=societe_id).first()
    if not bl:
        raise HTTPException(404, "Bon de livraison introuvable")

    date_facture = data.date or _date.today()
    exercice_facture = _verifier_date_operation_ouverte(db, societe_id, date_facture, "facture")
    est_achat = bl.type == "achat"
    doc = "bon de réception" if est_achat else "bon de livraison"

    # Une facturation directe du BC couvre déjà toute la commande : facturer
    # ensuite ses BL/BR provoquerait un doublon.
    if bl.bon_commande_id:
        bc = db.query(models.BonCommande).filter_by(id=bl.bon_commande_id, societe_id=societe_id).first()
        if bc and bc.facture_id:
            f = db.query(models.Facture).filter_by(id=bc.facture_id, societe_id=societe_id).first()
            if _facture_active(f):
                raise HTTPException(409,
                    f"Le bon de commande {bc.numero} a déjà été facturé directement"
                    + (f" (facture {f.numero})" if f else "")
                    + f" : facturer aussi ce {doc} créerait un doublon.")

    if not bl.lignes:
        raise HTTPException(400, f"Ce {doc} ne comporte aucune ligne à facturer.")

    situation_avant = _situation_facturation_bl(db, societe_id, bl)
    if situation_avant["solde"]:
        nums = ", ".join(situation_avant.get("facture_numeros") or [])
        raise HTTPException(409,
            f"Ce {doc} est déjà entièrement facturé" + (f" ({nums})." if nums else "."))

    # Quantités demandées ; sans sélection, on facture tout le reliquat.
    demande = {}
    if data.lignes:
        for x in data.lignes:
            if x.quantite < 0:
                raise HTTPException(422, "Une quantité à facturer ne peut pas être négative.")
            demande[x.ligne_bl_id] = demande.get(x.ligne_bl_id, 0.0) + float(x.quantite or 0)

    lignes_par_id = {l.id: l for l in bl.lignes}
    qtes_a_facturer = {}
    for info in situation_avant["lignes"]:
        ligne_id = info["ligne_bl_id"]
        reste = float(info["reste_a_facturer"] or 0)
        qte = demande.get(ligne_id, 0.0) if data.lignes else reste
        if qte > reste + 0.0001:
            raise HTTPException(409,
                f"{info['description']} : quantité à facturer {qte:g} supérieure au reliquat {reste:g}.")
        if qte > 0.0001:
            qtes_a_facturer[ligne_id] = qte

    if data.lignes:
        inconnues = set(demande) - set(lignes_par_id)
        if inconnues:
            raise HTTPException(422, "Une ligne sélectionnée n'appartient pas à ce bon.")
    if not qtes_a_facturer:
        raise HTTPException(400, "Aucune quantité à facturer : le reliquat sélectionné est nul.")

    # FACT.4 : la conversion BL/BR crée un brouillon sans consommer de numéro.
    societe = db.query(models.Societe).filter_by(id=societe_id).first()
    numero_f = None

    tiers_obj = _resoudre_tiers(
        db, societe_id, bl.tiers_id, bl.tiers, "fournisseur" if est_achat else "client"
    )
    facture = models.Facture(
        societe_id=societe_id, numero=numero_f, type=("achat" if est_achat else "vente"),
        date=date_facture, exercice=exercice_facture.annee,
        tiers=(tiers_obj.nom if tiers_obj else bl.tiers),
        tiers_id=(tiers_obj.id if tiers_obj else bl.tiers_id),
        tiers_ice_snapshot=(tiers_obj.ice if tiers_obj else None),
        tiers_if_snapshot=(tiers_obj.identifiant_fiscal if tiers_obj else None),
        tiers_rc_snapshot=(tiers_obj.rc if tiers_obj else None),
        tiers_adresse_snapshot=(tiers_obj.adresse if tiers_obj else None),
        tiers_ville_snapshot=(tiers_obj.ville if tiers_obj else None),
        tiers_telephone_snapshot=(tiers_obj.telephone if tiers_obj else None),
        tiers_email_snapshot=(tiers_obj.email if tiers_obj else None),
        tiers_categorie_snapshot=(getattr(tiers_obj, "categorie_fiscale", None) if tiers_obj else None),
        reference=(None if est_achat else bl.numero), statut="en_attente",
        delai_paiement=_delai_paiement_tiers(tiers_obj),
        date_echeance=date_facture + timedelta(days=_delai_paiement_tiers(tiers_obj)), est_validee=False,
        regime_tva=(getattr(societe, "regime_tva", None) or "encaissement"),
    )
    db.add(facture); db.flush()

    # Remontée aux conditions du BC pour les anciens BL/BR incomplets.
    bc_src = None
    bc_lignes_par_id = {}
    bc_lignes_par_desc = {}
    if bl.bon_commande_id:
        bc_src = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
            .filter_by(id=bl.bon_commande_id, societe_id=societe_id).first()
        if bc_src:
            bc_lignes_par_id = {x.id: x for x in bc_src.lignes}
            for x in bc_src.lignes:
                bc_lignes_par_desc.setdefault(x.description, []).append(x)

    def _conditions(ligne_bl):
        src = bc_lignes_par_id.get(ligne_bl.source_ligne_bc_id)
        if src is None:
            candidats = bc_lignes_par_desc.get(ligne_bl.description, [])
            src = candidats[0] if len(candidats) == 1 else None
        article = _article_ligne(db, societe_id, ligne_bl.article_id, ligne_bl.description)
        pu = float(ligne_bl.prix_unitaire or 0)
        tva = float(ligne_bl.tva if ligne_bl.tva is not None else 20)
        remise = float(ligne_bl.remise or 0); remise2 = float(ligne_bl.remise2 or 0); rabais = float(ligne_bl.rabais or 0)
        if src:
            if pu == 0: pu = float(src.prix_unitaire or 0)
            tva = float(src.tva if src.tva is not None else tva)
            remise = float(src.remise or 0); remise2 = float(src.remise2 or 0); rabais = float(src.rabais or 0)
            article = article or _article_ligne(db, societe_id, src.article_id, src.description)
        try:
            if pu == 0 and article:
                prix_source = article.prix_achat_ht if est_achat else article.prix_vente_ht
                schemas._nombre_fini(prix_source)
                pu = float(prix_source)
            schemas._nombre_fini(pu)
        except ValueError as exc:
            db.rollback()
            raise HTTPException(409,
                f"Prix historique absent ou non fini pour {ligne_bl.description} : "
                "vérifiez le bon et sa source avant facturation.") from exc
        return src, article, pu, tva, remise, remise2, rabais

    declencheur = (getattr(societe,
        "stock_declencheur_achat" if est_achat else "stock_declencheur_vente", None) or "facture")
    # Le stock à la facture sera appliqué à la validation du brouillon, jamais
    # lors de sa simple création.
    stock_a_la_facture = False

    total_ht = total_tva = 0.0
    for ligne_id, qte in qtes_a_facturer.items():
        l = lignes_par_id[ligne_id]
        src_bc, art, pu, tva, remise, remise2, rabais = _conditions(l)
        ligne_facture = models.LigneFacture(
            facture_id=facture.id, article_id=(art.id if art else l.article_id),
            source_ligne_devis_id=(src_bc.source_ligne_devis_id if src_bc else None),
            source_ligne_bc_id=(src_bc.id if src_bc else l.source_ligne_bc_id),
            source_ligne_bl_id=l.id, description=l.description,
            quantite=qte, prix_unitaire=pu, tva=tva, qualification_tva=getattr(l, "qualification_tva", "taxable") or "taxable",
            remise=remise, remise2=remise2, rabais=rabais,
        )
        db.add(ligne_facture); db.flush()
        ht = _net_ht_ligne(ligne_facture)
        total_ht += ht
        total_tva += ht * (_taux_effectif_ligne(ligne_facture) / 100)

        if stock_a_la_facture and art is not None and art.is_stockable:
            try:
                valorisation.enregistrer_mouvement(
                    db, societe_id, art,
                    "entree" if est_achat else "sortie", qte,
                    reference=facture.numero,
                    note=f"{'Achat' if est_achat else 'Vente'} — {bl.tiers} (depuis {bl.numero})",
                    facture_id=facture.id,
                    cout_unitaire=(pu if est_achat else None),
                    date_mouvement=facture.date,
                    source_type="facture", source_id=facture.id,
                    source_ligne_id=ligne_facture.id,
                    cle_idempotence=f"facture:{facture.id}:ligne:{ligne_facture.id}",
                    user_id=current_user.get("id"),
                )
            except ValueError as exc:
                db.rollback()
                raise HTTPException(status_code=409, detail=str(exc))

    # ``facture_id`` reste un lien legacy vers la première facture uniquement.
    # L'état réel multi-factures est dérivé des lignes source_ligne_bl_id.
    if not bl.facture_id:
        bl.facture_id = facture.id
    db.flush()

    if bl.bon_commande_id:
        bc = db.query(models.BonCommande).options(joinedload(models.BonCommande.lignes)) \
            .filter_by(id=bl.bon_commande_id, societe_id=societe_id).first()
        if bc:
            cycle = _situation_cycle_bc(db, societe_id, bc)
            if cycle["statut_cycle"] in {"termine", "facture"}:
                bc.statut = "facture"
            elif cycle["statut_cycle"] == "partiel":
                bc.statut = "partiel"

    if not all(math.isfinite(m) for m in (total_ht, total_tva, total_ht + total_tva)):
        db.rollback()
        raise HTTPException(409, "Les montants issus de ce bon dépassent la précision autorisée : vérifiez les sources avant facturation.")
    db.commit(); db.refresh(facture)
    return {
        **facture.__dict__,
        "total_ht": total_ht, "total_tva": total_tva, "total_ttc": total_ht + total_tva,
        "lignes": [{
            **l.__dict__,
            "montant_ht": l.quantite * l.prix_unitaire,
            "montant_tva": l.quantite * l.prix_unitaire * (_taux_effectif_ligne(l) / 100),
            "montant_ttc": l.quantite * l.prix_unitaire * (1 + _taux_effectif_ligne(l) / 100),
        } for l in facture.lignes]
    }


@router_regl.post("/{reglement_id}/comptabiliser")
def comptabiliser_reglement(
    reglement_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session  = Depends(get_db),
):
    """Génère (ou régénère) l'écriture comptable d'un règlement.

    Utile lorsque le règlement a été saisi sans comptabilisation, ou que son
    écriture a été supprimée depuis le journal.
    """
    societe_id = current_user["societe_id"]
    reglement = db.query(models.Reglement).filter_by(
        id=reglement_id, societe_id=societe_id).populate_existing().with_for_update().first()
    if not reglement:
        raise HTTPException(404, "Règlement introuvable")
    _verifier_montant_reglement_historique(reglement)

    if getattr(reglement, "est_comptabilisee", False):
        raise HTTPException(400, "Ce règlement est déjà comptabilisé.")

    if reglement.statut == "annule":
        raise HTTPException(409, "Ce règlement est annulé : il ne peut plus être comptabilisé.")

    from routers.cloture import exercice_est_clos
    ex_ref = _exercice_ref(db, societe_id, reglement.date)
    if exercice_est_clos(db, societe_id, ex_ref):
        raise HTTPException(423,
            f"Exercice {ex_ref} clôturé : impossible de comptabiliser ce règlement.")

    module = db.query(models.ModuleActif).filter_by(
        societe_id=societe_id, module="comptabilite", actif=True).first()
    if not module:
        raise HTTPException(400, "Module Comptabilité inactif.")

    facture = None
    if reglement.facture_id:
        facture = db.query(models.Facture).filter_by(
            id=reglement.facture_id, societe_id=societe_id).first()

    _ecriture_reception_reglement(db, societe_id, reglement, facture)
    reglement.est_comptabilisee = True
    db.commit()
    return {"message": f"Écriture générée pour le règlement {reglement.numero or reglement.id}."}
