"""RNI déclaré et équivalence mathématique annuelle/12 ; aucune liquidation."""
from copy import deepcopy
from calendar import monthrange
from datetime import date
from decimal import Decimal,localcontext,ROUND_HALF_UP
from fractions import Fraction
from services.paie_ir_annuel_moteur import REFERENTIEL as ANNUEL,ventiler
from services.paie_campagnes_service import empreinte

REFERENTIEL={'version_interne':'RNI-MENSUEL-EQUIVALENCE-2026-921','annee':2026,
 'methode':'Equivalence mathématique : barème annuel appliqué à12fois leRNI du mois,puis résultat divisé par12. Ce multiplicateur est une transformation de barème,pas une prévision de revenu annuel.',
 'qualification':'CONTROLE_PEDAGOGIQUE_NON_LIQUIDE','source_bareme_annuel':deepcopy(ANNUEL),
 'arrondis':'Aucun arrondi fiscal de base ou de retenue appliqué. Fractions exactes conservées ;affichage4décimales ROUND_HALF_UP seulement.',
 'limite':'Frais etautres déductions déclarés avec références ;aucun forfait mensuel automatique. Méthode périodique etarrondis réglementaires à qualifier avant retenue,net oupaie définitive.'}

def fraction(v):return {'numerateur':str(v.numerator),'denominateur':str(v.denominator)}
def afficher(v):
    with localcontext() as c:
        c.prec=64;return format((Decimal(v.numerator)/Decimal(v.denominator)).quantize(Decimal('.0001'),rounding=ROUND_HALF_UP),'.4f')

def calculer(e,periode,data,variables):
    debut=date.fromisoformat(periode);fin=debut.replace(day=monthrange(debut.year,debut.month)[1]);erreurs=[]
    r={'periode':periode,'employe_id':e['employe_id'],'nom':e['nom'],'matricule':e['matricule'],
       'mode':'CONTROLE_MENSUEL_PREPARATOIRE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT','paie_definitive_autorisee':False,
       'declaration':data.model_dump(mode='json',exclude={'cle_idempotence','motif'}),'referentiel':deepcopy(REFERENTIEL),'referentiel_sha256':empreinte(REFERENTIEL),
       'bases_sources':{k:e.get(k) for k in ['brut_imposable','base_frais_professionnels','cotisations_salariales_deductibles','cotisations_salariales_non_deductibles']},
       'rni_arithmetique':None,'base_annuelle_equivalente':None,'ir_avant_reduction_arithmetique':None,'reduction_appliquee_arithmetique':None,
       'ir_mensuel_arithmetique':None,'fractions_exactes':{},'tranches_annuelles_de_reference':[],
       'retenue_a_operer':None,'montant_a_declarer':None,'versement':None,'net_a_payer':None,'anomalies':erreurs,
       'avertissement':'RNI sur déductions déclarées et équivalence mathématique annuelle/12,avant liquidation. Aucun frais mensuel ou arrondi réglementaire supposé,aucune retenue à opérer,déclaration,versement,net oupaie définitive. Les références déclarées ne sont pas une validation juridique.'}
    def signaler(k,t):erreurs.append({'code':k,'message':t})
    if debut.year!=2026 or debut.day!=1:signaler('PERIODE_HORS_CADRE','Seul un mois complet2026 est couvert par ce contrôle préparatoire.')
    if e.get('anomalies') or any(e.get(k) is None for k in ['brut_imposable','base_frais_professionnels','cotisations_salariales_deductibles']):signaler('BASES_INCOMPLETES','Compléter les bases fiscales sources avant de constituer leRNI.')
    if not data.cadre_mensuel_general_confirme or not data.reference_controle_mensuel:signaler('CADRE_MENSUEL_NON_CONFIRME','Confirmer le mois complet et le cadre mensuel courant,sans cas particulier ou rappel non traité.')
    if not data.deductions_confirmees or data.frais_professionnels_declares is None or not data.reference_frais or data.autres_deductions_declarees is None or not data.reference_autres_deductions:signaler('DEDUCTIONS_A_COMPLETER','Établir et référencer les frais et autres déductions du mois,y compris une déclaration de zéro ;aucun forfait ou zéro implicite.')
    if data.date_versement_declaree is not None and data.date_versement_declaree.year!=2026:signaler('VERSEMENT_AUTRE_ANNEE','Versement déclaré sur une autre année : méthode et millésime à analyser séparément.')
    for v in variables:
        meta=v.get('rattachement_revenus') or {}
        if v.get('periodicite')!='mensuelle' or meta.get('reference_debut') is not None and (meta['reference_debut']!=debut.isoformat() or meta.get('reference_fin')!=fin.isoformat()):
            signaler('RATTACHEMENT_SPECIFIQUE','Variable #'+str(v['id'])+' :prime/rappel ou période de référence distincte,à régulariser séparément ;aucune taxation intégrale par défaut sur le mois.')
        if meta.get('versement_date') and data.date_versement_declaree and meta['versement_date']!=data.date_versement_declaree.isoformat():signaler('VERSEMENTS_DISTINCTS','Des dates de versement déclarées diffèrent ; analyser les paiements séparément.')
        if meta.get('versement_date') and date.fromisoformat(meta['versement_date']).year!=debut.year:signaler('VERSEMENT_SOURCE_AUTRE_ANNEE','Une variable mentionne un versement sur une autre année ; qualification du millésime et du rattachement nécessaire.')
    if not erreurs:
        brut=Decimal(e['brut_imposable']);ded=Decimal(e['cotisations_salariales_deductibles']);fp=data.frais_professionnels_declares;autres=data.autres_deductions_declarees
        if fp>Decimal(e['base_frais_professionnels']):signaler('FRAIS_SUPERIEURS_BASE','Frais déclarés supérieurs à leur base source ;aucune correction silencieuse.')
        elif brut-ded-fp-autres<0:signaler('DEDUCTIONS_EXCESSIVES','Déductions supérieures au revenu disponible ;aucun zéro ou déficit salarial de secours.')
        else:
            rni=brut-ded-fp-autres;r['rni_arithmetique']=format(rni,'.2f');equivalent=rni*12;r['base_annuelle_equivalente']=format(equivalent,'.2f')
            lignes,impot=ventiler(equivalent);total=Fraction(impot)/12
            r['tranches_annuelles_de_reference']=lignes;r['ir_avant_reduction_arithmetique']=afficher(total);r['fractions_exactes']['ir_avant_reduction']=fraction(total)
    if data.personnes_charge is None or not data.eligibilite_famille_confirmee or not data.reference_famille:signaler('FAMILLE_A_COMPLETER','Nombre et éligibilité des personnes fiscalement à charge à confirmer pour le mois ;ne pas les déduire de l’état civil.')
    elif r['ir_avant_reduction_arithmetique'] is not None:
        reduction=min(total,Fraction(min(Decimal(data.personnes_charge)*Decimal(ANNUEL['reduction_personne_annuelle']),Decimal(ANNUEL['plafond_reduction_annuelle'])))/12)
        r['reduction_appliquee_arithmetique']=afficher(reduction);r['ir_mensuel_arithmetique']=afficher(total-reduction)
        r['fractions_exactes'].update(reduction_appliquee=fraction(reduction),ir_apres_reduction=fraction(total-reduction))
    return r
