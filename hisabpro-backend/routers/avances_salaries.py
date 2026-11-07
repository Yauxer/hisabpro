"""Métadonnées GRH séparées : aucune mutation d'écriture ni retenue automatique."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, requiert_ecriture
from services.personnel_acces_service import exiger_lecture, exiger_mutation_historique

router = APIRouter(prefix='/avances', tags=['GRH'])


class Affectation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    employe_id: int = Field(gt=0, strict=True)
    ligne_id: int = Field(gt=0, strict=True)
    motif: str = Field(min_length=1, max_length=500)


class Annulation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    motif: str = Field(min_length=1, max_length=500)


def disponible(db):
    if not db.scalar(text("SELECT to_regclass('public.grh_avances_affectations') IS NOT NULL")):
        raise HTTPException(503, 'Registre des avances indisponible : migration 095 à installer après sauvegarde.')


def lignes(db, sid):
    return db.execute(text('''
        SELECT l.id AS ligne_id,e.id AS ecriture_id,e.date,e.exercice,e.numero_ecriture,e.libelle,
               l.debit,l.credit,e.contrepassation_de_id,
               a.id AS affectation_id,a.employe_id,a.motif,a.created_by,a.created_at,
               p.nom AS nom_employe,p.actif AS employe_actif
        FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id
        LEFT JOIN grh_avances_affectations a ON a.ligne_id=l.id AND a.annule_at IS NULL
        LEFT JOIN employes p ON p.id=a.employe_id AND p.societe_id=e.societe_id
        WHERE e.societe_id=:s AND e.est_validee AND l.compte='3431'
        ORDER BY e.date DESC,e.id DESC,l.id DESC
    '''), {'s': sid}).mappings().all()


@router.get('')
def consulter(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    exiger_lecture(db,current_user,'personnel.lire_identite','personnel.lire_remuneration')
    disponible(db)
    sid=current_user['societe_id']
    rows=lignes(db,sid)
    for row in rows:
        if not row['debit'].is_finite() or not row['credit'].is_finite():
            raise HTTPException(409,'Montant historique non fini sur le compte 3431 ; aucun solde présenté.')
    soldes={}
    for r in rows:
        if r['affectation_id']:
            p=soldes.setdefault(r['employe_id'],{'employe_id':r['employe_id'],'nom':r['nom_employe'],
                 'debit':0,'credit':0,'solde':0})
            p['debit']+=r['debit'];p['credit']+=r['credit'];p['solde']+=r['debit']-r['credit']
    historique=db.execute(text('''SELECT a.*,p.nom AS nom_employe FROM grh_avances_affectations a
        JOIN employes p ON p.id=a.employe_id AND p.societe_id=a.societe_id
        WHERE a.societe_id=:s ORDER BY a.id DESC'''),{'s':sid}).mappings().all()
    return {'mouvements':rows,'soldes':list(soldes.values()),'historique':historique,
            'non_affectes':sum(r['affectation_id'] is None for r in rows),
            'perimetre':'Toutes les écritures définitives 3431, tous exercices. Soldes limités aux mouvements affectés ; aucune retenue sur salaire automatique.'}


def enregistrer(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        code=getattr(exc.orig,'pgcode',None)
        if code=='23505':
            raise HTTPException(409,'Cette ligne possède déjà une affectation active.') from exc
        if code=='23514':
            raise HTTPException(409, str(exc.orig).split('\n')[0]) from exc
        raise


@router.post('',status_code=201)
def affecter(data:Affectation,current_user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    exiger_mutation_historique(db,current_user)
    disponible(db);sid=current_user['societe_id']
    emp=db.execute(text('SELECT id,actif FROM employes WHERE id=:e AND societe_id=:s FOR UPDATE'),
                   {'e':data.employe_id,'s':sid}).mappings().first()
    if not emp:raise HTTPException(404,'Salarié introuvable dans cette société')
    source=db.execute(text('''SELECT l.debit,l.credit FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id
        WHERE l.id=:l AND e.societe_id=:s AND e.est_validee AND l.compte='3431' '''),
        {'l':data.ligne_id,'s':sid}).mappings().first()
    if not source:raise HTTPException(404,'Ligne 3431 définitive introuvable dans cette société')
    if not source['debit'].is_finite() or not source['credit'].is_finite():
        raise HTTPException(409,'Montant historique non fini : affectation impossible.')
    if not emp['actif'] and source['debit']>0:
        raise HTTPException(409,'Réactiver la fiche salariée avant d’affecter un versement.')
    try:
        ident=db.scalar(text('''INSERT INTO grh_avances_affectations(societe_id,employe_id,ligne_id,created_by,motif)
            VALUES(:s,:e,:l,:u,:m) RETURNING id'''),
            {'s':sid,'e':data.employe_id,'l':data.ligne_id,'u':current_user['id'],'m':data.motif})
        enregistrer(db)
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig,'pgcode',None) in ('23505','23514'):
            raise HTTPException(409,str(exc.orig).split('\n')[0]) from exc
        raise
    return {'id':ident}


@router.post('/{ident}/annuler')
def annuler(ident:int,data:Annulation,current_user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    exiger_mutation_historique(db,current_user)
    disponible(db);sid=current_user['societe_id']
    a=db.execute(text('SELECT employe_id FROM grh_avances_affectations WHERE id=:i AND societe_id=:s'),
                 {'i':ident,'s':sid}).mappings().first()
    if not a:raise HTTPException(404,'Affectation introuvable dans cette société')
    db.execute(text('SELECT id FROM employes WHERE id=:e AND societe_id=:s FOR UPDATE'),{'e':a['employe_id'],'s':sid})
    try:
        result=db.execute(text('''UPDATE grh_avances_affectations SET annule_par=:u,annule_at=:d,motif_annulation=:m
            WHERE id=:i AND societe_id=:s AND annule_at IS NULL'''),
            {'u':current_user['id'],'d':datetime.now(timezone.utc).replace(tzinfo=None),'m':data.motif,'i':ident,'s':sid})
        if not result.rowcount:raise HTTPException(409,'Cette affectation est déjà annulée.')
        enregistrer(db)
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig,'pgcode',None)=='23514':raise HTTPException(409,str(exc.orig).split('\n')[0]) from exc
        raise
    return {'id':ident,'statut':'annule'}
