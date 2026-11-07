"""082 : permissions réelles et conservation, exclusivement PostgreSQL nonce."""
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK, candidats
from recette_installation_vierge_consolidee import COMPLEMENTS


def test_manifeste_082_ne_change_pas_phase077():
    assert len(candidats()) == 64
    assert len(COMPLEMENTS) == 9 and len(set(COMPLEMENTS)) == 9
    assert COMPLEMENTS[-1] == '082_paie_referentiels.sql'
    assert [n for n in COMPLEMENTS if int(n.split('_', 1)[0]) < 77] == list(COMPLEMENTS[:3])


def test_082_runtime_insertion_sequence_lecture_et_immutabilite():
    with cluster_isole() as cible:
        def garde():
            assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        garde()
        owner = create_engine(cible['url'])
        runtime = None
        def migration():
            garde()
            with owner.begin() as db:
                db.exec_driver_sql((BACK / COMPLEMENTS[-1]).read_text(encoding='utf-8'))
        def refuse(engine, sql, code):
            garde()
            with engine.connect() as db:
                with pytest.raises(DBAPIError) as erreur:
                    db.execute(text(sql))
                assert erreur.value.orig.pgcode == code
                db.rollback()
        try:
            with owner.begin() as db:
                db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
            models.Base.metadata.create_all(owner)
            migration()
            with Session(owner) as db:
                societe = models.Societe(raison_sociale='Laboratoire installation082')
                db.add(societe); db.flush()
                utilisateur = models.Utilisateur(societe_id=societe.id, nom='Administrateur fictif',
                    email='installation082@example.com', hashed_password='NON-CONNECTABLE', role='admin')
                db.add(utilisateur); db.flush()
                sid, uid = societe.id, utilisateur.id
                db.commit()
            runtime = create_engine(make_url(cible['url']).set(username='hisabpro'))
            garde()
            with runtime.begin() as db:
                assert db.scalar(text('SELECT current_user')) == 'hisabpro'
                identifiant = db.scalar(text("INSERT INTO paie_referentiel_versions "
                    "(societe_id,annee,version,empreinte,parametres,sources,qualification,created_by) "
                    "VALUES (:sid,2026,1,:empreinte,'{}','[]','non_verifie',:uid) RETURNING id"),
                    {'sid': sid, 'uid': uid, 'empreinte': 'a'*64})
                assert identifiant > 0
                assert db.scalar(text('SELECT count(*) FROM paie_referentiel_versions')) == 1
                assert db.scalar(text("SELECT has_sequence_privilege(current_user,'paie_referentiel_versions_id_seq','USAGE')"))
                assert db.scalar(text("SELECT has_sequence_privilege(current_user,'paie_referentiel_versions_id_seq','SELECT')"))
                avant = db.execute(text('SELECT * FROM paie_referentiel_versions')).one()
            migration()
            migration()
            for annee, version, qualification, code in ((2026, 1, 'non_verifie', '23505'),
                    (2026, 0, 'non_verifie', '23514'), (2024, 2, 'non_verifie', '23514'),
                    (2026, 2, 'certifie', '23514')):
                refuse(runtime, "INSERT INTO paie_referentiel_versions "
                    "(societe_id,annee,version,empreinte,parametres,sources,qualification,created_by) "
                    f"VALUES ({sid},{annee},{version},'{'a'*64}','{{}}','[]','{qualification}',{uid})", code)
            for sql in ("UPDATE paie_referentiel_versions SET commentaire='altération'",
                        'DELETE FROM paie_referentiel_versions', 'TRUNCATE paie_referentiel_versions'):
                refuse(owner, sql, '23514')
                refuse(runtime, sql, '42501')
            with runtime.connect() as db:
                assert db.execute(text('SELECT * FROM paie_referentiel_versions')).one() == avant
                assert not db.scalar(text("SELECT has_sequence_privilege(current_user,'paie_referentiel_versions_id_seq','UPDATE')"))
        finally:
            if runtime is not None:
                runtime.dispose()
            owner.dispose()
    assert not cible['directory'].exists()
