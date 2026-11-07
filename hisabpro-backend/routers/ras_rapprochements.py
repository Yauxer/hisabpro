from decimal import Decimal, InvalidOperation
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from auth import get_current_user, requiert_ecriture
from database import get_db
from services.ventes_preparation_service import preparer_lecture
from services import ras_rapprochement_service as service
import models

router=APIRouter(prefix='/ras/captures/{cid}/rapprochements',tags=['RAS rapprochement documentaire'])


def lecture(db:Session=Depends(get_db)):
    return preparer_lecture(db)


class Creation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    ecriture_id:int=Field(gt=0,strict=True)
    montant:Decimal
    cle:UUID
    rapprochement_verifie:bool=Field(strict=True)

    @field_validator('montant',mode='before')
    @classmethod
    def fini(cls,v):
        try:
            if isinstance(v,bool):raise ValueError()
            d=Decimal(str(v))
            if not d.is_finite() or not 0<d<Decimal('1e16') or d!=d.quantize(Decimal('.01')):raise ValueError()
            return d
        except (ValueError,InvalidOperation):raise ValueError('Montant positif, fini, au centime requis.')


class Retrait(BaseModel):
    model_config=ConfigDict(extra='forbid')
    motif:str=Field(min_length=1,max_length=500)

    @field_validator('motif')
    @classmethod
    def non_vide(cls,v):
        v=v.strip()
        if not v:raise ValueError('Motif de retrait requis.')
        return v


@router.get('')
def consulter(cid:int,db:Session=Depends(lecture),user=Depends(get_current_user)):
    return service.lire(db,user['societe_id'],cid)


@router.get('/options')
def options(cid:int,recherche:str=Query('',max_length=100),page:int=Query(1,ge=1),
    db:Session=Depends(lecture),user=Depends(get_current_user)):
    return service.options(db,user['societe_id'],cid,recherche,page)


@router.get('/pdf')
def pdf(cid:int,db:Session=Depends(lecture),user=Depends(get_current_user)):
    from services.ras_rapprochement_pdf import generer
    data=service.lire(db,user['societe_id'],cid)
    societe=db.query(models.Societe).filter_by(id=user['societe_id']).one()
    return Response(generer(data,societe),media_type='application/pdf',headers={
        'Content-Disposition':f'attachment; filename="Rapprochements_RAS_capture_{cid}.pdf"',
        'Access-Control-Expose-Headers':'Content-Disposition'})


@router.post('',status_code=201)
def creer(cid:int,data:Creation,db:Session=Depends(get_db),user=Depends(requiert_ecriture)):
    try:return service.enregistrer(db,user,cid,data)
    except IntegrityError as exc:
        db.rollback();raise HTTPException(409,'Le rapprochement ne recoupe plus les sources ou sa capacité. Actualisez avant de recommencer.') from exc


@router.post('/{rid}/retirer')
def retirer(cid:int,rid:int,data:Retrait,db:Session=Depends(get_db),user=Depends(requiert_ecriture)):
    try:return service.retirer(db,user,cid,rid,data.motif)
    except IntegrityError as exc:
        db.rollback();raise HTTPException(409,'Retrait incompatible avec le rapprochement conservé. Actualisez.') from exc
