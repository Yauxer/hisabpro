"""Arithmétique documentaire du capital, sans déclaration d'exhaustivité."""
from decimal import Decimal, localcontext

NOTE = ('Contrôles arithmétiques des seules lignes C1 déclarées. '
        'Les inconnus et les tableaux sans ligne ne deviennent jamais zéro. '
        'Le rapprochement utilise les soldes détaillés des comptes 111 de la balance N '
        'conservée, selon le préfixe déjà utilisé par le bilan HisabPro. '
        'Il est indicatif : le capital social ou personnel comptable ne prouve pas '
        'la répartition juridique. Un écart nul ne prouve ni l’exhaustivité des associés '
        'ni la validité des titres. Aucun montant, pourcentage ou compte n’est corrigé.')


def calculer(dossier, demande):
    table = next(r for r in demande['tables'] if r['code'] == 'C1')
    lignes = table['lignes']
    def d(v):return None if v is None else Decimal(v)
    def f(v):return None if v is None else format(v, 'f')
    with localcontext() as ctx:
        ctx.prec = 60
        controles = []
        for i, row in enumerate(lignes, 1):
            titres, nominal, declare = (d(row[k]) for k in ('titres','nominal','capital'))
            attendu = None if titres is None or nominal is None else titres * nominal
            ecart = None if attendu is None or declare is None else declare - attendu
            controles.append({'ligne': i, 'associe': row['associe'], 'titres': row['titres'],
                'nominal': row['nominal'], 'capital_declare': row['capital'],
                'capital_calcule': f(attendu), 'ecart_capital': f(ecart)})
        def somme(champ):
            if not lignes or any(r[champ] is None for r in lignes):return None
            return sum((d(r[champ]) for r in lignes), Decimal('0'))
        total, pourcentages = somme('capital'), somme('pourcentage')
        source = dossier['contenu'].get('sources', {}).get('n')
        capital_balance = None if source is None else sum(
            (Decimal(r['credit']) - Decimal(r['debit']) for r in source if r['compte'].startswith('111')),Decimal('0.00'))
        ecart_balance = None if total is None or capital_balance is None else total - capital_balance
        ecart_pourcentages = None if pourcentages is None else pourcentages - Decimal('100')
        return {'schema_version':1,'note':NOTE,'statut_declare':table['statut'],
            'lignes':controles,'somme_capital_declare':f(total),'capital_balance_111':f(capital_balance),
            'ecart_capital_balance':f(ecart_balance),'somme_pourcentages':f(pourcentages),
            'ecart_pourcentages_100':f(ecart_pourcentages),'source_n_disponible':source is not None,
            'pret_a_deposer':False}


def lignes_export(controle):
    rows = [('Portée', controle['note'], ''),
        ('Déclaration du tableau', controle['statut_declare'], ''),
        ('Source détaillée N disponible', 'Oui' if controle['source_n_disponible'] else 'Non', ''),
        ('Somme des capitaux déclarés', controle['somme_capital_declare'], 'MAD'),
        ('Capital des comptes 111 dans la balance N', controle['capital_balance_111'], 'MAD'),
        ('Écart capitaux déclarés moins balance 111', controle['ecart_capital_balance'], 'MAD'),
        ('Somme des pourcentages déclarés', controle['somme_pourcentages'], '%'),
        ('Écart somme des pourcentages moins 100', controle['ecart_pourcentages_100'], '%')]
    for row in controle['lignes']:
        prefix = 'Ligne ' + str(row['ligne']) + ' · ' + (row['associe'] or 'Associé à compléter') + ' · '
        rows += [(prefix + label, row[key], unite) for key,label,unite in [
            ('titres','Titres déclarés','titres'),('nominal','Nominal déclaré','MAD'),
            ('capital_declare','Capital déclaré','MAD'),('capital_calcule','Produit titres × nominal','MAD'),
            ('ecart_capital','Écart capital déclaré moins produit','MAD')]]
    return rows
