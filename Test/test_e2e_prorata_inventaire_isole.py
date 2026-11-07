from contextlib import closing
from decimal import Decimal
from io import BytesIO
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader
from test_journal_cloture_concurrente_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_ajustements_inventaire_isole import exercice
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_logo_societe import image_data
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def ouvrir(page,app):
    page.goto(app['web_url']+'/cloture',wait_until='domcontentloaded')
    page.get_by_label('Exercice actif',exact=True).select_option('2025')
    expect(page.get_by_role('region',name='Calcul documentaire CCA PCA',exact=True,include_hidden=True)).to_contain_text('2025-12-31')
    page.get_by_text('Calcul documentaire facultatif CCA / PCA',exact=True).click()
    region=page.get_by_role('region',name='Calcul documentaire CCA PCA',exact=True)
    expect(region).to_be_visible()
    return region


def remplir(region,type_='cca'):
    region.get_by_label('Type de report',exact=True).select_option(type_)
    region.get_by_label('Référence du contrat ou de la pièce',exact=True).fill('CONTRAT-FICTIF595')
    region.get_by_label('Montant déjà comptabilisé (MAD)',exact=True).fill('12000,00')
    region.get_by_label('Base du montant',exact=True).select_option('autre')
    region.get_by_label('Début de la période',exact=True).fill('2025-10-01')
    region.get_by_label('Fin de la période',exact=True).fill('2026-03-31')
    region.get_by_role('button',name='Calculer en jours calendaires',exact=True).click()
    resultat=region.get_by_role('region',name='Résultat du calcul documentaire',exact=True)
    expect(resultat).to_contain_text('5.934,07')
    return resultat


def ecriture(api,date,lignes,ref):
    e=ok(api.post('/api/ecritures',json={'date':date,'date_piece':date,'reference':ref,
        'journal':'BQ','libelle':ref,'lignes':[{'compte':c,'debit':d,'credit':cr,'libelle':ref} for c,d,cr in lignes]}),201)
    ok(api.post(f"/api/ecritures/{e['id']}/valider"));return e['id']


def photo(app,ids):
    with app['engine'].connect() as db:
        return [(db.execute(text('SELECT row_to_json(e)::text FROM ecritures e WHERE id=:i'),{'i':i}).scalar_one(),
            db.execute(text('SELECT row_to_json(l)::text FROM lignes_ecriture l WHERE ecriture_id=:i ORDER BY id'),{'i':i}).scalars().all()) for i in ids]


@pytest.mark.parametrize('role,type_,largeur',[('admin','cca',1440),('comptable','pca',390),('lecture','cca',390)])
def test_595_calcul_pdf_reprise_et_comptabilite(application,role,type_,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api);ok(api.patch('/api/societe/moi',json={'logo_url':image_data('PNG')}))
        ids=[ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAPITAL-FICTIF595')]
        lignes=[('6125','12000',0),('5141',0,'12000')] if type_=='cca' else [('5141','12000',0),('7124',0,'12000')]
        ids.append(ecriture(api,'2025-10-01',lignes,'BASE-COMPTABLE-FICTIVE595'))
        sources=photo(application,ids)
        if role!='admin':
            email=email.replace('@','-'+role+'@')
            ok(api.post('/api/utilisateurs',json={'nom':'Fictif595','email':email,'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            erreurs,serveur=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
            region=ouvrir(page,application);avant=donnees_metier(application);resultat=remplir(region,type_)
            expect(resultat).to_contain_text('90 / 182 jours')
            with page.expect_download() as telechargement:resultat.get_by_role('button',name='Télécharger la feuille PDF',exact=True).click()
            d=telechargement.value;destination=tmp_path/f'prorata595_{role}.pdf';d.save_as(destination)
            assert d.suggested_filename==f'calcul_prorata_2025_{type_}.pdf'
            pdf=PdfReader(destination);assert any(p.images for p in pdf.pages)
            assert '5934.07' in '\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert donnees_metier(application)==avant
            region.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'prorata595_{role}_{largeur}.png'))
            assert region.evaluate('(e)=>e.scrollWidth<=e.clientWidth+1')
            reprendre=resultat.get_by_role('button',name='Utiliser le montant et le libellé',exact=True)
            if role=='lecture':expect(reprendre).to_be_disabled()
            else:
                reprendre.click()
                expect(page.get_by_label('Montant HT / comptable (MAD)',exact=True)).to_have_value('5934.07')
                assert '90/182 jours' in page.get_by_label('Libellé / justification',exact=True).input_value()
                assert donnees_metier(application)==avant
                creer=page.get_by_role('button',name='Créer l’écriture',exact=True);expect(creer).to_be_disabled()
                page.get_by_role('button',name='Vérifier l’écriture',exact=True).click();expect(creer).to_be_enabled()
                with page.expect_response(lambda r:r.request.method=='POST' and '/ajustements?exercice=2025' in r.url) as creation:creer.click()
                assert creation.value.status==200,creation.value.text()
                a=creation.value.json();ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
                with application['engine'].connect() as db:
                    rows=db.execute(text('SELECT compte,debit,credit FROM lignes_ecriture WHERE ecriture_id=:i ORDER BY id'),{'i':a['ecriture_id']}).all()
                    assert [(r.compte,r.debit,r.credit) for r in rows]==(
                        [('3491',Decimal('5934.07'),0),('6125',0,Decimal('5934.07'))] if type_=='cca' else
                        [('7124',Decimal('5934.07'),0),('4491',0,Decimal('5934.07'))])
                    cp=db.execute(text('SELECT date,exercice,est_validee FROM ecritures WHERE id=:i'),{'i':a['contrepassation_id']}).one()
                    assert (str(cp.date),cp.exercice,cp.est_validee)==('2026-01-01',2026,False)
                liasse=ok(api.get('/api/etats/liasse/2025'))
                assert Decimal(str(liasse['etats']['cpc']['resultat_net']))==(Decimal('-6065.93') if type_=='cca' else Decimal('6065.93'))
                assert liasse['etats']['bilan']['equilibre']
            assert photo(application,ids)==sources and not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()


def test_595_changement_saisie_invalide_resultat_et_pdf_perime(application):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api);browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page();page.set_default_timeout(20000);connexion(page,application['web_url'],email,password)
            region=ouvrir(page,application);resultat=remplir(region)
            region.get_by_label('Montant déjà comptabilisé (MAD)',exact=True).fill('10000')
            expect(resultat).to_have_count(0)
            resultat=remplir(region)
            ok(api.patch('/api/societe/moi',json={'raison_sociale':'Nouvelle identité fictive595'}))
            resultat.get_by_role('button',name='Télécharger la feuille PDF',exact=True).click()
            expect(region.get_by_role('alert')).to_contain_text('Recalculez')
            expect(resultat).to_have_count(0)
            resultat=remplir(region)
            ok(api.patch('/api/societe/moi',json={'raison_sociale':'Autre identité fictive595'}))
            resultat.get_by_role('button',name='Utiliser le montant et le libellé',exact=True).click()
            expect(region.get_by_role('alert')).to_contain_text('Recalculez avant de reprendre')
            expect(resultat).to_have_count(0)
            expect(page.get_by_label('Montant HT / comptable (MAD)',exact=True)).to_have_count(0)
        finally:browser.close()
