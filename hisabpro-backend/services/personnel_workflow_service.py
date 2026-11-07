"""Workflow Personnel transactionnel. Aucun appel au service comptable ou paie."""
from datetime import date
from functools import wraps
import json
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from services.personnel_acces_service import contexte
from services.personnel_dossiers_service import normaliser_matricule
from services.utilisateurs_acces_service import verrouiller_administration

IDENTITE='personnel.lire_identite'
REMUNERATION='personnel.lire_remuneration'
AUDIT='personnel.audit_lire'
SENSIBLE='personnel.lire_identifiants_sensibles'
CHAMPS_FISCAUX=('situation_familiale','nb_enfants','personnes_charge_ir')
CHAMPS_PERSONNELS=('date_embauche','email','telephone','numero_cnss',*CHAMPS_FISCAUX)
REGIMES=('regime_amo','regime_retraite','regime_mutuelle')


def exiger_donnees_identite(ctx,contenu):
    if 'numero_cnss' in contenu and SENSIBLE not in ctx['capacites']:
        raise HTTPException(403,'Habilitation identifiants sensibles requise pour le numéro CNSS.')
    if any(k in contenu for k in CHAMPS_FISCAUX) and REMUNERATION not in ctx['capacites']:
        raise HTTPException(403,'Habilitation rémunération requise pour les données fiscales personnelles.')


def exiger_regimes(ctx,contenu):
    if any(k in contenu for k in REGIMES) and SENSIBLE not in ctx['capacites']:
        raise HTTPException(403,'Habilitation identifiants sensibles requise pour les régimes sociaux déclarés.')


def donnees_saisies(data):
    valeurs=data.model_dump(mode='json')
    return {k:valeurs[k] for k in CHAMPS_PERSONNELS if k in data.model_fields_set}


def sql(db,commande,params=None):
    return db.execute(text(commande),params or {})


def verifier_schema(db):
    if db.bind.dialect.name!='postgresql':
        raise HTTPException(503,'Le workflow Personnel nécessite PostgreSQL et la migration107.')
    tables=['personnel_dossiers','personnel_demandes','personnel_contrats_versions',
            'personnel_remunerations_versions','personnel_evenements','personnel_demandes_details']
    if not all(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'),{'t':'public.'+t}) for t in tables):
        raise HTTPException(503,'Installer les migrations105 à107 avant le workflow Personnel.')
    if not db.scalar(text("SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name='employes' AND column_name='salaire_brut' AND is_nullable='YES')")) or not db.scalar(text(
        "SELECT EXISTS(SELECT 1 FROM pg_constraint WHERE conrelid='public.personnel_habilitations'::regclass AND conname='ck_personnel_capacites107')")):
        raise HTTPException(503,'Installation du workflow Personnel incomplète.')


def autoriser(db,user,action=None):
    if action:
        verrouiller_administration(db,user['societe_id'])
    ctx=contexte(db,user)
    verifier_schema(db)
    if ctx['mode']!='protege':
        raise HTTPException(409,'Activer explicitement la protection Personnel avant ce workflow.')
    requis={IDENTITE} | ({'personnel.'+action} if action else set())
    if not ctx['module_actif'] or not requis<=set(ctx['capacites']):
        raise HTTPException(403,'Habilitation Personnel requise.')
    if action:
        role=db.scalar(text("SELECT CASE WHEN u.societe_id=:s THEN u.role ELSE a.role END "
            "FROM utilisateurs u LEFT JOIN utilisateurs_societes a ON a.utilisateur_id=u.id AND a.societe_id=:s AND a.actif "
            "WHERE u.id=:u AND u.actif AND (u.societe_id=:s OR a.id IS NOT NULL)"),{'s':user['societe_id'],'u':user['id']})
        if role not in {'admin','comptable','personnel'}:
            raise HTTPException(403,'Un profil autorisé à modifier le Personnel est requis.')
    return ctx


def transaction(fn):
    @wraps(fn)
    def executer(db,*args,**kwargs):
        try:
            valeur=fn(db,*args,**kwargs)
            db.commit()
            return valeur
        except DBAPIError as exc:
            db.rollback()
            if getattr(exc.orig,'pgcode',None) in {'23505','23514','23503','40001','40P01'}:
                raise HTTPException(409,'Dossier ou demande en conflit. Rechargez avant de réessayer.') from exc
            raise
        except Exception:
            db.rollback()
            raise
    return executer


def dossier(db,sid,eid,*,bloquer=False):
    row=sql(db,'SELECT d.*,e.nom,e.poste,e.date_embauche,e.email,e.telephone,e.numero_cnss,e.situation_familiale,e.nb_enfants,e.personnes_charge_ir FROM personnel_dossiers d JOIN employes e '
        'ON e.id=d.employe_id AND e.societe_id=d.societe_id WHERE d.societe_id=:s AND d.employe_id=:e'
        +(' FOR UPDATE OF d' if bloquer else ''),{'s':sid,'e':eid}).mappings().first()
    if row is None:raise HTTPException(404,'Dossier introuvable dans cette société.')
    return row


def revision(d,attendue):
    if d['revision']!=attendue:raise HTTPException(409,'Révision périmée. Rechargez le dossier.')


def evenement(db,user,d,nature,motif,demande_id=None,revision_apres=None):
    sql(db,'INSERT INTO personnel_evenements(societe_id,employe_id,demande_id,revision,nature,auteur_id,motif,cree_at) '
        'VALUES(:s,:e,:i,:r,:n,:u,:m,clock_timestamp())',{'s':user['societe_id'],'e':d['employe_id'],'i':demande_id,
        'r':d['revision'] if revision_apres is None else revision_apres,'n':nature,'u':user['id'],'m':motif})


def verifier_beneficiaire(db,sid,data):
    uid=data.utilisateur_beneficiaire_id
    if uid is not None and not db.scalar(text('SELECT hisabpro_personnel_membre(:s,:u,false)'),{'s':sid,'u':uid}):
        raise HTTPException(404,'Utilisateur bénéficiaire actif introuvable dans cette société.')


def ajouter_demande(db,user,d,nature,contenu,motif):
    if not d['reference_beneficiaire'] or not (d['utilisateur_beneficiaire_id'] is not None or d['beneficiaire_sans_compte_confirme']):
        raise HTTPException(409,'Lien bénéficiaire à attester avant de proposer une opération.')
    i=sql(db,'INSERT INTO personnel_demandes(societe_id,employe_id,nature,revision_attendue,prepare_par,beneficiaire_snapshot,motif) '
        'VALUES(:s,:e,:n,:r,:u,:b,:m) RETURNING id',{'s':user['societe_id'],'e':d['employe_id'],'n':nature,
        'r':d['revision'],'u':user['id'],'b':d['utilisateur_beneficiaire_id'],'m':motif}).scalar_one()
    sql(db,'INSERT INTO personnel_demandes_details(demande_id,societe_id,employe_id,contenu) VALUES(:i,:s,:e,CAST(:c AS jsonb))',
        {'i':i,'s':user['societe_id'],'e':d['employe_id'],'c':json.dumps(contenu,ensure_ascii=False)})
    p={'s':user['societe_id'],'e':d['employe_id'],'i':i,**contenu}
    if nature=='CONTRAT':
        extra=any(k in contenu for k in REGIMES)
        if extra:
            n=db.scalar(text("SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='personnel_contrats_versions' AND column_name IN ('regime_amo','regime_retraite','regime_mutuelle')"))
            if n!=3:raise HTTPException(503,'Installer la migration110 avant de renseigner les régimes sociaux du contrat.')
            for k in REGIMES:p.setdefault(k,None)
        colonnes=','+','.join(REGIMES) if extra else ''
        valeurs=','+','.join(':'+k for k in REGIMES) if extra else ''
        sql(db,'INSERT INTO personnel_contrats_versions(societe_id,employe_id,demande_id,version,date_effet,type_contrat,date_debut,date_fin,reference_justificatif'+colonnes+') '
            'SELECT :s,:e,:i,coalesce(max(version),0)+1,CAST(:date_effet AS date),:type_contrat,CAST(:date_debut AS date),CAST(:date_fin AS date),:reference_justificatif'+valeurs+' '
            'FROM personnel_contrats_versions WHERE societe_id=:s AND employe_id=:e',p)
    elif nature=='REMUNERATION':
        sql(db,'INSERT INTO personnel_remunerations_versions(societe_id,employe_id,demande_id,contrat_version_id,version,date_effet,montant,periodicite,devise,reference_justificatif) '
            'SELECT :s,:e,:i,:contrat_version_id,coalesce(max(version),0)+1,CAST(:date_effet AS date),:montant,:periodicite,:devise,:reference_justificatif '
            'FROM personnel_remunerations_versions WHERE societe_id=:s AND employe_id=:e',p)
    evenement(db,user,d,'DEMANDE_CREEE',motif,i)
    return {'id':i,'employe_id':d['employe_id'],'nature':nature,'statut':'BROUILLON','revision_attendue':d['revision']}


@transaction
def creer(db,user,data,*,reprise=False):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id']
    supplement={} if reprise else donnees_saisies(data)
    exiger_donnees_identite(ctx,supplement)
    verifier_beneficiaire(db,sid,data)
    if reprise:
        e=sql(db,'SELECT id,nom,poste,matricule FROM employes WHERE id=:e AND societe_id=:s FOR UPDATE',
              {'e':data.employe_id,'s':sid}).mappings().first()
        if e is None:raise HTTPException(404,'Employé historique introuvable dans cette société.')
        eid=e['id'];cle=normaliser_matricule(e['matricule']);nom=e['nom'];poste=e['poste']
        if cle is None:raise HTTPException(409,'Matricule historique manquant :consulter le diagnostic sans réparation automatique.')
    else:
        cle=data.matricule;nom=data.nom;poste=data.poste
        # Même verrou que106, avant toute création :aucun doublon historique caché.
        sql(db,'SELECT pg_advisory_xact_lock(hashtextextended(:k,0))',{'k':f'hisabpro:personnel:matricule:{sid}:{cle}'})
        if db.scalar(text('SELECT EXISTS(SELECT 1 FROM employes WHERE societe_id=:s AND hisabpro_personnel_matricule(matricule)=:m)'),{'s':sid,'m':cle}):
            raise HTTPException(409,'Ce matricule existe déjà dans cette société.')
        eid=sql(db,'INSERT INTO employes(societe_id,nom,poste,matricule,salaire_brut,actif) VALUES(:s,:n,:p,:m,NULL,false) RETURNING id',
                {'s':sid,'n':nom,'p':poste,'m':cle}).scalar_one()
    sql(db,'INSERT INTO personnel_dossiers(employe_id,societe_id,matricule_cle,origine,cree_par,utilisateur_beneficiaire_id,beneficiaire_sans_compte_confirme,reference_beneficiaire) '
        'VALUES(:e,:s,:m,:o,:u,:b,:a,:ref)',{'e':eid,'s':sid,'m':cle,'o':'historique_a_confirmer' if reprise else 'nouveau',
        'u':user['id'],'b':data.utilisateur_beneficiaire_id,'a':data.beneficiaire_sans_compte_confirme,'ref':data.reference_beneficiaire})
    d=dossier(db,sid,eid)
    evenement(db,user,d,'DOSSIER_REPRIS' if reprise else 'DOSSIER_CREE',
        'Reprise explicite de la fiche historique' if reprise else 'Création du dossier')
    return {'employe_id':eid,'statut':'BROUILLON','revision':0,
            'demande':ajouter_demande(db,user,d,'DOSSIER',{'nom':nom,'poste':poste,**supplement},data.motif)}


def verifier_contenu(db,d,nature,c,*,approuver=False):
    sid=d['societe_id'];eid=d['employe_id']
    if d['statut']=='SORTI' or d['date_sortie_approuvee'] is not None and nature=='DOSSIER':
        raise HTTPException(409,'Dossier sorti ou sortie déjà approuvée.')
    if nature!='DOSSIER' and d['statut'] not in {'ACTIF','SUSPENDU'}:
        raise HTTPException(409,'Faire approuver le dossier avant ses conditions contractuelles.')
    effet=date.fromisoformat(c['date_effet']) if nature in {'CONTRAT','REMUNERATION','BANQUE'} else None
    if effet and d['date_sortie_approuvee'] and effet>d['date_sortie_approuvee']:
        raise HTTPException(409,'Date d’effet postérieure à la sortie approuvée.')
    if nature=='BANQUE':
        if db.scalar(text('SELECT EXISTS(SELECT 1 FROM personnel_banque_versions WHERE societe_id=:s AND employe_id=:e AND date_effet=:d AND approuvee_at IS NOT NULL)'),{'s':sid,'e':eid,'d':effet}):
            raise HTTPException(409,'Une version bancaire est déjà approuvée à cette date ;examiner une rectification contrôlée.')
    if nature=='CONTRAT' and db.scalar(text('SELECT EXISTS(SELECT 1 FROM personnel_remunerations_versions '
        'WHERE societe_id=:s AND employe_id=:e AND approuvee_at IS NOT NULL AND date_effet>=:d)'),{'s':sid,'e':eid,'d':effet}):
        raise HTTPException(409,'Des rémunérations approuvées seraient détachées de leur contrat. Examiner leur régularisation avant cette nouvelle version de contrat.')
    if nature=='REMUNERATION':
        contrat=sql(db,'SELECT * FROM personnel_contrats_versions WHERE id=:i AND societe_id=:s AND employe_id=:e',
                    {'i':c['contrat_version_id'],'s':sid,'e':eid}).mappings().first()
        if contrat is None:raise HTTPException(404,'Contrat introuvable dans ce dossier.')
        courant=db.scalar(text('SELECT id FROM personnel_contrats_periodes WHERE societe_id=:s AND employe_id=:e AND date_effet<=:d '
            'AND (date_fin_effet_exclue IS NULL OR :d<date_fin_effet_exclue) AND date_debut<=:d AND (date_fin IS NULL OR :d<=date_fin)'),{'s':sid,'e':eid,'d':effet})
        if contrat['approuvee_at'] is None or courant!=contrat['id']:
            raise HTTPException(409,'Contrat approuvé applicable à cette date requis.')
    if nature=='SORTIE':
        if d['date_sortie_approuvee'] is not None:raise HTTPException(409,'Une sortie est déjà approuvée.')
        sortie=date.fromisoformat(c['date_sortie'])
        debut=db.scalar(text('SELECT min(date_debut) FROM personnel_contrats_versions WHERE societe_id=:s AND employe_id=:e AND approuvee_at IS NOT NULL'),{'s':sid,'e':eid})
        if debut and sortie<debut:raise HTTPException(409,'La sortie précède le début du contrat approuvé.')
        # Une sortie antérieure à une condition future déjà approuvée nécessite
        # une décision corrective distincte ;aucun effacement de version.
        if db.scalar(text('SELECT EXISTS(SELECT 1 FROM personnel_contrats_versions WHERE societe_id=:s AND employe_id=:e AND approuvee_at IS NOT NULL AND date_effet>:d) OR '
            'EXISTS(SELECT 1 FROM personnel_remunerations_versions WHERE societe_id=:s AND employe_id=:e AND approuvee_at IS NOT NULL AND date_effet>:d)'),{'s':sid,'e':eid,'d':sortie}):
            raise HTTPException(409,'Des conditions futures approuvées dépassent cette sortie :régularisation à examiner.')


@transaction
def proposer(db,user,eid,data):
    ctx=autoriser(db,user,'proposer');d=dossier(db,user['societe_id'],eid,bloquer=True);revision(d,data.revision_attendue)
    if data.nature=='REMUNERATION' and REMUNERATION not in ctx['capacites']:raise HTTPException(403,'Lecture rémunération requise pour la proposer.')
    if data.nature=='BANQUE':
        from services.personnel_coffre_service import proposer_banque
        return proposer_banque(db,user,d,data)
    c=data.contenu.model_dump(mode='json')
    if data.nature=='CONTRAT':
        for k in REGIMES:
            if k not in data.contenu.model_fields_set:c.pop(k,None)
        # La vue106 ne connaît pas les colonnes ajoutées :retrouver la racine par son ID.
        ancien=sql(db,"SELECT "+','.join("to_jsonb(v)->>'"+k+"' AS "+k for k in REGIMES)+
            ' FROM personnel_contrats_versions v WHERE id=(SELECT id FROM personnel_contrats_periodes '
            'WHERE societe_id=:s AND employe_id=:e AND date_effet<=:d AND date_debut<=:d AND (date_fin IS NULL OR :d<=date_fin) '
            'AND (date_fin_effet_exclue IS NULL OR :d<date_fin_effet_exclue) LIMIT 1)',
            {'s':user['societe_id'],'e':eid,'d':c['date_effet']}).mappings().first()
        if ancien:
            for k in REGIMES:
                if k not in c and ancien[k] is not None:c[k]=ancien[k]
        exiger_regimes(ctx,c)
    if data.nature=='DOSSIER':
        c={'nom':c['nom'],'poste':c['poste'],**donnees_saisies(data.contenu)}
        exiger_donnees_identite(ctx,c)
    verifier_contenu(db,d,data.nature,c)
    return ajouter_demande(db,user,d,data.nature,c,data.motif)


def demande(db,sid,i):
    row=sql(db,'SELECT d.*,p.contenu,pre.nom AS prepare_par_nom,dec.nom AS decision_par_nom FROM personnel_demandes d JOIN personnel_demandes_details p ON p.demande_id=d.id '
        'AND p.societe_id=d.societe_id AND p.employe_id=d.employe_id LEFT JOIN utilisateurs pre ON pre.id=d.prepare_par '
        'LEFT JOIN utilisateurs dec ON dec.id=d.decision_par WHERE d.societe_id=:s AND d.id=:i',{'s':sid,'i':i}).mappings().first()
    if row is None:raise HTTPException(404,'Demande introuvable dans cette société.')
    return row


@transaction
def soumettre(db,user,i,data):
    ctx=autoriser(db,user,'soumettre');r=demande(db,user['societe_id'],i)
    d=dossier(db,user['societe_id'],r['employe_id'],bloquer=True)
    r=demande(db,user['societe_id'],i);revision(d,data.revision_attendue)
    if r['prepare_par']!=user['id']:raise HTTPException(403,'Seul le préparateur peut soumettre sa demande.')
    if r['statut']!='BROUILLON' or r['revision_attendue']!=d['revision']:raise HTTPException(409,'Demande déjà soumise ou périmée.')
    if r['nature']=='REMUNERATION' and REMUNERATION not in ctx['capacites']:raise HTTPException(403,'Lecture rémunération requise.')
    if r['nature']=='DOSSIER':exiger_donnees_identite(ctx,r['contenu'])
    if r['nature']=='CONTRAT':exiger_regimes(ctx,r['contenu'])
    if r['nature']=='BANQUE':
        from services.personnel_coffre_service import verifier_action_banque
        verifier_action_banque(db,user,r,data)
    verifier_contenu(db,d,r['nature'],r['contenu'])
    sql(db,"UPDATE personnel_demandes SET statut='SOUMIS',soumis_at=clock_timestamp() WHERE id=:i",{'i':i})
    if r['nature']=='DOSSIER' and d['statut']=='BROUILLON':sql(db,"UPDATE personnel_dossiers SET statut='A_VALIDER' WHERE employe_id=:e AND societe_id=:s",{'e':d['employe_id'],'s':user['societe_id']})
    evenement(db,user,d,'DEMANDE_SOUMISE',data.motif,i)
    return {'id':i,'statut':'SOUMIS','revision':d['revision']}


@transaction
def decider(db,user,i,data,*,approuver=True):
    ctx=autoriser(db,user,'approuver');r=demande(db,user['societe_id'],i)
    d=dossier(db,user['societe_id'],r['employe_id'],bloquer=True);r=demande(db,user['societe_id'],i)
    revision(d,data.revision_attendue)
    if r['statut']!='SOUMIS':raise HTTPException(409,'Cette demande n’attend plus de décision.')
    from services.personnel_acces_service import validation_unique
    if (user['id']==r['prepare_par'] and not validation_unique(db,user['societe_id'])) or user['id'] in {r['beneficiaire_snapshot'],d['utilisateur_beneficiaire_id']}:
        raise HTTPException(403,'Préparateur et bénéficiaire ne peuvent pas approuver ou rejeter leur propre demande.')
    if r['nature']=='REMUNERATION' and REMUNERATION not in ctx['capacites']:raise HTTPException(403,'Lecture rémunération requise pour la décision.')
    if r['nature']=='DOSSIER':exiger_donnees_identite(ctx,r['contenu'])
    if r['nature']=='CONTRAT':exiger_regimes(ctx,r['contenu'])
    if r['nature']=='BANQUE':
        from services.personnel_coffre_service import verifier_action_banque
        verifier_action_banque(db,user,r,data,approuver=approuver)
    if approuver:
        if r['revision_attendue']!=d['revision']:raise HTTPException(409,'Demande périmée :préparer une nouvelle proposition.')
        verifier_contenu(db,d,r['nature'],r['contenu'],approuver=True)
    etat='APPROUVE' if approuver else 'REJETE'
    decision=sql(db,'UPDATE personnel_demandes SET statut=:st,decision_par=:u,decision_at=clock_timestamp(),motif_decision=:m,'
        'independance_confirmee=true,reference_independance=:ref WHERE id=:i RETURNING decision_at',
        {'st':etat,'u':user['id'],'m':data.motif,'ref':data.reference_independance,'i':i}).scalar_one()
    statut=d['statut'];sortie=d['date_sortie_approuvee']
    if approuver:
        if r['nature']=='DOSSIER':
            sql(db,'UPDATE employes SET nom=:n,poste=:p WHERE id=:e AND societe_id=:s',
                {'n':r['contenu']['nom'],'p':r['contenu']['poste'],'e':d['employe_id'],'s':user['societe_id']})
            for champ in CHAMPS_PERSONNELS:
                if champ in r['contenu']:
                    sql(db,f'UPDATE employes SET {champ}=:v WHERE id=:e AND societe_id=:s',
                        {'v':r['contenu'][champ],'e':d['employe_id'],'s':user['societe_id']})
            statut='ACTIF'
        elif r['nature'] in {'CONTRAT','REMUNERATION'}:
            table='personnel_contrats_versions' if r['nature']=='CONTRAT' else 'personnel_remunerations_versions'
            sql(db,f'UPDATE {table} SET approuvee_par=:u,approuvee_at=:t WHERE demande_id=:i AND societe_id=:s',
                {'u':user['id'],'t':decision,'i':i,'s':user['societe_id']})
        elif r['nature']=='BANQUE':
            sql(db,'UPDATE personnel_banque_versions SET verification_confirmee=true,approuvee_par=:u,approuvee_at=:t WHERE demande_id=:i AND societe_id=:s',
                {'u':user['id'],'t':decision,'i':i,'s':user['societe_id']})
        else:
            sortie=date.fromisoformat(r['contenu']['date_sortie'])
            if sortie<=date.today():statut='SORTI'
    elif r['nature']=='DOSSIER' and d['statut']=='A_VALIDER':statut='BROUILLON'
    rev=d['revision']+1
    sql(db,'UPDATE personnel_dossiers SET statut=:st,revision=:r,date_sortie_approuvee=:d WHERE employe_id=:e AND societe_id=:s',
        {'st':statut,'r':rev,'d':sortie,'e':d['employe_id'],'s':user['societe_id']})
    evenement(db,user,d,'DEMANDE_APPROUVEE' if approuver else 'DEMANDE_REJETEE',data.motif,i,rev)
    return {'id':i,'statut':etat,'employe_id':d['employe_id'],'revision':rev}


def projection(db,d,ctx,au):
    p={'s':d['societe_id'],'e':d['employe_id'],'d':au}
    c=sql(db,"SELECT c.id,c.version,c.type_contrat,c.date_effet,c.date_debut,c.date_fin,"+
        ','.join("to_jsonb(v)->>'"+k+"' AS "+k for k in REGIMES)+
        ' FROM personnel_contrats_periodes c JOIN personnel_contrats_versions v ON v.id=c.id AND v.societe_id=c.societe_id '
        'WHERE c.societe_id=:s AND c.employe_id=:e AND c.date_effet<=:d AND (c.date_fin_effet_exclue IS NULL OR :d<c.date_fin_effet_exclue) '
        'AND c.date_debut<=:d AND (c.date_fin IS NULL OR :d<=c.date_fin)',p).mappings().first()
    if c:
        c=dict(c);c['regimes']={k:c.pop(k) for k in REGIMES}
        c['regimes_masques']=SENSIBLE not in ctx['capacites']
        if c['regimes_masques']:c['regimes']=None
    r=None
    if c:
        r=sql(db,'SELECT id,version,montant,devise,periodicite,date_effet FROM personnel_remunerations_periodes '
            'WHERE societe_id=:s AND employe_id=:e AND contrat_version_id=:c AND date_effet<=:d AND (date_fin_effet_exclue IS NULL OR :d<date_fin_effet_exclue)',dict(p,c=c['id'])).mappings().first()
    sorti=d['date_sortie_approuvee'] is not None and d['date_sortie_approuvee']<=au
    statut='SORTI' if sorti else ('ACTIF' if d['statut']=='SORTI' and d['date_sortie_approuvee'] and au<d['date_sortie_approuvee'] else d['statut'])
    salaire=None
    if r and REMUNERATION in ctx['capacites']:
        salaire=dict(r);salaire['montant']=format(salaire['montant'],'.2f')
    from services.personnel_coffre_service import banque_courante
    return {**banque_courante(db,d,ctx,au),'employe_id':d['employe_id'],'societe_id':d['societe_id'],'matricule':d['matricule_cle'],'nom':d['nom'],'poste':d['poste'],
        'date_embauche':d['date_embauche'],'email':d['email'],'telephone':d['telephone'],'numero_cnss':d['numero_cnss'] if SENSIBLE in ctx['capacites'] else None,
        'cnss_masque':SENSIBLE not in ctx['capacites'],
        'donnees_fiscales':{k:d[k] for k in CHAMPS_FISCAUX} if REMUNERATION in ctx['capacites'] else None,
        'origine':d['origine'],'statut':statut,'revision':d['revision'],'au':au,'date_sortie_approuvee':d['date_sortie_approuvee'],
        'contrat':dict(c) if c else None,'remuneration':salaire,'remuneration_masquee':REMUNERATION not in ctx['capacites'],
        'dossier_complet_a_date':statut=='ACTIF' and c is not None and r is not None,
        'paie_definitive_autorisee':False}


def lire(db,user,eid,au):
    ctx=autoriser(db,user)
    return projection(db,dossier(db,user['societe_id'],eid),ctx,au)


def options_saisie(db,user):
    ctx=autoriser(db,user)
    if 'personnel.proposer' not in ctx['capacites'] or user['role'] not in {'admin','comptable','personnel'}:
        raise HTTPException(403,'Habilitation de proposition Personnel requise.')
    p={'s':user['societe_id']}
    comptes=sql(db,'SELECT u.id,u.nom,u.email FROM utilisateurs u WHERE hisabpro_personnel_membre(:s,u.id,false) ORDER BY u.nom,u.id',p).mappings().all()
    historiques=sql(db,"SELECT e.id,e.nom,e.matricule,CASE WHEN hisabpro_personnel_matricule(e.matricule) IS NULL THEN 'Matricule manquant' "
        "WHEN EXISTS(SELECT 1 FROM employes x WHERE x.societe_id=e.societe_id AND x.id<>e.id AND hisabpro_personnel_matricule(x.matricule)=hisabpro_personnel_matricule(e.matricule)) "
        "THEN 'Matricule ambigu' ELSE NULL END AS blocage FROM employes e LEFT JOIN personnel_dossiers d ON d.employe_id=e.id AND d.societe_id=e.societe_id "
        "WHERE e.societe_id=:s AND d.employe_id IS NULL ORDER BY e.created_at DESC,e.id DESC",p).mappings().all()
    return {'beneficiaires':[dict(c) for c in comptes],'historiques':[dict(e) for e in historiques]}


def lister(db,user,au,recherche,statut,decalage,limite):
    ctx=autoriser(db,user)
    condition="d.societe_id=:s AND (:q='' OR e.nom ILIKE :like OR d.matricule_cle ILIKE :like)"
    p={'s':user['societe_id'],'q':recherche or '','like':'%'+(recherche or '')+'%','decalage':decalage,'limite':limite,'au':au,'st':statut}
    if statut:
        condition+=" AND (CASE WHEN d.date_sortie_approuvee<=:au THEN 'SORTI' WHEN d.statut='SORTI' AND :au<d.date_sortie_approuvee THEN 'ACTIF' ELSE d.statut END)=:st"
    total=db.scalar(text('SELECT count(*) FROM personnel_dossiers d JOIN employes e ON e.id=d.employe_id AND e.societe_id=d.societe_id WHERE '+condition),p)
    rows=sql(db,'SELECT d.*,e.nom,e.poste,e.date_embauche,e.email,e.telephone,e.numero_cnss,e.situation_familiale,e.nb_enfants,e.personnes_charge_ir FROM personnel_dossiers d JOIN employes e ON e.id=d.employe_id AND e.societe_id=d.societe_id '
        'WHERE '+condition+' ORDER BY d.cree_at DESC,d.employe_id DESC OFFSET :decalage LIMIT :limite',p).mappings().all()
    return {'total':total,'decalage':decalage,'limite':limite,'elements':[projection(db,d,ctx,au) for d in rows]}


def projection_demande(row,ctx,user):
    r=dict(row)
    financier=r['nature']=='REMUNERATION'
    r['champs_masques']=[]
    if r['nature']=='DOSSIER' and r['contenu']:
        c=dict(r['contenu'])
        masques=([k for k in CHAMPS_FISCAUX if k in c] if REMUNERATION not in ctx['capacites'] else [])
        if SENSIBLE not in ctx['capacites'] and 'numero_cnss' in c:masques.append('numero_cnss')
        for k in masques:c[k]=None
        r['contenu']=c;r['champs_masques']=masques
        if masques:
            for k in ['motif','motif_decision','reference_independance']:r[k]=None
    if r['nature']=='CONTRAT' and SENSIBLE not in ctx['capacites']:
        c=dict(r['contenu'] or {})
        r['champs_masques']=[k for k in REGIMES if k in c]
        for k in r['champs_masques']:c[k]=None
        r['contenu']=c
        if r['champs_masques']:
            for k in ['motif','motif_decision','reference_independance']:r[k]=None
            c['reference_justificatif']=None
    if r['nature']=='BANQUE' and SENSIBLE not in ctx['capacites']:
        for k in ['contenu','motif','motif_decision','reference_independance']:r[k]=None
        r['champs_masques']=['coordonnees_bancaires']
    if financier and REMUNERATION not in ctx['capacites']:
        for champ in ['contenu','motif','motif_decision','reference_independance']:r[champ]=None
    if not (AUDIT in ctx['capacites'] or 'personnel.approuver' in ctx['capacites'] or r['prepare_par']==user['id']):
        for champ in ['motif','motif_decision','reference_independance']:r[champ]=None
    r['contenu_masque']=(financier and REMUNERATION not in ctx['capacites']) or (r['nature']=='BANQUE' and SENSIBLE not in ctx['capacites'])
    return r


def lire_demande(db,user,i):
    ctx=autoriser(db,user)
    return projection_demande(demande(db,user['societe_id'],i),ctx,user)


def lister_demandes(db,user,statut,eid,decalage,limite):
    ctx=autoriser(db,user)
    condition='d.societe_id=:s'
    p={'s':user['societe_id'],'decalage':decalage,'limite':limite}
    if statut:condition+=' AND d.statut=:st';p['st']=statut
    if eid is not None:
        dossier(db,user['societe_id'],eid);condition+=' AND d.employe_id=:e';p['e']=eid
    jointure=' FROM personnel_demandes d JOIN personnel_demandes_details p ON p.demande_id=d.id AND p.societe_id=d.societe_id AND p.employe_id=d.employe_id LEFT JOIN utilisateurs pre ON pre.id=d.prepare_par LEFT JOIN utilisateurs dec ON dec.id=d.decision_par WHERE '+condition
    total=db.scalar(text('SELECT count(*)'+jointure),p)
    rows=sql(db,'SELECT d.*,p.contenu,pre.nom AS prepare_par_nom,dec.nom AS decision_par_nom'+jointure+' ORDER BY d.id DESC OFFSET :decalage LIMIT :limite',p).mappings().all()
    return {'total':total,'decalage':decalage,'limite':limite,
            'elements':[projection_demande(r,ctx,user) for r in rows]}


def historique(db,user,eid,decalage,limite):
    ctx=autoriser(db,user)
    if AUDIT not in ctx['capacites']:raise HTTPException(403,'Habilitation audit Personnel requise.')
    dossier(db,user['societe_id'],eid)
    p={'s':user['societe_id'],'e':eid,'decalage':decalage,'limite':limite}
    rows=sql(db,"SELECT e.*,d.nature AS nature_demande,u.nom AS auteur_nom,"
        "coalesce(p.contenu ?| ARRAY['situation_familiale','nb_enfants','personnes_charge_ir'],false) AS identite_financiere,"
        "coalesce(p.contenu ?| ARRAY['numero_cnss','regime_amo','regime_retraite','regime_mutuelle'],false) AS identite_sensible "
        'FROM personnel_evenements e LEFT JOIN personnel_demandes d ON d.id=e.demande_id AND d.societe_id=e.societe_id LEFT JOIN utilisateurs u ON u.id=e.auteur_id '
        'LEFT JOIN personnel_demandes_details p ON p.demande_id=d.id AND p.societe_id=d.societe_id '
        'WHERE e.societe_id=:s AND e.employe_id=:e ORDER BY e.id DESC OFFSET :decalage LIMIT :limite',p).mappings().all()
    total=db.scalar(text('SELECT count(*) FROM personnel_evenements WHERE societe_id=:s AND employe_id=:e'),p)
    elements=[]
    for row in rows:
        r=dict(row)
        if r['nature_demande']=='BANQUE' and SENSIBLE not in ctx['capacites']:r['motif']=None
        if (r['nature_demande']=='REMUNERATION' or r['identite_financiere']) and REMUNERATION not in ctx['capacites'] or r['identite_sensible'] and SENSIBLE not in ctx['capacites']:r['motif']=None
        elements.append(r)
    return {'total':total,'elements':elements,'decalage':decalage,'limite':limite}
