"""ZIPs différentiels explicites et vérifiés de la session de finalisation."""
from pathlib import Path
from datetime import datetime, timezone
from zipfile import ZipFile, ZIP_DEFLATED
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'Test/.session132_baseline.json'
MANIFEST = ROOT / 'docs/audit/LIVRAISONS_SESSION_20261006_2012.json'


def livrer(nom, fichiers, description, tests, etape=None, prochaine=None):
    target = (ROOT / nom).resolve()
    if target.parent != ROOT or target.suffix != '.zip' or target.exists():
        raise ValueError('Nom ZIP neuf requis, à la racine du workspace.')
    if etape:
        from journal_codex import etapes
        courant = etapes(ROOT / 'CODEX_PROGRESS.md').get(etape)
        if not courant or courant['statut'] == 'termine':
            raise ValueError('Étape active du journal requise avant livraison.')
        prochaine = prochaine or courant['prochaine']
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
    paths = set(fichiers)
    for rel in paths:
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file() or path.name == '.env':
            raise ValueError('Fichier hors livraison : ' + rel)
        if any(p in {'node_modules', 'dist', '__pycache__', '.venv', 'venv', '.codex-tests'} for p in path.parts):
            raise ValueError('Environnement ou cache exclu : ' + rel)
        if baseline.get(rel) == hashlib.sha256(path.read_bytes()).hexdigest():
            raise ValueError('Fichier inchangé exclu : ' + rel)
    with (ROOT / 'CODEX_PROGRESS.md').open('a', encoding='utf-8') as out:
        out.write(f'\n## {nom.removesuffix(".zip")} — terminé\n\n{description}\n\nTests : {tests}\n\nZIP différentiel : `{nom}` ; contenu listé et CRC vérifiés.\n')
    paths.add('CODEX_PROGRESS.md')
    entries = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else []
    entries.append({'zip': nom, 'date_utc': datetime.now(timezone.utc).isoformat(),
                    'description': description, 'tests': tests, 'fichiers': sorted(paths)})
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding='utf-8')
    paths.add(MANIFEST.relative_to(ROOT).as_posix())
    with ZipFile(target, 'w', ZIP_DEFLATED) as z:
        for rel in sorted(paths):
            z.write(ROOT / rel, rel)
    with ZipFile(target) as z:
        assert set(z.namelist()) == paths and z.testzip() is None
    if etape:
        from journal_codex import consigner
        consigner('fin', etape, fait=description, tests=tests, zip_path=target,
                  prochaine=prochaine, path=ROOT / 'CODEX_PROGRESS.md')
        # Le reçu final est dans l'archive : une reprise depuis le ZIP sait
        # donc que la livraison a été vérifiée, sans fichier à copier à part.
        with ZipFile(target, 'w', ZIP_DEFLATED) as z:
            for rel in sorted(paths):
                z.write(ROOT / rel, rel)
    with ZipFile(target) as z:
        assert set(z.namelist()) == paths and z.testzip() is None
        print(target.name, ':', len(paths), 'fichiers')
        print('\n'.join(z.namelist()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nom', required=True)
    parser.add_argument('--fichiers', nargs='+', required=True)
    parser.add_argument('--description', required=True)
    parser.add_argument('--tests', required=True)
    parser.add_argument('--etape', help='Identifiant actif à terminer après vérification du ZIP.')
    parser.add_argument('--prochaine', help='Prochaine action après livraison.')
    args = parser.parse_args()
    livrer(args.nom, args.fichiers, args.description, args.tests, args.etape, args.prochaine)
