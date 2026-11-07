"""Crédits IS externes : justificatifs qualifiés, sans imputation effective."""
from copy import deepcopy
from datetime import date
from decimal import Decimal, localcontext
import re

from services import balance_etic_tables_service as commun
from services.balance_css_service import SOURCE as SOURCE_CGI
from services.fiscalite_credits_service import construire_credits_is

BLOC = 'credits_is_documentaires'
REGIME = 'Société IS hors exonération totale'
TYPES = {
    'PPRF — CGI159': 'pprf',
    'Sukuk — CGI159': 'pprf',
    'Rémunérations de tiers — CGI157': 'retenue_tiers',
    'Location — CGI157': 'retenue_tiers',
    'Autre — à qualifier': None,
}
PAYEURS = ('Public ou filiale publique', 'Banque ou assurance',
           'Entreprise privée CA au moins 500 millions MAD', 'Autre payeur — à qualifier')
SOURCE = {**SOURCE_CGI, 'titre': 'CGI 2026, articles 157, 159, 247-XXXXVI ; LF50-25 article7-IV-1/5',
          'pages_imprimees': '294-296, 483, 609-610'}
LIBELLES = {
    'montant_total': 'Montant total des justificatifs saisis',
    'deja_impute_acomptes': 'Part déjà imputée sur acomptes',
    'autres_utilisations': 'Autres utilisations ou restitutions antérieures',
    'disponible_arithmetique': 'Reliquat arithmétique des justificatifs saisis',
    'credits_proposes': 'Crédits disponibles proposés après qualifications',
    'ecart_montant_contexte': 'Écart total saisi moins total du contexte fiscal',
    'ecart_imputations_contexte': 'Écart déjà imputé moins part du contexte fiscal',
}
NOTE = (
    'Crédits IS externes2026, codes CR internes. PPRF et Sukuk relèvent de '
    'l’article159 ; rémunérations de tiers et locations de l’article157 du CGI2026. '
    'Le type, le rattachement fiscal, la date et l’éligibilité sont explicitement '
    'déclarés et justifiés. '
    'La date d’allocation et la catégorie du payeur doivent être qualifiées pour '
    'l’article157 : locations allouées à compter du1juillet2026 ; nouvelles '
    'retenues des banques/assurances et entreprises privées CA au moins500millions '
    'à compter de cette date. Une date de retenue tardive ne remplace pas une '
    'date d’allocation inconnue ou antérieure à l’entrée en vigueur. '
    'Aucun taux de retenue ni droit individuel n’est déduit du libellé, de la balance ou du Journal. Le profil confirme la période source '
    'et l’exhaustivité ; un crédit antérieur ou un autre type reste à qualifier. '
    'Les utilisations et restitutions antérieures sont retirées avant le calcul '
    'du reliquat par le moteur partagé ; les parts déjà imputées sur acomptes '
    'ne seront pas disponibles une seconde fois. Les regroupements du moteur '
    'ne fixent aucun ordre juridique entre les types. Une exclusion explicite '
    'est conservée ; un champ vide reste inconnu. Néant seul ne vaut pas zéro : '
    'une absence exhaustive doit être confirmée dans le profil et justifiée. '
    'Les comparaisons au contexte fiscal ne le corrigent pas. Aucune imputation, '
    'restitution, liquidation, écriture ou paiement confirmé ; CSS distincte, '
    'aucun prêt à déposer. Les versions conservées ne sont pas recalculées.'
)


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    profil = [('nature', 'Désignation du profil crédits', 'text'),
              ('regime', 'Périmètre IS des crédits', 'text'),
              ('periode_confirmee', 'Période source confirmée', 'text'),
              ('exhaustivite', 'Liste des crédits exhaustive', 'text'),
              ('absence_credits', 'Absence de tout crédit confirmée', 'text')]
    credits = [('nature', 'Désignation du justificatif crédit', 'text'),
               ('type_credit', 'Type juridique du crédit', 'text'),
               ('exercice_rattachement', 'Exercice fiscal de rattachement', 'text'),
               ('date_retenue', 'Date de la retenue justifiée', 'date'),
               ('date_allocation', 'Date d’allocation du produit justifiée', 'date'),
               ('categorie_payeur', 'Catégorie du payeur article157 déclarée', 'text'),
               ('eligibilite_confirmee', 'Éligibilité IS de cette ligne confirmée', 'text'),
               ('montant', 'Montant total du justificatif', 'number'),
               ('deja_impute_acomptes', 'Part déjà imputée sur acomptes', 'number'),
               ('autres_utilisations', 'Autres utilisations ou restitutions', 'number')]
    return [{'code': code, 'groupe': 'Interne', 'titre': titre,
             'colonnes_saisie': [{'cle': k, 'label': label, 'type': typ} for k, label, typ in cols]}
            for code, titre, cols in [('CR-PROFIL', 'Profil et exhaustivité des crédits', profil),
                                       ('CR-LIGNES', 'Justificatifs des crédits IS', credits)]]


def normaliser(dossier, tables):
    ts = commun.normaliser(dossier, tables, referentiel=catalogue)
    if len(ts[0]['lignes']) > 1 or len(ts[1]['lignes']) > 50:
        raise ValueError('Un profil et cinquante justificatifs crédits maximum.')
    profil = ts[0]['lignes'][0] if ts[0]['lignes'] else {}
    vus = set()
    for t in ts:
        for r in t['lignes']:
            if not r['nature'] or not r['reference_source']:
                raise ValueError('Désignation et référence de source requises, même pour une ligne partielle.')
            for k in ('periode_confirmee', 'exhaustivite', 'absence_credits', 'eligibilite_confirmee'):
                if k in r and r[k] not in ('', 'oui', 'non'):
                    raise ValueError('Qualification crédits : oui, non ou champ vide.')
            if t['code'] == 'CR-PROFIL':
                if r['regime'] not in ('', REGIME):
                    raise ValueError('Périmètre IS des crédits non couvert.')
                continue
            ref = r['reference_source'].casefold()
            if ref in vus:
                raise ValueError('Référence de justificatif crédit en doublon ; identifier chaque ligne source distinctement.')
            vus.add(ref)
            if r['type_credit'] not in ('', *TYPES):
                raise ValueError('Type juridique de crédit inconnu.')
            annee = r['exercice_rattachement']
            if annee and (not re.fullmatch('[0-9]{4}', annee) or not 1900 <= int(annee) <= dossier['exercice']):
                raise ValueError('Exercice de rattachement : année de quatre chiffres au plus égale à la préparation.')
            if r['categorie_payeur'] not in ('', *PAYEURS):
                raise ValueError('Catégorie du payeur article157 inconnue.')
            for champ in ('date_retenue', 'date_allocation'):
                if r[champ]:
                    try:
                        date.fromisoformat(r[champ])
                        if not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', r[champ]):
                            raise ValueError()
                    except ValueError as exc:
                        raise ValueError('Date ISO valide requise pour ' + champ + '.') from exc
            if r['montant'] is not None and Decimal(r['montant']) <= 0:
                raise ValueError('Le montant total du justificatif crédit doit être positif.')
            if all(r[k] is not None for k in ('montant', 'deja_impute_acomptes', 'autres_utilisations')):
                with localcontext() as ctx:
                    ctx.prec = 60
                    if Decimal(r['deja_impute_acomptes']) + Decimal(r['autres_utilisations']) > Decimal(r['montant']):
                        raise ValueError('Les utilisations cumulées dépassent le montant du crédit.')
    if profil.get('absence_credits') == 'oui' and ts[1]['lignes']:
        raise ValueError('Absence de crédits incompatible avec les justificatifs saisis.')
    return ts


def source_contexte(dossier):
    bloc = dossier['contenu'].get('contexte_fiscal_documentaire')
    if not bloc:
        return None
    m = bloc['controle_contexte_fiscal']['montants']
    return {'cle': bloc['cle'], 'credits_total': m['credits_total'], 'credits_deja_imputes': m['credits_deja_imputes']}


def calculer_controles(dossier, demande):
    tp, tl = demande['tables']
    profil = tp['lignes'][0] if tp['lignes'] else {}
    periode = deepcopy(dossier['contenu']['periode'])
    exercice = dossier['exercice']
    couvert = type(exercice) is int and exercice == 2026
    profil_ok = tp['statut'] == 'documente' and profil.get('regime') == REGIME and all(
        profil.get(k) == 'oui' for k in ('periode_confirmee', 'exhaustivite'))
    absence = profil_ok and profil.get('absence_credits') == 'oui' and tl['statut'] == 'neant_declare' and not tl['lignes']
    lignes, moteur, alertes = [], [], []
    src = source_contexte(dossier)
    with localcontext() as ctx:
        ctx.prec = 60
        for i, r in enumerate(tl['lignes'], 1):
            numeriques = all(r[k] is not None for k in ('montant', 'deja_impute_acomptes', 'autres_utilisations'))
            disponible = Decimal(r['montant']) - Decimal(r['deja_impute_acomptes']) - Decimal(r['autres_utilisations']) if numeriques else None
            exclusion = r['eligibilite_confirmee'] == 'non'
            effet = True
            if TYPES.get(r['type_credit']) == 'retenue_tiers':
                allocation, payeur = r.get('date_allocation'), r.get('categorie_payeur')
                effet = bool(allocation and r['date_retenue'] and allocation <= r['date_retenue']
                    and payeur in PAYEURS[:3])
                if r['type_credit'] == 'Location — CGI157' or payeur in PAYEURS[1:3]:
                    effet = effet and allocation >= '2026-07-01'
            qualifie = (tl['statut'] == 'documente' and numeriques and bool(r['type_credit'])
                and TYPES.get(r['type_credit']) is not None and r['exercice_rattachement'] == str(exercice)
                and bool(r['date_retenue']) and periode['debut'] <= r['date_retenue'] <= periode['fin']
                and r['eligibilite_confirmee'] == 'oui' and effet)
            statut = 'exclu_declare' if exclusion else 'qualifie_declare' if qualifie else 'a_qualifier'
            lignes.append({'ligne': i, 'type_credit': r['type_credit'], 'reference_source': r['reference_source'],
                           'statut': statut, 'disponible_arithmetique': None if disponible is None else format(disponible, '.2f')})
            if qualifie:
                net = Decimal(r['montant']) - Decimal(r['autres_utilisations'])
                if net > 0:
                    moteur.append({'type': TYPES[r['type_credit']], 'montant': net,
                                   'montant_deja_impute_acomptes': r['deja_impute_acomptes']})
        complet = bool(absence or (profil_ok and profil.get('absence_credits') == 'non' and tl['statut'] == 'documente'
                        and lignes and all(r['statut'] != 'a_qualifier' for r in lignes)))
        def somme(champ):
            if absence:
                return Decimal('0.00')
            if not tl['lignes'] or any(r[champ] is None for r in tl['lignes']):
                return None
            return sum((Decimal(r[champ]) for r in tl['lignes']), Decimal('0.00'))
        total, deja, autres = (somme(k) for k in ('montant', 'deja_impute_acomptes', 'autres_utilisations'))
        vals = {'montant_total': total, 'deja_impute_acomptes': deja, 'autres_utilisations': autres,
                'disponible_arithmetique': None if any(v is None for v in (total, deja, autres)) else total - deja - autres,
                'credits_proposes': construire_credits_is(moteur)['total_disponible_liquidation'] if couvert and complet else None,
                'ecart_montant_contexte': None, 'ecart_imputations_contexte': None}
        for k, nom, valeur in [('ecart_montant_contexte', 'credits_total', total),
                               ('ecart_imputations_contexte', 'credits_deja_imputes', deja)]:
            if src and src[nom] is not None and valeur is not None:
                vals[k] = valeur - Decimal(src[nom])
                if vals[k] != 0:
                    alertes.append(LIBELLES[k] + ' non nul : revoir les sources sans corriger le contexte automatiquement.')
        if not couvert:
            alertes.append('Référentiel crédits vérifié pour2026 uniquement ; aucun disponible proposé pour cet exercice.')
        if not complet:
            alertes.append('Profil ou justificatifs incomplets : disponibilité fiscale globale inconnue, même si un reliquat arithmétique est calculable.')
        if any(r['statut'] == 'exclu_declare' for r in lignes):
            alertes.append('Des justificatifs sont explicitement exclus ; leurs montants restent visibles et ne sont pas proposés à imputation.')
        return {'methode': 'credits_qualifies_moteur_partage_2026_v1', 'exercice': exercice, 'periode_source': periode,
                'exercice_couvert': couvert, 'qualification_complete_declaree': complet,
                'absence_exhaustive_confirmee': bool(absence),
                'montants': {k: None if v is None else format(v, '.2f') for k, v in vals.items()},
                'lignes': lignes, 'source_contexte_fiscal': src, 'reference_juridique': deepcopy(SOURCE), 'alertes': alertes,
                'solde_final': None, 'liquidation_confirmee': False, 'imputation_confirmee': False, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC) or {}
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue, note=bloc.get('note_conservee', NOTE))
    c = vue['controle_credits'] = deepcopy(bloc.get('controle_credits'))
    vue['source_contexte_modifiee'] = bool(c and (c['source_contexte_fiscal'] or {}).get('cle') != (source_contexte(dossier) or {}).get('cle'))
    if vue['source_contexte_modifiee']:
        vue['alertes'].append('Le contexte fiscal a changé : comparaison crédits conservée pour mémoire ; relire puis conserver une nouvelle qualification, sans recalcul historique.')
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC, normalisation=normaliser,
        referentiel=catalogue, enrichir=lambda d, q: {'controle_credits': calculer_controles(d, q), 'note_conservee': NOTE})
