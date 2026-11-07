"""B1 depuis les sources figées : aucune ventilation d'amortissement inventée."""
from copy import deepcopy
from decimal import Decimal, localcontext
from types import SimpleNamespace
from services.balance_import_service import montant_import
from services import balance_etic_tables_service as commun

BLOC = 'non_valeurs_documentaires'
NOTE = ('Détail B1 interne en MAD depuis les seules balances conservées. '
        'Brut = solde débiteur des comptes21 ; amortissements groupés = solde créditeur '
        'des comptes281 ; net = brut moins amortissements, comme dans le bilan existant. '
        'Les soldes inverses restent signés. Aucune ventilation des amortissements par '
        'compte21, aucun mouvement brut, acquisition ou sortie n’est déduit. '
        'Les libellés individuels ne sont pas conservés à l’import. Les écarts avec '
        'la rubrique21 du bilan figé restent visibles sans correction. '
        'Une valeur indisponible n’est pas zéro ; aucun dossier prêt à déposer n’est produit.')


def calculer(dossier):
    from services.etic_service import CATALOGUE_ETIC
    c = dossier['contenu']; periodes = {}
    with localcontext() as ctx:
        ctx.prec = 60
        for p in ('n', 'n1'):
            source = c.get('sources', {}).get(p)
            etats = c.get('preparation', {}).get('etats' if p == 'n' else 'etats_n1') or {}
            ref = next((r for r in etats.get('bilan', {}).get('actif', {}).get('immobilise', []) if r.get('code') == '21'), {})
            v = {'disponible': False, 'motif': '', 'lignes': [], **{k: None for k in (
                'brut', 'amortissements', 'net', 'bilan_brut', 'bilan_amortissements', 'bilan_net',
                'ecart_brut', 'ecart_amortissements', 'ecart_net')}}
            if source is None:
                v['motif'] = 'Source détaillée absente ; aucun solde reconstitué.'
            elif not isinstance(source, list) or any(not isinstance(r, dict) or not isinstance(r.get('compte'), str)
                    or any(r.get(k) is None or r.get(k) == '' for k in ('debit','credit')) for r in source):
                v['motif'] = 'Source détaillée incomplète ; aucun montant manquant remplacé par zéro.'
            else:
                comptes = {}
                for r in source:
                    compte = r['compte']
                    if compte.startswith(('21', '281')):
                        net = montant_import(r['debit'], compte) - montant_import(r['credit'], compte)
                        comptes[compte] = comptes.get(compte, Decimal(0)) + net
                v['lignes'] = [{'compte': compte, 'intitule': None,
                    'nature': 'Brut' if compte.startswith('21') else 'Amortissement groupé',
                    'montant': format(n if compte.startswith('21') else -n, '.2f')}
                    for compte, n in sorted(comptes.items()) if n != 0]
                brut = sum((n for compte,n in comptes.items() if compte.startswith('21')), Decimal(0))
                amort = -sum((n for compte,n in comptes.items() if compte.startswith('281')), Decimal(0))
                for k,n,rk in [('brut',brut,'brut'),('amortissements',amort,'amort_prov'),('net',brut-amort,'net')]:
                    reference = ref.get(rk)
                    reference = None if reference is None else Decimal(str(reference))
                    if reference is not None and not reference.is_finite():
                        raise ValueError('Rubrique21 du bilan conservé non finie.')
                    v[k] = format(n, '.2f')
                    v['bilan_' + k] = None if reference is None else format(reference, 'f')
                    v['ecart_' + k] = None if reference is None else format(n-reference, 'f')
                v['disponible'] = True
            periodes[p] = v
    return {'code': 'B1', 'titre': next(r['titre'] for r in CATALOGUE_ETIC if r['code']=='B1'),
            'methode': 'soldes_21_281_decimal_v1', 'note': NOTE, 'periodes': periodes, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC)
    return ({**deepcopy(bloc), 'conserve': True, 'pret_a_deposer': False} if bloc else
            {'conserve': False, 'vue': None, 'note': NOTE, 'pret_a_deposer': False})


def conserver(db, user, preparation_id, data):
    # Réutilise les verrous, empreintes, versions et rejouabilité du service partagé.
    demande = SimpleNamespace(empreinte_parent=data.empreinte_parent, cle=data.cle, tables=[])
    return commun.conserver(db, user, preparation_id, demande, nom_bloc=BLOC,
        normalisation=lambda dossier,tables: [], referentiel=lambda dossier: [],
        enrichir=lambda dossier,demande: {'vue': calculer(dossier)})
