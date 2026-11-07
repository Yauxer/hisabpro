"""Source C3 N-2 explicite : copie d'un snapshot conservé, aucun Journal lu."""
from copy import deepcopy
from decimal import Decimal
from types import SimpleNamespace
from fastapi import HTTPException
import models
from services import balance_etic_tables_service as commun
from services.balance_import_service import lire_preparation,normaliser_balance

BLOC='comparatif_n2_documentaire'
NOTE=('Source comparative N-2 explicitement rattachée depuis une préparation '
 'conservée de la même société, exercice de clôture N−2. La référence, la '
 'version et l’empreinte de cette source restent figées avec sa balance N et '
 'ses états déjà conservés. Aucun historique du Journal n’est repris. '
 'Les pièces restent attachées à leur préparation d’origine ; aucun fichier '
 'n’est transféré automatiquement. Après rattachement, conserver une nouvelle '
 'version des indicateurs C3 pour y inclure N-2 ; les anciens contrôles C3 '
 'ne sont pas réécrits. Une balance après solde119 ne fournit pas l’activité '
 'annuelle. Ce rattachement ne complète pas les données extra-comptables '
 'et ne vaut pas liasse prête à déposer.')


def presentation(dossier):
 bloc=dossier['contenu'].get(BLOC)
 return ({**deepcopy(bloc),'conserve':True,'pret_a_deposer':False} if bloc else
  {'conserve':False,'note':NOTE,'source_preparation':None,'reference_source':'','pret_a_deposer':False})


def candidats(db,user,dossier):
 rows=db.query(models.LiasseBalancePreparation).filter_by(societe_id=user['societe_id'],
  exercice=dossier['exercice']-2).order_by(models.LiasseBalancePreparation.version.desc()).limit(200).all()
 return [{'id':r.id,'version':r.version,'exercice':r.exercice,'empreinte_sha256':r.empreinte_sha256} for r in rows]


def conserver(db,user,preparation_id,data):
 def normaliser(dossier,_tables):
  reference=commun.texte(data.reference_source,'Référence de la source N-2')
  if not reference:raise ValueError('Référence de source N-2 explicitement renseignée requise.')
  return [{'source_preparation_id':data.source_preparation_id,'source_empreinte_sha256':data.source_empreinte_sha256,
    'reference_source':reference}]
 def enrichir(dossier,demande):
  q=demande['tables'][0]
  row=db.query(models.LiasseBalancePreparation).filter_by(id=q['source_preparation_id'],societe_id=user['societe_id']).first()
  if not row:raise HTTPException(404,'Source N-2 introuvable dans cette société.')
  try:source=lire_preparation(row)
  except ValueError as exc:raise HTTPException(409,str(exc)) from exc
  if source['empreinte_sha256']!=q['source_empreinte_sha256']:raise HTTPException(409,'Empreinte de la source N-2 différente de celle choisie.')
  if source['exercice']!=dossier['exercice']-2:raise ValueError('La source doit appartenir à l’exercice de clôture N-2.')
  lignes=source['contenu'].get('sources',{}).get('n')
  if not isinstance(lignes,list) or not lignes or any(not isinstance(r,dict) or not isinstance(r.get('compte'),str)
    or any(r.get(k) is None or r.get(k)=='' for k in ('debit','credit')) for r in lignes):
   raise ValueError('Balance détaillée N de la source N-2 absente ou incomplète.')
  # Même contrôle d’équilibre, doublons, nombres et clôture mixte que l’import.
  # Le plan historique est celui du snapshot, pas un plan courant potentiellement modifié.
  soldes,_=normaliser_balance(lignes,{r['compte'] for r in lignes},'N-2')
  etats=source['contenu'].get('preparation',{}).get('etats')
  if not isinstance(etats,dict) or not etats:raise ValueError('États figés de la source N-2 absents.')
  return {'note':NOTE,'source_preparation':{k:source[k] for k in ('id','version','exercice','empreinte_sha256')},
   'reference_source':q['reference_source'],'periode_source':deepcopy(source['contenu'].get('periode')),
   'nom_fichier_source':source['contenu'].get('sources',{}).get('noms_fichiers',{}).get('n'),
   'sources_n2':deepcopy(lignes),'etats_n2':deepcopy(etats),
   'totaux_exacts':{'comptes':len(soldes),**{k:format(sum((r[k] for r in soldes.values()),Decimal('0.00')),'.2f') for k in ('debit','credit')}}}
 demande=SimpleNamespace(empreinte_parent=data.empreinte_parent,cle=data.cle,tables=[])
 return commun.conserver(db,user,preparation_id,demande,nom_bloc=BLOC,normalisation=normaliser,
  referentiel=lambda d:[],enrichir=enrichir)
