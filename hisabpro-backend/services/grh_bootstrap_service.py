"""Compléments GRH additifs du démarrage avec création de schéma autorisée.

create_all ne modifie pas les contraintes des tables existantes. Les deux
clés composites référencées doivent donc être présentes avant cette création.
Les migrations historiques restent inchangées ; aucune ligne n'est réparée.
"""
from pathlib import Path

from sqlalchemy import text


def initialiser_schema_developpement(engine, metadata):
    if engine.dialect.name != 'postgresql':
        metadata.create_all(bind=engine)
        return
    backend = Path(__file__).resolve().parents[1]
    # Vérifier les fichiers avant toute opération sur le schéma.
    scripts = [(backend / nom).read_text(encoding='utf-8') for nom in (
        '080_dossiers_employes.sql', '081_grh_absences.sql',
        '082_paie_referentiels.sql')]
    with engine.begin() as connection:
        connection.execute(text('SELECT pg_advisory_xact_lock(726881, 1)'))
        for table, contrainte in (
            ('employes', 'uq_employes_id_societe'),
            ('grh_absences', 'uq_grh_absences_id_societe'),
        ):
            # Identifiants fixes du programme, aucune entrée utilisateur.
            connection.execute(text(f"""
                DO $$ BEGIN
                  IF to_regclass('public.{table}') IS NOT NULL
                     AND NOT EXISTS (
                       SELECT 1 FROM pg_constraint
                       WHERE conrelid=to_regclass('public.{table}')
                         AND conname='{contrainte}'
                     ) THEN
                    ALTER TABLE public.{table}
                      ADD CONSTRAINT {contrainte} UNIQUE (id, societe_id);
                  END IF;
                END $$;
            """))
    metadata.create_all(bind=engine)
    # 080 ajoute les colonnes optionnelles ; 081/082 protègent les historiques.
    # Chaque fichier conserve sa propre transaction BEGIN/COMMIT.
    raw = engine.raw_connection()
    ancienne_autocommit = raw.autocommit
    try:
        raw.autocommit = True
        with raw.cursor() as cursor:
            for script in scripts:
                cursor.execute(script)
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.autocommit = ancienne_autocommit
        raw.close()
