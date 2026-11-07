"""Expérience d'installation vierge, jamais une migration de base existante.

Exécution explicite uniquement ; aucune URL utilisateur acceptée. Le cluster,
son rôle, son marqueur et ses tables métier sont vérifiés avant chaque SQL.
Arrêt au premier échec ; registre JSON temporaire dans le seul cluster créé.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import types

from sqlalchemy import create_engine, text

from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
REPORT = ROOT / 'Test' / 'rapport_installation_vierge_postgres.md'
EXCLUS = {
    '007b_cloture_hotfix.sql', '021_fiscalite_is_CORRIGE.sql',
    '065_reparation_liquidations_is_reference_acomptes.sql',
    '067_reparation_fec_historique_sure.sql',
    '068_fec_complements_historiques_append_only.sql',
    '070_reparation_is_cloture_historique_2026.sql',
}
TABLES_METIER = (
    'societes', 'utilisateurs', 'utilisateurs_societes', 'tiers', 'articles',
    'factures', 'reglements', 'ecritures', 'lignes_ecriture', 'mouvements_stock',
    'inventaires_stock', 'immobilisations', 'clotures_exercice',
    'fiscal_liquidations_is', 'liasses_fiscales_archives', 'etic_sections_exercice',
    'livres_inventaire_archives', 'ligne_auxiliaire_complements',
)


def candidats():
    import re
    fichiers = sorted(p for p in BACK.glob('*.sql')
        if re.match(r'\d', p.name) and int(re.match(r'\d+', p.name).group()) <= 73)
    resultat = [p for p in fichiers if p.name not in EXCLUS]
    assert len(fichiers) == 70 and len(resultat) == 64, 'Inventaire modifié : revoir le manifeste.'
    return resultat


def tables_vides(engine, cible):
    verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
    with engine.connect() as db:
        compte = {nom: db.execute(text(f'SELECT COUNT(*) FROM "{nom}"')).scalar_one()
                  for nom in TABLES_METIER}
    if any(compte.values()):
        raise RuntimeError('Installation refusée : données métier présentes ' + json.dumps(compte))
    return compte


def phase(fichier):
    n = int(fichier.name[:3])
    return ('comptabilite' if n <= 19 else 'fiscalite' if n <= 27 else
            'facturation_audit' if n <= 53 else 'referentiel' if n <= 66 else
            'complements_permissions' if n <= 69 else 'protections_finales')


def controles_catalogue(engine):
    with engine.connect() as db:
        contraintes = set(db.execute(text('SELECT conname FROM pg_constraint')).scalars())
        triggers = set(db.execute(text("SELECT tgname FROM pg_trigger WHERE NOT tgisinternal")).scalars())
        contenu_type = db.execute(text("SELECT data_type FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='liasse_balances_preparation' AND column_name='contenu'" )).scalar()
    return {
        'check_code_etic': 'ck_etic_section_code' in contraintes,
        'check_sha256_archive': 'ck_liasse_archive_sha256' in contraintes,
        'trigger_complements_append_only': 'trg_ligne_aux_complements_append_only' in triggers,
        'trigger_archive_truncate': 'trg_hisabpro_liasse_archive_truncate' in triggers,
        'type_contenu_preparation': contenu_type,
        'nombre_triggers_metier': len(triggers),
    }


def executer():
    debut = time.monotonic()
    registre = []
    resultat = {'date_utc': datetime.now(timezone.utc).isoformat(), 'statut': 'en_cours',
                'fichier_en_cours': 'socle_ORM', 'erreur': None, 'appliquees': registre}
    ancien_url = os.environ.get('DATABASE_URL')
    directory = None
    try:
        with cluster_isole() as cible:
            directory = cible['directory']
            verifier_cible_isolee(cible['url'], directory, cible['nonce'])
            # Bloquer totalement la lecture .env, avant l'import du backend.
            dotenv = types.ModuleType('dotenv')
            dotenv.load_dotenv = lambda *args, **kwargs: False
            sys.modules['dotenv'] = dotenv
            os.environ['DATABASE_URL'] = cible['url']
            sys.path.insert(0, str(BACK))
            import models
            from database import Base, engine as backend_engine
            verifier_cible_isolee(str(backend_engine.url), directory, cible['nonce'])
            engine = create_engine(cible['url'], connect_args={
                'options': '-c statement_timeout=30000 -c lock_timeout=10000'})
            try:
                with engine.begin() as db:
                    db.execute(text('CREATE ROLE hisabpro NOLOGIN'))
                verifier_cible_isolee(cible['url'], directory, cible['nonce'])
                Base.metadata.create_all(engine)
                resultat['nombre_tables_orm'] = len(Base.metadata.tables)
                resultat['zero_initial'] = tables_vides(engine, cible)
                registry_path = directory / 'installation_registry.json'
                derniere_phase = None
                for fichier in candidats():
                    nom_phase = phase(fichier)
                    if nom_phase != derniere_phase:
                        tables_vides(engine, cible)
                        derniere_phase = nom_phase
                    resultat['fichier_en_cours'] = fichier.name
                    verifier_cible_isolee(cible['url'], directory, cible['nonce'])
                    tables_vides(engine, cible)
                    connection = engine.raw_connection()
                    try:
                        connection.autocommit = True
                        with connection.cursor() as cursor:
                            cursor.execute(fichier.read_text(encoding='utf-8'))
                    finally:
                        connection.close()
                    registre.append({'fichier': fichier.name, 'phase': nom_phase,
                        'sha256': hashlib.sha256(fichier.read_bytes()).hexdigest(),
                        'date_utc': datetime.now(timezone.utc).isoformat()})
                    registry_path.write_text(json.dumps(registre, ensure_ascii=False, indent=2), encoding='utf-8')
                    tables_vides(engine, cible)
                    print('APPLIQUE ' + fichier.name, flush=True)
                resultat['zero_final'] = tables_vides(engine, cible)
                resultat['catalogue'] = controles_catalogue(engine)
                resultat['statut'] = '64_scripts_executés_installation_incomplete'
            except Exception as exc:
                resultat['statut'] = 'echec_arret_premier_sql'
                resultat['erreur'] = str(exc)[:6000]
                print('ECHEC ' + resultat['fichier_en_cours'] + ': ' + str(exc)[:2500], flush=True)
            finally:
                engine.dispose()
                backend_engine.dispose()
    finally:
        if ancien_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = ancien_url
        resultat['duree_secondes'] = round(time.monotonic() - debut, 2)
        resultat['cluster_supprime'] = directory is not None and not directory.exists()
        lignes = ["# Expérience réelle d'installation PostgreSQL vierge", '',
            f"Date UTC : {resultat['date_utc']}",
            f"Statut : **{resultat['statut']}**",
            f"Durée : {resultat['duree_secondes']} s ; scripts terminés : {len(registre)}/64.",
            f"Cluster temporaire supprimé : {resultat['cluster_supprime']}.", '',
            "Commande : `hisabpro-backend/.venv/Scripts/python.exe Test/recette_installation_vierge.py`.", '',
            "Aucune connexion réelle, aucun .env lu, aucune donnée comptable créée. "
            "Rôle hisabpro NOLOGIN et socle ORM préparés sur le seul cluster marqué. "
            "Garde de cible et comptes des tables métier vérifiés avant et après chaque SQL. "
            "Registre SHA-256 local conservé dans le cluster pendant l'expérience puis supprimé avec lui.", '',
            "## Résultat exact", '',
            f"Dernier objet tenté : `{resultat['fichier_en_cours']}`.", '',
            '```text', resultat['erreur'] or 'Aucun échec des scripts candidats.', '```', '',
            "## Scripts effectivement terminés", '',
            '| Fichier | Phase | SHA-256 |', '|---|---|---|']
        lignes += [f"| `{x['fichier']}` | {x['phase']} | `{x['sha256']}` |" for x in registre]
        lignes += ['', '## Catalogue observé', '', '```json',
            json.dumps(resultat.get('catalogue', {}), ensure_ascii=False, indent=2), '```', '',
            '## Limites', '',
            'Installation exhaustive et permissions runtime non validées. Les tables métier restent vides ; '
            'aucun parcours utilisateur exécuté ici. Les réparations 065/067/068/070, init.sql et seed paie '
            'sont exclus. Les protections structurales de 068 manquent toujours dans cette route candidate ; '
            'une exécution réussie des 64 scripts ne prouverait donc pas une installation complète. '
            'Les nouvelles migrations après 073 ne sont pas incluses dans cette première expérience. '
            'Arrêt au premier échec, aucun SQL original modifié ni contourné.']
        REPORT.write_text('\n'.join(lignes) + '\n', encoding='utf-8')
    return 1 if resultat['erreur'] else 0


if __name__ == '__main__':
    raise SystemExit(executer())
