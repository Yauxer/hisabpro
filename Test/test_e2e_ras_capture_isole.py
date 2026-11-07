"""Capture RAS explicite : vrais Edge, API et PostgreSQL nonce, aucun taux créé."""
from datetime import date
from decimal import Decimal
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ
from test_e2e_facturation_isole import application as application_absente
from test_ras_lecture_conservation import client
from test_ras_capture_reglement_postgres import appliquer, preparer, paiement, ok
from test_e2e_ras_situation_isole import photo


def ouvrir(page, application, nature):
    page.goto(application['web_url']+'/commercial')
    page.get_by_role('button',name='Vente' if nature=='vente' else 'Achat',exact=True).click()
    page.get_by_role('button',name='Règlements',exact=True).click()


@pytest.mark.parametrize('largeur',[1365,390])
@pytest.mark.parametrize('nature',['vente','achat'])
def test_captures_declarees_reglements_od_et_annulation_tracees(application,largeur,nature):
    appliquer(application)
    api,email,password=client(application)
    try:
        f=preparer(api,nature)
        ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        with Session(application['engine']) as db:
            sid=db.get(models.Facture,f['id']).societe_id
            initial=[e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
        for eid in initial: ok(api.post(f'/api/ecritures/{eid}/valider'))
        original=photo(application,initial)
        compte='3453' if nature=='vente' else '4457'
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000})
                page.set_default_timeout(20000)
                page.on('dialog',lambda d:d.accept())
                erreurs,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                rids=[]; captures=[]
                for montant,ras,solde in [(400,30,770),(700,70,0)]:
                    r=paiement(api,f,montant); rids.append(r['id'])
                    ouvrir(page,application,nature)
                    row=page.locator('tbody tr').filter(has_text=f'{montant},00 MAD')
                    row.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
                    modal=page.get_by_role('dialog')
                    pw.expect(modal.get_by_label('Montant RAS *',exact=True)).to_have_value('')
                    pw.expect(modal.get_by_label('Compte destination RAS *',exact=True)).to_have_value('')
                    pw.expect(modal.get_by_label('Référence RAS *',exact=True)).to_have_value('')
                    pw.expect(modal.get_by_label("Date de l'opération RAS *",exact=True)).to_have_value(date.today().isoformat())
                    modal.get_by_label('Montant RAS *',exact=True).fill(str(ras))
                    modal.get_by_label('Référence RAS *',exact=True).fill('RAS-EXPLICITE-'+str(ras))
                    modal.get_by_label('Compte destination RAS *',exact=True).select_option(compte)
                    with page.expect_response(lambda rr:rr.url.endswith(f"/api/reglements/{r['id']}/ras") and rr.request.method=='POST') as response:
                        modal.get_by_role('button',name='Préparer la RAS déclarée',exact=True).click()
                    assert response.value.status==200,response.value.text()
                    captures.append(response.value.json())
                    modal.wait_for(state='hidden')
                    pw.expect(row).to_contain_text('Soldée' if solde==0 else 'Partiel')
                    row.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
                    modal=page.get_by_role('dialog')
                    pw.expect(modal.get_by_text('À contrôler et à valider',exact=False)).to_be_visible()
                    pw.expect(modal.get_by_role('button',name='Préparer la RAS déclarée',exact=True)).to_have_count(0)
                    modal.get_by_text('Fermer',exact=True).click()
                    s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
                    assert s['solde_restant']==solde and s['ras_origine']=='capture_reglement'
                    if solde:
                        page.goto(application['web_url']+'/factures')
                        facture_row=page.locator('tbody tr').filter(has_text=f['tiers'])
                        facture_row.get_by_title('Encaisser le client' if nature=='vente' else 'Payer le fournisseur',exact=True).click()
                        detail=page.get_by_role('dialog')
                        pw.expect(detail.get_by_text('RAS déclarée sur règlement :',exact=False)).to_contain_text('30,00 MAD')
                        pw.expect(detail.get_by_text('RAS historiquement comptabilisée :',exact=False)).to_have_count(0)
                        detail.get_by_role('button',name='Annuler',exact=True).click()
                with Session(application['engine']) as db:
                    entries=db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(entries)==5 and sum(len(e.lignes) for e in entries)==11
                    expected=sum(map(Decimal,['1200','400','30','700','70']))
                    assert sum(Decimal(str(l.debit)) for e in entries for l in e.lignes)==expected
                    assert sum(Decimal(str(l.credit)) for e in entries for l in e.lignes)==expected
                    assert all(not db.get(models.Ecriture,c['ecriture_id']).est_validee for c in captures)
                assert photo(application,initial)==original
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
                champ(page,'Compte','select').select_option('3421' if nature=='vente' else '4411')
                champ(page,'Tiers','select').select_option(label=f['tiers'])
                pw.expect(page.locator('tbody input[type="checkbox"]')).to_have_count(5)
                for box in page.locator('tbody input[type="checkbox"]').all(): box.check()
                with page.expect_response(lambda rr:'/api/lettrage' in rr.url and rr.request.method=='POST') as lettrage:
                    page.get_by_role('button',name='Lettrer 5 lignes',exact=True).click()
                assert lettrage.value.status==200 and lettrage.value.json()['code']=='AAA'
                pw.expect(page.get_by_text('5 lettrée(s)',exact=True)).to_be_visible()
                # Délettrage explicite préalable à l'annulation, aucune écriture réécrite.
                with page.expect_response(lambda rr:'/api/lettrage/comptable/delettrer/' in rr.url and rr.request.method=='POST') as delettrage:
                    page.get_by_title('Délettrer le code AAA',exact=True).first.click()
                assert delettrage.value.status==200,delettrage.value.text()
                assert photo(application,ids)==avant_lettrage
                # Annulation réelle du second cash : la RAS correspondante est contrepassée aussi.
                ouvrir(page,application,nature)
                row=page.locator('tbody tr').filter(has_text='700,00 MAD')
                with page.expect_response(lambda rr:rr.url.endswith(f'/api/reglements/{rids[1]}/annuler')) as annulation:
                    row.get_by_title('Annuler par contrepassation',exact=True).click()
                    page.get_by_role('dialog',name='Annuler le règlement',exact=True).get_by_role('button',name='Confirmer l’annulation',exact=True).click()
                assert annulation.value.status==200,annulation.value.text()
                pw.expect(row).to_contain_text('annule')
                row.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(modal.get_by_text('Annulée par contrepassation',exact=False)).to_be_visible()
                assert ok(api.get(f"/api/factures/{f['id']}/reglements"))['solde_restant']==770
                assert photo(application,initial)==original
                assert photo(application,ids)==avant_lettrage
                with Session(application['engine']) as db:
                    finales=db.query(models.Ecriture).filter_by(societe_id=sid).all()
                    assert len(finales)==7 and sum(len(e.lignes) for e in finales)==15
                    attendu=expected+Decimal('700')+Decimal('70')
                    assert sum(Decimal(str(l.debit)) for e in finales for l in e.lignes)==attendu
                    assert sum(Decimal(str(l.credit)) for e in finales for l in e.lignes)==attendu
                assert not erreurs and not serveur,(erreurs,serveur)
            finally: browser.close()
    finally: api.close()


def test_capture_absente_migration_affichee_sans_post_ni_ddl(application_absente):
    # Fixture distincte : le banc module des quatre cas précédents a reçu 083.
    application=application_absente
    api,email,password=client(application)
    try:
        with application['engine'].connect() as db:
            assert db.execute(text("SELECT to_regclass('public.ras_reglement_captures')")).scalar() is None
        f=preparer(api,'vente'); r=paiement(api,f,400)
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':390,'height':1000}); page.set_default_timeout(20000)
                erreurs,serveur=observer(page,application['api_url'])
                posts=[]
                page.on('request',lambda q:posts.append(q.url) if q.method=='POST' and q.url.endswith('/ras') else None)
                connexion(page,application['web_url'],email,password)
                try:
                    ouvrir(page,application,'vente')
                except Exception as e:
                    raise AssertionError((page.url,page.locator('body').inner_text()[:2500],erreurs,serveur)) from e
                page.get_by_title('Consulter ou déclarer la RAS',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(modal.get_by_role('alert')).to_contain_text('083_ras_reglements.sql')
                pw.expect(modal.get_by_role('button',name='Préparer la RAS déclarée',exact=True)).to_have_count(0)
                assert posts==[]
                assert not erreurs and not serveur,(erreurs,serveur)
            finally: browser.close()
        with application['engine'].connect() as db:
            assert db.execute(text("SELECT to_regclass('public.ras_reglement_captures')")).scalar() is None
    finally: api.close()
