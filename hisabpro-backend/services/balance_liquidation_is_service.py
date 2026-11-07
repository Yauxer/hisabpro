"""Proposition IS/CM externe sur contrôles figés et sources qualifiées cohérentes."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext

from services import balance_etic_tables_service as commun
from services.balance_acomptes_is_service import SOURCE as SOURCE_CGI
from services.fiscalite_acomptes_service import calculer_liquidation

BLOC = 'liquidation_is_documentaire'
SOURCE = {**SOURCE_CGI, 'titre': 'CGI2026, articles144, 157, 159, 170 ; conditions déclarées et sources conservées',
          'pages_imprimees': '268-270, 294-296, 321-323'}
LIBELLES = {
    'is_theorique': 'IS théorique au taux B12 déclaré', 'cm_proposee': 'CM proposée selon qualification conservée',
    'impot_avant_imputations': 'Maximum IS/CM proposé avant imputations',
    'credits_disponibles': 'Crédits qualifiés disponibles après utilisations antérieures',
    'acomptes_imputables': 'Acomptes justifiés proposés',
    'excedent_anterieur_restant': 'Excédent antérieur restant après acomptes',
    'excedent_anterieur_annuel_demande': 'Excédent antérieur réservé à cette simulation annuelle',
    'credits_appliques': 'Crédits et excédent annuel appliqués dans la simulation',
    'acomptes_appliques': 'Acomptes appliqués dans la simulation',
    'solde_is_propose': 'Solde IS/CM proposé à payer', 'excedent_arithmetique': 'Excédent arithmétique de la simulation',
    'css_separee': 'CSS proposée séparément dans sa qualification conservée',
}
NOTE = (
    'Proposition externe2026 sur B12, CM, crédits et acomptes conservés, qualifiés '
    'et cohérents entre eux. Aucun Journal ou module fiscal actif n’est consulté. '
    'Le taux/régime IS et les déficits B12 restent à vérifier explicitement. '
    'Le crédit déjà utilisé est compté une fois dans les acomptes et retiré du '
    'disponible crédits. Un excédent antérieur restant n’est imputé annuellement '
    'que pour un montant explicitement demandé, qualifié et disponible. '
    'Ordre de simulation à examiner et justifier : PPRF/Sukuk, tiers/location, '
    'excédent antérieur réservé à ce solde, puis acomptes. Il s’agit d’une '
    'répartition de calcul à vérifier dans le dossier, sans affirmer un ordre '
    'légal universel ou un droit à restitution/report de l’excédent arithmétique. '
    'CSS est affichée séparément depuis son contrôle, jamais compensée avec '
    'l’IS/CM ou ses crédits. Une donnée requise inconnue ou une liaison entre '
    'contrôles devenue ancienne bloque la proposition, sans fabriquer un zéro. '
    'Conserver fige une nouvelle version ; aucune liquidation officielle, '
    'imputation effective, écriture, paiement ou dépôt confirmé.'
)


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    return [{'code': 'LIQ-N', 'groupe': 'Interne', 'titre': 'Revue de la proposition annuelle IS/CM',
        'colonnes_saisie': [{'cle': k, 'label': label, 'type': typ} for k, label, typ in [
            ('nature', 'Désignation de la revue fiscale', 'text'),
            ('b12_verifie', 'Taux, régime et déficits B12 vérifiés', 'text'),
            ('cm_verifiee', 'Qualification CM vérifiée', 'text'),
            ('exhaustivite_verifiee', 'Crédits et acomptes exhaustifs vérifiés', 'text'),
            ('excedent_verifie', 'Solde d’excédent antérieur vérifié', 'text'),
            ('ordre_examine', 'Ordre de simulation examiné et justifié', 'text'),
            ('excedent_annuel', 'Excédent antérieur à utiliser dans cette simulation annuelle', 'number')]]}]


def normaliser(dossier, tables):
    ts = commun.normaliser(dossier, tables, referentiel=catalogue)
    if len(ts[0]['lignes']) > 1:
        raise ValueError('Une seule revue de liquidation par préparation.')
    for r in ts[0]['lignes']:
        if not r['nature'] or not r['reference_source']:
            raise ValueError('Désignation et références des contrôles revus requises, même pour une revue partielle.')
        for k in ('b12_verifie', 'cm_verifiee', 'exhaustivite_verifiee', 'excedent_verifie', 'ordre_examine'):
            if r[k] not in ('', 'oui', 'non'):
                raise ValueError('Revue de liquidation : oui, non ou champ vide.')
    return ts


def sources(dossier):
    contenu = dossier['contenu']; resultat = {}
    for k, bloc, champ in [('b12', 'passage_fiscal_documentaire', 'controle_passage_fiscal'),
                           ('cm', 'cotisation_minimale_documentaire', 'controle_cm'),
                           ('credits', 'credits_is_documentaires', 'controle_credits'),
                           ('acomptes', 'acomptes_is_documentaires', 'controle_acomptes'),
                           ('css', 'css_documentaire', 'controle_css')]:
        b = contenu.get(bloc)
        resultat[k] = {'cle': b['cle'], 'controle': deepcopy(b[champ])} if b else None
    return resultat


def argent(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        d = Decimal(str(value))
        return d if d.is_finite() and d >= 0 and d == d.quantize(Decimal('.01')) else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def calculer_controles(dossier, demande):
    t = demande['tables'][0]; r = t['lignes'][0] if t['lignes'] else {}; src = sources(dossier)
    vals = {k: None for k in LIBELLES}; alertes = []; detail = None
    controles = {k: v['controle'] if v else {} for k, v in src.items()}; b, cm, cr, ap, css = (controles[k] for k in ('b12', 'cm', 'credits', 'acomptes', 'css'))
    def m(c, k):
        return argent(c.get('montants', {}).get(k))
    with localcontext() as ctx:
        ctx.prec = 60
        vals.update(is_theorique=m(b, 'is_theorique_taux_declare'), cm_proposee=m(cm, 'cm_exigible'),
            impot_avant_imputations=m(cm, 'impot_avant_imputations_propose'), credits_disponibles=m(cr, 'credits_proposes'),
            acomptes_imputables=m(ap, 'acomptes_proposes'), excedent_anterieur_restant=m(ap, 'excedent_anterieur_restant'),
            excedent_anterieur_annuel_demande=argent(r.get('excedent_annuel')))
        if css.get('qualification_complete_declaree') and css.get('exercice_couvert'):
            vals['css_separee'] = m(css, 'css_proposee')
        direct, restant = vals['excedent_anterieur_annuel_demande'], vals['excedent_anterieur_restant']
        if direct is not None and restant is not None and direct > restant:
            raise ValueError('L’excédent demandé pour le solde annuel dépasse le restant conservé après acomptes.')
        liens = (all(src[k] for k in ('b12', 'cm', 'credits', 'acomptes'))
            and (cm.get('source_b12') or {}).get('cle') == src['b12']['cle']
            and (ap.get('source_credits') or {}).get('cle') == src['credits']['cle'])
        revu = t['statut'] == 'documente' and all(r.get(k) == 'oui' for k in (
            'b12_verifie', 'cm_verifiee', 'exhaustivite_verifiee', 'excedent_verifie', 'ordre_examine'))
        complets = (dossier['exercice'] == 2026 and b.get('disponible') and cm.get('qualification_complete_declaree')
            and cm.get('exercice_couvert') and cr.get('qualification_complete_declaree') and cr.get('exercice_couvert')
            and ap.get('qualification_complete_declaree') and all(vals[k] is not None for k in (
                'is_theorique', 'cm_proposee', 'impot_avant_imputations', 'credits_disponibles', 'acomptes_imputables',
                'excedent_anterieur_restant', 'excedent_anterieur_annuel_demande')))
        coherents = False; par_type = {'pprf': Decimal('0.00'), 'retenue_tiers': Decimal('0.00'), 'autre': direct}
        if complets and liens:
            groupes = {'PPRF — CGI159': 'pprf', 'Sukuk — CGI159': 'pprf',
                       'Rémunérations de tiers — CGI157': 'retenue_tiers', 'Location — CGI157': 'retenue_tiers'}
            credit_ok = True
            for ligne in cr['lignes']:
                if ligne['statut'] == 'exclu_declare':
                    continue
                disponible = argent(ligne['disponible_arithmetique']); typ = groupes.get(ligne['type_credit'])
                if ligne['statut'] != 'qualifie_declare' or disponible is None or typ is None:
                    credit_ok = False
                else:
                    par_type[typ] += disponible
            apm = ap['montants']; initial = argent(apm.get('excedent_anterieur_disponible')); apvals = [argent(apm[k]) for k in ('versements_declares', 'excedent_anterieur_impute', 'retenues_affectees')]
            ant = dossier['contenu']['acomptes_is_documentaires']['tables'][0]['lignes'][0]
            direct_ok = direct == 0 or (ant['excedent_qualifie'] == 'oui' and bool(ant['origine_excedent']) and 2015 <= int(ant['origine_excedent']) <= dossier['exercice'])
            coherents = (credit_ok and direct_ok and all(v is not None for v in apvals)
                and initial is not None and initial - apvals[1] == restant
                and sum(apvals) == vals['acomptes_imputables'] and par_type['pprf'] + par_type['retenue_tiers'] == vals['credits_disponibles']
                and max(vals['is_theorique'], vals['cm_proposee']) == vals['impot_avant_imputations']
                and m(cm, 'is_theorique_b12') == vals['is_theorique'])
            if revu and coherents:
                detail = calculer_liquidation(impot_du_avant_acomptes=vals['impot_avant_imputations'],
                    situation_acomptes={'total_verse': apvals[0], 'credit_n_1_impute': apvals[1], 'credit_ras_impute': apvals[2]},
                    credits_is={'par_type': par_type})
                vals.update(credits_appliques=detail['credits_is_appliques'], acomptes_appliques=detail['acomptes_appliques_liquidation'],
                    solde_is_propose=detail['solde_a_payer'], excedent_arithmetique=detail['excedent_total'])
        possible = bool(complets and liens and revu and coherents)
        for nom, controle in controles.items():
            alertes.extend(nom.upper() + ' — contrôle source conservé : ' + a for a in controle.get('alertes', []))
        if not possible:
            alertes.append('Proposition indisponible : vérifier les sources qualifiées, leurs liaisons, la cohérence des montants et la revue fiscale explicite. Aucun inconnu remplacé par zéro.')
        if not liens:
            alertes.append('B12/CM ou crédits/acomptes absents ou désynchronisés ; conserver les contrôles dépendants sur les sources à jour avant une nouvelle proposition.')
        if vals['css_separee'] is None:
            alertes.append('CSS distincte non qualifiée : aucun zéro ou total global IS+CSS fabriqué.')
        def exact(v):
            if isinstance(v, Decimal):
                return format(v, '.2f')
            if isinstance(v, dict):
                return {k: exact(x) for k, x in v.items()}
            return v
        return {'methode': 'simulation_is_cm_moteur_partage_sources_figees_2026_v1', 'exercice': dossier['exercice'],
            'proposition_disponible': possible, 'montants': exact(vals), 'detail_simulation': exact(detail),
            'sources_conservees': src, 'reference_juridique': deepcopy(SOURCE), 'alertes': alertes,
            'total_global_is_css': None, 'liquidation_confirmee': False, 'paiement_confirme': False, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC) or {}
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue, note=bloc.get('note_conservee', NOTE))
    c = vue['controle_liquidation'] = deepcopy(bloc.get('controle_liquidation')); actuel = sources(dossier)
    vue['sources_is_modifiees'] = bool(c and any((c['sources_conservees'][k] or {}).get('cle') != (actuel[k] or {}).get('cle') for k in ('b12', 'cm', 'credits', 'acomptes')))
    vue['source_css_modifiee'] = bool(c and (c['sources_conservees']['css'] or {}).get('cle') != (actuel['css'] or {}).get('cle'))
    if vue['sources_is_modifiees']:
        vue['alertes'].append('Les sources IS/CM ont changé : proposition conservée pour mémoire ; relire, actualiser les contrôles dépendants puis conserver une nouvelle proposition. Ancien calcul inchangé.')
    if vue['source_css_modifiee']:
        vue['alertes'].append('La qualification CSS a changé : montant CSS conservé pour mémoire, distinct du solde IS/CM ; aucune actualisation historique automatique.')
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC, normalisation=normaliser,
        referentiel=catalogue, enrichir=lambda d, q: {'controle_liquidation': calculer_controles(d, q), 'note_conservee': NOTE})
