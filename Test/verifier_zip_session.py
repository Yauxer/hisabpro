"""Vérifier une livraison par manifeste embarqué, sans extraire ni accéder à la DB."""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile

MANIFESTE='Test/MANIFEST_SESSION_20261018_591_609.json'


def chemin_valide(nom):
    p=PurePosixPath(nom)
    return bool(nom and not nom.endswith('/') and not p.is_absolute()
        and '\\' not in nom and ':' not in nom and p.as_posix()==nom
        and all(s not in {'.','..','.venv','node_modules','__pycache__','.git'} for s in p.parts)
        and p.name!='.env' and p.suffix!='.pyc')


def verifier(archive):
    with ZipFile(archive) as z:
        infos=z.infolist()
        noms=[i.filename for i in infos]
        if len(noms)!=len(set(noms)):raise ValueError('Entrée ZIP dupliquée.')
        if not all(chemin_valide(i.orig_filename) and chemin_valide(i.filename) for i in infos):
            raise ValueError('Chemin ZIP non autorisé.')
        if z.testzip() is not None:raise ValueError('CRC ZIP invalide.')
        if MANIFESTE not in noms:raise ValueError('Manifeste de session absent.')
        try:m=json.loads(z.read(MANIFESTE))
        except (ValueError,UnicodeError) as exc:raise ValueError('Manifeste JSON invalide.') from exc
        if not isinstance(m,dict) or m.get('version')!=1 or not isinstance(m.get('variantes'),list):
            raise ValueError('Format de manifeste invalide.')
        variantes=[v for v in m['variantes'] if isinstance(v,dict) and isinstance(v.get('fichiers'),dict)
            and set(v['fichiers'])|{MANIFESTE}==set(noms)]
        if len(variantes)!=1:raise ValueError('Liste des fichiers différente du manifeste.')
        variante=variantes[0]
        for nom,attendu in variante['fichiers'].items():
            contenu=z.read(nom)
            if not isinstance(attendu,dict) or attendu.get('taille')!=len(contenu) or attendu.get('sha256')!=hashlib.sha256(contenu).hexdigest():
                raise ValueError('Taille ou empreinte différente : '+nom)
        return {'livraison':variante.get('nom',''),'fichiers':len(noms),'crc':'OK','sha256':'OK'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',help='ZIP différentiel ou cumulatif avec manifeste de session, même renommé.')
    args=parser.parse_args()
    try:resultat=verifier(args.archive)
    except (OSError,ValueError,BadZipFile) as exc:parser.exit(1,str(exc)+'\n')
    print(json.dumps(resultat,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
