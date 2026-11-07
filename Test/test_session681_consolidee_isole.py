"""Qualification commune103 et témoins non vides, indépendante des baselines privées."""
from pathlib import Path
from io import BytesIO
import hashlib,importlib,json
import pytest
from pypdf import PdfReader
from sqlalchemy import text
import test_consolidation_ras_documents651_isole as precedent
from test_ras_rapprochements681_isole import (
    application as application103,application102,application101,application100,application099,
    application098,application097,application093,application092,application091,application090,
    application089,application087,migration,client,capture,versement,corps,chemin,ok)
from postgres_isole import verifier_cible_isolee
from test_e2e_facturation_isole import application as application_absente
from test_balance_preparations import api
from test_balance_preparations_postgres import moteur
from test_session132_balance_navigateur import bundle,page_recette
from test_e2e_balance_exports677_isole import test_677_import_versions_rechargement_et_exports_figes_edge
from test_e2e_balance_detail679_isole import test_679_bilan_sources_filtre_et_comparatif_natifs

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def application(application103):
    app=application103;c=app['cluster']
    assert verifier_cible_isolee(c['url'],c['directory'],c['nonce']) and app['role_sql']=='hisabpro'
    api,_,_=client(app)
    _,_,cap=capture(api);cid=cap['capture']['id'];e=versement(api)
    ok(api.post(chemin(cid),json=corps(e,'30.00')),201)
    d=ok(api.post(chemin(cid),json=corps(e,'45.00')),201)
    ok(api.post(chemin(cid)+f'/{d["items"][0]["id"]}/retirer',json={'motif':'Témoin consolidé681'}))
    sid=ok(api.get('/api/auth/me'))['societe_id']
    def photo():
        with app['engine'].connect() as db:
            tables={t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x WHERE societe_id=:s ORDER BY 1'),{'s':sid}).scalars().all()
                for t in ('ecritures','reglements','ras_reglement_captures','ras_tva_reglement_details','ras_tva_rapprochements','ras_tva_rapprochement_retraits')}
            tables['lignes']=db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id WHERE e.societe_id=:s ORDER BY l.id'),{'s':sid}).scalars().all()
        return tables
    def vue():
        data=ok(api.get(chemin(cid)))
        r=api.get(chemin(cid)+'/pdf');assert r.status_code==200,r.text
        texte='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(r.content)).pages)
        return data,texte
    initial,lecture=photo(),vue()
    historique=ROOT/'.codex-tests/consolidation651_preuve.json'
    ancien=historique.read_bytes() if historique.exists() else None
    interdits={ROOT/'.codex-tests/baseline645.json',ROOT/'.codex-tests/cumul649_preuve.json'}
    lire=Path.read_text
    def portable(path,*a,**kw):
        if path.resolve() in interdits:raise FileNotFoundError('Baseline privée interdite dans une recette livrée.')
        return lire(path,*a,**kw)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path,'read_text',portable)
        banc=precedent.application.__wrapped__(app)
        demarre=False
        try:
            next(banc);demarre=True
            yield app
        finally:
            try:
                banc.close()
                if demarre:
                    preuve=json.loads(historique.read_text(encoding='utf8'))
                    preuve.update(lectures_baselines_privees_interdites=True,role_sql='hisabpro',schema_manuel=103,
                        temoin_rapprochement_donnees_et_pdf_inchanges=photo()==initial and vue()==lecture,
                        temoin_rapprochement_societe=sid,capture_temoin=cid,
                        temoin_rapprochement_sha256=hashlib.sha256(json.dumps(initial,sort_keys=True).encode()).hexdigest(),
                        dossier_cluster=str(c['directory']),dossier_application=str(app['directory']))
                    (ROOT/'.codex-tests/session681_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
                    assert preuve['temoin_rapprochement_donnees_et_pdf_inchanges']
            finally:
                api.close()
                if ancien is not None:historique.write_bytes(ancien)
                elif historique.exists():historique.unlink()


MODULES=(
    'test_recette_candidate675_isole',
    'test_ras_rapprochements681_isole','test_e2e_ras_rapprochements681_isole',
    'test_installation_vierge_103','test_restauration_ras_rapprochements681_isole',
    'test_e2e_ras_cle681_isole',
)
vus={(f.__module__,f.__qualname__) for n,f in list(globals().items()) if n.startswith('test_') and callable(f)}
for i,nom in enumerate(MODULES):
    for cle,f in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(f):
            identite=f.__module__,f.__qualname__
            if identite not in vus:
                vus.add(identite);globals()[f'test_681_{i}_{cle[5:]}']=f
