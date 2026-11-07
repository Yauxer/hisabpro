"""Versions append-only ;aucune comptabilisation ni règle légale préchargée."""
from datetime import date
from decimal import Decimal
import json
from fastapi import HTTPException
from sqlalchemy import text
from services import personnel_workflow_service as w
from services.paie_social_schemas import Contenu
from services.paie_qualification_ir_service import exiger_installation,qualifie

def autoriser(db,user,action=None):
    ctx=w.autoriser(db,user,action)
    if w.REMUNERATION not in ctx['capacites']:raise HTTPException(403,'Habilitation rémunération requise pour les éléments de paie.')
    if not all(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'),{'t':'public.'+t}) for t in ['paie_branches_sociales','paie_branche_sociale_versions']):
        raise HTTPException(503,'Installer la migration116 du référentiel social.')
    return ctx

def branche(db,sid,ident,bloquer=False):
    if bloquer:db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:branche:{sid}:{ident}'})
    r=db.execute(text('SELECT * FROM paie_branches_sociales WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid}).mappings().first()
    if not r:raise HTTPException(404,'Branche introuvable dans cette société.')
    return r

def verifier_contenu(db,sid,r,c):
    exiger_installation(db,c,'deductibilite_ir')
    if c.applicabilite=='APPLICABLE' and db.scalar(text('SELECT hisabpro_paie_social_conflit(:s,:r,:d,:f,CAST(:c AS jsonb))'),
      {'s':sid,'r':r['id'],'d':c.date_debut,'f':c.date_fin,'c':json.dumps(c.composants)}):
        raise HTTPException(409,'Un composant est déjà couvert dans ce régime sur cette période. Modifier la composition ou les dates, sans double comptage.')

def ajouter(db,user,r,c,motif):
    exiger_installation(db,c,'deductibilite_ir')
    # Une proposition peut documenter un conflit ; celui-ci bloque son approbation.
    numero=db.scalar(text('SELECT coalesce(max(numero),0)+1 FROM paie_branche_sociale_versions WHERE branche_id=:i'),{'i':r['id']})
    ident=db.scalar(text('INSERT INTO paie_branche_sociale_versions(societe_id,branche_id,numero,contenu,date_debut,date_fin,prepare_par,motif) '
      'VALUES(:s,:r,:n,CAST(:c AS jsonb),:d,:f,:u,:m) RETURNING id'),{'s':user['societe_id'],'r':r['id'],'n':numero,'c':json.dumps(c.model_dump(mode='json'),ensure_ascii=False),'d':c.date_debut,'f':c.date_fin,'u':user['id'],'m':motif})
    return {'id':ident,'branche_id':r['id'],'numero':numero,'statut':'PROPOSEE'}

@w.transaction
def creer(db,user,data):
    autoriser(db,user,'proposer')
    if db.scalar(text('SELECT EXISTS(SELECT 1 FROM paie_branches_sociales WHERE societe_id=:s AND code=:c AND regime=:g)'),{'s':user['societe_id'],'c':data.code,'g':data.regime}):
        raise HTTPException(409,'Ce code de branche existe déjà. Ouvrez sa fiche pour proposer une nouvelle version.')
    ident=db.scalar(text('INSERT INTO paie_branches_sociales(societe_id,code,regime,cree_par) VALUES(:s,:c,:g,:u) RETURNING id'),{'s':user['societe_id'],'c':data.code,'g':data.regime,'u':user['id']})
    return ajouter(db,user,{'id':ident,'code':data.code,'regime':data.regime},data.contenu,data.motif)

@w.transaction
def proposer(db,user,ident,data):
    autoriser(db,user,'proposer');r=branche(db,user['societe_id'],ident,True)
    version=db.scalar(text('SELECT max(numero) FROM paie_branche_sociale_versions WHERE branche_id=:i'),{'i':ident})
    if version!=data.version_attendue:raise HTTPException(409,'Version périmée. Rechargez la branche.')
    return ajouter(db,user,r,data.contenu,data.motif)

def lire(db,user,ident):
    autoriser(db,user);r=dict(branche(db,user['societe_id'],ident))
    r['versions']=[dict(x) for x in db.execute(text('SELECT * FROM paie_branche_sociale_versions WHERE branche_id=:i AND societe_id=:s ORDER BY numero DESC'),{'i':ident,'s':user['societe_id']}).mappings()]
    return r

def lister(db,user,au,recherche,decalage,limite,regime=None):
    autoriser(db,user);p={'s':user['societe_id'],'q':'%'+(recherche or '')+'%','au':au,'o':decalage,'l':limite,'g':regime}
    filtre="r.societe_id=:s AND (CAST(:g AS text) IS NULL OR r.regime=:g) AND (r.code ILIKE :q OR EXISTS(SELECT 1 FROM paie_branche_sociale_versions x WHERE x.branche_id=r.id AND x.contenu->>'libelle' ILIKE :q))"
    total=db.scalar(text('SELECT count(*) FROM paie_branches_sociales r WHERE '+filtre),p)
    rows=db.execute(text('SELECT r.*,derniere.id AS derniere_id,derniere.numero AS derniere_numero,derniere.statut AS derniere_statut,derniere.contenu AS dernier_contenu,'
      'courante.id AS courante_id,courante.contenu AS contenu_applicable FROM paie_branches_sociales r '
      'LEFT JOIN LATERAL(SELECT v.* FROM paie_branche_sociale_versions v WHERE v.branche_id=r.id ORDER BY numero DESC LIMIT 1) derniere ON true '
      'LEFT JOIN LATERAL(SELECT v.* FROM paie_branche_sociale_versions v WHERE v.branche_id=r.id AND v.statut=\'APPROUVEE\' AND v.date_debut<=:au ORDER BY date_debut DESC LIMIT 1) courante ON (courante.date_fin IS NULL OR courante.date_fin>=:au) '
      'WHERE '+filtre+' ORDER BY r.id DESC OFFSET :o LIMIT :l'),p).mappings().all()
    return {'total':total,'elements':[dict(x) for x in rows],'au':au,'avertissement':'Catalogue uniquement ;aucune paie ou écriture générée. Une approbation du référentiel social ne certifie pas les règles.'}

@w.transaction
def decider(db,user,ident,data,approuver):
    ctx=autoriser(db,user,'approuver');sid=user['societe_id']
    # Ordre de verrous identique à proposer :racine avant version.
    rid=db.scalar(text('SELECT branche_id FROM paie_branche_sociale_versions WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid})
    if rid is None:raise HTTPException(404,'Version introuvable dans cette société.')
    r=branche(db,sid,rid,True)
    v=db.execute(text('SELECT * FROM paie_branche_sociale_versions WHERE id=:i AND societe_id=:s FOR UPDATE'),{'i':ident,'s':sid}).mappings().one()
    if v['statut']!='PROPOSEE':raise HTTPException(409,'Cette version a déjà reçu une décision.')
    if approuver:
        from services.personnel_acces_service import validation_unique
        if (v['prepare_par']==user['id'] and not validation_unique(db,sid)) or not data.independance_confirmee:raise HTTPException(403,'Un décideur indépendant du préparateur est requis.')
        if not db.scalar(text('SELECT hisabpro_personnel_membre(:s,:u,false)'),{'s':sid,'u':v['prepare_par']}):raise HTTPException(409,'Le préparateur doit être actif pour approuver.')
        c=Contenu.model_validate(v['contenu']);verifier_contenu(db,sid,r,c)
        if c.statut_reglementaire=='VALIDE' or qualifie(c,'deductibilite_ir'):
            if 'personnel.valider_regles_paie' not in ctx['capacites']:raise HTTPException(403,'Habilitation dédiée à la qualification réglementaire de paie requise.')
            if not data.verification_reglementaire_confirmee:raise HTTPException(400,'Confirmer le contrôle des textes,preuves et conditions des règles déclarées validées.')
        # Une approbation rétroactive ne doit pas déplacer la règle d'une période déjà passée.
        derniere=db.scalar(text("SELECT max(date_debut) FROM paie_branche_sociale_versions WHERE branche_id=:i AND statut='APPROUVEE'"),{'i':rid})
        if derniere is not None and c.date_debut<=max(derniere,date.today()):raise HTTPException(409,'La nouvelle version approuvée doit commencer dans le futur et après la dernière version approuvée.')
    statut='APPROUVEE' if approuver else 'REJETEE'
    db.execute(text('UPDATE paie_branche_sociale_versions SET statut=:st,decision_par=:u,decision_at=clock_timestamp(),motif_decision=:m,reference_controle=:ref,verification_reglementaire_confirmee=:v WHERE id=:i'),
      {'st':statut,'u':user['id'],'m':data.motif,'ref':data.reference_controle,'v':data.verification_reglementaire_confirmee if approuver else False,'i':ident})
    return {'id':ident,'statut':statut,'certification_automatique':False}
