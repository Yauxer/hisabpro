"""Préparation interne151 : identités et montants explicites, aucun dépôt ni taux."""
from copy import deepcopy
from datetime import date
from decimal import Decimal,localcontext
import re
from services import balance_etic_tables_service as commun
from services.balance_css_service import SOURCE as SOURCE_CGI

BLOC='remunerations_tiers_documentaires'
SOURCE={**SOURCE_CGI,'titre':'CGI2026, article151 — préparation documentaire interne','pages_imprimees':'283-284'}
CATEGORIES=('Honoraires','Commissions, courtages et rémunérations similaires','Rabais, remises et ristournes après facturation','Produits de location — annexe à qualifier','Autre — à qualifier')
REGIMES=('Personne morale IS','Personne physique RNR ou RNS','CPU','Autoentrepreneur','Autre — à qualifier')
EVENEMENTS=('Versement','Mise à disposition','Inscription en compte','Aucune retenue déclarée')
SENS=('Allocation','Correction documentée')
MONTANTS={'comptabilise':'Sommes comptabilisées nettes déclarées','soumis':'Sommes soumises nettes déclarées','retenu':'Retenues nettes déclarées'}
CHAMPS={'adresse':'Adresse','activite':'Profession ou activité','cnss':'CNSS du bénéficiaire à qualifier sur pièce','regime':'Régime du bénéficiaire','identite_revue':'Revue de l’identité sur pièces','identification_fiscale_ou_tp':'Identification fiscale ou taxe professionnelle','beneficiaire_ref':'Bénéficiaire lié','categorie':'Catégorie de rémunération','sens':'Sens du mouvement','date_comptabilisation':'Date comptable','evenement':'Événement fiscal déclaré','comptabilise':'Somme comptabilisée','soumis':'Somme soumise','retenu':'Montant retenu','source_revue':'Revue de la source','date_evenement':'Date fiscale justifiée','comptabilisation_hors_periode':'Comptabilisation hors de la période source','evenement_hors_periode':'Événement fiscal hors de la période source','categorie_particuliere_a_qualifier':'Catégorie particulière et annexe à qualifier','identite_a_completer':'Identité du bénéficiaire à compléter','regime_particulier_a_qualifier':'Régime particulier et annexe à qualifier'}
NOTE=('Préparation interne des rémunérations allouées aux tiers. Les bénéficiaires, catégories, '
      'dates et montants sont déclarés sur pièces, sans taux ou qualification automatique. '
      'Les trois montants sont distincts ; vide signifie inconnu et zéro doit être explicite. '
      'Une correction documentée soustrait les montants saisis et conserve sa référence d’origine. '
      'Aucune écriture, fiche tiers, capture RAS ou donnée fiscale réelle n’est modifiée. '
      'Les états particuliers CPU/autoentrepreneurs et locations restent à qualifier. '
      'Le modèle administratif applicable reste à obtenir ; aucun dépôt officiel, EDI ou prêt à déposer. '
      'Une saisie documentée et des totaux concordants ne prouvent pas la conformité juridique. '
      'Les totaux portent sur les pièces saisies ; aucun rapprochement au CPC ou au Journal n’est vérifié automatiquement. '
      'La CNSS demandée est celle du bénéficiaire tiers, distincte de la paie.')

def catalogue(dossier):
 b=dossier['contenu'].get(BLOC)
 if b:return deepcopy(b['catalogue'])
 p=[('nature','Désignation du dossier tiers','text'),('periode_confirmee','Période comptable vérifiée','text'),('exhaustivite','Exhaustivité des sources revue','text'),('absence','Absence de rémunérations confirmée','text')]
 b=[('nature','Nom ou raison sociale du bénéficiaire','text'),('beneficiaire_ref','Identifiant interne du bénéficiaire','text'),('adresse','Adresse du bénéficiaire','text'),('activite','Profession ou activité du bénéficiaire','text'),('identifiant_fiscal','Identification fiscale du bénéficiaire','text'),('identification_tp','Identification taxe professionnelle','text'),('cnss','CNSS du bénéficiaire','text'),('regime','Régime déclaré du bénéficiaire','text'),('identite_revue','Identité revue sur pièces','text')]
 m=[('nature','Désignation du mouvement tiers','text'),('beneficiaire_ref','Bénéficiaire du mouvement','text'),('categorie','Catégorie déclarée de rémunération','text'),('sens','Sens documentaire du mouvement','text'),('date_comptabilisation','Date comptable source','date'),('comptabilise','Somme comptabilisée','number'),('evenement','Événement fiscal déclaré','text'),('date_evenement','Date de cet événement justifiée','date'),('soumis','Somme soumise à retenue','number'),('retenu','Montant retenu','number'),('reference_origine','Référence du mouvement corrigé','text'),('source_revue','Source du mouvement revue','text')]
 return [{'code':code,'groupe':'Interne','titre':titre,'colonnes_saisie':[{'cle':k,'label':label,'type':typ} for k,label,typ in cols]} for code,titre,cols in [('T151-P','Profil documentaire annuel',p),('T151-B','Identités documentaires des bénéficiaires',b),('T151-M','Mouvements et retenues documentés',m)]]

def normaliser(dossier,tables):
 ts=commun.normaliser(dossier,tables,referentiel=catalogue)
 if len(ts[0]['lignes'])>1 or len(ts[1]['lignes'])>50:raise ValueError('Un profil et cinquante bénéficiaires maximum.')
 for t in ts:
  for row in t['lignes']:
   if not row['nature'] or not row['reference_source']:raise ValueError('Désignation et référence source requises, même pour une saisie partielle.')
   for k in ('periode_confirmee','exhaustivite','absence','identite_revue','source_revue'):
    if k in row and row[k] not in ('','oui','non'):raise ValueError('Revue documentaire : oui, non ou champ vide.')
 refs={}
 for row in ts[1]['lignes']:
  ref=row['beneficiaire_ref'].casefold()
  if not ref:raise ValueError('Identifiant interne du bénéficiaire requis pour relier ses mouvements.')
  if ref in refs:raise ValueError('Identifiant interne du bénéficiaire en doublon.')
  refs[ref]=row
  if row['regime'] not in ('',*REGIMES):raise ValueError('Régime documentaire inconnu.')
 vus=set()
 for row in ts[2]['lignes']:
  ref=row['reference_source'].casefold()
  if ref in vus:raise ValueError('Référence source du mouvement en doublon ; conserver chaque source une seule fois.')
  vus.add(ref)
  if row['beneficiaire_ref'] and row['beneficiaire_ref'].casefold() not in refs:raise ValueError('Le bénéficiaire du mouvement est absent des identités de cette préparation.')
  for champ,choix in [('categorie',CATEGORIES),('sens',SENS),('evenement',EVENEMENTS)]:
   if row[champ] not in ('',*choix):raise ValueError('Valeur documentaire inconnue : '+champ+'.')
  for k in ('date_comptabilisation','date_evenement'):
   if row[k]:
    try:
     if not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}',row[k]):raise ValueError()
     date.fromisoformat(row[k])
    except ValueError as exc:raise ValueError('Date ISO valide requise : '+k+'.') from exc
  if row['sens']=='Correction documentée' and (not row['reference_origine'] or row['reference_origine'].casefold()==ref):raise ValueError('La correction doit référencer un mouvement d’origine distinct.')
  if row['sens']=='Allocation' and row['reference_origine']:raise ValueError('Une référence corrigée nécessite le sens Correction documentée.')
  if row['soumis'] is not None and row['retenu'] is not None and Decimal(row['retenu'])>Decimal(row['soumis']):raise ValueError('Le montant retenu saisi dépasse la somme soumise saisie.')
  if row['evenement']=='Aucune retenue déclarée' and (row['date_evenement'] or any(row[k] is not None and Decimal(row[k])!=0 for k in ('soumis','retenu'))):raise ValueError('Absence de retenue incompatible avec une date fiscale ou un montant soumis/retenu non nul.')
 p=ts[0]['lignes'][0] if ts[0]['lignes'] else {}
 if p.get('absence')=='oui' and (ts[1]['lignes'] or ts[2]['lignes']):raise ValueError('Absence de rémunérations incompatible avec des bénéficiaires ou mouvements saisis.')
 return ts

def calculer_controles(dossier,demande):
 tp,tb,tm=demande['tables'];p=tp['lignes'][0] if tp['lignes'] else {};periode=deepcopy(dossier['contenu']['periode'])
 profil=tp['statut']=='documente' and p.get('periode_confirmee')=='oui' and p.get('exhaustivite')=='oui'
 absence=bool(profil and p.get('absence')=='oui' and tb['statut']==tm['statut']=='neant_declare')
 beneficiaires=[];refs={};ifs={};alertes=[]
 for i,b in enumerate(tb['lignes'],1):
  manquants=[k for k in ('adresse','activite','cnss','regime') if not b[k]]
  if not b['identifiant_fiscal'] and not b['identification_tp']:manquants.append('identification_fiscale_ou_tp')
  if b['identite_revue']!='oui':manquants.append('identite_revue')
  if b['regime'] in ('CPU','Autoentrepreneur'):alertes.append('Bénéficiaire '+b['beneficiaire_ref']+' : état particulier CPU/autoentrepreneur à qualifier ; aucun modèle administratif généré.')
  if b['identifiant_fiscal']:
   cle=b['identifiant_fiscal'].casefold()
   if cle in ifs:alertes.append('Identification fiscale partagée entre bénéficiaires '+ifs[cle]+' et '+b['beneficiaire_ref']+' : vérifier les identités, aucun regroupement automatique.')
   ifs[cle]=b['beneficiaire_ref']
  r={'reference':b['beneficiaire_ref'],'nom':b['nature'],'champs_a_completer':manquants,'points_a_revoir':[CHAMPS[k] for k in manquants],'revue_declaree':b['identite_revue']=='oui'}
  refs[b['beneficiaire_ref'].casefold()]=r;beneficiaires.append(r)
 def total(rows,k,zero=False):
  if zero:return '0.00'
  if not rows or any(a[k] is None or a['sens'] not in SENS for a in rows):return None
  with localcontext() as ctx:
   ctx.prec=60
   return format(sum((Decimal(a[k])*(-1 if a['sens']=='Correction documentée' else 1) for a in rows),Decimal(0)),'.2f')
 lignes=[];groupes={}
 for i,m in enumerate(tm['lignes'],1):
  inconnus=[k for k in ('beneficiaire_ref','categorie','sens','date_comptabilisation','evenement') if not m[k]]
  inconnus += [k for k in MONTANTS if m[k] is None]
  if m['source_revue']!='oui':inconnus.append('source_revue')
  if m['evenement'] in EVENEMENTS[:3] and not m['date_evenement']:inconnus.append('date_evenement')
  if m['date_comptabilisation'] and not periode['debut']<=m['date_comptabilisation']<=periode['fin']:inconnus.append('comptabilisation_hors_periode')
  if m['date_evenement'] and not periode['debut']<=m['date_evenement']<=periode['fin']:inconnus.append('evenement_hors_periode')
  if m['categorie'] in CATEGORIES[3:]:inconnus.append('categorie_particuliere_a_qualifier')
  b=refs.get(m['beneficiaire_ref'].casefold())
  if not b or b['champs_a_completer']:inconnus.append('identite_a_completer')
  if b:
   bsource=next(a for a in tb['lignes'] if a['beneficiaire_ref'].casefold()==m['beneficiaire_ref'].casefold())
   if bsource['regime'] in REGIMES[2:]:inconnus.append('regime_particulier_a_qualifier')
  lignes.append({'ligne':i,'reference_source':m['reference_source'],'beneficiaire_ref':m['beneficiaire_ref'],'champs_a_completer':inconnus,'points_a_revoir':[CHAMPS[k] for k in inconnus]})
  key=(m['beneficiaire_ref'].casefold(),m['categorie'])
  groupes.setdefault(key,[]).append(m)
 regroupements=[{'beneficiaire_ref':refs[k[0]]['reference'] if k[0] in refs else '', 'categorie':k[1], 'montants':{champ:total(rows,champ) for champ in MONTANTS}} for k,rows in groupes.items()]
 montants={k:total(tm['lignes'],k,absence) for k in MONTANTS}
 if any(v is not None and Decimal(v)<0 for v in montants.values()):alertes.append('Un total documentaire net est négatif : revoir les corrections et leurs sources ; aucune correction fiscale automatique.')
 revue=bool(absence or (profil and p.get('absence')=='non' and tb['statut']==tm['statut']=='documente' and beneficiaires and lignes and not any(b['champs_a_completer'] for b in beneficiaires) and not any(l['champs_a_completer'] for l in lignes)))
 if not revue:alertes.append('Préparation à compléter ou à qualifier ; des totaux arithmétiques connus ne prouvent pas la complétude.')
 alertes.append('Modèle administratif151/annexes applicables non intégré : déclaration officielle et dépôt non validés.')
 return {'methode':'preparation_tiers_interne_v1','periode_source':periode,'exercice':dossier['exercice'],'montants':montants,'beneficiaires':beneficiaires,'lignes':lignes,'regroupements':regroupements,'revue_documentaire_declaree':revue,'absence_exhaustive_confirmee':absence,'reference_juridique':deepcopy(SOURCE),'alertes':alertes,'pret_a_deposer':False,'declaration_officielle':False,'ecritures_generees':False,'rapprochement_comptable_verifie':False}

def presentation(dossier):
 bloc=dossier['contenu'].get(BLOC) or {}
 vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
 vue['controle_tiers']=deepcopy(bloc.get('controle_tiers'))
 return vue

def conserver(db,user,preparation_id,data):
 return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,referentiel=catalogue,enrichir=lambda d,q:{'controle_tiers':calculer_controles(d,q),'note_conservee':NOTE})
