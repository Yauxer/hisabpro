from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import os
import hashlib
import hmac
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
_PRODUCTION = os.getenv("APP_ENV", "dev").strip().casefold() in ("prod", "production")
if _PRODUCTION and (
    not SECRET_KEY or not SECRET_KEY.strip() or SECRET_KEY.strip() == "dev-secret-change-in-production"
):
    raise RuntimeError(
        "SECRET_KEY manquante ou clé de développement en production : "
        "définissez un secret privé avant de démarrer.")
if not SECRET_KEY:
    SECRET_KEY = "dev-secret-change-in-production"
    print("⚠️  AVERTISSEMENT : SECRET_KEY par défaut (dev uniquement). "
          "Définissez SECRET_KEY dans .env avant toute mise en production.")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))

# bcrypt tronque au-delà de 72 octets. Le format Passlib bcrypt_sha256
# protège tout le secret pour les nouveaux mots de passe ; les anciens hashes
# bcrypt restent lisibles, sans migration ni réécriture automatique des comptes.
# Référence : https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt_sha256.html
pwd_context    = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def valider_mot_de_passe(password: str):
    """Politique commune à l'inscription et à l'administration des comptes."""
    if not isinstance(password, str) or len(password) < 8:
        raise HTTPException(400, "Le mot de passe doit contenir au moins 8 caractères.")
    if not password.strip() or password.strip().casefold() in {"password", "12345678", "azertyui", "motdepasse"}:
        raise HTTPException(400, "Mot de passe trop courant.")
    if "\x00" in password:
        raise HTTPException(400, "Le mot de passe contient un caractère non autorisé.")
    if len(password.encode("utf-8")) > 4096:
        raise HTTPException(400, "Le mot de passe dépasse la longueur maximale de 4096 octets.")


def hash_password(password: str) -> str:
    valider_mot_de_passe(password)
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        if not isinstance(plain, str) or "\x00" in plain or len(plain.encode("utf-8")) > 4096:
            return False
        return pwd_context.verify(plain, hashed)
    except (ValueError, TypeError):
        # Un hash historique invalide ou une entrée malformée ne doit pas
        # produire une erreur serveur ni divulguer des détails cryptographiques.
        return False

def empreinte_mot_de_passe(hashed_password: str) -> str:
    """Version opaque du secret, sans exposer le hash de connexion dans le JWT."""
    return hmac.new(SECRET_KEY.encode("utf-8"), hashed_password.encode("utf-8"), hashlib.sha256).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, password_hash: Optional[str] = None) -> str:
    to_encode = data.copy()
    if password_hash is not None:
        to_encode["pwd_version"] = empreinte_mot_de_passe(password_hash)
    expire = datetime.utcnow() + (expires_delta if expires_delta is not None else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    if not isinstance(token, str) or len(token) > 8192:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (JWTError, RecursionError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dépendance FastAPI : récupère l'utilisateur depuis le token puis revalide
# son état et ses droits en base à chaque requête. Ainsi, une désactivation,
# une révocation d'accès société ou un changement de rôle prend effet
# immédiatement, sans attendre l'expiration du JWT.
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
):
    payload = decode_token(token)
    user_id = payload.get("sub")
    societe_id = payload.get("societe_id")
    if user_id is None or societe_id is None:
        raise HTTPException(status_code=401, detail="Token invalide")

    try:
        user_id = int(user_id)
        societe_id = int(societe_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token invalide")

    user = db.query(models.Utilisateur).filter_by(id=user_id).first()
    if not user or not user.actif:
        raise HTTPException(status_code=401, detail="Compte désactivé ou introuvable")
    # Toutes les sessions acceptées doivent être liées au mot de passe courant.
    # Fin de la transition des anciens JWT : une reconnexion produit une version,
    # sans réécrire le hash historique ni modifier les données de l'utilisateur.
    if "pwd_version" not in payload:
        raise HTTPException(status_code=401, detail="Session ancienne : reconnectez-vous")
    version = payload.get("pwd_version")
    if (
        not isinstance(version, str) or not hmac.compare_digest(version, empreinte_mot_de_passe(user.hashed_password))
    ):
        raise HTTPException(status_code=401, detail="Mot de passe modifié : reconnectez-vous")

    if user.societe_id == societe_id:
        role = user.role
    else:
        liaison = db.query(models.UtilisateurSociete).filter_by(
            utilisateur_id=user_id, societe_id=societe_id, actif=True
        ).first()
        if not liaison:
            raise HTTPException(status_code=403, detail="Accès à cette société révoqué")
        role = liaison.role

    if role not in {"admin", "comptable", "lecture", "personnel"}:
        # Fail closed : un rôle inconnu ne doit jamais hériter implicitement de
        # droits d'écriture.
        role = "lecture"

    from services.personnel_profil_service import exiger_chemin_personnel
    exiger_chemin_personnel(role, request)
    return {"id": user_id, "societe_id": societe_id, "role": role}


# ─── Contrôle d'accès basé sur les rôles (RBAC) ──────────────────────────────
# Rôles, du plus large au plus restreint :
#   admin     : tout, y compris la gestion des utilisateurs et les paramètres société
#   comptable : toutes les opérations métier (saisie, factures, clôture, immobilisations)
#   lecture   : consultation seule — aucune création/modification/suppression
ROLES_ECRITURE = ("admin", "comptable")


def exiger_ecriture(current_user: dict):
    """Bloque les utilisateurs en lecture seule sur toute opération modifiante."""
    if (current_user or {}).get("role") not in ROLES_ECRITURE:
        raise HTTPException(
            status_code=403,
            detail="Votre profil est en consultation seule : cette opération n'est pas autorisée.",
        )


def exiger_admin(current_user: dict):
    """Réserve l'opération aux administrateurs."""
    if (current_user or {}).get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Cette opération est réservée aux administrateurs.",
        )


# Variantes utilisables directement comme dépendances FastAPI
def requiert_ecriture(current_user: dict = Depends(get_current_user)):
    exiger_ecriture(current_user)
    return current_user


def requiert_admin(current_user: dict = Depends(get_current_user)):
    exiger_admin(current_user)
    return current_user


def requiert_personnel_ecriture(current_user: dict = Depends(get_current_user)):
    """Droit de profil seulement ; les capacités et la protection restent vérifiées par le service."""
    if current_user['role'] not in {'admin','comptable','personnel'}:
        raise HTTPException(403,'Votre profil ne permet pas les modifications Personnel.')
    return current_user
