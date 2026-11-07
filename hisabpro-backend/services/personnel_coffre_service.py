"""Pièces RH privées,configuration explicite et audit sans corps de document."""
import base64
from fastapi import HTTPException
from sqlalchemy import text
from services import personnel_workflow_service as workflow
from services.personnel_acces_service import contexte
from services.personnel_coffre_crypto import charger,ConfigurationCoffreError,IntegriteCoffreError

MAX_PIECE=4*1024*1024

def schema(db):
    if not db.scalar(text("SELECT to_regclass('public.personnel_coffre_pieces') IS NOT NULL AND to_regclass('public.personnel_coffre_politiques') IS NOT NULL")):
        raise HTTPException(503,'Installer la migration111 avant le coffre RH.')

def trousseau():
    try:return charger()
    except ConfigurationCoffreError:raise HTTPException(503,'Clés du coffre RH indisponibles. Contacter l’administrateur de déploiement.') from None

def politique(db,sid):
    return db.execute(text('SELECT * FROM personnel_coffre_politiques WHERE societe_id=:s ORDER BY id DESC LIMIT 1'),{'s':sid}).mappings().first()

def lecture_autorisee(db,user):
    ctx=workflow.autoriser(db,user);schema(db)
    if workflow.SENSIBLE not in ctx['capacites']:raise HTTPException(403,'Habilitation identifiants sensibles requise pour le coffre RH.')
    return ctx

def etat(db,user):
    installe=db.bind.dialect.name=='postgresql' and bool(db.scalar(text("SELECT to_regclass('public.personnel_coffre_pieces') IS NOT NULL AND to_regclass('public.personnel_coffre_politiques') IS NOT NULL")))
    if not installe:return {'schema_installe':False,'banque_disponible':False,'cles_configurees':False,'politique_declaree':False,'collecte_autorisee':False}
    if user['role']!='admin':lecture_autorisee(db,user)
    else:
        workflow.verifier_schema(db);schema(db)
    ctx=contexte(db,user);p=politique(db,user['societe_id'])
    try:charger();cles=True
    except ConfigurationCoffreError:cles=False
    r={'schema_installe':True,'banque_disponible':banque_installee(db),'cles_configurees':cles,'politique_declaree':p is not None,'collecte_autorisee':bool(cles and p and ctx['module_actif'] and ctx['mode']=='protege')}
    if user['role']=='admin':r['politique']=dict(p) if p else None
    return r

@workflow.transaction
def declarer(db,user,data):
    from auth import exiger_admin
    from services.utilisateurs_acces_service import verrouiller_administration,verifier_admin_apres_verrou
    exiger_admin(user);verrouiller_administration(db,user['societe_id']);verifier_admin_apres_verrou(db,user['id'],user['societe_id'])
    schema(db);trousseau()
    p={'s':user['societe_id'],'u':user['id'],**data.model_dump(exclude={'confirmation'})}
    ident=db.scalar(text('INSERT INTO personnel_coffre_politiques(societe_id,reference_garde_cles,reference_conservation,reference_rotation_sauvegarde,motif,declaree_par) '
      'VALUES(:s,:reference_garde_cles,:reference_conservation,:reference_rotation_sauvegarde,:motif,:u) RETURNING id'),p)
    return {'id':ident,'declaration_enregistree':True,'validation_humaine':'Références déclarées par l’administrateur ;aucune certification automatique.'}

def collecte(db,user,eid):
    ctx=workflow.autoriser(db,user,'proposer');schema(db)
    if workflow.SENSIBLE not in ctx['capacites']:raise HTTPException(403,'Habilitation identifiants sensibles requise pour le coffre RH.')
    d=workflow.dossier(db,user['societe_id'],eid,bloquer=True)
    p=politique(db,user['societe_id'])
    if not p:raise HTTPException(409,'Déclarer les références de garde des clés,conservation et rotation/sauvegarde avant toute collecte RH.')
    return d,p,trousseau()

def type_piece(brut):
    if brut.startswith(b'%PDF-'):return 'application/pdf'
    if brut.startswith(b'\x89PNG\r\n\x1a\n'):return 'image/png'
    if brut.startswith(b'\xff\xd8\xff'):return 'image/jpeg'
    raise HTTPException(400,'Pièce attendue :PDF,PNG ouJPEG. Le contenu ne correspond pas à un type autorisé.')

@workflow.transaction
def deposer(db,user,eid,categorie,brut):
    d,p,cles=collecte(db,user,eid)
    if categorie not in {'contrat','banque','autre'}:raise HTTPException(400,'Catégorie de pièce non autorisée.')
    if not brut or len(brut)>MAX_PIECE:raise HTTPException(413,'Pièce vide ou dépassant la limite de4Mio.')
    mime=type_piece(brut)
    ident=db.scalar(text("SELECT nextval(pg_get_serial_sequence('public.personnel_coffre_pieces','id'))"))
    portee={'societe_id':user['societe_id'],'employe_id':eid,'piece_id':ident}
    cle,jeton=cles.chiffrer('piece-rh',portee,{'contenu':base64.b64encode(brut).decode('ascii'),'mime':mime})
    db.execute(text('INSERT INTO personnel_coffre_pieces(id,societe_id,employe_id,politique_id,categorie,mime,octets,cle_id,contenu_chiffre,deposee_par) '
      'VALUES(:i,:s,:e,:p,:cat,:mime,:n,:cle,:j,:u)'),{'i':ident,'s':user['societe_id'],'e':eid,'p':p['id'],'cat':categorie,'mime':mime,'n':len(brut),'cle':cle,'j':jeton,'u':user['id']})
    workflow.evenement(db,user,d,'PIECE_DEPOSEE','Pièce chiffrée déposée ;identifiant '+str(ident))
    return {'id':ident,'categorie':categorie,'mime':mime,'octets':len(brut),'statut':'Déposée ;contenu à contrôler humainement'}

def lister(db,user,eid):
    lecture_autorisee(db,user);workflow.dossier(db,user['societe_id'],eid)
    return db.execute(text('SELECT id,categorie,mime,octets,deposee_par,deposee_at FROM personnel_coffre_pieces '
      'WHERE societe_id=:s AND employe_id=:e ORDER BY id DESC'),{'s':user['societe_id'],'e':eid}).mappings().all()

@workflow.transaction
def telecharger(db,user,eid,ident):
    lecture_autorisee(db,user);d=workflow.dossier(db,user['societe_id'],eid)
    r=db.execute(text('SELECT * FROM personnel_coffre_pieces WHERE id=:i AND societe_id=:s AND employe_id=:e'),{'i':ident,'s':user['societe_id'],'e':eid}).mappings().first()
    if not r:raise HTTPException(404,'Pièce introuvable dans ce dossier.')
    try:
        donnees=trousseau().dechiffrer(r['cle_id'],r['contenu_chiffre'],'piece-rh',{'societe_id':user['societe_id'],'employe_id':eid,'piece_id':ident})
        brut=base64.b64decode(donnees['contenu'],validate=True)
        if len(brut)!=r['octets'] or donnees['mime']!=r['mime'] or type_piece(brut)!=r['mime']:raise IntegriteCoffreError()
    except ConfigurationCoffreError:raise HTTPException(503,'Une clé historique du coffre RH est indisponible.') from None
    except (IntegriteCoffreError,ValueError,TypeError,KeyError):raise HTTPException(409,'Intégrité de la pièce RH non vérifiée ;aucun contenu restitué.') from None
    workflow.evenement(db,user,d,'PIECE_CONSULTEE','Téléchargement privé de la pièce '+str(ident))
    return brut,r['mime']

def banque_installee(db):
    return bool(db.scalar(text("SELECT to_regclass('public.personnel_banque_versions') IS NOT NULL")))

def masque_banque(valeur):
    return '•••• '+''.join(c for c in valeur if c.isalnum())[-4:]

def controler_notes(valeur,*notes):
    secret=''.join(c for c in valeur.casefold() if c.isalnum())
    if secret and any(secret in ''.join(c for c in (n or '').casefold() if c.isalnum()) for n in notes):
        raise HTTPException(400,'Ne recopiez pas les coordonnées bancaires dans le motif ou la référence ;utilisez uniquement le champ privé prévu.')

def proposer_banque(db,user,d,data):
    if not banque_installee(db):raise HTTPException(503,'Installer la migration112 avant les coordonnées bancaires RH.')
    _,p,cles=collecte(db,user,d['employe_id']);c=data.contenu
    secret=c.rib_iban.get_secret_value();controler_notes(secret,data.motif,c.reference_justificatif)
    if c.piece_id is not None and not db.scalar(text('SELECT EXISTS(SELECT 1 FROM personnel_coffre_pieces WHERE id=:i AND societe_id=:s AND employe_id=:e)'),{'i':c.piece_id,'s':user['societe_id'],'e':d['employe_id']}):
        raise HTTPException(404,'Pièce justificative introuvable dans ce dossier.')
    contenu={'date_effet':c.date_effet.isoformat(),'masque':masque_banque(secret),'piece_id':c.piece_id,'reference_justificatif':c.reference_justificatif}
    workflow.verifier_contenu(db,d,'BANQUE',contenu)
    r=workflow.ajouter_demande(db,user,d,'BANQUE',contenu,data.motif);i=r['id']
    cle,jeton=cles.chiffrer('banque-rh',{'societe_id':user['societe_id'],'employe_id':d['employe_id'],'demande_id':i},
       {'rib_iban':secret,'banque':c.banque,'titulaire':c.titulaire,'date_effet':c.date_effet.isoformat(),'piece_id':c.piece_id})
    db.execute(text('INSERT INTO personnel_banque_versions(demande_id,societe_id,employe_id,politique_id,piece_id,version,date_effet,cle_id,contenu_chiffre,masque) '
      'SELECT :i,:s,:e,:p,:piece,coalesce(max(version),0)+1,:dt,:cle,:j,:m FROM personnel_banque_versions WHERE societe_id=:s AND employe_id=:e'),
      {'i':i,'s':user['societe_id'],'e':d['employe_id'],'p':p['id'],'piece':c.piece_id,'dt':c.date_effet,'cle':cle,'j':jeton,'m':contenu['masque']})
    return r

def contenu_banque(db,user,eid,ident):
    r=db.execute(text('SELECT * FROM personnel_banque_versions WHERE demande_id=:i AND societe_id=:s AND employe_id=:e'),{'i':ident,'s':user['societe_id'],'e':eid}).mappings().first()
    if not r:raise HTTPException(404,'Version bancaire introuvable dans ce dossier.')
    try:
        donnees=trousseau().dechiffrer(r['cle_id'],r['contenu_chiffre'],'banque-rh',{'societe_id':user['societe_id'],'employe_id':eid,'demande_id':ident})
        if donnees['date_effet']!=r['date_effet'].isoformat() or donnees['piece_id']!=r['piece_id'] or masque_banque(donnees['rib_iban'])!=r['masque']:raise IntegriteCoffreError()
        return donnees
    except ConfigurationCoffreError:raise HTTPException(503,'Une clé historique bancaire est indisponible.') from None
    except (IntegriteCoffreError,KeyError,TypeError,ValueError):raise HTTPException(409,'Intégrité des coordonnées bancaires non vérifiée ;aucune valeur restituée.') from None

@workflow.transaction
def reveler_banque(db,user,eid,ident):
    lecture_autorisee(db,user);d=workflow.dossier(db,user['societe_id'],eid)
    donnees=contenu_banque(db,user,eid,ident)
    workflow.evenement(db,user,d,'BANQUE_CONSULTEE','Consultation privée des coordonnées proposées ou approuvées',ident)
    return donnees

def verifier_action_banque(db,user,r,data,*,approuver=False):
    lecture_autorisee(db,user)
    if approuver and not data.verification_bancaire_confirmee:raise HTTPException(400,'Confirmez le contrôle indépendant des coordonnées bancaires et de leur justificatif.')
    if approuver and not db.scalar(text("SELECT EXISTS(SELECT 1 FROM personnel_evenements WHERE societe_id=:s AND employe_id=:e AND demande_id=:i AND auteur_id=:u AND nature='BANQUE_CONSULTEE')"),{'s':user['societe_id'],'e':r['employe_id'],'i':r['id'],'u':user['id']}):
        raise HTTPException(409,'Consultez les coordonnées bancaires proposées avant leur approbation.')
    donnees=contenu_banque(db,user,r['employe_id'],r['id'])
    controler_notes(donnees['rib_iban'],data.motif,getattr(data,'reference_independance',None))

def banque_courante(db,d,ctx,au):
    if workflow.SENSIBLE not in ctx['capacites']:return {'banque':None,'banque_masquee':True}
    if '_banque_installee' not in ctx:ctx['_banque_installee']=banque_installee(db)
    if not ctx['_banque_installee']:return {'banque':None,'banque_masquee':False}
    r=db.execute(text('SELECT demande_id,version,date_effet,masque FROM personnel_banque_versions WHERE societe_id=:s AND employe_id=:e '
      'AND approuvee_at IS NOT NULL AND date_effet<=:d ORDER BY date_effet DESC LIMIT 1'),{'s':d['societe_id'],'e':d['employe_id'],'d':au}).mappings().first()
    return {'banque':dict(r) if r else None,'banque_masquee':False}
