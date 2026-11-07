"""Le banc doit suivre les nouveaux fichiers et écarter secrets et données générées."""
import hashlib
from pathlib import Path
from test_consolidation_ras_documents651_isole import empreintes_application


def test_sources_sans_baseline_privee_secrets_caches_ni_uploads(tmp_path,monkeypatch):
    utiles={'src/Application.jsx':b'application','hisabpro-backend/services/metier.py':b'metier',
        'hisabpro-backend/103_exemple.sql':b'migration fictive','package.json':b'configuration'}
    exclus=['hisabpro-backend/.env','hisabpro-backend/.env.production',
        'hisabpro-backend/.venv/secret.py','hisabpro-backend/venv/secret.py',
        'hisabpro-backend/uploads/document.pdf','hisabpro-backend/__pycache__/cache.pyc',
        'hisabpro-backend/serveur.log','hisabpro-backend/archive.zip',
        'src/node_modules/dependance.js','src/dist/bundle.js',
        '.codex-tests/baseline645.json','.codex-tests/cumul649_preuve.json']
    for nom,contenu in {**utiles,**dict.fromkeys(exclus,b'NE PAS LIRE')}.items():
        p=tmp_path/nom;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(contenu)
    lire=Path.read_bytes
    def lire_source(path):
        assert path.relative_to(tmp_path).as_posix() not in exclus,'Lecture de secret ou fichier non livre'
        return lire(path)
    monkeypatch.setattr(Path,'read_bytes',lire_source)
    assert empreintes_application(tmp_path)=={f:hashlib.sha256(b).hexdigest() for f,b in utiles.items()}
    initial=empreintes_application(tmp_path)
    p=tmp_path/'src/Nouveau.jsx';p.write_bytes(b'nouveau')
    ajout=empreintes_application(tmp_path)
    assert ajout!=initial and set(ajout)-set(initial)=={'src/Nouveau.jsx'}
    p.write_bytes(b'modifie')
    assert empreintes_application(tmp_path)!=ajout
    p.unlink()
    assert empreintes_application(tmp_path)==initial
