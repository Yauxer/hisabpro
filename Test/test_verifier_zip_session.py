import hashlib
import json
from zipfile import ZipFile
import pytest
from verifier_zip_session import MANIFESTE, verifier, main


def creer(tmp_path,donnees=None,contenu=None,nom='renomme.zip',plus=None):
    donnees=donnees or {'src/exemple.txt':b'contenu fictif'}
    fichiers={n:{'taille':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in donnees.items()}
    manifeste={'version':1,'variantes':[{'nom':'livraison attendue.zip','fichiers':fichiers}]}
    path=tmp_path/nom
    with ZipFile(path,'w') as z:
        for n,b in (contenu if contenu is not None else donnees).items():z.writestr(n,b)
        if plus:
            for n,b in plus.items():z.writestr(n,b)
        z.writestr(MANIFESTE,json.dumps(manifeste).encode())
    return path


def test_zip_renomme_valide_sans_extraction(tmp_path):
    p=creer(tmp_path)
    avant=set(tmp_path.iterdir())
    assert verifier(p)==dict(livraison='livraison attendue.zip',fichiers=2,crc='OK',sha256='OK')
    assert set(tmp_path.iterdir())==avant


def test_modification_detectee_meme_si_crc_valide(tmp_path):
    p=creer(tmp_path,contenu={'src/exemple.txt':b'contenu altere'})
    with ZipFile(p) as z:assert z.testzip() is None
    with pytest.raises(ValueError,match='empreinte'):verifier(p)


def test_crc_corrompu_refuse(tmp_path):
    p=creer(tmp_path)
    b=p.read_bytes();i=b.index(b'contenu fictif')
    p.write_bytes(b[:i]+b'X'+b[i+1:])
    with pytest.raises(ValueError,match='CRC'):verifier(p)


def test_cli_archive_invalide_erreur_lisible(tmp_path,monkeypatch,capsys):
    import sys
    p=tmp_path/'invalide.zip';p.write_bytes(b'pas une archive')
    monkeypatch.setattr(sys,'argv',['verifier_zip_session.py',str(p)])
    with pytest.raises(SystemExit) as erreur:main()
    assert erreur.value.code==1 and 'zip' in capsys.readouterr().err.lower()


def test_fichier_manquant_ou_ajoute_refuse(tmp_path):
    for p in (creer(tmp_path,contenu={},nom='manquant.zip'),creer(tmp_path,plus={'ajout.txt':b'x'},nom='ajout.zip')):
        with pytest.raises(ValueError,match='Liste'):verifier(p)


@pytest.mark.parametrize('nom',['../secret','a\\b','C:/x','.env','src/__pycache__/x.pyc','node_modules/x','/abs'])
def test_chemins_non_autorises_refuses(tmp_path,nom):
    p=creer(tmp_path,donnees={nom:b'x'})
    if '\\' in nom:
        # ZipInfo normalise os.sep sous Windows. Injecter le nom réellement
        # invalide dans les deux en-têtes, sans changer les tailles/données.
        b=p.read_bytes();p.write_bytes(b.replace(nom.replace('\\','/').encode(),nom.encode()))
    with pytest.raises(ValueError,match='Chemin'):verifier(p)


def test_doublon_refuse(tmp_path):
    p=creer(tmp_path)
    with pytest.warns(UserWarning,match='Duplicate'):
        with ZipFile(p,'a') as z:z.writestr('src/exemple.txt',b'doublon')
    with pytest.raises(ValueError,match='dupliquée'):verifier(p)


def test_manifeste_absent_ou_malforme_refuse(tmp_path):
    for i,data in enumerate((None,b'{',b'{"version":2,"variantes":[]}')):
        p=tmp_path/f'invalide{i}.zip'
        with ZipFile(p,'w') as z:
            z.writestr('src/a.txt',b'a')
            if data is not None:z.writestr(MANIFESTE,data)
        with pytest.raises(ValueError,match='[Mm]anifeste'):verifier(p)
