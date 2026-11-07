"""Lecture cohérente du registre interne et exports, sur une seule connexion."""
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
import models
from services.ventes_preparation_service import preparer_lecture
from services.ras_tva_registre_service import construire
from services.ras_tva_preparation_service import construire as preparer
from services.ras_tva_registre_export_service import csv_bytes, xlsx_bytes, pdf_bytes

router=APIRouter()


def lecture(db:Session=Depends(get_db)):
    return preparer_lecture(db)


@router.get('/ras/preparation/{annee}/{mois}')
def preparation(annee:Annotated[int,Path(ge=2026,le=9999)],mois:Annotated[int,Path(ge=1,le=12)],
    db:Session=Depends(lecture),user=Depends(get_current_user)):
    return preparer(db,user['societe_id'],annee,mois)


@router.get('/ras/preparation/{annee}/{mois}/export/{format_export}')
def exporter_preparation(annee:Annotated[int,Path(ge=2026,le=9999)],mois:Annotated[int,Path(ge=1,le=12)],
    format_export:Literal['csv','xlsx','pdf'],empreinte:Annotated[str,Query(pattern=r'^[a-f0-9]{64}$')],
    db:Session=Depends(lecture),user=Depends(get_current_user)):
    data=preparer(db,user['societe_id'],annee,mois)
    return reponse_export(data,format_export,empreinte,db,user['societe_id'],f'preparation_ras_tva_{annee}_{mois:02d}')


@router.get('/ras/registre/{annee}')
def consulter(annee:Annotated[int,Path(ge=1,le=9999)],db:Session=Depends(lecture),user=Depends(get_current_user)):
    return construire(db,user['societe_id'],annee)


@router.get('/ras/registre/{annee}/export/{format_export}')
def exporter(annee:Annotated[int,Path(ge=1,le=9999)],format_export:Literal['csv','xlsx','pdf'],
    empreinte:Annotated[str,Query(pattern=r'^[a-f0-9]{64}$')],db:Session=Depends(lecture),user=Depends(get_current_user)):
    data=construire(db,user['societe_id'],annee)
    return reponse_export(data,format_export,empreinte,db,user['societe_id'],f'registre_ras_tva_{annee}')


def reponse_export(data,format_export,empreinte,db,sid,nom):
    if not data['disponible']:
        raise HTTPException(409,'Registre indisponible : migration099 requise.')
    if data['empreinte_sha256']!=empreinte:
        raise HTTPException(409,'Le registre a changé. Actualisez-le avant de télécharger.')
    societe=db.get(models.Societe,sid)
    contenu=(csv_bytes(data) if format_export=='csv' else xlsx_bytes(data,societe) if format_export=='xlsx' else pdf_bytes(data,societe))
    mime={'csv':'text/csv; charset=utf-8','xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','pdf':'application/pdf'}[format_export]
    return Response(contenu,media_type=mime,headers={
        'Content-Disposition':f'attachment; filename="{nom}.{format_export}"',
        'Access-Control-Expose-Headers':'Content-Disposition',
    })
