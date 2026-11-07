"""Snapshots sociaux pédagogiques : sources courantes, calcul distinct de l'IR."""
from calendar import monthrange
from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import text
from pydantic import ValidationError
from services import personnel_workflow_service as w,paie_campagnes_service as brut,paie_social_service as social
from services.paie_social_schemas import Contenu
from services.paie_catalogue_schemas import Contenu as Rubrique
from services.paie_social_moteur import assiettes,branche,argent,anomalie


def autoriser(db,user,action=None):
    ctx=social.autoriser(db,user,action)
    if not db.scalar(text("SELECT to_regclass('public.paie_simulations_sociales') IS NOT NULL")):raise HTTPException(503,'Installer la migration117 des simulations sociales.')
    return ctx


def options(db,user,ident):
    autoriser(db,user);source=brut.lire(db,user,ident)
    regimes=list(db.scalars(text('SELECT DISTINCT regime FROM paie_branches_sociales WHERE societe_id=:s ORDER BY regime LIMIT 501'),{'s':user['societe_id']}))
    if len(regimes)>500:raise HTTPException(409,'Plus de500régimes : réduire le référentiel avant la simulation.')
    return {'brut':source,'regimes':regimes,'avertissement':'Les bases CNSS/AMO et l’éligibilité sont à déclarer après contrôle ; aucune affectation automatique.'}


def charger_branches(db,sid,regime,debut,fin):
    roots=db.execute(text('SELECT id,code FROM paie_branches_sociales WHERE societe_id=:s AND regime=:g ORDER BY id LIMIT 501'),{'s':sid,'g':regime}).mappings().all()
    if len(roots)>500:raise HTTPException(409,'Plus de500branches : aucun total tronqué autorisé.')
    result=[]
    for r in roots:
        def au(d):
            v=db.execute(text("SELECT * FROM paie_branche_sociale_versions WHERE societe_id=:s AND branche_id=:i AND statut='APPROUVEE' AND date_debut<=:d ORDER BY date_debut DESC LIMIT 1"),{'s':sid,'i':r['id'],'d':d}).mappings().first()
            return v if v and (v['date_fin'] is None or v['date_fin']>=d) else None
        a=au(debut);b=au(fin);erreurs=[];c=None
        if not a or not b:erreurs.append(anomalie('BRANCHE_SANS_VERSION','Branche '+r['code']+' : version approuvée absente ou expirée sur une partie du mois.'))
        elif a['id']!=b['id']:erreurs.append(anomalie('BRANCHE_CHANGE_DANS_MOIS','Branche '+r['code']+' modifiée dans le mois ; aucun taux moyen inventé.'))
        else:
            try:c=Contenu.model_validate(a['contenu']).model_dump(mode='json')
            except ValidationError:erreurs.append(anomalie('BRANCHE_INVALIDE','Contenu de branche à contrôler, aucune valeur de secours.'))
        result.append({'branche_id':r['id'],'code':r['code'],'version_id':a['id'] if a else None,'version_fin_id':b['id'] if b else None,'contenu':c,'anomalies':erreurs})
    return result


def calcul_salarie(db,user,ctx,e,declaration,branches,debut,fin):
    erreurs=[]
    if not e['brut'] or e['anomalies']:erreurs.append(anomalie('BRUT_INCOMPLET','Brut incomplet ; traiter ses anomalies avant le calcul social.'))
    actuel=brut.simulation_salarie(db,user,ctx,e['employe_id'],debut,fin)
    if brut.empreinte(actuel)!=brut.empreinte(e):erreurs.append(anomalie('SOURCE_BRUT_CHANGEE','Sources courantes différentes du snapshot du brut ; créer une nouvelle simulation du brut.'))
    if not declaration.conditions_confirmees or not declaration.reference_controle:erreurs.append(anomalie('ELIGIBILITE_NON_CONFIRMEE','Régime, parts de base soumises et conditions des rubriques à confirmer avec référence de contrôle.'))
    base={'CNSS':declaration.base_cnss,'AMO':declaration.base_amo}
    if e['base'] is not None and any(x is not None and x>Decimal(e['base']) for x in base.values()):erreurs.append(anomalie('BASE_HORS_SALAIRE','Part soumise de base supérieure à la base salariale ; les gains sont ajoutés séparément.'))
    variables=[]
    for v in e['variables']:
        row=db.execute(text("SELECT * FROM paie_variables WHERE id=:i AND societe_id=:s AND employe_id=:e AND statut='APPROUVE'"),{'i':v['id'],'s':user['societe_id'],'e':e['employe_id']}).mappings().first()
        if not row:erreurs.append(anomalie('VARIABLE_SOURCE_ABSENTE','Variable source approuvée introuvable.'));continue
        try:regles=Rubrique.model_validate(row['instantane']['rubrique']).regles.model_dump(mode='json')
        except (ValidationError,KeyError):erreurs.append(anomalie('RUBRIQUE_SOURCE_INVALIDE','Règles de rubrique source non calculables.'));continue
        variables.append({'id':row['id'],'code':v['code'],'montant':format(row['montant'],'.2f'),'rubrique_id':row['rubrique_id'],'rubrique_version_id':row['rubrique_version_id'],'regles':regles})
    bases=assiettes(base,Decimal(e['brut']) if e['brut'] is not None else None,variables)
    if not branches:erreurs.append(anomalie('REGIME_SANS_BRANCHE','Aucune branche déclarée dans ce régime ; aucun zéro présumé.'))
    lignes=[]
    for b in branches:
        if erreurs or b['anomalies']:
            q={'assiette_avant_plafond':None,'assiette_retenue':None,'salarial':None,'patronal':None,'anomalies':b['anomalies'] or [anomalie('SOURCES_NON_QUALIFIEES','Les anomalies du salarié bloquent cette branche.')]}
        else:q=branche(b['contenu'],bases)
        lignes.append({'branche_id':b['branche_id'],'code':b['code'],'version_id':b['version_id'],**q})
    def total(k):return argent(sum((Decimal(x[k]) for x in lignes),Decimal(0))) if lignes and not erreurs and all(x[k] is not None for x in lignes) else None
    salarial=total('salarial');patronal=total('patronal')
    if salarial is not None and Decimal(salarial)>Decimal(e['brut']):
        erreurs.append(anomalie('COTISATIONS_SUPERIEURES_BRUT','Cotisations salariales supérieures au brut ; paramètres à examiner.'));salarial=None
    return {'employe_id':e['employe_id'],'nom':e['nom'],'matricule':e['matricule'],'brut':e['brut'],'declaration':declaration.model_dump(mode='json'),
      'assiettes':{k:{'montant':argent(v['montant']) if v['montant'] is not None and not erreurs else None,'anomalies':v['anomalies']} for k,v in bases.items()},
      'variables_sources':variables,'branches':lignes,'anomalies':erreurs,'salarial':salarial,'patronal':patronal,'ir':None,'net_a_payer':None}


def sortie(row,user,ctx,reutilise=False):
    r=dict(row)
    if brut.empreinte(r['contenu'])!=r['empreinte']:raise HTTPException(409,'Empreinte de la simulation sociale incohérente.')
    if not (w.AUDIT in ctx['capacites'] or r['auteur_id']==user['id'] or 'personnel.approuver' in ctx['capacites']):r['motif']=None
    r.pop('cle_idempotence',None);r.pop('demande_sha256',None);r['reutilise']=reutilise;return r


@w.transaction
def simuler(db,user,data):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id'];demande=brut.empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'}))
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:social:{sid}:{data.regime}'})
    ancien=db.execute(text('SELECT * FROM paie_simulations_sociales WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Clé de reprise déjà utilisée pour une autre demande.')
        return sortie(ancien,user,ctx,True)
    source=brut.lire(db,user,data.brut_id);c=source['contenu'];debut=date.fromisoformat(c['periode']);fin=debut.replace(day=monthrange(debut.year,debut.month)[1])
    declarations={d.employe_id:d for d in data.declarations}
    if set(declarations)!={e['employe_id'] for e in c['employes']}:raise HTTPException(400,'Déclarer exactement tous les salariés du snapshot du brut ; aucune sélection partielle silencieuse.')
    branches=charger_branches(db,sid,data.regime,debut,fin)
    lignes=[calcul_salarie(db,user,ctx,e,declarations[e['employe_id']],branches,debut,fin) for e in c['employes']]
    def total(k):return argent(sum((Decimal(x[k]) for x in lignes),Decimal(0))) if all(x[k] is not None for x in lignes) else None
    contenu={'mode':'SIMULATION_SOCIALE_NON_VALIDEE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT','paie_definitive_autorisee':False,
      'periode':c['periode'],'regime':data.regime,'brut_id':source['id'],'brut_empreinte':source['empreinte'],'brut_numero':source['numero'],
      'complet_pour_social':all(x['salarial'] is not None and x['patronal'] is not None for x in lignes),'branches_sources':branches,'employes':lignes,
      'totaux':{'brut':c['totaux']['brut'],'cotisations_salariales':total('salarial'),'cotisations_patronales':total('patronal'),'ir':None,'net_a_payer':None,'cout_employeur':None},
      'avertissement':'Arithmétique pédagogique sur paramètres et éligibilité déclarés ; aucune validation juridique ou paie définitive. IR et net non calculés. Les sources étaient contrôlées au moment du calcul, pas requalifiées à la consultation.'}
    numero=db.scalar(text('SELECT coalesce(max(numero),0)+1 FROM paie_simulations_sociales WHERE brut_id=:b AND regime=:g'),{'b':source['id'],'g':data.regime})
    i=db.scalar(text('INSERT INTO paie_simulations_sociales(societe_id,brut_id,regime,numero,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:b,:g,:n,:k,:d,CAST(:j AS jsonb),:h,:u,:m) RETURNING id'),
      {'s':sid,'b':source['id'],'g':data.regime,'n':numero,'k':str(data.cle_idempotence),'d':demande,'j':brut.canonique(contenu),'h':brut.empreinte(contenu),'u':user['id'],'m':data.motif})
    return sortie(db.execute(text('SELECT * FROM paie_simulations_sociales WHERE id=:i AND societe_id=:s'),{'i':i,'s':sid}).mappings().one(),user,ctx)


def lire(db,user,i):
    ctx=autoriser(db,user);r=db.execute(text('SELECT * FROM paie_simulations_sociales WHERE id=:i AND societe_id=:s'),{'i':i,'s':user['societe_id']}).mappings().first()
    if not r:raise HTTPException(404,'Simulation sociale introuvable dans cette société.')
    return sortie(r,user,ctx)


def lister(db,user,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'o':decalage,'l':limite}
    return {'total':db.scalar(text('SELECT count(*) FROM paie_simulations_sociales WHERE societe_id=:s'),p),
      'elements':[dict(x) for x in db.execute(text("SELECT id,brut_id,regime,numero,auteur_id,cree_at,contenu->>'periode' AS periode,contenu->>'complet_pour_social' AS complet,contenu#>>'{totaux,cotisations_salariales}' AS salarial,contenu#>>'{totaux,cotisations_patronales}' AS patronal FROM paie_simulations_sociales WHERE societe_id=:s ORDER BY id DESC OFFSET :o LIMIT :l"),p).mappings()]}
