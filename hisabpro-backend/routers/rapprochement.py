from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import math
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StrictInt
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import rapprochement_ventilation as ventilation
from rapprochement_propositions import construire as construire_propositions
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user, requiert_ecriture
import models, schemas

router = APIRouter(prefix="/api/rapprochement", tags=["rapprochement"])


class RapprocherIn(BaseModel):
    ecriture_ligne_id: int


class RapprocherVentilationIn(BaseModel):
    operation_id: UUID


class ConfirmerPropositionsIn(BaseModel):
    date_debut: date
    date_fin: date
    empreinte: str = Field(pattern=r'^[a-f0-9]{64}$')
    releve_ids: List[StrictInt] = Field(min_length=1, max_length=500)


class LigneReleveLectureOut(schemas.RapprochementLigneOut):
    montant: Optional[float] = None
    montant_valide: bool = True
    montant_anomalie: Optional[str] = None


def _montant_releve_exploitable(montant):
    return montant is not None and math.isfinite(montant) and montant > 0


def _releve_out(ligne):
    out = schemas.RapprochementLigneOut.model_validate(ligne).model_dump(mode='json')
    valide = _montant_releve_exploitable(ligne.montant)
    out['montant_valide'] = valide
    out['montant_anomalie'] = None if valide else 'Montant historique manquant, non fini ou non positif : à vérifier avec le justificatif.'
    if not valide:
        out['montant'] = None
    return out


class EtatRapprochementIn(BaseModel):
    date_debut: date
    date_fin: date
    # ``solde_releve`` est conservé uniquement pour compatibilité avec le front
    # livré avant 048. La source de vérité devient initial + final.
    solde_releve: Optional[Decimal] = None
    solde_initial: Optional[Decimal] = None
    solde_final: Optional[Decimal] = None


class LigneImportIn(BaseModel):
    date: date
    libelle: Optional[str] = None
    montant: Decimal = Field(gt=0)
    sens: str


class ImportRapprochementIn(BaseModel):
    compte: str
    lignes: List[LigneImportIn]


def _sens_valide(sens: str) -> str:
    sens = (sens or "").strip().lower()
    if sens not in {"debit", "credit"}:
        raise HTTPException(400, "Le sens du relevé doit être 'debit' ou 'credit'.")
    return sens


def _montant_releve_valide(value) -> Decimal:
    try:
        montant = Decimal(str(value))
        if not montant.is_finite():
            raise ValueError()
        montant = montant.quantize(Decimal("0.01"))
        if montant <= 0:
            raise ValueError()
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(400, "Le montant doit être un nombre fini strictement positif au centime.")
    return montant


def _ligne_releve(db: Session, sid: int, ligne_id: int):
    ligne = db.query(models.RapprochementLigne).filter_by(id=ligne_id, societe_id=sid).first()
    if not ligne:
        raise HTTPException(404, "Ligne de relevé introuvable")
    return ligne


def _ligne_comptable(db: Session, sid: int, ligne_id: int):
    row = (
        db.query(models.LigneEcriture, models.Ecriture)
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.LigneEcriture.id == ligne_id,
            models.Ecriture.societe_id == sid,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
        )
        .first()
    )
    if not row:
        raise HTTPException(404, "Ligne comptable définitive introuvable")
    return row


def _exercice_pour_date(db: Session, sid: int, d: date):
    return (
        db.query(models.ExerciceComptable)
        .filter(
            models.ExerciceComptable.societe_id == sid,
            models.ExerciceComptable.date_debut <= d,
            models.ExerciceComptable.date_fin >= d,
        )
        .order_by(models.ExerciceComptable.date_debut.desc())
        .first()
    )


def _date_est_cloturee(db: Session, sid: int, d: date) -> bool:
    ex = _exercice_pour_date(db, sid, d)
    if not ex:
        return False
    return bool(ex.statut == "cloture") or db.query(models.ClotureExercice.id).filter_by(
        societe_id=sid, exercice=ex.annee
    ).first() is not None


def _assert_date_modifiable(db: Session, sid: int, d: date):
    """Le rapprochement d'un exercice clôturé est une archive en lecture seule."""
    ex = _exercice_pour_date(db, sid, d)
    annee = ex.annee if ex else d.year
    if _date_est_cloturee(db, sid, d):
        raise HTTPException(
            409,
            f"Exercice {annee} clôturé : le rapprochement bancaire est en lecture seule.",
        )


def _assert_plage_modifiable(db: Session, sid: int, debut: date, fin: date):
    if fin < debut:
        raise HTTPException(400, "La date de fin doit être postérieure à la date de début.")
    ex_clos = (
        db.query(models.ExerciceComptable)
        .filter(
            models.ExerciceComptable.societe_id == sid,
            models.ExerciceComptable.date_debut <= fin,
            models.ExerciceComptable.date_fin >= debut,
            models.ExerciceComptable.statut == "cloture",
        )
        .first()
    )
    if ex_clos:
        raise HTTPException(
            409,
            f"Exercice {ex_clos.annee} clôturé : le rapprochement bancaire est en lecture seule.",
        )
    cloture = (
        db.query(models.ClotureExercice)
        .join(
            models.ExerciceComptable,
            (models.ExerciceComptable.societe_id == models.ClotureExercice.societe_id)
            & (models.ExerciceComptable.annee == models.ClotureExercice.exercice),
        )
        .filter(
            models.ClotureExercice.societe_id == sid,
            models.ExerciceComptable.date_debut <= fin,
            models.ExerciceComptable.date_fin >= debut,
        )
        .first()
    )
    if cloture:
        raise HTTPException(
            409,
            f"Exercice {cloture.exercice} clôturé : le rapprochement bancaire est en lecture seule.",
        )


def _plage_est_cloturee(db: Session, sid: int, debut: date, fin: date) -> bool:
    """La lecture et les mutations utilisent exactement la même archive."""
    try:
        _assert_plage_modifiable(db, sid, debut, fin)
    except HTTPException as exc:
        if exc.status_code == 409:
            return True
        raise
    return False


def _compta_out(ligne, ec, rapprochement_ligne_id=None):
    return {
        "ligne_id": ligne.id,
        "ecriture_id": ec.id,
        "numero_ecriture": ec.numero_ecriture,
        "date": ec.date.isoformat(),
        "journal": str(getattr(ec.journal, "value", ec.journal)),
        "reference": ec.reference,
        "libelle": ec.libelle,
        "ligne_libelle": ligne.libelle,
        "compte": ligne.compte,
        "debit": float(ligne.debit or 0),
        "credit": float(ligne.credit or 0),
        "rapprochee": rapprochement_ligne_id is not None,
        "rapprochement_ligne_id": rapprochement_ligne_id,
    }


def _solde_comptable_fin(db: Session, sid: int, compte: str, date_fin: date) -> Decimal:
    """Solde du compte banque à la date de fin, depuis le début de l'exercice.

    Le report à nouveau du bilan est une écriture du début d'exercice ; on évite
    donc de sommer les exercices antérieurs, ce qui le compterait deux fois.
    """
    ex = _exercice_pour_date(db, sid, date_fin)
    debut = ex.date_debut if ex else date(date_fin.year, 1, 1)
    valeur = (
        db.query(
            func.coalesce(
                func.sum(
                    func.coalesce(models.LigneEcriture.debit, 0)
                    - func.coalesce(models.LigneEcriture.credit, 0)
                ),
                0,
            )
        )
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == sid,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
            models.Ecriture.date >= debut,
            models.Ecriture.date <= date_fin,
            models.LigneEcriture.compte == compte,
        )
        .scalar()
    )
    return Decimal(str(valeur or 0)).quantize(Decimal("0.01"))


def _solde_initial_periode_suivante(db: Session, sid: int, compte: str, debut: date):
    """Calcule l'ouverture à partir d'un relevé couvrant la veille.

    Un solde final déclaré n'est repris que si le relevé se termine la veille.
    Pour un relevé annuel englobant la date demandée, seul son solde initial
    et les mouvements *antérieurs* à la nouvelle période sont utilisés.
    Les montants restent indépendants des écritures comptables.
    """
    precedente = (
        db.query(models.RapprochementEtat)
        .filter(
            models.RapprochementEtat.societe_id == sid,
            models.RapprochementEtat.compte == compte,
            models.RapprochementEtat.date_fin >= debut - timedelta(days=1),
            models.RapprochementEtat.date_debut <= debut - timedelta(days=1),
        )
        .order_by(models.RapprochementEtat.date_debut.desc(), models.RapprochementEtat.date_fin.asc())
        .first()
    )
    if precedente is None:
        return None
    final_declare = (
        precedente.solde_final if precedente.solde_final is not None
        else precedente.solde_releve
    )
    if final_declare is not None and precedente.date_fin == debut - timedelta(days=1):
        return Decimal(str(final_declare)).quantize(Decimal("0.01"))
    if precedente.solde_initial is None:
        return None
    mouvements = (
        db.query(models.RapprochementLigne.sens, models.RapprochementLigne.montant)
        .filter(
            models.RapprochementLigne.societe_id == sid,
            models.RapprochementLigne.compte == compte,
            models.RapprochementLigne.date >= precedente.date_debut,
            models.RapprochementLigne.date < debut,
        )
        .all()
    )
    if any(not _montant_releve_exploitable(m) for _, m in mouvements):
        return None
    variation = sum(
        (Decimal(str(montant or 0)) if sens == "credit" else -Decimal(str(montant or 0))
         for sens, montant in mouvements),
        Decimal("0.00"),
    )
    return (Decimal(str(precedente.solde_initial)) + variation).quantize(Decimal("0.01"))


@router.get("/{compte}/situation")
def situation_rapprochement(
    compte: str,
    date_debut: date = Query(...),
    date_fin: date = Query(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if date_fin < date_debut:
        raise HTTPException(400, "La date de fin doit être postérieure à la date de début.")
    sid = current_user["societe_id"]

    relev = (
        db.query(models.RapprochementLigne)
        .filter(
            models.RapprochementLigne.societe_id == sid,
            models.RapprochementLigne.compte == compte,
            models.RapprochementLigne.date >= date_debut,
            models.RapprochementLigne.date <= date_fin,
        )
        .order_by(models.RapprochementLigne.date, models.RapprochementLigne.id)
        .all()
    )
    rapproche_par_ligne = {
        r.ecriture_ligne_id: r.id for r in db.query(models.RapprochementLigne).filter(
            models.RapprochementLigne.societe_id == sid,
            models.RapprochementLigne.rapprochee.is_(True),
            models.RapprochementLigne.ecriture_ligne_id.isnot(None),
        ).all()
    }

    liens_ventilation = ventilation.affectations(db, sid)
    rapproche_par_ligne.update({a['ecriture_ligne_id']: a['releve_id'] for a in liens_ventilation})
    releves_out = []
    for r in relev:
        out = _releve_out(r)
        liens = [a for a in liens_ventilation if a['releve_id'] == r.id]
        out['ecriture_ligne_ids'] = [a['ecriture_ligne_id'] for a in liens]
        out['ventilation_operation_id'] = str(liens[0]['operation_id']) if liens else None
        releves_out.append(out)

    compta = (
        db.query(models.LigneEcriture, models.Ecriture)
        .join(models.Ecriture, models.Ecriture.id == models.LigneEcriture.ecriture_id)
        .filter(
            models.Ecriture.societe_id == sid,
            models.Ecriture.est_validee.is_(True),
            models.Ecriture.numero_ecriture.isnot(None),
            models.Ecriture.date >= date_debut,
            models.Ecriture.date <= date_fin,
            models.LigneEcriture.compte == compte,
        )
        .order_by(models.Ecriture.date, models.Ecriture.id, models.LigneEcriture.id)
        .all()
    )

    etat = db.query(models.RapprochementEtat).filter_by(
        societe_id=sid, compte=compte, date_debut=date_debut, date_fin=date_fin
    ).first()

    # Compatibilité 047 : si l'utilisateur avait déjà saisi l'ancien solde
    # unique, on le traite comme solde final jusqu'à sa prochaine sauvegarde.
    solde_final = None
    if etat:
        solde_final = etat.solde_final if getattr(etat, "solde_final", None) is not None else etat.solde_releve
    suggestion = (_solde_initial_periode_suivante(db, sid, compte, date_debut)
                  if etat is None or etat.solde_initial is None else None)

    return {
        "compte": compte,
        "date_debut": date_debut.isoformat(),
        "date_fin": date_fin.isoformat(),
        "lecture_seule": _plage_est_cloturee(db, sid, date_debut, date_fin),
        "solde_initial": float(etat.solde_initial) if etat and getattr(etat, "solde_initial", None) is not None else None,
        "solde_initial_suggere": float(suggestion) if suggestion is not None else None,
        "solde_final": float(solde_final) if solde_final is not None else None,
        "solde_releve": float(solde_final) if solde_final is not None else None,
        "solde_comptable_final": float(_solde_comptable_fin(db, sid, compte, date_fin)),
        "lignes_releve": releves_out,
        "ventilations": ventilation.candidats(db, sid, compte, date_debut, date_fin),
        "ventilations_activees": ventilation.active(db),
        "ecritures": [_compta_out(l, e, rapproche_par_ligne.get(l.id)) for l, e in compta],
    }


@router.put("/{compte}/etat")
def enregistrer_etat_rapprochement(
    compte: str,
    data: EtatRapprochementIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    _assert_plage_modifiable(db, sid, data.date_debut, data.date_fin)

    etat = db.query(models.RapprochementEtat).filter_by(
        societe_id=sid, compte=compte, date_debut=data.date_debut, date_fin=data.date_fin
    ).first()
    if not etat:
        etat = models.RapprochementEtat(
            societe_id=sid, compte=compte, date_debut=data.date_debut, date_fin=data.date_fin
        )
        db.add(etat)

    final = data.solde_final if data.solde_final is not None else data.solde_releve
    etat.solde_initial = data.solde_initial
    etat.solde_final = final
    # Colonne historique gardée synchronisée pour les anciennes versions.
    etat.solde_releve = final
    etat.updated_by = current_user.get("id")
    etat.updated_at = datetime.utcnow()
    db.commit()
    return {
        "ok": True,
        "solde_initial": float(data.solde_initial) if data.solde_initial is not None else None,
        "solde_final": float(final) if final is not None else None,
    }


@router.post("/{ligne_id}/rapprocher")
def rapprocher_ligne(
    ligne_id: int,
    data: RapprocherIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    releve = _rapprocher_ligne_sans_commit(ligne_id, data, current_user, db)
    db.commit()
    db.refresh(releve)
    return releve


def _rapprocher_ligne_sans_commit(ligne_id, data, current_user, db):
    sid = current_user["societe_id"]
    ventilation.verrou(db, sid)
    releve = _ligne_releve(db, sid, ligne_id)
    compta, ec = _ligne_comptable(db, sid, data.ecriture_ligne_id)
    _assert_date_modifiable(db, sid, releve.date)
    _assert_date_modifiable(db, sid, ec.date)

    if releve.rapprochee and releve.ecriture_ligne_id != compta.id:
        raise HTTPException(409, "Dérapprochez cette ligne de relevé avant de choisir une autre écriture.")

    if releve.compte != compta.compte:
        raise HTTPException(409, "La ligne du relevé et la ligne comptable ne portent pas le même compte bancaire.")

    deja = db.query(models.RapprochementLigne).filter(
        models.RapprochementLigne.societe_id == sid,
        models.RapprochementLigne.ecriture_ligne_id == compta.id,
        models.RapprochementLigne.id != releve.id,
        models.RapprochementLigne.rapprochee.is_(True),
    ).first()
    if deja:
        raise HTTPException(409, "Cette ligne comptable est déjà rapprochée avec une autre ligne de relevé.")

    if any(a['releve_id'] == releve.id for a in ventilation.affectations(db, sid)):
        raise HTTPException(409, "Dérapprochez la ventilation avant de choisir une ligne individuelle.")
    ventilation.deja_pointees(db, sid, [compta.id], releve.id)

    if not _montant_releve_exploitable(releve.montant):
        raise HTTPException(409, "Le montant historique du relevé est inexploitable : vérifiez le justificatif avant tout pointage.")
    montant_releve = Decimal(str(releve.montant or 0)).quantize(Decimal("0.01"))
    sens = _sens_valide(releve.sens)
    # Relevé crédit = entrée d'argent = débit du compte banque en comptabilité.
    montant_compta = Decimal(str(compta.debit if sens == "credit" else compta.credit or 0)).quantize(Decimal("0.01"))
    if abs(montant_releve - montant_compta) > Decimal("0.01"):
        attendu = "débit" if sens == "credit" else "crédit"
        raise HTTPException(
            409,
            f"Montants incompatibles : relevé {montant_releve:.2f} MAD, {attendu} comptable {montant_compta:.2f} MAD.",
        )

    releve.ecriture_ligne_id = compta.id
    releve.reglement_id = None
    releve.rapprochee = True
    releve.date_rapprochement = datetime.utcnow()
    releve.rapproche_par = current_user.get("id")
    db.flush()
    return releve


@router.get("/{compte}/propositions")
def proposer_rapprochements(
    compte: str, date_debut: date = Query(...), date_fin: date = Query(...),
    current_user=Depends(get_current_user), db: Session = Depends(get_db),
):
    return construire_propositions(situation_rapprochement(compte, date_debut, date_fin, current_user, db))


@router.post("/{compte}/rapprocher-propositions")
def confirmer_rapprochements(
    compte: str, data: ConfirmerPropositionsIn,
    current_user=Depends(requiert_ecriture), db: Session = Depends(get_db),
):
    sid=current_user['societe_id']
    try:
        ventilation.verrou(db,sid)
        _assert_plage_modifiable(db,sid,data.date_debut,data.date_fin)
        courant=proposer_rapprochements(compte,data.date_debut,data.date_fin,current_user,db)
        if courant['empreinte']!=data.empreinte:
            raise HTTPException(409,"La situation bancaire a changé. Recalculez les propositions avant de confirmer.")
        par_id={p['releve_id']:p for p in courant['propositions']}
        if len(set(data.releve_ids))!=len(data.releve_ids) or any(i not in par_id for i in data.releve_ids):
            raise HTTPException(409,"La sélection doit contenir seulement des propositions uniques de cette situation.")
        for rid in sorted(data.releve_ids):
            p=par_id[rid]
            if p['operation_id']:
                releve=_ligne_releve(db,sid,rid)
                ventilation.rapprocher(db,sid,releve,p['operation_id'],current_user.get('id'))
            else:
                _rapprocher_ligne_sans_commit(rid,RapprocherIn(ecriture_ligne_id=p['ecriture_ligne_id']),current_user,db)
        db.commit()
        return {'ok':True,'nb_rapprochees':len(data.releve_ids),'releve_ids':sorted(data.releve_ids)}
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,"Un contrôle comptable a refusé le pointage. Aucun pointage de cette sélection n'a été enregistré.") from exc
    except Exception:
        db.rollback()
        raise


@router.post("/{ligne_id}/rapprocher-ventilation")
def rapprocher_ventilation(
    ligne_id: int,
    data: RapprocherVentilationIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    try:
        ventilation.verrou(db, sid)
        releve = _ligne_releve(db, sid, ligne_id)
        resultat = ventilation.rapprocher(db, sid, releve, data.operation_id, current_user.get('id'))
        db.commit()
        return {"ok": True, "releve_id": releve.id, **resultat}
    except Exception:
        db.rollback()
        raise


@router.post("/{ligne_id}/derapprocher")
def derapprocher_ligne(
    ligne_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    ventilation.verrou(db, sid)
    releve = _ligne_releve(db, sid, ligne_id)
    _assert_date_modifiable(db, sid, releve.date)
    if releve.ecriture_ligne_id:
        _, ec = _ligne_comptable(db, sid, releve.ecriture_ligne_id)
        _assert_date_modifiable(db, sid, ec.date)
    ventilation.depointer(db, sid, releve)
    releve.ecriture_ligne_id = None
    releve.reglement_id = None
    releve.rapprochee = False
    releve.date_rapprochement = None
    releve.rapproche_par = None
    db.commit()
    db.refresh(releve)
    return releve


@router.post("/import", status_code=201)
def importer_lignes(
    data: ImportRapprochementIn,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    # Validation complète avant toute insertion : pas d'import partiel si une
    # ligne appartient à un exercice clôturé.
    for item in data.lignes:
        _assert_date_modifiable(db, sid, item.date)
        _sens_valide(item.sens)
        _montant_releve_valide(item.montant)

    creees = []
    ignorees = 0
    for item in data.lignes:
        sens = _sens_valide(item.sens)
        montant = float(_montant_releve_valide(item.montant))
        libelle = (item.libelle or "").strip() or None
        existe = db.query(models.RapprochementLigne.id).filter_by(
            societe_id=sid, compte=data.compte, date=item.date,
            libelle=libelle, montant=montant, sens=sens,
        ).first()
        if existe:
            ignorees += 1
            continue
        ligne = models.RapprochementLigne(
            societe_id=sid, compte=data.compte, date=item.date,
            libelle=libelle, montant=montant, sens=sens,
        )
        db.add(ligne)
        creees.append(ligne)
    db.commit()
    for ligne in creees:
        db.refresh(ligne)
    return {"nb_creees": len(creees), "nb_ignorees": ignorees, "lignes": creees}


@router.get("/{compte}", response_model=List[LigneReleveLectureOut])
def lister_lignes(
    compte: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    lignes = db.query(models.RapprochementLigne).filter_by(
        societe_id=current_user["societe_id"],
        compte=compte,
    ).order_by(models.RapprochementLigne.date, models.RapprochementLigne.id).all()
    return [_releve_out(ligne) for ligne in lignes]


@router.post("", response_model=schemas.RapprochementLigneOut, status_code=201)
def ajouter_ligne(
    data: schemas.RapprochementLigneCreate,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    _assert_date_modifiable(db, sid, data.date)
    payload = data.model_dump()
    payload["sens"] = _sens_valide(payload.get("sens"))
    payload["montant"] = float(_montant_releve_valide(payload.get("montant")))
    ligne = models.RapprochementLigne(
        societe_id=sid,
        **payload,
    )
    db.add(ligne)
    db.commit()
    db.refresh(ligne)
    return ligne


@router.patch("/{ligne_id}", response_model=schemas.RapprochementLigneOut)
def modifier_ligne(
    ligne_id: int,
    data: schemas.RapprochementLigneUpdate,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    ventilation.verrou(db, sid)
    ligne = _ligne_releve(db, sid, ligne_id)
    _assert_date_modifiable(db, sid, ligne.date)

    payload = data.model_dump(exclude_unset=True)
    champs_metier = {"date", "libelle", "montant", "sens"}.intersection(payload)
    if champs_metier and (ligne.rapprochee or ligne.ecriture_ligne_id):
        raise HTTPException(409, "Dérapprochez cette ligne avant de modifier son contenu.")

    if data.rapprochee is True:
        raise HTTPException(400, "Utilisez /{ligne_id}/rapprocher avec une ligne comptable explicite.")
    if data.rapprochee is False:
        # Le raccourci PATCH doit respecter le même verrou d'archive que la
        # route dédiée : une écriture clôturée ne perd pas son rapprochement.
        if ligne.ecriture_ligne_id:
            _, ec = _ligne_comptable(db, sid, ligne.ecriture_ligne_id)
            _assert_date_modifiable(db, sid, ec.date)
        ventilation.depointer(db, sid, ligne)
        ligne.ecriture_ligne_id = None
        ligne.reglement_id = None
        ligne.rapprochee = False
        ligne.date_rapprochement = None
        ligne.rapproche_par = None

    if "date" in payload and payload["date"] is not None:
        _assert_date_modifiable(db, sid, payload["date"])
        ligne.date = payload["date"]
    if "libelle" in payload:
        ligne.libelle = (payload["libelle"] or "").strip() or None
    if "montant" in payload and payload["montant"] is not None:
        ligne.montant = float(_montant_releve_valide(payload["montant"]))
    if "sens" in payload and payload["sens"] is not None:
        ligne.sens = _sens_valide(payload["sens"])

    db.commit()
    db.refresh(ligne)
    return ligne


@router.delete("/{ligne_id}", status_code=204)
def supprimer_ligne(
    ligne_id: int,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    sid = current_user["societe_id"]
    ventilation.verrou(db, sid)
    ligne = _ligne_releve(db, sid, ligne_id)
    _assert_date_modifiable(db, sid, ligne.date)
    if ligne.rapprochee or ligne.ecriture_ligne_id:
        raise HTTPException(409, "Dérapprochez cette ligne avant de la supprimer.")
    db.delete(ligne)
    db.commit()
