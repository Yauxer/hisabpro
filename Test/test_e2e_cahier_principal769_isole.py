"""Premiers cas exacts du cahier principal : vraies saisies UI, aucune donnée réelle."""
from datetime import date
from pathlib import Path
from uuid import uuid4
import hashlib,json,re,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'Test'),str(ROOT/'hisabpro-backend')]
import httpx
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_facturation_isole import application
from test_e2e_administration_isole import observer
from postgres_isole import verifier_cible_isolee


def champ(page,label,tag='input'):
    return page.locator('label').filter(has_text=re.compile('^'+re.escape(label)+'$')).locator('..').locator(tag).first


def test_769_creation_societe_parametres_et_exercices_du_cahier(application):
    c=application['cluster'];assert verifier_cible_isolee(c['url'],c['directory'],c['nonce'])
    src=ROOT/'docs/recette/jeu_donnees_recette.json';data=json.loads(src.read_text(encoding='utf8'));s=data['societe']
    email=f'cahier769-{uuid4().hex[:8]}@hisabpro-recette.example'
    preuve={'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'parcours_reel_UI':True,'largeur':1440,
      'variation_source':'Adresse email de laboratoire unique ; autres valeurs société identiques au cahier', 'cas':[], 'erreur':None}
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1100});page.set_default_timeout(15000)
            errors,server_errors=observer(page,application['api_url'])
            page.goto(application['web_url'],wait_until='domcontentloaded')
            page.get_by_role('button',name='Créer un compte',exact=True).click()
            page.get_by_placeholder('Prénom NOM').fill(s['nom_admin'])
            page.get_by_placeholder('Ma Société SARL').fill(s['raison_sociale'])
            page.get_by_placeholder('Casablanca').fill(s['ville'])
            page.get_by_placeholder('admin@societe.ma').fill(email)
            page.locator('input[type="password"]').fill(s['password_test'])
            page.get_by_role('button',name='Créer mon compte',exact=True).click();page.wait_for_url('**/dashboard')
            token=page.evaluate("localStorage.getItem('hisabpro_token')");assert token
            assert page.evaluate("localStorage.getItem('hisabpro_role')")=='admin'
            with httpx.Client(base_url=application['api_url'],headers={'Authorization':'Bearer '+token},timeout=30) as api:
                def lire(url):
                    r=api.get(url);assert r.status_code==200,r.text;return r.json()
                profil=lire('/api/societe/moi');assert profil['raison_sociale']==s['raison_sociale']
                expect(page.locator('aside').get_by_text('Facturation',exact=True)).to_be_visible()
                expect(page.locator('aside').get_by_text('Comptabilité',exact=True)).to_be_visible()
                preuve['cas'].append({'id':'HP-ADM-001','etapes':'Création société et administrateur via interface,connexion immédiate','statut_automatise':'Réussi'})
                page.goto(application['web_url']+'/parametres')
                expect(champ(page,'Raison sociale *')).to_have_value(s['raison_sociale'])
                champs={'Capital social (MAD)':s['capital_social'],'Identifiant Fiscal (IF)':s['identifiant_fiscal'],
                    'ICE':s['ice'],'RC (Registre Commerce)':s['rc'],'Patente':s['patente'],
                    'Ville':s['ville'],'Premier exercice (année de clôture)':str(s['exercice_debut'])}
                for label,value in champs.items():champ(page,label).fill(value)
                champ(page,'Adresse','textarea').fill(s['adresse'])
                for label,value in [('Forme juridique',s['forme_juridique']),('Périodicité TVA',s['periodicite_tva']),
                    ('Régime fiscal',s['regime_fiscal']),('Régime de TVA',s['regime_tva']),('Devise de tenue de comptabilité',s['devise'])]:
                    champ(page,label,'select').select_option(value)
                page.get_by_role('button',name='Enregistrer',exact=True).click();expect(page.get_by_text('Enregistré',exact=True)).to_be_visible()
                page.reload();expect(champ(page,'Identifiant Fiscal (IF)')).to_have_value(s['identifiant_fiscal'])
                profil=lire('/api/societe/moi')
                for key in ['forme_juridique','identifiant_fiscal','ice','rc','patente','adresse','ville','devise','regime_fiscal','regime_tva','periodicite_tva','exercice_debut']:
                    assert profil[key]==s[key],(key,profil[key],s[key])
                assert float(profil['capital_social'])==200000
                preuve['cas'].append({'id':'HP-ADM-002','etapes':'Identité et paramètres exacts saisis,sauvegardés,rechargés et comparés àAPI','statut_automatise':'Réussi'})
                exercices=lire('/api/exercices');exercices={e['annee']:e for e in exercices}
                for annee in [2025,2026]:
                    assert exercices[annee]['date_debut']==f'{annee}-01-01' and exercices[annee]['date_fin']==f'{annee}-12-31'
                    periodes=lire(f'/api/exercices/{annee}/periodes');assert len(periodes)==12
                    assert [p['numero'] for p in periodes]==list(range(1,13))
                    assert periodes[0]['date_debut']==f'{annee}-01-01' and periodes[-1]['date_fin']==f'{annee}-12-31'
                page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2025')
                expect(page.get_by_label('Exercice actif',exact=True)).to_have_value('2025')
                assert lire('/api/ecritures?exercice=2025')==[]
                preuve['cas'].append({'id':'HP-ADM-003','etapes':'Exercices2025/2026 présents avec12mois exacts,sélection2025 ; branche création conditionnelle nonrequise','statut_automatise':'Partiel','limite':'Préparer exercice suivant ettest de refus surpériode clôturée couverts par autres scénarios,nonjoués dansce cas'})
                page.screenshot(path=str(ROOT/'.codex-tests/recette769_societe_cahier.png'),full_page=True)
                assert not errors and not server_errors,(errors,server_errors)
        except BaseException as e:
            preuve['erreur']=repr(e)
            page.screenshot(path=str(ROOT/'.codex-tests/recette769_societe_echec.png'),full_page=True)
            (ROOT/'.codex-tests/recette769_societe_echec.txt').write_text(page.locator('body').inner_text(),encoding='utf8')
            raise
        finally:
            (ROOT/'.codex-tests/cahier_principal769_preuve.json').write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
            browser.close()
