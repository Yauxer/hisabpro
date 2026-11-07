"""API de dossiers sous capacités, avec profil Personnel cloisonné ;aucun calcul de paie."""
from datetime import date
from typing import Literal
from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_personnel_ecriture
from services import personnel_workflow_service as service
from services.personnel_workflow_schemas import Creation,Reprise,Proposition,Revision,Decision

router=APIRouter(prefix='/personnel',tags=['Personnel : dossiers et approbations'])
from routers.personnel_coffre import router as coffre_router
router.include_router(coffre_router)
from routers.paie_catalogue import router as catalogue_router
router.include_router(catalogue_router)
from routers.paie_campagnes import router as campagnes_router
router.include_router(campagnes_router)
from routers.paie_social import router as social_router
router.include_router(social_router)
from routers.paie_ir_annuel import router as ir_router
router.include_router(ir_router)
from routers.paie_bulletins import router as bulletins_router
router.include_router(bulletins_router)


@router.get('')
def lister(au: date=Query(default_factory=date.today),recherche: str|None=Query(None,max_length=150),
           statut: Literal['BROUILLON','A_VALIDER','ACTIF','SUSPENDU','SORTI']|None=None,
           decalage: int=Query(0,ge=0),limite: int=Query(25,ge=1,le=100),
           user=Depends(get_current_user),db: Session=Depends(get_db)):
    return service.lister(db,user,au,recherche,statut,decalage,limite)


@router.post('',status_code=201)
def creer(data: Creation,user=Depends(requiert_personnel_ecriture),db: Session=Depends(get_db)):
    return service.creer(db,user,data)


@router.post('/reprises',status_code=201)
def reprendre(data: Reprise,user=Depends(requiert_personnel_ecriture),db: Session=Depends(get_db)):
    return service.creer(db,user,data,reprise=True)


@router.get('/contexte')
def contexte_personnel(user=Depends(get_current_user),db: Session=Depends(get_db)):
    from sqlalchemy import text
    from services.personnel_acces_service import contexte
    ctx=contexte(db,user)
    societe=db.execute(text('SELECT id,raison_sociale FROM societes WHERE id=:s'),{'s':user['societe_id']}).mappings().one()
    return {'societe':dict(societe),'module_actif':ctx['module_actif']}


@router.get('/options')
def options(user=Depends(get_current_user),db: Session=Depends(get_db)):
    return service.options_saisie(db,user)


@router.get('/demandes')
def demandes(statut: Literal['BROUILLON','SOUMIS','APPROUVE','REJETE']|None=None,
             employe_id: int|None=Query(None,gt=0),decalage: int=Query(0,ge=0),limite: int=Query(25,ge=1,le=100),
             user=Depends(get_current_user),db: Session=Depends(get_db)):
    return service.lister_demandes(db,user,statut,employe_id,decalage,limite)


@router.get('/demandes/{ident}')
def demande(ident: int,user=Depends(get_current_user),db: Session=Depends(get_db)):
    return service.lire_demande(db,user,ident)


@router.post('/demandes/{ident}/soumettre')
def soumettre(ident: int,data: Revision,user=Depends(requiert_personnel_ecriture),db: Session=Depends(get_db)):
    return service.soumettre(db,user,ident,data)


@router.post('/demandes/{ident}/approuver')
def approuver(ident: int,data: Decision,user=Depends(requiert_personnel_ecriture),db: Session=Depends(get_db)):
    return service.decider(db,user,ident,data)


@router.post('/demandes/{ident}/rejeter')
def rejeter(ident: int,data: Decision,user=Depends(requiert_personnel_ecriture),db: Session=Depends(get_db)):
    return service.decider(db,user,ident,data,approuver=False)


@router.get('/{employe_id}/historique')
def historique(employe_id: int,decalage: int=Query(0,ge=0),limite: int=Query(25,ge=1,le=100),
               user=Depends(get_current_user),db: Session=Depends(get_db)):
    return service.historique(db,user,employe_id,decalage,limite)


@router.post('/{employe_id}/modifications',status_code=201)
def proposer(employe_id: int,data: Proposition,user=Depends(requiert_personnel_ecriture),db: Session=Depends(get_db)):
    return service.proposer(db,user,employe_id,data)


@router.get('/{employe_id}')
def lire(employe_id: int,au: date=Query(default_factory=date.today),user=Depends(get_current_user),db: Session=Depends(get_db)):
    return service.lire(db,user,employe_id,au)
