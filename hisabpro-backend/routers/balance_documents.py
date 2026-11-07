from uuid import UUID
import mimetypes
from fastapi import APIRouter,Depends,UploadFile,File,Form,HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
from auth import get_current_user,requiert_ecriture
from database import get_db
from services import balance_documents_service as service

router=APIRouter(prefix='/liasse/balance/dossiers/{preparation_id}/documents',tags=['Justificatifs des balances'])


@router.get('')
def liste(preparation_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    return service.lire(db,user['societe_id'],preparation_id)


@router.post('',status_code=201)
async def ajouter(preparation_id:int,file:UploadFile=File(...),cle:UUID=Form(...),
                  empreinte:str=Form(...,pattern=r'^[a-f0-9]{64}$'),reference:str=Form('',max_length=500),
                  db:Session=Depends(get_db),user=Depends(requiert_ecriture)):
    try:return await service.ajouter(db,user,preparation_id,file,cle,empreinte,reference)
    except FileExistsError as exc:
        db.rollback();raise HTTPException(409,'Un fichier existe déjà pour cette demande sans trace correspondante ; vérifiez le stockage.') from exc
    except DBAPIError as exc:
        db.rollback();raise HTTPException(409,'Justificatif refusé par les contrôles de traçabilité ; aucun fichier nouveau conservé.') from exc
    finally:await file.close()


@router.get('/{document_id}')
def telecharger(preparation_id:int,document_id:int,db:Session=Depends(get_db),user=Depends(get_current_user)):
    data=service.lire(db,user['societe_id'],preparation_id)
    r=next((r for r in data['documents'] if r['id']==document_id),None)
    if not r:raise HTTPException(404,'Justificatif introuvable dans cette préparation.')
    raw=service.octets(user['societe_id'],preparation_id,r)
    return Response(raw,media_type=mimetypes.guess_type(r['nom_stockage'])[0] or 'application/octet-stream',headers={
        'Content-Disposition':f'attachment; filename="{r["nom_stockage"]}"',
        'Access-Control-Expose-Headers':'Content-Disposition','Cache-Control':'no-store'})
