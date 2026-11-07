"""Conservation interne du PDF exact ; ne vaut pas archivage légal certifié."""
import hashlib,json
from typing import Literal
from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel,ConfigDict,Field,field_validator
from sqlalchemy import text
import models

class Conservation(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    motif:str=Field(min_length=1,max_length=500)
    conservation_confirmee:Literal[True]

    @field_validator('conservation_confirmee',mode='before')
    @classmethod
    def explicite(cls,v):
        if v is not True:raise ValueError('Confirmer explicitement la conservation de cette copie figée.')
        return v

def sha(data):return hashlib.sha256(data).hexdigest()
def canonique(source):return json.dumps(source,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')

def installee(db):return bool(db.scalar(text("SELECT to_regclass('public.factures_copies_conservees') IS NOT NULL")))

def facture_source(db,user,ident,verrou=False,exiger_migration=True):
    q=db.query(models.Facture).filter_by(id=ident,societe_id=user['societe_id'])
    if verrou:q=q.with_for_update()
    f=q.first()
    if not f:raise HTTPException(404,'Facture introuvable dans cette société.')
    if exiger_migration and not installee(db):
        raise HTTPException(503,'Installer la migration125 sur une copie de la base avant la conservation des PDF.')
    return f

def chercher(db,user,ident):
    return db.execute(text('SELECT * FROM factures_copies_conservees WHERE societe_id=:s AND facture_id=:f'),{'s':user['societe_id'],'f':ident}).mappings().first()

def verifier(row):
    if sha(bytes(row['document_pdf']))!=row['pdf_sha256'] or sha(canonique(row['source']))!=row['source_sha256']:
        raise HTTPException(409,'Intégrité de la copie conservée incohérente ; ne pas utiliser ce document.')

def metadata(row,reutilise=False):
    if row is None:return None
    verifier(row)
    return {**{k:row[k] for k in ['id','facture_id','auteur_id','motif','cree_at','pdf_sha256','source_sha256','source']},
            'octets':len(row['document_pdf']),'reutilise':reutilise,
            'portee':'Copie interne figée du PDF émis ; ni preuve de règlement ni archivage légal certifié.'}

def consulter(db,user,ident):
    facture_source(db,user,ident,exiger_migration=False)
    if not installee(db):return {'copie':None,'disponible':False,'message':'La conservation du PDF nécessite la migration125 sur une copie de la base. Le téléchargement habituel reste disponible.'}
    return {'copie':metadata(chercher(db,user,ident)),'disponible':True}

def conserver(db,user,ident,data,generer_pdf):
    try:
        f=facture_source(db,user,ident,verrou=True)
        ancien=chercher(db,user,ident)
        if ancien:
            resultat=metadata(ancien,True);db.commit();return resultat
        if not f.est_validee or f.est_proforma or str(getattr(f.type,'value',f.type))!='vente':
            raise HTTPException(409,'Conserver une facture de vente validée ; brouillons, proformas et pièces d’achat sont hors de ce parcours.')
        document=bytes(generer_pdf(ident,current_user=user,db=db).body)
        if not document.startswith(b'%PDF-') or len(document)>10485760:raise HTTPException(409,'PDF invalide ou supérieur à10Mo ; aucune copie conservée.')
        source={'version':'COPIE_FACTURE_923','facture_id':f.id,'numero':f.numero,'date':f.date.isoformat(),
                'type':'vente','date_validation':f.date_validation.isoformat() if f.date_validation else None,
                'portee':'PDF produit par HisabPro lors de cette conservation. Ne certifie ni un dépôt, ni un paiement, ni une durée légale de conservation.'}
        db.execute(text('INSERT INTO factures_copies_conservees(societe_id,facture_id,auteur_id,motif,document_pdf,pdf_sha256,source,source_sha256) VALUES(:s,:f,:u,:m,:p,:h,CAST(:j AS jsonb),:a)'),
          {'s':user['societe_id'],'f':ident,'u':user['id'],'m':data.motif,'p':document,'h':sha(document),'j':canonique(source).decode('utf8'),'a':sha(canonique(source))})
        resultat=metadata(chercher(db,user,ident));db.commit();return resultat
    except Exception:
        db.rollback();raise

def telecharger(db,user,ident):
    facture_source(db,user,ident);row=chercher(db,user,ident)
    if not row:raise HTTPException(404,'Aucune copie figée conservée pour cette facture.')
    verifier(row)
    return Response(content=bytes(row['document_pdf']),media_type='application/pdf',headers={
      'Content-Disposition':f'attachment; filename="facture_{ident}_copie_conservee.pdf"',
      'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','X-Document-SHA256':row['pdf_sha256']})
