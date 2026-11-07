from datetime import date
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import paie_social_service as service
from services.paie_social_schemas import Creation,Version,Decision

router=APIRouter(prefix='/social',tags=['Paie :référentiel social'])
from routers.paie_social_calcul import router as calcul_router
router.include_router(calcul_router)
@router.get('')
def lister(au:date=Query(default_factory=date.today),recherche:str|None=Query(None,max_length=150),decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),regime:str|None=Query(None,pattern=r'^[A-Z][A-Z0-9_]{1,79}$'),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lister(db,user,au,recherche,decalage,limite,regime)

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

