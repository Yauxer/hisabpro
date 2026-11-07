"""Sauvegarde GRH082 réelle ; deux clusters isolés sans données utilisateur."""
from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError
import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK, candidats
from recette_installation_vierge_consolidee import COMPLEMENTS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ops.postgres_sauvegarde import sauvegarder, restaurer_isole

TABLES = ('societes', 'utilisateurs', 'employes', 'grh_absences',
          'grh_absence_evenements', 'paie_referentiel_versions', 'ecritures', 'lignes_ecriture')


def canonique(valeur):
    if isinstance(valeur, (date, datetime)):
        return valeur.isoformat()
    if isinstance(valeur, Decimal):
        return str(valeur)
    raise TypeError(type(valeur).__name__)


def instantane(engine):
    with engine.connect() as db:
        return {table: json.dumps([dict(r._mapping) for r in db.execute(text(
            f'SELECT * FROM {table} ORDER BY id'))], sort_keys=True, ensure_ascii=False,
            allow_nan=False, default=canonique) for table in TABLES}


def migration(engine, fichier):
    raw = engine.raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cursor:
            cursor.execute(fichier.read_text(encoding='utf-8'))
    finally:
        raw.close()


def refuse(engine, sql, code):
    with engine.connect() as db:
        with pytest.raises(DBAPIError) as erreur:
            db.execute(text(sql))
        assert erreur.value.orig.pgcode == code
        db.rollback()


def test_dump_restore_grh_paie_082_et_ecriture_definitive():
    with cluster_isole() as source_cible, cluster_isole() as restauree_cible:
        def garde():
            for c in (source_cible, restauree_cible):
                assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        garde()
        source, restauree = create_engine(source_cible['url']), create_engine(restauree_cible['url'])
        runtime = None
        try:
            with source.begin() as db:
                db.execute(text('CREATE ROLE hisabpro NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
            models.Base.metadata.create_all(source)
            for fichier in list(candidats()) + [BACK/n for n in COMPLEMENTS]:
                garde(); migration(source, fichier)
            with Session(source) as db:
                s = models.Societe(raison_sociale='Dossier sauvegarde fictif', devise='MAD')
                db.add(s); db.flush()
                u = models.Utilisateur(societe_id=s.id, nom='Admin laboratoire',
                    email='sauvegarde082@example.com', hashed_password='NON-CONNECTABLE', role='admin')
                db.add(u); db.flush()
                emp = models.Employe(societe_id=s.id, nom='Salarié historique fictif',
                    salaire_brut=10000, type_contrat=None, personnes_charge_ir=None,
                    matricule='BACKUP-082', date_embauche=date(2025,1,1))
                db.add(emp); db.flush()
                absence = models.AbsenceRH(societe_id=s.id, employe_id=emp.id, type_absence='absence',
                    date_debut=date(2026,10,6), date_fin=date(2026,10,7), statut='demande',
                    motif='Motif fictif sauvegarde', created_by=u.id)
                db.add(absence); db.flush()
                db.add(models.EvenementAbsenceRH(societe_id=s.id, absence_id=absence.id,
                    acteur_id=u.id, ancien_statut=None, nouveau_statut='demande', commentaire='Demande initiale'))
                db.add(models.PaieReferentielVersion(societe_id=s.id, annee=2026, version=1,
                    empreinte='a'*64, parametres={'laboratoire':True,'taux_fictif':0.123,'plafond':None},
                    sources=[{'titre':'Pièce de laboratoire sans portée réglementaire','url':'https://example.com/fixture'}],
                    qualification='non_verifie', regime='Simulation laboratoire', created_by=u.id))
                e = models.Ecriture(societe_id=s.id, date=date(2026,10,6), exercice=2026,
                    journal='OD', libelle='Équilibre sauvegarde fictif', reference='BACKUP-100',
                    date_piece=date(2026,10,6), lignes=[
                        models.LigneEcriture(compte='5141',libelle='Fixture débit',debit=100,credit=0),
                        models.LigneEcriture(compte='1111',libelle='Fixture crédit',debit=0,credit=100)])
                db.add(e); db.flush()
                e.est_validee=True; e.validee_par=u.id; e.date_validation=datetime(2026,10,6,12)
                db.commit()
            avant = instantane(source)
            garde()
            archive = sauvegarder(source_cible['url'], source_cible['directory']/'preuve082.dump', source_cible['bin'])
            garde()
            restaurer_isole(restauree_cible['url'], archive, restauree_cible['bin'],
                            restauree_cible['directory'], restauree_cible['nonce'])
            assert instantane(restauree)==avant==instantane(source)
            with restauree.connect() as db:
                assert db.scalar(text('SELECT type_contrat FROM employes')) is None
                assert db.scalar(text('SELECT est_validee FROM ecritures'))
                assert db.execute(text('SELECT sum(debit),sum(credit) FROM lignes_ecriture')).one()==(100,100)
                triggers = dict(db.execute(text("SELECT tgname,tgenabled FROM pg_trigger WHERE NOT tgisinternal "
                    "AND tgname IN ('trg_grh_historique_immutable','trg_grh_historique_truncate',"
                    "'trg_paie_referentiel_immutable','trg_paie_referentiel_truncate')")).all())
                assert len(triggers)==4 and set(triggers.values())=={'O'}
            for table in ('grh_absence_evenements','paie_referentiel_versions'):
                for operation in (f'UPDATE {table} SET id=id', f'DELETE FROM {table}', f'TRUNCATE {table}'):
                    garde(); refuse(restauree,operation,'23514')
            garde()
            with pytest.raises(ValueError, match='doit être vide'):
                restaurer_isole(restauree_cible['url'],archive,restauree_cible['bin'],
                                restauree_cible['directory'],restauree_cible['nonce'])
            assert instantane(restauree)==avant
            # --no-privileges ne transporte aucune ACL. Reprovisionnement082 seulement.
            with restauree.begin() as db:
                db.execute(text('CREATE ROLE hisabpro LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS'))
                assert not db.scalar(text("SELECT has_table_privilege('hisabpro','paie_referentiel_versions','SELECT')"))
            garde(); migration(restauree, BACK/'082_paie_referentiels.sql')
            runtime = create_engine(make_url(restauree_cible['url']).set(username='hisabpro'))
            with runtime.connect() as db:
                assert db.scalar(text('SELECT current_user'))=='hisabpro'
                assert db.scalar(text('SELECT count(*) FROM paie_referentiel_versions'))==1
                for privilege in ('SELECT','INSERT'):
                    assert db.scalar(text("SELECT has_table_privilege(current_user,'paie_referentiel_versions',:p)"),{'p':privilege})
                for privilege in ('USAGE','SELECT'):
                    assert db.scalar(text("SELECT has_sequence_privilege(current_user,'paie_referentiel_versions_id_seq',:p)"),{'p':privilege})
                preuve_insert = db.scalar(text("INSERT INTO paie_referentiel_versions "
                    "(societe_id,annee,version,empreinte,parametres,sources,qualification,created_by) "
                    "SELECT societe_id,annee,2,empreinte,parametres,sources,qualification,created_by "
                    "FROM paie_referentiel_versions RETURNING id"))
                assert preuve_insert > 1
                db.rollback()  # Preuve INSERT/séquence réelle sans laisser une version supplémentaire.
            for operation in ('UPDATE paie_referentiel_versions SET id=id',
                              'DELETE FROM paie_referentiel_versions','TRUNCATE paie_referentiel_versions'):
                garde(); refuse(runtime,operation,'42501')
            assert instantane(restauree)==avant==instantane(source)
        finally:
            if runtime is not None: runtime.dispose()
            source.dispose(); restauree.dispose()
    assert not source_cible['directory'].exists() and not restauree_cible['directory'].exists()
