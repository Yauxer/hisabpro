"""Gestion manuelle des clés RH ;ne se connecte à aucune base.

Le secret n'est jamais écrit sur stdout. Initialisation/rotation exigent une
sauvegarde séparée fournie par l'opérateur ;les clés anciennes sont conservées.
"""
import argparse,json,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hisabpro-backend'))
from cryptography.fernet import Fernet
from services.personnel_coffre_crypto import RACINE,IDENTIFIANT,Trousseau,charger

def chemin_externe(valeur):
    p=Path(valeur)
    if not p.is_absolute() or p.is_symlink():raise ValueError('Chemin privé absolu externe requis.')
    p=p.resolve()
    if p==RACINE or RACINE in p.parents or not p.parent.is_dir():raise ValueError('Préparer un répertoire privé hors du dépôt.')
    return p

def ecrire_neuf(p,brut):
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:f.write(brut);f.flush();os.fsync(f.fileno())

def gerer(operation,fichier,identifiant,sauvegarde):
    p=chemin_externe(fichier);b=chemin_externe(sauvegarde)
    if p==b or p.parent==b.parent:raise ValueError('Prévoir la sauvegarde dans un autre répertoire privé.')
    if not isinstance(identifiant,str) or not IDENTIFIANT.fullmatch(identifiant):raise ValueError('Identifiant de clé invalide.')
    verrou=p.with_name(p.name+'.lock')
    fd=os.open(verrou,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);os.close(fd)
    provisoire=None
    try:
        if operation=='initialiser':
            if p.exists():raise ValueError('Le trousseau existe déjà ;aucun écrasement.')
            conf={'version':1,'active':identifiant,'cles':{}}
        elif operation=='rotation':
            ancien=os.environ.get('PERSONNEL_COFFRE_CLES_FICHIER')
            try:
                os.environ['PERSONNEL_COFFRE_CLES_FICHIER']=str(p);charger()
            finally:
                if ancien is None:os.environ.pop('PERSONNEL_COFFRE_CLES_FICHIER',None)
                else:os.environ['PERSONNEL_COFFRE_CLES_FICHIER']=ancien
            conf=json.loads(p.read_text(encoding='utf8'))
            if identifiant in conf['cles']:raise ValueError('Identifiant déjà présent ;aucune clé remplacée.')
        else:raise ValueError('Opération inconnue.')
        conf['cles'][identifiant]=Fernet.generate_key().decode('ascii');conf['active']=identifiant
        Trousseau(conf['cles'],conf['active'])
        brut=json.dumps(conf,separators=(',',':')).encode('utf8')
        # Sauvegarde avant activation ;jamais d'écrasement silencieux.
        ecrire_neuf(b,brut)
        if operation=='initialiser':ecrire_neuf(p,brut)
        else:
            fd,nom=tempfile.mkstemp(prefix='.coffre-',dir=p.parent);provisoire=Path(nom)
            with os.fdopen(fd,'wb') as f:f.write(brut);f.flush();os.fsync(f.fileno())
            os.replace(provisoire,p);provisoire=None
        return {'operation':operation,'cle_active':identifiant,'anciennes_cles_conservees':True,'sauvegarde_creee':True}
    finally:
        if provisoire is not None and provisoire.exists():provisoire.unlink()
        verrou.unlink()

def main():
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('operation',choices=['initialiser','rotation'])
    a.add_argument('--fichier',required=True);a.add_argument('--identifiant',required=True);a.add_argument('--sauvegarde',required=True)
    n=a.parse_args()
    try:r=gerer(n.operation,n.fichier,n.identifiant,n.sauvegarde)
    except Exception:raise SystemExit('Opération refusée ;vérifier chemins privés,droits,identifiant et sauvegarde. Aucun secret affiché.') from None
    print(json.dumps(r,ensure_ascii=False));print('Vérifier les ACL du fichier et de sa sauvegarde ;le nom de clé n’est pas un secret.')

if __name__=='__main__':main()
