"""Arrêt/redémarrage du seul backend créé par la fixture, jamais d'un service réel."""
from contextlib import closing
from pathlib import Path
from datetime import date
import json
import os
import subprocess
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import make_url
from test_factures_conservation923_isole import (
    application, application104, application103, application102, application101,
    application100, application099, application098, application097, application093,
    application092, application091, application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from cahier_formulaires773_support import ok
from cahier_suite777_support import core
from e2e_isole_support import BACK, arreter_processus_cree, attendre_http
from postgres_isole import verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]


def test_951_redemarrage_backend_brouillon_puis_validation_unique(application):
    app = application
    c = app['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    # Cet objet Popen provient du contexte isolé, pas d'une recherche de PID.
    initial = app['processus'][0]
    assert initial.poll() is None and '--host' in initial.args and '127.0.0.1' in initial.args
    assert Path(app['directory']).resolve().parent == (ROOT/'.codex-tests').resolve()
    nouveau = None
    enregistre = False
    preuve = {'nonce': c['nonce'], 'aucune_base_reelle': True, 'erreur': None}
    try:
        with closing(client(app)[0]) as api:
            sid = ok(api.get('/api/societe/moi'))['id']
            annee = date.today().year
            e = ok(api.post('/api/ecritures', json={'date': f'{annee}-01-02', 'journal': 'BQ',
                'reference': 'INCIDENT-FICTIF951', 'libelle': 'Brouillon avant arrêt FICTIF951',
                'lignes': [{'compte': '5141', 'debit': 1000}, {'compte': '1111', 'credit': 1000}]}), 201)
            avant = core(app, sid)
            assert len(avant) == 1 and not e['est_validee']
            with app['engine'].connect() as db:
                audit_avant = [dict(r._mapping) for r in db.execute(text('SELECT * FROM audit_actions WHERE societe_id=:s ORDER BY id'), {'s': sid})]
            arreter_processus_cree(initial)
            assert initial.poll() is not None
            assert core(app, sid) == avant
            env = os.environ.copy()
            env.update(DATABASE_URL=str(make_url(c['url']).set(username=app['role_sql'])),
                APP_ENV='test', HISABPRO_CREATE_TABLES='false',
                SECRET_KEY='secret-prive-synthetique-e2e-' + c['nonce'], ALGORITHM='HS256',
                CORS_ORIGINS=app['web_url'], PYTHON_DOTENV_DISABLED='1', PYTHONUTF8='1',
                HISABPRO_UPLOAD_DIR=str(app['uploads_dir']))
            assert make_url(env['DATABASE_URL']).set(username='hisabpro_recette') == make_url(c['url'])
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
            log = Path(app['directory'])/'reprise951.log'
            with log.open('ab') as sortie:
                nouveau = subprocess.Popen(initial.args, cwd=BACK, env=env, stdout=sortie,
                    stderr=subprocess.STDOUT, **options)
            app['enregistrer_processus'](nouveau)
            enregistre = True
            preuve.update(pid_initial=initial.pid, pid_redemarre=nouveau.pid)
            attendre_http(app['api_url']+'/api/health', nouveau, log)
            relues = ok(api.get('/api/ecritures', params={'exercice': annee}))
            assert len(relues) == 1 and relues[0]['id'] == e['id'] and not relues[0]['est_validee']
            assert core(app, sid) == avant
            valide = ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
            assert valide['numero_ecriture']
            officiel = core(app, sid)
            assert len(officiel) == 1
            assert api.post(f'/api/ecritures/{e["id"]}/valider').status_code == 400
            assert core(app, sid) == officiel
            with app['engine'].connect() as db:
                audit_apres = [dict(r._mapping) for r in db.execute(text('SELECT * FROM audit_actions WHERE societe_id=:s ORDER BY id'), {'s': sid})]
                assert all(r in audit_apres for r in audit_avant)
                assert db.scalar(text('SELECT count(*) FROM ecritures WHERE societe_id=:s AND est_validee'), {'s': sid}) == 1
                totaux = db.execute(text('SELECT sum(l.debit),sum(l.credit) FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s'), {'s': sid}).one()
                assert tuple(totaux) == (Decimal('1000'), Decimal('1000'))
            preuve.update(brouillon_id=e['id'], numero_validation=valide['numero_ecriture'],
                brouillon_conserve_apres_arret=True, validation_unique=True,
                debit_credit='1000.00', audit_anterieur_preserve=True,
                redemarrage_meme_cible_et_role=True)
    except BaseException as exc:
        preuve['erreur'] = repr(exc)
        raise
    finally:
        if nouveau is not None and not enregistre:
            arreter_processus_cree(nouveau)
            preuve['nouveau_processus_arrete'] = nouveau.poll() is not None
        preuve['nettoyage_du_nouveau_processus_confie_au_contexte'] = enregistre
        (ROOT/'.codex-tests/reprise951_preuve.json').write_text(json.dumps(preuve,
            ensure_ascii=False, indent=2), encoding='utf8')
