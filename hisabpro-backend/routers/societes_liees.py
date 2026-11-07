from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user,requiert_admin
import models
from services.societes_liees_service import schema_disponible,verifier_acces,verifier_tiers,liaison,sortie
from services.utilisateurs_acces_service import verrouiller_administration

router=APIRouter(prefix='/liaisons',tags=['sociétés liées'])
from routers.factures_liees import router as factures_liees_router
router.include_router(factures_liees_router)


class LiaisonIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    acheteur_id:int=Field(gt=0,strict=True)
    client_id:int=Field(gt=0,strict=True)
    fournisseur_id:int=Field(gt=0,strict=True)
    cle:UUID
    justification:str=Field(min_length=1,max_length=500)
    association_verifiee:bool

    @field_validator('justification')
    @classmethod
    def non_vide(cls,v):
        v=v.strip()
        if not v:raise ValueError('Justification requise.')
        return v


class RetraitIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    motif:str=Field(min_length=1,max_length=500)

    @field_validator('motif')
    @classmethod
    def non_vide(cls,v):
        v=v.strip()
        if not v:raise ValueError('Motif requis.')
        return v


@router.get('')
def lister(user=Depends(get_current_user),db:Session=Depends(get_db)):
    schema_disponible(db)
    ls=db.execute(text('SELECT l.*,r.motif AS motif_retrait,r.created_at AS retired_at FROM societes_liees l LEFT JOIN societes_liees_retraits r ON r.liaison_id=l.id WHERE l.vendeur_id=:sid OR l.acheteur_id=:sid ORDER BY l.id DESC'),{'sid':user['societe_id']}).mappings().all()
    result=[]
    for l in ls:
        try:verifier_acces(db,user['id'],(l['vendeur_id'],l['acheteur_id']))
        except HTTPException:continue
        result.append(sortie(db,l))
    return result


@router.get('/options/{acheteur_id}')
def options(acheteur_id:int,user=Depends(requiert_admin),db:Session=Depends(get_db)):
    if acheteur_id==user['societe_id']:raise HTTPException(422,'Choisissez une autre société.')
    verifier_acces(db,user['id'],(user['societe_id'],acheteur_id),('admin',))
    a=db.get(models.Societe,acheteur_id)
    return {'id':a.id,'raison_sociale':a.raison_sociale,'ice':a.ice,
        'clients':[{'id':t.id,'nom':t.nom,'ice':t.ice} for t in db.query(models.Tiers).filter(models.Tiers.societe_id==user['societe_id'],models.Tiers.actif.is_(True),models.Tiers.type.in_(['client','les_deux'])).order_by(models.Tiers.nom).all()],
        'fournisseurs':[{'id':t.id,'nom':t.nom,'ice':t.ice} for t in db.query(models.Tiers).filter(models.Tiers.societe_id==acheteur_id,models.Tiers.actif.is_(True),models.Tiers.type.in_(['fournisseur','les_deux'])).order_by(models.Tiers.nom).all()]}


@router.post('',status_code=201)
def creer(data:LiaisonIn,user=Depends(requiert_admin),db:Session=Depends(get_db)):
    schema_disponible(db);v=user['societe_id'];a=data.acheteur_id
    if v==a:raise HTTPException(422,'Deux sociétés distinctes sont nécessaires.')
    if not data.association_verifiee:raise HTTPException(422,'Vérifiez explicitement les sociétés et leurs tiers.')
    verifier_acces(db,user['id'],(v,a),('admin',))
    verrouiller_administration(db,[v,a])
    verifier_acces(db,user['id'],(v,a),('admin',))
    db.execute(text('SELECT pg_advisory_xact_lock(:v,:a)'),{'v':min(v,a),'a':max(v,a)})
    params={'v':v,'a':a,'c':data.client_id,'f':data.fournisseur_id,'cle':str(data.cle),'j':data.justification,'u':user['id']}
    old=db.execute(text('SELECT id,acheteur_id,client_id,fournisseur_id,justification FROM societes_liees WHERE vendeur_id=:v AND cle=CAST(:cle AS uuid)'),params).mappings().first()
    if old:
        if (old['acheteur_id'],old['client_id'],old['fournisseur_id'],old['justification'])!=(a,data.client_id,data.fournisseur_id,data.justification):raise HTTPException(409,'Clé déjà utilisée pour une autre association.')
        return sortie(db,liaison(db,old['id'],v))
    verifier_tiers(db,v,a,data.client_id,data.fournisseur_id)
    if db.scalar(text('SELECT EXISTS(SELECT 1 FROM societes_liees l WHERE vendeur_id=:v AND acheteur_id=:a AND NOT EXISTS(SELECT 1 FROM societes_liees_retraits r WHERE r.liaison_id=l.id))'),params):raise HTTPException(409,'Une liaison active existe déjà pour cette vente entre sociétés.')
    lid=db.scalar(text('INSERT INTO societes_liees(vendeur_id,acheteur_id,client_id,fournisseur_id,cle,justification,created_by) VALUES(:v,:a,:c,:f,CAST(:cle AS uuid),:j,:u) RETURNING id'),params)
    result=sortie(db,liaison(db,lid,v));db.commit();return result


@router.post('/{liaison_id}/retirer')
def retirer(liaison_id:int,data:RetraitIn,user=Depends(requiert_admin),db:Session=Depends(get_db)):
    l=liaison(db,liaison_id,user['societe_id'])
    # Une société peut retirer son consentement sans conserver de droits chez l'autre.
    verrouiller_administration(db,user['societe_id'])
    verifier_acces(db,user['id'],(user['societe_id'],),('admin',))
    db.execute(text('SELECT pg_advisory_xact_lock(:v,:a)'),{'v':min(l['vendeur_id'],l['acheteur_id']),'a':max(l['vendeur_id'],l['acheteur_id'])})
    l=liaison(db,liaison_id,user['societe_id'])
    if l['retired_at']:
        if l['motif_retrait']!=data.motif:raise HTTPException(409,'Cette liaison a déjà été retirée pour un autre motif.')
    else:
        db.execute(text('INSERT INTO societes_liees_retraits(liaison_id,motif,created_by) VALUES(:id,:m,:u)'),{'id':liaison_id,'m':data.motif,'u':user['id']})
    # Le retrait ne révèle pas l'identité de la société devenue inaccessible.
    db.commit();return {'id':liaison_id,'active':False,'motif_retrait':data.motif}
