"""Versions concurrentes et immutabilité vérifiées dans un cluster PG marqué."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Barrier
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from services.balance_import_service import enregistrer_preparation, lire_preparation

ROOT = Path(__file__).resolve().parents[1]
ROWS = [{'compte': '1111', 'credit': '100'}, {'compte': '5141', 'debit': '100'}]


@pytest.fixture(scope='module')
def moteur():
    with cluster_isole() as cluster:
        verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        engine = create_engine(cluster['url'])
        try:
            models.Base.metadata.create_all(engine)
            for _ in range(2):
                raw = engine.raw_connection()
                try:
                    cursor = raw.cursor(); cursor.execute((ROOT / 'hisabpro-backend/071_liasse_balances_preparation.sql').read_text(encoding='utf-8'))
                    raw.commit(); cursor.close()
                finally:
                    raw.close()
            with Session(engine) as db:
                db.add(models.Societe(id=1, raison_sociale='Test fictif balances'))
                db.flush()
                db.add(models.Utilisateur(id=1, societe_id=1, nom='Recette', email='balances@recette.test', hashed_password='test', role='admin'))
                db.add(models.ExerciceComptable(id=1, societe_id=1, annee=2025,
                    date_debut=date(2025,1,1), date_fin=date(2025,12,31), statut='ouvert'))
                for numero in ['1111', '5141']:
                    db.add(models.CompteSociete(societe_id=1, numero=numero, libelle=numero, classe=int(numero[0])))
                db.commit()
            yield engine
        finally:
            engine.dispose()


def test_versions_concurrentes_preservent_sources_et_grand_livre(moteur):
    barrier = Barrier(2)
    def creer():
        with Session(moteur) as db:
            barrier.wait(timeout=10)
            return enregistrer_preparation(db, 1, 2025, ROWS, None, {'n': 'test.csv'}, 1)
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(lambda _: creer(), range(2)))
    assert sorted(row['version'] for row in result) == [1, 2]
    with Session(moteur) as db:
        assert db.query(models.Ecriture).count() == 0
        assert db.query(models.LigneEcriture).count() == 0
        assert db.query(models.LiasseFiscaleArchive).count() == 0
        assert lire_preparation(db.get(models.LiasseBalancePreparation, result[0]['id']))['id'] == result[0]['id']


@pytest.mark.parametrize('commande', [
    "UPDATE liasse_balances_preparation SET contenu='{}'::jsonb WHERE id=(SELECT min(id) FROM liasse_balances_preparation)",
    'DELETE FROM liasse_balances_preparation WHERE id=(SELECT min(id) FROM liasse_balances_preparation)'])
def test_migration_immuable_et_repeatable(moteur, commande):
    with moteur.connect() as c:
        with pytest.raises(Exception, match='immuable'):
            c.execute(text(commande))
        c.rollback()
        assert c.scalar(text('SELECT count(*) FROM liasse_balances_preparation')) == 2
