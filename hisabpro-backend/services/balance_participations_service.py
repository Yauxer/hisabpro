"""B4 indépendant : soldes251 certains, émetteurs et données hors balance inconnus."""
from copy import deepcopy
from decimal import Decimal, localcontext
from types import SimpleNamespace
from services.balance_import_service import montant_import
from services import balance_etic_tables_service as commun

BLOC = 'participations_documentaires'
INFORMATIONS = ['Identité de l’émetteur', 'Capital de l’émetteur', 'Quote-part détenue', 'Produits reçus']
NOTE = ('Détail B4 interne en MAD depuis les seules balances conservées. '
        'Les soldes251 sont débiteurs moins créditeurs et restent signés. '
        'Le bilan figé regroupe24/25 : le contrôle porte sur ce brut financier entier, '
        'jamais sur une comparaison du seul251 au24/25. Les autres soldes24/25 '
        'sont présentés séparément. Aucun libellé historique, émetteur, capital, '
        'quote-part ou produit reçu n’est déduit d’un compte. Les provisions ne '
        'sont pas ventilées sur les titres ; aucun mouvement brut n’est inventé. '
        'Indisponible ne signifie pas zéro. À compléter, sans validation fiscale officielle.')


def calculer(dossier):
    from services.etic_service import CATALOGUE_ETIC
    contenu = dossier['contenu']; periodes = {}
    with localcontext() as ctx:
        ctx.prec = 60
        for periode in ('n', 'n1'):
            source = contenu.get('sources', {}).get(periode)
            etats = contenu.get('preparation', {}).get('etats' if periode == 'n' else 'etats_n1') or {}
            ref = next((r for r in etats.get('bilan', {}).get('actif', {}).get('immobilise', [])
                        if r.get('code') == '24/25'), {})
            v = {'disponible': False, 'motif': '', 'lignes': [],
                 **{k: None for k in ('participations','autres_financieres','financieres_brut',
                                     'bilan_financieres_brut','ecart_financieres_brut')}}
            if source is None:
                v['motif'] = 'Source détaillée absente ; aucun solde251 ou comparatif reconstitué.'
            elif not isinstance(source, list) or any(not isinstance(r, dict) or not isinstance(r.get('compte'), str)
                    or any(r.get(k) is None or r.get(k) == '' for k in ('debit','credit')) for r in source):
                v['motif'] = 'Source détaillée incomplète ; aucun montant manquant remplacé par zéro.'
            else:
                comptes = {}
                for r in source:
                    compte = r['compte']
                    if compte.startswith(('24', '25')):
                        net = montant_import(r['debit'], compte) - montant_import(r['credit'], compte)
                        comptes[compte] = comptes.get(compte, Decimal(0)) + net
                participations = sum((n for c,n in comptes.items() if c.startswith('251')), Decimal(0))
                autres = sum((n for c,n in comptes.items() if not c.startswith('251')), Decimal(0))
                total = participations + autres
                v['lignes'] = [{'compte': c, 'intitule': None, 'nature': 'Titre de participation',
                    'montant': format(n, '.2f'), 'emetteur': None, 'capital_emetteur': None,
                    'quote_part': None, 'produits_recus': None}
                    for c,n in sorted(comptes.items()) if c.startswith('251') and n != 0]
                for k,n in [('participations',participations),('autres_financieres',autres),('financieres_brut',total)]:
                    v[k] = format(n, '.2f')
                reference = ref.get('brut')
                reference = None if reference is None else Decimal(str(reference))
                if reference is not None and not reference.is_finite():
                    raise ValueError('Brut financier du bilan conservé non fini.')
                v['bilan_financieres_brut'] = None if reference is None else format(reference, 'f')
                v['ecart_financieres_brut'] = None if reference is None else format(total-reference, 'f')
                v['disponible'] = True
            periodes[periode] = v
    return {'code': 'B4', 'titre': next(r['titre'] for r in CATALOGUE_ETIC if r['code']=='B4'),
            'methode': 'soldes_251_et_controle_brut_24_25_decimal_v1', 'note': NOTE,
            'informations_a_completer': deepcopy(INFORMATIONS), 'periodes': periodes, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC)
    return ({**deepcopy(bloc), 'conserve': True, 'pret_a_deposer': False} if bloc else
            {'conserve': False, 'vue': None, 'note': NOTE, 'pret_a_deposer': False})


def conserver(db, user, preparation_id, data):
    demande = SimpleNamespace(empreinte_parent=data.empreinte_parent, cle=data.cle, tables=[])
    return commun.conserver(db, user, preparation_id, demande, nom_bloc=BLOC,
        normalisation=lambda dossier,tables: [], referentiel=lambda dossier: [],
        enrichir=lambda dossier,demande: {'vue': calculer(dossier)})
