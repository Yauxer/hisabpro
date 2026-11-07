from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import paie_bases_fiscales_service as service
from services.paie_bases_fiscales_schemas import Simulation

router=APIRouter(prefix='/preparations',tags=['Paie : préparation des bases fiscales'])

@router.get('')
def lister(decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lister(db,user,decalage,limite)

@router.get('/options')
def options(social_id:int=Query(...,gt=0),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.options(db,user,social_id)

@router.get('/{ident}')
def lire(ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lire(db,user,ident)

@router.post('',status_code=201)
def simuler(data:Simulation,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.simuler(db,user,data)
