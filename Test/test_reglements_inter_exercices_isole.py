"""Un paiement N de facture N-1 reste visible dans le bon cycle, sans mutation."""
from datetime import date
from decimal import Decimal
import uuid
import pytest
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_lecture_reglements_historiques import photo
from test_e2e_administration_isole import connexion, observer
from browser_support import chromium_executable


def preparer(application, sens, complement=60):
    api,email,password=client(application)
    annee=date.today().year
    exercices=api.get('/api/exercices').json()
    if not any(x['annee']==annee-1 for x in exercices):
        r=api.post('/api/exercices',json={'annee':annee-1,'date_debut':f'{annee-1}-01-01','date_fin':f'{annee-1}-12-31'})
        assert r.status_code==201,r.text
    nom='Tiers inter-exercices fictif '+uuid.uuid4().hex[:8]
    r=api.post('/api/tiers',json={'nom':nom,'type':'client' if sens=='vente' else 'fournisseur'})
    assert r.status_code==201,r.text
    r=api.post('/api/factures',json={'type':sens,'date':f'{annee-1}-12-15','tiers':nom,'tiers_id':r.json()['id'],
        'reference':'FACT-INTER-FICTIVE','lignes':[{'description':'Prestation fictive','quantite':1,'prix_unitaire':100,'tva':20}]})
    assert r.status_code==201,r.text
    fid=r.json()['id']
    r=api.post(f'/api/factures/{fid}/valider',json={})
    assert r.status_code==200,r.text
    numero=r.json()['numero']
    assert isinstance(numero,str) and numero
    r=api.post(f'/api/factures/{fid}/comptabiliser',json={})
    assert r.status_code==200,r.text
    rows=[]
    for jour,montant,reference in [(f'{annee-1}-12-20',60,'VIR-INTER-PREMIER'),(f'{annee}-01-10',complement,'VIR-INTER-SOLDE')]:
        r=api.post('/api/reglements',json={'facture_id':fid,'date':jour,'tiers':nom,'montant':montant,
            'mode':'virement','reference':reference,'comptabiliser':True})
        assert r.status_code==201,r.text
        rows.append(r.json())
    with Session(application['engine']) as db:
        sid=db.get(models.Facture,fid).societe_id
        eids=[e.id for e in db.query(models.Ecriture).filter_by(societe_id=sid)]
    for eid in eids:
        r=api.post(f'/api/ecritures/{eid}/valider',json={})
        assert r.status_code==200,r.text
    return api,email,password,fid,numero,rows,annee


@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('largeur',[1365,390])
def test_reglement_n_facture_n_moins_un_visible_recharge_et_bon_sens(application,sens,largeur):
    api,email,password,fid,numero,rows,annee=preparer(application,sens)
    try:
        r=api.get('/api/reglements',params={'exercice':annee})
        assert r.status_code==200 and [x['id'] for x in r.json()]==[rows[1]['id']]
        assert api.get('/api/factures',params={'exercice':annee}).json()==[]
        situation=api.get(f'/api/factures/{fid}/reglements').json()
        assert situation['total_regle']==120 and situation['solde_restant']==0
        avant=photo(application)
        from playwright.sync_api import sync_playwright,expect
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000})
                page.set_default_timeout(15000)
                erreurs,serveurs=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/commercial')
                for tour in range(2):
                    page.get_by_role('button',name='Vente' if sens=='vente' else 'Achat',exact=True).click()
                    page.get_by_role('button',name='Règlements',exact=True).click()
                    ligne=page.locator('tbody tr')
                    expect(ligne).to_have_count(1)
                    expect(ligne).to_contain_text(numero)
                    expect(ligne).to_contain_text('Soldée')
                    expect(ligne).to_contain_text('VIR-INTER-SOLDE')
                    page.get_by_role('button',name='Achat' if sens=='vente' else 'Vente',exact=True).click()
                    page.get_by_role('button',name='Règlements',exact=True).click()
                    expect(page.locator('tbody tr')).to_have_count(0)
                    page.reload()
                assert not erreurs and not serveurs,(erreurs,serveurs)
            finally:
                browser.close()
        assert photo(application)==avant
    finally:
        api.close()


@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('complement',[20,60])
def test_projection_lien_native_hors_annee_et_conservation(application,sens,complement):
    api,email,password,fid,numero,rows,annee=preparer(application,sens,complement)
    autre=client(application)[0]
    try:
        avant=photo(application)
        for exercice,rid in [(annee-1,rows[0]['id']),(annee,rows[1]['id'])]:
            r=api.get('/api/reglements',params={'exercice':exercice})
            assert r.status_code==200,r.text
            row=next(x for x in r.json() if x['id']==rid)
            assert row['facture_type']==sens and row['facture_numero']==numero
            assert row['facture_exercice']==annee-1
            assert row['facture_statut']==('payee' if complement==60 else 'partiellement_payee')
            assert row['facture_montants_valides'] is True
            assert autre.get('/api/reglements',params={'exercice':exercice}).json()==[]
        assert Decimal(str(api.get(f'/api/factures/{fid}/reglements').json()['solde_restant']))==Decimal(60-complement)
        assert photo(application)==avant
    finally:
        api.close();autre.close()


@pytest.mark.parametrize('lien',['autre_societe','absent'])
def test_projection_historique_ne_divulgue_pas_piece_autre_societe(application,lien):
    api,email,password,fid,numero,rows,annee=preparer(application,'vente')
    autre=client(application)[0]
    try:
        from test_articles_alertes_stock_historique_postgres import cible
        cible(application)
        sid=autre.get('/api/societe/moi').json()['id']
        # Ancien règlement non comptabilisé fictif ; aucune écriture définitive altérée.
        with Session(application['engine']) as db:
            legacy=models.Reglement(societe_id=sid,facture_id=fid if lien=='autre_societe' else None,
                date=date(annee,1,11),tiers='Historique fictif local',montant=1,mode='virement',
                statut='complet',est_comptabilisee=False)
            db.add(legacy);db.commit();rid=legacy.id
        avant=photo(application)
        r=autre.get('/api/reglements',params={'exercice':annee})
        assert r.status_code==200,r.text
        assert len(r.json())==1 and r.json()[0]['id']==rid
        assert all(r.json()[0][champ] is None for champ in (
            'facture_type','facture_numero','facture_exercice','facture_statut','facture_montants_valides'))
        assert numero not in r.text
        assert photo(application)==avant
    finally:
        api.close();autre.close()
