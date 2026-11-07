"""B13 documentaire autonome : sources exactes, aucun taux ou impôt déduit."""
from copy import deepcopy
from decimal import Decimal, localcontext

from services import balance_etic_tables_service as commun
from services.balance_cpc_detail_service import calculer as detail_cpc
from services.balance_source_controle_service import cloture_technique

BLOC = 'resultat_courant_documentaire'
PERIODES = {'B13-N': 'n', 'B13-N1': 'n1'}
NOTE = ('B13 documentaire interne en MAD depuis les seules balances conservées. '
        'Résultat courant : produits71/73 moins charges61/63, selon le périmètre '
        'du moteur ETIC existant ; écart au CPC VII figé visible. Les soldes67 '
        'comptabilisés sont présentés pour mémoire, jamais assimilés à un impôt '
        'théorique courant. Réintégrations, déductions et impôt théorique sont '
        'déclarés explicitement avec leur source, sans taux, avantage ou régime '
        'déduit. Base documentaire = courant + réintégrations − déductions ; '
        'courant après impôt déclaré = courant − impôt théorique déclaré. '
        'Ces équations ne calculent ni IS dû, ni liquidation, ni paiement. '
        'Une case vide reste inconnue ; néant ne vaut pas zéro. B13-N/B13-N1 '
        'sont des identifiants internes, sans validation fiscale officielle. '
        'Contrôles figés de la version conservée, distincts du brouillon. '
        'Aucune donnée du Journal courant utilisée ou modifiée.')


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    colonnes = [
        {'cle': 'nature', 'label': 'Désignation de la synthèse', 'type': 'text'},
        {'cle': 'reintegrations', 'label': 'Réintégrations courantes déclarées', 'type': 'number'},
        {'cle': 'deductions', 'label': 'Déductions courantes déclarées', 'type': 'number'},
        {'cle': 'impot_theorique', 'label': 'Impôt théorique courant déclaré', 'type': 'number'},
        {'cle': 'regime_avantages', 'label': 'Régime et avantages à documenter', 'type': 'text'},
    ]
    return [{'code': code, 'groupe': 'B', 'titre': 'Résultat courant — ' + ('N' if p == 'n' else 'N-1'),
             'colonnes_saisie': deepcopy(colonnes)} for code, p in PERIODES.items()]


def sources(dossier):
    resultat = {}
    for p in ('n', 'n1'):
        contenu = dossier['contenu']
        rows = contenu.get('sources', {}).get(p)
        cpc = (contenu.get('preparation', {}).get('etats' if p == 'n' else 'etats_n1') or {}).get('cpc')
        disponible = (isinstance(rows, list) and all(isinstance(r, dict) and isinstance(r.get('compte'), str)
            and all(r.get(k) is not None and r.get(k) != '' for k in ('debit', 'credit')) for r in rows)
            and bool(cpc) and cpc.get('disponible') is not False and not cloture_technique(dossier, p))
        resultat[p] = {'disponible': bool(disponible)}
    return resultat


def normaliser(dossier, tables):
    resultat = commun.normaliser(dossier, tables, referentiel=catalogue)
    disponibles = sources(dossier)
    for table in resultat:
        if len(table['lignes']) > 1:
            raise ValueError('Une seule ligne de synthèse par période est autorisée ; agréger sur un justificatif explicite.')
        if not disponibles[PERIODES[table['code']]]['disponible'] and (
                table['lignes'] or table['statut'] != 'a_completer' or table['justification']):
            raise ValueError('Source détaillée/CPC de cette période indisponible ; aucune donnée fiscale rattachée ne peut être conservée.')
        for row in table['lignes']:
            if not row['nature'] or not row['reference_source']:
                raise ValueError('Désignation et référence de source requises pour toute synthèse fiscale, même partielle.')
    return resultat


def calculer_controles(dossier, demande):
    # Réutilisation du détail exact B11 et de sa garde du CPC techniquement soldé.
    bases = detail_cpc(dossier)['periodes']
    resultat = {}
    f = lambda v: None if v is None else format(v, '.2f')
    with localcontext() as ctx:
        ctx.prec = 60
        for table in demande['tables']:
            p = PERIODES[table['code']]
            base = bases[p]
            if cloture_technique(dossier, p):
                base = {**base, 'disponible': False, 'lignes': [],
                        'motif': 'Classes6/7 soldées et résultat119 présent : balance avant clôture technique requise.'}
            row = table['lignes'][0] if table['lignes'] else {}
            courant = impots = reference = None
            lignes = []
            if base['disponible']:
                lignes = [deepcopy(r) for r in base['lignes'] if r['compte'].startswith(('61', '63', '67', '71', '73'))]
                courant = sum((Decimal(r['montant']) * (-1 if r['compte'].startswith(('61', '63')) else 1)
                               for r in lignes if not r['compte'].startswith('67')), Decimal('0.00'))
                impots = sum((Decimal(r['montant']) for r in lignes if r['compte'].startswith('67')), Decimal('0.00'))
                cpc = dossier['contenu']['preparation']['etats' if p == 'n' else 'etats_n1']['cpc']
                if cpc.get('VII') is not None:
                    reference = Decimal(str(cpc['VII']))
                    if not reference.is_finite():
                        raise ValueError('Résultat courant CPC conservé non fini.')
            ri, ded, impot = (None if row.get(k) is None else Decimal(row[k])
                             for k in ('reintegrations', 'deductions', 'impot_theorique'))
            imposable = None if courant is None or ri is None or ded is None else courant + ri - ded
            apres = None if courant is None or impot is None else courant - impot
            alertes = []
            if table['statut'] == 'neant_declare' and courant not in (None, Decimal(0)):
                alertes.append('Néant déclaré malgré un résultat courant non nul ; aucune hypothèse fiscale égale à zéro déduite.')
            if reference is not None and courant != reference:
                alertes.append('Écart entre le détail source et le CPC VII conservé ; à justifier sans correction automatique.')
            resultat[p] = {'disponible': base['disponible'], 'motif': base['motif'], 'lignes': lignes,
                'resultat_courant': f(courant), 'cpc_resultat_courant': f(reference),
                'ecart_courant': f(None if courant is None or reference is None else courant - reference),
                'impots_comptabilises_67': f(impots), 'reintegrations': f(ri), 'deductions': f(ded),
                'impot_theorique_declare': f(impot), 'base_courante_documentaire': f(imposable),
                'courant_apres_impot_declare': f(apres), 'alertes': alertes}
    return {'methode': 'courant_61_63_71_73_et_hypotheses_sourcees_decimal_v1',
            'periodes': resultat, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC) or {}
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue,
                             note=bloc.get('note_conservee', NOTE))
    vue['sources'] = sources(dossier)
    vue['controle_resultat_courant'] = deepcopy(bloc.get('controle_resultat_courant'))
    notes = dossier['contenu'].get('notes_etic_documentaires', {}).get('lignes', [])
    if any(r['code'] == 'B13' and r['statut'] == 'non_applicable' for r in notes) and any(t['lignes'] for t in vue['tables']):
        vue['alertes'].append('La note B13 est non applicable alors que des hypothèses fiscales sont déclarées ; revoir les deux compléments.')
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC,
        normalisation=normaliser, referentiel=catalogue,
        enrichir=lambda d, q: {'controle_resultat_courant': calculer_controles(d, q), 'note_conservee': NOTE})
