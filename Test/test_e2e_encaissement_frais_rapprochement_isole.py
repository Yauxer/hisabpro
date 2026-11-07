"""120 brut = 109.99 banque +10.01 frais ; Edge/API/PGnonce, pointage et lettrage."""
from datetime import date
from decimal import Decimal
import csv,io
import pytest
from sqlalchemy.orm import Session
from playwright.sync_api import sync_playwright,expect
import models
from browser_support import chromium_executable
from test_e2e_facturation_isole import application,champ
from test_e2e_administration_isole import connexion,observer
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok,photo
from test_rapprochement_ventilation_isole import migration,situation


@pytest.mark.parametrize('mode,largeur',[('cheque',1365),('effet',390)])
def test_encaissement_frais_validation_proposition_et_lettrage(application,migration,mode,largeur,annee=None,controle_apres=None):
    api,email,password=client(application)
    historique=annee is not None;annee=annee or date.today().year
    jour=f'{annee}-06-15' if historique else date.today().isoformat()
    nom='Client encaissement fictif';ref='ENCAISSE-FRAIS-FICTIF'
    try:
        if historique:
            ok(api.patch('/api/societe/moi',json={'forme_juridique':'SARL','regime_fiscal':'is',
                'regime_tva':'encaissement','periodicite_tva':'mensuelle','devise':'MAD','exercice_debut':2020}))
            if annee not in {e['annee'] for e in ok(api.get('/api/exercices'))}:
                ok(api.post('/api/exercices',json={'annee':annee,'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}),201)
        tiers=ok(api.post('/api/tiers',json={'nom':nom,'type':'client'}),201)
        f=ok(api.post('/api/factures',json={'type':'vente','tiers':nom,'tiers_id':tiers['id'],
            'date':jour,'ras_taux':0,'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':100,'tva':20}]}),201)
        ok(api.post(f"/api/factures/{f['id']}/valider"));ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,f['id']).societe_id
            initial=[e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
        assert len(initial)==1
        ok(api.post(f'/api/ecritures/{initial[0]}/valider'))
        original=photo(application,initial)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                page.on('dialog',lambda d:d.accept());errors,server=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                if historique:
                    page.locator('select').filter(has=page.locator(f'option[value="{annee}"]')).first.select_option(str(annee))
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                expect(champ(modal,'Montant *')).to_have_value('120.00')
                champ(modal,'Date *').fill(jour);champ(modal,'Mode','select').select_option(mode)
                modal.get_by_placeholder('N° chèque, virement...').fill(ref)
                if mode=='effet':
                    modal.locator('input[type=date]').last.fill(jour)
                with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as receipt:
                    modal.get_by_role('button',name='Enregistrer',exact=True).click()
                assert receipt.value.status==201,receipt.value.text()
                reg=receipt.value.json();rid=reg['id'];assert reg['statut']=='portefeuille'
                modal.wait_for(state='hidden')
                page.goto(application['web_url']+'/effets');champ(page,'Statut','select').select_option('tous')
                effect=page.locator('tbody tr').filter(has_text=ref)
                for action,title,button in [('remettre',"Remettre à l'encaissement","Remettre à l'encaissement"),
                                          ('encaisser',"Confirmer l'encaissement","Confirmer l'encaissement")]:
                    effect.get_by_title(title,exact=True).click();modal=page.get_by_role('dialog')
                    modal.locator('input[type=date]').fill(jour)
                    if action=='encaisser':modal.get_by_placeholder('0.00',exact=True).fill('10.01')
                    with page.expect_response(lambda r:r.url.endswith(f'/api/reglements/{rid}/transition')) as transition:
                        modal.get_by_role('button',name=button,exact=True).click()
                    assert transition.value.status==200,transition.value.text()
                    assert transition.value.request.post_data_json=={'action':action,'frais':10.01 if action=='encaisser' else 0,'date_effective':jour}
                    modal.wait_for(state='hidden');assert photo(application,initial)==original
                expect(effect).to_contain_text('Encaissé')
                totals=ok(api.get(f"/api/factures/{f['id']}/reglements"))
                assert (totals['total_regle'],totals['total_encaisse'],totals['solde_restant'])==(120,120,0)
                # Oracle indépendant : quatre pièces, dix lignes, 480 débit/crédit.
                with Session(application['engine']) as db:
                    entries=db.query(models.Ecriture).filter_by(societe_id=sid).all();ids=[e.id for e in entries]
                    assert len(entries)==4 and sum(len(e.lignes) for e in entries)==10
                    assert sum(l.debit for e in entries for l in e.lignes)==sum(l.credit for e in entries for l in e.lignes)==Decimal(480)
                    soldes={}
                    for e in entries:
                        for l in e.lignes:soldes[l.compte]=soldes.get(l.compte,Decimal(0))+l.debit-l.credit
                    attente=['51111','51112'] if mode=='cheque' else ['3425','51132']
                    assert all(soldes[c]==0 for c in attente+['3421'])
                    assert soldes['5141']==Decimal('109.99') and soldes['61472']==Decimal('10.01')
                page.goto(application['web_url']+'/journal')
                expect(page.get_by_role('button',name='Valider',exact=True)).to_have_count(3)
                with page.expect_response(lambda r:r.url.endswith('/api/ecritures/valider-lot')) as validation:
                    page.get_by_role('button',name='Valider les brouillons',exact=True).click()
                assert validation.value.status==200 and validation.value.json()['nb_validees']==3
                avant=photo(application,ids)
                ok(api.post('/api/rapprochement',json={'date':jour,'compte':'5141','libelle':ref,'montant':109.99,'sens':'credit'}),201)
                page.goto(application['web_url']+'/rapprochement')
                page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                modal=page.get_by_role('dialog',name='Propositions de rapprochement')
                expect(modal.locator('input[type=checkbox]')).to_have_count(1)
                with page.expect_response(lambda r:r.url.endswith('/5141/rapprocher-propositions')) as pointage:
                    modal.get_by_role('button',name='Rapprocher la sélection',exact=True).click()
                assert pointage.value.status==200,pointage.value.text()
                params={'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}
                banque=ok(api.get('/api/rapprochement/5141/situation',params=params))
                assert sum(l['rapprochee'] for l in banque['ecritures'])==1
                assert all(l['rapprochee'] for l in banque['lignes_releve'])
                assert photo(application,ids)==avant
                page.goto(application['web_url']+'/lettrage')
                champ(page,'Compte','select').select_option('3421');champ(page,'Tiers','select').select_option(label=nom)
                expect(page.locator('tbody input[type=checkbox]')).to_have_count(2)
                for box in page.locator('tbody input[type=checkbox]').all():box.check()
                with page.expect_response(lambda r:'/api/lettrage' in r.url and r.request.method=='POST') as lettre:
                    page.get_by_role('button',name='Lettrer 2 lignes',exact=True).click()
                assert lettre.value.status==200 and lettre.value.json()['code']=='AAA'
                expect(page.get_by_text('2 lettrée(s)',exact=True)).to_be_visible()
                assert photo(application,ids)==avant
                page.reload();expect(page.get_by_text('2 lettrée(s)',exact=True)).to_be_visible()
                controle=ok(api.get(f'/api/fec/apercu?exercice={annee}'))
                assert controle['conforme_export'],controle
                export=api.get(f'/api/fec/export?exercice={annee}')
                assert export.status_code==200,export.text
                lignes=list(csv.DictReader(io.StringIO(export.content.decode('utf-8-sig')),delimiter='\t'))
                assert len(lignes)==10,lignes
                assert sum(Decimal(l['Montant_Debit'].replace(',','.')) for l in lignes)==sum(Decimal(l['Montant_Credit'].replace(',','.')) for l in lignes)==480
                refus=api.post(f'/api/reglements/{rid}/annuler',json={'motif':'Essai négatif fictif après encaissement'})
                assert refus.status_code==409,refus.text
                assert photo(application,ids)==avant
                if controle_apres:controle_apres(api,page,application,sid,ids,avant)
                assert not errors and not server,(errors,server)
            finally:browser.close()
    finally:api.close()


@pytest.mark.parametrize('mode,largeur',[('cheque',1365),('effet',390)])
def test_annee_frais_2025_cloture_an2026_pointage_archive_et_fec(application,migration,mode,largeur):
    def cloturer(api,page,app,sid,ids,avant):
        etat=ok(api.get('/api/cloture/etat?exercice=2025'))
        assert Decimal(str(etat['resultat_net']))==Decimal('89.99'),etat
        assert Decimal(str(etat['fiscalite_is']['a_comptabiliser']))==3000,etat
        page.goto(app['web_url']+'/cloture')
        bouton=page.get_by_role('button',name="Clôturer l'exercice 2025",exact=True)
        expect(bouton).to_be_enabled()
        with page.expect_response(lambda r:'/api/cloture/cloturer?exercice=2025' in r.url) as fermeture:
            bouton.click()
        assert fermeture.value.status==200,fermeture.value.text()
        assert Decimal(str(fermeture.value.json()['resultat_net']))==Decimal('-2910.01')
        assert fermeture.value.json()['a_nouveaux_sur']==2026
        assert photo(app,ids)==avant
        with Session(app['engine']) as db:
            ex=db.query(models.ExerciceComptable).filter_by(societe_id=sid,annee=2025).one()
            assert ex.statut=='cloture' and all(p.statut=='fermee' for p in ex.periodes)
            trace=db.query(models.ClotureExercice).filter_by(societe_id=sid,exercice=2025).one()
            an=db.get(models.Ecriture,trace.ecriture_an_id)
            assert an.est_validee and an.exercice==2026
            soldes={l.compte:l.debit-l.credit for l in an.lignes}
            assert soldes=={'5141':Decimal('109.99'),'1199':Decimal('2910.01'),
                '4455':Decimal('-20'),'4453':Decimal('-3000')},soldes
            assert sum(l.debit for l in an.lignes)==sum(l.credit for l in an.lignes)==3020
        for annee in [2025,2026]:
            assert ok(api.get(f'/api/fec/apercu?exercice={annee}'))['conforme_export']
            export=api.get(f'/api/fec/export?exercice={annee}');assert export.status_code==200,export.text
            lignes=list(csv.DictReader(io.StringIO(export.content.decode('utf-8-sig')),delimiter='\t'))
            assert sum(Decimal(l['Montant_Debit'].replace(',','.')) for l in lignes)==sum(Decimal(l['Montant_Credit'].replace(',','.')) for l in lignes)
            if annee==2026:assert len(lignes)==4
        params={'date_debut':'2025-01-01','date_fin':'2025-12-31'}
        banque=ok(api.get('/api/rapprochement/5141/situation',params=params))
        assert banque['lecture_seule'] and len(banque['lignes_releve'])==1
        rid=banque['lignes_releve'][0]['id'];assert banque['lignes_releve'][0]['rapprochee']
        assert api.post(f'/api/rapprochement/{rid}/derapprocher',json={}).status_code==409
        page.goto(app['web_url']+'/rapprochement')
        expect(page.get_by_role('button',name='Proposer les rapprochements',exact=True)).to_be_disabled()
        expect(page.get_by_text('Rapprochée',exact=True)).to_have_count(1)
        assert photo(app,ids)==avant
    test_encaissement_frais_validation_proposition_et_lettrage(application,migration,mode,largeur,annee=2025,controle_apres=cloturer)
