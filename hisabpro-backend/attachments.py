"""
Router pour la gestion des pièces jointes.
Stockage local dans hisabpro-backend/uploads/{societe_id}/{doc_type}/{doc_id}/

FACT.11 :
- écriture réservée aux profils admin/comptable ;
- types de documents explicitement autorisés ;
- vérification que le document appartient bien à la société courante ;
- protection contre la traversée de répertoires ;
- taille maximale configurable ;
- noms physiques non ambigus pour éviter l'écrasement silencieux.
"""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, requiert_ecriture
import models

router = APIRouter(prefix="/api/attachments", tags=["attachments"])

UPLOAD_DIR = os.path.abspath(os.getenv("HISABPRO_UPLOAD_DIR") or os.path.join(os.path.dirname(__file__), "uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_ATTACHMENT_BYTES", str(10 * 1024 * 1024)))
EXTENSIONS_AUTORISEES = {'.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx'}

# Les seules pièces actuellement exposées dans l'UI HisabPro.
DOCUMENTS = {
    "facture": (models.Facture, None),
    "bc": (models.BonCommande, None),
    "bl": (models.BonLivraison, "vente"),
    "br": (models.BonLivraison, "achat"),
    # COMPTA.4 : une écriture peut recevoir un justificatif même après sa
    # validation. Le fichier est stocké à part : aucune donnée comptable
    # définitive n'est réécrite.
    "ecriture": (models.Ecriture, None),
}


def _document(db: Session, societe_id: int, doc_type: str, doc_id: int, *, verrouiller: bool = False):
    config = DOCUMENTS.get((doc_type or "").lower())
    if not config:
        raise HTTPException(400, "Type de document non autorisé pour les pièces jointes")
    modele, type_attendu = config
    q = db.query(modele).filter(modele.id == doc_id, modele.societe_id == societe_id)
    if type_attendu is not None:
        q = q.filter(modele.type == type_attendu)
    if verrouiller:
        # Sérialise la suppression documentaire avec la validation du parent.
        # OF limite le verrou à la table visée, même en présence de jointures.
        q = q.with_for_update(of=modele)
    obj = q.first()
    if not obj:
        # 404 volontaire : ne révèle pas l'existence d'un document d'une autre société.
        raise HTTPException(404, "Document introuvable")
    return obj


def get_upload_path(societe_id: int, doc_type: str, doc_id: int, *, creer: bool = False) -> str:
    doc_type = (doc_type or "").lower()
    if doc_type not in DOCUMENTS:
        raise HTTPException(400, "Type de document non autorisé")
    path = os.path.abspath(os.path.join(UPLOAD_DIR, str(int(societe_id)), doc_type, str(int(doc_id))))
    racine_societe = os.path.abspath(os.path.join(UPLOAD_DIR, str(int(societe_id))))
    if os.path.commonpath([path, racine_societe]) != racine_societe:
        raise HTTPException(400, "Chemin de pièce jointe invalide")
    if creer:
        os.makedirs(path, exist_ok=True)
    return path


def _safe_existing_file(base: str, filename: str) -> str:
    # Un nom reçu via l'URL ne doit jamais contenir un chemin, même encodé.
    if not filename or os.path.basename(filename) != filename or filename in {".", ".."}:
        raise HTTPException(400, "Nom de fichier invalide")
    path = os.path.abspath(os.path.join(base, filename))
    if os.path.commonpath([path, os.path.abspath(base)]) != os.path.abspath(base):
        raise HTTPException(400, "Nom de fichier invalide")
    return path


@router.get("/{doc_type}/{doc_id}")
def lister(
    doc_type: str,
    doc_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _document(db, current_user["societe_id"], doc_type, doc_id)
    path = get_upload_path(current_user["societe_id"], doc_type, doc_id)
    if not os.path.exists(path):
        return []
    files = []
    for fname in sorted(os.listdir(path)):
        fpath = _safe_existing_file(path, fname)
        if os.path.isfile(fpath):
            files.append({
                "nom": fname,
                "taille": os.path.getsize(fpath),
                "url": f"/api/attachments/{doc_type}/{doc_id}/download/{fname}",
            })
    return files


@router.post("/{doc_type}/{doc_id}")
async def uploader(
    doc_type: str,
    doc_id: int,
    file: UploadFile = File(...),
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    document = _document(db, current_user["societe_id"], doc_type, doc_id)
    original_filename = os.path.basename(file.filename or "")
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in EXTENSIONS_AUTORISEES:
        raise HTTPException(400, f"Extension non autorisée : {ext or 'aucune'}")

    stem = os.path.splitext(original_filename)[0]
    stem = "".join(c for c in stem if c.isalnum() or c in '-_ ').strip()[:60] or "piece"
    # Le suffixe court évite qu'un second fichier homonyme écrase le premier.
    final_name = f"{stem}_{uuid.uuid4().hex[:8]}{ext}"
    path = get_upload_path(current_user["societe_id"], doc_type, doc_id, creer=True)
    dest = _safe_existing_file(path, final_name)

    total = 0
    try:
        with open(dest, "xb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, f"Fichier trop volumineux (maximum {MAX_UPLOAD_BYTES // (1024*1024)} Mo)")
                out.write(chunk)
    except Exception:
        if os.path.exists(dest):
            os.remove(dest)
        raise
    finally:
        await file.close()

    if (doc_type or "").lower() == "ecriture":
        # Le nom du document n'est utilisé comme référence FEC qu'en dernier
        # recours. Si l'écriture porte déjà une référence (facture, règlement,
        # etc.), on la conserve comme référence métier.
        reference = (getattr(document, "reference", None) or original_filename or final_name).strip()[:100]
        piece = models.EcritureJustificatif(
            societe_id=current_user["societe_id"],
            ecriture_id=document.id,
            reference=reference,
            date_piece=getattr(document, "date_piece", None) or getattr(document, "date", None),
            source_type="fichier",
            fichier_nom=final_name,
            prioritaire=False,
            created_by=current_user.get("id"),
        )
        try:
            db.add(piece)
            db.commit()
        except Exception:
            db.rollback()
            # Ne pas laisser un fichier orphelin si l'enregistrement de sa
            # traçabilité comptable échoue.
            if os.path.exists(dest):
                os.remove(dest)
            raise

    return {
        "nom": final_name,
        "taille": total,
        "url": f"/api/attachments/{doc_type}/{doc_id}/download/{final_name}",
    }


@router.get("/{doc_type}/{doc_id}/download/{filename}")
def telecharger(
    doc_type: str,
    doc_id: int,
    filename: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _document(db, current_user["societe_id"], doc_type, doc_id)
    base = get_upload_path(current_user["societe_id"], doc_type, doc_id)
    path = _safe_existing_file(base, filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "Fichier introuvable")
    return FileResponse(path, filename=filename)


@router.delete("/{doc_type}/{doc_id}/{filename}", status_code=204)
def supprimer(
    doc_type: str,
    doc_id: int,
    filename: str,
    current_user=Depends(requiert_ecriture),
    db: Session = Depends(get_db),
):
    est_ecriture = (doc_type or "").lower() == "ecriture"
    document = _document(db, current_user["societe_id"], doc_type, doc_id,
                         verrouiller=est_ecriture)
    if (doc_type or "").lower() == "ecriture" and getattr(document, "est_validee", False):
        raise HTTPException(409,
            "Une pièce jointe à une écriture définitive est conservée dans l'archive. "
            "Ajoutez le bon document ou une nouvelle référence au lieu de supprimer l'historique.")
    base = get_upload_path(current_user["societe_id"], doc_type, doc_id)
    path = _safe_existing_file(base, filename)
    if not os.path.isfile(path):
        raise HTTPException(404, "Fichier introuvable")
    if est_ecriture:
        try:
            db.query(models.EcritureJustificatif).filter_by(
                societe_id=current_user["societe_id"], ecriture_id=document.id, fichier_nom=filename
            ).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
            # Un refus SQL doit laisser le fichier et sa trace récupérables.
            raise
    os.remove(path)
