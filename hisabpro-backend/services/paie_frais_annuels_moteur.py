"""Cumuls des périodes choisies et frais annuels59-I-A, sans mensualisation."""
from copy import deepcopy
from decimal import Decimal as D
from services.paie_campagnes_service import empreinte
from services.paie_social_moteur import anomalie

REFERENTIEL={'version_interne':'FRAIS-ANNUELS-MA-2026-59IA-913','annee':2026,
    'seuil_revenu_brut_annuel_imposable':'78000.00','taux_jusqua_seuil':'35','taux_au_dessus':'25','plafond_annuel':'35000.00',
    'reference':'CGI2026, article59-I-A et base hors avantages, pages98–99',
    'url':'https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf',
    'document_sha256':'fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1','date_consultation':'2026-10-28',
    'limite':'Cadre général59-I-A confirmé seulement ; catégoriesB/C, mensualisation, versements et net non traités.'}
CHAMPS=['brut_imposable','base_frais_professionnels','cotisations_salariales_deductibles','cotisations_salariales_non_deductibles','revenu_avant_frais_autres_deductions']


def calculer(data,sources):
    erreurs=[];periodes={x['periode'] for x in sources};attendu={f'{data.annee}-{m:02d}-01' for m in range(1,13)}
    def somme(k):return format(sum((D(x['employe'][k]) for x in sources),D(0)),'.2f') if all(x['employe'].get(k) is not None for x in sources) else None
    cumuls={k:somme(k) for k in CHAMPS}
    if periodes!=attendu:erreurs.append(anomalie('ANNEE_INCOMPLETE','Douze périodes mensuelles distinctes requises ; aucun mois multiplié ni période manquante remplacée par zéro.'))
    if any(x['employe']['anomalies'] for x in sources) or any(v is None for v in cumuls.values()):
        erreurs.append(anomalie('BASES_INCOMPLETES','Certaines préparations sources comportent des anomalies ou des bases inconnues.'))
    if not data.cadre_frais_general_confirme:erreurs.append(anomalie('CADRE_FRAIS_NON_CONFIRME','Confirmer le cadre général59-I-A ; ne pas assimiler les catégoriesB/C à ce cadre.'))
    if not data.correspondance_revenus_annee_confirmee or not data.reference_controle_annuel:
        erreurs.append(anomalie('REVENUS_ANNUELS_NON_CONFIRMES','Confirmer que les périodes choisies correspondent au revenu annuel à contrôler ; une période ne prouve pas une date de paiement.'))
    taux=None;frais=None;avant=None;rni=None
    if not erreurs:
        brut=D(cumuls['brut_imposable']);base=D(cumuls['base_frais_professionnels']);ded=D(cumuls['cotisations_salariales_deductibles'])
        if base>brut or ded>brut:erreurs.append(anomalie('BASES_ANNUELLES_INCOHERENTES','Base des frais ou cotisations déductibles supérieures au revenu imposable.'))
        else:
            taux=REFERENTIEL['taux_jusqua_seuil'] if brut<=D(REFERENTIEL['seuil_revenu_brut_annuel_imposable']) else REFERENTIEL['taux_au_dessus']
            frais=min(base*D(taux)/D(100),D(REFERENTIEL['plafond_annuel']));avant=brut-ded-frais
            if avant<0:erreurs.append(anomalie('DEDUCTIONS_SUPERIEURES_REVENU','Déductions supérieures au revenu ; aucun déficit salarial ni zéro de secours inventé.'));avant=None
    autres=data.autres_deductions_annuelles
    if autres is None or not data.autres_deductions_confirmees or not data.reference_autres_deductions:
        erreurs.append(anomalie('AUTRES_DEDUCTIONS_INCONNUES','Autres déductions annuelles à établir et confirmer avec référence, y compris une déclaration de zéro.'))
    elif avant is not None:
        if autres>avant:erreurs.append(anomalie('AUTRES_DEDUCTIONS_EXCESSIVES','Autres déductions supérieures au revenu disponible ; aucune correction silencieuse.'))
        else:rni=avant-autres
    exact=lambda v:None if v is None else format(v,'.4f')
    return {'annee':data.annee,'mois_couverts':sorted(periodes),'nombre_mois':len(periodes),'cumuls':cumuls,
        'taux_frais_pourcent':taux,'frais_professionnels_annuels_arithmetiques':exact(frais),'revenu_apres_frais_avant_autres_deductions':exact(avant),
        'rni_annuel_arithmetique_avant_arrondis':exact(rni),'autres_deductions_annuelles':None if autres is None else format(autres,'.2f'),
        'referentiel':deepcopy(REFERENTIEL),'referentiel_sha256':empreinte(REFERENTIEL),'anomalies':erreurs,
        'ir':None,'retenue_mensuelle':None,'net_a_payer':None,'versement':None,'paie_definitive_autorisee':False}
