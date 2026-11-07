"""Simulation brute TP sur VL/classe explicitement fournies, sans imposition."""
from copy import deepcopy
from datetime import date
from decimal import Decimal,localcontext,ROUND_HALF_UP
import re
from services import balance_etic_tables_service as commun
BLOC='taxe_professionnelle_documentaire'
TAUX={'C3':10,'C2':20,'C1':30}
NORMAL='Établissement avec local — hors régime particulier, exonération et réduction'
SOURCE={'titre':'Loi47-06, article9-I — taux normaux ; extraits officiels DGCT','notice_url':'https://pnct.ltc.ma/fr/principales-dispositions-de-la-loi-ndeg14-25-en-date-du-6-juin-2025-modifiant-et-completant-la-loi','url':'https://www.collectivites-territoriales.gov.ma/sites/default/files/pnct/2025-05/Fiscalit%C3%A9%20des%20CTs%20VF%2019%2012%202024.pdf','lecture':'Extraits officiels indexés du guide DGCT2024 et notices07-20/14-25 ; binaire consolidé non obtenu','pages':'Guide DGCT, page imprimée120 ; articles7-10 à qualifier sur pièces'}
LIBELLES={'valeur_locative_totale':'Valeurs locatives saisies','brut_arithmetique':'Somme des simulations brutes au centime','brut_propose':'Brut simulé après revue documentaire déclarée','avis_comparables':'Avis saisis et rattachés explicitement','ecart_brut_avis':'Écart brut simulé moins avis déclarés'}
NOTE=('Simulation interne de taxe professionnelle sur valeurs locatives et classes fournies sur pièces. '
 'Le barème normal lu dans les extraits officiels DGCT est C3=10%,C2=20%,C1=30%. '
 'Aucune classe ou VL n’est déduite du plan comptable, du loyer ou de la valeur nette des immobilisations. '
 'La base annuelle complète, la classe, la situation au1erjanvier et l’absence de régime particulier/exonération/réduction doivent être explicitement revues. '
 'Les règles de base de l’article7, établissements hôteliers, exonérations, réductions et cas sans local restent à qualifier. '
 'Aucun droit minimum universel, franchise d’émission, prorata, échéance, montant dû ou paiement calculé. '
 'Un brut faible ou nul n’est pas une exonération ; un tableau néant ne prouve pas une absence de TP. '
 'Les calculs sont arrondis au centime HALF_UP par établissement comme convention arithmétique documentaire, pas comme arrondi légal validé ; le brut exact reste conservé. '
 'Le modèle administratif applicable n’est pas intégré. Aucun Journal, immobilisation, avis ou donnée réelle modifié ; aucune imposition ou déclaration officielle validée.')

def catalogue(dossier):
 b=dossier['contenu'].get(BLOC)
 if b:return deepcopy(b['catalogue'])
 p=[('nature','Désignation du dossier TP','text'),('annee_tp','Année civile TP déclarée','text'),('periode_revue','Période fiscale revue','text'),('exhaustivite','Liste des établissements exhaustive revue','text'),('referentiel_revu','Référentiel applicable revu sur pièces','text')]
 e=[('nature','Désignation de l’établissement','text'),('etablissement_ref','Identifiant interne de l’établissement','text'),('commune','Commune déclarée','text'),('adresse','Adresse de l’établissement','text'),('activite','Activité principale déclarée','text'),('classe','Classe déclarée et justifiée','text'),('valeur_locative','Valeur locative annuelle fournie','number'),('base_revue','Base annuelle complète revue','text'),('classe_revue','Classe revue sur référence','text'),('regime','Périmètre déclaré de l’établissement','text'),('situation_janvier_revue','Situation au premier janvier revue','text'),('montant_avis','Montant de l’avis fourni','number'),('reference_avis','Référence de l’avis fourni','text'),('avis_rattache','Avis rattaché à l’année TP déclaré','text')]
 return [{'code':code,'groupe':'Interne','titre':titre,'colonnes_saisie':[{'cle':k,'label':label,'type':typ} for k,label,typ in cols]} for code,titre,cols in [('TP-P','Profil documentaire TP annuel',p),('TP-E','Établissements, bases et avis',e)]]

def normaliser(dossier,tables):
 ts=commun.normaliser(dossier,tables,referentiel=catalogue)
 if len(ts[0]['lignes'])>1 or len(ts[1]['lignes'])>50:raise ValueError('Un profil et cinquante établissements maximum.')
 vus=set()
 for t in ts:
  for a in t['lignes']:
   if not a['nature'] or not a['reference_source']:raise ValueError('Désignation et référence source requises, même pour une saisie partielle.')
   for k in ('periode_revue','exhaustivite','referentiel_revu','base_revue','classe_revue','situation_janvier_revue','avis_rattache'):
    if k in a and a[k] not in ('','oui','non'):raise ValueError('Revue TP : oui, non ou champ vide.')
   if t['code']=='TP-P':
    if a['annee_tp'] and (not re.fullmatch('[0-9]{4}',a['annee_tp']) or not 1900<=int(a['annee_tp'])<=9999):raise ValueError('Année civile TP de quatre chiffres requise.')
   else:
    ref=a['etablissement_ref'].casefold()
    if not ref or ref in vus:raise ValueError('Identifiant interne d’établissement requis et unique.')
    vus.add(ref)
    if a['classe'] not in ('',*TAUX):raise ValueError('Classe TP inconnue.')
    if a['regime'] not in ('',NORMAL,'Situation particulière — à qualifier'):raise ValueError('Périmètre documentaire TP inconnu.')
 return ts

def calculer_controles(dossier,demande):
 tp,te=demande['tables'];p=tp['lignes'][0] if tp['lignes'] else {};annee=p.get('annee_tp','')
 couvert=annee=='2026' and dossier['exercice']==2026
 profil=tp['statut']=='documente' and all(p.get(k)=='oui' for k in ('periode_revue','exhaustivite','referentiel_revu'))
 lignes=[];alertes=[];refs_avis={};doublon_avis=False
 with localcontext() as ctx:
  ctx.prec=60
  for i,a in enumerate(te['lignes'],1):
   points=[]
   for k,label in [('commune','Commune'),('adresse','Adresse'),('activite','Activité principale')]:
    if not a[k]:points.append(label)
   if a['valeur_locative'] is None:points.append('Valeur locative annuelle')
   if not a['classe']:points.append('Classe')
   for k,label in [('base_revue','Base annuelle complète à revoir'),('classe_revue','Classe et référence à revoir'),('situation_janvier_revue','Situation au1erjanvier à revoir')]:
    if a[k]!='oui':points.append(label)
   if a['regime']!=NORMAL:points.append('Régime particulier ou périmètre à qualifier')
   taux=TAUX.get(a['classe']);exact=Decimal(a['valeur_locative'])*taux/100 if taux is not None and a['valeur_locative'] is not None else None
   brut=None if exact is None else exact.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
   avis_ok=a['montant_avis'] is not None and bool(a['reference_avis']) and a['avis_rattache']=='oui'
   if a['reference_avis']:
    ref=a['reference_avis'].casefold()
    if ref in refs_avis:doublon_avis=True
    refs_avis[ref]=a['etablissement_ref']
   ecart=None if brut is None or not avis_ok else brut-Decimal(a['montant_avis'])
   if ecart is not None and ecart!=0:alertes.append('Établissement '+a['etablissement_ref']+' : écart avec l’avis saisi, revoir les sources sans corriger l’avis ni le Journal.')
   if brut is not None and brut<200:alertes.append('Établissement '+a['etablissement_ref']+' : brut inférieur à200MAD ; aucune franchise, émission ou exonération déduite automatiquement.')
   lignes.append({'etablissement_ref':a['etablissement_ref'],'nom':a['nature'],'classe':a['classe'],'taux_normal':taux,'brut_exact':None if exact is None else format(exact,'f'),'brut_arithmetique':None if brut is None else format(brut,'.2f'),'points_a_revoir':points,'avis_comparable_declare':bool(avis_ok),'ecart_avis':None if ecart is None else format(ecart,'.2f')})
  complet=bool(couvert and profil and te['statut']=='documente' and lignes and not any(a['points_a_revoir'] for a in lignes))
  def somme(vals):return None if not vals or any(v is None for v in vals) else format(sum((Decimal(v) for v in vals),Decimal(0)),'.2f')
  vl=somme([a['valeur_locative'] for a in te['lignes']]);brut=somme([a['brut_arithmetique'] for a in lignes])
  avis=somme([a['montant_avis'] if l['avis_comparable_declare'] else None for a,l in zip(te['lignes'],lignes)]) if not doublon_avis else None
  if doublon_avis:alertes.append('Référence d’avis partagée entre établissements : total des avis inconnu sans ventilation justifiée ; aucune double addition automatique.')
  if not couvert:alertes.append('Année TP non renseignée, différente de la préparation ou hors2026 ; brut global qualifié indisponible.')
  if not complet:alertes.append('Profil ou établissements à compléter/qualifier ; le brut arithmétique ne prouve pas une imposition.')
  if not lignes:alertes.append('Aucun établissement saisi ne signifie pas absence de taxe professionnelle : les situations sans local restent à qualifier.')
  return {'methode':'simulation_tp_normale_documentaire_v1','annee_tp_declaree':annee,'periode_balance':deepcopy(dossier['contenu']['periode']),'exercice_couvert':couvert,'revue_documentaire_declaree':complet,'montants':{'valeur_locative_totale':vl,'brut_arithmetique':brut,'brut_propose':brut if complet else None,'avis_comparables':avis,'ecart_brut_avis':None if brut is None or avis is None else format(Decimal(brut)-Decimal(avis),'.2f')},'etablissements':lignes,'reference_juridique':deepcopy(SOURCE),'alertes':alertes,'montant_du_confirme':None,'imposition_confirmee':False,'paiement_confirme':False,'pret_a_deposer':False}

def presentation(dossier):
 b=dossier['contenu'].get(BLOC) or {};v=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=b.get('note_conservee',NOTE));v['controle_tp']=deepcopy(b.get('controle_tp'));return v

def conserver(db,user,preparation_id,data):
 return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,referentiel=catalogue,enrichir=lambda d,q:{'controle_tp':calculer_controles(d,q),'note_conservee':NOTE})
