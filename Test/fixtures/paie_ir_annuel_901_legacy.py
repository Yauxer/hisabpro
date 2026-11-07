"""Barème général annuel2026, distinct de la liquidation et des arrondis déclaratifs.

Sources primaires et accès effectivement obtenus : voir SOURCES_IR_ANNUEL_901.md.
Le RNI et l'éligibilité sont déclarés ; aucune assiette, déduction ou mensualisation
n'est inventée. Les résultats exacts à quatre décimales ne sont pas un impôt exigible.
"""
from decimal import Decimal
from copy import deepcopy
from services.paie_campagnes_service import empreinte

D=Decimal
REFERENTIEL={
 'version_interne':'IR-GENERAL-ANNUEL-2026-901', 'annee':2026,
 'date_effet':'2026-01-01','date_fin':'2026-12-31','date_consultation':'2026-10-28',
 'tranches':[{'borne':'40000.00','taux_pourcent':'0'}, {'borne':'60000.00','taux_pourcent':'10'},
             {'borne':'80000.00','taux_pourcent':'20'}, {'borne':'100000.00','taux_pourcent':'30'},
             {'borne':'180000.00','taux_pourcent':'34'}, {'borne':None,'taux_pourcent':'37'}],
 'reduction_personne_annuelle':'600.00','plafond_reduction_annuelle':'3600.00',
 'sources':[{'titre':'CGI2026, article73-I et article74','url':'https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf','acces':'Extraits indexés officiels, pages119/125 ; ouverture directe en timeout.'},
            {'titre':'LF50-25, BO7465bis du16/12/2025, article7','url':'https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7465-bis_Fr.pdf','acces':'PDF ouvert ; modification article74 page24 et date d’effet page33 lues.'}],
 'limite':'Barème général annuel et réduction familiale seulement ; applicabilité et éligibilité déclarées. Aucun taux spécifique, frais professionnels, assiette automatique, retenue mensuelle ou arrondi de liquidation.'}


def calculer(data):
    r={'mode':'CONTROLE_IR_ANNUEL_NON_VALIDE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT','paie_definitive_autorisee':False,
       'annee':data.annee,'declaration':data.model_dump(mode='json',exclude={'cle_idempotence','motif'}),
       'referentiel':deepcopy(REFERENTIEL),'referentiel_sha256':empreinte(REFERENTIEL),'tranches':[],
       'ir_avant_reduction':None,'reduction_theorique':None,'reduction_appliquee':None,'ir_annuel_arithmetique':None,
       'ir_a_declarer':None,'retenue_mensuelle':None,'net_a_payer':None,'anomalies':[],
       'avertissement':'Contrôle annuel avant arrondis et obligations déclaratives. Le RNI est déclaré après déductions qualifiées séparément. Aucun calcul mensuel, net, bulletin ou validation de paie.'}
    def signaler(code,message):r['anomalies'].append({'code':code,'message':message})
    if data.annee!=REFERENTIEL['annee']:raise ValueError('Aucun référentiel qualifié pour cette année ; aucun repli vers2026.')
    if data.revenu_net_imposable_annuel is None:signaler('RNI_INCONNU','Revenu net imposable annuel inconnu ; aucun salaire ou brut mensuel de substitution.')
    if not data.cadre_general_confirme or not data.reference_rni:signaler('RNI_NON_CONFIRME','Confirmer le cadre général et la référence du revenu net imposable annuel.')
    if not r['anomalies']:
        revenu=data.revenu_net_imposable_annuel;borne=D(0);total=D(0)
        for t in REFERENTIEL['tranches']:
            maximum=D(t['borne']) if t['borne'] is not None else revenu
            base=max(D(0),min(revenu,maximum)-borne);impot=base*D(t['taux_pourcent'])/D(100);total+=impot
            r['tranches'].append({'de':format(borne,'.2f'),'a':t['borne'],'taux_pourcent':t['taux_pourcent'],'base':format(base,'.2f'),'impot_arithmetique':format(impot,'.4f')})
            if t['borne'] is not None:borne=maximum
        r['ir_avant_reduction']=format(total,'.4f')
    if data.personnes_charge is None or not data.eligibilite_famille_confirmee or not data.reference_famille:
        signaler('FAMILLE_NON_CONFIRMEE','Nombre de personnes fiscalement éligibles et contrôle à confirmer ; ne pas le déduire de l’état civil.')
    else:r['reduction_theorique']=format(min(D(data.personnes_charge)*D(REFERENTIEL['reduction_personne_annuelle']),D(REFERENTIEL['plafond_reduction_annuelle'])),'.2f')
    if r['ir_avant_reduction'] is not None and r['reduction_theorique'] is not None:
        reduction=min(D(r['ir_avant_reduction']),D(r['reduction_theorique']))
        r['reduction_appliquee']=format(reduction,'.4f');r['ir_annuel_arithmetique']=format(D(r['ir_avant_reduction'])-reduction,'.4f')
    return r
