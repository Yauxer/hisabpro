"""Copie documentaire contrôlée, sans validation ni écriture entre sociétés."""
import hashlib,json
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import joinedload
import models,schemas
from pydantic import ValidationError
from services.societes_liees_service import liaison,verifier_acces,verifier_tiers
from services.compta_mapping_service import compte_article

ENTETE=('date','date_echeance','delai_paiement','remise_globale','ristourne','escompte',
 'frais_transport_ht','frais_transport_tva','frais_transport_mode','frais_transport_qualification_tva',
 'frais_emballage_ht','frais_emballage_tva','frais_emballage_mode','frais_emballage_qualification_tva')
LIGNE=('description','quantite','prix_unitaire','tva','qualification_tva','remise','remise2','rabais')


def disponible(db):
    if not db.scalar(text("SELECT to_regclass('public.factures_correspondantes') IS NOT NULL")):
        raise HTTPException(503,'Les factures correspondantes nécessitent la migration explicite102.')


def verifier_suppression_correspondance(db,fid):
    if db.scalar(text("SELECT to_regclass('public.factures_correspondantes') IS NOT NULL")) and db.scalar(text('SELECT EXISTS(SELECT 1 FROM factures_correspondantes WHERE facture_vente_id=:id OR facture_achat_id=:id)'),{'id':fid}):
        raise HTTPException(409,'Facture liée à une correspondance tracée : conservez la pièce ; utilisez son statut ou un document correctif.')


def valeur(v):
    return getattr(v,'value',v)


def canonique(d):
    return json.dumps(d,sort_keys=True,ensure_ascii=False,separators=(',',':'),default=str,allow_nan=False)


def trouver_source(db,l,fid):
    f=db.query(models.Facture).options(joinedload(models.Facture.lignes),joinedload(models.Facture.echeances)).filter_by(id=fid,societe_id=l['vendeur_id']).populate_existing().first()
    if not f:raise HTTPException(404,'Facture de vente introuvable chez le vendeur associé.')
    return f


def periode_ouverte(db,sid,d):
    exs=db.query(models.ExerciceComptable).filter(models.ExerciceComptable.societe_id==sid,models.ExerciceComptable.date_debut<=d,models.ExerciceComptable.date_fin>=d).all()
    if len(exs)!=1:raise HTTPException(422,'Paramétrez un exercice unique couvrant la date de facture chez l’acheteur.')
    ex=exs[0]
    if ex.statut=='cloture' or db.query(models.ClotureExercice).filter_by(societe_id=sid,exercice=ex.annee).first():raise HTTPException(423,'Exercice de l’acheteur clôturé.')
    ps=db.query(models.PeriodeComptable).filter(models.PeriodeComptable.exercice_id==ex.id,models.PeriodeComptable.date_debut<=d,models.PeriodeComptable.date_fin>=d).all()
    if len(ps)!=1 or ps[0].statut!='ouverte':raise HTTPException(423,'Période de l’acheteur absente ou fermée.')
    return ex


def configurer(db,user,l,fid):
    verifier_acces(db,user['id'],(l['vendeur_id'],l['acheteur_id']),('admin','comptable'))
    if user['societe_id']!=l['vendeur_id']:raise HTTPException(403,'Préparez la correspondance depuis la société vendeuse.')
    if l['retired_at']:raise HTTPException(409,'Cette liaison a été retirée.')
    f=trouver_source(db,l,fid)
    if valeur(f.type)!='vente' or not f.est_validee or f.est_proforma or valeur(f.statut)=='annulee' or not f.numero or not f.lignes:
        raise HTTPException(409,'Choisissez une facture de vente validée, active et non proforma.')
    if f.tiers_id!=l['client_id']:raise HTTPException(422,'Le client de la facture ne correspond pas à cette liaison.')
    if f.ras_taux is None or not Decimal(str(f.ras_taux)).is_finite() or Decimal(str(f.ras_taux))!=0:
        raise HTTPException(422,'La reprise des factures portant une RAS historique n’est pas qualifiée dans ce parcours.')
    c,t=verifier_tiers(db,l['vendeur_id'],l['acheteur_id'],l['client_id'],l['fournisseur_id'])
    v=db.get(models.Societe,l['vendeur_id']);a=db.get(models.Societe,l['acheteur_id'])
    if any(s.devise!='MAD' for s in (v,a)):raise HTTPException(422,'Ce parcours est limité aux deux comptabilités tenues en MAD.')
    if f.tiers_ice_snapshot and a.ice and f.tiers_ice_snapshot!=a.ice:raise HTTPException(409,'L’identité de l’acheteur ne recoupe plus celle figée dans la facture.')
    for sid in (v.id,a.id):
        if not db.query(models.ModuleActif).filter_by(societe_id=sid,module='facturation',actif=True).first():raise HTTPException(409,'Le module Facturation doit être actif dans les deux sociétés.')
    ex=periode_ouverte(db,a.id,f.date)
    from routers.factures import _verifier_montants_representables,_calc_totaux
    _verifier_montants_representables(f)
    arts=db.query(models.Article).filter_by(societe_id=a.id,actif=True).order_by(models.Article.designation,models.Article.id).all()
    lignes=[{'id':x.id,**{k:getattr(x,k) for k in LIGNE}} for x in sorted(f.lignes,key=lambda x:x.id)]
    ht,tva,ttc,_,_=_calc_totaux(f)
    return f,{'liaison_id':l['id'],'source':{'id':f.id,'numero':f.numero,'exercice':f.exercice,'tiers_id':f.tiers_id,'statut':valeur(f.statut),'vendeur':v.raison_sociale,**{k:getattr(f,k) for k in ENTETE},'lignes':lignes,'total_ht':str(ht),'total_tva':str(tva),'total_ttc':str(ttc)},
        'acheteur':{'id':a.id,'nom':a.raison_sociale,'ice':a.ice,'exercice':ex.annee,'regime_tva':a.regime_tva,'fournisseur_id':t.id,'fournisseur':t.nom,'fournisseur_ice':t.ice},
        'articles':[{'id':ar.id,'code':ar.code,'designation':ar.designation,'is_stockable':ar.is_stockable,'compte_achat':compte_article(db,a.id,ar.id,est_vente=False)} for ar in arts],
        'echeances':[{'date_echeance':e.date_echeance,'montant':e.montant,'libelle':e.libelle} for e in f.echeances],
        'mode_reglement_prevu':valeur(f.mode_reglement_prevu)}


def preparer(db,user,l,fid,data):
    f,c=configurer(db,user,l,fid)
    m={x.source_ligne_id:x.article_id for x in data.lignes}
    if len(m)!=len(data.lignes) or set(m)!={x.id for x in f.lignes}:raise HTTPException(422,'Associez exactement une fois chaque ligne source à un article de l’acheteur.')
    arts={x['id']:x for x in c['articles']}
    if not set(m.values())<=set(arts):raise HTTPException(422,'Un article sélectionné est absent, inactif ou appartient à une autre société.')
    params={'nature_tva_achat':data.nature_tva_achat,'tva_deductible_pct':format(data.tva_deductible_pct,'.2f'),'lignes':[{'source_ligne_id':i,'article_id':m[i]} for i in sorted(m)]}
    payload={'type':'achat','date':f.date,'tiers_id':l['fournisseur_id'],'tiers':c['acheteur']['fournisseur'],'reference':f.numero,
        **{k:getattr(f,k) for k in ENTETE},'mode_reglement_prevu':c['mode_reglement_prevu'],
        'notes':f'Correspondance de la facture {f.numero} — vendeur {c["source"]["vendeur"]}.',
        'nature_tva_achat':data.nature_tva_achat,'tva_deductible_pct':float(data.tva_deductible_pct),'ras_taux':0,
        'echeances':c['echeances'] or None,'lignes':[{**{k:getattr(x,k) for k in LIGNE},'article_id':m[x.id]} for x in sorted(f.lignes,key=lambda x:x.id)]}
    try:creation=schemas.FactureCreate.model_validate(payload)
    except ValidationError as exc:raise HTTPException(422,'Les données historiques de la source ne permettent pas une copie fiable ; vérifiez la facture sans la réécrire.') from exc
    # Empreinte : faits utiles, articles choisis uniquement ; aucun stock courant
    # ni article non sélectionné ne rend artificiellement l'aperçu périmé.
    base={**c,'articles':[arts[i] for i in sorted(set(m.values()))],'parametres':params}
    empreinte=hashlib.sha256(canonique(base).encode()).hexdigest()
    return {'empreinte':empreinte,**base,'note':'Brouillon uniquement. Vérifiez et validez séparément la facture et son écriture chez l’acheteur. Les paiements et avoirs ne sont pas répliqués.'},creation,params


def suivi(db,row,user):
    l=liaison(db,row['liaison_id'],user['societe_id'])
    verifier_acces(db,user['id'],(l['vendeur_id'],l['acheteur_id']))
    fs=[db.query(models.Facture).options(joinedload(models.Facture.lignes)).filter_by(id=row[k]).first() for k in ('facture_vente_id','facture_achat_id')]
    v,a=fs
    ecarts=[]
    if a.tiers_id!=l['fournisseur_id']:ecarts.append('fournisseur')
    if a.nature_tva_achat!=row['faits']['parametres']['nature_tva_achat']:ecarts.append('nature_tva_achat')
    if a.tva_deductible_pct is None or not Decimal(str(a.tva_deductible_pct)).is_finite():
        ecarts.append('tva_deductible_pct_inconnu')
    elif Decimal(str(a.tva_deductible_pct))!=Decimal(row['faits']['parametres']['tva_deductible_pct']):ecarts.append('tva_deductible_pct')
    for champ in ENTETE:
        if getattr(v,champ)!=getattr(a,champ):ecarts.append(champ)
    if a.reference!=v.numero:ecarts.append('reference')
    paires=row['faits']['lignes'];vl={x.id:x for x in v.lignes};al={x.id:x for x in a.lignes}
    if len(al)!=len(paires):ecarts.append('nombre_lignes')
    for p in paires:
        x,y=vl.get(p['source_id']),al.get(p['achat_id'])
        if not x or not y or y.article_id!=p['article_id'] or any(getattr(x,k)!=getattr(y,k) for k in LIGNE):ecarts.append(f'ligne_source_{p["source_id"]}')
    if valeur(v.statut)=='annulee' or valeur(a.statut)=='annulee':ecarts.append('annulation_non_repliquee')
    # Les avoirs ne modifient pas forcément le statut de la facture source.
    for f in fs:
        if db.query(models.Avoir).filter(models.Avoir.facture_id==f.id,models.Avoir.statut!='annule').first():ecarts.append('avoir_a_traiter_separement')
    result={'id':row['id'],'liaison_id':l['id'],'liaison_active':not bool(l['retired_at']),'ecarts':sorted(set(ecarts)),
        'facture_vente_id':v.id,'facture_achat_id':a.id,'vendeur_id':l['vendeur_id'],'acheteur_id':l['acheteur_id'],
        'vente':{'numero':v.numero,'exercice':v.exercice,'validee':v.est_validee,'comptabilisee':bool(v.est_comptabilisee)},
        'achat':{'numero':a.numero,'reference':a.reference,'exercice':a.exercice,'validee':a.est_validee,'comptabilisee':bool(a.est_comptabilisee)},
        'note':'Les brouillons restent modifiables ; les écarts sont signalés. Validation, écritures, paiements et avoirs restent propres à chaque société.'}
    return result
