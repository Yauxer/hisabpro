"""CSS externe2026 : base fiscale sourcée du dernier exercice clos, sans Journal."""
from copy import deepcopy
from decimal import Decimal,localcontext
import re
from services import balance_etic_tables_service as commun
from services.fiscalite_css_service import calculer_css

BLOC='css_documentaire'
REGIME='Société relevant de l’IS'
SOURCE={'titre':'CGI 2026, articles 267 à 273','pages_imprimees':'510-512',
 'editeur':'DGI, document republié par le CRI Casablanca-Settat',
 'notice_url':'https://casainvest.ma/fr/node/719',
 'url':'https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf',
 'sha256':'fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1'}
LIBELLES={'benefice_reference':'Bénéfice net fiscal de référence déclaré',
 'css_proposee':'CSS proposée selon qualifications déclarées',
 'css_declaree_contexte':'CSS déclarée dans le contexte fiscal conservé',
 'ecart_css_declaree':'Écart CSS proposée moins CSS déclarée'}
NOTE=('CSS externe de l’année2026 en MAD, calcul partagé avec le moteur existant, '
 'CGI2026 articles267 à273. CSS-N est un code interne. Le bénéfice net fiscal '
 'servant à l’IS du dernier exercice clos est explicitement déclaré et sourcé ; '
 'il n’est jamais remplacé par le résultat net comptable, le B12 N/N-1 ou le '
 'Journal de la société active. Le périmètre société IS, l’exercice de référence, '
 'la confirmation du dernier exercice clos et l’exonération permanente d’IS '
 'sont déclarés, jamais déduits d’un taux IS nul ou d’une exonération temporaire. '
 'Les taux sont proportionnels au bénéfice entier, non progressifs par tranches. '
 'Une case vide ou néant reste inconnue. Hors2026 ou qualification incomplète, '
 'aucun montant CSS proposé. La comparaison au contexte fiscal conservé signale '
 'un écart sans modifier la déclaration. Aucune date de clôture ou échéance '
 'n’est inventée ; calendrier de déclaration/paiement à qualifier séparément '
 'depuis la clôture source. CSS reste distincte de l’IS/CM et de ses crédits '
 'ou acomptes. Aucune écriture, liquidation, imputation ou paiement confirmé, '
 'aucun prêt à déposer. Les versions et contrôles conservés ne sont pas recalculés.')


def catalogue(dossier):
 bloc=dossier['contenu'].get(BLOC)
 if bloc:return deepcopy(bloc['catalogue'])
 return [{'code':'CSS-N','groupe':'Interne','titre':'CSS2026 sur dernier exercice clos déclaré',
  'colonnes_saisie':[
   {'cle':'nature','label':'Désignation de la qualification CSS','type':'text'},
   {'cle':'regime','label':'Périmètre CSS déclaré','type':'text'},
   {'cle':'exercice_reference','label':'Exercice fiscal de référence déclaré','type':'text'},
   {'cle':'benefice_reference','label':'Bénéfice net fiscal du dernier exercice clos','type':'number'},
   {'cle':'dernier_clos_confirme','label':'Source du dernier exercice clos confirmée','type':'text'},
   {'cle':'exoneration_permanente','label':'Exonération permanente d’IS justifiée','type':'text'}]}]


def normaliser(dossier,tables):
 ts=commun.normaliser(dossier,tables,referentiel=catalogue)
 if len(ts[0]['lignes'])>1:raise ValueError('Une seule qualification CSS par préparation est autorisée.')
 for r in ts[0]['lignes']:
  if not r['nature'] or not r['reference_source']:raise ValueError('Désignation et référence des justificatifs CSS requises, même pour une qualification partielle.')
  if r['regime'] not in ('',REGIME):raise ValueError('Ce calcul couvre uniquement le périmètre société IS déclaré.')
  for k in ('dernier_clos_confirme','exoneration_permanente'):
   if r[k] not in ('','oui','non'):raise ValueError('Qualification CSS : choisir oui ou non, ou laisser à qualifier.')
  y=r['exercice_reference'];exercice=dossier.get('exercice',dossier['contenu'].get('exercice'))
  if y and (not re.fullmatch('[0-9]{4}',y) or not 1900<=int(y)<=exercice):
   raise ValueError('Exercice de référence : année de quatre chiffres, au plus égale à l’année de la préparation.')
 return ts


def source_contexte(dossier):
 bloc=dossier['contenu'].get('contexte_fiscal_documentaire')
 if not bloc:return None
 return {'cle':bloc['cle'],'css_declaree':bloc['controle_contexte_fiscal']['montants']['css_declaree']}


def calculer_controles(dossier,demande):
 t=demande['tables'][0];r=t['lignes'][0] if t['lignes'] else {}
 exercice=dossier.get('exercice',dossier['contenu'].get('exercice'));couvert=type(exercice)is int and exercice==2026
 complet=t['statut']=='documente' and r.get('regime')==REGIME and bool(r.get('exercice_reference')) and r.get('benefice_reference') is not None and r.get('dernier_clos_confirme')=='oui' and r.get('exoneration_permanente') in ('oui','non')
 src=source_contexte(dossier);montants={k:None for k in LIBELLES};taux=None;alertes=[]
 with localcontext() as ctx:
  ctx.prec=60
  if r.get('benefice_reference') is not None:montants['benefice_reference']=Decimal(r['benefice_reference'])
  if src and src['css_declaree'] is not None:montants['css_declaree_contexte']=Decimal(src['css_declaree'])
  if couvert and complet:
   calcul=calculer_css(annee=2026,reference_forcee=r['benefice_reference'],exercice_reference=int(r['exercice_reference']),
    exoneration_permanente=r['exoneration_permanente']=='oui')
   taux=format(calcul['taux'],'.3f');montants['css_proposee']=calcul['montant_du']
  if not couvert:alertes.append('Référentiel vérifié pour2026 uniquement ; aucune CSS proposée pour cet exercice.')
  if not complet:alertes.append('Qualification CSS incomplète ou dernier exercice clos non confirmé ; aucun inconnu remplacé par zéro ou non.')
  if montants['css_proposee'] is not None and montants['css_declaree_contexte'] is not None:
   montants['ecart_css_declaree']=montants['css_proposee']-montants['css_declaree_contexte']
   if montants['ecart_css_declaree']!=0:alertes.append('La CSS proposée diffère de la CSS déclarée dans le contexte conservé ; revoir les sources, aucune déclaration corrigée automatiquement.')
  return {'methode':'moteur_css_partage_dernier_clos_declare_2026_v1','annee_css':exercice,
   'exercice_reference_declare':int(r['exercice_reference']) if r.get('exercice_reference') else None,
   'qualification_complete_declaree':bool(complet),'exercice_couvert':couvert,
   'montants':{k:None if v is None else format(v,'.2f') for k,v in montants.items()},'taux_proportionnel':taux,
   'source_contexte_fiscal':src,'reference_juridique':deepcopy(SOURCE),'alertes':alertes,
   'date_echeance':None,'solde_is':None,'liquidation_confirmee':False,'paiement_confirme':False,'pret_a_deposer':False}


def presentation(dossier):
 bloc=dossier['contenu'].get(BLOC) or {}
 vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
 vue['controle_css']=deepcopy(bloc.get('controle_css'));c=vue['controle_css']
 vue['source_contexte_modifiee']=bool(c and (c['source_contexte_fiscal'] or {}).get('cle')!=(source_contexte(dossier) or {}).get('cle'))
 if vue['source_contexte_modifiee']:vue['alertes'].append('Le contexte fiscal a changé : comparaison CSS conservée pour mémoire. Relire les sources et conserver une nouvelle qualification CSS ; ancien contrôle inchangé.')
 return vue


def conserver(db,user,preparation_id,data):
 return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,referentiel=catalogue,
  enrichir=lambda d,q:{'controle_css':calculer_controles(d,q),'note_conservee':NOTE})
