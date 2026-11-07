# -*- coding: utf-8 -*-
"""Inventaire physique, valorisation et rapprochement comptable des stocks."""
from datetime import date as date_cls
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, requiert_ecriture, requiert_admin
from services.exercices_service import ensure_exercice, verifier_date_ecriture, trouver_exercice_pour_date
from services.exercice_verrou_service import verrouiller_operation_stock
from services.stock_service import (
    creer_snapshot_inventaire,
    etat_stock_cloture,
    generer_ecriture_stock_cloture,
    articles_comptage,
)
from services.stock_ledger_service import auditer_ledger_stock
import models
import valorisation
from services.inventaire_nombres_service import (
    projection_article, nombre, produit, somme, diagnostics_lignes,
)

router = APIRouter(prefix="/api/inventaire", tags=["inventaire"])


class LigneComptage(BaseModel):
    article_id: int
    quantite_reelle: float

    @field_validator('quantite_reelle', mode='before')
    @classmethod
    def quantite_numerique(cls, value):
        if isinstance(value, bool):
            raise ValueError('La quantité doit être un nombre, pas un booléen.')
        return value


class InventaireIn(BaseModel):
    date: Optional[str] = None
    reference: Optional[str] = None
    note: Optional[str] = None
    lignes: List[LigneComptage]


def _date_data(data: InventaireIn):
    if not data.date:
        return date_cls.today()
    try:
        return date_cls.fromisoformat(data.date)
    except ValueError:
        raise HTTPException(400, "Date d'inventaire invalide (format attendu AAAA-MM-JJ).")


@router.get("/feuille")
def feuille_comptage(
    famille_id: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Feuille de comptage basée sur l'état courant du stock."""
    q = db.query(models.Article).filter_by(
        societe_id=current_user["societe_id"], actif=True, is_stockable=True)
    if famille_id:
        q = q.filter(models.Article.famille_id == famille_id)

    articles = q.order_by(models.Article.designation).all()
    return [{
        "article_id": a.id,
        "code": a.code,
        "designation": a.designation,
        "unite": a.unite,
        "famille_id": a.famille_id,
        "stock_theorique": projection_article(a)['stock'],
        "cmup": projection_article(a)['cmup'],
        "valeur_theorique": projection_article(a)['valeur'],
        "nombres_diagnostics": projection_article(a)['nombres_diagnostics'],
    } for a in articles]


@router.post("/simuler")
def simuler_inventaire(
    data: InventaireIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calcule les écarts sans rien enregistrer."""
    societe_id = current_user["societe_id"]
    resultat, total_perte, total_excedent, total_stock = [], 0.0, 0.0, 0.0

    try:
        articles, reels = articles_comptage(db, societe_id, data.lignes)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    for l in data.lignes:
        a = articles[l.article_id]
        reel = float(reels[l.article_id])
        theorique = a.stock_actuel or 0
        ecart = reel - theorique
        cout = valorisation.cout_sortie(a)
        cmup_final = a.cmup or cout or 0
        valeur_stock = round(reel * (cmup_final or 0), 2)
        total_stock += valeur_stock
        if abs(ecart) < 0.0001:
            continue
        valeur = round(ecart * (cout or 0), 2)
        if valeur < 0:
            total_perte += -valeur
        else:
            total_excedent += valeur
        resultat.append({
            "article_id": a.id,
            "code": a.code,
            "designation": a.designation,
            "unite": a.unite,
            "stock_theorique": theorique,
            "stock_reel": reel,
            "ecart": round(ecart, 4),
            "sens": "sortie" if ecart < 0 else "entree",
            "cout_unitaire": round(cout or 0, 4),
            "valeur_ecart": valeur,
        })

    return {
        "nb_ecarts": len(resultat),
        "total_perte": round(total_perte, 2),
        "total_excedent": round(total_excedent, 2),
        "impact_net": round(total_excedent - total_perte, 2),
        "valeur_stock_compte": round(total_stock, 2),
        "ecarts": resultat,
    }


@router.post("/valider")
def valider_inventaire(
    data: InventaireIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    """Valide le comptage, régularise les quantités et fige une photographie."""
    sid = current_user["societe_id"]
    jour = _date_data(data)
    try:
        exercice_obj = trouver_exercice_pour_date(db, sid, jour)
        verrouiller_operation_stock(db, sid, exercice_obj.annee)
        # La clôture peut avoir terminé entre la résolution de la date et
        # l'acquisition du verrou : relire avant tout contrôle et comptage.
        db.refresh(exercice_obj)
        exercice_obj = verifier_date_ecriture(db, sid, jour, action="enregistrer")
        inv, regularises = creer_snapshot_inventaire(
            db, sid, exercice_obj, data, current_user.get("id")
        )
        db.commit()
        db.refresh(inv)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))

    return {
        "inventaire_id": inv.id,
        "reference": inv.reference,
        "date": inv.date_inventaire.isoformat(),
        "exercice": inv.exercice,
        "nb_regularises": len(regularises),
        "nb_articles": len(inv.lignes),
        "total_perte": float(inv.total_perte or 0),
        "total_excedent": float(inv.total_excedent or 0),
        "impact_net": float((inv.total_excedent or 0) - (inv.total_perte or 0)),
        "total_valeur": float(inv.total_valeur or 0),
        "lignes_regularisees": regularises,
    }


@router.get("/stock/cloture")
def controle_stock_cloture(
    exercice: int = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ex = ensure_exercice(db, current_user["societe_id"], exercice)
    return etat_stock_cloture(db, current_user["societe_id"], ex)


@router.post("/comptabiliser-stock")
def comptabiliser_stock_cloture(
    exercice: int = Query(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    ex = ensure_exercice(db, sid, exercice)
    try:
        verrouiller_operation_stock(db, sid, exercice)
        db.refresh(ex)
        verifier_date_ecriture(db, sid, ex.date_fin, action="comptabiliser")
        ec = generer_ecriture_stock_cloture(db, sid, ex, current_user.get("id"))
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc))

    if ec is None:
        return {
            "message": "Le stock comptable brut correspond déjà à l'inventaire physique.",
            "ecriture_id": None,
            "deja_rapproche": True,
        }
    return {
        "message": f"Écriture de stock {exercice} générée en brouillon.",
        "ecriture_id": ec.id,
        "reference": ec.reference,
        "deja_rapproche": False,
    }


@router.get("/inventaires-stock")
def historique_inventaires_stock(
    exercice: Optional[int] = Query(None),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(models.InventaireStock).filter_by(societe_id=current_user["societe_id"])
    if exercice is not None:
        q = q.filter(models.InventaireStock.exercice == exercice)
    rows = q.order_by(models.InventaireStock.date_inventaire.desc(), models.InventaireStock.id.desc()).all()
    resultat = [{
        "id": x.id,
        "exercice": x.exercice,
        "date": x.date_inventaire.isoformat(),
        "reference": x.reference,
        "total_valeur": nombre(x.total_valeur, 'total_valeur', diag, negatif=True, decimales=2),
        "total_perte": nombre(x.total_perte, 'total_perte', diag, decimales=2),
        "total_excedent": nombre(x.total_excedent, 'total_excedent', diag, decimales=2),
        "nombres_diagnostics": diag,
        "ecriture_stock_id": x.ecriture_stock_id,
    } for x in rows for diag in [{}]]
    return resultat


@router.get("/valorisation")
def etat_valorisation(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    articles = db.query(models.Article).filter_by(
        societe_id=current_user["societe_id"], actif=True, is_stockable=True
    ).order_by(models.Article.designation).all()

    lignes = []
    for a in articles:
        projection = projection_article(a)
        diag = projection['nombres_diagnostics']
        seuil = nombre(a.stock_min, 'stock_min', diag)
        lignes.append({
            "article_id": a.id,
            "code": a.code,
            "designation": a.designation,
            "unite": a.unite,
            **projection,
            "sous_seuil": (seuil > 0 and projection['stock'] <= seuil)
                if seuil is not None and projection['stock'] is not None else None,
        })
    totals_diag = {}
    total = somme([l['valeur'] for l in lignes], 'total_valeur', totals_diag)
    diagnostics = diagnostics_lignes(lignes)
    diagnostics.extend({'article_id': None, 'code': None, 'champ': c, 'message': m}
                       for c, m in totals_diag.items())
    return {"total_valeur": total, "nb_articles": len(lignes), "lignes": lignes,
            "valorisation_complete": total is not None and not diagnostics, "diagnostics": diagnostics}


@router.get("/historique/{article_id}")
def historique_valorise(
    article_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    a = db.query(models.Article).filter_by(
        id=article_id, societe_id=current_user["societe_id"]).first()
    if not a:
        raise HTTPException(404, "Article introuvable")

    mvts = db.query(models.MouvementStock).filter_by(
        societe_id=current_user["societe_id"], article_id=article_id
    ).order_by(models.MouvementStock.date_mouvement, models.MouvementStock.id).all()

    return {
        "article": {"id": a.id, "code": a.code, "designation": a.designation,
                    **projection_article(a)},
        "mouvements": [{
            "id": m.id,
            "date": m.date_mouvement.isoformat() if getattr(m, "date_mouvement", None) else None,
            "cree_le": m.created_at.isoformat() if m.created_at else None,
            "type": m.type,
            "quantite": nombre(m.quantite, 'quantite', diag, negatif=True),
            "stock_avant": nombre(m.stock_avant, 'stock_avant', diag, negatif=True),
            "stock_apres": nombre(m.stock_apres, 'stock_apres', diag, negatif=True),
            "cout_unitaire": nombre(m.cout_unitaire, 'cout_unitaire', diag, decimales=4),
            "cmup_apres": nombre(m.cmup_apres, 'cmup_apres', diag, decimales=4),
            "valeur": produit(nombre(m.quantite, 'quantite', diag, negatif=True),
                              nombre(m.cout_unitaire, 'cout_unitaire', diag), 'valeur', diag),
            "nombres_diagnostics": diag,
            "reference": m.reference,
            "note": m.note,
            "source_type": getattr(m, "source_type", None),
            "source_id": getattr(m, "source_id", None),
            "source_ligne_id": getattr(m, "source_ligne_id", None),
            "annule_mouvement_id": getattr(m, "annule_mouvement_id", None),
        } for m in mvts for diag in [{}]],
    }


@router.get("/controle-mouvements")
def controle_mouvements_stock(
    anomalies_uniquement: bool = Query(False),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Audit lecture seule de la continuité des mouvements et du CMUP."""
    return auditer_ledger_stock(
        db, current_user["societe_id"], anomalies_uniquement=anomalies_uniquement
    )


# ─── Livre d'inventaire annuel ────────────────────────────────────────────────

def _charger_archive_livre(db: Session, societe_id: int, exercice: int):
    import json
    from services.livre_inventaire_service import empreinte_snapshot

    row = (
        db.query(models.LivreInventaireArchive)
        .filter_by(societe_id=societe_id, exercice=exercice)
        .order_by(models.LivreInventaireArchive.version.desc(), models.LivreInventaireArchive.id.desc())
        .first()
    )
    if not row:
        return None
    try:
        snapshot = json.loads(row.contenu_json)
    except Exception:
        raise HTTPException(500, "Archive du livre d'inventaire illisible.")
    if empreinte_snapshot(snapshot) != row.empreinte_sha256:
        raise HTTPException(500, "L'empreinte du livre d'inventaire ne correspond plus au contenu archivé.")
    return row, snapshot


def _reponse_livre(row, snapshot, revision_requise: bool = False):
    return {
        "archive": None if row is None else {
            "id": row.id,
            "version": row.version,
            "date_etablissement": row.date_etablissement.isoformat() if row.date_etablissement else None,
            "empreinte_sha256": row.empreinte_sha256,
            "cree_par": row.cree_par,
        },
        # Si une archive v1 existe, ``snapshot`` peut être un aperçu recalculé
        # selon les contrôles v2. L'archive v1 reste conservée et son empreinte
        # n'est jamais modifiée ; une v2 pourra ensuite la superséder.
        "revision_requise": bool(revision_requise),
        "snapshot": snapshot,
    }


@router.get("/livre")
def livre_inventaire(
    exercice: int = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne l'archive figée si elle existe, sinon un aperçu calculé à l'instant."""
    from services.livre_inventaire_service import construire_snapshot, CURRENT_LIVRE_VERSION

    sid = current_user["societe_id"]
    archive = _charger_archive_livre(db, sid, exercice)
    if archive:
        row, snapshot_archive = archive
        if row.version >= CURRENT_LIVRE_VERSION:
            return _reponse_livre(row, snapshot_archive)
        # Les archives créées avant le Patch 05B restent intactes mais ne
        # suffisent plus : on affiche un aperçu recalculé avec les nouveaux
        # contrôles afin de pouvoir produire une archive v2 sans supprimer v1.
        try:
            snapshot_courant = construire_snapshot(db, sid, exercice)
        except ValueError as exc:
            raise HTTPException(404, str(exc))
        return _reponse_livre(row, snapshot_courant, revision_requise=True)
    try:
        snapshot = construire_snapshot(db, sid, exercice)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return _reponse_livre(None, snapshot)


@router.post("/livre/archiver")
def archiver_livre_inventaire(
    exercice: int = Query(...),
    current_user=Depends(requiert_admin),
    db: Session = Depends(get_db),
):
    """Fige définitivement le livre d'inventaire d'un exercice clôturé.

    Une seule archive est créée par société/exercice. Le contenu canonique est
    accompagné d'une empreinte SHA-256 afin de détecter toute altération ultérieure.
    """
    from services.livre_inventaire_service import (
        construire_snapshot, canonical_json, empreinte_snapshot, CURRENT_LIVRE_VERSION
    )

    sid = current_user["societe_id"]
    existante = _charger_archive_livre(db, sid, exercice)
    if existante and existante[0].version >= CURRENT_LIVRE_VERSION:
        raise HTTPException(
            409,
            f"Le livre d'inventaire {exercice} est déjà archivé en version {CURRENT_LIVRE_VERSION} "
            "et ne peut pas être remplacé."
        )

    try:
        snapshot = construire_snapshot(db, sid, exercice)
    except ValueError as exc:
        raise HTTPException(404, str(exc))

    ctrl = snapshot.get("controles", {})
    if not ctrl.get("exercice_cloture"):
        raise HTTPException(409, "Le livre d'inventaire ne peut être archivé définitivement qu'après la clôture de l'exercice.")
    if not ctrl.get("aucun_brouillon"):
        raise HTTPException(409, "Des écritures sont encore en brouillon : archive impossible.")
    if not ctrl.get("balance_equilibree"):
        raise HTTPException(409, "La balance débit/crédit n'est pas équilibrée : archive impossible.")
    if not ctrl.get("bilan_equilibre"):
        raise HTTPException(409, "Le bilan n'est pas équilibré : archive impossible.")
    if not ctrl.get("inventaire_stock_valide"):
        raise HTTPException(409, "Aucun inventaire physique de clôture validé : archive impossible.")
    if not ctrl.get("stock_rapproche"):
        stocks = snapshot.get("stocks", {})
        if stocks.get('valorisation_complete') is False:
            raise HTTPException(409, "Valorisation historique de stock à vérifier : archive impossible.")
        physique = stocks.get("valeur_physique", 0)
        comptable = stocks.get("valeur_comptable_brute", 0)
        ecart = stocks.get("ecart_physique_comptable", 0)
        raise HTTPException(
            409,
            f"Stock non rapproché : physique brut {physique:.2f} MAD, "
            f"comptable brut {comptable:.2f} MAD, écart {ecart:.2f} MAD. "
            "Comptabilisez le stock final avant l'archivage définitif."
        )
    if not ctrl.get("immobilisations_rapprochees"):
        rap = snapshot.get("immobilisations", {}).get("rapprochement", {})
        raise HTTPException(
            409,
            "Immobilisations non rapprochées : "
            f"brut registre {rap.get('brut_module', 0):.2f} MAD / "
            f"comptabilité {rap.get('brut_comptable', 0):.2f} MAD ; "
            f"amortissements registre {rap.get('amortissements_module', 0):.2f} MAD / "
            f"comptabilité {rap.get('amortissements_comptables', 0):.2f} MAD. "
            "Analysez les comptes d'immobilisations avant l'archivage définitif."
        )

    contenu = canonical_json(snapshot)
    empreinte = empreinte_snapshot(snapshot)
    row = models.LivreInventaireArchive(
        societe_id=sid,
        exercice=exercice,
        version=CURRENT_LIVRE_VERSION,
        contenu_json=contenu,
        empreinte_sha256=empreinte,
        cree_par=current_user.get("id"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _reponse_livre(row, snapshot)


@router.get("/livre/pdf")
def pdf_livre_inventaire(
    exercice: int = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Télécharge le Livre d'inventaire en PDF, archivé si disponible."""
    from fastapi.responses import Response
    from services.livre_inventaire_service import construire_snapshot, CURRENT_LIVRE_VERSION

    sid = current_user["societe_id"]
    archive = _charger_archive_livre(db, sid, exercice)
    row = None
    if archive and archive[0].version >= CURRENT_LIVRE_VERSION:
        row, snapshot = archive
    else:
        # Une archive v1 reste conservée en base mais l'export affiché pendant
        # la révision 05B doit refléter les contrôles courants, pas reproduire
        # silencieusement une présentation désormais connue comme incomplète.
        try:
            snapshot = construire_snapshot(db, sid, exercice)
        except ValueError as exc:
            raise HTTPException(404, str(exc))

    societe = db.query(models.Societe).filter_by(id=sid).first()
    try:
        from services.livre_inventaire_pdf import generer_livre_inventaire_pdf
        pdf = generer_livre_inventaire_pdf(
            societe,
            snapshot,
            None if row is None else {
                "version": row.version,
                "date_etablissement": row.date_etablissement.isoformat() if row.date_etablissement else None,
                "empreinte_sha256": row.empreinte_sha256,
            },
        )
    except ImportError:
        raise HTTPException(503, "Export PDF indisponible : installez la dépendance reportlab du requirements.txt.")

    nom = f"livre_inventaire_{exercice}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nom}"'},
    )
