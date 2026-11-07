"""Simulation de salaire fixe : paramètres explicites, aucune comptabilisation.

Le référentiel historique incomplet ne produit pas silencieusement une paie.
Les variables, prorata et régimes particuliers restent à traiter séparément.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal('0.01')
CODES = ('cnss_retraite', 'cnss_prest_fam', 'amo', 'amo_participation', 'formation_prof')
AVERTISSEMENTS = [
    'Simulation de salaire fixe sur mois complet, sans validation de paie ni déclaration.',
    'Référentiel social non vérifié auprès de la CNSS pendant cette session : validation humaine requise.',
    'Primes, indemnités, absences, heures supplémentaires, avances, CIMR et régimes particuliers non couverts.',
    'Assurance accidents du travail exclue : aucun taux contractuel confirmé.',
]
SOURCES = [
    {'titre': 'CGI 2026, articles 59, 73 et 74', 'url': 'https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf', 'statut': 'Référence fiscale ; cas particuliers à vérifier'},
    {'titre': 'CNSS — paiement des cotisations sociales', 'url': 'https://www.cnss.ma/fr/content/paiement-de-vos-cotisations-sociales', 'statut': 'Source indisponible pendant la session ; taux non confirmés'},
]


def nombre(value):
    if isinstance(value, bool):
        raise ValueError('Nombre booléen interdit')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError('Nombre invalide') from exc
    if not result.is_finite():
        raise ValueError('Nombre non fini interdit')
    return result


def montant(value):
    try:
        return nombre(value).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError('Montant hors limites') from exc


def verifier_parametres(taux, bareme, deductions):
    erreurs = []
    codes = [t.code for t in taux]
    for code in CODES:
        if codes.count(code) != 1:
            erreurs.append(f'Paramètre {code} absent ou en doublon')
    try:
        for t in taux:
            if t.code not in CODES:
                continue
            if not (0 <= nombre(t.taux_sal) <= 1 and 0 <= nombre(t.taux_pat) <= 1):
                raise ValueError('Taux hors limites')
            if t.plafond is not None and nombre(t.plafond) <= 0:
                raise ValueError('Plafond annuel invalide')
        if not bareme:
            erreurs.append('Barème IR absent pour cette année')
        else:
            borne = Decimal(0)
            for index, tranche in enumerate(bareme):
                if nombre(tranche.tranche_min) != borne or not 0 <= nombre(tranche.taux) <= 1 or nombre(tranche.deduction) < 0:
                    raise ValueError('Barème IR discontinu ou invalide')
                if tranche.tranche_max is None:
                    if index != len(bareme) - 1:
                        raise ValueError('Tranche IR ouverte avant la dernière tranche')
                else:
                    borne = nombre(tranche.tranche_max)
                    if borne <= nombre(tranche.tranche_min):
                        raise ValueError('Tranche IR vide')
            if bareme[-1].tranche_max is not None:
                raise ValueError('Dernière tranche IR non ouverte')
        enfants = [d for d in deductions if d.code == 'enfant']
        if len(enfants) != 1:
            erreurs.append('Réduction IR par personne à charge absente ou en doublon')
        elif nombre(enfants[0].montant_an) < 0 or enfants[0].max_beneficiaires != 6:
            raise ValueError('Réduction familiale invalide')
    except ValueError as exc:
        erreurs.append(str(exc))
    return erreurs


def simuler_salaire(employe, taux_list, bareme, deductions):
    erreurs = verifier_parametres(taux_list, bareme, deductions)
    if erreurs:
        raise ValueError('; '.join(erreurs))
    personnes = employe.personnes_charge_ir
    if personnes is None or isinstance(personnes, bool) or not 0 <= personnes <= 6:
        raise ValueError('Nombre de personnes à charge IR à confirmer explicitement')
    if not 0 <= nombre(employe.salaire_brut) <= Decimal('9999999999.99'):
        raise ValueError('Salaire brut hors limites')
    brut = montant(employe.salaire_brut)
    taux = {t.code: t for t in taux_list}
    valeurs = {}
    for code in CODES:
        param = taux[code]
        base = brut if param.plafond is None else min(brut, nombre(param.plafond) / 12)
        valeurs[code] = {'base': montant(base), 'salarial': montant(base * nombre(param.taux_sal)), 'patronal': montant(base * nombre(param.taux_pat))}
    retenues = sum(v['salarial'] for v in valeurs.values())
    charges = sum(v['patronal'] for v in valeurs.values())
    annuel = brut * 12
    frais = min(annuel * (Decimal('.35') if annuel <= 78000 else Decimal('.25')), Decimal(35000))
    revenu_net = max(Decimal(0), annuel - frais - retenues * 12)
    tranche = next(t for t in bareme if t.tranche_max is None or revenu_net <= nombre(t.tranche_max))
    reduction = next(d for d in deductions if d.code == 'enfant')
    ir_annuel = max(Decimal(0), revenu_net * nombre(tranche.taux) - nombre(tranche.deduction) - personnes * nombre(reduction.montant_an))
    ir = montant(ir_annuel / 12)
    return {
        'salaire_brut': brut, 'cnss_retraite_sal': valeurs['cnss_retraite']['salarial'],
        'amo_sal': valeurs['amo']['salarial'], 'total_retenues_sal': retenues,
        'ir': ir, 'salaire_net': brut - retenues - ir,
        'cnss_retraite_pat': valeurs['cnss_retraite']['patronal'],
        'prestations_fam': valeurs['cnss_prest_fam']['patronal'],
        'amo_pat': valeurs['amo']['patronal'] + valeurs['amo_participation']['patronal'],
        'accidents': None, 'formation': valeurs['formation_prof']['patronal'],
        'total_charges_pat': charges, 'cout_employeur': brut + charges,
        'revenu_net_imposable_annuel': montant(revenu_net), 'frais_professionnels_annuels': montant(frais),
        'personnes_charge_ir': personnes, 'detail_cotisations': valeurs,
    }
