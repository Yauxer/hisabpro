"""Plan : consultations sans mutation et préparation CGNC explicitement admin."""
from sqlalchemy import event
from sqlalchemy.orm import Session
import pytest
import models
from routers import plan_comptable
from test_session132_admin_acces_invites import acces, headers


@pytest.fixture
def plan(acces):
    client, engine = acces
    # Le même banc utilise l'authentification et les rôles réels ; seuls les
    # comptes et écritures de ce test sont créés dans son moteur en mémoire.
    for model in (models.CompteCGNCReference, models.CompteSociete, models.Ecriture, models.LigneEcriture):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add_all([
            models.CompteCGNCReference(numero="1111", libelle="Capital social", classe=1, type_compte="SP"),
            models.CompteCGNCReference(numero="5141", libelle="Banques", classe=5, type_compte="SP"),
        ])
        db.commit()
    client.app.include_router(plan_comptable.router)
    yield client, engine


@pytest.mark.parametrize("inclure_inactifs", ["true", "false"])
def test_get_plan_vide_ne_cree_pas_de_comptes(plan, inclure_inactifs):
    client, engine = plan
    sqls = []

    def enregistrer(connection, cursor, statement, parameters, context, executemany):
        sqls.append(statement.strip().upper())

    event.listen(engine, "before_cursor_execute", enregistrer)
    try:
        response = client.get(f"/api/plan-comptable?inclure_inactifs={inclure_inactifs}", headers=headers(3))
        assert response.status_code == 200 and response.json() == []
        assert not any(sql.startswith(("INSERT", "UPDATE", "DELETE", "CREATE", "ALTER")) for sql in sqls)
    finally:
        event.remove(engine, "before_cursor_execute", enregistrer)
    with Session(engine) as db:
        assert db.query(models.CompteSociete).count() == 0


@pytest.mark.parametrize("user_id,societe_id", [(3, 1), (3, 2)])
def test_preparation_interdite_lecture_et_comptable(plan, user_id, societe_id):
    client, engine = plan
    assert client.post("/api/plan-comptable/initialiser", headers=headers(user_id, societe_id)).status_code == 403
    with Session(engine) as db:
        assert db.query(models.CompteSociete).count() == 0


def test_preparation_admin_idempotente_et_limitee_a_sa_societe(plan):
    client, engine = plan
    for _ in range(2):
        response = client.post("/api/plan-comptable/initialiser", headers=headers())
        assert response.status_code == 200 and response.json()["nb_comptes"] == 2
    with Session(engine) as db:
        assert db.query(models.CompteSociete).filter_by(societe_id=1).count() == 2
        assert db.query(models.CompteSociete).filter_by(societe_id=2).count() == 0
    rows = client.get("/api/plan-comptable?inclure_inactifs=false", headers=headers(3)).json()
    assert {row["compte"] for row in rows} == {"1111", "5141"}


def test_preparation_preserve_libelles_personnalises_et_desactivation(plan):
    client, engine = plan
    with Session(engine) as db:
        db.add(models.CompteSociete(societe_id=1, numero="1111", libelle="Libellé documenté spécifique",
                                   classe=1, type_compte="SP", origine="cgnc", actif=False))
        db.commit()
    assert client.post("/api/plan-comptable/initialiser", headers=headers()).status_code == 200
    with Session(engine) as db:
        row = db.query(models.CompteSociete).filter_by(societe_id=1, numero="1111").one()
        assert row.libelle == "Libellé documenté spécifique" and row.actif is False
        assert db.query(models.CompteSociete).filter_by(societe_id=1).count() == 2


def test_filtre_actif_vide_ne_reactive_pas_comptes_existants(plan):
    client, engine = plan
    with Session(engine) as db:
        db.add(models.CompteSociete(societe_id=1, numero="1111", libelle="Capital", classe=1, type_compte="SP", origine="cgnc", actif=False))
        db.commit()
    response = client.get("/api/plan-comptable?inclure_inactifs=false", headers=headers())
    assert response.status_code == 200 and response.json() == []
    with Session(engine) as db:
        assert db.query(models.CompteSociete).filter_by(societe_id=1).count() == 1
