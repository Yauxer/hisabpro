"""Variables approuvables ;aucun calcul social/fiscal ni mouvement comptable."""
from datetime import date
import json
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from services import paie_catalogue_service as catalogue,personnel_workflow_service as w

ACTIFS=('BROUILLON','SOUMIS','APPROUVE')

def autoriser(db,user,action=None):
    ctx=catalogue.autoriser(db,user,action)
    if not all(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'),{'t':'public.'+t}) for t in ['paie_variables','paie_variables_evenements']):raise HTTPException(503,'Installer la migration114 des variables de paie.')
    return ctx

def verrou(db,sid,eid,annee):
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:variables:{sid}:{eid}:{annee}'})

def applicable(db,sid,rid,effet):
    catalogue.rubrique(db,sid,rid)
    r=db.execute(text("SELECT v.*,r.code FROM paie_rubrique_versions v JOIN paie_rubriques r ON r.id=v.rubrique_id AND r.societe_id=v.societe_id "
      "WHERE v.rubrique_id=:i AND v.societe_id=:s AND v.statut='APPROUVEE' AND v.date_debut<=:d ORDER BY v.date_debut DESC LIMIT 1"),{'i':rid,'s':sid,'d':effet}).mappings().first()
    if not r or r['date_fin'] and r['date_fin']<effet:raise HTTPException(409,'Aucune version de rubrique approuvée applicable à cette date.')
    return r

def conditions(db,user,ctx,eid,rid,effet):
    d=w.dossier(db,user['societe_id'],eid,bloquer=True);p=w.projection(db,d,ctx,effet)
    if not p['dossier_complet_a_date'] or d['date_embauche'] and effet<d['date_embauche']:
        raise HTTPException(409,'Dossier actif,contrat et rémunération approuvés à la date d’effet requis ;aucun salaire historique supposé.')
    r=applicable(db,user['societe_id'],rid,effet)
    return d,p,r

def controles(db,user,data,r,*,ignorer=None):
    contenu=r['contenu']
    if data.mode!=contenu['formule']:raise HTTPException(400,'Le mode doit correspondre à la formule de la rubrique approuvée.')
    if set(data.justificatifs)!=set(contenu['justificatifs']):raise HTTPException(400,'Renseigner une référence pour chaque type de justificatif attendu,et uniquement ces types.')
    rows=db.execute(text("SELECT id,periode,rubrique_id,source_reference,instantane FROM paie_variables WHERE societe_id=:s AND employe_id=:e AND annee=:a AND statut IN ('BROUILLON','SOUMIS','APPROUVE')"),{'s':user['societe_id'],'e':data.employe_id,'a':data.periode.year}).mappings()
    for x in rows:
        if x['id']==ignorer:continue
        ancien=x['instantane']['rubrique'];meme_mois=x['periode']==data.periode
        if x['rubrique_id']==data.rubrique_id:
            if 'annuelle' in [ancien['periodicite'],contenu['periodicite']] or meme_mois and ('mensuelle' in [ancien['periodicite'],contenu['periodicite']] or x['source_reference']==data.source_reference):
                raise HTTPException(409,'Variable déjà présente pour cette source ou périodicité. Annuler/rejeter un brouillon erroné avant une nouvelle proposition.')
        if meme_mois and (x['instantane']['code'] in contenu['incompatibilites'] or r['code'] in ancien['incompatibilites']):
            raise HTTPException(409,'Rubriques incompatibles déjà présentes pour ce salarié et ce mois.')

def evenement(db,user,i,statut,motif):
    db.execute(text('INSERT INTO paie_variables_evenements(societe_id,variable_id,statut,auteur_id,motif) VALUES(:s,:i,:st,:u,:m)'),{'s':user['societe_id'],'i':i,'st':statut,'u':user['id'],'m':motif})

def exiger_rattachement_installe(db,data):
    if data.rattachement_revenus is not None and not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_trigger WHERE tgrelid='public.paie_variables'::regclass AND tgname='aaa_paie_reference123' AND tgenabled IN ('O','A') AND NOT tgisinternal)")):
        raise HTTPException(503,'Installer la migration123 des rattachements documentaires avant cette saisie.')


@w.transaction
def creer(db,user,data):
    ctx=autoriser(db,user,'proposer');exiger_rattachement_installe(db,data);sid=user['societe_id'];verrou(db,sid,data.employe_id,data.periode.year)
    d,p,r=conditions(db,user,ctx,data.employe_id,data.rubrique_id,data.date_effet);controles(db,user,data,r)
    snap={'code':r['code'],'rubrique':r['contenu'],'contrat_id':p['contrat']['id'],'remuneration':p['remuneration'],'matricule':p['matricule'],'nom':p['nom'],'arrondi':'Quantité × taux :ROUND_HALF_UP au centime,une fois à la ligne ;montant saisi sans arrondi implicite.'}
    declaration=data.model_dump(mode='json')
    if data.rattachement_revenus is None:declaration.pop('rattachement_revenus',None)
    params={'s':sid,'e':data.employe_id,'r':data.rubrique_id,'v':r['id'],'c':p['contrat']['id'],'rem':p['remuneration']['id'],'b':d['utilisateur_beneficiaire_id'],
      'p':data.periode,'a':data.periode.year,'d':data.date_effet,'per':r['contenu']['periodicite'],'mode':data.mode,'m':data.total(),'data':json.dumps(declaration,ensure_ascii=False),'snap':json.dumps(jsonable_encoder(snap),ensure_ascii=False),'ref':data.source_reference,'u':user['id']}
    ident=db.scalar(text('INSERT INTO paie_variables(societe_id,employe_id,rubrique_id,rubrique_version_id,contrat_version_id,remuneration_version_id,beneficiaire_snapshot,periode,annee,date_effet,periodicite,mode,montant,donnees,instantane,source_reference,prepare_par) '
      'VALUES(:s,:e,:r,:v,:c,:rem,:b,:p,:a,:d,:per,:mode,:m,CAST(:data AS jsonb),CAST(:snap AS jsonb),:ref,:u) RETURNING id'),params)
    evenement(db,user,ident,'BROUILLON',data.motif)
    return {'id':ident,'statut':'BROUILLON','montant':format(data.total(),'.2f'),'paie_definitive_autorisee':False}

def variable(db,sid,i,bloquer=False):
    r=db.execute(text('SELECT * FROM paie_variables WHERE id=:i AND societe_id=:s'+(' FOR UPDATE' if bloquer else '')),{'i':i,'s':sid}).mappings().first()
    if not r:raise HTTPException(404,'Variable introuvable dans cette société.')
    return r

def sortie(r,ctx,user):
    d=dict(r);d['montant']=format(d['montant'],'.2f');d['paie_definitive_autorisee']=False
    d['historique_masque']=not (w.AUDIT in ctx['capacites'] or 'personnel.approuver' in ctx['capacites'] or d['prepare_par']==user['id'])
    if d['historique_masque']:
        d['source_reference']=None;d['reference_controle']=None;d['donnees']=dict(d['donnees'],motif=None,source_reference=None,justificatifs=None)
        if d['donnees'].get('rattachement_revenus') is not None:d['donnees']['rattachement_revenus']=dict(d['donnees']['rattachement_revenus'],reference_justification=None,versement_reference=None)
    return d

def lire(db,user,i):
    ctx=autoriser(db,user);d=sortie(variable(db,user['societe_id'],i),ctx,user)
    d['evenements']=[] if d['historique_masque'] else [dict(x) for x in db.execute(text('SELECT id,statut,auteur_id,motif,cree_at FROM paie_variables_evenements WHERE variable_id=:i AND societe_id=:s ORDER BY id'),{'i':i,'s':user['societe_id']}).mappings()]
    return d

def lister(db,user,periode,statut,eid,decalage,limite):
    ctx=autoriser(db,user);clauses=['societe_id=:s'];params={'s':user['societe_id'],'o':decalage,'l':limite}
    for nom,val in [('periode',periode),('statut',statut),('employe_id',eid)]:
        if val is not None:clauses.append(nom+'=:'+nom);params[nom]=val
    filtre=' AND '.join(clauses)
    total=db.scalar(text('SELECT count(*) FROM paie_variables WHERE '+filtre),params)
    rows=db.execute(text('SELECT * FROM paie_variables WHERE '+filtre+' ORDER BY id DESC OFFSET :o LIMIT :l'),params).mappings()
    return {'total':total,'elements':[sortie(x,ctx,user) for x in rows],'decalage':decalage,'limite':limite}

@w.transaction
def transition(db,user,i,data,action):
    capacite={'soumettre':'soumettre','annuler':'proposer','approuver':'approuver','rejeter':'approuver'}[action]
    ctx=autoriser(db,user,capacite);sid=user['societe_id'];premiere=variable(db,sid,i)
    verrou(db,sid,premiere['employe_id'],premiere['annee']);v=variable(db,sid,i,True)
    attendu='BROUILLON' if action in {'soumettre','annuler'} else 'SOUMIS'
    if v['statut']!=attendu:raise HTTPException(409,'État de la variable modifié. Rechargez avant de réessayer.')
    if action in {'soumettre','annuler'} and v['prepare_par']!=user['id']:raise HTTPException(403,'Cette action est réservée au préparateur.')
    if action in {'soumettre','approuver'}:
        from services.paie_variables_schemas import Creation
        entree=Creation.model_validate(v['donnees']);exiger_rattachement_installe(db,entree);d,p,r=conditions(db,user,ctx,v['employe_id'],v['rubrique_id'],v['date_effet'])
        if (r['id'],p['contrat']['id'],p['remuneration']['id'])!=(v['rubrique_version_id'],v['contrat_version_id'],v['remuneration_version_id']):raise HTTPException(409,'Sources approuvées modifiées depuis la préparation ;annuler/rejeter puis proposer de nouveau.')
        controles(db,user,entree,r,ignorer=i)
    statut={'soumettre':'SOUMIS','annuler':'ANNULE','approuver':'APPROUVE','rejeter':'REJETE'}[action]
    if action=='approuver':
        from services.personnel_acces_service import validation_unique
        if (user['id']==v['prepare_par'] and not validation_unique(db,sid)) or user['id']==v['beneficiaire_snapshot'] or not data.independance_confirmee:raise HTTPException(403,'Un approbateur indépendant du préparateur et du bénéficiaire est requis.')
        if not data.justificatifs_verifies:raise HTTPException(400,'Confirmer la vérification des sources et justificatifs de cette variable.')
        if not db.scalar(text('SELECT hisabpro_personnel_membre(:s,:u,false)'),{'s':sid,'u':v['prepare_par']}):raise HTTPException(409,'Préparateur inactif ;rejeter la demande pour conserver sa traçabilité.')
    if action=='soumettre':db.execute(text("UPDATE paie_variables SET statut='SOUMIS',soumise_at=clock_timestamp() WHERE id=:i"),{'i':i})
    else:db.execute(text('UPDATE paie_variables SET statut=:st,decision_par=:u,decision_at=clock_timestamp(),reference_controle=:ref,justificatifs_verifies=:ok WHERE id=:i'),
      {'i':i,'st':statut,'u':user['id'],'ref':'ANNULATION_BROUILLON' if action=='annuler' else data.reference_controle,'ok':action=='approuver' and data.justificatifs_verifies})
    evenement(db,user,i,statut,data.motif)
    return {'id':i,'statut':statut,'paie_definitive_autorisee':False}

def options(db,user,au,recherche_salarie,recherche_rubrique):
    autoriser(db,user)
    personnes=w.lister(db,user,au,recherche_salarie,None,0,30)
    rubriques=catalogue.lister(db,user,au,recherche_rubrique,0,30)
    return {'salaries':[{'id':d['employe_id'],'nom':d['nom'],'matricule':d['matricule'],'complet':d['dossier_complet_a_date'],'remuneration':d['remuneration']} for d in personnes['elements']],
      'total_salaries':personnes['total'],'rubriques':[{'id':r['id'],'code':r['code'],'version_id':r['courante_id'],'contenu':r['contenu_applicable']} for r in rubriques['elements'] if r['courante_id']],
      'total_rubriques':rubriques['total'],'limite_options':30,'au':au}
