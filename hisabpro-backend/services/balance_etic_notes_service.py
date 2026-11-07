"""Notes de travail ETIC sur une préparation figée, sans données présumées."""
from copy import deepcopy
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
import models
from services.balance_import_service import lire_preparation, empreinte_preparation
from services.etic_service import CATALOGUE_ETIC

NOTE = ('Notes documentaires de préparation, pas des tableaux ETIC complets. '
        'Une rubrique sans note reste à compléter. Non applicable est une déclaration '
        'explicite et justifiée, sans validation automatique. Aucune donnée du Journal '
        'ou de l’ETIC comptable n’est modifiée ; aucun état prêt à déposer n’est créé.')
STATUTS = {'a_completer': 'À compléter', 'renseigne': 'Note renseignée',
           'non_applicable': 'Non applicable — déclaré'}


def catalogue(dossier):
    bloc = dossier['contenu'].get('notes_etic_documentaires')
    # Les titres font partie du snapshot ; une évolution du catalogue ne réécrit
    # jamais les anciennes notes à la lecture ou à l'export.
    return deepcopy(bloc['catalogue'] if bloc else [
        {k: r[k] for k in ('code', 'groupe', 'titre')} for r in CATALOGUE_ETIC])


def presentation(dossier):
    bloc = dossier['contenu'].get('notes_etic_documentaires') or {}
    saisis = {r['code']: r for r in bloc.get('lignes', [])}
    lignes = [{**r, **saisis.get(r['code'], {
        'statut': 'a_completer', 'texte': '', 'justification': ''})} for r in catalogue(dossier)]
    return {'lignes': lignes, 'note': NOTE, 'parent': bloc.get('parent'),
            'auteur': bloc.get('auteur'), 'conserve_le_utc': bloc.get('conserve_le_utc'),
            'comptage_notes': {k: sum(r['statut'] == k for r in lignes) for k in STATUTS},
            'pret_a_deposer': False}


def normaliser(dossier, lignes):
    ordre = {r['code']: i for i, r in enumerate(catalogue(dossier))}
    resultat, vus = [], set()
    for r in lignes:
        if r.code not in ordre or r.code in vus:
            raise ValueError('Rubrique ETIC inconnue ou en doublon.')
        vus.add(r.code)
        texte, justification = r.texte.strip(), r.justification.strip()
        if r.statut != 'a_completer' and not justification:
            raise ValueError('Une référence de source ou justification est requise pour cette déclaration.')
        if r.statut == 'renseigne' and not texte:
            raise ValueError('Le texte de la note renseignée ne peut pas être vide.')
        resultat.append({'code': r.code, 'statut': r.statut,
                         'texte': texte, 'justification': justification})
    return sorted(resultat, key=lambda r: ordre[r['code']])


def conserver(db, user, preparation_id, data):
    sid = user['societe_id']
    if not db.query(models.Societe).filter_by(id=sid).with_for_update().first():
        raise HTTPException(404, 'Société introuvable.')
    row = db.query(models.LiasseBalancePreparation).filter_by(id=preparation_id, societe_id=sid).first()
    if not row:
        raise HTTPException(404, 'Préparation introuvable dans cette société.')
    try:
        dossier = lire_preparation(row)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if data.empreinte_parent != dossier['empreinte_sha256']:
        raise HTTPException(409, 'La préparation ne correspond plus à la source attendue.')
    try:
        lignes = normaliser(dossier, data.lignes)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    demande = {'schema_version': 1, 'cle': str(data.cle), 'catalogue': catalogue(dossier),
               'parent': {'id': row.id, 'version': row.version, 'empreinte_sha256': row.empreinte_sha256},
               'lignes': lignes}
    ancien = db.query(models.LiasseBalancePreparation).filter(
        models.LiasseBalancePreparation.societe_id == sid,
        models.LiasseBalancePreparation.contenu['notes_etic_documentaires']['cle'].as_string() == str(data.cle)).first()
    if ancien:
        try:
            sauvegarde = lire_preparation(ancien)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        bloc = sauvegarde['contenu']['notes_etic_documentaires']
        if {k: bloc[k] for k in demande} != demande:
            raise HTTPException(409, 'Clé déjà utilisée pour d’autres notes documentaires.')
        return sauvegarde
    acteur = db.query(models.Utilisateur).filter_by(id=user['id']).one()
    contenu = deepcopy(row.contenu)
    contenu['notes_etic_documentaires'] = {**demande,
        'auteur': {'id': acteur.id, 'nom': acteur.nom},
        'conserve_le_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    latest = db.query(func.max(models.LiasseBalancePreparation.version)).filter_by(
        societe_id=sid, exercice=row.exercice).scalar() or 0
    nouveau = models.LiasseBalancePreparation(societe_id=sid, exercice=row.exercice,
        exercice_id=row.exercice_id, version=latest + 1, contenu=contenu,
        empreinte_sha256=empreinte_preparation(contenu), created_by=user['id'])
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return lire_preparation(nouveau)
