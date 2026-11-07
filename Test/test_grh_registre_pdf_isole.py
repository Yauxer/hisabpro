"""Registre GRH réel, PDF/logo/filtre, rôles et sociétés sur PostgreSQL nonce."""
from contextlib import closing
from datetime import date
from io import BytesIO
from pathlib import Path
import httpx
import pytest
import hashlib,json
from pypdf import PdfReader
from test_journal_cloture_concurrente_isole import (
    application as application098,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_logo_societe import image_data
from test_reglement_comptabilisation_concurrente_isole import metier
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable

CHEMIN='/api/employes/conges/export/pdf'


@pytest.fixture(scope='module')
def application(application098):
    root=Path(__file__).resolve().parents[1]
    paths=['hisabpro-backend/routers/grh.py','hisabpro-backend/services/grh_registre_pdf.py',
        'src/pages/CNSS.jsx','Test/test_grh_registre_pdf_isole.py']
    sources=lambda:{f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in paths}
    avant=sources();preuve={'sources':avant,'erreur':None}
    try:
        yield application098
        assert sources()==avant
        preuve['sources_inchangees']=True
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:
        (root/'.codex-tests/grh547_preuve.json').write_text(json.dumps(preuve,indent=2),encoding='utf8')
        (root/'.codex-tests/grh547_api.log').write_text(application098['api_log'].read_text(encoding='utf8'),encoding='utf8')


def donnees(api,suffix='A',long=False):
    annee=date.today().year
    ok(api.patch('/api/societe/moi',json={'raison_sociale':'Societe GRH fictive '+suffix,'logo_url':image_data()}))
    rows=[]
    for i in (1,2):
        rows.append(ok(api.post('/api/employes',json={'nom':f'Salarie fictif {suffix}-{i}',
            'salaire_brut':8000,'date_embauche':f'{annee}-01-01','personnes_charge_ir':0}),201))
    demandes=[]
    for i,(employe,jour,statut) in enumerate([(rows[0],1,'approuve'),(rows[1],5,'refuse'),(rows[0],10,None)]):
        motif=f'MOTIF-{suffix}-{i} <preuve & source>'
        if long and i==0:motif+='\n'+'suite de justification fictive '*25
        a=ok(api.post('/api/employes/conges',json={'employe_id':employe['id'],
            'type_absence':'conge' if i!=1 else 'absence','date_debut':f'{annee}-11-{jour:02}',
            'date_fin':f'{annee}-11-{jour+2 if i==0 else jour:02}','motif':motif}),201)
        if statut:a=ok(api.patch(f"/api/employes/conges/{a['id']}",json={'statut':statut,'commentaire_decision':f'DECISION-{suffix}-{i}'}))
        demandes.append(a)
    return demandes


def pdf(response):
    assert response.status_code==200,response.text[:1000]
    assert response.headers['content-type'].startswith('application/pdf')
    assert response.content.startswith(b'%PDF')
    doc=PdfReader(BytesIO(response.content))
    texte='\n'.join(p.extract_text() or '' for p in doc.pages)
    assert any(p.images for p in doc.pages),'Logo absent du PDF'
    return doc,texte


@pytest.mark.parametrize('role',['admin','lecture'])
def test_api_registre_statut_logo_lecture_sans_mutation(application,role):
    admin,email,password=client(application)
    with closing(admin):
        donnees(admin)
        with httpx.Client(base_url=application['api_url']) as lecteur:
            api=admin
            if role=='lecture':
                email=email.replace('@','-lecture@')
                ok(admin.post('/api/utilisateurs',json={'nom':'Lecteur registre fictif','email':email,'mot_de_passe':password,'role':'lecture'}),201)
                lecteur.headers['Authorization']='Bearer '+ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                api=lecteur
            avant=metier(application)
            _,texte=pdf(api.get(CHEMIN))
            assert 'Societe GRH fictive A' in texte
            for i in (0,1,2):assert f'MOTIF-A-{i}' in texte
            _,texte=pdf(api.get(CHEMIN,params={'statut':'approuve'}))
            assert 'MOTIF-A-0' in texte and 'DECISION-A-0' in texte and '<preuve & source>' in texte
            assert 'MOTIF-A-1' not in texte and 'MOTIF-A-2' not in texte
            _,vide=pdf(api.get(CHEMIN,params={'statut':'annule'}))
            assert 'Aucune demande' in vide and 'MOTIF-A' not in vide
            assert api.get(CHEMIN,params={'statut':'invente'}).status_code==422
            assert metier(application)==avant


def test_export_autre_societe_longues_notes_et_session_obligatoire(application):
    with closing(client(application)[0]) as a,closing(client(application)[0]) as b:
        donnees(a,'A',long=True);donnees(b,'B')
        avant=metier(application)
        _,ta=pdf(a.get(CHEMIN));_,tb=pdf(b.get(CHEMIN))
        assert 'MOTIF-A-0' in ta and 'MOTIF-B-0' not in ta
        assert 'MOTIF-B-0' in tb and 'MOTIF-A-0' not in tb
        # Le motif figure aussi dans l'événement de création : comparer le PDF
        # à tous les champs réellement enregistrés, sans supprimer cette trace.
        phrase='suite de justification fictive'
        source=ok(a.get('/api/employes/conges'))
        attendu=sum((x.get('motif') or '').count(phrase)+(x.get('commentaire_decision') or '').count(phrase)
            +sum((h.get('commentaire') or '').count(phrase) for h in x['historique']) for x in source)
        assert attendu==50 and ' '.join(ta.split()).count(phrase)==attendu
        with httpx.Client(base_url=application['api_url']) as anonyme:
            assert anonyme.get(CHEMIN).status_code==401
        assert metier(application)==avant


@pytest.mark.parametrize('largeur',[390,1440])
def test_e2e_registre_pdf_depuis_conges_filtre_lecteur(application,largeur,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    admin,email,password=client(application)
    with closing(admin),playwright.sync_playwright() as p:
        donnees(admin)
        email=email.replace('@','-lecteur@')
        ok(admin.post('/api/utilisateurs',json={'nom':'Lecteur registre fictif','email':email,'mot_de_passe':password,'role':'lecture'}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000);erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/cnss',wait_until='domcontentloaded')
            page.get_by_role('button',name='Congés & absences',exact=True).click()
            page.get_by_label('Filtrer les demandes',exact=True).select_option('approuve')
            bouton=page.get_by_role('button',name='Exporter le registre PDF',exact=True)
            playwright.expect(bouton).to_be_enabled()
            avant=metier(application)
            with page.expect_download() as dl:
                with page.expect_response(lambda r:CHEMIN in r.url) as export:
                    bouton.click()
            assert export.value.status==200 and 'statut=approuve' in export.value.url
            contenu=Path(dl.value.path()).read_bytes()
            texte='\n'.join(x.extract_text() or '' for x in PdfReader(BytesIO(contenu)).pages)
            assert 'MOTIF-A-0' in texte and 'MOTIF-A-1' not in texte
            assert metier(application)==avant and not erreurs and not serveur,(erreurs,serveur)
        except BaseException:
            print(page.locator('body').inner_text()[-5000:])
            page.screenshot(path=str(tmp_path/f'registre547-{largeur}.png'),full_page=True);raise
        finally:browser.close()
