"""Bulletins, avances/prêts, comptabilisation, paiements et états de paie (lot 968)."""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, requiert_personnel_ecriture
from services import paie_bulletins_service as service
from services.paie_bulletins_service import Creation, Annulation, Comptabilisation, Paiement, Avance
from services import paie_mois_service

router = APIRouter(prefix='/paie', tags=['Paie : bulletins, paiements et comptabilisation'])


@router.get('/bulletins')
def lister(periode: date | None = None, annee: int | None = Query(None, ge=2000, le=2100),
           user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.lister(db, user, periode, annee)


@router.get('/bulletins/apercu')
def apercu(controle_id: int = Query(gt=0), user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.apercu(db, user, controle_id)


@router.get('/bulletins/{ident}')
def lire(ident: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.lire(db, user, ident)


@router.post('/bulletins', status_code=201)
def creer(data: Creation, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.creer(db, user, data)


@router.post('/bulletins/{ident}/annuler')
def annuler(ident: int, data: Annulation, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.annuler(db, user, ident, data)


@router.post('/comptabiliser', status_code=201)
def comptabiliser(data: Comptabilisation, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.comptabiliser(db, user, data)


@router.post('/paiements', status_code=201)
def payer(data: Paiement, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.payer(db, user, data)


@router.post('/calculer-mois')
def calculer_mois(data: paie_mois_service.Demande, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    """Lot 976 : brut, cotisations, bases fiscales, IR et bulletins du mois en une fois."""
    return paie_mois_service.calculer_mois(db, user, data)


@router.get('/etats')
def etats(annee: int = Query(ge=2000, le=2100), user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.etats(db, user, annee)


@router.get('/salaries')
def salaries(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.salaries(db, user)


@router.get('/avances')
def lister_avances(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return service.lister_avances(db, user)


@router.post('/avances', status_code=201)
def creer_avance(data: Avance, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.creer_avance(db, user, data)


@router.post('/avances/{ident}/annuler')
def annuler_avance(ident: int, data: Annulation, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.annuler_avance(db, user, ident, data)


@router.post('/avances/{ident}/comptabiliser', status_code=201)
def comptabiliser_avance(ident: int, user=Depends(requiert_personnel_ecriture), db: Session = Depends(get_db)):
    return service.comptabiliser_avance(db, user, ident)
