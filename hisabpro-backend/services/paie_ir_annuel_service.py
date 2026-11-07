from fastapi import HTTPException
from sqlalchemy import text
from services import personnel_workflow_service as w,paie_social_service as social,paie_campagnes_service as brut
from services.paie_ir_annuel_moteur import calculer,REFERENTIEL


def autoriser(db,user,action=None):
    ctx=social.autoriser(db,user,action)
    if not db.scalar(text("SELECT to_regclass('public.paie_controles_ir_annuels') IS NOT NULL")):raise HTTPException(503,'Installer la migration118 du contrôle annuel IR.')
    return ctx


def sortie(db,row,user,ctx,reutilise=False):
    r=dict(row)
    if brut.empreinte(r['contenu'])!=r['empreinte']:raise HTTPException(409,'Empreinte du contrôle IR incohérente.')
    source=r['contenu'].get('source_frais_annuels')
    if source is not None:
        if not db.scalar(text("SELECT to_regclass('public.paie_ir_sources_annuelles') IS NOT NULL")):raise HTTPException(503,'Installer la migration122 pour consulter ce lien annuel.')
        lien=db.execute(text('SELECT l.frais_annuels_id,f.empreinte FROM paie_ir_sources_annuelles l JOIN paie_controles_frais_annuels f ON f.id=l.frais_annuels_id AND f.societe_id=l.societe_id WHERE l.ir_id=:i AND l.societe_id=:s'),{'i':r['id'],'s':user['societe_id']}).mappings().first()
        if not lien or lien['frais_annuels_id']!=source['id'] or lien['empreinte']!=source['empreinte']:raise HTTPException(409,'Lien du contrôle IR vers son RNI annuel incomplet ou incohérent.')
    if not (w.AUDIT in ctx['capacites'] or r['auteur_id']==user['id'] or 'personnel.approuver' in ctx['capacites']):r['motif']=None
    r.pop('cle_idempotence',None);r.pop('demande_sha256',None);r['reutilise']=reutilise;return r


@w.transaction
def simuler(db,user,data):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id'];demande=brut.empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'}))
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:ir:annuel:{sid}'})
    ancien=db.execute(text('SELECT * FROM paie_controles_ir_annuels WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Clé de reprise déjà utilisée pour une autre demande.')
        return sortie(db,ancien,user,ctx,True)
    c=calculer(data)
    i=db.scalar(text('INSERT INTO paie_controles_ir_annuels(societe_id,annee,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:a,:k,:d,CAST(:c AS jsonb),:h,:u,:m) RETURNING id'),
      {'s':sid,'a':data.annee,'k':str(data.cle_idempotence),'d':demande,'c':brut.canonique(c),'h':brut.empreinte(c),'u':user['id'],'m':data.motif})
    return sortie(db,db.execute(text('SELECT * FROM paie_controles_ir_annuels WHERE id=:i AND societe_id=:s'),{'i':i,'s':sid}).mappings().one(),user,ctx)


def lire(db,user,ident):
    ctx=autoriser(db,user);r=db.execute(text('SELECT * FROM paie_controles_ir_annuels WHERE id=:i AND societe_id=:s'),{'i':ident,'s':user['societe_id']}).mappings().first()
    if not r:raise HTTPException(404,'Contrôle IR introuvable dans cette société.')
    return sortie(db,r,user,ctx)


def lister(db,user,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'o':decalage,'l':limite}
    return {'total':db.scalar(text('SELECT count(*) FROM paie_controles_ir_annuels WHERE societe_id=:s'),p),
      'elements':[dict(x) for x in db.execute(text("SELECT id,annee,auteur_id,cree_at,contenu#>>'{source_frais_annuels,id}' AS source_frais_id,contenu#>>'{declaration,revenu_net_imposable_annuel}' AS rni,contenu->>'ir_annuel_arithmetique' AS ir FROM paie_controles_ir_annuels WHERE societe_id=:s ORDER BY id DESC OFFSET :o LIMIT :l"),p).mappings()]}


def referentiel(db,user):
    autoriser(db,user);return {'contenu':REFERENTIEL,'empreinte':brut.empreinte(REFERENTIEL),'certification_automatique':False}
