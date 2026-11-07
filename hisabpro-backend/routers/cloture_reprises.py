"""Registre explicite de reprises partielles ; les pièces restent à valider au Journal."""
import json
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, requiert_ecriture
import models
from services.ventes_preparation_service import preparer_lecture
from services.reprises_provisions_service import (
    RepriseIn,CreationIn,AnnulationIn,TYPES,exiger_registre,lecture_source,preparer,faits,source,periode,registre)

router=APIRouter(prefix='/reprises-provisions')


def lecture(db:Session=Depends(get_db)):
    return preparer_lecture(db)


@router.get('')
def lister(page:int=Query(1,ge=1),db:Session=Depends(lecture),user=Depends(get_current_user)):
    exiger_registre(db)
    q=db.query(models.AjustementInventaire.id).filter(models.AjustementInventaire.societe_id==user['societe_id'],
        models.AjustementInventaire.type.in_(TYPES)).order_by(models.AjustementInventaire.id.desc())
    total=q.count()
    return {'total':total,'page':page,'items':[lecture_source(db,user['societe_id'],aid) for (aid,) in q.offset((page-1)*20).limit(20)]}


@router.get('/{aid}')
def lire(aid:int,db:Session=Depends(lecture),user=Depends(get_current_user)):
    exiger_registre(db)
    return lecture_source(db,user['societe_id'],aid)


@router.get('/{aid}/preparation')
def preparation(aid:int,db:Session=Depends(lecture),user=Depends(get_current_user)):
    from services.reprises_provisions_export_service import preparer
    return preparer(db,user['societe_id'],aid)[0]


@router.get('/{aid}/export/{format_export}')
def exporter(aid:int,format_export:Literal['pdf','xlsx'],empreinte:str=Query(pattern=r'^[a-f0-9]{64}$'),
    db:Session=Depends(lecture),user=Depends(get_current_user)):
    from services.reprises_provisions_export_service import preparer,pdf_bytes,xlsx_bytes
    data,societe=preparer(db,user['societe_id'],aid)
    if empreinte!=data['empreinte_sha256']:
        raise HTTPException(409,'Le suivi ou l’identité de la société a changé. Actualisez avant de télécharger.')
    contenu=pdf_bytes(data,societe) if format_export=='pdf' else xlsx_bytes(data,societe)
    return Response(contenu,media_type='application/pdf' if format_export=='pdf' else
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',headers={
        'Content-Disposition':f'attachment; filename="suivi_reprises_provision_{aid}.{format_export}"',
        'Access-Control-Expose-Headers':'Content-Disposition'})


@router.post('/{aid}/apercu')
def apercu(aid:int,data:RepriseIn,db:Session=Depends(lecture),user=Depends(get_current_user)):
    return preparer(db,user['societe_id'],aid,data)


@router.post('/{aid}')
def creer(aid:int,data:CreationIn,db:Session=Depends(get_db),user=Depends(requiert_ecriture)):
    sid=user['societe_id'];exiger_registre(db)
    # Clé avant verrou source : même demande rejouée, y compris après timeout.
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:k,0))'),{'k':f'reprise:{sid}:{data.cle}'})
    ancien=db.execute(text('SELECT id,ajustement_id,faits FROM reprises_provisions WHERE societe_id=:s AND cle=:k'),{'s':sid,'k':str(data.cle)}).mappings().first()
    if ancien:
        if ancien['ajustement_id']!=aid or ancien['faits']['faits']!=faits(data) or not data.mouvements_verifies:
            raise HTTPException(409,'Cette clé de demande correspond à une autre reprise.')
        return lecture_source(db,sid,aid)
    if not data.mouvements_verifies:
        raise HTTPException(422,'Vérifiez les mouvements du compte et les justificatifs avant création.')
    doc=preparer(db,sid,aid,data,verrou=True)
    if doc['empreinte']!=data.empreinte:
        raise HTTPException(409,'La capacité ou les données ont changé. Recalculez l’aperçu.')
    e=models.Ecriture(societe_id=sid,date=data.date,date_piece=data.date_piece,journal='OD',
        exercice=doc['exercice'],source='reprise_provision',reference=data.reference,
        libelle=('Reprise — '+data.justification)[:300],
        lignes=[models.LigneEcriture(**{k:l[k] for k in ('compte','debit','credit')},
            libelle='Reprise de provision') for l in doc['lignes']])
    db.add(e);db.flush()
    db.execute(text('''INSERT INTO reprises_provisions(societe_id,ajustement_id,ecriture_id,cle,montant,faits,created_by)
        VALUES(:s,:a,:e,:k,:m,CAST(:f AS jsonb),:u)'''),
        {'s':sid,'a':aid,'e':e.id,'k':str(data.cle),'m':data.montant,'f':json.dumps(doc,ensure_ascii=False),'u':user['id']})
    db.commit()
    return lecture_source(db,sid,aid)


@router.post('/{aid}/{rid}/annuler')
def annuler(aid:int,rid:int,data:AnnulationIn,db:Session=Depends(get_db),user=Depends(requiert_ecriture)):
    sid=user['societe_id'];exiger_registre(db)
    source(db,sid,aid,verrou=True)
    r=next((r for r in registre(db,sid,aid) if r['id']==rid),None)
    if not r:raise HTTPException(404,'Reprise introuvable.')
    if r['annulation_id']:
        if r['motif']!=data.motif or db.get(models.Ecriture,r['inverse_id']).date!=data.date:
            raise HTTPException(409,'Une annulation différente existe déjà pour cette reprise.')
        return lecture_source(db,sid,aid)
    e=db.query(models.Ecriture).filter_by(id=r['ecriture_id'],societe_id=sid).populate_existing().with_for_update().one()
    if data.date<e.date:raise HTTPException(422,'L’annulation ne peut pas précéder la reprise.')
    ex=periode(db,sid,data.date)
    inverse=models.Ecriture(societe_id=sid,date=data.date,journal='OD',exercice=ex.annee,source='reprise_provision',
        reference=f'ANN-REPRISE-{rid}',libelle=('Annulation reprise — '+data.motif)[:300],motif_correction=data.motif,
        lignes=[models.LigneEcriture(compte=l.compte,libelle='Annulation de reprise',debit=l.credit,credit=l.debit) for l in e.lignes])
    db.add(inverse);db.flush()
    db.execute(text('''INSERT INTO reprises_provisions_annulations(reprise_id,societe_id,ecriture_id,motif,created_by)
        VALUES(:r,:s,:e,:m,:u)'''),{'r':rid,'s':sid,'e':inverse.id,'m':data.motif,'u':user['id']})
    db.commit()
    return lecture_source(db,sid,aid)
