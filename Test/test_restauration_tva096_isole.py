"""Restauration froide096 : oracles452 et registre095 renseigné conservés."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import json
from sqlalchemy import create_engine,text
import test_restauration_justificatifs_acl_isole as recette
from test_restauration_avances095_isole import test_restauration095_registre_historique_soldes_et_reprise as scenario095
from test_avances_salaries_isole import appliquer
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def test_restauration096_fonction_verrou_acl_registre_et_pieces(monkeypatch,tmp_path):
    application=recette.application_isolee;lancer=recette.lancer_cible
    fonction={}
    fichier=ROOT/'.codex-tests/restauration482_preuve.json'
    ancien=fichier.read_bytes() if fichier.exists() else None
    @contextmanager
    def source096(**kwargs):
        with application(**kwargs) as app:
            appliquer(app,'096_verrou_parametres_tva.sql')
            with app['engine'].connect() as db:
                fonction['source']=db.scalar(text("SELECT pg_get_functiondef('hisabpro_proteger_parametres_tva_clotures()'::regprocedure)"))
                assert 'FOR SHARE' in fonction['source']
            yield app
    def cible096(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        engine=create_engine(c['url'])
        try:
            with engine.connect() as db:
                assert db.scalar(text("SELECT pg_get_functiondef('hisabpro_proteger_parametres_tva_clotures()'::regprocedure)"))==fonction['source']
        finally:engine.dispose()
        return lancer(c,uploads)
    monkeypatch.setattr(recette,'application_isolee',source096)
    monkeypatch.setattr(recette,'lancer_cible',cible096)
    try:
        scenario095(monkeypatch,tmp_path)
        preuve=json.loads(fichier.read_text(encoding='utf8'))
        preuve.update(extension096=True,fonction096_octets_identiques=True,
            migration096_sha256=hashlib.sha256((recette.BACK/'096_verrou_parametres_tva.sql').read_bytes()).hexdigest())
        (ROOT/'.codex-tests/restauration485_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    finally:
        if ancien is not None:fichier.write_bytes(ancien)
