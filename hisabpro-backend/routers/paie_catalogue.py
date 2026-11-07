from datetime import date
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import paie_catalogue_service as service
from services.paie_catalogue_schemas import Creation,Version,Decision,Apercu

router=APIRouter(prefix='/elements',tags=['Paie :catalogue et versions'])
from routers.paie_variables import router as variables_router
router.include_router(variables_router)

@router.get('')
def lister(au:date=Query(default_factory=date.today),recherche:str|None=Query(None,max_length=150),decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lister(db,user,au,recherche,decalage,limite)

@router.post('',status_code=201)
def creer(data:Creation,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.creer(db,user,data)

@router.get('/{ident}')
def lire(ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lire(db,user,ident)

@router.post('/{ident}/versions',status_code=201)
def proposer(ident:int,data:Version,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.proposer(db,user,ident,data)

@router.post('/versions/{ident}/approuver')
def approuver(ident:int,data:Decision,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.decider(db,user,ident,data,True)

@router.post('/versions/{ident}/rejeter')
def rejeter(ident:int,data:Decision,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.decider(db,user,ident,data,False)

@router.post('/versions/{ident}/apercu')
def apercu(ident:int,data:Apercu,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.apercu(db,user,ident,data)
