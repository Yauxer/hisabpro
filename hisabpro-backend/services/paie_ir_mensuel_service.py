from fastapi import HTTPException
from sqlalchemy import text
from services import paie_bases_fiscales_service as bases,paie_campagnes_service as brut,personnel_workflow_service as w
from services.paie_ir_mensuel_moteur import calculer

def autoriser(db,user,action=None):
    ctx=bases.autoriser(db,user,action)
    if not db.scalar(text("SELECT to_regclass('public.paie_controles_mensuels') IS NOT NULL")):raise HTTPException(503,'Installer la migration124 du contrôle mensuel préparatoire.')
    return ctx

def sortie(db,row,user,ctx,reutilise=False):
    r=brut.sortie(row,user,ctx,reutilise);s=r['contenu']['source_preparation']
    p=db.execute(text('SELECT empreinte FROM paie_preparations_fiscales WHERE id=:i AND societe_id=:s'),{'i':r['preparation_id'],'s':user['societe_id']}).mappings().first()
    if not p or s['id']!=r['preparation_id'] or p['empreinte']!=s['empreinte']:raise HTTPException(409,'Provenance du contrôle mensuel incomplète.')
    return r

@w.transaction
def simuler(db,user,data):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id'];demande=brut.empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'}))
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:mensuel:{sid}'})
    ancien=db.execute(text('SELECT * FROM paie_controles_mensuels WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Clé de reprise utilisée pour une autre demande mensuelle.')
        return sortie(db,ancien,user,ctx,True)
    p=bases.lire(db,user,data.preparation_id);e=bases.verifier_sources_salarie(db,user,ctx,p,data.employe_id);variables=[]
    for v in e['variables_sources']:
        row=db.execute(text("SELECT id,periodicite,donnees FROM paie_variables WHERE id=:i AND societe_id=:s AND employe_id=:e AND statut='APPROUVE'"),{'i':v['id'],'s':sid,'e':data.employe_id}).mappings().first()
        if not row:raise HTTPException(409,'Variable fiscale source approuvée introuvable.')
        meta=row['donnees'].get('rattachement_revenus');variables.append({'id':row['id'],'periodicite':row['periodicite'],'rattachement_revenus':None if meta is None else {k:meta.get(k) for k in ['reference_debut','reference_fin','versement_date']}})
    c=calculer(e,p['contenu']['periode'],data,variables)
    c['source_preparation']={'id':p['id'],'numero':p['numero'],'empreinte':p['empreinte'],'brut_id':p['contenu']['brut_id'],'brut_empreinte':p['contenu']['brut_empreinte'],'social_id':p['contenu']['social_id'],'social_empreinte':p['contenu']['social_empreinte']}
    c['variables_documentaires']=variables
    if c['periode'][:4]!='2026':raise HTTPException(409,'Aucun contrôleur préparatoire qualifié pour ce millésime ;aucun repli vers2026.')
    ident=db.scalar(text('INSERT INTO paie_controles_mensuels(societe_id,employe_id,preparation_id,periode,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:e,:p,:d,:k,:h,CAST(:c AS jsonb),:f,:u,:m) RETURNING id'),{'s':sid,'e':data.employe_id,'p':p['id'],'d':c['periode'],'k':str(data.cle_idempotence),'h':demande,'c':brut.canonique(c),'f':brut.empreinte(c),'u':user['id'],'m':data.motif})
    return sortie(db,db.execute(text('SELECT * FROM paie_controles_mensuels WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid}).mappings().one(),user,ctx)

def lire(db,user,ident):
    ctx=autoriser(db,user);r=db.execute(text('SELECT * FROM paie_controles_mensuels WHERE id=:i AND societe_id=:s'),{'i':ident,'s':user['societe_id']}).mappings().first()
    if not r:raise HTTPException(404,'Contrôle mensuel introuvable dans cette société.')
    return sortie(db,r,user,ctx)

def lister(db,user,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'o':decalage,'l':limite}
    return {'total':db.scalar(text('SELECT count(*) FROM paie_controles_mensuels WHERE societe_id=:s'),p),'elements':[dict(x) for x in db.execute(text("SELECT id,periode,contenu->>'nom' AS nom,contenu->>'matricule' AS matricule,contenu->>'rni_arithmetique' AS rni,contenu->>'ir_mensuel_arithmetique' AS ir FROM paie_controles_mensuels WHERE societe_id=:s ORDER BY id DESC OFFSET :o LIMIT :l"),p).mappings()]}
