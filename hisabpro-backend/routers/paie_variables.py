from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import paie_variables_service as service
from services.paie_variables_schemas import Creation,Motif,Decision

router=APIRouter(prefix='/variables',tags=['Paie :variables mensuelles'])

@router.get('')
def lister(periode:date|None=None,statut:Literal['BROUILLON','SOUMIS','APPROUVE','REJETE','ANNULE']|None=None,employe_id:int|None=Query(None,gt=0),decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lister(db,user,periode,statut,employe_id,decalage,limite)

@router.get('/options')
def options(au:date=Query(default_factory=date.today),recherche_salarie:str|None=Query(None,max_length=150),recherche_rubrique:str|None=Query(None,max_length=150),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.options(db,user,au,recherche_salarie,recherche_rubrique)

@router.get('/{ident}')
def lire(ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lire(db,user,ident)

@router.post('',status_code=201)
def creer(data:Creation,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.creer(db,user,data)

@router.post('/{ident}/soumettre')
def soumettre(ident:int,data:Motif,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.transition(db,user,ident,data,'soumettre')

@router.post('/{ident}/annuler')
def annuler(ident:int,data:Motif,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.transition(db,user,ident,data,'annuler')

@router.post('/{ident}/approuver')
def approuver(ident:int,data:Decision,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.transition(db,user,ident,data,'approuver')

@router.post('/{ident}/rejeter')
def rejeter(ident:int,data:Decision,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.transition(db,user,ident,data,'rejeter')
