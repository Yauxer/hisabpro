"""Registre et application contrôlée des migrations SQL HisabPro (128).

La connexion est lue dans une variable d'environnement, jamais en argument.
`--base-attendue` doit égaler current_database() : aucune cible implicite.

  etat       : fichiers enregistrés, en attente, empreinte modifiée.
  constater  : déclare des migrations déjà présentes sur une base existante,
               sans les exécuter (liste explicite ou --jusqua).
  appliquer  : exécute puis enregistre ; --suivantes (après la dernière
               enregistrée), --fichier explicite, ou --jusqua sur base vierge.

Les réparations historiques (065, 067, 070) ne sont jamais incluses
implicitement : elles exigent --fichier nominatif.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BACK = Path(__file__).resolve().parents[1] / 'hisabpro-backend'
MOTIF = re.compile(r'^(\d{3})[a-z]?_.+\.sql$')
REPARATIONS = {'065', '067', '070'}
REGISTRE = '128_registre_migrations.sql'


def fichiers(dossier=BACK):
    out = sorted((p for p in dossier.iterdir() if MOTIF.match(p.name)), key=lambda p: (int(p.name[:3]), p.name))
    return out


def numero(nom):
    return MOTIF.match(nom).group(1)


def empreinte(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def executer_script(engine, p):
    raw = engine.raw_connection()
    try:
        raw.autocommit = True
        with raw.cursor() as cur:
            cur.execute(p.read_text(encoding='utf-8'))
    finally:
        raw.close()


def registre(engine):
    with engine.connect() as db:
        if not db.scalar(text("SELECT to_regclass('public.hisabpro_migrations') IS NOT NULL")):
            return None
        return {f: (s, m) for f, s, m in db.execute(text('SELECT fichier, sha256, mode FROM public.hisabpro_migrations'))}


def enregistrer(engine, p, mode, note=None):
    with engine.begin() as db:
        db.execute(text("""INSERT INTO public.hisabpro_migrations(fichier, sha256, mode, note)
                           VALUES (:f, :s, :m, :n)"""), {'f': p.name, 's': empreinte(p), 'm': mode, 'n': note})


def assurer_registre(engine, dossier):
    if registre(engine) is None:
        executer_script(engine, dossier / REGISTRE)
    reg = registre(engine)
    if REGISTRE not in reg:
        enregistrer(engine, dossier / REGISTRE, 'executee')
    return registre(engine)


def base_vierge(engine):
    with engine.connect() as db:
        return not db.scalar(text("SELECT to_regclass('public.factures') IS NOT NULL OR to_regclass('public.ecritures') IS NOT NULL"))


def etat(engine, dossier):
    reg = registre(engine) or {}
    lignes = []
    for p in fichiers(dossier):
        if p.name in reg:
            statut = reg[p.name][1] if reg[p.name][0] == empreinte(p) else 'EMPREINTE_MODIFIEE'
        else:
            statut = 'en_attente' + (' (réparation : sur demande nominative)' if numero(p.name) in REPARATIONS else '')
        lignes.append((p.name, statut))
    return lignes


def selection(dossier, reg, args):
    tous = fichiers(dossier)
    par_nom = {p.name: p for p in tous}
    if args.fichier:
        inconnus = [f for f in args.fichier if f not in par_nom]
        if inconnus:
            raise SystemExit(f'Fichiers inconnus : {inconnus}')
        return [par_nom[f] for f in args.fichier]
    if args.jusqua is None:
        raise SystemExit('Préciser --fichier ou --jusqua.')
    return [p for p in tous if int(numero(p.name)) <= args.jusqua and numero(p.name) not in REPARATIONS
            and p.name != REGISTRE]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['etat', 'constater', 'appliquer'])
    parser.add_argument('--url-env', default='DATABASE_URL')
    parser.add_argument('--base-attendue', required=True)
    parser.add_argument('--fichier', nargs='+')
    parser.add_argument('--jusqua', type=int)
    parser.add_argument('--suivantes', action='store_true')
    parser.add_argument('--dossier', default=str(BACK), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    dossier = Path(args.dossier)
    url = os.environ.get(args.url_env)
    if not url or make_url(url).get_backend_name() != 'postgresql':
        raise SystemExit(f'Connexion PostgreSQL absente de {args.url_env}.')
    engine = create_engine(url)
    try:
        with engine.connect() as db:
            courante = db.scalar(text('SELECT current_database()'))
        if courante != args.base_attendue:
            raise SystemExit(f'Base connectée « {courante} » différente de --base-attendue.')
        if args.action == 'etat':
            for nom, statut in etat(engine, dossier):
                print(f'{nom}\t{statut}')
            return 0
        vierge = base_vierge(engine)
        reg = assurer_registre(engine, dossier)
        for nom, (sha, _) in reg.items():
            if (dossier / nom).exists() and empreinte(dossier / nom) != sha:
                raise SystemExit(f'Empreinte modifiée pour {nom} : arrêt sans exécution.')
        if args.action == 'constater':
            for p in selection(dossier, reg, args):
                if p.name not in reg:
                    enregistrer(engine, p, 'constatee', 'Déclarée présente par l’administrateur')
                    print(f'constatée\t{p.name}')
            return 0
        if args.suivantes:
            numeros = [int(numero(n)) for n in reg if n != REGISTRE and MOTIF.match(n)]
            if not numeros:
                raise SystemExit('Registre vide : constater d’abord l’existant ou utiliser --jusqua sur base vierge.')
            cibles = [p for p in fichiers(dossier) if int(numero(p.name)) > max(numeros)
                      and numero(p.name) not in REPARATIONS and p.name != REGISTRE]
        else:
            cibles = selection(dossier, reg, args)
            if args.jusqua is not None and not args.fichier and not vierge:
                raise SystemExit('Base existante : --jusqua est réservé à une base vierge. '
                                 'Constater l’existant puis utiliser --suivantes ou --fichier.')
        for p in cibles:
            if p.name in reg:
                continue
            executer_script(engine, p)
            enregistrer(engine, p, 'executee')
            print(f'exécutée\t{p.name}')
        return 0
    finally:
        engine.dispose()


if __name__ == '__main__':
    sys.exit(main())
