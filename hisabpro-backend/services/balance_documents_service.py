"""Pièces complémentaires immuables, hors empreinte de la préparation071."""
import hashlib
import os
from pathlib import Path
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
import models
import attachments
from services.balance_import_service import lire_preparation

LIMITE_DOSSIER = 50 * 1024 * 1024
NOTE = ('Pièces complémentaires associées uniquement à cette version. '
        'Leur contenu, taille, empreinte et auteur sont conservés séparément, hors empreinte historique des balances. '
        'Les ajouts restent conservés ; les versions suivantes ne recopient pas automatiquement ces pièces. '
        'Le contenu doit être contrôlé par la personne chargée du dossier ; aucune qualification fiscale n’est certifiée.')


def disponible(db):
    return bool(db.scalar(text("SELECT to_regclass('public.liasse_balance_documents') IS NOT NULL")))


def parent(db,sid,pid):
    row=db.query(models.LiasseBalancePreparation).filter_by(id=pid,societe_id=sid).first()
    if not row:raise HTTPException(404,'Préparation introuvable dans cette société.')
    try:return lire_preparation(row)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc


def exiger(db):
    if not disponible(db):
        raise HTTPException(503,'Justificatifs de préparation indisponibles : migration104 manuelle requise. Aucune migration automatique.')


def chemin_fichier(sid,pid,nom,creer=False):
    racine=Path(attachments.UPLOAD_DIR).resolve()
    dossier=racine/str(int(sid))/'balance_preparation_documents'/str(int(pid))
    cible=Path(attachments._safe_existing_file(str(dossier),nom))
    if os.path.commonpath([str(racine),str(cible.resolve())])!=str(racine):
        raise HTTPException(409,'Chemin du justificatif incompatible avec le stockage documentaire.')
    if creer:dossier.mkdir(parents=True,exist_ok=True)
    return cible


def metadata(r):
    return {**{k:r[k] for k in ('id','preparation_id','empreinte_preparation','nom_original','nom_stockage',
                               'reference','taille','sha256','created_by','acteur_nom')},
            'created_at':r['created_at'].isoformat()}


def lignes(db,sid,pid):
    try:
        return [metadata(r) for r in db.execute(text('SELECT * FROM liasse_balance_documents WHERE societe_id=:s AND preparation_id=:p ORDER BY id DESC'),
                                               {'s':sid,'p':pid}).mappings().all()]
    except DBAPIError as exc:
        db.rollback();raise HTTPException(503,'Accès aux justificatifs indisponible ; vérifiez la migration104 et les droits applicatifs.') from exc


def lire(db,sid,pid):
    dossier=parent(db,sid,pid);exiger(db)
    docs=lignes(db,sid,pid)
    return {'id':pid,'empreinte_sha256':dossier['empreinte_sha256'],'documents':docs,'note':NOTE,
            'limite_fichier':min(attachments.MAX_UPLOAD_BYTES,10*1024*1024),
            'limite_dossier':LIMITE_DOSSIER,'taille_totale':sum(r['taille'] for r in docs)}


def octets(sid,pid,r):
    p=chemin_fichier(sid,pid,r['nom_stockage'])
    if not p.is_file():raise HTTPException(409,'Justificatif conservé absent du stockage ; vérifier sa restauration.')
    with p.open('rb') as f:raw=f.read(10*1024*1024+1)
    if len(raw)!=r['taille'] or hashlib.sha256(raw).hexdigest()!=r['sha256']:
        raise HTTPException(409,'Intégrité du justificatif incohérente ; fichier non délivré.')
    return raw


def paquet(db,sid,pid):
    if not disponible(db):
        return {'statut':'indisponible_migration104','note':NOTE,'documents':None},{}
    docs=lignes(db,sid,pid)
    fichiers={f'justificatifs/{r["nom_stockage"]}':octets(sid,pid,r) for r in docs}
    return {'statut':'disponible','note':NOTE,'documents':docs},fichiers


async def ajouter(db,user,pid,file,cle:UUID,empreinte,reference):
    sid=user['societe_id'];dossier=parent(db,sid,pid);exiger(db)
    if empreinte!=dossier['empreinte_sha256']:
        raise HTTPException(409,'La préparation sélectionnée ne correspond pas à la source attendue.')
    original=(file.filename or '').replace('\\','/').rsplit('/',1)[-1].strip()
    ext=Path(original).suffix.lower()
    if not original or len(original)>255 or ext not in attachments.EXTENSIONS_AUTORISEES:
        raise HTTPException(422,'Nom de justificatif valide requis : PDF, image PNG/JPEG, Excel ou Word.')
    ref=(reference or '').strip() or original
    if len(ref)>500:raise HTTPException(422,'Référence documentaire limitée à 500 caractères.')
    limite=min(attachments.MAX_UPLOAD_BYTES,10*1024*1024)
    raw=await file.read(limite+1)
    if len(raw)>limite:raise HTTPException(413,'Justificatif trop volumineux pour la limite configurée (maximum10Mo).')
    if not raw:raise HTTPException(422,'Le justificatif est vide.')
    sha=hashlib.sha256(raw).hexdigest()
    db.execute(text("SELECT pg_advisory_xact_lock(hashtext('hisabpro_balance_documents'),:s)"),{'s':sid})
    ancien=db.execute(text('SELECT * FROM liasse_balance_documents WHERE societe_id=:s AND cle=CAST(:k AS uuid)'),
                       {'s':sid,'k':str(cle)}).mappings().first()
    if ancien:
        if (ancien['preparation_id'],ancien['empreinte_preparation'],ancien['nom_original'],ancien['reference'],ancien['sha256'])!=(pid,empreinte,original,ref,sha):
            raise HTTPException(409,'Clé déjà utilisée pour un autre justificatif.')
        octets(sid,pid,ancien)
        return metadata(ancien)
    total=db.scalar(text('SELECT coalesce(sum(taille),0) FROM liasse_balance_documents WHERE societe_id=:s AND preparation_id=:p'),{'s':sid,'p':pid})
    if total+len(raw)>LIMITE_DOSSIER:raise HTTPException(409,'Capacité documentaire de50Mo dépassée pour cette version.')
    nom=cle.hex+ext;p=chemin_fichier(sid,pid,nom,creer=True)
    cree=False
    try:
        with p.open('xb') as f:
            cree=True;f.write(raw)
        r=db.execute(text('''INSERT INTO liasse_balance_documents(societe_id,preparation_id,empreinte_preparation,cle,
            nom_original,nom_stockage,reference,taille,sha256,created_by)
            VALUES(:s,:p,:h,CAST(:k AS uuid),:o,:n,:r,:t,:sha,:u) RETURNING *'''),
            {'s':sid,'p':pid,'h':empreinte,'k':str(cle),'o':original,'n':nom,'r':ref,'t':len(raw),'sha':sha,'u':user['id']}).mappings().one()
        result=metadata(r);db.commit();return result
    except BaseException:
        db.rollback()
        if cree:p.unlink(missing_ok=True)
        raise
