"""Coffre authentifié ;clés hors dépôt et données métier,aucune création implicite.

Référence :https://cryptography.io/en/latest/fernet/ ;API testée50.0.1.
La portée est authentifiée dans l'enveloppe chiffrée,avant toute restitution.
"""
import json,os,re,stat
from pathlib import Path
from cryptography.fernet import Fernet,InvalidToken

RACINE=Path(__file__).resolve().parents[2]
IDENTIFIANT=re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')
MAX_CLAIR=6*1024*1024

class ConfigurationCoffreError(Exception):
    def __init__(self):super().__init__('Configuration des clés du coffre RH indisponible ou invalide.')

class IntegriteCoffreError(Exception):
    def __init__(self):super().__init__('Contenu du coffre RH invalide ou rattaché à un autre dossier.')

def _objet_unique(paires):
    d={}
    for k,v in paires:
        if k in d:raise ValueError('Clé JSON dupliquée')
        d[k]=v
    return d

class Trousseau:
    def __init__(self,cles,active):
        try:
            if not isinstance(cles,dict) or not 1<=len(cles)<=16 or not isinstance(active,str) or active not in cles:raise ValueError()
            if any(not isinstance(k,str) or not IDENTIFIANT.fullmatch(k) or not isinstance(v,str) for k,v in cles.items()):raise ValueError()
            self._cles={k:Fernet(v.encode('ascii')) for k,v in cles.items()};self.active=active
        except (ValueError,TypeError,UnicodeError):raise ConfigurationCoffreError() from None

    def chiffrer(self,usage,portee,donnees):
        if not isinstance(usage,str) or not usage or not isinstance(portee,dict) or not portee or any(type(v)is not int or v<=0 for v in portee.values()):raise IntegriteCoffreError()
        brut=json.dumps({'version':1,'usage':usage,'portee':portee,'donnees':donnees},ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf8')
        if len(brut)>MAX_CLAIR:raise IntegriteCoffreError()
        return self.active,self._cles[self.active].encrypt(brut).decode('ascii')

    def dechiffrer(self,cle_id,jeton,usage,portee):
        if cle_id not in self._cles:raise ConfigurationCoffreError()
        try:
            if not isinstance(jeton,str) or len(jeton)>MAX_CLAIR*2:raise ValueError()
            contenu=json.loads(self._cles[cle_id].decrypt(jeton.encode('ascii')),object_pairs_hook=_objet_unique)
            if set(contenu)!={'version','usage','portee','donnees'} or contenu['version']!=1 or contenu['usage']!=usage or contenu['portee']!=portee:raise ValueError()
            return contenu['donnees']
        except (InvalidToken,ValueError,TypeError,UnicodeError,KeyError):raise IntegriteCoffreError() from None

def charger():
    """Chemin privé fourni au déploiement ;pas de .env lu ici,pas de cache secret."""
    try:
        valeur=os.environ.get('PERSONNEL_COFFRE_CLES_FICHIER','')
        p=Path(valeur)
        if not valeur or not p.is_absolute() or p.is_symlink():raise ValueError()
        p=p.resolve(strict=True)
        if p==RACINE or RACINE in p.parents or not p.is_file():raise ValueError()
        if os.name!='nt' and stat.S_IMODE(p.stat().st_mode)&0o077:raise ValueError()
        with p.open('rb') as f:brut=f.read(16385)
        if len(brut)>16384:raise ValueError()
        conf=json.loads(brut,object_pairs_hook=_objet_unique)
        if not isinstance(conf,dict) or set(conf)!={'version','active','cles'} or conf['version']!=1:raise ValueError()
        return Trousseau(conf['cles'],conf['active'])
    except (OSError,ValueError,TypeError,UnicodeError):raise ConfigurationCoffreError() from None
