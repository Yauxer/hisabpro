"""Vérifie une montée de version sur COPIE isolée d'une sauvegarde (961).

Usage : python -X utf8 ops/verifier_montee_version_copie.py <sauvegarde.dump> <dossier_rapport> [--jusqua 70]

La sauvegarde (pg_dump -Fc avec propriétaires et droits) est restaurée dans un cluster
PostgreSQL éphémère (Test/postgres_isole.py, port distinct de 5432) : aucune base existante
n'est contactée. Commandes exactes de la procédure : constater --jusqua N, puis
appliquer --suivantes (deux fois). Contrôles : empreintes des données avant/après,
écritures validées équilibrées, API lancée sous le rôle « hisabpro » et sondage de toutes
les routes GET sans paramètre de chemin, pour chaque société et exercice présents.
Rapport JSON écrit dans <dossier_rapport>. Ne jamais livrer la sauvegarde dans un ZIP.
"""
import hashlib, hmac, json, os, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DUMP = Path(sys.argv[1]).resolve()
TMP = Path(sys.argv[2]).resolve()
JUSQUA = sys.argv[sys.argv.index('--jusqua') + 1] if '--jusqua' in sys.argv else '70'
for p in (ROOT / 'Test', ROOT / 'ops', ROOT / 'hisabpro-backend'):
    sys.path.insert(0, str(p))
os.environ.setdefault('PYTHON_DOTENV_DISABLED', '1')
os.environ['SECRET_KEY'] = 'copie961-' + os.urandom(8).hex()
os.environ['DATABASE_URL'] = 'postgresql://inerte@127.0.0.1:1/inerte'

import httpx
from jose import jwt
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from postgres_isole import binaires_postgres, cluster_isole, verifier_cible_isolee
from e2e_isole_support import attendre_http, port_loopback_libre
import postgres_sauvegarde as sauvegarde
import migrations_hisabpro as mh

RAPPORT = {'debut': datetime.now().isoformat(timespec='seconds')}


def empreintes(engine, colonnes=None):
    out, cols = {}, {}
    with engine.connect() as db:
        tables = db.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")).all()
        for t in tables:
            c = colonnes.get(t) if colonnes else db.scalars(text(
                "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:t ORDER BY ordinal_position"), {'t': t}).all()
            if c is None:
                continue
            liste = ', '.join(f'"{x}"' for x in c)
            out[t] = tuple(db.execute(text(
                f'SELECT count(*), md5(coalesce(string_agg(r::text, \'|\' ORDER BY r::text), \'\')) FROM (SELECT {liste} FROM public."{t}") r')).one())
            cols[t] = c
    return out, cols


def main():
    binaires, suffix = binaires_postgres()
    with cluster_isole() as c:
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        su = create_engine(c['url'])
        base = make_url(c['url']).database
        with su.begin() as db:
            # Fidèle à une installation standard : « postgres » est superutilisateur
            # (les contrôles de clés étrangères s'exécutent avec les droits du propriétaire).
            db.execute(text("CREATE ROLE postgres SUPERUSER NOLOGIN"))
            db.execute(text("CREATE ROLE hisabpro LOGIN PASSWORD 'copie961'"))
        r = subprocess.run([str(Path(binaires) / ('pg_restore' + suffix)), '--exit-on-error', '--single-transaction',
                            '--no-password', '--dbname', base, str(DUMP)], env=sauvegarde.connexion_pg(c['url']),
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
        RAPPORT['restauration'] = {'code': r.returncode, 'erreurs': r.stderr[-1500:]}
        assert r.returncode == 0, r.stderr[-1500:]
        import models
        with su.begin() as db:
            # Sauvegarde faite avec le rôle applicatif : la table qu'il ne peut pas lire est
            # absente ; sa structure est recréée depuis le modèle (sans données).
            if not db.scalar(text("SELECT to_regclass('public.decisions_affectation_resultat') IS NOT NULL")):
                models.Base.metadata.tables['decisions_affectation_resultat'].create(bind=db)
                db.execute(text("ALTER TABLE public.decisions_affectation_resultat OWNER TO postgres"))
                RAPPORT['table_recreee_sans_donnees'] = 'decisions_affectation_resultat'
            db.execute(text("SELECT setval('public.audit_ecritures_id_seq', GREATEST((SELECT COALESCE(max(id),0) FROM public.audit_ecritures),1))"))
        avant, colonnes = empreintes(su)
        RAPPORT['avant'] = {'tables': len(avant), 'lignes': sum(v[0] for v in avant.values())}
        os.environ['URL961'] = c['url']
        # Commandes exactes de la procédure utilisateur.
        mh.main(['constater', '--url-env', 'URL961', '--base-attendue', base, '--jusqua', JUSQUA])
        mh.main(['appliquer', '--url-env', 'URL961', '--base-attendue', base, '--suivantes'])
        mh.main(['appliquer', '--url-env', 'URL961', '--base-attendue', base, '--suivantes'])  # rejeu sans effet
        with su.connect() as db:
            RAPPORT['registre'] = {m: n for m, n in db.execute(text('SELECT mode, count(*) FROM hisabpro_migrations GROUP BY 1'))}
            RAPPORT['reparations_non_enregistrees'] = db.scalars(text(
                "SELECT unnest(ARRAY['065','067','070']) EXCEPT SELECT left(fichier,3) FROM hisabpro_migrations")).all()
        apres, _ = empreintes(su, colonnes)
        diffs = sorted(t for t in avant if avant[t] != apres.get(t))
        RAPPORT['donnees_inchangees'] = not diffs
        RAPPORT['tables_modifiees'] = {t: {'avant': avant[t], 'apres': apres.get(t)} for t in diffs}
        with su.connect() as db:
            for t in diffs:
                # Lignes d'origine encore présentes à l'identique ?
                liste = ', '.join(f'"{x}"' for x in colonnes[t])
                RAPPORT['tables_modifiees'][t]['lignes_origine_modifiees_ou_supprimees'] = None
        with su.connect() as db:
            RAPPORT['tables_apres'] = db.scalar(text("SELECT count(*) FROM pg_tables WHERE schemaname='public'"))
            RAPPORT['ecritures_desequilibrees'] = db.scalar(text(
                "SELECT count(*) FROM (SELECT e.id FROM ecritures e JOIN lignes_ecriture l ON l.ecriture_id=e.id "
                "WHERE e.est_validee GROUP BY e.id HAVING sum(l.debit)<>sum(l.credit)) x"))
            users = db.execute(text(
                "SELECT DISTINCT ON (s.sid) u.id, s.sid AS societe_id, u.hashed_password, s.role FROM ("
                " SELECT id AS uid, societe_id AS sid, role FROM utilisateurs WHERE actif"
                " UNION ALL SELECT utilisateur_id, societe_id, role FROM utilisateurs_societes WHERE actif) s"
                " JOIN utilisateurs u ON u.id=s.uid AND u.actif"
                " WHERE s.role IN ('admin','comptable') ORDER BY s.sid, (s.role='admin') DESC, u.id")).all()
            exercices = db.execute(text("SELECT DISTINCT societe_id, exercice FROM ecritures ORDER BY 1,2")).all()
        RAPPORT['societes_admins'] = len({u.societe_id for u in users})
        RAPPORT['exercices'] = [list(x) for x in exercices]
        # API sous le rôle applicatif, comme en production.
        port = port_loopback_libre()
        url_app = make_url(c['url']).set(username='hisabpro', password='copie961').render_as_string(hide_password=False)
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')}
        env.update(DATABASE_URL=url_app, APP_ENV='test', HISABPRO_CREATE_TABLES='false', PYTHONUTF8='1',
                   PYTHON_DOTENV_DISABLED='1', HISABPRO_UPLOAD_DIR=str(Path(c['directory']) / 'uploads'),
                   CORS_ORIGINS='http://127.0.0.1:9')
        log = Path(c['directory']) / 'api.log'
        with log.open('w', encoding='utf-8') as sortie:
            proc = subprocess.Popen([sys.executable, '-X', 'utf8', '-m', 'uvicorn', 'main:app', '--host', '127.0.0.1',
                                     '--port', str(port), '--log-level', 'warning'], cwd=ROOT / 'hisabpro-backend',
                                    env=env, stdout=sortie, stderr=subprocess.STDOUT)
            try:
                api = f'http://127.0.0.1:{port}'
                attendre_http(api + '/api/health', proc, log)
                spec = httpx.get(api + '/openapi.json', timeout=60).json()
                routes = sorted(p for p, ops in spec['paths'].items() if 'get' in ops and '{' not in p and p.startswith('/api/'))
                RAPPORT['routes_get'] = len(routes)
                sondes = []
                for u in users:
                    pv = hmac.new(os.environ['SECRET_KEY'].encode(), u.hashed_password.encode(), hashlib.sha256).hexdigest()
                    tok = jwt.encode({'sub': str(u.id), 'societe_id': u.societe_id, 'role': u.role, 'pwd_version': pv,
                                      'exp': datetime.utcnow() + timedelta(hours=1)}, os.environ['SECRET_KEY'], algorithm='HS256')
                    annees = sorted({e for s, e in exercices if s == u.societe_id}) or [2026]
                    with httpx.Client(base_url=api, headers={'Authorization': 'Bearer ' + tok}, timeout=120) as cl:
                        for annee in annees:
                            for route in routes:
                                rr = cl.get(route, params={'exercice': annee, 'annee': annee}); st = rr.status_code
                                sondes.append({'societe': u.societe_id, 'annee': annee, 'route': route, 'code': st,
                                               'detail': rr.text[:200] if st in (409, 500) else None})
                            for route in (f'/api/etats/source/{annee}', f'/api/etats/etic/{annee}', f'/api/cloture/etat',
                                          '/api/fec/export', '/api/ecritures/reporting/grand-livre'):
                                rr = cl.get(route, params={'exercice': annee}); st = rr.status_code
                                sondes.append({'societe': u.societe_id, 'annee': annee, 'route': route, 'code': st,
                                               'detail': rr.text[:200] if st in (409, 500) else None})
                            for m in range(1, 13):
                                st = cl.get('/api/tva/declaration', params={'exercice': annee, 'mois': m}).status_code
                                sondes.append({'societe': u.societe_id, 'annee': annee, 'route': f'/api/tva/declaration?mois={m}', 'code': st})
                RAPPORT['sondes'] = len(sondes)
                RAPPORT['sondes_5xx'] = [s for s in sondes if s['code'] >= 500]
                RAPPORT['sondes_409'] = [s for s in sondes if s['code'] == 409]
                RAPPORT['codes'] = {str(k): sum(1 for s in sondes if s['code'] == k) for k in sorted({s['code'] for s in sondes})}
            finally:
                proc.terminate(); proc.wait(timeout=30)
                erreurs = [l for l in log.read_text(encoding='utf-8', errors='replace').splitlines()
                           if 'Error' in l or 'Exception' in l]
                RAPPORT['api_erreurs_log'] = erreurs[-40:]
        su.dispose()


try:
    main()
    RAPPORT['statut'] = 'termine'
except BaseException as exc:
    RAPPORT['statut'] = 'echec'
    RAPPORT['erreur'] = (repr(exc))[:1500]
finally:
    RAPPORT['fin'] = datetime.now().isoformat(timespec='seconds')
    (TMP / 'rapport_montee_version.json').write_text(json.dumps(RAPPORT, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    print(json.dumps({k: v for k, v in RAPPORT.items() if k not in ('migrations',)}, ensure_ascii=False, default=str)[:3000])
    if 'migrations' in RAPPORT:
        print('migrations :', sum(1 for m in RAPPORT['migrations'] if m['statut'] == 'ok'), 'ok ;',
              [m for m in RAPPORT['migrations'] if m['statut'] != 'ok'])
