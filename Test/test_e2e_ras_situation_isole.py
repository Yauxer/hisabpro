"""RAS estimée distincte d'une imputation historique : vrais Edge/API/PG nonce."""
from datetime import date
from decimal import Decimal
import math
import re
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ
from test_ras_lecture_conservation import client, lire, verifier_ras
from test_ras_taux_finis import facture


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def photo(application, ids):
    with application['engine'].connect() as db:
        return [(db.execute(text('SELECT row_to_json(t)::text FROM ecritures t WHERE id=:id'), {'id': eid}).scalar_one(),
                 db.execute(text('SELECT row_to_json(t)::text FROM lignes_ecriture t WHERE ecriture_id=:id ORDER BY id'), {'id': eid}).scalars().all())
                for eid in ids]


def preparer(application, sens, historique=False):
    api, email, password = client(application)
    nom = 'Tiers RAS '+sens+' fictif'
    t = ok(api.post('/api/tiers', json={'nom':nom,'type':'client' if sens=='vente' else 'fournisseur'}),201)
    f = ok(api.post('/api/factures', json=facture(type=sens, tiers=nom, tiers_id=t['id'],
        reference='FOURN-RAS-FICTIF' if sens=='achat' else None)),201)
    if historique:
        # Précondition legacy seulement sur brouillon fictif, avant validation.
        with Session(application['engine']) as db:
            db.get(models.Facture,f['id']).ras_comptabilisee=True
            db.commit()
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
    compte = '3421' if sens=='vente' else '4411'
    if historique:
        lignes = ([{'compte':'3453','debit':100},{'compte':compte,'credit':100,'tiers_id':t['id']}]
                  if sens=='vente' else [{'compte':compte,'debit':100,'tiers_id':t['id']},{'compte':'4457','credit':100}])
        ok(api.post('/api/ecritures',json={'date':date.today().isoformat(),'journal':'OD',
           'reference':'RAS-LEGACY-FICTIVE','libelle':'Retenue historique laboratoire','lignes':lignes}),201)
    with Session(application['engine']) as db:
        sid=db.get(models.Facture,f['id']).societe_id
        ids=[e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
    for eid in ids: ok(api.post(f'/api/ecritures/{eid}/valider'))
    return api,email,password,t,f,ids,sid


@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('largeur',[1365,390])
def test_estimation_ne_regle_pas_facture_et_paiement_net_laisse_cent(application,sens,largeur):
    api,email,password,t,f,ids,sid=preparer(application,sens)
    try:
        avant=photo(application,ids)
        s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert (s['montant_ras_estime'],s['montant_ras_impute'],s['montant_ras'],s['solde_restant'])==(100,0,0,1200)
        verifier_ras(lire(api,f['id']))  # Contrat documentaire 10 %, 100, net estimé 1100 conservé.
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000}); page.set_default_timeout(20000)
                erreurs,serveur=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text=t['nom'])
                row.get_by_title('Payer le fournisseur' if sens=='achat' else 'Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(modal.get_by_text('RAS estimée :',exact=False)).to_contain_text('100,00 MAD')
                pw.expect(modal.get_by_text('RAS historiquement comptabilisée',exact=False)).to_have_count(0)
                montant=champ(modal,'Montant *'); pw.expect(montant).to_have_value('1200.00')
                montant.fill('1100')
                modal.get_by_placeholder('N° chèque, virement...').fill('NET-SANS-RAS-FICTIF')
                with page.expect_response(lambda r:r.url.endswith('/api/reglements') and r.request.method=='POST') as paiement:
                    modal.get_by_role('button',name='Enregistrer',exact=True).click()
                assert paiement.value.status==201,paiement.value.text()
                modal.wait_for(state='hidden')
                pw.expect(row).to_contain_text('Part. payée')
                row.get_by_title('Payer le fournisseur' if sens=='achat' else 'Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(champ(modal,'Montant *')).to_have_value('100.00')
                pw.expect(modal.get_by_text('RAS estimée :',exact=False)).to_contain_text('100,00 MAD')
                modal.get_by_role('button',name='Annuler',exact=True).click()
                assert lire(api,f['id'])['statut']=='partiellement_payee'
                page.goto(application['web_url']+'/commercial')
                page.get_by_role('button',name='Vente' if sens=='vente' else 'Achat',exact=True).click()
                page.get_by_role('button',name='Factures',exact=True).click()
                pw.expect(page.locator('tbody tr').filter(has_text=t['nom'])).to_contain_text('Part. payée')
                assert not erreurs and not serveur,(erreurs,serveur)
            finally: browser.close()
        s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert (s['montant_ras_impute'],s['total_regle'],s['solde_restant'],s['est_solde'])==(0,1100,100,False)
        verifier_ras(lire(api,f['id']))
        assert photo(application,ids)==avant
        with Session(application['engine']) as db:
            ecritures=db.query(models.Ecriture).filter_by(societe_id=sid).all()
            assert len(ecritures)==2 and sum(len(e.lignes) for e in ecritures)==5
            assert not db.get(models.Facture,f['id']).ras_comptabilisee
            assert all(l.compte not in ('3453','4457') for e in ecritures for l in e.lignes)
            lignes=[l for e in ecritures for l in e.lignes]
            assert sum(Decimal(str(l.debit)) for l in lignes)==Decimal('2300')
            assert sum(Decimal(str(l.credit)) for l in lignes)==Decimal('2300')
    finally: api.close()


@pytest.mark.parametrize('sens',['vente','achat'])
def test_ras_historique_identifiee_sans_attestation_ni_reecriture(application,sens):
    api,email,password,t,f,ids,sid=preparer(application,sens,True)
    try:
        avant=photo(application,ids)
        s=ok(api.get(f"/api/factures/{f['id']}/reglements"))
        assert (s['montant_ras_estime'],s['montant_ras_impute'],s['ras_origine'],s['solde_restant'])==(100,100,'historique_comptabilisee',1100)
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(); page.set_default_timeout(20000)
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures')
                page.locator('tbody tr').filter(has_text=t['nom']).get_by_title('Payer le fournisseur' if sens=='achat' else 'Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(modal.get_by_text('RAS historiquement comptabilisée :',exact=False)).to_contain_text('ne constitue pas une attestation')
                pw.expect(champ(modal,'Montant *')).to_have_value('1100.00')
                modal.get_by_role('button',name='Annuler',exact=True).click()
            finally: browser.close()
        assert photo(application,ids)==avant
        with Session(application['engine']) as db:
            assert db.query(models.Reglement).filter_by(societe_id=sid).count()==0
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count()==2
    finally: api.close()


def test_solde_historique_inconnu_visible_et_reglement_impossible(application):
    api,email,password=client(application)
    try:
        # Préparation d'un historique fictif neuf, avant fixation de son état.
        with Session(application['engine']) as db:
            sid=ok(api.get('/api/societe/moi'))['id']
            f=models.Facture(societe_id=sid,numero='LEGACY-RAS-NAN-FICTIVE',type='vente',
                date=date.today(),date_echeance=date.today(),exercice=date.today().year,
                tiers='Tiers RAS inconnu fictif',est_validee=False,statut='en_attente',ras_taux=float('nan'))
            f.lignes=[models.LigneFacture(description='Service historique fictif',quantite=1,prix_unitaire=1000,tva=20)]
            db.add(f); db.flush(); f.est_validee=True; db.flush(); fid=f.id; db.commit()
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':390,'height':1000}); page.set_default_timeout(20000)
                mutations=[]
                page.on('request',lambda r:mutations.append(r.url) if r.method=='POST' and '/api/reglements' in r.url else None)
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/factures')
                row=page.locator('tbody tr').filter(has_text='Tiers RAS inconnu fictif')
                row.get_by_title('Encaisser le client',exact=True).click()
                modal=page.get_by_role('dialog')
                pw.expect(modal.get_by_role('alert').filter(has_text='historique invalide')).to_contain_text('historique invalide')
                pw.expect(modal.get_by_text('RAS estimée :',exact=False)).to_contain_text('À vérifier')
                pw.expect(modal.get_by_role('button',name=re.compile(r'Enregistrer$'))).to_be_disabled()
                pw.expect(champ(modal,'Montant *')).to_have_value('')
                assert mutations==[]
            finally: browser.close()
        with Session(application['engine']) as db:
            assert math.isnan(db.get(models.Facture,fid).ras_taux)
            assert db.query(models.Reglement).filter_by(societe_id=sid).count()==0
            assert db.query(models.Ecriture).filter_by(societe_id=sid).count()==0
    finally: api.close()
