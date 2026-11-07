"""Tables documentaires B8/B9, sans présumer une sûreté ou un engagement."""
from copy import deepcopy
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
import models
from services.balance_import_service import lire_preparation, empreinte_preparation
from services.etic_service import CATALOGUE_ETIC

NOTE = ('Saisie documentaire B8/B9 selon les colonnes du catalogue HisabPro existant. '
        'Les montants sont exprimés en MAD. Une case vide reste inconnue, jamais zéro. '
        'Documenté est une déclaration sourcée, pas un contrôle de complétude. '
        'Aucune sûreté ou engagement n’est déduit des balances. '
        'Aucune donnée du Journal ou de l’ETIC comptable n’est modifiée ; '
        'cette préparation ne vaut pas liasse prête à déposer.')
STATUTS = {'a_completer': 'À compléter', 'documente': 'Saisie documentée — à revoir',
           'neant_declare': 'Néant — déclaré et justifié'}


def catalogue(dossier):
    bloc = dossier['contenu'].get('tables_etic_documentaires')
    return deepcopy(bloc['catalogue'] if bloc else [
        {k: r[k] for k in ('code', 'groupe', 'titre', 'colonnes_saisie')}
        for r in CATALOGUE_ETIC if r['code'] in ('B8', 'B9')])


def presentation(dossier, *, nom_bloc='tables_etic_documentaires', referentiel=None, note=NOTE):
    bloc = dossier['contenu'].get(nom_bloc) or {}
    saisis = {r['code']: r for r in bloc.get('tables', [])}
    tables = [{**r, **saisis.get(r['code'], {
        'statut': 'a_completer', 'justification': '', 'lignes': []})} for r in (referentiel or catalogue)(dossier)]
    notes = {r['code']: r for r in dossier['contenu'].get('notes_etic_documentaires', {}).get('lignes', [])}
    alertes = [r['code'] + ' : la note est déclarée non applicable alors que le tableau contient des lignes. '
               'Revoir les deux compléments ; aucune donnée n’a été corrigée automatiquement.'
               for r in tables if r['lignes'] and notes.get(r['code'], {}).get('statut') == 'non_applicable']
    return {'tables': tables, 'note': note, 'parent': bloc.get('parent'),
            'auteur': bloc.get('auteur'), 'conserve_le_utc': bloc.get('conserve_le_utc'),
            'alertes': alertes, 'pret_a_deposer': False}


def texte(value, contexte):
    if not isinstance(value, str) or len(value) > 2000:
        raise ValueError(contexte + ' : texte de 2 000 caractères maximum requis.')
    return value.strip()


def normaliser(dossier, tables, *, referentiel=None, convertir_nombre=None):
    from services.balance_import_service import montant_import
    schemas = {r['code']: r for r in (referentiel or catalogue)(dossier)}
    resultat, vus = [], set()
    for table in tables:
        if table.code not in schemas or table.code in vus:
            raise ValueError('Tableau ETIC inconnu ou en doublon.')
        vus.add(table.code)
        colonnes = schemas[table.code]['colonnes_saisie']
        champs = {c['cle'] for c in colonnes} | {'reference_source'}
        lignes = []
        for i, r in enumerate(table.lignes, 1):
            if set(r) - champs:
                raise ValueError('Colonne inconnue dans ' + table.code + '.')
            ligne = {}
            for c in colonnes:
                v = r.get(c['cle'])
                contexte = f"{table.code} ligne {i} {c['label']}"
                if c['type'] == 'number':
                    ligne[c['cle']] = None if v is None or v == '' else (convertir_nombre(c, v, contexte) if convertir_nombre else format(montant_import(v, contexte), '.2f'))
                else:
                    ligne[c['cle']] = texte('' if v is None else v, contexte)
            ligne['reference_source'] = texte(r.get('reference_source', ''), 'Référence de source')
            identifiant = schemas[table.code].get('champ_identifiant', 'nature')
            if table.statut == 'documente' and (not ligne[identifiant] or not ligne['reference_source']):
                raise ValueError('Chaque ligne documentée nécessite une désignation et une référence de source pour être identifiable et vérifiable.')
            lignes.append(ligne)
        justification = table.justification.strip()
        if table.statut != 'a_completer' and not justification:
            raise ValueError('Une justification du tableau est requise pour cette déclaration.')
        if table.statut == 'documente' and not lignes:
            raise ValueError('Un tableau documenté nécessite au moins une ligne ; sinon déclarer néant avec justification.')
        if table.statut == 'neant_declare' and lignes:
            raise ValueError('Un tableau déclaré néant ne peut pas contenir de lignes ; les retirer explicitement ou modifier la déclaration.')
        resultat.append({'code': table.code, 'statut': table.statut,
                         'justification': justification, 'lignes': lignes})
    # Chaque POST remplace les tableaux du formulaire ; un oubli ne supprime jamais un tableau.
    if vus != set(schemas):
        raise ValueError('Tous les tableaux du formulaire sont requis dans la demande.')
    return sorted(resultat, key=lambda r: list(schemas).index(r['code']))


def conserver(db, user, preparation_id, data, *, nom_bloc='tables_etic_documentaires', normalisation=None, referentiel=None, enrichir=None):
    sid = user['societe_id']
    societe = db.query(models.Societe).filter_by(id=sid).with_for_update().first()
    if not societe:
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
    if (societe.devise or 'MAD').strip().upper() != 'MAD':
        raise HTTPException(422, 'Cette préparation est exprimée en MAD ; aucune conversion de devise automatique.')
    try:
        tables = (normalisation or normaliser)(dossier, data.tables)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    demande = {'schema_version': 1, 'cle': str(data.cle), 'catalogue': (referentiel or catalogue)(dossier),
               'parent': {'id': row.id, 'version': row.version, 'empreinte_sha256': row.empreinte_sha256},
               'tables': tables}
    ancien = db.query(models.LiasseBalancePreparation).filter(
        models.LiasseBalancePreparation.societe_id == sid,
        models.LiasseBalancePreparation.contenu[nom_bloc]['cle'].as_string() == str(data.cle)).first()
    if ancien:
        try:
            sauvegarde = lire_preparation(ancien)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        bloc = sauvegarde['contenu'][nom_bloc]
        if {k: bloc[k] for k in demande} != demande:
            raise HTTPException(409, 'Clé déjà utilisée pour d’autres tableaux documentaires.')
        return sauvegarde
    acteur = db.query(models.Utilisateur).filter_by(id=user['id']).one()
    contenu = deepcopy(row.contenu)
    contenu[nom_bloc] = {**demande,
        'auteur': {'id': acteur.id, 'nom': acteur.nom},
        'conserve_le_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    if enrichir:
        try:
            supplement = enrichir(dossier, demande)
            if set(supplement) & set(contenu[nom_bloc]):
                raise ValueError('Un contrôle ne peut pas remplacer les données déclarées.')
            contenu[nom_bloc].update(supplement)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
    latest = db.query(func.max(models.LiasseBalancePreparation.version)).filter_by(
        societe_id=sid, exercice=row.exercice).scalar() or 0
    nouveau = models.LiasseBalancePreparation(societe_id=sid, exercice=row.exercice,
        exercice_id=row.exercice_id, version=latest + 1, contenu=contenu,
        empreinte_sha256=empreinte_preparation(contenu), created_by=user['id'])
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return lire_preparation(nouveau)
