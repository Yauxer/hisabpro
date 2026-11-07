"""Acomptes externes : versements et affectations déclarés, jamais réalloués."""
from copy import deepcopy
from datetime import date
from decimal import Decimal, localcontext
import re

from services import balance_etic_tables_service as commun
from services.balance_credits_is_service import SOURCE as SOURCE_CGI
from services.fiscalite_acomptes_service import construire_acomptes, echeances_acomptes

BLOC = 'acomptes_is_documentaires'
REGIME = 'Société relevant de l’IS'
MODES = ('Quatre acomptes — exercice de douze mois', 'Minimum CM3000 — versement unique')
SOURCE = {**SOURCE_CGI, 'titre': 'CGI2026, article170 et article247-XXXVII-B', 'pages_imprimees': '321-323, 478'}
LIBELLES = {
    'versements_declares': 'Versements effectifs déclarés',
    'excedent_anterieur_impute': 'Excédent antérieur affecté aux acomptes',
    'retenues_affectees': 'Retenues affectées aux acomptes',
    'excedent_anterieur_disponible': 'Excédent antérieur disponible avant affectations',
    'excedent_anterieur_restant': 'Excédent antérieur restant après affectations',
    'ecart_retenues': 'Écart retenues affectées moins déjà utilisées côté crédits',
    'acomptes_proposes': 'Acomptes imputables proposés après qualifications',
    'total_echeances_calcule': 'Total des échéances calculées',
    'ecart_arrondi_reference': 'Écart total échéances moins référence annuelle',
}
NOTE = (
    'Acomptes externes2026, codes AP internes. Les versements, excédents antérieurs '
    'et retenues affectées sont saisis distinctement et sourcés ; aucune allocation '
    'automatique entre les échéances. Chaque retenue affectée désigne exactement '
    'un justificatif de crédits qualifié et doit recouper sa part déjà utilisée. '
    'Un excédent antérieur relève explicitement de l’article170-IV, exercice '
    'd’origine depuis2015 et solde disponible justifié ; aucun report ancien '
    'ou crédit de CM présumé. L’exhaustivité et les rattachements sont déclarés. '
    'Le calendrier couvre ici les exercices de douze mois, référence annuelle '
    'manuelle qualifiée au taux applicable2026, ou minimum CM3000 en versement '
    'unique. Un ancien impôt N-1 n’est pas automatiquement la référence2026. '
    'Exercice court, exonération ou régime spécifique : calendrier à qualifier, '
    'sans fabriquer quatre échéances. Les montants effectivement documentés '
    'restent distincts du calendrier. La date de contrôle est explicitement '
    'saisie et figée ; aucun statut historique ne dépend de la date du jour. '
    'Néant seul ne vaut pas zéro. Aucun paiement, affectation, écriture ou '
    'liquidation confirmé ; CSS distincte, aucun prêt à déposer.'
)


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    profil = [('nature', 'Désignation du profil acomptes', 'text'), ('regime', 'Périmètre IS des acomptes', 'text'),
        ('mode', 'Régime de versements déclaré', 'text'), ('reference_annuelle', 'Référence annuelle ajustée2026 justifiée', 'number'),
        ('reference_qualifiee', 'Référence annuelle fiscalement qualifiée', 'text'),
        ('exercice_reference', 'Exercice de référence déclaré', 'text'), ('dernier_clos_confirme', 'Dernier exercice clos confirmé', 'text'),
        ('excedent_anterieur_disponible', 'Excédent antérieur disponible avant acomptes', 'number'),
        ('origine_excedent', 'Exercice d’origine de l’excédent170-IV', 'text'),
        ('excedent_qualifie', 'Excédent170-IV et solde disponible qualifiés', 'text'),
        ('exhaustivite', 'Mouvements et affectations exhaustifs', 'text'),
        ('absence_mouvements', 'Absence de tout mouvement confirmée', 'text'), ('date_controle', 'Date de contrôle déclarée', 'date')]
    lignes = [('nature', 'Désignation du mouvement acompte', 'text'), ('numero', 'Numéro de l’acompte', 'text'),
        ('date_mouvement', 'Date du mouvement justifiée', 'date'), ('verse', 'Versement effectif', 'number'),
        ('credit_anterieur', 'Excédent antérieur affecté', 'number'), ('retenue', 'Retenue affectée', 'number'),
        ('reference_credit', 'Référence exacte du justificatif crédit', 'text'), ('rattachement_confirme', 'Rattachement et justificatif confirmés', 'text')]
    return [{'code': code, 'groupe': 'Interne', 'titre': titre,
        'colonnes_saisie': [{'cle': k, 'label': label, 'type': typ} for k, label, typ in cols]}
        for code, titre, cols in [('AP-PROFIL', 'Profil et référence annuelle des acomptes', profil), ('AP-LIGNES', 'Versements et affectations justifiés', lignes)]]


def normaliser(dossier, tables):
    ts = commun.normaliser(dossier, tables, referentiel=catalogue)
    if len(ts[0]['lignes']) > 1 or len(ts[1]['lignes']) > 50:
        raise ValueError('Un profil et cinquante mouvements acomptes maximum.')
    vus = set()
    for t in ts:
        for r in t['lignes']:
            if not r['nature'] or not r['reference_source']:
                raise ValueError('Désignation et référence source requises, même pour une ligne partielle.')
            for k in ('reference_qualifiee', 'dernier_clos_confirme', 'excedent_qualifie', 'exhaustivite', 'absence_mouvements', 'rattachement_confirme'):
                if k in r and r[k] not in ('', 'oui', 'non'):
                    raise ValueError('Qualification acomptes : oui, non ou champ vide.')
            for k in ('date_mouvement', 'date_controle'):
                if r.get(k):
                    try:
                        date.fromisoformat(r[k])
                        if not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', r[k]):
                            raise ValueError()
                    except ValueError as exc:
                        raise ValueError('Date ISO valide requise : ' + k + '.') from exc
            if t['code'] == 'AP-PROFIL':
                if r['regime'] not in ('', REGIME) or r['mode'] not in ('', *MODES):
                    raise ValueError('Périmètre ou régime de versements non couvert.')
                for k in ('exercice_reference', 'origine_excedent'):
                    if r[k] and (not re.fullmatch('[0-9]{4}', r[k]) or not 1900 <= int(r[k]) <= dossier['exercice']):
                        raise ValueError('Exercice source : année de quatre chiffres au plus égale à la préparation.')
                if r['mode'] == MODES[1] and r['reference_annuelle'] is not None and Decimal(r['reference_annuelle']) != 3000:
                    raise ValueError('Le régime minimum CM3000 nécessite une référence explicite de3000MAD.')
            else:
                if r['numero'] not in ('', '1', '2', '3', '4'):
                    raise ValueError('Numéro acompte attendu :1,2,3 ou4.')
                ref = r['reference_source'].casefold()
                if ref in vus:
                    raise ValueError('Référence de mouvement acompte en doublon.')
                vus.add(ref)
    profil = ts[0]['lignes'][0] if ts[0]['lignes'] else {}
    if profil.get('date_controle') and profil['date_controle'] < dossier['contenu']['periode']['debut']:
        raise ValueError('La date de contrôle ne peut pas précéder l’ouverture de la période source.')
    if profil.get('absence_mouvements') == 'oui' and ts[1]['lignes']:
        raise ValueError('Absence de mouvements incompatible avec les lignes saisies.')
    return ts


def source_credits(dossier):
    bloc = dossier['contenu'].get('credits_is_documentaires')
    if not bloc:
        return None
    c = bloc['controle_credits']; lignes = bloc['tables'][1]['lignes']
    return {'cle': bloc['cle'], 'qualifie': bool(c['qualification_complete_declaree'] and c['exercice_couvert']),
        'deja_impute_acomptes': c['montants']['deja_impute_acomptes'],
        'lignes': [{'reference': r['reference_source'], 'deja_impute': r['deja_impute_acomptes'], 'statut': ctrl['statut']}
                   for r, ctrl in zip(lignes, c['lignes'])]}


def calculer_controles(dossier, demande):
    tp, tl = demande['tables']; p = tp['lignes'][0] if tp['lignes'] else {}
    periode = deepcopy(dossier['contenu']['periode']); couvert = dossier['exercice'] == 2026
    profil = tp['statut'] == 'documente' and p.get('regime') == REGIME and p.get('exhaustivite') == 'oui' and bool(p.get('date_controle'))
    absence = profil and p.get('absence_mouvements') == 'oui' and tl['statut'] == 'neant_declare' and not tl['lignes']
    src = source_credits(dossier); alertes = []; details = []; rapprochement = []; echeancier = []
    with localcontext() as ctx:
        ctx.prec = 60
        def somme(k):
            if absence:
                return Decimal('0.00')
            if not tl['lignes'] or any(r[k] is None for r in tl['lignes']):
                return None
            return sum((Decimal(r[k]) for r in tl['lignes']), Decimal('0.00'))
        verse, ant, ras = (somme(k) for k in ('verse', 'credit_anterieur', 'retenue'))
        for i, r in enumerate(tl['lignes'], 1):
            qualifie = (tl['statut'] == 'documente' and all(r[k] is not None for k in ('verse', 'credit_anterieur', 'retenue'))
                and bool(r['numero']) and (p.get('mode') != MODES[1] or r['numero'] == '1') and bool(r['date_mouvement']) and bool(p.get('date_controle'))
                and periode['debut'] <= r['date_mouvement'] <= p['date_controle'] and r['rattachement_confirme'] == 'oui')
            details.append({'ligne': i, 'qualifie_declare': bool(qualifie)})
        complet = bool(absence or (profil and p.get('absence_mouvements') == 'non' and tl['statut'] == 'documente'
                                  and details and all(r['qualifie_declare'] for r in details)))
        disponible = Decimal(p['excedent_anterieur_disponible']) if p.get('excedent_anterieur_disponible') is not None else None
        if disponible is not None and ant is not None and ant > disponible:
            raise ValueError('Les affectations dépassent l’excédent antérieur disponible déclaré.')
        ant_ok = ant == 0 or (ant is not None and disponible is not None and p.get('excedent_qualifie') == 'oui'
            and bool(p.get('origine_excedent')) and 2015 <= int(p['origine_excedent']) <= dossier['exercice'])
        ecart = ras - Decimal(src['deja_impute_acomptes']) if src and src['deja_impute_acomptes'] is not None and ras is not None else None
        refs = {r['reference_credit'].strip().casefold() for r in tl['lignes'] if r['retenue'] is not None and Decimal(r['retenue']) > 0}
        connus = {r['reference'].casefold() for r in (src or {}).get('lignes', [])}
        ras_ok = ras == 0 if not src else bool(src['qualifie'] and ecart == 0 and not refs - connus)
        if src:
            for credit in src['lignes']:
                affectes = [r['retenue'] for r in tl['lignes'] if r['reference_credit'].strip().casefold() == credit['reference'].casefold()]
                montant = None if any(v is None for v in affectes) else sum((Decimal(v) for v in affectes), Decimal('0.00'))
                attendu = None if credit['deja_impute'] is None else Decimal(credit['deja_impute'])
                ok = montant is not None and attendu is not None and montant == attendu and (montant == 0 or credit['statut'] == 'qualifie_declare')
                ras_ok = ras_ok and ok
                rapprochement.append({'reference': credit['reference'], 'attendu': None if attendu is None else format(attendu, '.2f'),
                    'affecte': None if montant is None else format(montant, '.2f'), 'coherent': bool(ok)})
        qualifie = bool(couvert and complet and ant_ok and ras_ok)
        vals = {'versements_declares': verse, 'excedent_anterieur_impute': ant, 'retenues_affectees': ras,
            'excedent_anterieur_disponible': disponible,
            'excedent_anterieur_restant': None if disponible is None or ant is None else disponible - ant,
            'ecart_retenues': ecart,
            'acomptes_proposes': verse + ant + ras if qualifie else None, 'total_echeances_calcule': None, 'ecart_arrondi_reference': None}
        calendrier = (couvert and tp['statut'] == 'documente' and p.get('regime') == REGIME and p.get('reference_qualifiee') == 'oui'
            and p.get('dernier_clos_confirme') == 'oui' and bool(p.get('exercice_reference'))
            and p.get('reference_annuelle') is not None and bool(p.get('date_controle')) and p.get('mode') in MODES
            and echeances_acomptes(date.fromisoformat(periode['debut']))[-1].isoformat() == periode['fin'])
        if calendrier:
            schema = construire_acomptes(date_debut=date.fromisoformat(periode['debut']), reference={'disponible': True, 'montant_annuel': p['reference_annuelle']},
                paiements=[], excedent_precedent=0, credits_ras_deja_imputes=0, date_reference=date.fromisoformat(p['date_controle']))
            for t in schema['acomptes'][:1 if p['mode'] == MODES[1] else 4]:
                du = Decimal('3000.00') if p['mode'] == MODES[1] else t['montant_du']
                rs = [r for r in tl['lignes'] if r['numero'] == str(t['numero'])]
                couverture = sum((sum(Decimal(r[k]) for k in ('verse', 'credit_anterieur', 'retenue')) for r in rs), Decimal('0.00')) if qualifie else None
                reste = max(Decimal('0.00'), du - couverture) if couverture is not None else None
                en_retard = t['date_echeance'].isoformat() < p['date_controle']
                statut = 'a_qualifier' if reste is None else 'couvert_declare' if reste == 0 else 'partiel_en_retard' if couverture > 0 and en_retard else 'en_retard' if en_retard else 'partiel' if couverture > 0 else 'a_venir'
                echeancier.append({'numero': t['numero'], 'date_echeance': t['date_echeance'].isoformat(), 'du': format(du, '.2f'),
                    'couverture_declaree': None if couverture is None else format(couverture, '.2f'), 'reste': None if reste is None else format(reste, '.2f'), 'statut': statut})
        if calendrier:
            vals['total_echeances_calcule'] = sum((Decimal(r['du']) for r in echeancier), Decimal('0.00'))
            vals['ecart_arrondi_reference'] = vals['total_echeances_calcule'] - Decimal(p['reference_annuelle'])
            if vals['ecart_arrondi_reference'] != 0:
                alertes.append('Les quarts arrondis au centime diffèrent de la référence annuelle ; écart explicite, aucune répartition du reliquat inventée.')
        if not qualifie:
            alertes.append('Mouvements, excédent ou rapprochement des retenues incomplets : aucun total imputable proposé ; aucun zéro inventé.')
        if not calendrier:
            alertes.append('Calendrier à qualifier : référence2026, dernier clos, régime de versements ou exercice de douze mois non documenté. Les versements ne sont pas inventés.')
        if ras_ok is False:
            alertes.append('Les affectations de retenues ne recoupent pas exactement leurs justificatifs qualifiés, y compris par référence ; aucun rapprochement global approximatif.')
        return {'methode': 'acomptes_justifies_sans_allocation_automatique_2026_v1', 'exercice': dossier['exercice'],
            'periode_source': periode, 'date_controle': p.get('date_controle') or None, 'qualification_complete_declaree': qualifie,
            'calendrier_disponible': bool(calendrier), 'absence_exhaustive_confirmee': bool(absence),
            'montants': {k: None if v is None else format(v, '.2f') for k, v in vals.items()},
            'lignes': details, 'rapprochement_retenues': rapprochement, 'echeancier': echeancier,
            'source_credits': src, 'reference_juridique': deepcopy(SOURCE), 'alertes': alertes,
            'solde_final': None, 'liquidation_confirmee': False, 'paiement_confirme': False, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC) or {}
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue, note=bloc.get('note_conservee', NOTE))
    c = vue['controle_acomptes'] = deepcopy(bloc.get('controle_acomptes'))
    vue['source_credits_modifiee'] = bool(c and (c['source_credits'] or {}).get('cle') != (source_credits(dossier) or {}).get('cle'))
    if vue['source_credits_modifiee']:
        vue['alertes'].append('Les crédits qualifiés ont changé : contrôle acomptes conservé pour mémoire ; relire puis conserver une nouvelle qualification, sans recalcul historique.')
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC, normalisation=normaliser,
        referentiel=catalogue, enrichir=lambda d, q: {'controle_acomptes': calculer_controles(d, q), 'note_conservee': NOTE})
