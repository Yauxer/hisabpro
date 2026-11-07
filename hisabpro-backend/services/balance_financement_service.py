"""Financement documentaire : moteur partagé, flux explicites et calcul figé."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func
import models
from services.balance_import_service import lire_preparation, empreinte_preparation, montant_import
from services.liasse_service import calculer_tableau_financement

CHAMPS = (
    ('distributions_benefices', 'Distributions de bénéfices'),
    ('cessions_immobilisations_incorporelles', 'Cessions d’immobilisations incorporelles'),
    ('cessions_immobilisations_corporelles', 'Cessions d’immobilisations corporelles'),
    ('cessions_immobilisations_financieres', 'Cessions d’immobilisations financières'),
    ('cessions_immobilisations_non_ventilees', 'Cessions non ventilées — à classer'),
    ('recuperations_creances_immobilisees', 'Récupérations de créances immobilisées'),
    ('augmentations_capitaux_propres', 'Augmentations de capital / apports'),
    ('subventions_investissement_recues', 'Subventions d’investissement reçues'),
    ('augmentations_dettes_financement', 'Augmentations des dettes de financement'),
    ('acquisitions_immobilisations_incorporelles', 'Acquisitions d’immobilisations incorporelles'),
    ('acquisitions_immobilisations_corporelles', 'Acquisitions d’immobilisations corporelles'),
    ('acquisitions_immobilisations_financieres', 'Acquisitions d’immobilisations financières'),
    ('augmentations_creances_immobilisees', 'Augmentations des créances immobilisées'),
    ('reductions_capitaux_propres', 'Remboursements des capitaux propres'),
    ('remboursements_dettes_financement', 'Remboursements des dettes de financement'),
    ('emplois_non_valeurs', 'Emplois en non-valeurs'),
)
NOTE = ('Préparation documentaire du financement en MAD. Les flux ne sont jamais '
        'déduits des écarts de balances. Vide signifie inconnu ; zéro signifie déclaré '
        'explicitement avec sa source. Les totaux ne sont calculés que si tous les '
        'flux de la période et sa CAF sont connus. Aucun contrôle ne vaut validation '
        'fiscale ou dossier prêt à déposer. Les flux N-1 restent inconnus sans saisie propre.')


def normaliser(dossier, lignes):
    rows = {k: {'code': k, 'n': None, 'n1': None, 'justification_n': '', 'justification_n1': ''} for k, _ in CHAMPS}
    vus = set()
    n1 = dossier['contenu'].get('sources', {}).get('n1') is not None
    for row in lignes:
        if row.code not in rows or row.code in vus:
            raise ValueError('Flux inconnu ou en doublon.')
        vus.add(row.code)
        for periode in ('n', 'n1'):
            v = getattr(row, periode)
            justif = getattr(row, 'justification_' + periode).strip()
            montant = None if v is None or v == '' else format(montant_import(v, row.code), '.2f')
            if periode == 'n1' and not n1 and (montant is not None or justif):
                raise ValueError('Balance N-1 absente : aucun flux N-1 ne peut être déclaré pour cette préparation.')
            if montant is not None and not justif:
                raise ValueError('Justification ou référence de source requise, y compris pour un zéro déclaré.')
            rows[row.code][periode] = montant
            rows[row.code]['justification_' + periode] = justif
    return list(rows.values())


def calculer(dossier, lignes):
    contenu = dossier['contenu']; prep = contenu['preparation']; sources = contenu.get('sources', {})
    base = {'note': NOTE, 'lignes': [{**r, 'titre': dict(CHAMPS)[r['code']]} for r in lignes],
            'sources_disponibles': sources.get('n') is not None,
            'comparatif_disponible': sources.get('n1') is not None,
            'pret_a_deposer': False}
    if sources.get('n') is None:
        return {**base, 'tableau': None, 'caf': {'n': None, 'n1': None},
                'flux_renseignes': {'n': 0, 'n1': 0}, 'calcul_disponible': {'n': False, 'n1': False}}
    esgs = {'n': prep['etats']['esg'], 'n1': (prep.get('etats_n1') or {}).get('esg') or {}}
    caf = {p: e.get('caf') if e.get('disponible') is not False else None for p, e in esgs.items()}
    counts = {p: sum(r[p] is not None for r in lignes) for p in ('n', 'n1')}
    complets = {p: counts[p] == len(CHAMPS) and caf[p] is not None for p in ('n', 'n1')}
    def soldes(p):
        return {r['compte']: {k: Decimal(r[k]) for k in ('debit', 'credit')} for r in sources.get(p) or []}
    # Le moteur partagé fournit les masses du bilan même sans flux complets.
    # Ses valeurs par défaut de partieII sont masquées intégralement ci-dessous.
    tf = calculer_tableau_financement(soldes('n'), soldes('n1'),
        prep['etats']['cpc'], (prep.get('etats_n1') or {}).get('cpc') or {},
        {r['code']: r['n'] for r in lignes} if complets['n'] else None,
        {r['code']: r['n1'] for r in lignes} if complets['n1'] else None,
        n1_disponible=base['comparatif_disponible'])
    for p, key in [('n', 'montant'), ('n1', 'n1')]:
        if complets[p]:
            montant_caf = next(r[key] for r in tf['ressources'] if r['code'] == 'A1')
            if montant_caf is None or Decimal(str(montant_caf)) != Decimal(str(caf[p])):
                raise ValueError('CAF du moteur différente de l’ESG figé : réimporter explicitement la balance avant ce calcul.')
        else:
            for r in tf['ressources'] + tf['emplois']:
                r[key] = None
    if not complets['n']:
        for k in ('total_ressources', 'total_emplois', 'total_general_ressources', 'total_general_emplois',
                  'ecart_controle', 'ecart_total_general', 'controle'):
            tf[k] = None
    tf['source_flux'] = 'declarations_documentaires_expressement_justifiees'
    # Somme des seules rubriques mères, sans doubler les sous-postes. Aucune
    # variation N-1 n'est inventée sans balance N-2.
    for rows, key in [('ressources', 'total_ressources_n1'), ('emplois', 'total_emplois_n1')]:
        tf[key] = float(sum((Decimal(str(r['n1'])) for r in tf[rows] if r['total']), Decimal(0))) if complets['n1'] else None
    tf['ecart_nul'] = None if tf['ecart_controle'] is None else Decimal(str(tf['ecart_controle'])) == 0
    # Aucun nombre interne de la branche par défaut n'est présenté comme flux connu.
    tf['avertissements'] = tf['avertissements'] if complets['n'] else []
    # Les montants détaillés restent exacts sous forme de chaînes. Le moteur
    # partagé expose des agrégats numériques : au-delà de sa borne d'import
    # par montant, ne pas présenter des centimes potentiellement arrondis.
    def hors_borne(v):
        if isinstance(v, dict):return any(hors_borne(x) for x in v.values())
        if isinstance(v, list):return any(hors_borne(x) for x in v)
        return not isinstance(v, bool) and isinstance(v, (float, int)) and abs(Decimal(str(v))) > Decimal('9999999999999.99')
    if hors_borne(tf) or hors_borne(caf):
        return {**base, 'tableau': None, 'caf': {p: None if hors_borne(v) else v for p, v in caf.items()},
                'flux_renseignes': counts, 'calcul_disponible': {'n': False, 'n1': False},
                'motif_precision': 'Limite technique de précision des masses ou totaux dépassée (9 999 999 999 999,99 MAD). Les flux détaillés sont conservés exactement ; aucun total approximatif n’est présenté.'}
    return {**base, 'tableau': tf, 'caf': caf, 'flux_renseignes': counts, 'calcul_disponible': complets}


def presentation(dossier):
    bloc = dossier['contenu'].get('financement_documentaire')
    if bloc:
        return {**deepcopy(bloc['vue']), 'parent': deepcopy(bloc['parent']),
                'auteur': deepcopy(bloc['auteur']), 'conserve_le_utc': bloc['conserve_le_utc']}
    rows = [{'code': k, 'n': None, 'n1': None, 'justification_n': '', 'justification_n1': ''} for k, _ in CHAMPS]
    return {**calculer(dossier, rows), 'parent': None, 'auteur': None, 'conserve_le_utc': None}


def conserver(db, user, preparation_id, data):
    sid = user['societe_id']
    societe = db.query(models.Societe).filter_by(id=sid).with_for_update().first()
    if not societe:
        raise HTTPException(404, 'Société introuvable.')
    if societe.devise != 'MAD':
        raise HTTPException(409, 'Financement documentaire limité aux montants explicitement exprimés en MAD.')
    row = db.query(models.LiasseBalancePreparation).filter_by(id=preparation_id, societe_id=sid).first()
    if not row:
        raise HTTPException(404, 'Préparation introuvable dans cette société.')
    try:
        dossier = lire_preparation(row)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if data.empreinte_parent != dossier['empreinte_sha256']:
        raise HTTPException(409, 'Préparation différente de la source attendue.')
    if dossier['contenu'].get('sources', {}).get('n') is None:
        raise HTTPException(409, 'Sources détaillées absentes : réimporter explicitement la balance.')
    try:
        lignes = normaliser(dossier, data.lignes)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    demande = {'schema_version': 1, 'cle': str(data.cle),
               'parent': {'id': row.id, 'version': row.version, 'empreinte_sha256': row.empreinte_sha256},
               'lignes': lignes}
    ancien = db.query(models.LiasseBalancePreparation).filter(
        models.LiasseBalancePreparation.societe_id == sid,
        models.LiasseBalancePreparation.contenu['financement_documentaire']['cle'].as_string() == str(data.cle)).first()
    if ancien:
        try:
            saved = lire_preparation(ancien)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        bloc = saved['contenu']['financement_documentaire']
        if {k: bloc[k] for k in demande} != demande:
            raise HTTPException(409, 'Clé déjà utilisée pour d’autres flux documentaires.')
        return saved
    try:
        vue = calculer(dossier, lignes)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    acteur = db.query(models.Utilisateur).filter_by(id=user['id']).one()
    contenu = deepcopy(row.contenu)
    contenu['financement_documentaire'] = {**demande, 'vue': vue,
        'auteur': {'id': acteur.id, 'nom': acteur.nom},
        'conserve_le_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    latest = db.query(func.max(models.LiasseBalancePreparation.version)).filter_by(
        societe_id=sid, exercice=row.exercice).scalar() or 0
    nouveau = models.LiasseBalancePreparation(societe_id=sid, exercice=row.exercice,
        exercice_id=row.exercice_id, version=latest + 1, contenu=contenu,
        empreinte_sha256=empreinte_preparation(contenu), created_by=user['id'])
    db.add(nouveau);db.commit();db.refresh(nouveau)
    return lire_preparation(nouveau)
