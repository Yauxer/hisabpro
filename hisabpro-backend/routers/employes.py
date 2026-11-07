from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from typing import List, Optional
from database import get_db
from auth import get_current_user, requiert_ecriture, exiger_admin
from datetime import date
from calendar import monthrange
from decimal import Decimal
from services.paie_service import simuler_salaire, verifier_parametres, AVERTISSEMENTS, SOURCES
from services.parametres_paie_service import sortie_taux_cotisation
from services.paie_referentiel_service import ConsignationPaie, lire_referentiel, consigner_referentiel
from services.personnel_acces_service import exiger_lecture, exiger_mutation_historique, sortie_employe, reponse_privee
import models, schemas

router = APIRouter(prefix="/api/employes", tags=["employes"], dependencies=[Depends(reponse_privee)])
from routers.avances_salaries import router as avances_router
router.include_router(avances_router)
from routers.personnel_habilitations import router as habilitations_router
router.include_router(habilitations_router)
from routers.personnel_workflow import router as personnel_router
router.include_router(personnel_router)


def dossiers_controles(db,sid):
    if db.bind.dialect.name=='postgresql' and db.scalar(text("SELECT to_regclass('public.personnel_dossiers') IS NOT NULL")):
        return set(db.scalars(text('SELECT employe_id FROM personnel_dossiers WHERE societe_id=:s'),{'s':sid}))
    return set()


def enregistrer_dossier_historique(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, 'pgcode', None) in {'23503', '23505', '23514'}:
            raise HTTPException(409, 'Dossier Personnel lié ou données en conflit. Rechargez et utilisez le circuit contrôlé.') from exc
        raise


@router.get("", response_model=List[schemas.EmployeOut])
def lister_employes(
    inclure_archives: bool = False,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    acces = exiger_lecture(db, current_user, 'personnel.lire_identite')
    query = db.query(models.Employe).filter_by(societe_id=current_user["societe_id"])
    if not inclure_archives:
        query = query.filter_by(actif=True)
    controles=dossiers_controles(db,current_user['societe_id']) if acces['mode']=='protege' else set()
    result=[]
    for emp in query.order_by(models.Employe.created_at.desc(),models.Employe.id.desc()).all():
        row=sortie_employe(emp,acces)
        # Le flottant historique n'est pas le salaire contractuel approuvé.
        if emp.id in controles:row=row.model_copy(update={'salaire_brut':None})
        result.append(row)
    return result


@router.post("", response_model=schemas.EmployeOut, status_code=201)
def creer_employe(
    data: schemas.EmployeCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    exiger_mutation_historique(db, current_user)
    emp = models.Employe(societe_id=current_user["societe_id"], **data.model_dump())
    db.add(emp)
    enregistrer_dossier_historique(db)
    db.refresh(emp)
    return emp


@router.get("/cotisations")
def cotisations_masse_salariale(
    annee: int = Query(..., ge=2025, le=2100),
    mois: int = Query(default=1, ge=1, le=12),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Préparation indicative du mois demandé, sans repli d'année ni écriture."""
    acces = exiger_lecture(db, current_user, 'personnel.lire_identite', 'personnel.lire_remuneration')
    employes = db.query(models.Employe).filter_by(
        societe_id=current_user["societe_id"], actif=True
    ).all()
    if acces['mode']=='protege' and dossiers_controles(db,current_user['societe_id']) & {e.id for e in employes}:
        raise HTTPException(409,'Dossiers Personnel contrôlés :consulter les rémunérations approuvées à date ;cette simulation historique est indisponible.')

    taux = db.query(models.TauxCotisation).filter_by(annee=annee).order_by(models.TauxCotisation.code).all()
    bareme = db.query(models.BaremeIR).filter_by(annee=annee).order_by(models.BaremeIR.tranche_min).all()
    deductions = db.query(models.DeductionIR).filter_by(annee=annee).order_by(models.DeductionIR.code).all()
    blocages = verifier_parametres(taux, bareme, deductions)
    debut, fin = date(annee, mois, 1), date(annee, mois, monthrange(annee, mois)[1])
    resultats = []
    totaux = {
        "salaire_brut": Decimal(0), "total_retenues_sal": Decimal(0), "ir": Decimal(0),
        "salaire_net": Decimal(0), "total_charges_pat": Decimal(0), "cout_employeur": Decimal(0)
    }

    for emp in employes:
        if (emp.date_embauche and emp.date_embauche > fin) or (emp.date_sortie and emp.date_sortie < debut):
            continue
        erreurs = list(blocages)
        if (emp.date_embauche and debut < emp.date_embauche <= fin) or (emp.date_sortie and debut <= emp.date_sortie < fin):
            erreurs.append('Entrée ou sortie en cours de mois : proratisation à établir')
        calc = None
        if not erreurs:
            try:
                calc = simuler_salaire(emp, taux, bareme, deductions)
            except ValueError as exc:
                erreurs.append(str(exc))
        resultats.append({"employe": sortie_employe(emp, acces), "cotisations": calc, "blocages": erreurs})
        if calc is not None:
            for k in totaux:
                totaux[k] += calc[k]
    incomplet = bool(blocages) or any(row['blocages'] for row in resultats)
    return {"employes": resultats, "totaux": None if incomplet else totaux, "annee_taux": annee,
            "mois": mois, "statut": "bloque" if incomplet else "simulation", "blocages": blocages,
            "avertissements": AVERTISSEMENTS, "sources": SOURCES,
            "parametres": {"taux": [sortie_taux_cotisation(t) for t in taux], "bareme": bareme, "deductions": deductions}}


@router.get("/referentiel")
def consulter_referentiel_paie(
    annee: int = Query(..., ge=2025, le=2100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    acces = exiger_lecture(db, current_user, 'personnel.audit_lire')
    resultat = lire_referentiel(db, current_user, annee)
    if acces['mode'] == 'protege':
        resultat['peut_consigner'] = False
    return resultat


@router.post("/referentiel", status_code=201)
def consigner_referentiel_paie(
    data: ConsignationPaie,
    annee: int = Query(..., ge=2025, le=2100),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    exiger_admin(current_user)
    exiger_mutation_historique(db, current_user)
    return consigner_referentiel(db, current_user, annee, data)


@router.put("/{employe_id}", response_model=schemas.EmployeOut)
def modifier_employe(
    employe_id: int,
    data: schemas.EmployeCreate,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    exiger_mutation_historique(db, current_user)
    emp = db.query(models.Employe).filter_by(
        id=employe_id, societe_id=current_user["societe_id"]
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employé introuvable")
    for k, v in data.model_dump().items():
        setattr(emp, k, v)
    enregistrer_dossier_historique(db)
    db.refresh(emp)
    return emp


@router.delete("/{employe_id}", status_code=204)
def supprimer_employe(
    employe_id: int,
    current_user = Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    exiger_mutation_historique(db, current_user)
    emp = db.query(models.Employe).filter_by(
        id=employe_id, societe_id=current_user["societe_id"]
    ).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employé introuvable")
    emp.actif = False
    db.commit()
