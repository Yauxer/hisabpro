from datetime import date
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import paie_campagnes_service as service,personnel_workflow_service as workflow
from services.paie_campagnes_schemas import Simulation

router=APIRouter(prefix='/traitement',tags=['Paie :campagnes etbrut simulé'])

@router.get('')
def lister(decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lister(db,user,decalage,limite)

@router.get('/options')
def options(au:date=Query(default_factory=date.today),recherche:str|None=Query(None,max_length=150),decalage:int=Query(0,ge=0),user=Depends(get_current_user),db:Session=Depends(get_db)):
    service.autoriser(db,user);q=workflow.lister(db,user,au,recherche,None,decalage,25)
    return {'total':q['total'],'elements':[{'id':r['employe_id'],'nom':r['nom'],'matricule':r['matricule'],'date_entree':r['date_embauche'],'remuneration':r['remuneration']} for r in q['elements']]}

@router.post('/simulations',status_code=201)
def simuler(data:Simulation,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.simuler(db,user,data)

@router.get('/simulations/{ident}')
def lire(ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lire(db,user,ident)

@router.get('/campagnes/{ident}/historique')
def historique(ident:int,decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.historique(db,user,ident,decalage,limite)
