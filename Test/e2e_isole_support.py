"""UI complète + vraie API, exclusivement PostgreSQL éphémère et loopback.

Ne lit aucun .env : python-dotenv est désactivé ; esbuild définit explicitement
import.meta.env. Tous les serveurs créés ici sont arrêtés au finally.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import urlopen

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from postgres_isole import cluster_isole, verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / "hisabpro-backend"


class DossierE2E(tempfile.TemporaryDirectory):
    def cleanup(self):
        cible = Path(self.name).resolve()
        espace = (ROOT / ".codex-tests").resolve()
        if cible.parent != espace or not cible.name.startswith("hisabpro_e2e_"):
            raise RuntimeError("Nettoyage E2E refusé hors du dossier temporaire attendu.")
        # Sous Windows, un handle de journal peut rester brièvement verrouillé
        # après la fin du processus. Un verrou permanent reste une erreur.
        for essai in range(20):
            try:
                return super().cleanup()
            except PermissionError:
                if essai == 19:
                    raise
                time.sleep(0.1)


def port_loopback_libre():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    if port in {5432, 8000, 3000}:
        return port_loopback_libre()
    return port


def attendre_http(url, processus, log, timeout=45):
    limite = time.monotonic() + timeout
    while time.monotonic() < limite:
        if processus.poll() is not None:
            raise RuntimeError("Serveur E2E arrêté : " + log.read_text(encoding="utf-8", errors="replace")[-4000:])
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.1)
    raise RuntimeError("Serveur E2E indisponible : " + log.read_text(encoding="utf-8", errors="replace")[-4000:])


def arreter_processus_cree(processus):
    if processus.poll() is not None:
        return
    # PID issu exclusivement de Popen dans ce contexte ; aucune recherche par
    # nom de processus, aucun arrêt du PostgreSQL ou serveur réel de l'utilisateur.
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(processus.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        os.killpg(processus.pid, signal.SIGTERM)
    try:
        processus.wait(timeout=15)
    except subprocess.TimeoutExpired:
        processus.kill()
        processus.wait(timeout=5)


@contextmanager
def application_isolee(*, preparer_runtime=None):
    import models
    from database import Base

    node = shutil.which("node")
    if not node or not (ROOT / "node_modules/esbuild").is_dir():
        raise RuntimeError("Node/esbuild locaux requis pour la recette E2E.")
    espace = (ROOT / ".codex-tests").resolve()
    espace.mkdir(exist_ok=True)
    with cluster_isole() as cluster, DossierE2E(prefix="hisabpro_e2e_", dir=espace) as temp:
        temp = Path(temp).resolve()
        assert temp.is_relative_to(espace) and temp.name.startswith("hisabpro_e2e_")
        verifier_cible_isolee(cluster["url"], cluster["directory"], cluster["nonce"])
        engine = create_engine(cluster["url"])
        processus, journaux = [], []
        web_server = web_thread = None
        try:
            # La garde précède strictement tout DDL et toute création serveur.
            Base.metadata.create_all(engine)
            with engine.connect() as connection:
                raw = connection.connection.driver_connection
                with raw.cursor() as cursor:
                    cursor.execute((BACK / "036_production_hardening.sql").read_text(encoding="utf-8"))
                raw.commit()
            with Session(engine) as db:
                # Référentiel volontairement limité et synthétique ; pas de
                # prétention de recette exhaustive du plan CGNC.
                db.add_all([models.CompteCGNCReference(numero=n, libelle=label, classe=int(n[0]), type_compte="SP")
                            for n, label in [("1111", "Capital social"), ("5141", "Banques"),
                                             ("3421", "Clients"), ("4411", "Fournisseurs")]])
                db.commit()
                assert db.query(models.Societe).count() == 0
            connexion_url = cluster['url']
            if preparer_runtime is not None:
                # Extension de recette uniquement : jamais d'URL externe ni
                # de rôle arbitraire. Le préparateur reçoit le seul bac créé.
                verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
                preparer_runtime(engine, cluster)
                connexion_url = make_url(cluster['url']).set(username='hisabpro').render_as_string(hide_password=False)
                runtime = create_engine(connexion_url)
                try:
                    with runtime.connect() as db:
                        role = db.execute(text('SELECT current_user,session_user,rolcanlogin,rolsuper,rolcreatedb,'
                            'rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user')).one()
                        assert tuple(role) == ('hisabpro','hisabpro',True,False,False,False,False,False)
                        assert not db.scalar(text("SELECT pg_has_role(current_user,'hisabpro_recette','MEMBER')"))
                        assert not db.scalar(text('SELECT count(*) FROM pg_class WHERE relowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
                        assert not db.scalar(text('SELECT count(*) FROM pg_proc WHERE proowner=(SELECT oid FROM pg_roles WHERE rolname=current_user)'))
                finally:
                    runtime.dispose()
            api_port, web_port = port_loopback_libre(), port_loopback_libre()
            while web_port == api_port:
                web_port = port_loopback_libre()
            api_url, web_url = f"http://127.0.0.1:{api_port}", f"http://127.0.0.1:{web_port}"
            env = os.environ.copy()
            env.update(DATABASE_URL=connexion_url, APP_ENV="test", HISABPRO_CREATE_TABLES="false",
                       SECRET_KEY="secret-prive-synthetique-e2e-" + cluster["nonce"], ALGORITHM="HS256",
                       CORS_ORIGINS=web_url, PYTHON_DOTENV_DISABLED="1", PYTHONUTF8="1",
                       VITE_API_URL=api_url, BROWSER="none", HISABPRO_UPLOAD_DIR=str(temp / "uploads"))
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
            api_log = temp / "api.log"
            api_out = api_log.open("w", encoding="utf-8")
            journaux.append(api_out)
            # La seule différence autorisée pour l'API est le nom du rôle.
            assert make_url(env['DATABASE_URL']).set(username='hisabpro_recette') == make_url(cluster['url'])
            verifier_cible_isolee(cluster['url'], cluster["directory"], cluster["nonce"])
            api_process = subprocess.Popen([sys.executable, "-X", "utf8", "-m", "uvicorn", "main:app",
                                            "--host", "127.0.0.1", "--port", str(api_port), "--log-level", "warning"],
                                           cwd=BACK, env=env, stdout=api_out, stderr=subprocess.STDOUT, **options)
            processus.append(api_process)
            attendre_http(api_url + "/api/health", api_process, api_log)
            web_dir = temp / "web"
            web_dir.mkdir()
            # Le serveur de recette doit servir les mêmes assets statiques que
            # Vite : les polices locales ne passent pas par le bundle esbuild.
            shutil.copytree(ROOT / "public", web_dir, dirs_exist_ok=True)
            script = temp / "build_ui.cjs"
            script.write_text("""
const esbuild=require(require.resolve('esbuild',{paths:[process.cwd()]}));
esbuild.buildSync({entryPoints:['src/main.jsx'],bundle:true,format:'esm',jsx:'automatic',
 outfile:process.argv[2],loader:{'.png':'file','.jpg':'file','.svg':'file','.woff':'file','.woff2':'file'},
 define:{'import.meta.env':JSON.stringify({VITE_API_URL:process.argv[3],DEV:false,PROD:true,MODE:'test'}),
         'process.env.NODE_ENV':JSON.stringify('production')}});
""", encoding="utf-8")
            web_log = temp / "web.log"
            web_out = web_log.open("w", encoding="utf-8")
            journaux.append(web_out)
            build = subprocess.run([node, str(script), str(web_dir / "app.js"), api_url], cwd=ROOT,
                                   env=env, stdout=web_out, stderr=subprocess.STDOUT, timeout=45,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            if build.returncode:
                web_out.flush()
                raise RuntimeError("Compilation UI complète échouée : " + web_log.read_text(encoding="utf-8", errors="replace")[-4000:])
            index = (ROOT / "index.html").read_text(encoding="utf-8")
            index = index.replace('src="/src/main.jsx"', 'src="/app.js"')
            index = index.replace("</head>", '<link rel="stylesheet" href="/app.css" /></head>')
            (web_dir / "index.html").write_text(index, encoding="utf-8")

            class SPAHandler(SimpleHTTPRequestHandler):
                def do_GET(self):
                    if not Path(self.translate_path(self.path)).exists() and "." not in self.path.rsplit("/", 1)[-1]:
                        self.path = "/index.html"
                    super().do_GET()

                def log_message(self, format, *args):
                    web_out.write((format % args) + "\n")
                    web_out.flush()

            web_server = ThreadingHTTPServer(("127.0.0.1", web_port), partial(SPAHandler, directory=str(web_dir)))
            web_server.daemon_threads = True
            web_thread = threading.Thread(target=web_server.serve_forever, daemon=True)
            web_thread.start()
            yield {"api_url": api_url, "web_url": web_url, "engine": engine, "cluster": cluster,
                   "role_sql": make_url(connexion_url).username,
                   "directory": temp, "uploads_dir": temp / "uploads", "api_log": api_log, "web_log": web_log,
                   "processus": tuple(processus), "web_thread": web_thread,
                   # Un test de reprise peut confier son nouveau Popen au contexte.
                   # Il reste actif pendant les contrôles de fin du rôle SQL,
                   # puis est arrêté avec tous les autres processus créés ici.
                   "enregistrer_processus": processus.append}
        finally:
            erreurs_arret = []
            try:
                if web_server is not None:
                    web_server.shutdown()
                    web_server.server_close()
                    web_thread.join(timeout=5)
                for process in reversed(processus):
                    try:
                        arreter_processus_cree(process)
                    except Exception as exc:
                        erreurs_arret.append(exc)
            finally:
                for journal in journaux:
                    journal.close()
                engine.dispose()
            if erreurs_arret:
                raise RuntimeError("Échec d'arrêt d'un serveur créé par la recette E2E.") from erreurs_arret[0]
