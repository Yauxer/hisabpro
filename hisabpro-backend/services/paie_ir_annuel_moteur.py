"""Barème général annuel2026, distinct de la liquidation et des arrondis déclaratifs.

Sources primaires et accès effectivement obtenus : voir SOURCES_IR_ANNUEL_901.md.
Le RNI et l'éligibilité sont déclarés ; aucune assiette, déduction ou mensualisation
n'est inventée. Les résultats exacts à quatre décimales ne sont pas un impôt exigible.
"""
from decimal import Decimal,ROUND_CEILING
from copy import deepcopy
from services.paie_campagnes_service import empreinte

D=Decimal
REFERENTIEL={
 'version_interne':'IR-GENERAL-ANNUEL-2026-911', 'annee':2026,
 'date_effet':'2026-01-01','date_fin':'2026-12-31','date_consultation':'2026-10-28',
 'tranches':[{'borne':'40000.00','taux_pourcent':'0'}, {'borne':'60000.00','taux_pourcent':'10'},
             {'borne':'80000.00','taux_pourcent':'20'}, {'borne':'100000.00','taux_pourcent':'30'},
             {'borne':'180000.00','taux_pourcent':'34'}, {'borne':None,'taux_pourcent':'37'}],
 'reduction_personne_annuelle':'600.00','plafond_reduction_annuelle':'3600.00',
 'sources':[{'titre':'CGI2026, article73-I et article74','url':'https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf','acces':'Extraits indexés officiels, pages119/125 ; ouverture directe en timeout.'},
            {'titre':'LF50-25, BO7465bis du16/12/2025, article7','url':'https://www.sgg.gov.ma/BO/FR/2873/2025/BO_7465-bis_Fr.pdf','acces':'PDF ouvert ; modification article74 page24 et date d’effet page33 lues.'}],
 'arrondi_base_annuelle':{'version_interne':'IR-BASE-ANNUELLE-2026-167-911','unite':'10.00','sens':'SUPERIEUR',
    'reference':'CGI2026, article167, page imprimée317','date_consultation':'2026-10-28',
    'url':'https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf',
    'document_sha256':'fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1'},
 'limite':'Barème général annuel, réduction familiale et comparaison après arrondi de la base annuelle déclarée. Applicabilité et éligibilité à confirmer. Aucun frais, retenue mensuelle, imputation ou versement déterminé.'}


def ventiler(revenu):
    lignes=[];borne=D(0);total=D(0)
    for t in REFERENTIEL['tranches']:
        maximum=D(t['borne']) if t['borne'] is not None else revenu
        base=max(D(0),min(revenu,maximum)-borne);impot=base*D(t['taux_pourcent'])/D(100);total+=impot
        lignes.append({'de':format(borne,'.2f'),'a':t['borne'],'taux_pourcent':t['taux_pourcent'],'base':format(base,'.2f'),'impot_arithmetique':format(impot,'.4f')})
        if t['borne'] is not None:borne=maximum
    return lignes,total


def calculer(data):
    r={'mode':'CONTROLE_IR_ANNUEL_NON_VALIDE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT','paie_definitive_autorisee':False,
       'annee':data.annee,'declaration':data.model_dump(mode='json',exclude={'cle_idempotence','motif'}),
       'referentiel':deepcopy(REFERENTIEL),'referentiel_sha256':empreinte(REFERENTIEL),'tranches':[],
       'ir_avant_reduction':None,'reduction_theorique':None,'reduction_appliquee':None,'ir_annuel_arithmetique':None,
       'controle_arrondi_base':{'base_arrondie':None,'ir_avant_reduction':None,'reduction_appliquee':None,'ir_apres_reduction':None,'ecart_sans_arrondi':None,'tranches':[],'versement':None},
       'ir_a_declarer':None,'retenue_mensuelle':None,'net_a_payer':None,'anomalies':[],
       'avertissement':'Contrôle annuel comparant le calcul exact et la base annuelle arrondie. Le RNI est déclaré après déductions qualifiées séparément. Imputations et versement non déterminés ; aucun calcul mensuel, net, bulletin ou validation de paie.'}
    def signaler(code,message):r['anomalies'].append({'code':code,'message':message})
    if data.annee!=REFERENTIEL['annee']:raise ValueError('Aucun référentiel qualifié pour cette année ; aucun repli vers2026.')
    if data.revenu_net_imposable_annuel is None:signaler('RNI_INCONNU','Revenu net imposable annuel inconnu ; aucun salaire ou brut mensuel de substitution.')
    if not data.cadre_general_confirme or not data.reference_rni:signaler('RNI_NON_CONFIRME','Confirmer le cadre général et la référence du revenu net imposable annuel.')
    if not r['anomalies']:
        r['tranches'],total=ventiler(data.revenu_net_imposable_annuel)
        r['ir_avant_reduction']=format(total,'.4f')
    if data.personnes_charge is None or not data.eligibilite_famille_confirmee or not data.reference_famille:
        signaler('FAMILLE_NON_CONFIRMEE','Nombre de personnes fiscalement éligibles et contrôle à confirmer ; ne pas le déduire de l’état civil.')
    else:r['reduction_theorique']=format(min(D(data.personnes_charge)*D(REFERENTIEL['reduction_personne_annuelle']),D(REFERENTIEL['plafond_reduction_annuelle'])),'.2f')
    if r['ir_avant_reduction'] is not None and r['reduction_theorique'] is not None:
        reduction=min(D(r['ir_avant_reduction']),D(r['reduction_theorique']))
        r['reduction_appliquee']=format(reduction,'.4f');r['ir_annuel_arithmetique']=format(D(r['ir_avant_reduction'])-reduction,'.4f')
    if r['ir_avant_reduction'] is not None:
        unite=D(REFERENTIEL['arrondi_base_annuelle']['unite'])
        base=(data.revenu_net_imposable_annuel/unite).to_integral_value(rounding=ROUND_CEILING)*unite
        lignes,total=ventiler(base);c=r['controle_arrondi_base']
        c.update(base_arrondie=format(base,'.2f'),ir_avant_reduction=format(total,'.4f'),tranches=lignes)
        if r['reduction_theorique'] is not None:
            reduction=min(total,D(r['reduction_theorique']));apres=total-reduction
            c.update(reduction_appliquee=format(reduction,'.4f'),ir_apres_reduction=format(apres,'.4f'),ecart_sans_arrondi=format(apres-D(r['ir_annuel_arithmetique']),'.4f'))
    return r
