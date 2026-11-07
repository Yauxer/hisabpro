"""Journal actif append-only : début, point de reprise, livraison et état.

Source unique : CODEX_PROGRESS.md. Chaque événement comporte une entrée lisible
et un marqueur JSON pour retrouver automatiquement les étapes incomplètes.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / 'CODEX_PROGRESS.md'
MARKER = re.compile(r'^<!-- CODEX_STEP (.*) -->$', re.MULTILINE)


def etapes(path=JOURNAL):
    texte = Path(path).read_text(encoding='utf-8') if Path(path).exists() else ''
    result = {}
    for raw in MARKER.findall(texte):
        event = json.loads(raw)
        result.pop(event['id'], None)
        result[event['id']] = event
    return result


def consigner(action, identifiant, *, objectif=None, fichiers=None, prochaine=None,
              fait=None, tests=None, limites=None, zip_path=None, path=JOURNAL):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', identifiant):
        raise ValueError('Identifiant court stable requis : lettres, chiffres, tirets.')
    records = etapes(path)
    precedent = records.get(identifiant)
    if action == 'debut':
        if precedent:
            raise ValueError('Étape déjà enregistrée : utiliser point pour la reprendre.')
        if not objectif or not prochaine:
            raise ValueError('Objectif et prochaine action requis dès le début.')
        event = {'id': identifiant, 'objectif': objectif, 'fichiers': fichiers or [],
                 'fait': 'Analyse initiale ; modifications à effectuer.',
                 'tests': 'Non exécutés pour cette étape.', 'limites': 'À préciser.',
                 'zip': None}
    else:
        if not precedent:
            raise ValueError('Enregistrer le début avant les modifications.')
        if precedent['statut'] == 'termine':
            raise ValueError('Étape terminée ; créer une étape complémentaire.')
        event = precedent.copy()
    for key, value in [('objectif', objectif), ('fichiers', fichiers), ('prochaine', prochaine),
                       ('fait', fait), ('tests', tests), ('limites', limites)]:
        if value is not None:
            event[key] = value
    if action not in {'debut', 'point', 'interruption', 'fin'}:
        raise ValueError('Action inconnue.')
    if not event.get('prochaine'):
        raise ValueError('Prochaine action obligatoire, même après livraison.')
    if action == 'fin':
        archive = Path(zip_path or '')
        if not archive.is_file() or archive.suffix.lower() != '.zip':
            raise ValueError('ZIP différentiel existant requis avant de terminer.')
        try:
            with ZipFile(archive) as z:
                if not z.namelist() or z.testzip() is not None:
                    raise ValueError('ZIP vide ou corrompu.')
        except BadZipFile as exc:
            raise ValueError('ZIP invalide.') from exc
        event['zip'] = str(archive)
    event['statut'] = {'debut': 'en_cours', 'point': 'en_cours',
                       'interruption': 'interrompu', 'fin': 'termine'}[action]
    event['date_utc'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    # Une entrée complète est écrite et synchronisée avant de rendre la main.
    # Les sections historiques sont conservées et ne sont jamais remplacées.
    def display(value):
        return str(value).replace('\r', ' ').replace('\n', ' ')
    fields = [('Objectif', event['objectif']), ('Fichiers', ', '.join(event['fichiers']) or 'À identifier'),
              ('Accompli / point exact', event['fait']), ('Tests et preuves', event['tests']),
              ('PostgreSQL réel / navigateur / limites', event['limites']),
              ('ZIP', event['zip'] or 'Non livré'), ('Prochaine action', event['prochaine'])]
    body = f"\n## Journal actif — {identifiant} — {event['statut']} — {event['date_utc']}\n\n"
    body += '\n'.join(f'- {label} : {display(value)}' for label, value in fields) + '\n\n'
    body += '<!-- CODEX_STEP ' + json.dumps(event, ensure_ascii=False) + ' -->\n'
    with Path(path).open('a', encoding='utf-8', newline='\n') as out:
        out.write(body)
        out.flush()
        os.fsync(out.fileno())
    return event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['debut', 'point', 'interruption', 'fin', 'etat'])
    parser.add_argument('id', nargs='?')
    for key in ['objectif', 'prochaine', 'fait', 'tests', 'limites', 'zip']:
        parser.add_argument('--' + key)
    parser.add_argument('--fichiers', nargs='+')
    args = parser.parse_args()
    if args.action == 'etat':
        records = etapes()
        pending = [e for e in records.values() if e['statut'] != 'termine']
        print(json.dumps({'a_reprendre': pending, 'derniere_etape': next(reversed(records.values()), None)},
                         ensure_ascii=False, indent=2))
        return 0
    if not args.id:
        parser.error('Identifiant requis.')
    try:
        event = consigner(args.action, args.id, objectif=args.objectif, prochaine=args.prochaine,
                          fait=args.fait, tests=args.tests, limites=args.limites,
                          fichiers=args.fichiers, zip_path=args.zip)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"{event['id']} : {event['statut']} ; point de reprise sauvegardé.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
