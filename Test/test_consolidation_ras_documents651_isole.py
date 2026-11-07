"""Campagne commune102 : témoins RAS/documentaire et factures liées préservés."""
from pathlib import Path
import hashlib,importlib,json,os
import pytest
from sqlalchemy import text
from test_factures_liees635_isole import (
    application as application102,application101,application100,application099,
    application098,application097,application093,application092,application091,
    application090,application089,application087,migration,vente,demande,chemin,PATH,
)
from test_ras_documents647_isole import capture,joindre,chemins,ligne
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok

ROOT=Path(__file__).resolve().parents[1]


def empreintes_application(root=ROOT):
    """Découverte locale portable ; aucune baseline privée ni lecture de secret."""
    root=Path(root)
    exclus={'.git','.venv','venv','node_modules','dist','__pycache__','uploads','.pytest_cache','.codex-tests'}
    fichiers=[]
    for dossier in ('src','hisabpro-backend'):
        for rep,dirs,noms in os.walk(root/dossier):
            dirs[:]=[d for d in dirs if d not in exclus]
            for nom in noms:
                p=Path(rep)/nom
                if nom.startswith('.env') or p.suffix in {'.pyc','.log','.zip'}:continue
                fichiers.append(p)
    for nom in ('package.json','package-lock.json','index.html','vite.config.js'):
        p=root/nom
        if p.is_file():fichiers.append(p)
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fichiers)}


@pytest.fixture(scope='module')
def application(application102):
    app=application102;a,b,ids=vente(app);ras,_,_=client(app)
    try:
        correspondance=ok(a.post(chemin(ids),json=demande(a,ids)),201)
        f,_,c=capture(ras,annuler=True);_,r=ligne(ras,chemins()[0],c['capture']['id'])
        joindre(ras,c['capture']['ecriture_id'],'temoin651_capture.pdf')
        joindre(ras,r['od_annulation_id'],'temoin651_annulation.pdf')
        rsid=ok(ras.get('/api/societe/moi'))['id'];societes={'a':ids['sid'],'b':ids['bid'],'r':rsid}
        def photos():
            with app['engine'].connect() as db:
                resultat={t:db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x WHERE societe_id IN (:a,:b,:r) ORDER BY 1'),societes).scalars().all()
                    for t in ('factures','ecritures','reglements','ras_reglement_captures','ras_reglement_annulations','ras_tva_reglement_details','ecriture_justificatifs')}
                for t,parent,cle in [('lignes_ecriture','ecritures','ecriture_id'),('lignes_facture','factures','facture_id')]:
                    resultat[t]=db.execute(text(f'SELECT row_to_json(x)::text FROM {t} x JOIN {parent} p ON p.id=x.{cle} WHERE p.societe_id IN (:a,:b,:r) ORDER BY x.id'),societes).scalars().all()
                return resultat
        def suivis():
            return {'liaison':ok(a.get(f'{PATH}/factures/{ids["fid"]}/correspondance')),
                'vue_liee':ok(a.get(f'{PATH}/{ids["liaison"]}/correspondances')),
                'ras':{p:ok(ras.get(p)) for p in chemins()},
                'files_capture':ok(ras.get(f"/api/attachments/ecriture/{c['capture']['ecriture_id']}")),
                'files_annulation':ok(ras.get(f"/api/attachments/ecriture/{r['od_annulation_id']}"))}
        def sources():return empreintes_application()
        origine,historique,empreintes=photos(),suivis(),sources()
        assert historique['liaison']==correspondance and len(historique['files_capture'])==len(historique['files_annulation'])==1
        try:yield app
        finally:
            maintenant,lecture,codes=photos(),suivis(),sources()
            preuve={'sources_inchangees':codes==empreintes,'temoins_comptables_documentaires_inchanges':maintenant==origine and lecture==historique,
                'sources':empreintes,'temoin_sha256':hashlib.sha256(json.dumps(origine,sort_keys=True).encode()).hexdigest(),
                'societes_temoin':societes,'documents_temoin':2}
            (ROOT/'.codex-tests/consolidation651_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
            assert preuve['sources_inchangees'] and preuve['temoins_comptables_documentaires_inchanges']
    finally:a.close();b.close();ras.close()


MODULES=('test_consolidation_ras_tva593_isole','test_consolidation_factures635_isole',
    'test_e2e_ras_tva_coherence_isole','test_ras_documents647_isole','test_e2e_ras_documents647_isole',
    'test_ras_documents647_precision','test_oracle_ras_documents649_isole','test_annexe_ras_documents649',
    'test_reglements_centimes642','test_e2e_pieces_contexte645_isole')
vus=set()
for i,nom in enumerate(MODULES):
    for cle,f in vars(importlib.import_module(nom)).items():
        if cle.startswith('test_') and callable(f):
            identite=f.__module__,f.__qualname__
            if identite not in vus:
                vus.add(identite);globals()[f'test_651_{i}_{cle[5:]}']=f
