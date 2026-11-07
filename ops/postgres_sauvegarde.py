"""Sauvegarde PostgreSQL en lecture seule et restauration limitée au bac de test.

Le mot de passe n'apparaît jamais dans les arguments ni les messages. Aucun
fichier existant n'est écrasé. Les restaurations hors cluster marqué sont refusées.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]


def connexion_pg(url):
    try:
        parsed = make_url(url)
        if parsed.get_backend_name() != 'postgresql' or not parsed.database:
            raise ValueError()
    except Exception as exc:
        raise ValueError('Une connexion PostgreSQL explicite est requise.') from exc
    # Une PGHOSTADDR/PGSERVICE héritée pourrait connecter libpq à une autre
    # cible malgré PGHOST explicite. Seule l'URL déclarée fait autorité.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')}
    env.update(PGHOST=parsed.host or 'localhost', PGPORT=str(parsed.port or 5432),
               PGUSER=parsed.username or '', PGDATABASE=parsed.database, PGCONNECT_TIMEOUT='10')
    if parsed.password is not None:
        env['PGPASSWORD'] = parsed.password
    else:
        env.pop('PGPASSWORD', None)
    for key in ('sslmode', 'sslrootcert', 'sslcert', 'sslkey'):
        if key in parsed.query:
            env['PG' + key.upper()] = str(parsed.query[key])
    return env


def executer_pg(args, url):
    result = subprocess.run([str(x) for x in args], env=connexion_pg(url),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                            timeout=600, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if result.returncode:
        # Les erreurs libpq peuvent inclure des chaînes de connexion : ne pas
        # diffuser stderr. Le code suffit à identifier un échec opérationnel.
        raise RuntimeError(f'{Path(str(args[0])).stem} a échoué (code {result.returncode}). Aucun secret affiché.')


def sauvegarder(url, destination, binaires, *, inclure_droits=False):
    connexion_pg(url)
    destination = Path(destination).resolve()
    if destination.exists():
        raise FileExistsError('La sauvegarde cible existe déjà ; choisir un nouveau nom.')
    if not destination.parent.is_dir():
        raise ValueError('Le dossier de sauvegarde doit exister.')
    suffix = '.exe' if os.name == 'nt' else ''
    with tempfile.TemporaryDirectory(prefix='.hisabpro_backup_', dir=destination.parent) as temporary:
        archive = Path(temporary) / 'database.dump'
        args = [Path(binaires) / ('pg_dump' + suffix), '--format=custom', '--no-owner']
        if not inclure_droits:
            args.append('--no-privileges')
        executer_pg([*args, '--no-password', '--file', archive], url)
        if not archive.is_file() or archive.stat().st_size == 0:
            raise RuntimeError('Archive de sauvegarde vide ou absente.')
        # Le lien dur échoue si la destination est apparue entre-temps, sans
        # l'écraser. Le fichier temporaire se trouve sur le même volume.
        os.link(archive, destination)
    return destination


def restaurer_isole(url, archive, binaires, directory, nonce, *, inclure_droits=False):
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from Test.postgres_isole import verifier_cible_isolee
    verifier_cible_isolee(url, directory, nonce)
    archive = Path(archive).resolve()
    if not archive.is_file():
        raise ValueError('Archive de sauvegarde introuvable.')
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            count = connection.scalar(text("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m','S')"))
            if count:
                raise ValueError('La base isolée de restauration doit être vide ; aucune suppression automatique.')
        suffix = '.exe' if os.name == 'nt' else ''
        args = [Path(binaires) / ('pg_restore' + suffix), '--exit-on-error', '--single-transaction', '--no-owner']
        if not inclure_droits:
            args.append('--no-privileges')
        executer_pg([*args, '--no-password', '--dbname', make_url(url).database, archive], url)
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--bin', required=True, dest='binaires')
    parser.add_argument('--url-env', default='DATABASE_URL', help='Nom de variable contenant la connexion ; jamais le mot de passe en argument.')
    parser.add_argument('--inclure-droits', action='store_true',
                        help='Conserver explicitement les GRANT/REVOKE. Les rôles ne sont pas sauvegardés et doivent être préparés séparément.')
    args = parser.parse_args()
    url = os.environ.get(args.url_env)
    if not url:
        parser.error('Variable de connexion absente.')
    try:
        path = sauvegarder(url, args.output, args.binaires, inclure_droits=args.inclure_droits)
        print(f'Sauvegarde créée : {path.name}')
    except (ValueError, FileExistsError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'Sauvegarde refusée ou échouée : {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
