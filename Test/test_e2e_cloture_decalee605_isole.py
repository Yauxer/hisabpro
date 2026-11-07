"""Clôture au30juin : référence2026, dates AN/CP au1juillet2025, Edge/PG natif."""
from contextlib import closing
from decimal import Decimal as D
import pytest
from playwright.sync_api import sync_playwright, expect
from sqlalchemy import text
from test_journal_cloture_concurrente_isole import (
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ajustements_inventaire_isole import exercice
from test_e2e_prorata_inventaire_isole import ecriture, photo
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_e2e_annee_connectee_isole import ORACLE as PROFIL, valider_brouillons_ui
from browser_support import chromium_executable


@pytest.mark.parametrize('type_,largeur',[('cca',390),('pca',1440)])
def test_605_cloture_decalee_an_contrepassation_et_fec(application,type_,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api,'2024-07-01','2025-06-30')
        ok(api.patch('/api/exercices/2026',json={'date_debut':'2025-07-01','date_fin':'2026-06-30'}))
        societe=ok(api.patch('/api/societe/moi',json={'forme_juridique':'SARL','regime_fiscal':'is',
            'exercice_debut':2020,'devise':'MAD','capital_social':20000}))
        sid=societe['id']
        ok(api.put('/api/fiscalite/is/2025/parametres',json=PROFIL['profil']['parametres_is']))
        ids=[ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAPITAL-FICTIF605')]
        lignes=[('6125','12000',0),('5141',0,'12000')] if type_=='cca' else [('5141','12000',0),('7124',0,'12000')]
        ids.append(ecriture(api,'2025-04-01',lignes,'BASE-FICTIVE605'))
        source=photo(application,ids)
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            page.on('dialog',lambda d:d.accept())
            erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/cloture')
            page.get_by_label('Exercice actif',exact=True).select_option('2025')
            region=page.get_by_role('region',name='Calcul documentaire CCA PCA',exact=True,include_hidden=True)
            expect(region).to_contain_text('2025-06-30')
            page.get_by_text('Calcul documentaire facultatif CCA / PCA',exact=True).click()
            region.get_by_label('Type de report',exact=True).select_option(type_)
            region.get_by_label('Référence du contrat ou de la pièce',exact=True).fill('CONTRAT-FICTIF605')
            region.get_by_label('Montant déjà comptabilisé (MAD)',exact=True).fill('12000')
            region.get_by_label('Base du montant',exact=True).select_option('autre')
            region.get_by_label('Début de la période',exact=True).fill('2025-04-01')
            region.get_by_label('Fin de la période',exact=True).fill('2025-09-30')
            region.get_by_role('button',name='Calculer en jours calendaires',exact=True).click()
            resultat=region.get_by_role('region',name='Résultat du calcul documentaire',exact=True)
            expect(resultat).to_contain_text('6.032,79')
            expect(resultat).to_contain_text('92 / 183 jours')
            resultat.get_by_role('button',name='Utiliser le montant et le libellé',exact=True).click()
            page.get_by_role('button',name='Vérifier l’écriture',exact=True).click()
            creer=page.get_by_role('button',name='Créer l’écriture',exact=True);expect(creer).to_be_enabled()
            with page.expect_response(lambda r:r.request.method=='POST' and '/ajustements?exercice=2025' in r.url) as rep:creer.click()
            assert rep.value.status==200,rep.value.text()
            a=rep.value.json()
            assert a['date']=='2025-06-30' and a['contrepassation_date']=='2025-07-01'
            valider_brouillons_ui(page,application,1)
            source_ad=photo(application,[a['ecriture_id']])
            page.goto(application['web_url']+'/cloture')
            bouton=page.get_by_role('button',name="Clôturer l'exercice 2025",exact=True);expect(bouton).to_be_enabled()
            with page.expect_response(lambda r:r.request.method=='POST' and '/cloturer?exercice=2025' in r.url) as rep:bouton.click()
            assert rep.value.status==200,rep.value.text()
            assert D(str(rep.value.json()['resultat_net']))==(D('-8967.21') if type_=='cca' else D('2967.21'))
            with application['engine'].connect() as db:
                an=db.execute(text('SELECT ecriture_an_id FROM clotures_exercice WHERE societe_id=:s AND exercice=2025'),{'s':sid}).scalar_one()
                for eid in (an,a['contrepassation_id']):
                    e=db.execute(text('SELECT date,exercice FROM ecritures WHERE id=:i'),{'i':eid}).one()
                    assert (str(e.date),e.exercice)==('2025-07-01',2026)
                soldes=dict(db.execute(text('SELECT compte,debit-credit FROM lignes_ecriture WHERE ecriture_id=:i'),{'i':an}).all())
                assert soldes==({'5141':D('8000'),'3491':D('6032.79'),'1199':D('8967.21'),'1111':D('-20000'),'4453':D('-3000')} if type_=='cca' else
                    {'5141':D('32000'),'1111':D('-20000'),'1191':D('-2967.21'),'4491':D('-6032.79'),'4453':D('-3000')})
                assert sum(soldes.values())==0
            suivi=ok(api.get('/api/cloture/contrepassations?exercice=2026'))
            assert suivi['total']==suivi['a_valider']==1
            assert suivi['items'][0]['source_date']=='2025-06-30' and suivi['items'][0]['date']=='2025-07-01'
            page.get_by_label('Exercice actif',exact=True).select_option('2026')
            valider_brouillons_ui(page,application,1)
            for annee in (2025,2026):
                assert ok(api.get(f'/api/fec/apercu?exercice={annee}'))['conforme_export']
                fec=api.get(f'/api/fec/export?exercice={annee}');assert fec.status_code==200,fec.text
                if annee==2026:assert b'20250701' in fec.content
                (tmp_path/f'FEC605_{type_}_{annee}.txt').write_bytes(fec.content)
            etats=ok(api.get('/api/etats/liasse/2026'))['etats']
            assert etats['bilan']['equilibre']
            assert D(str(etats['cpc']['resultat_net']))==(D('-6032.79') if type_=='cca' else D('6032.79'))
            assert photo(application,ids)==source and photo(application,[a['ecriture_id']])==source_ad
            page.goto(application['web_url']+'/cloture')
            suivi_ui=page.get_by_role('region',name='Contrepassations d’ouverture',exact=True)
            expect(suivi_ui).to_contain_text('1 liée(s) · 0 à valider · 1 validée(s)')
            expect(suivi_ui).to_contain_text('2025-07-01')
            suivi_ui.scroll_into_view_if_needed();page.screenshot(path=str(tmp_path/f'decale605_{type_}_{largeur}.png'))
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
