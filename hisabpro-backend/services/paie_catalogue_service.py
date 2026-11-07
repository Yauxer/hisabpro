"""Versions append-only ;aucune comptabilisation ni règle légale préchargée."""
from datetime import date
from decimal import Decimal
import json
from fastapi import HTTPException
from sqlalchemy import text
from services import personnel_workflow_service as w
from services.paie_catalogue_schemas import Contenu
from services.paie_qualification_ir_service import exiger_installation,qualifie

def autoriser(db,user,action=None):
    ctx=w.autoriser(db,user,action)
    if w.REMUNERATION not in ctx['capacites']:raise HTTPException(403,'Habilitation rémunération requise pour les éléments de paie.')
    if not all(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'),{'t':'public.'+t}) for t in ['paie_rubriques','paie_rubrique_versions']):
        raise HTTPException(503,'Installer la migration113 du catalogue de paie.')
    return ctx

def rubrique(db,sid,ident,bloquer=False):
    if bloquer:db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:rubrique:{sid}:{ident}'})
    r=db.execute(text('SELECT * FROM paie_rubriques WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid}).mappings().first()
    if not r:raise HTTPException(404,'Rubrique introuvable dans cette société.')
    return r

def verifier_contenu(db,sid,code,c):
    exiger_installation(db,c,'frais_professionnels')
    if code in c.incompatibilites:raise HTTPException(400,'Une rubrique ne peut être incompatible avec elle-même.')
    if c.incompatibilites:
        connus=set(db.scalars(text('SELECT code FROM paie_rubriques WHERE societe_id=:s'),{'s':sid}))
        if not set(c.incompatibilites)<=connus:raise HTTPException(400,'Une incompatibilité référence une rubrique inconnue de cette société.')
    if c.compte_charge and not db.scalar(text('SELECT EXISTS(SELECT 1 FROM comptes_societe WHERE societe_id=:s AND numero=:n AND actif)'),{'s':sid,'n':c.compte_charge}):
        raise HTTPException(400,'Compte actif introuvable dans le plan de cette société ;aucun compte de secours.')

def ajouter(db,user,r,c,motif):
    verifier_contenu(db,user['societe_id'],r['code'],c)
    numero=db.scalar(text('SELECT coalesce(max(numero),0)+1 FROM paie_rubrique_versions WHERE rubrique_id=:i'),{'i':r['id']})
    ident=db.scalar(text('INSERT INTO paie_rubrique_versions(societe_id,rubrique_id,numero,contenu,date_debut,date_fin,prepare_par,motif) '
      'VALUES(:s,:r,:n,CAST(:c AS jsonb),:d,:f,:u,:m) RETURNING id'),{'s':user['societe_id'],'r':r['id'],'n':numero,'c':json.dumps(c.model_dump(mode='json'),ensure_ascii=False),'d':c.date_debut,'f':c.date_fin,'u':user['id'],'m':motif})
    return {'id':ident,'rubrique_id':r['id'],'numero':numero,'statut':'PROPOSEE'}

@w.transaction
def creer(db,user,data):
    autoriser(db,user,'proposer')
    if db.scalar(text('SELECT EXISTS(SELECT 1 FROM paie_rubriques WHERE societe_id=:s AND code=:c)'),{'s':user['societe_id'],'c':data.code}):
        raise HTTPException(409,'Ce code de rubrique existe déjà. Ouvrez sa fiche pour proposer une nouvelle version.')
    ident=db.scalar(text('INSERT INTO paie_rubriques(societe_id,code,cree_par) VALUES(:s,:c,:u) RETURNING id'),{'s':user['societe_id'],'c':data.code,'u':user['id']})
    return ajouter(db,user,{'id':ident,'code':data.code},data.contenu,data.motif)

@w.transaction
def proposer(db,user,ident,data):
    autoriser(db,user,'proposer');r=rubrique(db,user['societe_id'],ident,True)
    version=db.scalar(text('SELECT max(numero) FROM paie_rubrique_versions WHERE rubrique_id=:i'),{'i':ident})
    if version!=data.version_attendue:raise HTTPException(409,'Version périmée. Rechargez la rubrique.')
    return ajouter(db,user,r,data.contenu,data.motif)

def lire(db,user,ident):
    autoriser(db,user);r=dict(rubrique(db,user['societe_id'],ident))
    r['versions']=[dict(x) for x in db.execute(text('SELECT * FROM paie_rubrique_versions WHERE rubrique_id=:i AND societe_id=:s ORDER BY numero DESC'),{'i':ident,'s':user['societe_id']}).mappings()]
    return r

def lister(db,user,au,recherche,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'q':'%'+(recherche or '')+'%','au':au,'o':decalage,'l':limite}
    filtre="r.societe_id=:s AND (r.code ILIKE :q OR EXISTS(SELECT 1 FROM paie_rubrique_versions x WHERE x.rubrique_id=r.id AND x.contenu->>'libelle' ILIKE :q))"
    total=db.scalar(text('SELECT count(*) FROM paie_rubriques r WHERE '+filtre),p)
    rows=db.execute(text('SELECT r.*,derniere.id AS derniere_id,derniere.numero AS derniere_numero,derniere.statut AS derniere_statut,derniere.contenu AS dernier_contenu,'
      'courante.id AS courante_id,courante.contenu AS contenu_applicable FROM paie_rubriques r '
      'LEFT JOIN LATERAL(SELECT v.* FROM paie_rubrique_versions v WHERE v.rubrique_id=r.id ORDER BY numero DESC LIMIT 1) derniere ON true '
      'LEFT JOIN LATERAL(SELECT v.* FROM paie_rubrique_versions v WHERE v.rubrique_id=r.id AND v.statut=\'APPROUVEE\' AND v.date_debut<=:au ORDER BY date_debut DESC LIMIT 1) courante ON (courante.date_fin IS NULL OR courante.date_fin>=:au) '
      'WHERE '+filtre+' ORDER BY r.id DESC OFFSET :o LIMIT :l'),p).mappings().all()
    return {'total':total,'elements':[dict(x) for x in rows],'au':au,'avertissement':'Catalogue uniquement ;aucune paie ou écriture générée. Une approbation du catalogue ne certifie pas les règles.'}

@w.transaction
def decider(db,user,ident,data,approuver):
    ctx=autoriser(db,user,'approuver');sid=user['societe_id']
    # Ordre de verrous identique à proposer :racine avant version.
    rid=db.scalar(text('SELECT rubrique_id FROM paie_rubrique_versions WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid})
    if rid is None:raise HTTPException(404,'Version introuvable dans cette société.')
    r=rubrique(db,sid,rid,True)
    v=db.execute(text('SELECT * FROM paie_rubrique_versions WHERE id=:i AND societe_id=:s FOR UPDATE'),{'i':ident,'s':sid}).mappings().one()
    if v['statut']!='PROPOSEE':raise HTTPException(409,'Cette version a déjà reçu une décision.')
    if approuver:
        from services.personnel_acces_service import validation_unique
        if (v['prepare_par']==user['id'] and not validation_unique(db,sid)) or not data.independance_confirmee:raise HTTPException(403,'Un décideur indépendant du préparateur est requis.')
        if not db.scalar(text('SELECT hisabpro_personnel_membre(:s,:u,false)'),{'s':sid,'u':v['prepare_par']}):raise HTTPException(409,'Le préparateur doit être actif pour approuver.')
        c=Contenu.model_validate(v['contenu']);verifier_contenu(db,sid,r['code'],c)
        if any(x.statut_reglementaire=='VALIDE' for x in [c.regles.IR,c.regles.CNSS,c.regles.AMO]) or qualifie(c,'frais_professionnels'):
            if 'personnel.valider_regles_paie' not in ctx['capacites']:raise HTTPException(403,'Habilitation dédiée à la qualification réglementaire de paie requise.')
            if not data.verification_reglementaire_confirmee:raise HTTPException(400,'Confirmer le contrôle des textes,preuves et conditions des règles déclarées validées.')
        # Une approbation rétroactive ne doit pas déplacer la règle d'une période déjà passée.
        derniere=db.scalar(text("SELECT max(date_debut) FROM paie_rubrique_versions WHERE rubrique_id=:i AND statut='APPROUVEE'"),{'i':rid})
        if derniere is not None and c.date_debut<=max(derniere,date.today()):raise HTTPException(409,'La nouvelle version approuvée doit commencer dans le futur et après la dernière version approuvée.')
    statut='APPROUVEE' if approuver else 'REJETEE'
    db.execute(text('UPDATE paie_rubrique_versions SET statut=:st,decision_par=:u,decision_at=clock_timestamp(),motif_decision=:m,reference_controle=:ref,verification_reglementaire_confirmee=:v WHERE id=:i'),
      {'st':statut,'u':user['id'],'m':data.motif,'ref':data.reference_controle,'v':data.verification_reglementaire_confirmee if approuver else False,'i':ident})
    return {'id':ident,'statut':statut,'certification_automatique':False}

def ventiler(contenu,montant):
    """Aperçu arithmétique à l'opération ;jamais cumul annuel ou liquidation."""
    result={}
    for regime in ('IR','CNSS','AMO'):
        regle=getattr(contenu.regles,regime)
        r=regle.model_dump()
        if r['traitement']=='A_VERIFIER':result[regime]={'soumis':None,'exonere':None,'alerte':'Traitement à vérifier'};continue
        if r['traitement']=='PLAFOND_MONTANT' and r['unite']!='operation':
            result[regime]={'soumis':None,'exonere':None,'alerte':'Cumul de période et éligibilité à contrôler ;aperçu non calculé'};continue
        ex=montant if r['traitement']=='EXONERE' else min(montant,regle.plafond) if r['traitement']=='PLAFOND_MONTANT' else Decimal(0)
        result[regime]={'soumis':format(montant-ex,'.2f'),'exonere':format(ex,'.2f'),'alerte':'Simulation pédagogique ;conditions et justificatifs non évalués automatiquement'}
    return result

def apercu(db,user,ident,data):
    autoriser(db,user);v=db.execute(text('SELECT contenu FROM paie_rubrique_versions WHERE id=:i AND societe_id=:s'),{'i':ident,'s':user['societe_id']}).scalar()
    if v is None:raise HTTPException(404,'Version introuvable dans cette société.')
    return {'mode':'SIMULATION_NON_VALIDEE','montant':format(data.montant,'.2f'),'regimes':ventiler(Contenu.model_validate(v),data.montant),'utilisable_paie_definitive':False}
