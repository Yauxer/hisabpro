"""CM externe2026 : calcul partagé, qualifications déclarées et versions figées."""
from copy import deepcopy
from decimal import Decimal, localcontext
from services import balance_etic_tables_service as commun
from services.balance_import_service import montant_import
from services.balance_resultat_courant_service import sources
from services.balance_contexte_fiscal_service import source_b12
from services.fiscalite_cm_service import calculer_base_cm, calculer_cotisation_minimale, FAMILLES_CM

BLOC = 'cotisation_minimale_documentaire'
REGIME = 'IS hors forfait non-résident'
SOURCE = {'titre': 'CGI 2026, article 144-I A à D', 'pages_imprimees': '268-270',
          'editeur': 'DGI, document republié par le CRI Casablanca-Settat',
          'notice_url': 'https://casainvest.ma/fr/node/719',
          'url': 'https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf',
          'sha256': 'fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1'}
LIBELLES = {'base_comptable_brute': 'Base CM comptable brute', 'base_exclue': 'Exclusions déclarées et justifiées',
    'base_apres_exclusion': 'Base après exclusions', 'base_taux_reduit_015': 'Base déclarée au taux réduit 0,15 %',
    'base_taux_standard_025': 'Base au taux standard 0,25 %', 'cm_part_standard': 'CM proportionnelle standard',
    'cm_part_reduite': 'CM proportionnelle réduite', 'cm_calculee': 'CM proportionnelle totale',
    'minimum_3000': 'Minimum de perception retenu', 'cm_exigible': 'CM proposée selon qualifications déclarées',
    'is_theorique_b12': 'IS théorique B12 selon taux déclaré',
    'impot_avant_imputations_propose': 'Maximum IS théorique / CM proposé avant imputations'}
NOTE = ('CM externe 2026 en MAD, depuis la seule balance N conservée avant clôture technique. '
    'Calcul partagé avec le moteur CM existant, CGI 2026 article 144-I. Les soldes des familles '
    '711/712,718,716,732/733/738,756/7586 forment la base comptable indicative ; les autres '
    'produits restent visibles hors base. Leur qualification fiscale et les exclusions sont '
    'à justifier. Le régime IS hors forfait non-résident, les exclusions, la base au taux '
    'réduit, l’exonération totale et celle du minimum sont explicitement déclarés, jamais '
    'déduits du secteur, de l’âge de la société ou de son activité. Une case vide ou néant '
    'ne vaut pas zéro/non. Hors exercice2026 ou source indisponible, aucun calcul proposé. '
    'CM et maximum IS/CM sont des propositions conditionnelles ; le taux B12 reste déclaré, '
    'non qualifié automatiquement. CSS, crédits, acomptes et solde final restent distincts '
    'et ne sont pas liquidés ici. Aucun paiement, écriture ou liquidation confirmé, aucun '
    'prêt à déposer. Le contexte fiscal documentaire préexistant reste inchangé.')


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc: return deepcopy(bloc['catalogue'])
    return [{'code': 'CM-N', 'groupe': 'Interne', 'titre': 'Calcul de CM qualifié — N 2026',
        'colonnes_saisie': [
            {'cle': 'nature', 'label': 'Désignation de la qualification CM', 'type': 'text'},
            {'cle': 'regime', 'label': 'Périmètre fiscal déclaré', 'type': 'text'},
            {'cle': 'base_exclue', 'label': 'Base exclue et justifiée', 'type': 'number'},
            {'cle': 'base_reduite', 'label': 'Base éligible au taux réduit 0,15 %', 'type': 'number'},
            {'cle': 'exoneration_totale', 'label': 'Exonération totale de CM justifiée', 'type': 'text'},
            {'cle': 'minimum_exonere', 'label': 'Exonération du minimum de perception justifiée', 'type': 'text'}]}]


def normaliser(dossier, tables):
    resultat = commun.normaliser(dossier, tables, referentiel=catalogue)
    t = resultat[0]
    if len(t['lignes']) > 1: raise ValueError('Une seule qualification CM par préparation est autorisée.')
    for r in t['lignes']:
        if not r['nature'] or not r['reference_source']:
            raise ValueError('Désignation et référence des justificatifs CM requises, même pour une qualification partielle.')
        if r['regime'] not in ('', REGIME): raise ValueError('Ce calcul couvre uniquement le périmètre IS hors forfait non-résident déclaré.')
        for cle in ('exoneration_totale', 'minimum_exonere'):
            if r[cle] not in ('', 'oui', 'non'): raise ValueError('Exonération : choisir explicitement oui ou non, ou laisser à qualifier.')
    return resultat


def calculer_controles(dossier, demande):
    t = demande['tables'][0];r = t['lignes'][0] if t['lignes'] else {}
    disponible = sources(dossier)['n']['disponible']
    exercice = dossier.get('exercice', dossier['contenu'].get('exercice'))
    annee = type(exercice) is int and exercice == 2026
    montants = {k: None for k in LIBELLES};lignes = [];alertes = []
    origine_b12 = source_b12(dossier)
    with localcontext() as ctx:
        ctx.prec = 60
        produits = {}
        if disponible:
            for ligne in dossier['contenu']['sources']['n']:
                code = ligne['compte']
                if code.startswith('7'):
                    produits[code] = produits.get(code, Decimal(0)) + montant_import(ligne['credit'], code) - montant_import(ligne['debit'], code)
            for code, montant in sorted(produits.items()):
                famille = next((lib for _k, lib, prefixes in FAMILLES_CM if code.startswith(prefixes)), None)
                lignes.append({'compte': code, 'montant': format(montant, '.2f'), 'retenu_base': famille is not None,
                    'famille': famille or 'Hors familles de la base CM du moteur ; qualification à revoir'})
            montants['base_comptable_brute'] = calculer_base_cm(produits)['base_comptable_brute']
        complet = t['statut'] == 'documente' and r.get('regime') == REGIME and all(
            r.get(k) is not None and r.get(k) != '' for k in ('base_exclue', 'base_reduite', 'exoneration_totale', 'minimum_exonere'))
        if not disponible: alertes.append('Source N/CPC indisponible ou soldée techniquement ; fournir la balance avant clôture.')
        if not annee: alertes.append('Référentiel vérifié pour2026 uniquement ; aucun calcul CM proposé pour cet exercice.')
        if not complet: alertes.append('Qualification CM incomplète ou non documentée ; aucun paramètre inconnu remplacé par zéro ou non.')
        for cle, champ in [('base_exclue','base_exclue'),('base_taux_reduit_015','base_reduite')]:
            montants[cle] = None if r.get(champ) is None else Decimal(r[champ])
        if disponible and annee and complet:
            is_b12 = None if not origine_b12 else origine_b12['is_theorique_taux_declare']
            calc = calculer_cotisation_minimale(produits_par_compte=produits, is_theorique=is_b12 or 0,
                base_exclue=r['base_exclue'], base_taux_reduit_015=r['base_reduite'],
                exoneration_totale=r['exoneration_totale']=='oui', minimum_3000_exonere=r['minimum_exonere']=='oui')
            for k in montants.keys() & calc.keys(): montants[k] = calc[k]
            if is_b12 is not None:
                montants['is_theorique_b12'] = Decimal(is_b12)
                montants['impot_avant_imputations_propose'] = calc['impot_du_avant_acomptes']
            else: alertes.append('IS théorique B12 indisponible ; CM calculable seule, maximum IS/CM indisponible.')
        # Les ajustements incohérents sont refusés même si une autre qualification reste inconnue.
        brute = montants['base_comptable_brute'];exclue = montants['base_exclue'];reduite = montants['base_taux_reduit_015']
        if brute is not None and exclue is not None and exclue > brute: raise ValueError('La base exclue dépasse la base comptable CM.')
        if brute is not None and exclue is not None and reduite is not None and reduite > brute - exclue:
            raise ValueError('La base réduite dépasse la base CM après exclusions.')
        return {'methode': 'moteur_cm_partage_qualifications_declarees_2026_v1', 'source_n_disponible': disponible,
            'exercice_couvert': annee, 'qualification_complete_declaree': bool(complet),
            'montants': {k: None if v is None else format(v, '.2f') for k,v in montants.items()},
            'lignes_sources': lignes, 'source_b12': origine_b12, 'reference_juridique': deepcopy(SOURCE),
            'alertes': alertes, 'solde_final': None, 'css': None, 'credits': None, 'acomptes': None,
            'liquidation_confirmee': False, 'paiement_confirme': False, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC) or {}
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue, note=bloc.get('note_conservee', NOTE))
    vue['controle_cm'] = deepcopy(bloc.get('controle_cm'))
    c = vue['controle_cm']
    vue['source_b12_modifiee'] = bool(c and (c['source_b12'] or {}).get('cle') != (source_b12(dossier) or {}).get('cle'))
    if vue['source_b12_modifiee']:
        vue['alertes'].append('B12 a changé : maximum IS/CM conservé pour mémoire. Revoir et conserver une nouvelle qualification CM ; aucun recalcul de l’ancienne version.')
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC, normalisation=normaliser,
        referentiel=catalogue, enrichir=lambda d,q: {'controle_cm': calculer_controles(d,q), 'note_conservee': NOTE})
