"""Exercices implicites : vraie API et PostgreSQL nonce, sans prérequis masquant."""
from contextlib import closing
from datetime import date
from decimal import Decimal
from pathlib import Path
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import models
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client


def cible(application):
    c = application['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])


def photographie(application):
    cible(application)
    with application['engine'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY id')).scalars().all()
                for t in ('exercices_comptables', 'periodes_comptables', 'ecritures',
                          'lignes_ecriture', 'audit_periodes_comptables')}


def dossier(application):
    cible(application)
    api, _, _ = client(application)
    r = api.get('/api/societe/moi')
    assert r.status_code == 200, r.text
    return api, r.json()['id']


def ok(application, response, attendu):
    if response.status_code != attendu:
        # Le traceback de la vraie API est sauvegardé avant nettoyage fixture.
        journal = application['api_log'].read_text(encoding='utf-8', errors='replace')
        preuve = Path(__file__).resolve().parents[1] / '.codex-tests' / (
            'exercice_implicite_318_api_echec_'+uuid.uuid4().hex[:10]+'.log')
        preuve.parent.mkdir(exist_ok=True)
        preuve.write_text(journal, encoding='utf-8')
        print('Journal API isolée sauvegardé :', preuve)
        print(journal[-30000:])
    assert response.status_code == attendu, response.text
    return response.json()


def payload(annee):
    return {'date': f'{annee}-12-31', 'journal': 'OD',
            'reference': 'CAPITAL-IMPLICITE-'+uuid.uuid4().hex[:10],
            'libelle': 'Capital fictif exercice implicite',
            'lignes': [{'compte': '5141', 'debit': 1000, 'credit': 0},
                       {'compte': '1111', 'debit': 0, 'credit': 1000}]}


def controle_persistant(application, sid, annee, eid, *, validee):
    cible(application)
    with Session(application['engine']) as db:
        ex = db.query(models.ExerciceComptable).filter_by(societe_id=sid, annee=annee).one()
        periodes = db.query(models.PeriodeComptable).filter_by(exercice_id=ex.id).order_by(
            models.PeriodeComptable.numero).all()
        assert len(periodes) == 12
        assert all(p.statut == 'ouverte' for p in periodes)
        assert periodes[0].date_debut == date(annee, 1, 1)
        assert periodes[-1].date_fin == date(annee, 12, 31)
        ec = db.get(models.Ecriture, eid)
        assert ec.societe_id == sid and ec.exercice == annee and ec.est_validee is validee
        assert len(ec.lignes) == 2
        assert sum((Decimal(str(l.debit)) for l in ec.lignes), Decimal('0')) == 1000
        assert sum((Decimal(str(l.credit)) for l in ec.lignes), Decimal('0')) == 1000
        return [(l.id, l.compte, str(l.debit), str(l.credit)) for l in ec.lignes]


@pytest.mark.parametrize('exercice_existant_sans_periodes', [False, True])
def test_creation_implicite_persiste_periodes_avant_ecriture(application, exercice_existant_sans_periodes):
    api, sid = dossier(application)
    annee = date.today().year - 1
    with closing(api):
        if exercice_existant_sans_periodes:
            # État historique synthétique : exercice seul, aucun DELETE de période.
            with Session(application['engine']) as db:
                db.add(models.ExerciceComptable(societe_id=sid, annee=annee,
                    date_debut=date(annee, 1, 1), date_fin=date(annee, 12, 31), statut='ouvert'))
                db.commit()
        avant = photographie(application)
        r = api.post('/api/ecritures', json=payload(annee))
        ec = ok(application, r, 201)
        assert ec['est_validee'] is False
        lignes = controle_persistant(application, sid, annee, ec['id'], validee=False)
        ok(application, api.post(f"/api/ecritures/{ec['id']}/valider"), 200)
        assert controle_persistant(application, sid, annee, ec['id'], validee=True) == lignes
        apres = photographie(application)
        assert len(apres['ecritures']) == len(avant['ecritures']) + 1
        assert len(apres['lignes_ecriture']) == len(avant['lignes_ecriture']) + 2
        assert len(apres['periodes_comptables']) == len(avant['periodes_comptables']) + 12
        assert len(apres['exercices_comptables']) == len(avant['exercices_comptables']) + (
            0 if exercice_existant_sans_periodes else 1)


@pytest.mark.parametrize('erreur', ['balance', 'compte'])
def test_refus_metier_annule_exercice_et_periodes_implicites(application, erreur):
    api, sid = dossier(application)
    annee = date.today().year - 1
    with closing(api):
        data = payload(annee)
        if erreur == 'balance':
            data['lignes'][1]['credit'] = 900
        else:
            data['lignes'][1]['compte'] = '999999'
        avant = photographie(application)
        response = api.post('/api/ecritures', json=data)
        detail = ok(application, response, 422 if erreur == 'balance' else 400)['detail']
        assert ('non équilibrée' in str(detail)) if erreur == 'balance' else ('absent' in detail)
        assert photographie(application) == avant


@pytest.mark.parametrize('fermeture', ['periode', 'exercice'])
def test_exercice_ou_periode_fermes_restent_bloquants(application, fermeture):
    api, sid = dossier(application)
    annee = date.today().year - 1
    with closing(api):
        ok(application, api.post('/api/exercices', json={'annee': annee,
            'date_debut': f'{annee}-01-01', 'date_fin': f'{annee}-12-31'}), 201)
        ok(application, api.patch(f'/api/exercices/{annee}/periodes/12', json={'statut': 'fermee'}), 200)
        if fermeture == 'exercice':
            # Prérequis négatif synthétique, exclusivement sur cluster nonce.
            with application['engine'].begin() as db:
                db.execute(text("UPDATE exercices_comptables SET statut='cloture' "
                                'WHERE societe_id=:sid AND annee=:a'), {'sid': sid, 'a': annee})
        avant = photographie(application)
        response = api.post('/api/ecritures', json=payload(annee))
        detail = ok(application, response, 423)['detail']
        assert ('clôturé' in detail) if fermeture == 'exercice' else ('fermée' in detail)
        assert photographie(application) == avant


def test_exercice_implicite_sans_creation_dans_autre_societe(application):
    api, sid = dossier(application)
    autre, autre_sid = dossier(application)
    annee = date.today().year - 1
    with closing(api), closing(autre):
        with application['engine'].connect() as db:
            autre_avant = db.execute(text('SELECT row_to_json(e)::text FROM exercices_comptables e '
                'WHERE societe_id=:sid ORDER BY id'), {'sid': autre_sid}).scalars().all()
        ec = ok(application, api.post('/api/ecritures', json=payload(annee)), 201)
        controle_persistant(application, sid, annee, ec['id'], validee=False)
        assert autre.post(f"/api/ecritures/{ec['id']}/valider").status_code == 404
        with application['engine'].connect() as db:
            assert db.execute(text('SELECT row_to_json(e)::text FROM exercices_comptables e '
                'WHERE societe_id=:sid ORDER BY id'), {'sid': autre_sid}).scalars().all() == autre_avant
            assert db.execute(text('SELECT count(*) FROM ecritures WHERE societe_id=:sid'),
                              {'sid': autre_sid}).scalar_one() == 0


def test_calendrier_partiel_historique_ne_devient_pas_douze_periodes(application):
    api, sid = dossier(application)
    annee = date.today().year - 1
    with closing(api):
        # Calendrier synthétique incomplet, sans supprimer une période existante.
        with Session(application['engine']) as db:
            ex = models.ExerciceComptable(societe_id=sid, annee=annee,
                date_debut=date(annee, 1, 1), date_fin=date(annee, 12, 31), statut='ouvert')
            db.add(ex)
            db.flush()
            db.add(models.PeriodeComptable(exercice_id=ex.id, numero=1, libelle='Janvier',
                date_debut=date(annee, 1, 1), date_fin=date(annee, 1, 31), statut='ouverte'))
            db.commit()
        avant = photographie(application)
        r = api.post('/api/ecritures', json=payload(annee))
        detail = ok(application, r, 423)['detail']
        assert 'période' in detail.lower()
        assert photographie(application) == avant
