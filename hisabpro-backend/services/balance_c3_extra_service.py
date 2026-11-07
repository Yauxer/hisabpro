"""Déclarations C3 explicites, indépendantes du Journal et des salariés."""
from copy import deepcopy
from services import balance_etic_tables_service as commun
from services.balance_emetteurs_service import nombre

BLOC='extra_c3_documentaire'
PERIODES={'C3-N':'n','C3-N1':'n1','C3-N2':'n2'}
CHAMPS={
 'effectif_moyen':('Effectif moyen déclaré','personnes',False),
 'benefices_distribues':('Bénéfices distribués déclarés','MAD',False),
 'resultat_par_titre':('Résultat par titre déclaré','MAD / titre',True),
 'distribution_par_titre':('Distribution par titre déclarée','MAD / titre',False)}
NOTE=('Déclarations extra-comptables C3 internes, une synthèse explicitement '
 'sourcée par période N/N-1/N-2. Effectif moyen en personnes, bénéfices distribués '
 'en MAD et valeurs par titre en MAD/titre ; précision technique de deux '
 'décimales maximum, sans arrondi silencieux. Aucun effectif déduit des salariés '
 'ou du6171 ; aucun bénéfice distribué ou montant par titre déduit du net, du '
 'capital ou d’un mouvement bancaire. Les valeurs par titre sont déclarées, '
 'pas calculées sans justificatif du nombre et de la nature des titres. '
 'Les décisions et affectations restent à justifier. Vide signifie inconnu, '
 'zéro explicite n’est jamais inféré. Un résultat par titre négatif est conservé. '
 'Aucune condition de distribution ou règle sociale n’est validée. '
 'Après conservation, créer une nouvelle version des indicateurs C3 pour y '
 'inclure ces déclarations ; anciens contrôles inchangés. Les données '
 'extra-comptables peuvent être documentées même si la balance d’une période '
 'reste absente : la comptabilité de cette période reste indisponible. '
 'Aucun Journal, salarié ou module de paie lu ou modifié ; pas de prêt à déposer.')


def catalogue(dossier):
 bloc=dossier['contenu'].get(BLOC)
 if bloc:return deepcopy(bloc['catalogue'])
 cols=[{'cle':'nature','label':'Désignation de la déclaration C3','type':'text'},
  *[{'cle':k,'label':label,'unite':u,'signe':s,'type':'number'} for k,(label,u,s) in CHAMPS.items()],
  {'cle':'affectations_justifiees','label':'Décisions et affectations à justifier','type':'text'}]
 return [{'code':code,'groupe':'C','titre':'Déclarations C3 — '+{'n':'N','n1':'N-1','n2':'N-2'}[p],
  'colonnes_saisie':deepcopy(cols)} for code,p in PERIODES.items()]


def nombre_declaration(colonne,valeur,contexte):
 # Unité de présentation (personnes/MAD par titre) distincte du pourcentage.
 return nombre({**colonne,'unite':'MAD'},valeur,contexte)


def normaliser(dossier,tables):
 tables=commun.normaliser(dossier,tables,referentiel=catalogue,convertir_nombre=nombre_declaration)
 for t in tables:
  if len(t['lignes'])>1:raise ValueError('Une seule synthèse C3 sourcée par période.')
  for row in t['lignes']:
   if not row['nature'] or not row['reference_source']:raise ValueError('Désignation et référence de source requises, même pour une déclaration partielle.')
 return tables


def declarations(demande):
 resultat={}
 for t in demande['tables']:
  r=t['lignes'][0] if t['lignes'] else {}
  resultat[PERIODES[t['code']]]={**{k:r.get(k) for k in CHAMPS},
   **{k:r.get(k,'') for k in ('nature','reference_source','affectations_justifiees')}}
 return resultat


def presentation(dossier):
 bloc=dossier['contenu'].get(BLOC) or {}
 vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
 vue['declarations_c3']=deepcopy(bloc.get('declarations_c3'))
 notes=dossier['contenu'].get('notes_etic_documentaires',{}).get('lignes',[])
 if any(r['code']=='C3' and r['statut']=='non_applicable' for r in notes) and any(t['lignes'] for t in vue['tables']):
  vue['alertes'].append('La note C3 est non applicable alors que des déclarations sont conservées ; revoir les deux compléments.')
 return vue


def conserver(db,user,preparation_id,data):
 return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,
  referentiel=catalogue,enrichir=lambda d,q:{'declarations_c3':declarations(q),'note_conservee':NOTE})


def integrer(vue,dossier):
 """Nouvelle projection C3 seulement : ne réécrit pas les contrôles conservés."""
 bloc=dossier['contenu'].get(BLOC);vue['provenance_extra_c3']=None
 if not bloc:return vue
 refs={}
 for p,v in vue['periodes'].items():
  r=deepcopy(bloc.get('declarations_c3',{}).get(p,{}))
  for k,(_label,u,signe) in CHAMPS.items():
   x=r.get(k);v[k]=None if x is None else nombre_declaration({'unite':u,'signe':signe},x,k)
  ref=commun.texte(r.get('reference_source',''),'Référence C3')
  nature=commun.texte(r.get('nature',''),'Désignation C3')
  affectation=commun.texte(r.get('affectations_justifiees',''),'Affectations C3')
  if (any(v[k] is not None for k in CHAMPS) or affectation) and (not ref or not nature):
   raise ValueError('Déclarations C3 sans désignation ou référence explicite.')
  v.update(reference_extra_c3=ref,nature_extra_c3=nature,affectations_justifiees=affectation);refs[p]=ref
 vue['provenance_extra_c3']={'cle':bloc['cle'],'references':refs}
 vue['note']=('C3 interne depuis les seules balances conservées et les compléments '
  'explicitement rattachés. Comptabilité et déclarations extra-comptables distinctes ; '
  'les valeurs par titre sont déclarées, pas calculées depuis le net/capital. '
  'Effectif en personnes, montants en MAD ou MAD/titre. Aucun salarié, Journal '
  'ou module fiscal réel lu. Garde119 : activité inconnue après solde technique. '
  'Les références et affectations restent à justifier ; vide ne vaut pas zéro. '
  'Écarts aux états figés visibles, aucun C3 réglementaire complet ou prêt à déposer.')
 vue['informations_a_completer']=([] if vue.get('provenance_n2') else ['Source N-2'])+[
  label+' '+{'n':'N','n1':'N-1','n2':'N-2'}[p]
  for p,d in vue['periodes'].items() for k,label in [(k,x[0]) for k,x in CHAMPS.items()]+[('affectations_justifiees','Affectations justifiées')]
  if d.get(k) is None or d.get(k)=='']
 return vue
