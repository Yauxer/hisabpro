"""Compléments documentaires sur sources importées figées, jamais sur le Journal."""
from copy import deepcopy
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
import models
from services.balance_import_service import lire_preparation, empreinte_preparation, montant_import

# Même sélection de comptes que les B6/B7 existants dans etic_service._automatiques.
# Pas de lecture du plan, des factures ni des échéances de la société courante.
PREFIXES = {'B6': ('241', '248', '34'), 'B7': ('14', '44', '55')}
CHAMPS = ('plus_un_an', 'moins_un_an', 'echues', 'devises',
          'etat_organismes_publics', 'entreprises_liees', 'effets')
LIBELLES = ('Plus d’un an', 'Moins d’un an', 'Échues', 'En devises',
            'État / organismes publics', 'Entreprises liées', 'Effets')
NOTE = ('Préparation documentaire depuis la seule balance N conservée. '
        'Les montants non renseignés sont inconnus, jamais présumés nuls. '
        'Le reliquat reste à qualifier. Les analyses complémentaires peuvent se recouper. '
        'Aucune écriture, échéance de facture ou ETIC officielle complète n’est créée.')


def lignes_sources(dossier):
    rows = dossier['contenu'].get('sources', {}).get('n')
    if rows is None:
        return None
    resultat = []
    for source in rows:
        compte = source['compte']
        solde = Decimal(source['debit']) - Decimal(source['credit'])
        for section, prefixes in PREFIXES.items():
            if compte.startswith(prefixes) and solde:
                total = solde if section == 'B6' else -solde
                resultat.append({'section': section, 'compte': compte, 'total': format(total, '.2f'),
                                 'ventilable': total > 0})
    return sorted(resultat, key=lambda r: (r['section'], r['compte']))


def presentation(dossier):
    bloc = dossier['contenu'].get('echeances_documentaires')
    rows = lignes_sources(dossier)
    saisis = {(r['section'], r['compte']): r for r in (bloc or {}).get('lignes', [])}
    result = []
    for source in rows or []:
        saisi = saisis.get((source['section'], source['compte']), {})
        montants = {k: saisi.get(k) for k in CHAMPS}
        qualifie = sum((Decimal(montants[k]) for k in CHAMPS[:3] if montants[k] is not None), Decimal(0))
        total = Decimal(source['total'])
        result.append({**source, **montants, 'justification': saisi.get('justification', ''),
                       'qualifie': format(qualifie, '.2f') if source['ventilable'] else None,
                       'reliquat': format(total - qualifie, '.2f') if source['ventilable'] else None})
    return {'lignes': result, 'sources_disponibles': rows is not None,
            'parent': (bloc or {}).get('parent'), 'note': NOTE}


def normaliser(dossier, lignes):
    sources = lignes_sources(dossier)
    if sources is None:
        raise ValueError('Sources détaillées absentes : réimporter explicitement la balance avant tout complément.')
    autorises = {(r['section'], r['compte']): r for r in sources}
    resultat, vus = [], set()
    for row in lignes:
        key = (row.section, row.compte)
        if key in vus:
            raise ValueError('Compte en doublon dans la même section documentaire.')
        vus.add(key)
        source = autorises.get(key)
        if not source or not source['ventilable']:
            raise ValueError('Compte absent des sources ventilables de cette préparation.')
        valeurs = {}
        for k in CHAMPS:
            v = getattr(row, k)
            valeurs[k] = None if v is None or v == '' else format(montant_import(v, row.compte + ' ' + k), '.2f')
        justification = row.justification.strip()
        if any(v is not None for v in valeurs.values()) and not justification:
            raise ValueError('Justification ou référence de source requise pour les montants renseignés.')
        total = Decimal(source['total'])
        qualifie = sum((Decimal(valeurs[k]) for k in CHAMPS[:3] if valeurs[k] is not None), Decimal(0))
        if qualifie > total or any(Decimal(valeurs[k]) > total for k in CHAMPS[3:] if valeurs[k] is not None):
            raise ValueError('La ventilation ou une analyse dépasse le solde du compte conservé.')
        resultat.append({'section': row.section, 'compte': row.compte, **valeurs, 'justification': justification})
    return sorted(resultat, key=lambda r: (r['section'], r['compte']))


def conserver(db, user, preparation_id, data):
    sid = user['societe_id']
    # Même verrou société que la création des préparations : numéros et rejeux sérialisés.
    societe = db.query(models.Societe).filter_by(id=sid).with_for_update().first()
    if not societe:
        raise HTTPException(404, 'Société introuvable.')
    if societe.devise != 'MAD':
        raise HTTPException(409, 'Complément limité aux balances explicitement tenues en MAD ; aucune conversion présumée.')
    row = db.query(models.LiasseBalancePreparation).filter_by(id=preparation_id, societe_id=sid).first()
    if not row:
        raise HTTPException(404, 'Préparation introuvable dans cette société.')
    try:
        dossier = lire_preparation(row)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if data.empreinte_parent != dossier['empreinte_sha256']:
        raise HTTPException(409, 'La préparation sélectionnée ne correspond plus à la source attendue.')
    try:
        lignes = normaliser(dossier, data.lignes)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    bloc = {'schema_version': 1, 'cle': str(data.cle),
            'parent': {'id': row.id, 'version': row.version, 'empreinte_sha256': row.empreinte_sha256},
            'lignes': lignes}
    ancien = db.query(models.LiasseBalancePreparation).filter(
        models.LiasseBalancePreparation.societe_id == sid,
        models.LiasseBalancePreparation.contenu['echeances_documentaires']['cle'].as_string() == str(data.cle)).first()
    if ancien:
        try:
            sauvegarde = lire_preparation(ancien)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if sauvegarde['contenu']['echeances_documentaires'] != bloc:
            raise HTTPException(409, 'Clé déjà utilisée pour un autre complément documentaire.')
        return sauvegarde
    contenu = deepcopy(row.contenu)
    contenu['echeances_documentaires'] = bloc
    latest = db.query(func.max(models.LiasseBalancePreparation.version)).filter_by(
        societe_id=sid, exercice=row.exercice).scalar() or 0
    nouveau = models.LiasseBalancePreparation(societe_id=sid, exercice=row.exercice,
        exercice_id=row.exercice_id, version=latest + 1, contenu=contenu,
        empreinte_sha256=empreinte_preparation(contenu), created_by=user['id'])
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return lire_preparation(nouveau)
