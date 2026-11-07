"""Chiffrement authentifié :aléa,portée,corruption et clés hors dépôt."""
from pathlib import Path
import json,os,tempfile
import pytest
from cryptography.fernet import Fernet
from services.personnel_coffre_crypto import Trousseau,charger,ConfigurationCoffreError,IntegriteCoffreError

PORTEE={'societe_id':1,'employe_id':2,'piece_id':3}

def cle():return Fernet.generate_key().decode('ascii')

def test_885_chiffrement_aleatoire_et_restitution_exacte():
    t=Trousseau({'a':cle()},'a');a,j=t.chiffrer('piece-rh',PORTEE,{'contenu':'SECRET-FICTIF885'})
    _,autre=t.chiffrer('piece-rh',PORTEE,{'contenu':'SECRET-FICTIF885'})
    assert j!=autre and 'SECRET-FICTIF885' not in j and t.dechiffrer(a,j,'piece-rh',PORTEE)=={'contenu':'SECRET-FICTIF885'}

@pytest.mark.parametrize('usage,portee',[('banque-rh',PORTEE),('piece-rh',dict(PORTEE,societe_id=2)),('piece-rh',dict(PORTEE,employe_id=3)),('piece-rh',dict(PORTEE,piece_id=4))])
def test_885_substitution_de_portee_refusee(usage,portee):
    t=Trousseau({'a':cle()},'a');i,j=t.chiffrer('piece-rh',PORTEE,{})
    with pytest.raises(IntegriteCoffreError):t.dechiffrer(i,j,usage,portee)

def test_885_corruption_et_perte_de_cle_sans_fuite():
    t=Trousseau({'a':cle()},'a');i,j=t.chiffrer('piece-rh',PORTEE,{'contenu':'SECRET-FICTIF885'})
    with pytest.raises(IntegriteCoffreError) as e:t.dechiffrer(i,j[:30]+'!'+j[31:],'piece-rh',PORTEE)
    assert 'SECRET' not in str(e.value)
    with pytest.raises(ConfigurationCoffreError):Trousseau({'b':cle()},'b').dechiffrer(i,j,'piece-rh',PORTEE)

def test_885_rotation_nouvelles_ecritures_et_restauration_anciennes():
    a,b=cle(),cle();ancien=Trousseau({'a':a},'a');i,j=ancien.chiffrer('piece-rh',PORTEE,{'contenu':'ANCIEN-FICTIF885'})
    neuf=Trousseau({'a':a,'b':b},'b');ii,jj=neuf.chiffrer('piece-rh',PORTEE,{'contenu':'NEUF-FICTIF885'})
    assert ii=='b' and neuf.dechiffrer(i,j,'piece-rh',PORTEE)['contenu']=='ANCIEN-FICTIF885'
    restaure=Trousseau(json.loads(json.dumps({'a':a,'b':b})),'b')
    assert restaure.dechiffrer(i,j,'piece-rh',PORTEE)['contenu']=='ANCIEN-FICTIF885' and restaure.dechiffrer(ii,jj,'piece-rh',PORTEE)['contenu']=='NEUF-FICTIF885'

@pytest.mark.parametrize('configuration',[{}, {'version':1,'active':'absente','cles':{'a':'FAUSSE-CLE-FICTIVE885'}}, {'version':1,'active':'a','cles':{'a':'FAUSSE-CLE-FICTIVE885'}}])
def test_885_configuration_invalide_refusee(monkeypatch,configuration):
    with tempfile.TemporaryDirectory(prefix='hisabpro_cles885_') as td:
        p=Path(td)/'cles.json';p.write_text(json.dumps(configuration),encoding='utf8');p.chmod(0o600)
        monkeypatch.setenv('PERSONNEL_COFFRE_CLES_FICHIER',str(p))
        with pytest.raises(ConfigurationCoffreError) as e:charger()
        assert str(p) not in str(e.value) and 'FAUSSE-CLE-FICTIVE885' not in str(e.value)

def test_885_chemin_interne_et_absence_configuration_refuses(monkeypatch,tmp_path):
    p=tmp_path/'cles.json';p.write_text(json.dumps({'version':1,'active':'a','cles':{'a':cle()}}),encoding='utf8')
    monkeypatch.setenv('PERSONNEL_COFFRE_CLES_FICHIER',str(p))
    with pytest.raises(ConfigurationCoffreError):charger()
    monkeypatch.delenv('PERSONNEL_COFFRE_CLES_FICHIER')
    with pytest.raises(ConfigurationCoffreError):charger()

def test_885_fichier_externe_valide_et_doublon_json_refuse(monkeypatch):
    with tempfile.TemporaryDirectory(prefix='hisabpro_cles885_') as td:
        p=Path(td)/'cles.json';p.write_text(json.dumps({'version':1,'active':'a','cles':{'a':cle()}}),encoding='utf8');p.chmod(0o600)
        monkeypatch.setenv('PERSONNEL_COFFRE_CLES_FICHIER',str(p));assert charger().active=='a'
        p.write_text('{"version":1,"active":"a","active":"b","cles":{}}',encoding='utf8')
        with pytest.raises(ConfigurationCoffreError):charger()
