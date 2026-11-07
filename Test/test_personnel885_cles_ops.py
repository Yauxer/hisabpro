"""Utilitaire d'exploitation testé exclusivement dans le répertoire temporaire."""
import importlib.util,json,tempfile,os
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('cles_ops885',Path(__file__).resolve().parents[1]/'ops/personnel_coffre_cles.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)

def test_885_initialisation_rotation_atomique_sauvegardes_et_anciennes_cles():
    with tempfile.TemporaryDirectory(prefix='hisabpro_ops885_') as td:
        d=Path(td);(d/'actif').mkdir();(d/'sauvegarde').mkdir();p=d/'actif/cles.json';b=d/'sauvegarde/initial.json'
        ops.gerer('initialiser',p,'k1',b);initial=json.loads(p.read_bytes());assert p.read_bytes()==b.read_bytes()
        ops.gerer('rotation',p,'k2',d/'sauvegarde/rotation.json');conf=json.loads(p.read_bytes())
        assert conf['active']=='k2' and conf['cles']['k1']==initial['cles']['k1'] and p.read_bytes()==(d/'sauvegarde/rotation.json').read_bytes()
        assert not list((d/'actif').glob('*.lock'))
        for op,k in [('initialiser','k3'),('rotation','k2')]:
            avant=p.read_bytes()
            with pytest.raises(ValueError):ops.gerer(op,p,k,d/'sauvegarde/refuse.json')
            assert p.read_bytes()==avant

def test_885_sauvegarde_existante_interdit_activation():
    with tempfile.TemporaryDirectory(prefix='hisabpro_ops885_') as td:
        d=Path(td);(d/'actif').mkdir();(d/'sauvegarde').mkdir();p=d/'actif/cles.json';b=d/'sauvegarde/existante.json';b.write_bytes(b'FICTIF')
        with pytest.raises(FileExistsError):ops.gerer('initialiser',p,'k1',b)
        assert not p.exists() and b.read_bytes()==b'FICTIF'
