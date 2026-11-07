"""Administration des accès limitée à une société, comptes principaux et invités."""
from fastapi import HTTPException
import models


def verrouiller_administration(db, societe_id):
    # Les changements d'administrateurs doivent partager un verrou PostgreSQL
    # pour que deux requêtes ne retirent pas chacune le dernier autre admin.
    ids = [societe_id] if isinstance(societe_id, int) else sorted(set(societe_id))
    societes = db.query(models.Societe).filter(models.Societe.id.in_(ids)).order_by(
        models.Societe.id.asc()
    ).with_for_update().all()
    if len(societes) != len(ids):
        raise HTTPException(404, "Société introuvable")


def verifier_admin_apres_verrou(db, utilisateur_id, societe_id):
    """Revalide les droits après attente du verrou, sans état ORM périmé."""
    user = db.query(models.Utilisateur).filter_by(id=utilisateur_id).populate_existing().first()
    if user and user.actif:
        if user.societe_id == societe_id and user.role == "admin":
            return
        if user.societe_id != societe_id:
            liaison = db.query(models.UtilisateurSociete).filter_by(
                utilisateur_id=utilisateur_id, societe_id=societe_id, actif=True,
            ).populate_existing().first()
            if liaison and liaison.role == "admin":
                return
    raise HTTPException(403, "Droits administrateur révoqués")


def societes_admin_secondaires(db, user):
    if not user.actif:
        return []
    return [row.societe_id for row in db.query(models.UtilisateurSociete).filter(
        models.UtilisateurSociete.utilisateur_id == user.id,
        models.UtilisateurSociete.societe_id != user.societe_id,
        models.UtilisateurSociete.role == "admin",
        models.UtilisateurSociete.actif.is_(True),
    ).all()]


def administrateurs_actifs(db, societe_id):
    principaux = db.query(models.Utilisateur.id).filter_by(
        societe_id=societe_id, role="admin", actif=True
    ).all()
    invites = db.query(models.Utilisateur.id).join(
        models.UtilisateurSociete,
        models.UtilisateurSociete.utilisateur_id == models.Utilisateur.id,
    ).filter(
        models.UtilisateurSociete.societe_id == societe_id,
        models.UtilisateurSociete.role == "admin",
        models.UtilisateurSociete.actif.is_(True),
        models.Utilisateur.actif.is_(True),
        models.Utilisateur.societe_id != societe_id,
    ).all()
    return {row[0] for row in principaux + invites}


def verifier_retrait_administrateur(db, societe_id, user_id, role_actuel, actif_actuel, role_futur, actif_futur):
    if role_actuel == "admin" and actif_actuel and not (role_futur == "admin" and actif_futur):
        if administrateurs_actifs(db, societe_id) <= {user_id}:
            raise HTTPException(400, "Impossible : cette société doit conserver au moins un administrateur actif.")
