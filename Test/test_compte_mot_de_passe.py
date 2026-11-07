"""API réelle et hashes réels sur base mémoire ; verrous PG testés séparément."""
import pytest
from sqlalchemy.orm import Session
import models
from auth import hash_password, verify_password, create_access_token
from test_session132_admin_acces_invites import acces

ACTUEL = 'AncienSecret133!'
NOUVEAU = 'NouveauSecret133!'


def preparer(acces, user_id=3, societe_id=1):
    client, engine = acces
    with Session(engine) as db:
        user = db.get(models.Utilisateur, user_id)
        user.hashed_password = hash_password(ACTUEL)
        digest = user.hashed_password
        db.commit()
    token = create_access_token({'sub': str(user_id), 'societe_id': societe_id}, password_hash=digest)
    return client, engine, {'Authorization': 'Bearer ' + token}, digest


@pytest.mark.parametrize('user_id,societe_id', [(1,1), (3,1), (3,2)])
def test_changement_personnel_admin_lecture_comptable_et_sessions_revoquees(acces, user_id, societe_id):
    client, engine, headers, original = preparer(acces, user_id, societe_id)
    autres_headers = {'Authorization': 'Bearer ' + create_access_token(
        {'sub': str(user_id), 'societe_id': 2 if user_id == 3 else 1}, password_hash=original)}
    r = client.post('/api/auth/mot-de-passe', headers=headers, json={
        'mot_de_passe_actuel': ACTUEL, 'nouveau_mot_de_passe': NOUVEAU})
    assert r.status_code == 204, r.text
    for session in (headers, autres_headers):
        assert client.get('/api/auth/me', headers=session).status_code == 401
    with Session(engine) as db:
        user = db.get(models.Utilisateur, user_id)
        assert verify_password(NOUVEAU, user.hashed_password)
        assert not verify_password(ACTUEL, user.hashed_password)
        email = user.email
        assert db.get(models.Utilisateur, 4).hashed_password == 'hash'
    assert client.post('/api/auth/login', json={'email': email, 'password': ACTUEL}).status_code == 401
    assert client.post('/api/auth/login', json={'email': email, 'password': NOUVEAU}).status_code == 200


@pytest.mark.parametrize('actuel,nouveau', [('incorrect', NOUVEAU), (ACTUEL, ACTUEL),
    (ACTUEL, 'password'), (ACTUEL, 'court'), (ACTUEL, ' ' * 10), (ACTUEL, 'secret\x00invalide'),
    (ACTUEL, 'é' * 2100)])
def test_erreur_ne_change_aucun_hash_ni_session(acces, actuel, nouveau):
    client, engine, headers, original = preparer(acces)
    r = client.post('/api/auth/mot-de-passe', headers=headers, json={
        'mot_de_passe_actuel': actuel, 'nouveau_mot_de_passe': nouveau})
    assert r.status_code == 400, r.text
    assert client.get('/api/auth/me', headers=headers).status_code == 200
    with Session(engine) as db:
        assert db.get(models.Utilisateur, 3).hashed_password == original


def test_changement_exige_authentification(acces):
    client, _ = acces
    assert client.post('/api/auth/mot-de-passe', json={
        'mot_de_passe_actuel': ACTUEL, 'nouveau_mot_de_passe': NOUVEAU}).status_code == 401
