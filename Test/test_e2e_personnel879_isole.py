"""Personnel complet dans Edge, API et PG natif nonce ;aucune donnée réelle."""
from contextlib import closing
from pathlib import Path
import json,re
import pytest
import httpx
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from navigation823_support import navigations_completes823
from test_e2e_administration_isole import connexion,observer,ouvrir_navigation
from test_personnel_workflow877_isole import (
    application875,application873,application093,application092,application091,
    application090,application089,application087,migration,client,ok,role_client,grant,activer,
    W,P,CAPS,comptabilite)
from test_personnel879_donnees_isole import application,application107

R=Path(__file__).resolve().parents[1]


def ouvrir_demande(page,i):
    page.get_by_role('button',name=f'Consulter la demande {i}',exact=True).click()
    return page.get_by_role('dialog')


def soumettre_ui(page,i):
    d=ouvrir_demande(page,i);d.get_by_role('button',name='Préparer la soumission',exact=True).click()
    d.get_by_label('Motif de soumission',exact=True).fill('Soumission fictive du parcours navigateur879')
    d.get_by_role('button',name='Soumettre',exact=True).click()
    expect(d).to_have_count(0)


def approuver_ui(page,i):
    page.get_by_role('button',name='Actualiser',exact=True).click()
    d=ouvrir_demande(page,i);d.get_by_role('button',name='Approuver',exact=True).click()
    d.get_by_label('Motif de la décision',exact=True).fill('Contrôle indépendant fictif879')
    d.get_by_label('Référence du contrôle indépendant',exact=True).fill('CONTROLE-FICTIF-879')
    d.get_by_label('Je confirme être indépendant du préparateur et du bénéficiaire de cette demande.',exact=True).check()
    d.get_by_role('button',name='Confirmer l’approbation',exact=True).click()
    expect(d).to_have_count(0)


def derniere(api,eid):
    return ok(api.get(W+'/demandes',params={'employe_id':eid}))['elements'][0]['id']


@pytest.mark.parametrize('largeur',[1440,390])
def test_879_creation_conditions_validation_et_masque_edge(application,largeur,navigations_completes823):
    app=application;preuve={'largeur':largeur,'erreur':None,'donnees_reelles':False}
    cible=R/f'.codex-tests/personnel879_{largeur}_preuve.json'
    try:
        a,email,secret=client(app)
        with closing(a):
            b,u,mailb,secretb=role_client(app,a,'comptable')
            with closing(b):
                me=ok(a.get('/api/auth/me'))
                for uid in [me['id'],u['id']]:
                    for cap in [*CAPS,'personnel.lire_identifiants_sensibles']:grant(a,uid,cap)
                activer(a);avant=comptabilite(app,me['societe_id'])
                with sync_playwright() as p:
                    browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                    try:
                        ca=browser.new_context(viewport={'width':largeur,'height':1000});cb=browser.new_context(viewport={'width':largeur,'height':1000})
                        page=ca.new_page();review=cb.new_page();page.set_default_timeout(15000);review.set_default_timeout(15000)
                        erreurs,serveur=observer(page,app['api_url']);eb,sb=observer(review,app['api_url'])
                        connexion(page,app['web_url'],email,secret);connexion(review,app['web_url'],mailb,secretb)
                        page.goto(app['web_url']+'/personnel-paie/personnel')
                        expect(page.get_by_role('button',name='Créer un salarié',exact=True)).to_be_visible()
                        ouvrir_navigation(page);nav=page.get_by_role('complementary',name='Navigation principale')
                        expect(nav.get_by_role('button',name='Personnel & Paie',exact=True)).to_have_attribute('aria-expanded','true')
                        expect(nav.locator('[aria-disabled="true"]')).to_have_count(0)
                        expect(nav.get_by_text('À venir',exact=True)).to_have_count(0)
                        nav.get_by_role('link',name='Personnel',exact=True).click()
                        if largeur<768:expect(page.get_by_role('button',name='Ouvrir la navigation',exact=True)).to_have_attribute('aria-expanded','false')
                        page.get_by_role('button',name='Créer un salarié',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Matricule',exact=True).fill(f'FICTIF-{largeur}-879')
                        d.get_by_label('Nom complet',exact=True).fill('Salariée interface fictive879')
                        d.get_by_label('Poste',exact=True).fill('Poste de recette fictif')
                        d.get_by_text('Coordonnées et informations personnelles (facultatif)',exact=True).click()
                        d.get_by_label('Adresse e-mail',exact=True).fill('sal.personnel879@example.com')
                        d.get_by_label('Téléphone',exact=True).fill('TEL-FICTIF-879')
                        d.get_by_label('Numéro CNSS',exact=True).fill('CNSS-FICTIF-879')
                        d.get_by_label('Situation familiale',exact=True).select_option('marie')
                        d.get_by_label('Nombre d’enfants',exact=True).fill('2')
                        d.get_by_label('Personnes à charge IR confirmées',exact=True).fill('2')
                        d.get_by_label('Compte utilisateur du salarié',exact=True).select_option('sans')
                        d.get_by_label('Je confirme l’absence de compte utilisateur pour ce salarié.',exact=True).check()
                        d.get_by_label('Référence du contrôle de rattachement',exact=True).fill('ATTESTATION-FICTIVE-879')
                        d.get_by_label('Motif de création ou de reprise',exact=True).fill('Création fictive par interface879')
                        page.screenshot(path=str(cible.with_name(f'personnel879_{largeur}_creation.png')))
                        d.get_by_role('button',name='Créer le brouillon',exact=True).click()
                        expect(page.get_by_role('heading',name='Salariée interface fictive879',exact=True)).to_be_visible()
                        fiche=ok(a.get(W))['elements'][0];eid=fiche['employe_id'];assert fiche['statut']=='BROUILLON' and fiche['remuneration'] is None
                        i=derniere(a,eid);soumettre_ui(page,i)
                        d=ouvrir_demande(page,i);expect(d.get_by_role('button',name='Approuver',exact=True)).to_have_count(0)
                        expect(d.get_by_text('La décision doit être prise',exact=False)).to_be_visible();d.get_by_role('button',name='Annuler',exact=True).click()
                        review.goto(app['web_url']+'/personnel-paie/demandes');approuver_ui(review,i)
                        page.get_by_role('button',name='Actualiser',exact=True).click()
                        expect(page.get_by_text('CNSS-FICTIF-879',exact=True)).to_be_visible()
                        page.get_by_label('Consulter les conditions au',exact=True).fill('2026-12-31')
                        page.get_by_role('button',name='Proposer une modification',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Nature de la proposition',exact=True).select_option('CONTRAT')
                        d.get_by_label('Type de contrat',exact=True).fill('CDI')
                        d.get_by_label('Début du contrat',exact=True).fill('2026-01-01')
                        d.get_by_label('Date d’effet',exact=True).fill('2026-01-01')
                        d.get_by_label('Référence du justificatif',exact=True).fill('CONTRAT-FICTIF-879')
                        d.get_by_label('Motif de la proposition',exact=True).fill('Contrat de recette fictif')
                        d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                        i=derniere(a,eid);soumettre_ui(page,i);approuver_ui(review,i)
                        page.get_by_role('button',name='Actualiser',exact=True).click()
                        for montant,effet in [('9000,10','2026-01-01'),('9876,54','2027-01-01')]:
                            page.get_by_role('button',name='Proposer une modification',exact=True).click();d=page.get_by_role('dialog')
                            d.get_by_label('Nature de la proposition',exact=True).select_option('REMUNERATION')
                            d.get_by_label('Montant en MAD',exact=True).fill(montant)
                            d.get_by_label('Date d’effet',exact=True).fill(effet)
                            d.get_by_label('Référence du justificatif',exact=True).fill('AVENANT-FICTIF-879')
                            d.get_by_label('Motif de la proposition',exact=True).fill('Condition fictive approuvée séparément')
                            d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                            i=derniere(a,eid);soumettre_ui(page,i);approuver_ui(review,i)
                            page.get_by_role('button',name='Actualiser',exact=True).click()
                        card=page.get_by_role('heading',name='Salariée interface fictive879',exact=True).locator('xpath=ancestor::section[1]')
                        expect(card.get_by_text('9\u202f000,10 MAD',exact=True)).to_be_visible()
                        page.get_by_label('Consulter les conditions au',exact=True).fill('2027-01-01')
                        expect(card.get_by_text('9\u202f876,54 MAD',exact=True)).to_be_visible()
                        page.screenshot(path=str(cible.with_name(f'personnel879_{largeur}_fiche.png')))
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                        assert ok(a.get(f'{W}/{eid}?au=2026-12-31'))['remuneration']['montant']=='9000.10'
                        assert ok(a.get(f'{W}/{eid}?au=2027-01-01'))['remuneration']['montant']=='9876.54'
                        h=next(x for x in ok(a.get(P+'/habilitations')) if x['utilisateur_id']==me['id'] and x['capacite']=='personnel.lire_remuneration' and x['revoquee_at'] is None)
                        ok(a.post(P+f'/habilitations/{h["id"]}/revoquer',json={'motif':'Retrait fictif879'}))
                        page.get_by_role('button',name='Actualiser',exact=True).click()
                        expect(card.get_by_text('Masquée',exact=True)).to_be_visible()
                        assert '9\u202f876,54 MAD' not in page.locator('body').inner_text()
                        page.get_by_role('button',name='Proposer une modification',exact=True).click();d=page.get_by_role('dialog')
                        d.get_by_label('Nature de la proposition',exact=True).select_option('SORTIE')
                        d.get_by_label('Date de sortie',exact=True).fill('2027-06-30')
                        d.get_by_label('Référence du justificatif',exact=True).fill('SORTIE-FICTIVE-879')
                        d.get_by_label('Motif de la proposition',exact=True).fill('Sortie fictive contrôlée')
                        d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                        i=derniere(a,eid);soumettre_ui(page,i);approuver_ui(review,i)
                        page.get_by_role('button',name='Actualiser',exact=True).click()
                        page.get_by_label('Consulter les conditions au',exact=True).fill('2027-07-01')
                        expect(card.get_by_text('Sorti',exact=True)).to_be_visible()
                        expect(page.get_by_role('button',name='Proposer une modification',exact=True)).to_have_count(0)
                        assert not erreurs and not serveur and not eb and not sb,(erreurs,serveur,eb,sb)
                        assert comptabilite(app,me['societe_id'])==avant
                        preuve.update(creation_ui=True,soumission_ui=True,approbation_independante_ui=True,contrat_salaire_futur_ui=True,
                                      sidebar_neuf_rubriques=True,masque_apres_revocation=True,sortie_ui=True,coordonnees_cnss_confirmees=True,sans_ecriture=True,debordement_global=False)
                    finally:browser.close()
    except BaseException as exc:
        preuve['erreur']=repr(exc);raise
    finally:cible.write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')


def test_879_options_scope_minimal_et_permissions(application):
    from test_paie_grh_postgres import dossier
    app=application
    with closing(client(app)[0]) as a,closing(client(app)[0]) as autre:
        me=ok(a.get('/api/auth/me'))
        for m in ['OK879',None,'DUP879','DUP879']:ok(a.post('/api/employes',json=dossier(matricule=m)),201)
        secret=ok(autre.post('/api/employes',json=dossier(matricule='ETRANGER879')),201)
        l,u,_,_=role_client(app,a)
        with closing(l):
            for cap in CAPS:grant(a,me['id'],cap)
            grant(a,u['id'],'personnel.lire_identite');activer(a)
            assert l.get(W+'/options').status_code==403
            r=a.get(W+'/options');q=ok(r)
            assert len(q['historiques'])==4 and len([x for x in q['historiques'] if x['blocage']])==3
            assert 'ETRANGER879' not in r.text and 'salaire' not in r.text and 'numero_cnss' not in r.text
            assert all(set(x)=={'id','nom','email'} for x in q['beneficiaires'])
            assert all(x['id']!=ok(autre.get('/api/auth/me'))['id'] for x in q['beneficiaires'])


@pytest.mark.parametrize('largeur',[1440,390])
def test_879_administrer_acces_activation_reprise_et_rejet_ui(application,largeur,navigations_completes823):
    from test_paie_grh_postgres import dossier
    app=application;a,email,secret=client(app)
    with closing(a):
        e=ok(a.post('/api/employes',json=dossier(nom='Fiche historique fictive879',matricule='HIST879')),201)
        b,u,mailb,secretb=role_client(app,a,'comptable')
        with closing(b):
            me=ok(a.get('/api/auth/me'));avant=comptabilite(app,me['societe_id'])
            with sync_playwright() as p:
                browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
                try:
                    page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
                    erreurs,serveur=observer(page,app['api_url']);connexion(page,app['web_url'],email,secret)
                    page.goto(app['web_url']+'/personnel-paie/personnel')
                    page.get_by_role('link',name='Préparer les habilitations',exact=True).click()
                    for uid,caps in [(me['id'],['personnel.lire_identite','personnel.proposer','personnel.soumettre','personnel.lire_remuneration']),
                                     (u['id'],['personnel.lire_identite','personnel.approuver','personnel.lire_remuneration'])]:
                        for cap in caps:
                            page.get_by_role('button',name='Accorder un droit',exact=True).click();d=page.get_by_role('dialog')
                            d.get_by_label('Utilisateur à habiliter',exact=True).select_option(str(uid))
                            d.get_by_label('Droit à accorder',exact=True).select_option(cap)
                            d.get_by_label('Motif de l’habilitation ou de l’activation',exact=True).fill('Délégation fictive par interface879')
                            d.get_by_role('button',name='Confirmer',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Activer la protection Personnel',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('J’ai compris et je souhaite activer la protection Personnel.',exact=True).check()
                    d.get_by_label('Motif de l’habilitation ou de l’activation',exact=True).fill('Activation du scénario fictif879')
                    d.get_by_role('button',name='Confirmer',exact=True).click();expect(d).to_have_count(0)
                    expect(page.get_by_text('Protection activée',exact=True)).to_be_visible()
                    page.get_by_role('link',name='Salariés',exact=True).click()
                    page.get_by_role('button',name='Reprendre une fiche existante',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Fiche historique',exact=True).select_option(str(e['id']))
                    d.get_by_label('Compte utilisateur du salarié',exact=True).select_option('sans')
                    d.get_by_label('Je confirme l’absence de compte utilisateur pour ce salarié.',exact=True).check()
                    d.get_by_label('Référence du contrôle de rattachement',exact=True).fill('REPRISE-FICTIVE-879')
                    d.get_by_label('Motif de création ou de reprise',exact=True).fill('Reprise de recette isolée879')
                    d.get_by_role('button',name='Créer le brouillon',exact=True).click()
                    expect(page.get_by_role('heading',name='Fiche historique fictive879',exact=True)).to_be_visible()
                    i=derniere(a,e['id']);soumettre_ui(page,i)
                    ctx=browser.new_context(viewport={'width':largeur,'height':1000});review=ctx.new_page();review.set_default_timeout(15000)
                    eb,sb=observer(review,app['api_url']);connexion(review,app['web_url'],mailb,secretb)
                    review.goto(app['web_url']+'/personnel-paie/demandes');d=ouvrir_demande(review,i)
                    d.get_by_role('button',name='Rejeter',exact=True).click()
                    d.get_by_label('Motif de la décision',exact=True).fill('Complément de pièce fictive nécessaire')
                    d.get_by_label('Référence du contrôle indépendant',exact=True).fill('REJET-FICTIF-879')
                    d.get_by_label('Je confirme être indépendant du préparateur et du bénéficiaire de cette demande.',exact=True).check()
                    d.get_by_role('button',name='Confirmer le rejet',exact=True).click();expect(d).to_have_count(0)
                    page.get_by_role('button',name='Actualiser',exact=True).click()
                    card=page.get_by_role('heading',name='Fiche historique fictive879',exact=True).locator('xpath=ancestor::section[1]')
                    expect(card.get_by_text('Brouillon',exact=True)).to_be_visible()
                    page.get_by_role('button',name='Proposer une modification',exact=True).click();d=page.get_by_role('dialog')
                    d.get_by_label('Motif de la proposition',exact=True).fill('Complément fourni en scénario fictif')
                    d.get_by_role('button',name='Enregistrer la proposition',exact=True).click();expect(d).to_have_count(0)
                    i2=derniere(a,e['id']);assert i2!=i;soumettre_ui(page,i2);approuver_ui(review,i2)
                    page.get_by_role('link',name='Habilitations',exact=True).click()
                    ligne=page.get_by_role('row').filter(has_text=email).filter(has_text='Consulter les rémunérations')
                    ligne.get_by_role('button',name=re.compile('Révoquer le droit')).click();d=page.get_by_role('dialog')
                    d.get_by_label('Motif de l’habilitation ou de l’activation',exact=True).fill('Retrait de recette fictif879')
                    d.get_by_role('button',name='Confirmer',exact=True).click();expect(d).to_have_count(0)
                    expect(page.get_by_role('row').filter(has_text=email).filter(has_text='Consulter les rémunérations').get_by_text('Révoqué',exact=True)).to_be_visible()
                    page.screenshot(path=str(R/f'.codex-tests/personnel879_{largeur}_habilitations.png'))
                    assert 'personnel.lire_remuneration' not in ok(a.get(P+'/acces'))['capacites']
                    assert comptabilite(app,me['societe_id'])==avant
                    assert not erreurs and not serveur and not eb and not sb,(erreurs,serveur,eb,sb)
                finally:browser.close()


def preparer_equipe(app):
    a,email,secret=client(app);b,u,mailb,secretb=role_client(app,a,'comptable')
    me=ok(a.get('/api/auth/me'))
    for uid in [me['id'],u['id']]:
        for cap in CAPS:grant(a,uid,cap)
    activer(a)
    return a,b,email,secret,me


def test_879_reseau_interrompu_reessai_et_navigations(application,navigations_completes823):
    app=application;a,b,email,secret,me=preparer_equipe(app)
    with closing(a),closing(b),sync_playwright() as p:
        avant=comptabilite(app,me['societe_id']);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':390,'height':900});page.set_default_timeout(15000)
            erreurs,serveur=observer(page,app['api_url']);connexion(page,app['web_url'],email,secret)
            coupe=[False]
            def transport(route):
                if not coupe[0] and route.request.method=='GET':coupe[0]=True;route.abort('failed')
                else:route.continue_()
            # Coupure de transport seulement ;aucune réponse métier factice.
            page.route(re.compile(r'/api/employes/personnel(?:\?|$)'),transport)
            page.goto(app['web_url']+'/personnel-paie/personnel')
            expect(page.get_by_role('alert').filter(has_text='Connexion au serveur indisponible')).to_be_visible()
            page.get_by_role('button',name='Actualiser',exact=True).click()
            expect(page.get_by_text('Aucun dossier salarié.',exact=False)).to_be_visible()
            ouvrir_navigation(page);page.keyboard.press('Escape')
            expect(page.get_by_role('button',name='Ouvrir la navigation',exact=True)).to_have_attribute('aria-expanded','false')
            page.goto(app['web_url']+'/personnel-paie/rubrique-inexistante')  # 968 : avances désormais disponible
            expect(page.get_by_role('heading',name='Rubrique à venir',exact=True)).to_be_visible()
            page.get_by_role('link',name='Revenir au Personnel',exact=True).click()
            page.get_by_role('link',name='Espace historique',exact=True).click()
            expect(page.get_by_role('heading',name='Paie & GRH',exact=True)).to_be_visible()
            assert not erreurs and not serveur and comptabilite(app,me['societe_id'])==avant
        finally:browser.close()


def test_879_conflit_revision_visible_sans_ecraser_dossier(application,navigations_completes823):
    from test_personnel_workflow877_isole import actif,proposition,creation,soumettre
    app=application;a,b,email,secret,me=preparer_equipe(app);eq={'a':a,'b':b}
    with closing(a),closing(b),sync_playwright() as p:
        eid=actif(eq)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(15000)
            erreurs,serveur=observer(page,app['api_url']);connexion(page,app['web_url'],email,secret)
            page.goto(app['web_url']+f'/personnel-paie/personnel/{eid}')
            page.get_by_role('button',name='Proposer une modification',exact=True).click();d=page.get_by_role('dialog')
            d.get_by_label('Nom complet',exact=True).fill('NE-PAS-ECRASER-879')
            d.get_by_label('Motif de la proposition',exact=True).fill('Proposition périmée fictive')
            q=proposition(eq,eid,1,'DOSSIER',{'nom':'Nom approuvé concurrent879','poste':None})
            soumettre(a,q['id'],1)
            ok(b.post(f'{W}/demandes/{q["id"]}/approuver',json={'revision_attendue':1,'motif':'Autre décision fictive',
                'independance_confirmee':True,'reference_independance':'CONCURRENCE-FICTIVE-879'}))
            d.get_by_role('button',name='Enregistrer la proposition',exact=True).click()
            expect(d.get_by_role('alert')).to_contain_text('Révision périmée')
            assert ok(a.get(f'{W}/{eid}'))['nom']=='Nom approuvé concurrent879'
            d.get_by_role('button',name='Annuler',exact=True).click();page.get_by_role('button',name='Actualiser',exact=True).click()
            expect(page.get_by_role('heading',name='Nom approuvé concurrent879',exact=True)).to_be_visible()
            assert not erreurs and not serveur
        finally:browser.close()


def test_879_changement_societe_ne_reprend_pas_donnees_ou_brouillon(application,navigations_completes823):
    from test_personnel_workflow877_isole import creation
    app=application;a,b,email,secret,me=preparer_equipe(app)
    with closing(a),closing(b),sync_playwright() as p:
        ok(a.post(W,json=creation(nom='DONNEE-SOCIETE-A-879')),201)
        nom_a=ok(a.get('/api/societe/moi'))['raison_sociale']
        nouvelle=ok(a.post('/api/societes/nouvelle',json={'raison_sociale':'SOCIETE-B-FICTIVE-879','ville':'Rabat'}),201)
        token=ok(a.post(f'/api/societes/switcher/{nouvelle["id"]}'))['access_token']
        with httpx.Client(base_url=app['api_url'],headers={'Authorization':'Bearer '+token}) as autre:
            grant(autre,me['id'],'personnel.lire_identite');activer(autre)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(15000)
            erreurs,serveur=observer(page,app['api_url']);connexion(page,app['web_url'],email,secret)
            page.goto(app['web_url']+'/personnel-paie/personnel')
            expect(page.get_by_text('DONNEE-SOCIETE-A-879',exact=True)).to_be_visible()
            page.get_by_role('button',name='Créer un salarié',exact=True).click();d=page.get_by_role('dialog')
            d.get_by_label('Nom complet',exact=True).fill('BROUILLON-LOCAL-A-879')
            d.get_by_role('button',name='Annuler',exact=True).click()
            page.get_by_role('button',name=nom_a,exact=True).click()
            page.get_by_role('button').filter(has_text='SOCIETE-B-FICTIVE-879').click()
            expect(page.get_by_text('Aucun dossier salarié.',exact=False)).to_be_visible()
            assert 'DONNEE-SOCIETE-A-879' not in page.locator('body').inner_text()
            assert not page.locator('input').evaluate_all("els=>els.some(e=>e.value==='BROUILLON-LOCAL-A-879')")
            expect(page.get_by_role('button',name='Créer un salarié',exact=True)).to_have_count(0)
            assert ok(a.get(W))['total']==1 and not erreurs and not serveur
        finally:browser.close()
