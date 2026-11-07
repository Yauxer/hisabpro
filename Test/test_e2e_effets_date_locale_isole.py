"""Date d'échéance civile, réel Edge/API/PGnonce, horloge de navigateur fixée."""
from datetime import date,datetime,timedelta,time,timezone
import re
from playwright.sync_api import sync_playwright,expect
from test_e2e_runtime_session_isole import application,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_ventes_preparation_isole import facture
from test_e2e_administration_isole import connexion,observer
from test_e2e_facturation_isole import champ
from browser_support import chromium_executable


def test_effet_du_jour_disponible_avant_minuit_utc_et_demain_bloque(application):
    api,email,password=client(application)
    try:
        jour=date.today()
        for delta in [0,1]:
            f,_=facture(api,100,date_piece=jour.isoformat())
            ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
            ok(api.post('/api/reglements',json={'date':jour.isoformat(),'facture_id':f['id'],
                'tiers':f['tiers'],'montant':120,'mode':'effet','reference':f'DATE-LOCALE471-{delta}',
                'date_echeance':(jour+timedelta(days=delta)).isoformat()}),201)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(timezone_id='Europe/Paris',viewport={'width':390,'height':1000})
                page.set_default_timeout(15000)
                # Le calendrier local est déjà au jour J, l'UTC est encore J-1.
                page.clock.set_fixed_time(datetime.combine(jour-timedelta(days=1),time(23,30),tzinfo=timezone.utc))
                errors,server=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/effets');champ(page,'Statut','select').select_option('tous')
                rows=page.locator('tbody tr')
                expect(rows.filter(has_text='DATE-LOCALE471-0').get_by_title("Confirmer l'encaissement",exact=True)).to_be_enabled()
                futur=rows.filter(has_text='DATE-LOCALE471-1').get_by_title(re.compile('^Encaissable à partir du'))
                expect(futur).to_be_disabled()
                expect(futur).to_have_attribute('title','Encaissable à partir du '+(jour+timedelta(days=1)).strftime('%d/%m/%Y'))
                assert not errors,errors
                assert not server,server
            finally:browser.close()
    finally:api.close()
