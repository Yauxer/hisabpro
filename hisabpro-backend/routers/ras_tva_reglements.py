"""Raccordement explicite du calcul559 à la capture083, atomique et auditable."""
import json
from pydantic import ValidationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from database import get_db
from auth import get_current_user, requiert_ecriture
from services.ras_reglement_service import captures_facture
from services.ras_tva_simulation_service import SimulationRasTvaIn
from services.ras_tva_reglement_service import (
    ApercuIn, CaptureTvaIn, disponible, exiger_disponible, details, preparer, faits_serialises,
)

router = APIRouter()


def source(db, user, rid, verrou=False):
    from routers.ras_reglements import reglement_source
    r = reglement_source(db, user['societe_id'], rid, verrou)
    q = db.query(models.Facture).filter_by(id=r.facture_id, societe_id=user['societe_id']).populate_existing()
    f = (q.with_for_update() if verrou else q).first()
    return r, f


@router.get('/{rid}/ras-tva')
def consulter(rid: int, user=Depends(get_current_user), db: Session=Depends(get_db)):
    source(db, user, rid)
    actif = disponible(db)
    return {'disponible': actif, 'migration_requise': None if actif else '099_ras_tva_details.sql',
        'dossier': details(db, user['societe_id'], rid) if actif else None}


@router.post('/{rid}/ras-tva/apercu')
def apercu(rid: int, data: ApercuIn, user=Depends(get_current_user), db: Session=Depends(get_db)):
    r, f = source(db, user, rid)
    return preparer(db, user['societe_id'], r, f, data)


@router.post('/{rid}/ras-tva')
def capturer_tva(rid: int, data: CaptureTvaIn, user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    from routers.ras_reglements import CaptureIn, creer_capture
    r, f = source(db, user, rid, True)
    exiger_disponible(db)
    if not data.pieces_verifiees:
        raise HTTPException(422, 'Confirmation explicite des pièces et de la ventilation requise.')
    sid = user['societe_id']
    existant = details(db, sid, rid)
    if existant:
        c = next(c for c in captures_facture(db, sid, r.facture_id) if c['reglement_id'] == rid)
        try:
            faits_conserves = faits_serialises(SimulationRasTvaIn.model_validate(existant['faits']))
        except (KeyError, TypeError, ValidationError):
            raise HTTPException(409, 'Faits conservés non qualifiables ; dossier historique préservé, contrôle nécessaire.')
        meme = (faits_conserves == faits_serialises(data.simulation) and
            existant['justification_quote_part'] == data.justification_quote_part and
            c['reference'] == data.reference and c['compte_destination'] == data.compte_destination and
            existant['empreinte_apercu'] == data.empreinte_apercu)
        if not meme or c['annulation_id'] is not None:
            raise HTTPException(409, 'Dossier RAS TVA immuable ; utiliser l’annulation du règlement.')
        return {'capture': c, 'dossier': existant}
    resultat = preparer(db, sid, r, f, data)
    if resultat['empreinte_apercu'] != data.empreinte_apercu:
        raise HTTPException(409, 'Source ou qualification modifiée : refaire l’aperçu avant de préparer la RAS TVA.')
    dossier = {**resultat['dossier'], 'empreinte_apercu': resultat['empreinte_apercu'], 'pieces_verifiees': True}
    def tracer(capture_id):
        db.execute(text('''INSERT INTO public.ras_tva_reglement_details(capture_id,societe_id,dossier)
            VALUES(:c,:s,CAST(:d AS jsonb))'''), {'c': capture_id, 's': sid, 'd': json.dumps(dossier, ensure_ascii=False)})
    c = creer_capture(rid, CaptureIn(montant=dossier['simulation']['retenue_tva'], date_operation=r.date,
        reference=data.reference, compte_destination=data.compte_destination), user, db, avant_commit=tracer)
    return {'capture': c, 'dossier': dossier}
