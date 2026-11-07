"""Contexte fiscal externe sourcé, sans liquidation ni qualification automatique."""
from copy import deepcopy
from decimal import Decimal, localcontext

from services import balance_etic_tables_service as commun
from services.balance_import_service import montant_import

BLOC = 'contexte_fiscal_documentaire'
SCHEMAS = {
    'CF-CM': ('Cotisation minimale déclarée', {'montant': 'CM déclarée'}, 1),
    'CF-CSS': ('CSS déclarée séparément', {'montant': 'CSS déclarée'}, 1),
    'CF-CREDITS': ('Crédits et retenues déclarés', {
        'montant': 'Montant total du crédit',
        'deja_impute': 'Part déjà imputée sur acomptes'}, 50),
    'CF-ACOMPTES': ('Acomptes et imputations déclarés', {
        'verse': 'Montant effectivement versé',
        'credit_anterieur': 'Crédit antérieur imputé',
        'credits_deja_imputes': 'Crédits et retenues déjà imputés'}, 20),
}
LIBELLES = {
    'cm_declaree': 'CM déclarée', 'css_declaree': 'CSS déclarée séparément',
    'credits_total': 'Total des crédits déclarés',
    'credits_deja_imputes': 'Crédits déjà imputés déclarés côté crédits',
    'credits_restants': 'Crédits déclarés moins part déjà imputée',
    'acomptes_verses': 'Acomptes effectivement versés déclarés',
    'credit_anterieur_impute': 'Crédits antérieurs imputés déclarés',
    'imputations_sur_acomptes': 'Crédits déjà imputés déclarés côté acomptes',
    'ecart_imputations': 'Écart imputations côté acomptes moins côté crédits',
}
NOTE = (
    'Contexte fiscal documentaire interne N en MAD. Les codes CF sont internes. '
    'CM, CSS, crédits et acomptes sont explicitement déclarés et sourcés, '
    'jamais déduits de la balance, du Journal ou du module fiscal actif. '
    'Les totaux portent seulement sur les lignes saisies ; ils ne prouvent '
    'pas leur exhaustivité ou leur éligibilité. Une case vide, une liste vide '
    'ou une déclaration néant ne vaut pas zéro. Chaque crédit distingue son '
    'montant total de sa part déjà imputée ; leur différence est arithmétique, '
    'sans nouveau droit à imputation ou restitution. Les acomptes distinguent '
    'les versements effectifs, crédits antérieurs et retenues déjà imputées. '
    'L’écart compare les deux déclarations des mêmes imputations, sans les '
    'corriger ni les additionner une seconde fois. CSS reste séparée. '
    'Aucun taux, exonération, calendrier, ordre d’imputation, impôt dû ou solde '
    'final n’est calculé ici. L’IS B12 conservé est affiché pour mémoire, sans '
    'recalcul et sans devenir une liquidation. Les sources et qualifications '
    'fiscales applicables restent à vérifier. Aucune écriture, liquidation, '
    'imputation ou paiement confirmé ; pas de prêt à déposer.'
)


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    return [{'code': code, 'groupe': 'Interne', 'titre': titre,
             'colonnes_saisie': [
                 {'cle': 'nature', 'label': 'Désignation du justificatif fiscal', 'type': 'text'},
                 *[{'cle': k, 'label': label, 'type': 'number', 'unite': 'MAD'}
                   for k, label in champs.items()]]}
            for code, (titre, champs, _max) in SCHEMAS.items()]


def nombre(_colonne, valeur, contexte):
    return format(montant_import(valeur, contexte), '.2f')


def normaliser(dossier, tables):
    tables = commun.normaliser(dossier, tables, referentiel=catalogue, convertir_nombre=nombre)
    for t in tables:
        if len(t['lignes']) > SCHEMAS[t['code']][2]:
            raise ValueError('Nombre de lignes dépassé pour ' + t['code'] + '.')
        vus = set()
        for r in t['lignes']:
            if not r['nature'] or not r['reference_source']:
                raise ValueError('Désignation et référence de source requises, même pour une ligne partielle.')
            identite = (r['nature'], r['reference_source'])
            if identite in vus:
                raise ValueError('Justificatif fiscal en doublon dans ' + t['code'] + '.')
            vus.add(identite)
            if t['code'] == 'CF-CREDITS' and all(r[k] is not None for k in ('montant', 'deja_impute')):
                if Decimal(r['deja_impute']) > Decimal(r['montant']):
                    raise ValueError('La part déjà imputée ne peut pas dépasser le crédit total déclaré.')
    return tables


def source_b12(dossier):
    bloc = dossier['contenu'].get('passage_fiscal_documentaire')
    if not bloc:
        return None
    return {'cle': bloc['cle'],
            'is_theorique_taux_declare': bloc['controle_passage_fiscal']['montants']['is_theorique_taux_declare']}


def calculer_controles(dossier, demande):
    tables = {t['code']: t['lignes'] for t in demande['tables']}
    with localcontext() as ctx:
        ctx.prec = 60

        def total(code, champ):
            lignes = tables[code]
            if not lignes or any(r[champ] is None for r in lignes):
                return None
            return sum((Decimal(r[champ]) for r in lignes), Decimal('0.00'))

        credits = total('CF-CREDITS', 'montant')
        imputes = total('CF-CREDITS', 'deja_impute')
        sur_acomptes = total('CF-ACOMPTES', 'credits_deja_imputes')
        valeurs = {
            'cm_declaree': total('CF-CM', 'montant'), 'css_declaree': total('CF-CSS', 'montant'),
            'credits_total': credits, 'credits_deja_imputes': imputes,
            'credits_restants': None if credits is None or imputes is None else credits - imputes,
            'acomptes_verses': total('CF-ACOMPTES', 'verse'),
            'credit_anterieur_impute': total('CF-ACOMPTES', 'credit_anterieur'),
            'imputations_sur_acomptes': sur_acomptes,
            'ecart_imputations': None if imputes is None or sur_acomptes is None else sur_acomptes - imputes,
        }
        alertes = []
        if valeurs['ecart_imputations'] not in (None, Decimal(0)):
            alertes.append('Les crédits déjà imputés diffèrent entre justificatifs de crédits et acomptes ; vérifier les sources, aucune correction automatique.')
        return {'methode': 'totaux_documentaires_sans_liquidation_v1',
                'montants': {k: None if v is None else format(v, '.2f') for k, v in valeurs.items()},
                'source_b12': source_b12(dossier), 'alertes': alertes,
                'impot_du': None, 'solde_final': None, 'liquidation_confirmee': False,
                'paiement_confirme': False, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC) or {}
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue,
                             note=bloc.get('note_conservee', NOTE))
    vue['controle_contexte_fiscal'] = deepcopy(bloc.get('controle_contexte_fiscal'))
    controle = vue['controle_contexte_fiscal']
    vue['source_b12_modifiee'] = bool(controle and
        (controle['source_b12'] or {}).get('cle') != (source_b12(dossier) or {}).get('cle'))
    if vue['source_b12_modifiee']:
        vue['alertes'].append('Le passage fiscal B12 a changé depuis ce contexte. Relire les justificatifs et conserver une nouvelle version du contexte pour actualiser la référence ; anciens contrôles inchangés.')
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC,
        normalisation=normaliser, referentiel=catalogue,
        enrichir=lambda d, q: {'controle_contexte_fiscal': calculer_controles(d, q), 'note_conservee': NOTE})
