"""TP761 : bases et classes pédagogiques explicitement fournies, pas de montant dû."""
from uuid import uuid4
from tiers759_support import (application,application103,application102,application101,application100,application099,application098,application097,application093,application092,application091,application090,application089,application087,migration,client,ok,BASE,donnees_metier,R,creer as creer_fiscal,body as tiers_body,url as tiers_url,verifier as verifier_tiers)
BLOC='taxe_professionnelle_documentaire'
NORMAL='Établissement avec local — hors régime particulier, exonération et réduction'
def creer(api):return ok(api.post(tiers_url(v:=creer_fiscal(api)),json=tiers_body(v)),201)
def url(v):return BASE+f'/{v["id"]}/taxe-professionnelle'
def body(v):
 return {'cle':str(uuid4()),'empreinte_parent':v['empreinte_sha256'],'tables':[
  {'code':'TP-P','statut':'documente','justification':'Profil et millésime fictifs revus, aucun droit réel attesté','lignes':[{'nature':'Simulation pédagogique TP2026','annee_tp':'2026','periode_revue':'oui','exhaustivite':'oui','referentiel_revu':'oui','reference_source':'NOTE761'}]},
  {'code':'TP-E','statut':'documente','justification':'Bases et classes choisies uniquement pour vérifier le calcul, pas une qualification réelle','lignes':[
   {'nature':'Local fictif A','etablissement_ref':'E761-A','commune':'Casablanca fictif','adresse':'Adresse pédagogique A','activite':'Activité fictive A sans classement réel','classe':'C2','valeur_locative':'30000','base_revue':'oui','classe_revue':'oui','regime':NORMAL,'situation_janvier_revue':'oui','montant_avis':'6200','reference_avis':'AVIS761-A','avis_rattache':'oui','reference_source':'BASE-CLASSE761-A'},
   {'nature':'Local fictif B','etablissement_ref':'E761-B','commune':'Rabat fictif','adresse':'Adresse pédagogique B','activite':'Activité fictive B sans classement réel','classe':'C3','valeur_locative':'12000','base_revue':'oui','classe_revue':'oui','regime':NORMAL,'situation_janvier_revue':'oui','montant_avis':'1200','reference_avis':'AVIS761-B','avis_rattache':'oui','reference_source':'BASE-CLASSE761-B'}]}]}
def controles(v):return v['contenu'][BLOC]['controle_tp']
def verifier(v):
 c=controles(v);assert c['montants']=={'valeur_locative_totale':'42000.00','brut_arithmetique':'7200.00','brut_propose':'7200.00','avis_comparables':'7400.00','ecart_brut_avis':'-200.00'}
 assert c['revue_documentaire_declaree'] and c['montant_du_confirme'] is None and not c['pret_a_deposer'] and not c['imposition_confirmee'] and not c['paiement_confirme']
 assert c['etablissements'][0]['ecart_avis']=='-200.00' and c['etablissements'][1]['ecart_avis']=='0.00';verifier_tiers(v)
