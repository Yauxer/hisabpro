"""Réunit les versions effectivement livrées, sans embarquer un lot en cours."""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import json

from journal_codex import consigner

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'docs/audit/LIVRAISONS_SESSION_20261006_2012.json'


def construire(nom, etape, minimum=160):
    target = (ROOT / nom).resolve()
    if target.parent != ROOT or target.suffix != '.zip' or target.exists():
        raise ValueError('Archive neuve à la racine requise')
    entries = json.loads(MANIFEST.read_text(encoding='utf-8'))
    contenus, sources = {}, []
    for entry in entries:
        archive = entry['zip']
        if not archive.startswith('HisabPro_Patch'):
            continue
        numero = int(archive.split('Patch', 1)[1].split('_', 1)[0])
        if numero < minimum:
            continue
        with ZipFile(ROOT / archive) as z:
            if z.testzip() is not None:
                raise ValueError('CRC invalide : ' + archive)
            for rel in z.namelist():
                path = PurePosixPath(rel)
                if path.is_absolute() or '..' in path.parts or '\\' in rel:
                    raise ValueError('Chemin non sûr : ' + rel)
                if any(p in {'.venv', 'node_modules', '__pycache__', '.codex-tests', 'dist', '.env'} for p in path.parts):
                    raise ValueError('Fichier exclu : ' + rel)
                contenus[rel] = z.read(rel)
        sources.append(archive)
    if not sources:
        raise ValueError('Aucune livraison sélectionnée')
    contenus['Test/livrer_cumulatif.py'] = Path(__file__).read_bytes()
    rapport = 'Union des versions livrées : ' + ', '.join(sources)
    tests = f'{len(sources)} différentiels sources CRC vérifiés ; chemins contrôlés ; cumulatif relu intégralement'
    consigner('point', etape, fait=rapport, tests=tests,
        limites='Les changements encore en cours ne sont pas inclus. Aucune base ou secret livré.',
        prochaine='Vérifier le cumulatif puis enregistrer sa livraison')
    entries.append({'zip': nom, 'description': rapport, 'tests': tests,
        'fichiers': sorted(contenus), 'sources': sources})
    MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')
    def ecrire():
        contenus['CODEX_PROGRESS.md'] = (ROOT / 'CODEX_PROGRESS.md').read_bytes()
        contenus[MANIFEST.relative_to(ROOT).as_posix()] = MANIFEST.read_bytes()
        with ZipFile(target, 'w', ZIP_DEFLATED) as z:
            for rel, data in sorted(contenus.items()):
                z.writestr(rel, data)
        with ZipFile(target) as z:
            assert set(z.namelist()) == set(contenus) and z.testzip() is None
            assert all(z.read(rel) == data for rel, data in contenus.items())
    ecrire()
    consigner('fin', etape, fait=rapport, tests=tests, zip_path=target,
        prochaine='Poursuivre les lots indépendants puis fournir un nouveau cumulatif final')
    ecrire()
    print(f'{nom} : {len(contenus)} fichiers, {len(sources)} ZIP sources')
    print('\n'.join(sorted(contenus)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nom', required=True)
    parser.add_argument('--etape', required=True)
    parser.add_argument('--minimum', type=int, default=160)
    args = parser.parse_args()
    construire(args.nom, args.etape, args.minimum)
