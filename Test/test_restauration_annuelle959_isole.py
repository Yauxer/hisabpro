"""Dossier annuel fictif complet : sauvegarde native puis restauration sur base vierge isolée (959).

Scénario existant (ventes, achats, ventilations, lettrage, clôture 2025, à-nouveaux et
règlements 2026), sauvegarde par ops/postgres_sauvegarde.py, restauration dans un
second cluster nonce, puis comparaison des tables, séquences et sorties métier servies
par une seconde API. Aucune base utilisateur.
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

import httpx
from jose import jwt
from sqlalchemy import create_engine, text

from e2e_isole_support import attendre_http, port_loopback_libre
from postgres_isole import binaires_postgres, cluster_isole, verifier_cible_isolee
from test_e2e_facturation_isole import application  # noqa: F401
from test_rapprochement_ventilation_isole import migration  # noqa: F401
from test_e2e_annee_ventilation_inter_exercices_isole import (
    test_annee_ventilation_cloture_an_reglements_anciens_lettrage_et_exports as scenario_annuel,
)

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
sys.path.insert(0, str(ROOT / 'ops'))
import postgres_sauvegarde as sauvegarde  # noqa: E402


def empreinte_base(url):
    engine = create_engine(url)
    try:
        with engine.connect() as db:
            tables = db.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")).all()
            out = {t: db.execute(text(
                f'SELECT count(*), md5(coalesce(string_agg(x::text, \'|\' ORDER BY x::text), \'\')) FROM public."{t}" x'
            )).one() for t in tables}
            seqs = db.execute(text("SELECT sequencename, last_value FROM pg_sequences WHERE schemaname='public' ORDER BY 1")).all()
        return {k: tuple(v) for k, v in out.items()}, dict(seqs)
    finally:
        engine.dispose()


def jeton(secret, user):
    pwd = hmac.new(secret.encode(), user.hashed_password.encode(), hashlib.sha256).hexdigest()
    return jwt.encode({'sub': str(user.id), 'societe_id': user.societe_id, 'role': user.role,
                       'pwd_version': pwd, 'exp': datetime.utcnow() + timedelta(hours=2)}, secret, algorithm='HS256')


ROUTES = [('/api/ecritures/reporting/balance', {'exercice': 2025}),
          ('/api/ecritures/reporting/balance', {'exercice': 2026}),
          ('/api/ecritures/reporting/grand-livre', {'exercice': 2025}),
          ('/api/fec/export', {'exercice': 2025}),
          ('/api/etats/source/2025', {}),
          ('/api/cloture/etat', {'exercice': 2025}),
          ('/api/factures', {'exercice': 2025}), ('/api/factures', {'exercice': 2026}),
          ] + [('/api/lettrage/comptable', {'exercice': a, 'compte': c}) for a in (2025, 2026) for c in ('3421', '4411')] + [
          ('/api/tva/declaration', {'exercice': 2025, 'mois': m}) for m in range(1, 13)]


def sorties(api_url, token):
    with httpx.Client(base_url=api_url, headers={'Authorization': 'Bearer ' + token}, timeout=120) as api:
        out = {}
        for route, params in ROUTES:
            r = api.get(route, params=params)
            assert r.status_code == 200, (route, params, r.status_code, r.text[:300])
            cle = route + '?' + json.dumps(params, sort_keys=True)
            out[cle] = r.json() if 'json' in r.headers.get('content-type', '') else hashlib.sha256(r.content).hexdigest()
        return out


def test_959_dossier_annuel_sauvegarde_restaure_et_identique(application, migration, tmp_path):
    scenario_annuel(application, tmp_path)
    c = application['cluster']
    assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    secret = 'secret-prive-synthetique-e2e-' + c['nonce']
    engine = create_engine(c['url'])
    try:
        with engine.connect() as db:
            sid = db.scalar(text('SELECT societe_id FROM clotures_exercice WHERE exercice=2025 ORDER BY id LIMIT 1'))
            assert sid, 'Le scénario doit avoir clôturé 2025'
            user = db.execute(text("SELECT id, societe_id, hashed_password, role FROM utilisateurs "
                                   "WHERE societe_id=:s AND role='admin' ORDER BY id LIMIT 1"), {'s': sid}).one()
    finally:
        engine.dispose()
    token = jeton(secret, user)
    avant = sorties(application['api_url'], token)
    base_avant, seq_avant = empreinte_base(c['url'])
    assert base_avant['clotures_exercice'][0] >= 1 and base_avant['ecritures'][0] > 0

    binaires, _ = binaires_postgres()
    archive = sauvegarde.sauvegarder(c['url'], tmp_path / 'dossier_annuel_fictif.dump', binaires)
    assert archive.stat().st_size > 0
    with cluster_isole() as cible:
        assert verifier_cible_isolee(cible['url'], cible['directory'], cible['nonce'])
        sauvegarde.restaurer_isole(cible['url'], archive, binaires, cible['directory'], cible['nonce'])
        base_apres, seq_apres = empreinte_base(cible['url'])
        assert base_apres == base_avant
        assert seq_apres == seq_avant
        # Pièces : copie du stockage configuré, comme le prévoit la procédure d'exploitation.
        uploads = Path(cible['directory']) / 'uploads'
        if Path(application['uploads_dir']).exists():
            shutil.copytree(application['uploads_dir'], uploads)
        else:
            uploads.mkdir()
        port = port_loopback_libre()
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')}
        env.update(DATABASE_URL=cible['url'], APP_ENV='test', HISABPRO_CREATE_TABLES='false', SECRET_KEY=secret,
                   ALGORITHM='HS256', PYTHON_DOTENV_DISABLED='1', PYTHONUTF8='1', HISABPRO_UPLOAD_DIR=str(uploads),
                   CORS_ORIGINS='http://127.0.0.1:9')
        log = Path(cible['directory']) / 'api_restauree.log'
        with log.open('w', encoding='utf-8') as sortie:
            proc = subprocess.Popen([sys.executable, '-X', 'utf8', '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1',
                                     '--port', str(port), '--log-level', 'warning'], cwd=BACK, env=env,
                                    stdout=sortie, stderr=subprocess.STDOUT)
            try:
                url = f'http://127.0.0.1:{port}'
                attendre_http(url + '/api/health', proc, log)
                apres = sorties(url, token)
            finally:
                proc.terminate()
                proc.wait(timeout=30)
    differences = [k for k in avant if avant[k] != apres[k]]
    if differences:
        (ROOT / '.codex-tests/restauration_annuelle959_ecarts.json').write_text(json.dumps(
            {k: {'avant': avant[k], 'apres': apres[k]} for k in differences}, ensure_ascii=False, indent=2,
            default=str), encoding='utf-8')
    assert not differences, differences
    (ROOT / '.codex-tests/restauration_annuelle959_preuve.json').write_text(json.dumps({
        'tables': len(base_avant), 'lignes': sum(v[0] for v in base_avant.values()),
        'sequences': len(seq_avant), 'sorties_comparees': sorted(avant),
        'archive_octets': archive.stat().st_size,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
