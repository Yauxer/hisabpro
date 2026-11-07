"""Migration075 : structure sans reparation, PostgreSQL ephemere exclusivement."""
from contextlib import contextmanager
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from routers.ecritures import AuxiliaireHistoriqueIn, ajouter_auxiliaire_historique

BACK = Path(__file__).resolve().parents[1] / 'hisabpro-backend'
TABLE = 'ligne_auxiliaire_complements'
CHECKS = ('ck_ligne_aux_complement_nature', 'ck_ligne_aux_complement_compte_non_vide',
          'ck_ligne_aux_complement_libelle_non_vide')


def instantane(engine):
    with engine.connect() as db:
        return {table: db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).all()
                for table in ('tiers', 'ecritures', 'lignes_ecriture', TABLE)}


def refuser(engine, sql, code):
    with engine.connect() as db:
        with pytest.raises(DBAPIError) as erreur:
            db.execute(text(sql))
            db.commit()
        assert erreur.value.orig.pgcode == code, erreur.value
        db.rollback()


@contextmanager
def cible_complements(origine='direct', table_absente=False, role_present=True):
    with cluster_isole() as cluster:
        def garde():
            assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        garde()
        owner = create_engine(cluster['url'])
        runtime = None
        def migration():
            garde()
            raw = owner.raw_connection()
            try:
                raw.autocommit = True
                with raw.cursor() as cursor:
                    cursor.execute((BACK / '075_complements_auxiliaires_structure.sql').read_text(encoding='utf-8'))
            finally:
                raw.close()
        try:
            garde()
            models.Base.metadata.create_all(owner)
            garde()
            with Session(owner) as db:
                societe = models.Societe(raison_sociale='Complements fictifs isoles')
                db.add(societe)
                db.flush()
                tiers = models.Tiers(societe_id=societe.id, type='client', nom='Client fictif connu',
                    code_aux_client='CLI-FICTIF-001', code_aux_fournisseur=None)
                db.add(tiers)
                ecriture = models.Ecriture(societe_id=societe.id, date=date(2025, 5, 1),
                    journal=models.JournalEnum.OD, libelle='Historique fictif conserve', exercice=2025,
                    est_validee=True, reference='FICTIF-001')
                db.add(ecriture)
                db.flush()
                ligne = models.LigneEcriture(ecriture_id=ecriture.id, compte='3421', debit=100,
                    credit=0, tiers_id=None, nature_auxiliaire=None,
                    compte_auxiliaire_snapshot=None, libelle_auxiliaire_snapshot=None)
                db.add(ligne)
                db.commit()
                ids = {'sid': societe.id, 'tid': tiers.id, 'lid': ligne.id}
            garde()
            with owner.begin() as db:
                if table_absente:
                    db.execute(text(f'DROP TABLE {TABLE}'))
                else:
                    for name in CHECKS:
                        db.execute(text(f'ALTER TABLE {TABLE} DROP CONSTRAINT {name}'))
                    db.execute(text(f'INSERT INTO {TABLE}(societe_id,ligne_ecriture_id,tiers_id,nature_auxiliaire,'
                        'compte_auxiliaire_snapshot,libelle_auxiliaire_snapshot,source_type,motif) '
                        "VALUES(:sid,:lid,:tid,'ancien_invalide',' ',' ','source_fictive','Historique non corrige')"), ids)
                    # Un meme nom dans une autre table ne doit pas masquer le CHECK cible.
                    db.execute(text('CREATE TABLE autre_controle(id integer CONSTRAINT ck_ligne_aux_complement_nature CHECK(id>0))'))
                if role_present:
                    db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                    db.execute(text('GRANT USAGE ON SCHEMA public TO hisabpro'))
                    db.execute(text('GRANT SELECT ON societes, tiers, ecritures, lignes_ecriture TO hisabpro'))
                    if not table_absente:
                        if origine == 'groupe':
                            db.execute(text('CREATE ROLE anciens_complements NOLOGIN'))
                            db.execute(text('GRANT anciens_complements TO hisabpro'))
                        destinataire = {'direct': 'hisabpro', 'public': 'PUBLIC', 'groupe': 'anciens_complements'}[origine]
                        db.execute(text(f'GRANT UPDATE, DELETE, TRUNCATE ON {TABLE} TO {destinataire}'))
            if role_present:
                runtime = create_engine(make_url(cluster['url']).set(username='hisabpro'))
            yield {'owner': owner, 'runtime': runtime, 'garde': garde, 'migration': migration, 'ids': ids}
        finally:
            if runtime is not None:
                runtime.dispose()
            owner.dispose()
    assert not cluster['directory'].exists()


@pytest.mark.parametrize('origine', ['direct', 'public', 'groupe'])
def test075_rejeu_preserve_historiques_et_bloque_acl_directes_heritees(origine):
    with cible_complements(origine) as cible:
        avant = instantane(cible['owner'])
        for _ in range(2):
            cible['migration']()
            assert instantane(cible['owner']) == avant
        with cible['owner'].connect() as db:
            checks = db.execute(text('SELECT conname,convalidated FROM pg_constraint WHERE conrelid=to_regclass(:table) '
                'AND contype=\'c\' ORDER BY conname'), {'table': TABLE}).all()
            assert checks == sorted((name, False) for name in CHECKS)
            acl = db.execute(text("SELECT a.privilege_type FROM pg_class c CROSS JOIN LATERAL aclexplode(c.relacl) a "
                "LEFT JOIN pg_roles r ON r.oid=a.grantee WHERE c.oid=to_regclass(:table) "
                "AND (a.grantee=0 OR r.rolname='hisabpro')"), {'table': TABLE}).scalars().all()
            assert not {'UPDATE', 'DELETE', 'TRUNCATE'}.intersection(acl)
        with cible['runtime'].connect() as db:
            assert db.execute(text('SELECT current_user,session_user')).one() == ('hisabpro', 'hisabpro')
            assert not db.scalar(text('SELECT rolsuper FROM pg_roles WHERE rolname=current_user'))
            assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
            assert db.scalar(text('SELECT relowner::regrole::text FROM pg_class WHERE oid=to_regclass(:table)'), {'table': TABLE}) != 'hisabpro'
            for operation in ('UPDATE', 'DELETE', 'TRUNCATE'):
                assert db.scalar(text('SELECT has_table_privilege(current_user,:table,:op)'),
                    {'table': TABLE, 'op': operation}) is (origine == 'groupe')
        for sql in (f'UPDATE {TABLE} SET motif=\'interdit\'', f'DELETE FROM {TABLE}', f'TRUNCATE {TABLE}'):
            cible['garde']()
            refuser(cible['runtime'], sql, '23514' if origine == 'groupe' else '42501')
            refuser(cible['owner'], sql, '23514')
            assert instantane(cible['owner']) == avant
        # Insertion explicite connue : aucun tiers ni auxiliaire n'est devine.
        cible['garde']()
        with Session(cible['runtime']) as db:
            eid = db.scalar(text('SELECT ecriture_id FROM lignes_ecriture WHERE id=:lid'), cible['ids'])
            resultat = ajouter_auxiliaire_historique(eid, cible['ids']['lid'],
                AuxiliaireHistoriqueIn(tiers_id=cible['ids']['tid'], motif='Source explicite fictive'),
                current_user={'societe_id': cible['ids']['sid'], 'role': 'admin'}, db=db)
            assert resultat['compte_auxiliaire'] == 'CLI-FICTIF-001'
            assert resultat['nature_auxiliaire'] == 'client'
        apres = instantane(cible['owner'])
        assert all(apres[t] == avant[t] for t in ('tiers', 'ecritures', 'lignes_ecriture'))
        assert apres[TABLE][:len(avant[TABLE])] == avant[TABLE] and len(apres[TABLE]) == len(avant[TABLE]) + 1
        for nature, compte, libelle in [('invalide', 'CLI-FICTIF-001', 'Client'), ('client', ' ', 'Client'), ('fournisseur', 'FOU-001', ' ')]:
            cible['garde']()
            with cible['runtime'].connect() as db:
                with pytest.raises(DBAPIError) as erreur:
                    db.execute(text(f'INSERT INTO {TABLE}(societe_id,ligne_ecriture_id,tiers_id,nature_auxiliaire,'
                        'compte_auxiliaire_snapshot,libelle_auxiliaire_snapshot,source_type) VALUES(:sid,:lid,:tid,:nature,:compte,:libelle,\'recette_isolee\')'),
                        {**cible['ids'], 'nature': nature, 'compte': compte, 'libelle': libelle})
                assert erreur.value.orig.pgcode == '23514'
                db.rollback()
        assert instantane(cible['owner']) == apres


@pytest.mark.parametrize('table_absente,role_present', [(True, True), (False, False)])
def test075_structure_absente_ou_role_absent_sans_reparation(table_absente, role_present):
    with cible_complements(table_absente=table_absente, role_present=role_present) as cible:
        for _ in range(2):
            cible['migration']()
        with cible['owner'].connect() as db:
            assert db.scalar(text(f'SELECT count(*) FROM {TABLE}')) == (0 if table_absente else 1)
            assert db.scalar(text('SELECT tiers_id FROM lignes_ecriture WHERE id=:lid'), cible['ids']) is None
            assert db.scalar(text('SELECT code_aux_client FROM tiers WHERE id=:tid'), cible['ids']) == 'CLI-FICTIF-001'
        cible['garde']()
        refuser(cible['owner'], f'TRUNCATE {TABLE}', '23514')
