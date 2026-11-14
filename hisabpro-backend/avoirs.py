from datetime import date as date_type, datetime
from math import isfinite
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel

from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from routers.factures import _libelle_ecriture, schemas
from services.commercial_numero_service import reserver_numero_commercial
from services.tva_service import D, ZERO, money, total_ventilation, ventilation_avoir
from services.compta_mapping_service import (
    compte_tiers_facture, groupes_avoir_par_compte, repartir_par_poids, compte_tresorerie,
    est_compte_immobilisation,
)
from services.auxiliaire_service import rattacher_tiers_aux_lignes

router = APIRouter(prefix="/api/avoirs", tags=["avoirs"])


class UtiliserAvoirIn(BaseModel):
    type_utilisation: Literal["imputation", "remboursement"]
    montant: float
    date_utilisation: date_type
    date_acceptation_compensation: Optional[date_type] = None
    facture_id: Optional[int] = None
    mode: Optional[Literal["virement", "cheque", "especes", "effet", "carte", "prelevement", "autre"]] = None
    compte_bancaire_id: Optional[int] = None
    banque: Optional[str] = None
    reference: Optional[str] = None


def _type_value(value):
    return getattr(value, "value", value)


def _totaux_avoir(avoir):
    """Totaux FACT.6 : base commerciale avant escompte, TVA/TTC après escompte."""
    avant = total_ventilation(ventilation_avoir(avoir, appliquer_escompte=False))
    apres = total_ventilation(ventilation_avoir(avoir, appliquer_escompte=True))
    return float(avant["base"]), float(apres["tva"]), float(apres["ttc"])


def _totaux_ligne(avoir, ligne):
    class _AvoirLigne:
        pass
    tmp = _AvoirLigne()
    tmp.lignes = [ligne]
    tmp.remise_globale_snapshot = getattr(avoir, "remise_globale_snapshot", 0) or 0
    tmp.ristourne_snapshot = getattr(avoir, "ristourne_snapshot", 0) or 0
    tmp.escompte_snapshot = getattr(avoir, "escompte_snapshot", 0) or 0
    avant = total_ventilation(ventilation_avoir(tmp, appliquer_escompte=False))
    apres = total_ventilation(ventilation_avoir(tmp, appliquer_escompte=True))
    return float(avant["base"]), float(apres["tva"]), float(apres["ttc"])


def _base_finale_source(facture, source, quantite=None, nouveau_prix_unitaire=None):
    """Base HT finale d'une fraction de ligne, après toutes les réductions source."""
    q = D(getattr(source, "quantite", 0) if quantite is None else quantite)
    pu = D(getattr(source, "prix_unitaire", 0) if nouveau_prix_unitaire is None else nouveau_prix_unitaire)
    r1 = D(getattr(source, "remise", 0)) / D(100)
    r2 = D(getattr(source, "remise2", 0)) / D(100)
    rabais = D(getattr(source, "rabais", 0))
    net = q * pu * (D(1) - r1) * (D(1) - r2) - rabais * q
    net = max(net, ZERO)
    net *= (D(1) - D(getattr(facture, "remise_globale", 0)) / D(100))
    net *= (D(1) - D(getattr(facture, "ristourne", 0)) / D(100))
    net *= (D(1) - D(getattr(facture, "escompte", 0)) / D(100))
    return money(max(net, ZERO))


def _base_finale_correction_prix(facture, source, quantite, nouveau_prix):
    """Montant HT à créditer quand seul le prix unitaire baisse."""
    ancien = D(getattr(source, "prix_unitaire", 0))
    nouveau = D(nouveau_prix)
    q = D(quantite)
    delta = max(ancien - nouveau, ZERO) * q
    delta *= (D(1) - D(getattr(source, "remise", 0)) / D(100))
    delta *= (D(1) - D(getattr(source, "remise2", 0)) / D(100))
    delta *= (D(1) - D(getattr(facture, "remise_globale", 0)) / D(100))
    delta *= (D(1) - D(getattr(facture, "ristourne", 0)) / D(100))
    delta *= (D(1) - D(getattr(facture, "escompte", 0)) / D(100))
    return money(max(delta, ZERO))


def _base_finale_ligne_avoir(avoir, ligne):
    class _Tmp:
        pass
    tmp = _Tmp()
    tmp.lignes = [ligne]
    tmp.remise_globale_snapshot = getattr(avoir, "remise_globale_snapshot", 0) or 0
    tmp.ristourne_snapshot = getattr(avoir, "ristourne_snapshot", 0) or 0
    tmp.escompte_snapshot = getattr(avoir, "escompte_snapshot", 0) or 0
    return D(total_ventilation(ventilation_avoir(tmp, appliquer_escompte=True))["base"])


def _montants_deja_credites(db, facture, societe_id: int):
    result = {l.id: ZERO for l in facture.lignes}
    avoirs = (
        db.query(models.Avoir).options(joinedload(models.Avoir.lignes))
        .filter_by(facture_id=facture.id, societe_id=societe_id)
        .filter(models.Avoir.statut != "annule").all()
    )
    for av in avoirs:
        for ligne in av.lignes:
            source_id = getattr(ligne, "facture_ligne_id", None)
            if source_id in result:
                result[source_id] += _base_finale_ligne_avoir(av, ligne)
    return result


def _credit_excedentaire_avoir(db, avoir):
    """Crédit réellement libre après absorption par la facture source et usages."""
    facture = db.query(models.Facture).options(joinedload(models.Facture.lignes)).filter_by(
        id=avoir.facture_id, societe_id=avoir.societe_id
    ).first()
    if not facture or _type_value(avoir.statut) == "annule":
        return 0.0, 0.0, 0.0

    from routers.factures import _calc_totaux, _montant_ras
    total_ht, _, total_ttc, _, _ = _calc_totaux(facture)
    # Un crédit n'est transférable/remboursable que si le règlement à l'origine
    # d'un éventuel trop-perçu est réellement encaissé/payé. Un chèque/effet
    # encore en portefeuille ne doit jamais permettre un remboursement anticipé.
    reglements = db.query(models.Reglement).filter(
        models.Reglement.societe_id == avoir.societe_id,
        models.Reglement.facture_id == facture.id,
        models.Reglement.statut.notin_(["rejete", "annule"]),
    ).all()
    total_regle = sum(
        float(r.montant or 0) for r in reglements
        if r.date_encaissement is not None or r.statut in {"complet", "encaisse", "paye"}
    )
    total_acomptes = float(db.query(func.coalesce(func.sum(models.ImputationAcompte.montant), 0)).filter(
        models.ImputationAcompte.societe_id == avoir.societe_id,
        models.ImputationAcompte.facture_id == facture.id,
        models.ImputationAcompte.statut == "active",
    ).scalar() or 0)
    from services.ras_paiement_service import lecture_ras_paiement
    from services.ras_reglement_service import montant_actif
    montant_ras = lecture_ras_paiement(_montant_ras(facture, total_ht), getattr(facture, 'ras_comptabilisee', False), montant_actif(db, avoir.societe_id, facture.id))['montant_ras_impute']
    if montant_ras is None:
        raise HTTPException(409,'Capture RAS incohérente : crédit disponible indéterminable')
    restant = max(float(total_ttc) - total_regle - total_acomptes - montant_ras, 0.0)

    credit_libre = 0.0
    actifs = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter(
        models.Avoir.societe_id == avoir.societe_id,
        models.Avoir.facture_id == facture.id,
        models.Avoir.statut != "annule",
    ).order_by(models.Avoir.date, models.Avoir.id).all()
    for av in actifs:
        montant = float(_totaux_avoir(av)[2])
        absorbe = min(restant, montant)
        libre = max(montant - absorbe, 0.0)
        restant = max(restant - absorbe, 0.0)
        if av.id == avoir.id:
            credit_libre = libre
            break

    usages = db.query(models.UtilisationAvoir).filter_by(
        societe_id=avoir.societe_id, avoir_id=avoir.id, statut="active"
    ).all()
    montant_utilise = sum(float(x.montant or 0) for x in usages)
    disponible = max(credit_libre - montant_utilise, 0.0)
    return round(credit_libre, 2), round(montant_utilise, 2), round(disponible, 2)


def _fmt_utilisations(db, avoir):
    rows = db.query(models.UtilisationAvoir).filter_by(
        societe_id=avoir.societe_id, avoir_id=avoir.id
    ).order_by(models.UtilisationAvoir.date_utilisation, models.UtilisationAvoir.id).all()
    out = []
    for row in rows:
        numero = None
        if row.facture_id:
            numero = db.query(models.Facture.numero).filter_by(
                id=row.facture_id, societe_id=avoir.societe_id
            ).scalar()
        out.append({
            "id": row.id, "type_utilisation": row.type_utilisation,
            "facture_id": row.facture_id, "facture_numero": numero,
            "date_utilisation": row.date_utilisation, "montant": float(row.montant or 0),
            "date_acceptation_compensation": row.date_acceptation_compensation,
            "date_annulation_effective": row.date_annulation_effective,
            "mode": row.mode, "banque": row.banque, "reference": row.reference,
            "statut": row.statut, "est_comptabilisee": bool(row.ecriture_id),
        })
    return out


def _fmt_avoir(a, db=None):
    ht, tva, ttc = _totaux_avoir(a)
    facture_num = None
    facture_tiers_id = None
    credit_excedentaire = montant_utilise = montant_disponible = 0.0
    utilisations = []
    if db is not None:
        f = db.query(models.Facture).filter_by(id=a.facture_id, societe_id=a.societe_id).first()
        facture_num = f.numero if f else None
        facture_tiers_id = f.tiers_id if f else None
        credit_excedentaire, montant_utilise, montant_disponible = _credit_excedentaire_avoir(db, a)
        utilisations = _fmt_utilisations(db, a)
    lignes = []
    for l in a.lignes:
        lht, ltva, lttc = _totaux_ligne(a, l)
        lignes.append({
            **l.__dict__,
            "montant_ht_avoir": float(getattr(l, "montant_ht_force", 0) or 0) or None,
            "montant_ht": lht, "montant_tva": ltva, "montant_ttc": lttc,
        })
    return {
        **a.__dict__, "facture_numero": facture_num, "tiers_id": facture_tiers_id,
        "credit_excedentaire": credit_excedentaire, "montant_utilise": montant_utilise,
        "montant_disponible": montant_disponible, "utilisations": utilisations,
        "total_ht": ht, "total_tva": tva, "total_ttc": ttc, "lignes": lignes,
    }


def _maj_statut_avoir_credit(db, avoir):
    if _type_value(avoir.statut) == "annule":
        return
    _, _, disponible = _credit_excedentaire_avoir(db, avoir)
    usages = db.query(models.UtilisationAvoir).filter_by(
        societe_id=avoir.societe_id, avoir_id=avoir.id, statut="active"
    ).all()
    if disponible > 0.01 or not usages:
        avoir.statut = "emis"
    elif usages and all(x.type_utilisation == "remboursement" for x in usages):
        avoir.statut = "rembourse"
    else:
        avoir.statut = "utilise"


def _verifier_date_avoir(db, societe_id: int, jour: date_type, facture):
    """Valide la date réelle de l'avoir et retourne son exercice comptable.

    FACT-C : un avoir de N peut parfaitement corriger en N+1 une facture de N.
    On interdit seulement l'antidatage avant la facture source et toute période
    fermée/clôturée ; le document correctif appartient à l'exercice de sa date.
    """
    if jour < facture.date:
        raise HTTPException(422, "La date de l'avoir ne peut pas précéder la facture d'origine.")
    try:
        from services.exercices_service import verifier_date_ecriture
        return verifier_date_ecriture(db, societe_id, jour, action="enregistrer")
    except ValueError as exc:
        msg = str(exc)
        status = 423 if "clôtur" in msg.lower() or "fermé" in msg.lower() else 409
        raise HTTPException(status, msg) from exc


def _resoudre_ligne_facture(facture, ligne_in):
    """Résout la ligne source de façon non ambiguë.

    FACT.6 privilégie l'identifiant technique. Le fallback par description n'est
    conservé que pour les anciens clients API et est refusé dès qu'il est ambigu.
    """
    if getattr(ligne_in, "facture_ligne_id", None):
        ligne = next((l for l in facture.lignes if l.id == ligne_in.facture_ligne_id), None)
        if not ligne:
            raise HTTPException(400, "Une ligne sélectionnée n'appartient pas à cette facture.")
        return ligne

    description = (getattr(ligne_in, "description", None) or "").strip()
    candidats = [l for l in facture.lignes if (l.description or "").strip() == description]
    if not candidats:
        raise HTTPException(400, f"Ligne de facture introuvable : « {description} ».")
    if len(candidats) > 1:
        raise HTTPException(
            409,
            f"Plusieurs lignes de la facture portent « {description} ». "
            "Rechargez la facture afin d'utiliser l'identifiant de ligne FACT.6.",
        )
    return candidats[0]


def _quantites_deja_creditees(db, facture, societe_id: int):
    """Quantités actives déjà créditées, indexées par ligne de facture."""
    result = {l.id: 0.0 for l in facture.lignes}
    descriptions = {}
    for l in facture.lignes:
        descriptions.setdefault((l.description or "").strip(), []).append(l.id)

    avoirs = (
        db.query(models.Avoir)
        .options(joinedload(models.Avoir.lignes))
        .filter_by(facture_id=facture.id, societe_id=societe_id)
        .filter(models.Avoir.statut != "annule")
        .all()
    )
    for av in avoirs:
        for l in av.lignes:
            # Les RRR/corrections de prix ne consomment pas une quantité physique.
            if getattr(l, "mode_calcul", "quantite") != "quantite":
                continue
            source_id = getattr(l, "facture_ligne_id", None)
            if source_id in result:
                result[source_id] += float(l.quantite or 0)
                continue
            # Compatibilité des avoirs créés avant FACT.6 : on ne rattache une
            # description legacy que si elle identifie une seule ligne source.
            ids = descriptions.get((l.description or "").strip(), [])
            if len(ids) == 1:
                result[ids[0]] += float(l.quantite or 0)
    return result


def _appliquer_retour_stock(db, societe_id: int, avoir, facture, user_id=None):
    if not getattr(avoir, "retour_stock", False):
        return
    from services.stock_movement_service import enregistrer_mouvement

    est_vente = _type_value(avoir.type) == "vente"
    for l in avoir.lignes:
        if not getattr(l, "article_id", None):
            continue
        article = db.query(models.Article).filter_by(
            id=l.article_id, societe_id=societe_id
        ).first()
        if not article or not getattr(article, "is_stockable", False):
            continue

        cout_unitaire = None
        if est_vente:
            original = (
                db.query(models.MouvementStock)
                .filter_by(
                    societe_id=societe_id,
                    source_type="facture",
                    source_id=facture.id,
                    source_ligne_id=getattr(l, "facture_ligne_id", None),
                )
                .order_by(models.MouvementStock.id.desc())
                .first()
            )
            if original is not None:
                cout_unitaire = float(original.cout_unitaire or 0)

        try:
            enregistrer_mouvement(
                db,
                societe_id,
                article,
                "entree" if est_vente else "sortie",
                float(l.quantite or 0),
                reference=avoir.numero,
                note=("Retour client" if est_vente else "Retour fournisseur") + f" — {avoir.tiers}",
                facture_id=None,
                cout_unitaire=cout_unitaire,
                date_mouvement=avoir.date,
                source_type="avoir",
                source_id=avoir.id,
                source_ligne_id=l.id,
                cle_idempotence=f"avoir:{avoir.id}:ligne:{l.id}",
                user_id=user_id,
            )
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc


def _statut_credit_facture(db, facture, societe_id: int):
    _, _, total_facture, _, _ = __import__("routers.factures", fromlist=["_calc_totaux"])._calc_totaux(facture)
    avoirs = (
        db.query(models.Avoir)
        .options(joinedload(models.Avoir.lignes))
        .filter_by(facture_id=facture.id, societe_id=societe_id)
        .filter(models.Avoir.statut != "annule")
        .all()
    )
    total_avoirs = sum(_totaux_avoir(a)[2] for a in avoirs)
    if total_avoirs <= 0.01:
        statut = "aucun"
    elif total_avoirs >= float(total_facture) - 0.01:
        statut = "totalement_creditee"
    else:
        statut = "partiellement_creditee"
    return total_avoirs, statut


@router.get("", response_model=List[schemas.AvoirOut])
def lister_avoirs(
    exercice: int = Query(...),
    facture_id: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Avoir)
        .options(joinedload(models.Avoir.lignes))
        .filter_by(societe_id=current_user["societe_id"])
        .filter(models.Avoir.exercice == exercice)
    )
    if facture_id:
        q = q.filter(models.Avoir.facture_id == facture_id)
    return [_fmt_avoir(a, db) for a in q.order_by(models.Avoir.date.desc()).all()]


@router.get("/{avoir_id}/pdf")
def generer_pdf_avoir(
    avoir_id: int,
    current_user=Depends(get_current_user),
    db: Session=Depends(get_db),
):
    """PDF FACT.9 d'un avoir, avec facture d'origine et traitement TVA détaillé."""
    from fastapi.responses import Response
    from pdf_generator import generer_document
    from services.document_pdf_service import (
        tiers_infos, societe_pour_document, resume_tva_depuis_ventilation, mentions_tva_depuis_lignes,
    )

    avoir = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter_by(
        id=avoir_id, societe_id=current_user["societe_id"]
    ).first()
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    facture = db.query(models.Facture).options(joinedload(models.Facture.lignes)).filter_by(
        id=avoir.facture_id, societe_id=current_user["societe_id"]
    ).first()
    societe = db.query(models.Societe).filter_by(id=current_user["societe_id"]).first()

    lignes_pdf = []
    sous_total = 0.0
    for l in avoir.lignes:
        net_ligne = float(getattr(l, "montant_ht", 0) or 0)
        sous_total += net_ligne
        lignes_pdf.append({
            "description": l.description, "quantite": l.quantite, "prix_unitaire": l.prix_unitaire,
            "remise": l.remise or 0, "remise2": l.remise2 or 0, "rabais": l.rabais or 0,
            "tva": l.tva or 0, "qualification_tva": l.qualification_tva or "taxable",
            "total_ht": net_ligne,
        })

    avant = total_ventilation(ventilation_avoir(avoir, appliquer_escompte=False))
    apres_vent = ventilation_avoir(avoir, appliquer_escompte=True)
    apres = total_ventilation(apres_vent)
    remise_g = float(getattr(avoir, "remise_globale_snapshot", 0) or 0)
    ristourne = float(getattr(avoir, "ristourne_snapshot", 0) or 0)
    escompte = float(getattr(avoir, "escompte_snapshot", 0) or 0)
    montant_rg = sous_total * remise_g / 100
    base_rg = sous_total - montant_rg
    montant_rist = base_rg * ristourne / 100
    totaux = [("Sous-total lignes", sous_total, False)]
    if remise_g: totaux.append((f"Remise globale d'origine ({remise_g:g}%)", -montant_rg, False))
    if ristourne: totaux.append((f"Ristourne d'origine ({ristourne:g}%)", -montant_rist, False))
    totaux.append(("Net commercial HT", float(avant["base"]), False))
    if escompte:
        totaux.append((f"Escompte d'origine ({escompte:g}%)", -(float(avant["base"]) - float(apres["base"])), False))
        totaux.append(("Net HT après escompte", float(apres["base"]), False))
    totaux += [("Total TVA", float(apres["tva"]), False), ("TOTAL TTC AVOIR", float(apres["ttc"]), True)]

    meta = []
    if facture and facture.numero: meta.append(("Facture d'origine", facture.numero))
    if avoir.motif: meta.append(("Motif", avoir.motif))
    nature = (getattr(avoir, "nature_avoir", None) or "retour_annulation").replace("_", " ")
    meta.append(("Nature", nature.capitalize()))
    if getattr(avoir, "retour_stock", False): meta.append(("Retour physique", "Oui"))
    mentions = mentions_tva_depuis_lignes(lignes_pdf)
    if getattr(avoir, "statut", None):
        statut = _type_value(avoir.statut).upper()
    else:
        statut = None
    pdf_bytes = generer_document(
        societe_pour_document(societe, avoir),
        titre="AVOIR CLIENT" if _type_value(avoir.type) == "vente" else "AVOIR FOURNISSEUR",
        numero=avoir.numero, date_doc=avoir.date, tiers=avoir.tiers,
        tiers_infos=tiers_infos(db, models, current_user["societe_id"], avoir, facture_source=facture),
        label_tiers="CLIENT" if _type_value(avoir.type) == "vente" else "FOURNISSEUR",
        meta=meta, lignes=lignes_pdf, colonnes="prix", totaux=totaux,
        resume_tva=resume_tva_depuis_ventilation(apres_vent),
        mention_lettres=float(apres["ttc"]), mentions=mentions,
        notes=(getattr(avoir, "notes_snapshot", None) if getattr(avoir, "notes_snapshot", None) is not None else avoir.notes),
        statut=statut,
    )
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="avoir_{avoir.numero}.pdf"'})


@router.post("", response_model=schemas.AvoirOut, status_code=201)
def creer_avoir(
    data: schemas.AvoirCreate,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]

    # Verrouiller la facture sérialise deux créations concurrentes d'avoirs et
    # empêche de dépasser le reliquat par double clic / deux utilisateurs.
    facture = (
        db.query(models.Facture)
        .filter_by(id=data.facture_id, societe_id=societe_id)
        .with_for_update()
        .first()
    )
    if not facture:
        raise HTTPException(404, "Facture introuvable")
    _ = facture.lignes
    if getattr(facture, "est_proforma", False):
        raise HTTPException(409, "Une proforma ne peut pas faire l'objet d'un avoir.")
    if not getattr(facture, "est_validee", False):
        raise HTTPException(409, "Cette facture est encore en brouillon : validez-la avant de créer un avoir.")
    if not data.lignes:
        raise HTTPException(400, "L'avoir doit contenir au moins une ligne")
    nature_avoir = (getattr(data, "nature_avoir", None) or "retour_annulation").lower()
    if nature_avoir not in {"retour_annulation", "rrr", "correction_prix", "autre"}:
        raise HTTPException(422, "Nature d'avoir invalide.")
    if nature_avoir != "retour_annulation" and data.retour_stock:
        raise HTTPException(422, "Seul un retour/annulation physique peut déclencher un mouvement de stock.")

    exercice_avoir = _verifier_date_avoir(db, societe_id, data.date, facture)
    deja_quantites = _quantites_deja_creditees(db, facture, societe_id)
    deja_montants = _montants_deja_credites(db, facture, societe_id)

    sources = []
    ids_vus = set()
    for ligne_in in data.lignes:
        source = _resoudre_ligne_facture(facture, ligne_in)
        if source.id in ids_vus:
            raise HTTPException(400, "Une même ligne de facture ne peut apparaître deux fois dans le même avoir.")
        ids_vus.add(source.id)

        qte = float(ligne_in.quantite or 0)
        if not isfinite(qte) or qte <= 0:
            raise HTTPException(400, "La quantité concernée doit être strictement positive.")
        if qte > float(source.quantite or 0) + 0.000001:
            raise HTTPException(409, f"Quantité supérieure à la quantité facturée pour « {source.description} ».")

        mode_calcul = "quantite"
        montant_force = None
        taux_rrr = None
        nouveau_prix = None

        if nature_avoir == "retour_annulation":
            dispo_qte = max(0.0, float(source.quantite or 0) - deja_quantites.get(source.id, 0.0))
            if qte > dispo_qte + 0.000001:
                raise HTTPException(409,
                    f"Quantité d'avoir ({qte:g}) supérieure au reliquat ({dispo_qte:g}) pour « {source.description} ».")
            nouveau_credit = _base_finale_source(facture, source, qte)
        elif nature_avoir == "rrr":
            mode_recu = (getattr(ligne_in, "mode_calcul", None) or "rrr_pourcentage").lower()
            if mode_recu == "rrr_pourcentage":
                taux_rrr = float(getattr(ligne_in, "taux_rrr", 0) or 0)
                if not isfinite(taux_rrr) or taux_rrr <= 0 or taux_rrr > 100:
                    raise HTTPException(422, "Le pourcentage de RRR doit être compris entre 0 et 100 %.")
                montant_force = money(_base_finale_source(facture, source, qte) * D(taux_rrr) / D(100))
                mode_calcul = "rrr_pourcentage"
            elif mode_recu == "rrr_montant":
                montant_force = money(getattr(ligne_in, "montant_ht_avoir", 0) or 0)
                if montant_force <= ZERO:
                    raise HTTPException(422, "Le montant HT du RRR doit être strictement positif.")
                mode_calcul = "rrr_montant"
            else:
                raise HTTPException(422, "Mode de calcul RRR invalide.")
            nouveau_credit = D(montant_force)
        elif nature_avoir == "correction_prix":
            nouveau_prix = getattr(ligne_in, "nouveau_prix_unitaire", None)
            if nouveau_prix is None:
                raise HTTPException(422, "Renseignez le nouveau prix unitaire pour une correction de prix.")
            nouveau_prix = float(nouveau_prix)
            ancien_prix = float(source.prix_unitaire or 0)
            if not isfinite(nouveau_prix) or nouveau_prix < 0 or nouveau_prix >= ancien_prix:
                raise HTTPException(422, "Le nouveau prix doit être positif ou nul et inférieur au prix facturé.")
            montant_force = _base_finale_correction_prix(facture, source, qte, nouveau_prix)
            if montant_force <= ZERO:
                raise HTTPException(422, "Cette correction de prix ne génère aucun montant à créditer.")
            mode_calcul = "correction_prix"
            nouveau_credit = D(montant_force)
        else:  # autre avoir : montant HT explicite rattaché à la ligne source
            montant_force = money(getattr(ligne_in, "montant_ht_avoir", 0) or 0)
            if montant_force <= ZERO:
                raise HTTPException(422, "Renseignez le montant HT à créditer pour cet avoir.")
            mode_calcul = "autre_montant"
            nouveau_credit = D(montant_force)

        plafond_ligne = _base_finale_source(facture, source)
        restant_valeur = max(plafond_ligne - deja_montants.get(source.id, ZERO), ZERO)
        if nouveau_credit > restant_valeur + D("0.01"):
            raise HTTPException(409,
                f"Le montant à créditer dépasse le reliquat économique de la ligne « {source.description} » "
                f"({float(restant_valeur):.2f} MAD HT disponibles).")

        sources.append({
            "source": source, "qte": qte, "mode_calcul": mode_calcul,
            "montant_force": float(montant_force) if montant_force is not None else None,
            "taux_rrr": taux_rrr, "nouveau_prix": nouveau_prix,
        })

    societe_obj = db.query(models.Societe).filter_by(id=societe_id).first()
    prefixe_av = getattr(societe_obj, "prefixe_avoir", None) or "AV"
    numero_avoir = reserver_numero_commercial(
        db, societe_id, exercice_avoir.annee, "avoir", prefixe_av
    )

    avoir = models.Avoir(
        societe_id=societe_id, facture_id=facture.id, numero=numero_avoir,
        type=facture.type, date=data.date, exercice=exercice_avoir.annee, tiers=facture.tiers,
        motif=data.motif, notes=data.notes, statut="emis",
        retour_stock=bool(data.retour_stock and nature_avoir == "retour_annulation"),
        nature_avoir=nature_avoir,
        remise_globale_snapshot=float(getattr(facture, "remise_globale", 0) or 0),
        ristourne_snapshot=float(getattr(facture, "ristourne", 0) or 0),
        escompte_snapshot=float(getattr(facture, "escompte", 0) or 0),
        nature_tva_achat_snapshot=getattr(facture, "nature_tva_achat", None),
        tva_deductible_pct_snapshot=getattr(facture, "tva_deductible_pct", None),
        societe_snapshot_json=getattr(facture, "societe_snapshot_json", None),
        tiers_ice_snapshot=getattr(facture, "tiers_ice_snapshot", None),
        tiers_if_snapshot=getattr(facture, "tiers_if_snapshot", None),
        tiers_rc_snapshot=getattr(facture, "tiers_rc_snapshot", None),
        tiers_adresse_snapshot=getattr(facture, "tiers_adresse_snapshot", None),
        tiers_ville_snapshot=getattr(facture, "tiers_ville_snapshot", None),
        tiers_telephone_snapshot=getattr(facture, "tiers_telephone_snapshot", None),
        tiers_email_snapshot=getattr(facture, "tiers_email_snapshot", None),
        tiers_categorie_snapshot=getattr(facture, "tiers_categorie_snapshot", None),
        notes_snapshot=data.notes,
    )
    db.add(avoir)
    db.flush()

    for item in sources:
        source = item["source"]
        db.add(models.LigneAvoir(
            avoir_id=avoir.id, facture_ligne_id=source.id,
            article_id=getattr(source, "article_id", None), description=source.description,
            quantite=item["qte"], prix_unitaire=source.prix_unitaire, tva=source.tva,
            qualification_tva=getattr(source, "qualification_tva", "taxable") or "taxable",
            remise=getattr(source, "remise", 0) or 0, remise2=getattr(source, "remise2", 0) or 0,
            rabais=getattr(source, "rabais", 0) or 0,
            montant_ht_force=item["montant_force"], mode_calcul=item["mode_calcul"],
            taux_rrr=item["taux_rrr"], nouveau_prix_unitaire=item["nouveau_prix"],
        ))

    db.commit()
    return _fmt_avoir(
        db.query(models.Avoir)
        .options(joinedload(models.Avoir.lignes))
        .filter_by(id=avoir.id)
        .first(),
        db,
    )


@router.get("/{avoir_id}/factures-imputables")
def factures_imputables_avoir(
    avoir_id: int, current_user=Depends(get_current_user), db: Session=Depends(get_db)
):
    societe_id = current_user["societe_id"]
    avoir = db.query(models.Avoir).filter_by(id=avoir_id, societe_id=societe_id).first()
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    facture_source = db.query(models.Facture).filter_by(id=avoir.facture_id, societe_id=societe_id).first()
    if not facture_source:
        raise HTTPException(409, "Facture source introuvable")
    from routers.factures import _situation_paiement_facture
    out = []
    for facture in db.query(models.Facture).filter(
        models.Facture.societe_id == societe_id,
        models.Facture.est_validee == True,  # noqa: E712
        models.Facture.est_proforma == False,  # noqa: E712
        models.Facture.id != facture_source.id,
    ).order_by(models.Facture.date.desc(), models.Facture.id.desc()).all():
        if _type_value(facture.type) != _type_value(avoir.type):
            continue
        meme_tiers = bool(
            getattr(facture_source, "tiers_id", None) and getattr(facture, "tiers_id", None)
            and facture_source.tiers_id == facture.tiers_id
        ) or (not getattr(facture_source, "tiers_id", None) and facture.tiers == avoir.tiers)
        if not meme_tiers:
            continue
        situation = _situation_paiement_facture(db, societe_id, facture)
        if situation["solde_restant"] <= 0.01:
            continue
        out.append({
            "id": facture.id, "numero": facture.numero, "date": facture.date,
            "exercice": facture.exercice, "total_ttc": situation["total_ttc"],
            "solde_restant": situation["solde_restant"],
        })
    return out


@router.post("/{avoir_id}/utiliser", response_model=schemas.AvoirOut)
def utiliser_credit_avoir(
    avoir_id: int, data: UtiliserAvoirIn,
    current_user=Depends(requiert_ecriture), db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    avoir = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter_by(
        id=avoir_id, societe_id=societe_id
    ).with_for_update(of=models.Avoir).first()
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    if _type_value(avoir.statut) == "annule":
        raise HTTPException(409, "Un avoir annulé ne peut pas être utilisé.")
    if not avoir.est_comptabilisee:
        raise HTTPException(409, "Comptabilisez d'abord l'avoir avant d'utiliser son crédit.")
    montant = float(data.montant or 0)
    if not isfinite(montant) or montant <= 0:
        raise HTTPException(422, "Le montant doit être strictement positif.")
    _, _, disponible = _credit_excedentaire_avoir(db, avoir)
    if round(montant, 2) > round(float(disponible), 2):
        raise HTTPException(409, f"Crédit disponible insuffisant : {disponible:.2f} MAD.")

    try:
        from services.exercices_service import verifier_date_ecriture
        exercice = verifier_date_ecriture(db, societe_id, data.date_utilisation, action="enregistrer")
    except ValueError as exc:
        msg = str(exc); status = 423 if "clôtur" in msg.lower() or "fermé" in msg.lower() else 409
        raise HTTPException(status, msg) from exc

    facture_source = db.query(models.Facture).filter_by(id=avoir.facture_id, societe_id=societe_id).first()
    if data.date_acceptation_compensation is not None:
        if data.type_utilisation != "imputation" or data.date_acceptation_compensation != data.date_utilisation:
            raise HTTPException(422, "La compensation doit être imputée à la date de signature de l'accord.")
        if not (data.reference or "").strip() or len(data.reference.strip()) > 100:
            raise HTTPException(422, "Renseignez la référence de l'accord signé (100 caractères maximum).")
    row = models.UtilisationAvoir(
        societe_id=societe_id, avoir_id=avoir.id, type_utilisation=data.type_utilisation,
        date_utilisation=data.date_utilisation, montant=round(montant, 2),
        date_acceptation_compensation=data.date_acceptation_compensation,
        mode=data.mode, compte_bancaire_id=data.compte_bancaire_id, banque=data.banque,
        reference=data.reference.strip() if data.date_acceptation_compensation else data.reference, statut="active",
    )

    if data.type_utilisation == "imputation":
        if not data.facture_id or data.facture_id == avoir.facture_id:
            raise HTTPException(422, "Choisissez une autre facture du même tiers.")
        cible = db.query(models.Facture).filter_by(id=data.facture_id, societe_id=societe_id).with_for_update().first()
        if not cible or not cible.est_validee or cible.est_proforma:
            raise HTTPException(404, "Facture cible introuvable ou non définitive.")
        if data.date_utilisation < max(cible.date, avoir.date):
            raise HTTPException(422, "L'imputation ne peut précéder la facture cible ni l'avoir.")
        if data.date_acceptation_compensation and data.date_acceptation_compensation < max(cible.date, avoir.date):
            raise HTTPException(422, "La signature de compensation ne peut précéder la facture et l'avoir.")
        if _type_value(cible.type) != _type_value(avoir.type):
            raise HTTPException(422, "Le type de la facture cible est incompatible avec cet avoir.")
        meme_tiers = bool(
            getattr(facture_source, "tiers_id", None) and getattr(cible, "tiers_id", None)
            and facture_source.tiers_id == cible.tiers_id
        ) or (not getattr(facture_source, "tiers_id", None) and cible.tiers == avoir.tiers)
        if not meme_tiers:
            raise HTTPException(422, "L'avoir ne peut être imputé que sur une facture du même tiers.")
        from routers.factures import _situation_paiement_facture
        situation = _situation_paiement_facture(db, societe_id, cible)
        if round(montant, 2) > round(situation["solde_restant"], 2):
            raise HTTPException(409, f"Le solde de la facture cible n'est que de {situation['solde_restant']:.2f} MAD.")
        row.facture_id = cible.id
    else:
        mode = data.mode or "virement"
        banque_nom = (data.banque or "").strip() or None
        if data.compte_bancaire_id:
            cb = db.query(models.CompteBancaire).filter_by(
                id=data.compte_bancaire_id, societe_id=societe_id, actif=True
            ).first()
            if not cb:
                raise HTTPException(422, "Compte bancaire introuvable ou inactif.")
            banque_nom = cb.banque
            treso = cb.compte_comptable or "5141"
        else:
            treso = compte_tresorerie(db, societe_id, mode=mode, banque=banque_nom)
        row.mode = mode; row.banque = banque_nom
        compte_tiers = compte_tiers_facture(db, societe_id, facture_source)
        if _type_value(avoir.type) == "vente":
            lignes = [
                models.LigneEcriture(compte=compte_tiers, libelle=f"Remboursement avoir {avoir.numero}", debit=montant, credit=0),
                models.LigneEcriture(compte=treso, libelle="Trésorerie", debit=0, credit=montant),
            ]
        else:
            lignes = [
                models.LigneEcriture(compte=treso, libelle="Trésorerie", debit=montant, credit=0),
                models.LigneEcriture(compte=compte_tiers, libelle=f"Remboursement avoir {avoir.numero}", debit=0, credit=montant),
            ]
        rattacher_tiers_aux_lignes(
            db, societe_id, lignes,
            tiers_id=getattr(facture_source, "tiers_id", None),
            nature="client" if _type_value(avoir.type) == "vente" else "fournisseur",
        )
        ecriture = models.Ecriture(
            societe_id=societe_id, journal="CA" if mode == "especes" else "BQ",
            date=data.date_utilisation, date_piece=data.date_utilisation,
            libelle=f"Remboursement crédit avoir {avoir.numero} — {avoir.tiers}",
            reference=f"REM-{avoir.numero}"[:100], exercice=exercice.annee, source="avoir", lignes=lignes,
        )
        db.add(ecriture); db.flush(); row.ecriture_id = ecriture.id

    db.add(row); db.flush()
    _maj_statut_avoir_credit(db, avoir)
    db.commit()
    return _fmt_avoir(db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter_by(id=avoir.id).first(), db)


@router.post("/{avoir_id}/utilisations/{utilisation_id}/annuler", response_model=schemas.AvoirOut)
def annuler_utilisation_avoir(
    avoir_id: int, utilisation_id: int, date_annulation: Optional[date_type] = Query(None),
    current_user=Depends(requiert_ecriture), db: Session=Depends(get_db),
):
    societe_id = current_user["societe_id"]
    avoir = db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter_by(
        id=avoir_id, societe_id=societe_id
    ).with_for_update(of=models.Avoir).first()
    row = db.query(models.UtilisationAvoir).filter_by(
        id=utilisation_id, avoir_id=avoir_id, societe_id=societe_id
    ).with_for_update().first()
    if not avoir or not row:
        raise HTTPException(404, "Utilisation de l'avoir introuvable")
    if row.statut == "annulee":
        return _fmt_avoir(avoir, db)
    jour = date_annulation or date_type.today()
    try:
        from services.exercices_service import verifier_date_ecriture
        exercice = verifier_date_ecriture(db, societe_id, jour, action="enregistrer")
    except ValueError as exc:
        msg = str(exc); status = 423 if "clôtur" in msg.lower() or "fermé" in msg.lower() else 409
        raise HTTPException(status, msg) from exc
    if row.ecriture_id:
        original = db.query(models.Ecriture).filter_by(id=row.ecriture_id, societe_id=societe_id).first()
        if not original:
            raise HTTPException(409, "Écriture de remboursement introuvable.")
        _ = original.lignes
        inverse = models.Ecriture(
            societe_id=societe_id, journal=original.journal, date=jour, date_piece=jour,
            libelle=f"Annulation remboursement avoir {avoir.numero}",
            reference=f"ANN-REM-{avoir.numero}-{row.id}"[:100], exercice=exercice.annee, source="avoir",
            lignes=[models.LigneEcriture(
                compte=l.compte, libelle=f"Annulation {l.libelle or avoir.numero}", debit=l.credit, credit=l.debit,
                tiers_id=getattr(l, "tiers_id", None),
                nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
            ) for l in original.lignes],
        )
        db.add(inverse); db.flush(); row.ecriture_annulation_id = inverse.id
    if row.date_acceptation_compensation and jour < row.date_acceptation_compensation:
        raise HTTPException(422, "L'annulation ne peut précéder la signature de compensation.")
    row.statut = "annulee"; row.date_annulation = datetime.now(); row.date_annulation_effective = jour; row.annulee_par = current_user.get("id")
    _maj_statut_avoir_credit(db, avoir)
    db.commit()
    return _fmt_avoir(db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter_by(id=avoir.id).first(), db)


@router.patch("/{avoir_id}", response_model=schemas.AvoirOut)
def modifier_avoir(
    avoir_id: int,
    data: schemas.AvoirUpdate,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    societe_id = current_user["societe_id"]
    avoir = db.query(models.Avoir).filter_by(id=avoir_id, societe_id=societe_id).first()
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    if _type_value(avoir.statut) == "annule":
        raise HTTPException(409, "Cet avoir est annulé et ne peut plus être modifié.")
    if data.statut == "annule":
        raise HTTPException(409, "Utilisez l'action dédiée « Annuler l'avoir » afin de conserver la piste d'audit.")
    if avoir.est_comptabilisee and data.statut is not None:
        raise HTTPException(400, "Impossible de changer le statut d'un avoir déjà comptabilisé.")

    for k, v in data.model_dump(exclude_none=True).items():
        setattr(avoir, k, v)
    db.commit()
    return _fmt_avoir(
        db.query(models.Avoir).options(joinedload(models.Avoir.lignes)).filter_by(id=avoir_id).first(),
        db,
    )


@router.delete("/{avoir_id}", status_code=204)
def supprimer_avoir(
    avoir_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    avoir = db.query(models.Avoir).filter_by(id=avoir_id, societe_id=current_user["societe_id"]).first()
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    raise HTTPException(409,
        "Un avoir numéroté ne se supprime pas afin de préserver la séquence documentaire. "
        "Utilisez l'action « Annuler l'avoir ».")


def _compte_rrr(compte_source: str, est_vente: bool) -> str:
    compte = str(compte_source or "")
    if est_vente:
        return "7119" if compte.startswith("711") else "7129"
    return "6119" if compte.startswith("611") else "6129"


@router.post("/{avoir_id}/comptabiliser")
def comptabiliser_avoir(
    avoir_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    from routers.cloture import exercice_est_clos

    societe_id = current_user["societe_id"]
    module = db.query(models.ModuleActif).filter_by(
        societe_id=societe_id, module="comptabilite", actif=True
    ).first()
    if not module:
        raise HTTPException(400, "Module Comptabilité inactif")

    avoir = (
        db.query(models.Avoir)
        .options(joinedload(models.Avoir.lignes))
        .filter_by(id=avoir_id, societe_id=societe_id)
        .with_for_update(of=models.Avoir)
        .first()
    )
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    if _type_value(avoir.statut) == "annule":
        raise HTTPException(409, "Un avoir annulé ne peut pas être comptabilisé.")
    if avoir.est_comptabilisee:
        raise HTTPException(409, "Cet avoir est déjà comptabilisé.")
    if exercice_est_clos(db, societe_id, avoir.exercice):
        raise HTTPException(423, f"Exercice {avoir.exercice} clôturé : impossible de comptabiliser cet avoir.")

    facture = db.query(models.Facture).filter_by(
        id=avoir.facture_id, societe_id=societe_id
    ).first()
    if not facture:
        raise HTTPException(409, "La facture d'origine de cet avoir est introuvable.")
    if not getattr(facture, "est_comptabilisee", False):
        raise HTTPException(409,
            "Comptabilisez d'abord la facture d'origine avant de comptabiliser son avoir.")

    avant = total_ventilation(ventilation_avoir(avoir, appliquer_escompte=False))
    apres = total_ventilation(ventilation_avoir(avoir, appliquer_escompte=True))
    total_ht_comptable = D(avant["base"])
    total_base_tva = D(apres["base"])
    total_tva = D(apres["tva"])
    total_ttc = D(apres["ttc"])
    montant_escompte_ht = money(total_ht_comptable - total_base_tva)

    est_vente = _type_value(avoir.type) == "vente"
    libelle = _libelle_ecriture(
        db, societe_id, "avoir", numero=avoir.numero, tiers=avoir.tiers,
        ref=facture.numero or "", date_doc=avoir.date,
    )

    compte_tiers = compte_tiers_facture(db, societe_id, facture)

    if est_vente:
        groupes_ca = groupes_avoir_par_compte(
            db, societe_id, avoir, facture, est_vente=True, cible=total_ht_comptable
        )
        lignes_ecriture = []
        nature = (getattr(avoir, "nature_avoir", None) or "retour_annulation").lower()
        for compte, montant in sorted(groupes_ca.items()):
            compte_ecriture = _compte_rrr(compte, True) if nature == "rrr" else compte
            libelle_ligne = "RRR accordés après facturation" if nature == "rrr" else "Avoir sur ventes"
            lignes_ecriture.append(models.LigneEcriture(
                compte=compte_ecriture, libelle=libelle_ligne, debit=montant, credit=0
            ))
        lignes_ecriture.extend([
            models.LigneEcriture(compte="4455", libelle="État — TVA facturée (avoir)", debit=total_tva, credit=0),
            models.LigneEcriture(compte=compte_tiers, libelle=avoir.tiers or "Clients", debit=0, credit=total_ttc),
        ])
        if montant_escompte_ht > ZERO:
            lignes_ecriture.append(models.LigneEcriture(
                compte="6386", libelle="Reprise escompte accordé", debit=0, credit=montant_escompte_ht
            ))
    else:
        # Reprendre le ratio TVA réellement comptabilisé sur la facture source,
        # plutôt que le paramétrage courant qui a pu changer depuis.
        refs_source = [r for r in {facture.reference, facture.numero} if (r or "").strip()]
        ecriture_source = (
            db.query(models.Ecriture)
            .options(joinedload(models.Ecriture.lignes))
            .filter(
                models.Ecriture.societe_id == societe_id,
                models.Ecriture.journal == "AC",
                models.Ecriture.reference.in_(refs_source),
            )
            .order_by(models.Ecriture.id.asc())
            .first()
        )
        if not ecriture_source:
            raise HTTPException(409,
                "Écriture d'achat d'origine introuvable : impossible de déterminer la TVA à reprendre.")
        tva_facture = D(total_ventilation(
            __import__("services.tva_service", fromlist=["ventilation_facture"]).ventilation_facture(
                facture, appliquer_escompte=True
            )
        )["tva"])
        tva_deductible_source = sum(
            (D(l.debit) - D(l.credit)) for l in ecriture_source.lignes if l.compte in ("34551", "34552")  # lot 979
        )
        ratio_deductible = (tva_deductible_source / tva_facture) if tva_facture > ZERO else ZERO
        ratio_deductible = max(ZERO, min(D(1), ratio_deductible))
        tva_deductible = money(total_tva * ratio_deductible)
        tva_non_deductible = money(total_tva - tva_deductible)

        groupes_achats = groupes_avoir_par_compte(
            db, societe_id, avoir, facture, est_vente=False, cible=total_ht_comptable
        )
        lignes_ecriture = [
            models.LigneEcriture(compte=compte_tiers, libelle=avoir.tiers or "Fournisseurs", debit=total_ttc, credit=0),
        ]
        nature = (getattr(avoir, "nature_avoir", None) or "retour_annulation").lower()
        for compte, montant in sorted(groupes_achats.items()):
            # Lot 979 : un RRR sur immobilisation diminue la valeur du bien, pas une charge.
            compte_ecriture = _compte_rrr(compte, False) if nature == "rrr" and not est_compte_immobilisation(compte) else compte
            libelle_ligne = "RRR obtenus après facturation" if nature == "rrr" else "Avoir sur achats"
            lignes_ecriture.append(models.LigneEcriture(
                compte=compte_ecriture, libelle=libelle_ligne, debit=0, credit=montant
            ))
        # Lot 979 : la TVA reprise suit la nature des lignes (34551 immobilisations, 34552 charges).
        total_groupes = sum(groupes_achats.values(), ZERO)
        part_immo = (sum((m for c, m in groupes_achats.items() if est_compte_immobilisation(c)), ZERO) / total_groupes) if total_groupes else ZERO
        tva_ded_immo = money(tva_deductible * part_immo)
        for compte_tva, montant_tva, libelle_tva in (("34551", tva_ded_immo, "État — TVA récupérable sur immobilisations (avoir)"),
                                                     ("34552", money(tva_deductible - tva_ded_immo), "État — TVA récupérable (avoir)")):
            if montant_tva > ZERO:
                lignes_ecriture.append(models.LigneEcriture(compte=compte_tva, libelle=libelle_tva, debit=0, credit=montant_tva))
        if tva_non_deductible > ZERO:
            allocation_non_ded = repartir_par_poids(tva_non_deductible, groupes_achats)
            if allocation_non_ded:
                for compte, montant in sorted(allocation_non_ded.items()):
                    lignes_ecriture.append(models.LigneEcriture(
                        compte=compte, libelle="Reprise TVA non déductible", debit=0, credit=montant
                    ))
            else:
                lignes_ecriture.append(models.LigneEcriture(
                    compte="6111", libelle="Reprise TVA non déductible", debit=0, credit=tva_non_deductible
                ))
        if montant_escompte_ht > ZERO:
            lignes_ecriture.append(models.LigneEcriture(
                compte="7386", libelle="Reprise escompte obtenu", debit=montant_escompte_ht, credit=0
            ))

    rattacher_tiers_aux_lignes(
        db, societe_id, lignes_ecriture,
        tiers_id=getattr(facture, "tiers_id", None),
        nature="client" if est_vente else "fournisseur",
    )

    _appliquer_retour_stock(db, societe_id, avoir, facture, user_id=current_user.get("id"))

    ecriture = models.Ecriture(
        societe_id=societe_id,
        journal="AV",
        date=avoir.date,
        date_piece=avoir.date,
        libelle=libelle,
        reference=avoir.numero,
        exercice=avoir.exercice,
        source="avoir",
        lignes=lignes_ecriture,
    )
    db.add(ecriture)
    avoir.est_comptabilisee = True
    db.commit()
    return {"message": "Avoir comptabilisé", "ecriture_id": ecriture.id}


@router.post("/{avoir_id}/annuler")
def annuler_avoir(
    avoir_id: int,
    date_annulation: Optional[date_type] = Query(None),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Annule un avoir sans effacer l'historique.

    Si l'avoir était comptabilisé, FACT.6 génère une écriture strictement inverse.
    Si un retour physique avait été enregistré, le ledger stock est compensé via
    le moteur 06C. Une seconde annulation est idempotente.
    """
    societe_id = current_user["societe_id"]
    avoir = (
        db.query(models.Avoir)
        .options(joinedload(models.Avoir.lignes))
        .filter_by(id=avoir_id, societe_id=societe_id)
        .with_for_update(of=models.Avoir)
        .first()
    )
    if not avoir:
        raise HTTPException(404, "Avoir introuvable")
    if _type_value(avoir.statut) == "annule":
        return {"message": "Avoir déjà annulé", "ecriture_annulation_id": avoir.ecriture_annulation_id}
    if db.query(models.UtilisationAvoir).filter_by(
        societe_id=societe_id, avoir_id=avoir.id, statut="active"
    ).count() > 0:
        raise HTTPException(409, "Cet avoir a déjà été utilisé/remboursé : annulez d'abord ses utilisations.")

    jour = date_annulation or date_type.today()
    try:
        from services.exercices_service import verifier_date_ecriture
        exercice_annulation = verifier_date_ecriture(db, societe_id, jour, action="enregistrer")
    except ValueError as exc:
        msg = str(exc)
        status = 423 if "clôtur" in msg.lower() or "fermé" in msg.lower() else 409
        raise HTTPException(status, msg) from exc

    ecriture_annulation = None
    if avoir.est_comptabilisee:
        original = (
            db.query(models.Ecriture)
            .options(joinedload(models.Ecriture.lignes))
            .filter_by(societe_id=societe_id, journal="AV", reference=avoir.numero)
            .order_by(models.Ecriture.id.asc())
            .first()
        )
        if not original:
            raise HTTPException(409, "Écriture comptable d'origine de l'avoir introuvable : annulation bloquée.")

        lignes_inversees = [
            models.LigneEcriture(
                compte=l.compte,
                libelle=f"Annulation {l.libelle or avoir.numero}",
                debit=l.credit,
                credit=l.debit,
                tiers_id=getattr(l, "tiers_id", None),
                nature_auxiliaire=getattr(l, "nature_auxiliaire", None),
                compte_auxiliaire_snapshot=getattr(l, "compte_auxiliaire_snapshot", None),
                libelle_auxiliaire_snapshot=getattr(l, "libelle_auxiliaire_snapshot", None),
            )
            for l in original.lignes
        ]
        ecriture_annulation = models.Ecriture(
            societe_id=societe_id,
            journal="AV",
            date=jour,
            date_piece=jour,
            libelle=f"Annulation avoir {avoir.numero} — {avoir.tiers}",
            reference=f"ANN-{avoir.numero}"[:100],
            exercice=exercice_annulation.annee,
            source="avoir",
            lignes=lignes_inversees,
        )
        db.add(ecriture_annulation)
        db.flush()

        if getattr(avoir, "retour_stock", False):
            from services.stock_movement_service import annuler_mouvements_source
            try:
                annuler_mouvements_source(
                    db,
                    societe_id,
                    source_type="avoir",
                    source_id=avoir.id,
                    reference=f"ANN-{avoir.numero}",
                    note=f"Annulation retour lié à l'avoir {avoir.numero}",
                    date_mouvement=jour,
                    user_id=current_user.get("id"),
                )
            except ValueError as exc:
                raise HTTPException(409, str(exc)) from exc

    avoir.statut = "annule"
    avoir.date_annulation = datetime.now()
    avoir.annulee_par = current_user.get("id")
    avoir.ecriture_annulation_id = ecriture_annulation.id if ecriture_annulation else None
    db.commit()
    return {
        "message": "Avoir annulé",
        "ecriture_annulation_id": avoir.ecriture_annulation_id,
    }
