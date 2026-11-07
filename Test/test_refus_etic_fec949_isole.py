"""Refus ETIC et historique incomplet : vraie API/PostgreSQL, sans réparation."""
from contextlib import closing
from decimal import Decimal as D
from pathlib import Path
import json

import pytest
from sqlalchemy.orm import Session
import models
from fiscal947_support import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
    client, ok, core,
)
from postgres_isole import verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]


def dossier(api, app, nature='vente', nombre=1):
    c = app['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    sid = ok(api.patch('/api/societe/moi', json={'exercice_debut': 2025}))['id']
    tiers = ok(api.post('/api/tiers', json={'nom': 'Tiers FICTIF949',
        'type': 'client' if nature == 'vente' else 'fournisseur'}), 201)
    for n in range(nombre):
        f = ok(api.post('/api/factures', json={'type': nature, 'tiers_id': tiers['id'],
            'tiers': tiers['nom'], 'date': '2025-12-01', 'date_echeance': '2025-12-31',
            'reference': f'SOURCE-FICTIVE949-{n}',
            'lignes': [{'description': 'Service FICTIF949', 'quantite': 1, 'prix_unitaire': 400, 'tva': 20}]}), 201)
        ok(api.post(f'/api/factures/{f["id"]}/valider'))
        ec = ok(api.post(f'/api/factures/{f["id"]}/comptabiliser'))
        ok(api.post(f'/api/ecritures/{ec["ecriture_id"]}/valider'))
    return sid, tiers


def section(api, code):
    return next(s for s in ok(api.get('/api/etats/etic/2025'))['sections'] if s['code'] == code)


def enregistrer_preuve(nom, **v):
    (ROOT/f'.codex-tests/etic949_{nom}.json').write_text(json.dumps(v, ensure_ascii=False,
        indent=2, default=str), encoding='utf8')


@pytest.mark.parametrize('valeur', [-1, 'NaN', 'Infinity', '-Infinity', 'abc'])
@pytest.mark.parametrize('confirme', [False, True])
def test_949_b6_montant_invalide_refuse_sans_mutation(application, valeur, confirme):
    with closing(client(application)[0]) as api:
        sid, _ = dossier(api, application)
        avant = core(application, sid)
        initial = section(api, 'B6')
        body = {'confirme': confirme, 'autres_analyses_neant': True,
            'ventilations': {'3421': {'plus_un_an': 0, 'moins_un_an': 0, 'echues': valeur}}}
        r = api.put('/api/etats/etic/2025/B6', json={'contenu': body})
        assert r.status_code == 422 and 'montant fini' in r.text, r.text
        assert section(api, 'B6')['contenu'] == initial['contenu']
        assert core(application, sid) == avant


def test_949_b6_vide_inconnu_et_zero_explicitement_prioritaire(application):
    with closing(client(application)[0]) as api:
        sid, tiers = dossier(api, application, nombre=0)
        e = ok(api.post('/api/ecritures', json={'date': '2025-12-01', 'journal': 'OD',
            'reference': 'ECHEANCE-INCONNUE-FICTIVE949', 'libelle': 'Échéance non documentée FICTIVE949',
            'lignes': [{'compte': '3421', 'debit': 480, 'tiers_id': tiers['id']},
                       {'compte': '1111', 'credit': 480}]}), 201)
        ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
        avant = core(application, sid)
        # Les valeurs manquantes restent inconnues dans un brouillon conservable.
        body = {'confirme': False, 'autres_analyses_neant': True,
            'ventilations': {'3421': {'plus_un_an': 0, 'moins_un_an': 0, 'echues': ''}}}
        ok(api.put('/api/etats/etic/2025/B6', json={'contenu': body}))
        vide = section(api, 'B6')
        assert vide['ventilation'][0]['echues'] is None and not vide['complete']
        body['ventilations']['3421'].update(echues=0, moins_un_an=480)
        body['notes'] = 'Ventilation manuelle FICTIVE de recette : zéro explicite, sans qualification de données réelles.'
        ok(api.put('/api/etats/etic/2025/B6', json={'contenu': body}))
        zero = section(api, 'B6')
        assert zero['ventilation'][0]['echues'] == 0
        assert zero['ventilation'][0]['moins_un_an'] == 480
        assert core(application, sid) == avant
        enregistrer_preuve('zero', vide=vide, zero=zero, ecritures_inchangees=True)


def test_949_zero_manuel_prioritaire_sur_auto_certaine(application):
    with closing(client(application)[0]) as api:
        sid, _ = dossier(api, application)
        avant = core(application, sid)
        assert section(api, 'B6')['ventilation'][0]['echues'] == 480
        body = {'confirme': False, 'autres_analyses_neant': True,
            'notes': 'Brouillon FICTIF de test du zéro explicite ;aucune qualification finale.',
            'ventilations': {'3421': {'plus_un_an': 0, 'moins_un_an': 480, 'echues': 0}}}
        ok(api.put('/api/etats/etic/2025/B6', json={'contenu': body}))
        assert section(api, 'B6')['ventilation'][0]['echues'] == 0
        assert not section(api, 'B6')['complete'] and core(application, sid) == avant


@pytest.mark.parametrize('ventilations', [[], {'3421': 'texte invalide'}])
def test_949_structure_ventilation_invalide_refusee(application, ventilations):
    with closing(client(application)[0]) as api:
        sid, _ = dossier(api, application)
        avant = core(application, sid)
        initial = section(api, 'B6')['contenu']
        r = api.put('/api/etats/etic/2025/B6', json={'contenu': {
            'confirme': False, 'ventilations': ventilations}})
        assert r.status_code == 422, r.text
        assert section(api, 'B6')['contenu'] == initial and core(application, sid) == avant


def test_949_b7_total480_ventilation479_refuse_confirmation(application):
    with closing(client(application)[0]) as api:
        sid, _ = dossier(api, application, 'achat')
        avant = core(application, sid)
        body = {'confirme': False, 'autres_analyses_neant': True,
            'ventilations': {'4411': {'plus_un_an': 0, 'moins_un_an': 0, 'echues': 479}}}
        ok(api.put('/api/etats/etic/2025/B7', json={'contenu': body}))
        brouillon = section(api, 'B7')
        assert not brouillon['complete'] and brouillon['erreurs_ventilation']
        ligne = brouillon['ventilation'][0]
        assert D(str(ligne['total'])) == 480 and D(str(ligne['echues'])) == 479
        body['confirme'] = True
        refus = api.put('/api/etats/etic/2025/B7', json={'contenu': body})
        assert refus.status_code == 422, refus.text
        assert section(api, 'B7')['contenu'] == brouillon['contenu']
        assert api.post('/api/etats/liasse/2025/finaliser').status_code == 409
        assert core(application, sid) == avant
        enregistrer_preuve('479', section=brouillon, confirmation_refusee=422,
                           finalisation_refusee=409, ecritures_inchangees=True)


def test_949_piece_historique_absente_reliquat_visible_sans_invention(application):
    with closing(client(application)[0]) as api:
        sid, tiers = dossier(api, application, nombre=2)
        e = ok(api.post('/api/ecritures', json={'date': '2025-12-02', 'journal': 'OD',
            'libelle': 'Ancienne opération FICTIVE949 sans pièce, sources ambiguës',
            'lignes': [{'compte': '3421', 'debit': 480, 'tiers_id': tiers['id']},
                       {'compte': '1111', 'credit': 480}]}), 201)
        # Les triggers actuels complètent la date des nouveaux enregistrements.
        # Ne pas les désactiver pour prétendre reproduire un ancien NULL.
        ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
        with Session(application['engine']) as db:
            date_piece_avant = db.get(models.Ecriture, e['id']).date_piece
        avant = core(application, sid)
        fec = ok(api.get('/api/fec/apercu', params={'exercice': 2025}))
        assert 'REFERENCE_PIECE_MANQUANTE' in json.dumps(fec)
        b6 = section(api, 'B6')
        ligne = next(x for x in b6['automatique']['lignes'] if x['compte'] == '3421')
        assert D(str(ligne['montant'])) == 1440
        assert D(str(ligne['echeance_auto_total'])) == 960
        assert D(str(ligne['echeance_auto_ecart'])) == 480
        assert not b6['complete']
        with Session(application['engine']) as db:
            source = db.get(models.Ecriture, e['id'])
            assert source.est_validee and source.reference is None and source.date_piece == date_piece_avant
        assert core(application, sid) == avant
        enregistrer_preuve('historique', fec=fec, section=b6,
            source_definitive_sans_reference_preservee=True, reliquat_non_reclasse='480.00',
            date_piece_conservee=str(date_piece_avant),
            limite='Ancienne date pièce NULL non reproduite ;triggers de création préservés,aucune protection désactivée.')
