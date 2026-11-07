"""Demandes datées et décisions traçables ; aucun droit à congé calculé."""
from datetime import date, datetime, timezone
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session
from auth import get_current_user, requiert_ecriture
from database import get_db
import models
from services.personnel_acces_service import exiger_lecture, exiger_mutation_historique, reponse_privee

router = APIRouter(prefix='/api/employes/conges', tags=['GRH'], dependencies=[Depends(reponse_privee)])


class DemandeAbsence(BaseModel):
    employe_id: int = Field(..., gt=0)
    type_absence: Literal['conge','absence','autre'] = 'conge'
    date_debut: date
    date_fin: date
    motif: Optional[str] = Field(None,max_length=1000)

    @field_validator('employe_id', mode='before')
    @classmethod
    def identifiant_entier(cls,value):
        if isinstance(value,bool) or not isinstance(value,int):
            raise ValueError('Un identifiant entier est requis')
        return value

    @model_validator(mode='after')
    def dates_coherentes(self):
        if self.date_fin < self.date_debut:
            raise ValueError('La fin précède le début de l’absence')
        return self


class DecisionAbsence(BaseModel):
    statut: Literal['approuve','refuse','annule']
    commentaire_decision: Optional[str] = Field(None,max_length=1000)


def transition_absence(statut, cible, role, auteur, acteur):
    if cible in ('approuve','refuse') and role != 'admin':
        raise HTTPException(403,'La décision est réservée aux administrateurs')
    if cible == 'annule' and role != 'admin' and auteur != acteur:
        raise HTTPException(403,'Seul l’auteur ou un administrateur peut annuler')
    permises = {'demande': {'approuve','refuse','annule'}, 'approuve': {'annule'}}
    if cible not in permises.get(statut,set()):
        raise HTTPException(409,'Cette demande est déjà traitée ou annulée')


def sortie(db,absence,current_user,employe=None,evenements=None):
    employe = employe or db.get(models.Employe,absence.employe_id)
    evenement = (db.query(models.EvenementAbsenceRH).filter_by(absence_id=absence.id,societe_id=absence.societe_id).order_by(models.EvenementAbsenceRH.id).all()
                 if evenements is None else evenements)
    return {col.name:getattr(absence,col.name) for col in absence.__table__.columns} | {
        'nom_employe': employe.nom,
        'jours_calendaires':(absence.date_fin-absence.date_debut).days+1,
        'peut_decider':current_user['role']=='admin' and absence.statut=='demande',
        'peut_annuler':current_user['role']!='lecture' and (current_user['role']=='admin' or absence.created_by==current_user['id']) and absence.statut in ('demande','approuve'),
        'historique':[{col.name:getattr(e,col.name) for col in e.__table__.columns} for e in evenement],
    }


def requete_absences(db,societe_id):
    return db.query(models.AbsenceRH,models.Employe).join(models.Employe,models.Employe.id==models.AbsenceRH.employe_id).filter(models.AbsenceRH.societe_id==societe_id).order_by(models.AbsenceRH.created_at.desc(),models.AbsenceRH.id.desc())


@router.get('')
def lister_absences(current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    acces = exiger_lecture(db,current_user,'personnel.lire_identite','personnel.lire_identifiants_sensibles')
    rows=requete_absences(db,current_user['societe_id']).all()
    resultats = [sortie(db,absence,current_user,employe) for absence,employe in rows]
    if acces['mode'] == 'protege':
        for row in resultats:
            row['peut_decider'] = row['peut_annuler'] = False
    return resultats


@router.get('/export/pdf')
def exporter_absences_pdf(statut:Optional[Literal['demande','approuve','refuse','annule']]=None,
                         current_user=Depends(get_current_user),db:Session=Depends(get_db)):
    exiger_lecture(db,current_user,'personnel.lire_identite','personnel.lire_identifiants_sensibles')
    from fastapi.responses import Response
    from services.grh_registre_pdf import generer_registre_absences_pdf
    sid=current_user['societe_id']
    query=requete_absences(db,sid)
    if statut is not None:
        query=query.filter(models.AbsenceRH.statut==statut)
    # Un seul SELECT donne une photographie cohérente de l'état et des événements,
    # même si une décision est enregistrée pendant la préparation du document.
    rows=query.add_entity(models.EvenementAbsenceRH).outerjoin(models.EvenementAbsenceRH,
        (models.EvenementAbsenceRH.absence_id==models.AbsenceRH.id) &
        (models.EvenementAbsenceRH.societe_id==sid)).order_by(models.EvenementAbsenceRH.id).all()
    groupes={}
    for absence,employe,evenement in rows:
        if absence.id not in groupes:
            groupes[absence.id]=(absence,employe,[])
        if evenement is not None:
            groupes[absence.id][2].append(evenement)
    donnees=[sortie(db,a,current_user,e,h) for a,e,h in groupes.values()]
    societe=db.query(models.Societe).filter_by(id=sid).first()
    contenu=generer_registre_absences_pdf(societe,donnees,statut)
    return Response(contenu,media_type='application/pdf',headers={
        'Content-Disposition':f'attachment; filename="registre_absences_{statut or "tous"}.pdf"',
        'Cache-Control':'no-store'})


@router.post('',status_code=201)
def creer_absence(data:DemandeAbsence,current_user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    exiger_mutation_historique(db,current_user)
    employe=db.query(models.Employe).filter_by(id=data.employe_id,societe_id=current_user['societe_id'],actif=True).with_for_update().first()
    if not employe:
        raise HTTPException(404,'Salarié actif introuvable dans cette société')
    if (employe.date_embauche and data.date_debut < employe.date_embauche) or (employe.date_sortie and data.date_fin > employe.date_sortie):
        raise HTTPException(400,'La période est hors des dates du dossier salarié')
    chevauchement=db.query(models.AbsenceRH.id).filter(models.AbsenceRH.societe_id==current_user['societe_id'],models.AbsenceRH.employe_id==employe.id,models.AbsenceRH.statut.in_(['demande','approuve']),models.AbsenceRH.date_debut<=data.date_fin,models.AbsenceRH.date_fin>=data.date_debut).first()
    if chevauchement:
        raise HTTPException(409,'Une demande active chevauche déjà cette période')
    absence=models.AbsenceRH(societe_id=current_user['societe_id'],created_by=current_user['id'],statut='demande',**data.model_dump())
    db.add(absence)
    db.flush()
    db.add(models.EvenementAbsenceRH(absence_id=absence.id,societe_id=absence.societe_id,acteur_id=current_user['id'],nouveau_statut='demande',commentaire=data.motif))
    db.commit()
    db.refresh(absence)
    return sortie(db,absence,current_user,employe)


@router.patch('/{absence_id}')
def decider_absence(absence_id:int,data:DecisionAbsence,current_user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    exiger_mutation_historique(db,current_user)
    absence=db.query(models.AbsenceRH).filter_by(id=absence_id,societe_id=current_user['societe_id']).with_for_update().first()
    if not absence:
        raise HTTPException(404,'Demande introuvable dans cette société')
    transition_absence(absence.statut,data.statut,current_user['role'],absence.created_by,current_user['id'])
    ancien=absence.statut
    absence.statut=data.statut
    absence.commentaire_decision=data.commentaire_decision
    absence.decided_by=current_user['id']
    absence.decided_at=datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(models.EvenementAbsenceRH(absence_id=absence.id,societe_id=absence.societe_id,acteur_id=current_user['id'],ancien_statut=ancien,nouveau_statut=data.statut,commentaire=data.commentaire_decision))
    db.commit()
    db.refresh(absence)
    return sortie(db,absence,current_user)
