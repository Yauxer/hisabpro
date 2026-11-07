"""Capture déclarative d'une RAS opérée ; aucune qualification fiscale automatique."""
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
import math
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from pydantic import ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from database import get_db
from auth import get_current_user, requiert_ecriture
from services.ras_reglement_service import disponible, captures_facture
from services.compta_mapping_service import compte_tiers_facture

router = APIRouter(prefix='/api/reglements', tags=['RAS explicite'])


class CaptureIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    montant: Decimal
    date_operation: date
    reference: Annotated[str, Field(min_length=1, max_length=100)]
    compte_destination: Annotated[str, Field(min_length=4, max_length=10)]

    @field_validator('montant', mode='before')
    @classmethod
    def fini(cls, v):
        if isinstance(v, bool):
            raise ValueError('Le montant ne peut pas être un booléen')
        try:
            d = Decimal(str(v))
            if not d.is_finite() or d <= 0 or not math.isfinite(float(d)):
                raise ValueError('Montant fini et strictement positif requis')
            with localcontext() as ctx:
                ctx.prec = 400
                if d != d.quantize(Decimal('.01')):
                    raise ValueError('Montant à saisir au centime')
                stockage = models.LigneEcriture.__table__.c.debit.type
                if d >= Decimal(10) ** (stockage.precision - stockage.scale):
                    raise ValueError('Montant non représentable dans les lignes comptables NUMERIC(18,2)')
            return d
        except (InvalidOperation, TypeError, OverflowError):
            raise ValueError('Montant invalide')

    @field_validator('reference', 'compte_destination')
    @classmethod
    def non_vide(cls, v):
        if not v.strip():
            raise ValueError('Valeur explicite requise')
        return v.strip()


def reglement_source(db, sid, rid, verrou=False):
    q = db.query(models.Reglement).filter_by(id=rid, societe_id=sid)
    if verrou:
        q = q.populate_existing().with_for_update()
    r = q.first()
    if r is None:
        raise HTTPException(404, 'Règlement introuvable')
    return r


@router.get('/{rid}/ras')
def lire_ras(rid: int, user=Depends(get_current_user), db: Session=Depends(get_db)):
    r = reglement_source(db, user['societe_id'], rid)
    actif = disponible(db)
    captures = [c for c in captures_facture(db, user['societe_id'], r.facture_id) if c['reglement_id'] == rid] if actif else []
    f = db.query(models.Facture).filter_by(id=r.facture_id, societe_id=user['societe_id']).first()
    blocages = []
    if not actif:
        blocages.append('Migration083 manuelle requise')
    if user.get('role') == 'lecture':
        blocages.append('Consultation seule')
    if captures:
        blocages.append('Ce règlement possède déjà une capture immuable')
    if f is None or not f.est_validee or f.est_proforma or getattr(f.statut,'value',f.statut)=='annulee':
        blocages.append('Facture source non admissible')
    elif f.ras_comptabilisee:
        blocages.append('RAS historique : mélange avec capture explicite interdit')
    if r.mode not in ('virement','especes') or r.statut != 'complet' or not r.est_comptabilisee or not r.ecriture_id:
        blocages.append('Règlement immédiat comptabilisé par virement ou espèces requis')
    solde = None
    if f is not None:
        from routers.factures import _situation_paiement_facture
        situation = _situation_paiement_facture(db,user['societe_id'],f,tolere_ras_invalide=True)
        solde = situation['solde_restant']
        if solde is None:
            blocages.append(situation['ras_anomalie'] or 'Solde indéterminable')
        elif solde <= .01:
            blocages.append('Facture déjà soldée')
    return {'disponible': actif, 'migration_requise': None if actif else '083_ras_reglements.sql',
        'modes_admis': ['virement','especes'], 'captures': captures,
        'peut_capturer': not blocages, 'blocages': blocages, 'solde_restant': solde,
        'qualification': 'Saisie déclarative ; OD préparée, aucun justificatif fiscal certifié'}


@router.post('/{rid}/ras')
def capturer(rid: int, data: CaptureIn, user=Depends(requiert_ecriture), db: Session=Depends(get_db)):
    return creer_capture(rid, data, user, db)


def creer_capture(rid, data, user, db, *, avant_commit=None):
    if not disponible(db):
        raise HTTPException(409, 'Capture indisponible : application manuelle explicite de 083_ras_reglements.sql requise')
    sid = user['societe_id']
    r = reglement_source(db, sid, rid, True)
    f = db.query(models.Facture).filter_by(id=r.facture_id, societe_id=sid).populate_existing().with_for_update().first()
    if not f:
        raise HTTPException(409, 'Facture source introuvable')
    rows = [c for c in captures_facture(db, sid, f.id) if c['reglement_id'] == rid]
    if rows:
        c = rows[0]
        if c['annulation_id'] is None and Decimal(str(c['montant'])) == data.montant and c['date_operation'] == data.date_operation and c['reference'] == data.reference and c['compte_destination'] == data.compte_destination:
            return c
        raise HTTPException(409, 'Ce règlement possède déjà une capture RAS immuable')
    if f.ras_comptabilisee:
        raise HTTPException(409, 'RAS historique comptabilisée : mélange avec captures explicites interdit')
    if r.mode not in ('virement','especes') or r.statut != 'complet' or not r.est_comptabilisee or not r.ecriture_id:
        raise HTTPException(409, 'Capture limitée aux règlements immédiats comptabilisés par virement ou espèces')
    if not f.est_validee or f.est_proforma or str(getattr(f.statut,'value',f.statut)) == 'annulee':
        raise HTTPException(409, 'Facture source non admissible')
    from routers.commercial import _verifier_date_operation_ouverte, _exercice_ref, _maj_statut_facture
    from routers.factures import _situation_paiement_facture
    from services.auxiliaire_service import rattacher_tiers_aux_lignes
    if data.date_operation > date.today() or data.date_operation < r.date:
        raise HTTPException(422, 'La date déclarée doit être comprise entre le règlement et aujourd’hui')
    _verifier_date_operation_ouverte(db, sid, data.date_operation, 'capture RAS')
    compte = db.query(models.CompteSociete).filter_by(societe_id=sid, numero=data.compte_destination, actif=True).first()
    collectif = compte_tiers_facture(db, sid, f)
    from services.auxiliaire_service import nature_auxiliaire_pour_compte
    if compte is None or data.compte_destination == collectif or nature_auxiliaire_pour_compte(data.compte_destination) or f.tiers_id is None:
        raise HTTPException(422, 'Compte destination actif distinct du collectif et tiers source explicite requis')
    situation = _situation_paiement_facture(db, sid, f)
    if data.montant > Decimal(str(situation['solde_restant'])):
        raise HTTPException(409, 'La capture dépasse le solde restant de la facture')
    vente = getattr(f.type,'value',f.type) == 'vente'
    m = data.montant
    lignes = [models.LigneEcriture(compte=data.compte_destination, libelle='RAS déclarée', debit=m if vente else 0, credit=0 if vente else m),
              models.LigneEcriture(compte=collectif, libelle=f.tiers, debit=0 if vente else m, credit=m if vente else 0)]
    rattacher_tiers_aux_lignes(db, sid, lignes, tiers_id=f.tiers_id, nature='client' if vente else 'fournisseur')
    ec = models.Ecriture(societe_id=sid, journal='OD', date=data.date_operation, date_piece=data.date_operation,
        exercice=_exercice_ref(db,sid,data.date_operation), source='ras_reglement', reference=data.reference,
        libelle=f'Capture RAS déclarée — règlement {r.id} — {f.numero}', lignes=lignes)
    db.add(ec); db.flush()
    capture_id = db.execute(text('''INSERT INTO public.ras_reglement_captures
       (societe_id,reglement_id,facture_id,ecriture_id,montant,date_operation,reference,compte_destination,created_by)
       VALUES(:sid,:rid,:fid,:eid,:montant,:jour,:ref,:compte,:acteur) RETURNING id'''),
       {'sid':sid,'rid':rid,'fid':f.id,'eid':ec.id,'montant':data.montant,'jour':data.date_operation,
        'ref':data.reference,'compte':data.compte_destination,'acteur':user['id']}).scalar_one()
    if avant_commit is not None:
        avant_commit(capture_id)
    _maj_statut_facture(db,sid,f.id)
    db.commit()
    return next(c for c in captures_facture(db,sid,f.id) if c['reglement_id']==rid)


from routers.ras_tva_reglements import router as router_ras_tva
router.include_router(router_ras_tva)
