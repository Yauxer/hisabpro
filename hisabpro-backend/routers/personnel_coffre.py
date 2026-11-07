"""Coffre RH :pas d'URL publique,ni de nom de fichier personnel conservé."""
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Response,Request
from sqlalchemy.orm import Session
from pydantic import BaseModel,ConfigDict,Field
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect
from database import get_db
from auth import get_current_user,requiert_admin,requiert_personnel_ecriture
from services import personnel_coffre_service as coffre

router=APIRouter(prefix='/coffre',tags=['Personnel :coffre privé'])

class Politique(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    reference_garde_cles:str=Field(min_length=1,max_length=200)
    reference_conservation:str=Field(min_length=1,max_length=200)
    reference_rotation_sauvegarde:str=Field(min_length=1,max_length=200)
    motif:str=Field(min_length=1,max_length=500)
    confirmation:Literal['DECLARER_POLITIQUE_COFFRE_RH']

@router.get('')
def etat(user=Depends(get_current_user),db:Session=Depends(get_db)):
    return coffre.etat(db,user)

@router.post('/politique',status_code=201)
def declarer(data:Politique,user=Depends(requiert_admin),db:Session=Depends(get_db)):
    return coffre.declarer(db,user,data)

@router.get('/{eid}/pieces')
def pieces(eid:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return coffre.lister(db,user,eid)

@router.post('/{eid}/pieces',status_code=201)
async def deposer(eid:int,request:Request,categorie:Literal['contrat','banque','autre'],
                  user=Depends(requiert_personnel_ecriture),db:Session=Depends(get_db)):
    # Corps binaire borné en mémoire :aucun spool multipart en clair sur disque.
    await run_in_threadpool(coffre.collecte,db,user,eid)
    contenu=bytearray()
    try:
        async for morceau in request.stream():
            if len(contenu)+len(morceau)>coffre.MAX_PIECE:raise HTTPException(413,'La pièce dépasse la limite de4Mio.')
            contenu.extend(morceau)
        return await run_in_threadpool(coffre.deposer,db,user,eid,categorie,bytes(contenu))
    except ClientDisconnect:raise HTTPException(400,'Transfert de la pièce interrompu ;aucun dépôt enregistré.') from None

@router.get('/{eid}/pieces/{ident}')
def telecharger(eid:int,ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    brut,mime=coffre.telecharger(db,user,eid,ident)
    extension={'application/pdf':'pdf','image/png':'png','image/jpeg':'jpg'}[mime]
    return Response(brut,media_type=mime,headers={'Content-Disposition':f'attachment; filename="piece-personnel-{ident}.{extension}"',
       'Cache-Control':'no-store','Pragma':'no-cache','X-Content-Type-Options':'nosniff'})

@router.get('/{eid}/banque/{ident}/reveler')
def banque(eid:int,ident:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    return coffre.reveler_banque(db,user,eid,ident)
