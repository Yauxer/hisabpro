"""Habilitations Personnel explicites ;aucun droit de paiement ou rôle global ajouté."""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from auth import get_current_user, requiert_admin
from database import get_db
from services.personnel_acces_service import contexte, schema_installe, verrou, exiger_lecture
from services.personnel_dossiers_service import preflight_dossiers
from services.utilisateurs_acces_service import verrouiller_administration, verifier_admin_apres_verrou

router = APIRouter(prefix='/securite', tags=['Personnel : habilitations'])


class Motif(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    motif: str = Field(min_length=1, max_length=500)


class Habilitation(Motif):
    utilisateur_id: int = Field(gt=0, strict=True)
    capacite: Literal['personnel.lire_identite', 'personnel.lire_remuneration',
                      'personnel.lire_identifiants_sensibles', 'personnel.audit_lire',
                      'personnel.proposer', 'personnel.soumettre', 'personnel.approuver',
                      'personnel.valider_regles_paie']


class Activation(Motif):
    confirmation: Literal['PROTEGER_PERSONNEL']


def preparer(db, user):
    verrouiller_administration(db, user['societe_id'])
    verifier_admin_apres_verrou(db, user['id'], user['societe_id'])
    verrou(db, user['societe_id'], exclusif=True)
    if not schema_installe(db):
        raise HTTPException(503, 'Installer la migration 105 avant de gérer les habilitations Personnel.')


def ecrire(db, requete, params, *, identifiant=False):
    try:
        result = db.execute(text(requete), params)
        valeur = result.scalar() if identifiant else None
        db.commit()
        return valeur
    except IntegrityError as exc:
        db.rollback()
        if getattr(exc.orig, 'pgcode', None) in {'23505', '23514', '23503'}:
            raise HTTPException(409, 'Les accès Personnel ont changé. Rechargez avant de réessayer.') from exc
        raise


@router.get('/acces')
def consulter_acces(current_user=Depends(get_current_user), db: Session=Depends(get_db)):
    return contexte(db, current_user)


@router.get('/preflight-dossiers')
def diagnostic_dossiers(limite: int=Query(50, ge=1, le=100),
                        current_user=Depends(requiert_admin), db: Session=Depends(get_db)):
    exiger_lecture(db, current_user, 'personnel.lire_identite', 'personnel.audit_lire')
    return preflight_dossiers(db, current_user['societe_id'], limite=limite)


@router.get('/habilitations')
def lister(current_user=Depends(requiert_admin), db: Session=Depends(get_db)):
    preparer(db, current_user)
    return db.execute(text('SELECT * FROM personnel_habilitations WHERE societe_id=:s ORDER BY id DESC'),
                      {'s': current_user['societe_id']}).mappings().all()


@router.post('/habilitations', status_code=201)
def accorder(data: Habilitation, current_user=Depends(requiert_admin), db: Session=Depends(get_db)):
    preparer(db, current_user)
    sid = current_user['societe_id']
    if data.capacite=='personnel.valider_regles_paie' and not db.scalar(text("SELECT to_regclass('public.paie_rubrique_versions') IS NOT NULL")):
        raise HTTPException(503,'Installer la migration113 avant de déléguer la qualification réglementaire de paie.')
    if data.capacite in {'personnel.proposer','personnel.soumettre','personnel.approuver'}:
        from services.personnel_workflow_service import verifier_schema
        verifier_schema(db)
    # Vérification réelle des accès principaux ou invités, sans révéler un compte étranger.
    if not db.scalar(text('SELECT hisabpro_personnel_membre(:s,:u,false)'), {'s': sid, 'u': data.utilisateur_id}):
        raise HTTPException(404, 'Utilisateur actif introuvable dans cette société.')
    if db.scalar(text('SELECT EXISTS(SELECT 1 FROM personnel_habilitations WHERE societe_id=:s '
                      'AND utilisateur_id=:u AND capacite=:c AND revoquee_at IS NULL)'),
                 {'s': sid, 'u': data.utilisateur_id, 'c': data.capacite}):
        raise HTTPException(409, 'Cette habilitation est déjà active.')
    liaison = db.scalar(text('SELECT a.id FROM utilisateurs p LEFT JOIN utilisateurs_societes a '
                             'ON a.utilisateur_id=p.id AND a.societe_id=:s AND a.actif AND p.societe_id<>:s '
                             'WHERE p.id=:u'), {'s': sid, 'u': data.utilisateur_id})
    ident = ecrire(db, 'INSERT INTO personnel_habilitations(societe_id,utilisateur_id,liaison_id_snapshot,capacite,accordee_par,motif) '
                       'VALUES(:s,:u,:l,:c,:a,:m) RETURNING id',
                  {'s': sid, 'u': data.utilisateur_id, 'l': liaison, 'c': data.capacite, 'a': current_user['id'], 'm': data.motif}, identifiant=True)
    return {'id': ident, 'capacite': data.capacite}


@router.post('/habilitations/{ident}/revoquer')
def revoquer(ident: int, data: Motif, current_user=Depends(requiert_admin), db: Session=Depends(get_db)):
    preparer(db, current_user)
    row = db.execute(text('SELECT revoquee_at FROM personnel_habilitations WHERE id=:i AND societe_id=:s FOR UPDATE'),
                     {'i': ident, 's': current_user['societe_id']}).mappings().first()
    if row is None:
        raise HTTPException(404, 'Habilitation introuvable dans cette société.')
    if row['revoquee_at'] is not None:
        raise HTTPException(409, 'Cette habilitation est déjà révoquée.')
    ecrire(db, 'UPDATE personnel_habilitations SET revoquee_par=:u,revoquee_at=CURRENT_TIMESTAMP,'
               'motif_revocation=:m WHERE id=:i', {'u': current_user['id'], 'm': data.motif, 'i': ident})
    return {'id': ident, 'statut': 'revoquee'}


class ValidationUnique(Motif):
    active: bool


@router.post('/validation-unique')
def validation_unique(data: ValidationUnique, current_user=Depends(requiert_admin), db: Session=Depends(get_db)):
    """Lot 974 : validation par une seule personne (petite entreprise), tracée."""
    preparer(db, current_user)
    sid = current_user['societe_id']
    if not db.scalar(text("SELECT to_regclass('public.personnel_validation_unique') IS NOT NULL")):
        raise HTTPException(503, 'Installer la migration 132 de validation unique.')
    if data.active:
        ecrire(db, 'INSERT INTO personnel_validation_unique(societe_id,active,activee_par,motif) VALUES(:s,true,:u,:m) '
                   'ON CONFLICT(societe_id) DO UPDATE SET active=true,activee_par=:u,activee_at=clock_timestamp(),motif=:m,desactivee_par=NULL,desactivee_at=NULL',
               {'s': sid, 'u': current_user['id'], 'm': data.motif})
    else:
        ecrire(db, 'UPDATE personnel_validation_unique SET active=false,desactivee_par=:u,desactivee_at=clock_timestamp() WHERE societe_id=:s',
               {'s': sid, 'u': current_user['id']})
    return {'validation_unique': data.active}


@router.post('/activation', status_code=201)
def activer(data: Activation, current_user=Depends(requiert_admin), db: Session=Depends(get_db)):
    preparer(db, current_user)
    sid = current_user['societe_id']
    if db.scalar(text('SELECT EXISTS(SELECT 1 FROM personnel_acces_societes WHERE societe_id=:s)'), {'s': sid}):
        raise HTTPException(409, 'La protection Personnel est déjà activée.')
    ecrire(db, 'INSERT INTO personnel_acces_societes(societe_id,activee_par,motif) VALUES(:s,:a,:m)',
           {'s': sid, 'a': current_user['id'], 'm': data.motif})
    return {'mode': 'protege', 'societe_id': sid}
