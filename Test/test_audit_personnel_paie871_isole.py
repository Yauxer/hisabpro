"""Caractérisation Lot 0, pas critères d'acceptation du nouveau Personnel & Paie.

Ces constats attendent les comportements ACTUELS, y compris les écarts au master.
Les tests doivent être remplacés par les refus ciblés lors de l'activation Lot 1.
Aucun montant, nom, numéro CNSS ni jeton n'est conservé dans la preuve.
"""
from datetime import date
import json
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text
from test_paie_grh_postgres import app_paie, application, compte, dossier
from postgres_isole import verifier_cible_isolee


@pytest.fixture(scope='module')
def preuves871():
    constats = []
    yield constats
    p = Path(__file__).resolve().parents[1] / '.codex-tests/personnel871_constats.json'
    p.write_text(json.dumps({'nature': 'Caractérisation existant, pas validation master',
                             'constats': constats}, ensure_ascii=False, indent=2), encoding='utf8')


def nombre_ecritures(app, sid):
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    with app['engine'].connect() as db:
        return db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s'), {'s': sid})


def test_871_constat_doublon_et_salaire_ecrase_actuels(app_paie, preuves871):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        sid = api.get('/api/auth/me').json()['societe_id']
        a = api.post('/api/employes', json=dossier())
        b = api.post('/api/employes', json=dossier(nom='Second dossier fictif871'))
        assert a.status_code == b.status_code == 201
        assert a.json()['id'] != b.json()['id'] and a.json()['matricule'] == b.json()['matricule']
        assert a.json()['actif'] is True
        r = api.put(f"/api/employes/{a.json()['id']}", json=dossier(salaire_brut=11000))
        assert r.status_code == 200 and r.json()['salaire_brut'] == 11000
        assert nombre_ecritures(app_paie, sid) == 0
        preuves871.append({'id': 'C01', 'doublons_matricule_meme_societe_acceptes': [201, 201],
                           'creation_active_sans_approbation': True, 'PUT_salaire_immediat': 200,
                           'ecritures_creees': 0, 'ecart_master': 'Unicité, activation et salaire à date d’effet à construire.'})


def test_871_constat_lecture_salaire_cnss_non_masques_actuelle(app_paie, preuves871):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        emp = api.post('/api/employes', json=dossier())
        assert emp.status_code == 201
        email = f'lecture871-{uuid4().hex[:8]}@hisabpro-recette.example'
        password = 'LectureFictive871!'
        r = api.post('/api/utilisateurs', json={'nom': 'Lecteur fictif871', 'email': email,
                                               'mot_de_passe': password, 'role': 'lecture'})
        assert r.status_code == 201
        r = api.post('/api/auth/login', json={'email': email, 'password': password})
        assert r.status_code == 200
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        r = api.get('/api/employes')
        assert r.status_code == 200
        row = next(x for x in r.json() if x['id'] == emp.json()['id'])
        assert row['salaire_brut'] == emp.json()['salaire_brut']
        assert row['numero_cnss'] == emp.json()['numero_cnss']
        assert api.post('/api/employes', json=dossier()).status_code == 403
        preuves871.append({'id': 'C02', 'lecture_liste': 200, 'montant_salaire_retourne_sans_masque': True,
                           'numero_cnss_retourne_sans_masque': True, 'creation_refusee_lecture': 403,
                           'ecart_master': 'Lecture financière/documentaire à habiliter et projections API à masquer.'})


def test_871_garde_reglement_hors_facture_existant(app_paie, preuves871):
    with httpx.Client(base_url=app_paie['api_url']) as api:
        compte(api)
        sid = api.get('/api/auth/me').json()['societe_id']
        r = api.post('/api/reglements', json={'date': date.today().isoformat(),
                     'tiers': 'Bénéficiaire fictif871', 'montant': 100, 'mode': 'virement'})
        assert r.status_code == 422 and 'facture' in r.json()['detail']
        assert nombre_ecritures(app_paie, sid) == 0
        preuves871.append({'id': 'C03', 'reglement_sans_facture_refuse': 422, 'ecritures_creees': 0,
                           'consequence': 'Adapter trésorerie hors facturation ; aucune fausse facture salariale.'})
