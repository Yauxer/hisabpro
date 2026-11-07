"""PostgreSQL éphémère propre à la recette, exclusivement dans le workspace.

Aucun DATABASE_URL existant n'est utilisé. Le port est distinct de 5432,
le serveur écoute uniquement 127.0.0.1 et l'arrêt est garanti par le contexte.
"""
from contextlib import contextmanager
from pathlib import Path
import os
import shutil
import socket
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]


def binaires_postgres():
    configured = os.getenv('HISABPRO_POSTGRES_BIN')
    candidates = ([Path(configured)] if configured else [])
    executable = shutil.which('initdb')
    if executable:
        candidates.append(Path(executable).parent)
    if os.name == 'nt':
        base = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'PostgreSQL'
        if base.exists():
            candidates += sorted((p / 'bin' for p in base.iterdir() if p.is_dir()), reverse=True)
    suffix = '.exe' if os.name == 'nt' else ''
    for candidate in candidates:
        if all((candidate / (name + suffix)).is_file() for name in ('initdb', 'pg_ctl', 'createdb')):
            return candidate, suffix
    raise RuntimeError('Binaires PostgreSQL absents : définir HISABPRO_POSTGRES_BIN.')


def _run(args, timeout=60):
    # Sous Windows, postgres peut hériter des pipes de pg_ctl et maintenir
    # communicate() ouvert après le démarrage. Les commandes de contrôle ne
    # capturent donc aucun pipe ; leur journal serveur reste dans le bac isolé.
    control = Path(str(args[0])).stem == 'pg_ctl'
    output = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL} if control else {'capture_output': True}
    result = subprocess.run([str(x) for x in args], **output, text=True,
        encoding='utf-8', errors='replace', timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        raise RuntimeError(f'{Path(str(args[0])).name} : {(result.stdout or "")[-1500:]} {(result.stderr or "")[-1500:]}')
    return result


@contextmanager
def cluster_isole():
    binaries, suffix = binaires_postgres()
    espace = (ROOT / '.codex-tests').resolve()
    assert espace.is_relative_to(ROOT.resolve())
    espace.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='hisabpro_pg_', dir=espace) as directory:
        directory = Path(directory).resolve()
        # Vérification avant toute initialisation/arrêt et suppression récursive
        # du seul dossier temporaire créé par ce contexte.
        assert directory.is_relative_to(espace) and directory.name.startswith('hisabpro_pg_')
        data = directory / 'data'
        nonce = uuid.uuid4().hex
        (directory / 'recette.marker').write_text(nonce, encoding='ascii')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        assert port != 5432
        pgctl = binaries / ('pg_ctl' + suffix)
        _run([binaries / ('initdb' + suffix), '-D', data, '-U', 'hisabpro_recette',
              '--encoding=UTF8', '--locale=C', '--auth-local=trust', '--auth-host=trust'])
        started = False
        try:
            started = True
            _run([pgctl, '-D', data, '-l', directory / 'postgres.log', '-o',
                  f'-h 127.0.0.1 -p {port}', '-w', 'start'])
            name = 'hisabpro_recette_' + nonce[:12]
            _run([binaries / ('createdb' + suffix), '-h', '127.0.0.1', '-p', port,
                  '-U', 'hisabpro_recette', name])
            yield {'url': f'postgresql+psycopg2://hisabpro_recette@127.0.0.1:{port}/{name}',
                   'port': port, 'directory': directory, 'nonce': nonce,
                   'bin': binaries, 'suffix': suffix}
        finally:
            if started:
                _run([pgctl, '-D', data, '-m', 'fast', '-w', 'stop'])


def verifier_cible_isolee(url, directory, nonce):
    from sqlalchemy.engine import make_url
    parsed = make_url(url)
    directory = Path(directory).resolve()
    if (not directory.is_relative_to((ROOT / '.codex-tests').resolve())
            or not directory.name.startswith('hisabpro_pg_')
            or (directory / 'recette.marker').read_text(encoding='ascii') != nonce
            or parsed.host != '127.0.0.1' or parsed.port in (None, 5432)
            or parsed.username != 'hisabpro_recette'
            or not ((parsed.database or '') == 'hisabpro_recette_' + nonce[:12]
                    or (parsed.database or '').startswith('hisabpro_recette_' + nonce[:12] + '_'))):
        raise ValueError('Cible hors PostgreSQL isolé : opération refusée.')
    return True
