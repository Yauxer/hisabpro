from uuid import UUID
from decimal import Decimal,InvalidOperation
from typing import Literal
from fastapi import APIRouter,Depends,HTTPException,Query
from pydantic import BaseModel,ConfigDict,Field,field_validator,model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from auth import get_current_user,requiert_ecriture
import models
from services.societes_liees_service import liaison,verifier_acces
from services.utilisateurs_acces_service import verrouiller_administration
from services.factures_liees_service import disponible,configurer,preparer,trouver_source,suivi
from services.factures_liees_service import periode_ouverte
from services.exercice_verrou_service import verrouiller_saisie_exercice

router=APIRouter()


def lecture_correspondances(db:Session=Depends(get_db)):
    from services.ventes_preparation_service import preparer_lecture
    return preparer_lecture(db)


@router.get('/{lid}/correspondances')
def lister_correspondances(lid:int,page:int=Query(1,ge=1),db:Session=Depends(lecture_correspondances),user=Depends(get_current_user)):
    # RO/RR initialisé avant la première lecture d'authentification, même Session.
    from services.correspondances_suivi_service import construire
    return construire(db,user,lid,page)


class LigneIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_ligne_id:int=Field(gt=0,strict=True)
    article_id:int=Field(gt=0,strict=True)


class ApercuIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    lignes:list[LigneIn]=Field(min_length=1,max_length=500)
    nature_tva_achat:Literal['charge','non_deductible']
    tva_deductible_pct:Decimal

    @field_validator('tva_deductible_pct',mode='before')
    @classmethod
    def taux(cls,v):
        try:
            if isinstance(v,bool):raise ValueError()
            d=Decimal(str(v))
            if not d.is_finite() or not 0<=d<=100 or d!=d.quantize(Decimal('.01')):raise ValueError()
        except (ValueError,InvalidOperation):raise ValueError('Pourcentage fini de0à100 avec deux décimales maximum requis.')
        return d

    @model_validator(mode='after')
    def nature_coherente(self):
        if self.nature_tva_achat=='non_deductible' and self.tva_deductible_pct!=0:
            raise ValueError('Une TVA non déductible nécessite un pourcentage déclaré de0.')
        return self


class CreationIn(ApercuIn):
    cle:UUID
    empreinte:str=Field(pattern=r'^[a-f0-9]{64}$')
    correspondance_verifiee:bool=Field(strict=True)


@router.get('/factures/{fid}/correspondance')
def correspondance(fid:int,user=Depends(get_current_user),db:Session=Depends(get_db)):
    disponible(db)
    if not db.query(models.Facture).filter_by(id=fid,societe_id=user['societe_id']).first():raise HTTPException(404,'Facture introuvable.')
    row=db.execute(text('SELECT * FROM factures_correspondantes WHERE facture_vente_id=:id OR facture_achat_id=:id'),{'id':fid}).mappings().first()
    if not row:return None
    return suivi(db,row,user)


@router.get('/{lid}/factures/{fid}/options')
def options(lid:int,fid:int,user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    disponible(db);l=liaison(db,lid,user['societe_id'])
    _,c=configurer(db,user,l,fid);return c


@router.post('/{lid}/factures/{fid}/apercu')
def apercu(lid:int,fid:int,data:ApercuIn,user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    disponible(db);l=liaison(db,lid,user['societe_id'])
    p,_,_=preparer(db,user,l,fid,data);return p


@router.post('/{lid}/factures/{fid}',status_code=201)
def creer(lid:int,fid:int,data:CreationIn,user=Depends(requiert_ecriture),db:Session=Depends(get_db)):
    disponible(db);l=liaison(db,lid,user['societe_id'])
    if user['societe_id']!=l['vendeur_id']:raise HTTPException(403,'Créez la correspondance depuis le vendeur.')
    verifier_acces(db,user['id'],(l['vendeur_id'],l['acheteur_id']),('admin','comptable'))
    if not data.correspondance_verifiee:raise HTTPException(422,'Vérifiez explicitement la correspondance.')
    verrouiller_administration(db,[l['vendeur_id'],l['acheteur_id']])
    verifier_acces(db,user['id'],(l['vendeur_id'],l['acheteur_id']),('admin','comptable'))
    db.execute(text('SELECT pg_advisory_xact_lock(:v,:a)'),{'v':min(l['vendeur_id'],l['acheteur_id']),'a':max(l['vendeur_id'],l['acheteur_id'])})
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:k,0))"),{'k':'factures_liees:'+str(data.cle)})
    # Source sérialisée avec validation/comptabilisation/annulation ordinaires.
    f=db.query(models.Facture).filter_by(id=fid,societe_id=l['vendeur_id']).populate_existing().with_for_update().first()
    if not f:raise HTTPException(404,'Facture de vente introuvable.')
    params={'nature_tva_achat':data.nature_tva_achat,'tva_deductible_pct':format(data.tva_deductible_pct,'.2f'),'lignes':[{'source_ligne_id':x.source_ligne_id,'article_id':x.article_id} for x in sorted(data.lignes,key=lambda x:x.source_ligne_id)]}
    old=db.execute(text('SELECT * FROM factures_correspondantes WHERE cle=CAST(:c AS uuid)'),{'c':str(data.cle)}).mappings().first()
    if old:
        if old['liaison_id']!=lid or old['facture_vente_id']!=fid or old['faits']['parametres']!=params:raise HTTPException(409,'Clé déjà utilisée pour une autre correspondance.')
        return suivi(db,old,user)
    if db.scalar(text('SELECT EXISTS(SELECT 1 FROM factures_correspondantes WHERE facture_vente_id=:id)'),{'id':fid}):raise HTTPException(409,'Cette vente possède déjà une facture d’achat correspondante.')
    # Relire les données sensibles après les attentes/verrous, sans objet ORM périmé.
    l=liaison(db,lid,user['societe_id'])
    ex=periode_ouverte(db,l['acheteur_id'],f.date)
    verrouiller_saisie_exercice(db,l['acheteur_id'],ex.annee)
    db.query(models.ExerciceComptable).filter_by(id=ex.id).populate_existing().with_for_update().one()
    db.query(models.PeriodeComptable).filter(models.PeriodeComptable.exercice_id==ex.id,models.PeriodeComptable.date_debut<=f.date,models.PeriodeComptable.date_fin>=f.date).populate_existing().with_for_update().all()
    db.query(models.Tiers).filter(models.Tiers.id.in_([l['client_id'],l['fournisseur_id']])).order_by(models.Tiers.id).populate_existing().with_for_update().all()
    db.query(models.Article).filter(models.Article.id.in_([x.article_id for x in data.lignes])).order_by(models.Article.id).populate_existing().with_for_update().all()
    p,creation,params=preparer(db,user,l,fid,data)
    if p['empreinte']!=data.empreinte:raise HTTPException(409,'Aperçu périmé : vérifiez à nouveau les sociétés, articles et données de facture.')
    from routers.factures import creer_brouillon_facture
    try:
        a=creer_brouillon_facture(creation,{**user,'societe_id':l['acheteur_id']},db)
        lignes=[{'source_id':v['id'],'achat_id':x['id'],'article_id':x['article_id']} for v,x in zip(p['source']['lignes'],sorted(a['lignes'],key=lambda x:x['id']))]
        faits={'parametres':params,'empreinte':p['empreinte'],'source':p['source'],'acheteur':p['acheteur'],'lignes':lignes}
        import json
        rid=db.scalar(text('INSERT INTO factures_correspondantes(liaison_id,facture_vente_id,facture_achat_id,cle,faits,created_by) VALUES(:l,:v,:a,CAST(:c AS uuid),CAST(:f AS jsonb),:u) RETURNING id'),{'l':lid,'v':fid,'a':a['id'],'c':str(data.cle),'f':json.dumps(faits,default=str,ensure_ascii=False,allow_nan=False),'u':user['id']})
        row=db.execute(text('SELECT * FROM factures_correspondantes WHERE id=:id'),{'id':rid}).mappings().one()
        result=suivi(db,row,user);db.commit();return result
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,'Création refusée par un contrôle d’intégrité. Aucun brouillon conservé ; vérifiez la référence fournisseur et la correspondance.') from exc
