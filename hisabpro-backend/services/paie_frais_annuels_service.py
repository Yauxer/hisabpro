from fastapi import HTTPException
from sqlalchemy import text
from services import personnel_workflow_service as w,paie_bases_fiscales_service as bases,paie_campagnes_service as brut
from services.paie_frais_annuels_moteur import calculer,REFERENTIEL


def autoriser(db,user,action=None):
    ctx=bases.autoriser(db,user,action)
    if not all(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'),{'t':'public.'+t}) for t in ['paie_controles_frais_annuels','paie_controle_frais_sources']):raise HTTPException(503,'Installer la migration 121 des frais annuels.')
    return ctx


def sortie(db,row,user,ctx,reutilise=False):
    r=brut.sortie(row,user,ctx,reutilise)
    liens=[dict(x) for x in db.execute(text('SELECT preparation_id,periode FROM paie_controle_frais_sources WHERE controle_id=:i AND societe_id=:s ORDER BY periode'),{'i':r['id'],'s':user['societe_id']}).mappings()]
    attendu=[{'preparation_id':x['preparation_id'],'periode':x['periode']} for x in r['contenu']['sources']]
    if brut.empreinte(liens)!=brut.empreinte(attendu):raise HTTPException(409,'Liens des sources annuelles incomplets ou incohérents.')
    return r


@w.transaction
def simuler(db,user,data):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id'];demande=brut.empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'}))
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:frais-annuels:{sid}:{data.employe_id}:{data.annee}'})
    ancien=db.execute(text('SELECT * FROM paie_controles_frais_annuels WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Clé de reprise déjà utilisée pour un autre contrôle annuel.')
        return sortie(db,ancien,user,ctx,True)
    sources=[];mois=set()
    for ident in data.preparation_ids:
        p=bases.lire(db,user,ident);c=p['contenu'];periode=c['periode']
        if not periode.startswith(str(data.annee)+'-'):raise HTTPException(400,'Préparation hors de l’année demandée.')
        if periode in mois:raise HTTPException(400,'Choisir une seule préparation par mois pour ce salarié ; aucun cumul de versions.')
        mois.add(periode);e=bases.verifier_sources_salarie(db,user,ctx,p,data.employe_id)
        sources.append({'preparation_id':p['id'],'numero':p['numero'],'empreinte':p['empreinte'],'periode':periode,'social_id':c['social_id'],'brut_id':c['brut_id'],'employe':e})
    sources.sort(key=lambda x:x['periode']);r=calculer(data,sources)
    contenu={**r,'mode':'CONTROLE_FRAIS_ANNUELS_NON_VALIDE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT',
        'employe_id':data.employe_id,'nom':sources[-1]['employe']['nom'],'matricule':sources[-1]['employe']['matricule'],
        'declaration':data.model_dump(mode='json',exclude={'cle_idempotence','motif'}),'sources':sources,
        'complet_pour_rni_arithmetique':r['rni_annuel_arithmetique_avant_arrondis'] is not None and not r['anomalies'],
        'avertissement':'Cumuls des périodes explicitement choisies, sans extrapolation. Frais du cadre annuel général confirmé ; autres déductions déclarées après contrôle. Le RNI est arithmétique avant arrondis, sans retenue mensuelle, versement, net, bulletin ou écriture. Les dates de paiement ne sont pas déduites des périodes.'}
    ident=db.scalar(text('INSERT INTO paie_controles_frais_annuels(societe_id,employe_id,annee,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:e,:a,:k,:d,CAST(:c AS jsonb),:h,:u,:m) RETURNING id'),
        {'s':sid,'e':data.employe_id,'a':data.annee,'k':str(data.cle_idempotence),'d':demande,'c':brut.canonique(contenu),'h':brut.empreinte(contenu),'u':user['id'],'m':data.motif})
    for x in sources:db.execute(text('INSERT INTO paie_controle_frais_sources(controle_id,societe_id,preparation_id,periode,auteur_id) VALUES(:i,:s,:p,:d,:u)'),{'i':ident,'s':sid,'p':x['preparation_id'],'d':x['periode'],'u':user['id']})
    return sortie(db,db.execute(text('SELECT * FROM paie_controles_frais_annuels WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid}).mappings().one(),user,ctx)


def lire(db,user,ident):
    ctx=autoriser(db,user);r=db.execute(text('SELECT * FROM paie_controles_frais_annuels WHERE id=:i AND societe_id=:s'),{'i':ident,'s':user['societe_id']}).mappings().first()
    if not r:raise HTTPException(404,'Contrôle annuel introuvable dans cette société.')
    return sortie(db,r,user,ctx)


def lister(db,user,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'o':decalage,'l':limite}
    return {'total':db.scalar(text('SELECT count(*) FROM paie_controles_frais_annuels WHERE societe_id=:s'),p),
        'elements':[dict(x) for x in db.execute(text("SELECT id,annee,employe_id,contenu->>'nom' AS nom,contenu->>'matricule' AS matricule,contenu->>'nombre_mois' AS nombre_mois,contenu->>'rni_annuel_arithmetique_avant_arrondis' AS rni FROM paie_controles_frais_annuels WHERE societe_id=:s ORDER BY id DESC OFFSET :o LIMIT :l"),p).mappings()]}


def options(db,user,employe_id=None):
    autoriser(db,user);p={'s':user['societe_id'],'e':employe_id}
    employes=[dict(x) for x in db.execute(text("SELECT DISTINCT ON ((e->>'employe_id')::int) (e->>'employe_id')::int AS id,e->>'nom' AS nom,e->>'matricule' AS matricule FROM paie_preparations_fiscales p CROSS JOIN LATERAL jsonb_array_elements(p.contenu->'employes') e WHERE p.societe_id=:s AND p.contenu->>'periode' LIKE '2026-%' ORDER BY (e->>'employe_id')::int,p.id DESC LIMIT 501"),p).mappings()]
    if len(employes)>500:raise HTTPException(409,'Plus de500 salariés préparés ; affiner le périmètre avant le contrôle annuel.')
    preparations=[]
    if employe_id is not None:
        if not any(x['id']==employe_id for x in employes):raise HTTPException(404,'Aucune préparation de ce salarié dans cette société.')
        preparations=[dict(x) for x in db.execute(text("SELECT p.id,p.numero,p.contenu->>'periode' AS periode,jsonb_array_length(e->'anomalies')=0 AS complet FROM paie_preparations_fiscales p CROSS JOIN LATERAL jsonb_array_elements(p.contenu->'employes') e WHERE p.societe_id=:s AND (e->>'employe_id')::int=:e AND p.contenu->>'periode' LIKE '2026-%' ORDER BY p.id DESC LIMIT 501"),p).mappings()]
        if len(preparations)>500:raise HTTPException(409,'Plus de500 préparations ; aucun choix tronqué autorisé.')
    return {'employes':employes,'preparations':preparations,'annee':2026}


def verifier_sources_courantes(db,user,ctx,source):
    c=source['contenu']
    if c['referentiel_sha256']!=brut.empreinte(REFERENTIEL):raise HTTPException(409,'Référentiel des frais annuels différent ; établir un nouveau contrôle avec la règle applicable.')
    for x in c['sources']:
        p=bases.lire(db,user,x['preparation_id'])
        if p['empreinte']!=x['empreinte']:raise HTTPException(409,'Empreinte d’une source annuelle incohérente.')
        bases.verifier_sources_salarie(db,user,ctx,p,c['employe_id'])
