"""Registre GRH après pg_dump/pg_restore réels : deux clusters nonce, aucun mock métier."""
from io import BytesIO
from pathlib import Path
import hashlib,json,re
import httpx
from pypdf import PdfReader
from sqlalchemy import create_engine
import test_restauration_justificatifs_acl_isole as recette
from test_restauration_journal098_isole import test_restauration098_journal_conflit_et_reprise as scenario098
from test_grh_registre_pdf_isole import donnees,CHEMIN
from test_reglement_comptabilisation_concurrente_isole import metier
from postgres_isole import verifier_cible_isolee

ROOT=Path(__file__).resolve().parents[1]


def contenu_pdf(response):
    assert response.status_code==200,response.text[:1000]
    doc=PdfReader(BytesIO(response.content))
    assert any(p.images for p in doc.pages)
    texte='\n'.join(p.extract_text() or '' for p in doc.pages)
    # L'heure d'édition change ; les dates des demandes/événements sont conservées.
    return re.sub(r'Édition : \d{2}/\d{2}/\d{4} \d{2}:\d{2} UTC','Édition : [variable]',texte)


def test_registre_grh_logo_historique_apres_restauration_froide098(monkeypatch,tmp_path):
    client_orig=recette.client;lancer_orig=recette.lancer_cible;memo={}
    fichiers=['hisabpro-backend/routers/grh.py','hisabpro-backend/services/grh_registre_pdf.py',
        'src/pages/CNSS.jsx','Test/test_grh_registre_pdf_isole.py',Path(__file__).relative_to(ROOT).as_posix()]
    sources=lambda:{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in fichiers}
    avant_sources=sources();preuve={'erreur':None,'sources':avant_sources}
    def client_grh(app):
        api,email,password=client_orig(app)
        if not memo:
            c=app['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
            donnees(api,'RESTAURATION')
            rows=recette.ok(api.get('/api/employes/conges'));assert len(rows)==3
            avant=metier(app)
            response=api.get(CHEMIN)
            texte=contenu_pdf(response)
            assert metier(app)==avant
            memo.update(email=email,password=password,rows=rows,texte=texte)
            (ROOT/'.codex-tests/registre_grh549_exemple.pdf').write_bytes(response.content)
            preuve['pdf_source_sha256']=hashlib.sha256(response.content).hexdigest()
        return api,email,password
    def cible_grh(c,uploads):
        assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
        proc,url,log=lancer_orig(c,uploads)
        engine=create_engine(c['url'])
        try:
            with httpx.Client(base_url=url) as api:
                recette.connecter(api,memo['email'],memo['password'])
                avant=metier({'engine':engine})
                assert recette.ok(api.get('/api/employes/conges'))==memo['rows']
                response=api.get(CHEMIN)
                assert contenu_pdf(response)==memo['texte']
                assert metier({'engine':engine})==avant
                preuve['pdf_cible_sha256']=hashlib.sha256(response.content).hexdigest()
            preuve['json_historique_logo_pdf_conserves']=True
            return proc,url,log
        except BaseException:
            recette.arreter_processus_cree(proc);raise
        finally:engine.dispose()
    # Enveloppes du laboratoire uniquement : les API, calculs, sauvegarde et
    # restauration du scénario098 sont exécutés réellement, sans interception.
    monkeypatch.setattr(recette,'client',client_grh)
    monkeypatch.setattr(recette,'lancer_cible',cible_grh)
    try:
        scenario098(monkeypatch,tmp_path)
        p=json.loads((ROOT/'.codex-tests/restauration490_preuve.json').read_text(encoding='utf8'))
        assert p['erreur'] is None and p['source_preservee'] and p['cibles_supprimees']
        assert p['tables']==74 and p['trois_fonctions098_identiques'] and p['journal409_et_reprise']
        assert preuve['json_historique_logo_pdf_conserves'] and sources()==avant_sources
        preuve.update(source_preservee=True,cibles_supprimees=True,tables=74,sources_inchangees=True)
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (ROOT/'.codex-tests/grh549_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
