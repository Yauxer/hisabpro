"""Snapshots pédagogiques du brut ;inconnues et cas complexes restent bloquants."""
from calendar import monthrange
from decimal import Decimal
import json,hashlib
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from services import personnel_workflow_service as w,paie_variables_service as variables

def canonique(d):return json.dumps(jsonable_encoder(d,custom_encoder={Decimal:lambda x:format(x,'f')}),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def empreinte(d):return hashlib.sha256(canonique(d).encode('utf8')).hexdigest()

def autoriser(db,user,action=None):
    ctx=variables.autoriser(db,user,action)
    if not all(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'),{'t':'public.'+t}) for t in ['paie_campagnes','paie_simulations_brut']):raise HTTPException(503,'Installer la migration115 des campagnes et simulations du brut.')
    return ctx

def simulation_salarie(db,user,ctx,eid,debut,fin):
    variables.verrou(db,user['societe_id'],eid,debut.year)
    d=w.dossier(db,user['societe_id'],eid,bloquer=True);a=w.projection(db,d,ctx,debut);b=w.projection(db,d,ctx,fin)
    erreurs=[]
    def signaler(code,message):erreurs.append({'code':code,'message':message})
    if not a['dossier_complet_a_date'] or not b['dossier_complet_a_date']:signaler('DOSSIER_INCOMPLET','Dossier actif,contrat et rémunération approuvés sur le mois requis.')
    if d['date_embauche'] is None:signaler('ENTREE_INCONNUE','Date d’entrée connue requise ;ne pas la déduire du contrat.')
    elif d['date_embauche']>debut:signaler('MOIS_INCOMPLET','Entrée dans le mois :prorata à traiter dans une étape ultérieure.')
    if d['date_sortie_approuvee'] is not None and d['date_sortie_approuvee']<=fin:signaler('SORTIE','Sortie concernant ce mois :traitement spécifique requis.')
    if a['contrat'] and b['contrat'] and a['contrat']['id']!=b['contrat']['id']:signaler('CONTRAT_CHANGE','Contrat modifié dans le mois ;aucun découpage supposé.')
    if a['contrat'] and (a['contrat']['date_debut']>debut or a['contrat']['date_fin'] and a['contrat']['date_fin']<fin):signaler('CONTRAT_PARTIEL','Le contrat ne couvre pas le mois complet.')
    if a['remuneration'] and b['remuneration'] and a['remuneration']['id']!=b['remuneration']['id']:signaler('SALAIRE_CHANGE','Rémunération modifiée dans le mois ;aucun prorata supposé.')
    if a['remuneration'] and a['remuneration']['periodicite']!='mensuelle':signaler('BASE_NON_MENSUELLE','Base horaire/journalière :quantité et prorata à traiter séparément.')
    params={'s':user['societe_id'],'e':eid,'p':debut}
    if db.scalar(text("SELECT EXISTS(SELECT 1 FROM paie_variables WHERE societe_id=:s AND employe_id=:e AND periode=:p AND statut IN ('BROUILLON','SOUMIS'))"),params):
        signaler('VARIABLES_EN_ATTENTE','Des variables de ce mois restent à soumettre ou décider ;ne pas les ignorer.')
    rows=db.execute(text("SELECT v.*,courante.id AS applicable_id FROM paie_variables v LEFT JOIN LATERAL("
      "SELECT r.* FROM paie_rubrique_versions r WHERE r.societe_id=v.societe_id AND r.rubrique_id=v.rubrique_id AND r.statut='APPROUVEE' AND r.date_debut<=v.date_effet ORDER BY date_debut DESC LIMIT 1) courante "
      "ON (courante.date_fin IS NULL OR courante.date_fin>=v.date_effet) WHERE v.societe_id=:s AND v.employe_id=:e AND v.periode=:p AND v.statut='APPROUVE' ORDER BY v.id LIMIT 501"),params).mappings().all()
    if len(rows)>500:signaler('VOLUME_VARIABLES','Plus de500variables :aucun total partiel présenté comme complet.')
    details=[];gains=Decimal(0)
    for v in rows:
        c=v['instantane']['rubrique'];nature=c['nature']
        details.append({'id':v['id'],'code':v['instantane']['code'],'nature':nature,'montant':format(v['montant'],'.2f'),'date_effet':v['date_effet'],'rubrique_version_id':v['rubrique_version_id']})
        if v['donnees'].get('rattachement_revenus') is not None:details[-1]['rattachement_revenus']={k:v['donnees']['rattachement_revenus'].get(k) for k in ['reference_debut','reference_fin','versement_date']}
        if nature!='GAIN':signaler('IMPACT_A_QUALIFIER','Variable '+str(v['id'])+' :retenue/remboursement à qualifier avant calcul du brut.')
        else:gains+=v['montant']
        if (not a['contrat'] or not a['remuneration'] or (v['contrat_version_id'],v['remuneration_version_id'],v['rubrique_version_id'])!=(a['contrat']['id'],a['remuneration']['id'],v['applicable_id'])):
            signaler('SOURCE_VARIABLE_CHANGEE','Sources de la variable '+str(v['id'])+' différentes des conditions courantes ;régularisation à examiner sans modifier le snapshot.')
    base=Decimal(a['remuneration']['montant']) if a['remuneration'] else None
    return {'employe_id':eid,'nom':a['nom'],'matricule':a['matricule'],'base':format(base,'.2f') if base is not None else None,
      'gains':None if erreurs else format(gains,'.2f'),'brut':None if erreurs else format(base+gains,'.2f'),'anomalies':erreurs,'variables':details,
      'sources':{'contrat':{k:a['contrat'][k] for k in ['id','version','type_contrat','date_effet','date_debut','date_fin']} if a['contrat'] else None,'remuneration':a['remuneration'],'date_entree':d['date_embauche']}}

def sortie(row,user,ctx,reutilise=False):
    r=dict(row)
    if empreinte(r['contenu'])!=r['empreinte']:raise HTTPException(409,'Empreinte du snapshot incohérente ;ne pas utiliser cette simulation.')
    if not (w.AUDIT in ctx['capacites'] or r['auteur_id']==user['id'] or 'personnel.approuver' in ctx['capacites']):r['motif']=None
    r.pop('cle_idempotence',None);r.pop('demande_sha256',None);r['reutilise']=reutilise
    return r

@w.transaction
def simuler(db,user,data):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id'];demande=empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'}))
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:campagnes:{sid}'})
    ancien=db.execute(text('SELECT * FROM paie_simulations_brut WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Cette clé de reprise correspond à une autre demande ;utiliser une nouvelle simulation.')
        return sortie(ancien,user,ctx,True)
    params={'s':sid,'p':data.periode,'t':data.type_campagne,'u':user['id']}
    cid=db.scalar(text('SELECT id FROM paie_campagnes WHERE societe_id=:s AND periode=:p AND type_campagne=:t'),params)
    if cid is None:cid=db.scalar(text('INSERT INTO paie_campagnes(societe_id,periode,type_campagne,cree_par) VALUES(:s,:p,:t,:u) RETURNING id'),params)
    fin=data.periode.replace(day=monthrange(data.periode.year,data.periode.month)[1])
    lignes=[simulation_salarie(db,user,ctx,eid,data.periode,fin) for eid in data.employe_ids]
    complet=all(not x['anomalies'] for x in lignes)
    total=lambda k:format(sum((Decimal(x[k]) for x in lignes),Decimal(0)),'.2f') if complet else None
    contenu={'mode':'SIMULATION_BRUT_NON_VALIDEE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT','periode':data.periode,'type_campagne':data.type_campagne,
      'mois_complets_confirmes':True,'complet_pour_brut':complet,'paie_definitive_autorisee':False,'employes':lignes,
      'totaux':{'base':total('base'),'gains':total('gains'),'brut':total('brut'),'cotisations_salariales':None,'cotisations_patronales':None,'ir':None,'net_a_payer':None,'cout_employeur':None},
      'avertissement':'Brut pédagogique uniquement ;conditions réglementaires,cotisations,IR,net,bulletins etcomptabilisation à compléter. Aucune validation de paie.'}
    numero=db.scalar(text('SELECT coalesce(max(numero),0)+1 FROM paie_simulations_brut WHERE campagne_id=:i'),{'i':cid})
    i=db.scalar(text('INSERT INTO paie_simulations_brut(societe_id,campagne_id,numero,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) '
      'VALUES(:s,:c,:n,:k,:d,CAST(:j AS jsonb),:h,:u,:m) RETURNING id'),{'s':sid,'c':cid,'n':numero,'k':str(data.cle_idempotence),'d':demande,'j':canonique(contenu),'h':empreinte(contenu),'u':user['id'],'m':data.motif})
    row=db.execute(text('SELECT * FROM paie_simulations_brut WHERE id=:i AND societe_id=:s'),{'i':i,'s':sid}).mappings().one()
    return sortie(row,user,ctx)

def lire(db,user,i):
    ctx=autoriser(db,user);r=db.execute(text('SELECT * FROM paie_simulations_brut WHERE id=:i AND societe_id=:s'),{'i':i,'s':user['societe_id']}).mappings().first()
    if not r:raise HTTPException(404,'Simulation introuvable dans cette société.')
    return sortie(r,user,ctx)

def lister(db,user,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'o':decalage,'l':limite}
    total=db.scalar(text('SELECT count(*) FROM paie_campagnes WHERE societe_id=:s'),p)
    rows=db.execute(text("SELECT c.*,v.id AS derniere_simulation_id,v.numero AS derniere_version,(v.contenu->>'complet_pour_brut')::boolean AS complet_pour_brut,v.contenu#>>'{totaux,brut}' AS brut,jsonb_array_length(v.contenu->'employes') AS nombre_salaries FROM paie_campagnes c "
      'LEFT JOIN LATERAL(SELECT * FROM paie_simulations_brut v WHERE v.campagne_id=c.id ORDER BY numero DESC LIMIT 1) v ON true '
      'WHERE c.societe_id=:s ORDER BY c.id DESC OFFSET :o LIMIT :l'),p).mappings()
    return {'total':total,'elements':[dict(x) for x in rows]}

def historique(db,user,cid,decalage=0,limite=25):
    autoriser(db,user)
    if not db.scalar(text('SELECT EXISTS(SELECT 1 FROM paie_campagnes WHERE id=:c AND societe_id=:s)'),{'c':cid,'s':user['societe_id']}):raise HTTPException(404,'Campagne introuvable dans cette société.')
    return [dict(x) for x in db.execute(text('SELECT id,numero,empreinte,auteur_id,cree_at FROM paie_simulations_brut WHERE campagne_id=:c AND societe_id=:s ORDER BY numero DESC OFFSET :o LIMIT :l'),{'c':cid,'s':user['societe_id'],'o':decalage,'l':limite}).mappings()]
