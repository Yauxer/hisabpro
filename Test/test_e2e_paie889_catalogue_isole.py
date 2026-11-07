"""Catalogue,aperçu et décision indépendante dans Edge desktop/mobile."""
from contextlib import closing
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_paie889_catalogue_isole import (
    application,application112,application111,application110,application109,application108,application107,application875,application873,
    application093,application092,application091,application090,application089,application087,migration,cles_coffre885,
    client,ok,role_client,grant,activer,CAPS,comptabilite,E)
from test_e2e_personnel881_isole import connexion_personnel
from test_e2e_administration_isole import observer

R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('largeur',[1440,390])
def test_889_catalogue_deux_personnels_edge(application,largeur):
    app=application
    with closing(client(app)[0]) as admin:
        prep,u,mail,secret=role_client(app,admin,'personnel');valid,v,mailv,secretv=role_client(app,admin,'personnel')
        with closing(prep),closing(valid):
            droit=None
            for uid in [u['id'],v['id']]:
                for cap in CAPS:
                    g=grant(admin,uid,cap)
                    if uid==u['id'] and cap=='personnel.lire_remuneration':droit=g['id']
            if largeur==1440:grant(admin,v['id'],'personnel.valider_regles_paie')
            activer(admin);sid=ok(admin.get('/api/auth/me'))['societe_id'];avant=comptabilite(app,sid)
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    cp=browser.new_context(viewport={'width':largeur,'height':1000});cv=browser.new_context(viewport={'width':largeur,'height':1000})
                    page=cp.new_page();review=cv.new_page();ep,sp=observer(page,app['api_url']);ev,sv=observer(review,app['api_url'])
                    connexion_personnel(page,app,mail,secret);connexion_personnel(review,app,mailv,secretv)
                    page.goto(app['web_url']+'/personnel-paie/elements');expect(page.get_by_role('heading',name='Éléments de paie',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Créer une rubrique',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Code de rubrique',exact=True).fill('PRIME_FICTIVE889');d.get_by_label('Libellé de rubrique',exact=True).fill('Prime FICTIVE889')
                    d.get_by_label('Début d’application',exact=True).fill('2026-01-01');d.get_by_label('Motif de la proposition',exact=True).fill('Exemple entièrement fictif889')
                    d.get_by_label('Justificatifs attendus (séparés par virgules)',exact=True).fill('ATTESTATION_FICTIVE, MISSION_FICTIVE')
                    for reg,plafond in [('IR','500.00'),('CNSS','300.00'),('AMO',None)]:
                        d.get_by_label('Traitement '+reg,exact=True).select_option('PLAFOND_MONTANT' if plafond else 'SOUMIS')
                        d.get_by_label('Unité du plafond '+reg,exact=True).select_option('operation')
                        d.get_by_label('Conditions '+reg,exact=True).fill('Hypothèse FICTIVE889 ;aucune valeur réglementaire')
                        if plafond:d.get_by_label(f'Plafond {reg} (MAD)',exact=True).fill(plafond)
                    if largeur==1440:
                        d.get_by_label('Statut réglementaire IR',exact=True).select_option('VALIDE')
                        for label,valeur in [('Texte IR','TEXTE FICTIF889,aucune règle légale validée'),('Article IR','ARTICLE FICTIF889'),('URL officielle IR','https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf'),('Empreinte SHA-256 de la preuve IR','a'*64)]:d.get_by_label(label,exact=True).fill(valeur)
                    d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                    item=ok(prep.get(E))['elements'][0];rid=item['id'];i=item['derniere_id']
                    assert item['dernier_contenu']['justificatifs']==['ATTESTATION_FICTIVE','MISSION_FICTIVE']
                    page.get_by_role('button',name='Consulter PRIME_FICTIVE889',exact=True).click()
                    page.get_by_text('Aperçu pédagogique de ventilation · version 1',exact=True).click()
                    page.get_by_label('Montant à simuler version 1',exact=True).fill('800.01');page.get_by_role('button',name='Simuler la ventilation',exact=True).click()
                    expect(page.get_by_text('IR : soumis 300.01 MAD',exact=False)).to_be_visible();expect(page.get_by_text('CNSS : soumis 500.01 MAD',exact=False)).to_be_visible()
                    review.goto(app['web_url']+'/personnel-paie/elements');review.get_by_role('button',name='Consulter PRIME_FICTIVE889',exact=True).click()
                    review.get_by_role('button',name='Approuver la version 1',exact=True).click();d=review.get_by_role('dialog')
                    d.get_by_label('Motif de la décision',exact=True).fill('Contrôle indépendant fictif889');d.get_by_label('Référence du contrôle',exact=True).fill('CONTROLE-FICTIF889')
                    d.get_by_label('Je confirme être indépendant du préparateur.',exact=True).check()
                    if largeur==1440:d.get_by_label('J’ai vérifié les textes, preuves et conditions des règles déclarées validées.',exact=True).check()
                    d.get_by_role('button',name='Confirmer l’approbation',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Actualiser',exact=True).click();page.get_by_role('button',name='Consulter PRIME_FICTIVE889',exact=True).click()
                    page.get_by_role('button',name='Proposer une nouvelle version',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Début d’application',exact=True).fill('2027-01-01');d.get_by_label('Libellé de rubrique',exact=True).fill('Prime FUTURE FICTIVE889');d.get_by_label('Motif de la proposition',exact=True).fill('Version future fictive889')
                    d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                    review.get_by_role('button',name='Actualiser',exact=True).click();review.get_by_role('button',name='Consulter PRIME_FICTIVE889',exact=True).click()
                    review.get_by_role('button',name='Approuver la version 2',exact=True).click();d=review.get_by_role('dialog')
                    d.get_by_label('Motif de la décision',exact=True).fill('Contrôle futur fictif889');d.get_by_label('Référence du contrôle',exact=True).fill('CONTROLE-FUTUR-FICTIF889');d.get_by_label('Je confirme être indépendant du préparateur.',exact=True).check()
                    if largeur==1440:d.get_by_label('J’ai vérifié les textes, preuves et conditions des règles déclarées validées.',exact=True).check()
                    d.get_by_role('button',name='Confirmer l’approbation',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Actualiser',exact=True).click();page.get_by_label('Règles applicables au',exact=True).fill('2026-12-31')
                    expect(page.get_by_text('Version approuvée applicable à cette date : Prime FICTIVE889',exact=True)).to_be_visible()
                    page.get_by_label('Règles applicables au',exact=True).fill('2027-01-01');expect(page.get_by_text('Version approuvée applicable à cette date : Prime FUTURE FICTIVE889',exact=True)).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    dossier=R/'docs/personnel-paie/preuves';page.screenshot(path=str(dossier/f'889_{largeur}_catalogue.png'))
                    ok(admin.post('/api/employes/securite/habilitations/'+str(droit)+'/revoquer',json={'motif':'Fin accès fictif889'}))
                    page.get_by_role('button',name='Actualiser',exact=True).click();expect(page.get_by_role('alert')).to_contain_text('habilitations identité et rémunération')
                    assert prep.get(E).status_code==403 and 'Prime FUTURE FICTIVE889' not in page.locator('body').inner_text()
                    assert comptabilite(app,sid)==avant and not ep and not sp and not ev and not sv,(ep,sp,ev,sv)
                finally:browser.close()
