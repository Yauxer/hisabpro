from fastapi import APIRouter,Depends,Query,Response
from typing import Literal
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import paie_ir_annuel_service as service
from services.paie_ir_annuel_schemas import Simulation
from services.paie_ir_source_annuelle_schemas import Creation as SourceAnnuelle

router=APIRouter(prefix='/fiscalite',tags=['Paie : contrôle annuel pédagogique IR'])
from routers.paie_ir_mensuel import router as mensuel_router
router.include_router(mensuel_router)
from routers.paie_bases_fiscales import router as bases_router
router.include_router(bases_router)
from routers.paie_frais_annuels import router as frais_router
router.include_router(frais_router)

@router.get('')
def lister(decalage:int=Query(0,ge=0),limite:int=Query(25,ge=1,le=100),user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lister(db,user,decalage,limite)

@router.get('/referentiel')
def referentiel(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.referentiel(db,user)

@router.get('/{ident}')
def lire(ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return service.lire(db,user,ident)

@router.post('',status_code=201)
def simuler(data:Simulation,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    return service.simuler(db,user,data)

@router.post('/depuis-frais-annuels',status_code=201)
def depuis_frais(data:SourceAnnuelle,user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    from services.paie_ir_source_annuelle_service import simuler
    return simuler(db,user,data)

@router.get('/{ident}/export/{format}')
def exporter(ident:int,format:Literal['pdf','xlsx'],user=Depends(get_current_user),db:Session=Depends(get_db)):
    from services.paie_ir_documents_service import exporter as document
    contenu=document(db,user,ident,format)
    return Response(contenu,media_type='application/pdf' if format=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={
        'Content-Disposition':f'attachment; filename="controle_ir_annuel_{ident}.{format}"',
        'Cache-Control':'no-store','Pragma':'no-cache','X-Content-Type-Options':'nosniff',
        'Access-Control-Expose-Headers':'Content-Disposition'})
