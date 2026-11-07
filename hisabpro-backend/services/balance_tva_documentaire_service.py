"""B14 documentaire indépendant : aucun flux TVA déduit d'une balance."""
from copy import deepcopy
from decimal import Decimal,localcontext
from services import balance_etic_tables_service as commun
from services.balance_emetteurs_service import nombre
from services.balance_import_service import montant_import

BLOC='tva_documentaire'
FAMILLES={'4455':'TVA facturée / collectée','34552':'TVA récupérable sur charges','34551':'TVA récupérable sur immobilisations'}
CHAMPS={'solde_debut_declare':'Solde de début déclaré','operations_declarees':'Opérations déclarées',
 'declarations_declarees':'Déclarations justifiées','solde_fin_reconstitue':'Solde de fin reconstitué',
 'solde_fin_balance_n':'Solde de fin balance N','solde_fin_balance_n1_memoire':'Solde de fin N-1 pour mémoire',
 'ecart_fin':'Écart fin reconstituée moins balance N'}
NOTE=('B14 documentaire interne en MAD : seules les balances conservées sont lues. '
 '4455 en crédit moins débit ;34551/34552 en débit moins crédit. Soldes inverses signés. '
 'Le solde de fin N-1 est pour mémoire, jamais assimilé à une ouverture N. '
 'Ouvertures, opérations et déclarations sont explicitement saisies et justifiées, '
 'jamais déduites d’une variation de soldes ou du journalTV. Fin reconstituée = '
 'début + opérations − déclarations, selon le périmètre du tableau existant. '
 'Une référence de déclarations ne prouve pas à elle seule leur dépôt. '
 'Une case vide reste inconnue ; zéro est une déclaration explicite sourcée. '
 'TVA récupérable = charges + immobilisations ; net documentaire = collectée '
 'moins récupérable, sans liquidation, déductibilité, exigibilité ou paiement '
 'déduits. Écarts visibles, aucune correction automatique. Les contrôles figés '
 'restent distincts du brouillon ; aucune écriture, déclaration ou donnée du '
 'module TVA réel n’est lue ou modifiée. Ce tableau n’est pas prêt à déposer.')


def disponibilites(dossier):
 def dispo(rows):
  return isinstance(rows,list) and all(isinstance(r,dict) and isinstance(r.get('compte'),str)
   and all(r.get(k) is not None and r.get(k)!='' for k in ('debit','credit')) for r in rows)
 return {p:{'disponible':dispo(dossier['contenu'].get('sources',{}).get(p))} for p in ('n','n1')}


def catalogue(dossier):
 bloc=dossier['contenu'].get(BLOC)
 if bloc:return deepcopy(bloc['catalogue'])
 return [{'code':'B14-N','groupe':'B','titre':'Détail TVA documentaire — N','colonnes_saisie':[
  {'cle':'nature','label':'Famille TVA (4455/34552/34551)','type':'text'},
  *[{'cle':k,'label':label,'type':'number','unite':'MAD','signe':True} for k,label in (
   ('solde_debut','Solde de début déclaré'),('operations','Opérations déclarées'),('declarations','Déclarations justifiées'))],
  {'cle':'references_declarations','label':'Références des déclarations ou du néant justifié','type':'text'}]}]


def normaliser(dossier,tables):
 tables=commun.normaliser(dossier,tables,referentiel=catalogue,convertir_nombre=nombre)
 t=tables[0];vus=set()
 if len(t['lignes'])>3:raise ValueError('Trois familles TVA au maximum.')
 if not disponibilites(dossier)['n']['disponible'] and (t['lignes'] or t['statut']!='a_completer' or t['justification']):
  raise ValueError('Source N détaillée indisponible ; aucune synthèse TVA conservée.')
 for row in t['lignes']:
  if row['nature'] not in FAMILLES or row['nature'] in vus:raise ValueError('Famille TVA inconnue ou en doublon.')
  vus.add(row['nature'])
  if not row['reference_source']:raise ValueError('Une référence de source est requise pour toute ligne, même partielle.')
  if row['declarations'] is not None and not row['references_declarations']:
   raise ValueError('Références de déclarations ou du néant justifié requises, y compris pour zéro.')
 return tables


def sources(dossier):
 dispo=disponibilites(dossier);result={}
 for p in ('n','n1'):
  d=dispo[p];totaux={k:Decimal('0.00') if d['disponible'] else None for k in FAMILLES};lignes=[]
  if d['disponible']:
   for row in dossier['contenu']['sources'][p]:
    for famille in FAMILLES:
     if row['compte'].startswith(famille):
      net=montant_import(row['credit'],'Source TVA crédit')-montant_import(row['debit'],'Source TVA débit')
      if famille!='4455':net=-net
      totaux[famille]+=net
      if net:lignes.append({'compte':row['compte'],'famille':famille,'montant':format(net,'.2f'),'intitule':None})
  result[p]={**d,'motif':'' if d['disponible'] else 'Source détaillée absente ou incomplète, aucun solde nul fabriqué.',
   'soldes':{k:None if v is None else format(v,'.2f') for k,v in totaux.items()},'lignes':sorted(lignes,key=lambda r:r['compte'])}
 return result


def calculer_controles(dossier,demande):
 with localcontext() as ctx:
  ctx.prec=60;src=sources(dossier);t=demande['tables'][0];rows={r['nature']:r for r in t['lignes']};lignes=[]
  for famille,label in FAMILLES.items():
   row=rows.get(famille,{})
   debut,ops,decl=(None if row.get(k) is None else Decimal(row[k]) for k in ('solde_debut','operations','declarations'))
   fin=None if any(v is None for v in (debut,ops,decl)) else debut+ops-decl
   n,n1=(None if src[p]['soldes'][famille] is None else Decimal(src[p]['soldes'][famille]) for p in ('n','n1'))
   montants=dict(zip(CHAMPS,(debut,ops,decl,fin,n,n1,None if fin is None or n is None else fin-n)))
   lignes.append({'famille':famille,'titre':label,'montants':montants,'references_declarations':row.get('references_declarations',''),
    'reference_source':row.get('reference_source','')})
  def total(cle,operateur,a,b):
   return None if a[cle] is None or b[cle] is None else operateur(a[cle],b[cle])
  a,b,c=[r['montants'] for r in lignes]
  rec={k:total(k,lambda x,y:x+y,b,c) for k in CHAMPS}
  net={k:total(k,lambda x,y:x-y,a,rec) for k in CHAMPS}
  for code,label,m in [('recuperable_total','TVA récupérable totale',rec),('net_documentaire','Net TVA documentaire',net)]:
   lignes.append({'famille':code,'titre':label,'montants':m,'references_declarations':'','reference_source':''})
  for r in lignes:r['montants']={k:None if v is None else format(v,'.2f') for k,v in r['montants'].items()}
  alertes=[r['titre']+' : écart à justifier, aucune correction automatique.' for r in lignes[:3]
   if r['montants']['ecart_fin'] is not None and Decimal(r['montants']['ecart_fin'])!=0]
  if t['statut']=='neant_declare' and any(v not in (None,'0.00') for v in src['n']['soldes'].values()):
   alertes.append('Néant déclaré avec soldes TVA non nuls ; aucun flux égal à zéro déduit.')
  return {'methode':'soldes_tva_sources_et_flux_declares_decimal_v1','sources':src,'lignes':lignes,
   'alertes':alertes,'depot_confirme':False,'liquidation_calculee':False,'pret_a_deposer':False}


def presentation(dossier):
 bloc=dossier['contenu'].get(BLOC) or {}
 vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
 vue['sources']=disponibilites(dossier);vue['controle_tva']=deepcopy(bloc.get('controle_tva'))
 notes=dossier['contenu'].get('notes_etic_documentaires',{}).get('lignes',[])
 if any(r['code']=='B14' and r['statut']=='non_applicable' for r in notes) and any(t['lignes'] for t in vue['tables']):
  vue['alertes'].append('La note B14 est non applicable alors que des flux TVA sont déclarés ; revoir les deux compléments.')
 return vue


def conserver(db,user,preparation_id,data):
 return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,referentiel=catalogue,
  enrichir=lambda d,q:{'controle_tva':calculer_controles(d,q),'note_conservee':NOTE})
