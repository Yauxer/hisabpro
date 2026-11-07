"""Chèque remis puis rejeté, virement de remplacement et lettrage : vraie UI/API/PG."""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok, photo


@pytest.mark.parametrize('largeur',[1365,390])
def test_cheque_impaye_remplacement_validation_et_lettrage(application,largeur):
    api,email,password=client(application)
    jour=date.today().isoformat()
    nom='Client chèque impayé fictif'
    try:
        tiers=ok(api.post('/api/tiers',json={'nom':nom,'type':'client'}),201)
        f=ok(api.post('/api/factures',json={'type':'vente','tiers':nom,'tiers_id':tiers['id'],
            'date':jour,'ras_taux':0,'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':1000,'tva':20}]}),201)
        ok(api.post(f"/api/factures/{f['id']}/valider"))
        ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,f['id']).societe_id
            initial=[e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
        assert len(initial)==1
        ok(api.post(f'/api/ecritures/{initial[0]}/valider'))
        original=photo(application,initial)
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000}); page.set_default_timeout(20000)
                page.on('dialog',lambda d:d.accept())
                erreurs,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(champ(modal,'Montant *')).to_have_value('1200.00')
                champ(modal,'Date *').fill(jour)
                champ(modal,'Mode','select').select_option('cheque')
                modal.get_by_placeholder('N° chèque, virement...').fill('CHEQUE-IMPAYE-FICTIF')
                with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as cheque:
                    modal.get_by_role('button',name='Enregistrer',exact=True).click()
                assert cheque.value.status==201,cheque.value.text()
                r=cheque.value.json(); rid=r['id']
                assert r['statut']=='portefeuille' and r['date_encaissement'] is None
                assert r['montant']==1200 and r['est_comptabilisee']
                modal.wait_for(state='hidden')
                s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
                assert (s['total_regle'],s['total_encaisse'],s['total_reglement_en_cours'])==(1200,0,1200)
                page.goto(application['web_url']+'/effets')
                champ(page,'Statut','select').select_option('tous')
                effect=page.locator('tbody tr').filter(has_text='CHEQUE-IMPAYE-FICTIF')
                pw.expect(effect).to_contain_text('En portefeuille')
                for action,titre,statut in [('remettre',"Remettre à l'encaissement",'encaissement'),('rejeter',"Déclarer l'impayé",'rejete')]:
                    effect.get_by_title("Remettre à l'encaissement" if action=='remettre' else 'Déclarer impayé',exact=True).click()
                    modal=page.get_by_role('dialog')
                    modal.locator('input[type="date"]').fill(jour)
                    if action=='rejeter': modal.get_by_placeholder('0.00',exact=True).fill('0')
                    with page.expect_response(lambda rr:rr.url.endswith(f'/api/reglements/{rid}/transition')) as transition:
                        modal.get_by_role('button',name=titre,exact=True).click()
                    assert transition.value.status==200,transition.value.text()
                    assert transition.value.json()['statut']==statut
                    assert transition.value.request.post_data_json=={'action':action,'frais':0,'date_effective':jour}
                    modal.wait_for(state='hidden')
                    pw.expect(effect).to_contain_text("À l'encaissement" if action=='remettre' else 'Rejeté / Impayé')
                    assert photo(application,initial)==original
                s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
                assert (s['total_regle'],s['total_encaisse'],s['solde_restant'],s['montant_ras_impute'])==(0,0,1200,0)
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(modal.get_by_text('REJETÉ — non compté',exact=True)).to_be_visible()
                pw.expect(champ(modal,'Montant *')).to_have_value('1200.00')
                champ(modal,'Date *').fill(jour)
                champ(modal,'Mode','select').select_option('virement')
                modal.get_by_placeholder('N° chèque, virement...').fill('VIREMENT-REMPLACEMENT-FICTIF')
                with page.expect_response(lambda rr:rr.url.endswith('/api/reglements') and rr.request.method=='POST') as remplacement:
                    modal.get_by_role('button',name='Enregistrer',exact=True).click()
                assert remplacement.value.status==201,remplacement.value.text()
                modal.wait_for(state='hidden')
                pw.expect(row).to_contain_text('Payée')
                s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
                assert (s['total_regle'],s['total_encaisse'],s['solde_restant'])==(1200,1200,0)
                with Session(application['engine']) as db:
                    entries=db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(entries)==5 and sum(len(e.lignes) for e in entries)==11
                    assert all(e.date==date.today() and e.date_piece==date.today() for e in entries)
                    debit=sum(Decimal(str(l.debit)) for e in entries for l in e.lignes)
                    credit=sum(Decimal(str(l.credit)) for e in entries for l in e.lignes)
                    assert debit==credit==Decimal('1200')*5
                    soldes={}
                    for e in entries:
                        for l in e.lignes: soldes[l.compte]=soldes.get(l.compte,Decimal(0))+Decimal(str(l.debit))-Decimal(str(l.credit))
                    assert {c:soldes[c] for c in ['5141','51111','51112','3421']}=={
                        '5141':Decimal('1200'),'51111':Decimal(0),'51112':Decimal(0),'3421':Decimal(0)}
                    collectives=[l for e in entries for l in e.lignes if l.compte=='3421']
                    assert len(collectives)==4 and all(l.tiers_id==tiers['id'] and l.compte_auxiliaire_snapshot for l in collectives)
                    assert sum(Decimal(str(l.debit)) for l in collectives)==sum(Decimal(str(l.credit)) for l in collectives)==Decimal('2400')
                page.goto(application['web_url']+'/journal')
                pw.expect(page.get_by_role('button',name='Valider',exact=True)).to_have_count(4)
                with page.expect_response(lambda rr:rr.url.endswith('/api/ecritures/valider-lot')) as validation:
                    page.get_by_role('button',name='Valider les brouillons',exact=True).click()
                assert validation.value.status==200 and validation.value.json()['nb_validees']==4
                with Session(application['engine']) as db:
                    ids=[e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
                    assert all(e.est_validee for e in db.query(models.Ecriture).filter_by(societe_id=sid))
                avant_lettrage=photo(application,ids)
                page.goto(application['web_url']+'/lettrage')
                champ(page,'Compte','select').select_option('3421')
                champ(page,'Tiers','select').select_option(label=nom)
                pw.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(4)
                for box in page.locator('tbody input[type="checkbox"]').all(): box.check()
                with page.expect_response(lambda rr:'/api/lettrage' in rr.url and rr.request.method=='POST') as lettrage:
                    page.get_by_role('button',name='Lettrer 4 lignes',exact=True).click()
                assert lettrage.value.status==200 and lettrage.value.json()['code']=='AAA'
                pw.expect(page.get_by_text('4 lettrée(s)',exact=True)).to_be_visible()
                assert photo(application,ids)==avant_lettrage
                assert not erreurs and not serveur,(erreurs,serveur)
            finally: browser.close()
        ok(api.post('/api/utilisateurs',json={'nom':'Lecteur impayés','email':'lecture-'+email,'mot_de_passe':password,'role':'lecture'}),201)
        lecteur=ok(api.post('/api/auth/login',json={'email':'lecture-'+email,'password':password}))
        headers={'Authorization':'Bearer '+lecteur['access_token']}
        assert api.post(f'/api/reglements/{rid}/transition',json={'action':'rejeter','frais':0,'date_effective':jour},headers=headers).status_code==403
        autre,_,_=client(application)
        try:
            assert autre.post(f'/api/reglements/{rid}/transition',json={'action':'rejeter','frais':0,'date_effective':jour}).status_code==404
        finally: autre.close()
        assert photo(application,ids)==avant_lettrage
    finally: api.close()
