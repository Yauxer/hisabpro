"""Pilotage et balances âgées : inconnus visibles, vrais exports, PG nonce gardé."""
from datetime import date
import csv
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from openpyxl import load_workbook
from pypdf import PdfReader
import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client


def ok(r,status=200):
    assert r.status_code==status,r.text
    return r.json()


def photographie(application):
    with application['engine'].connect() as db:
        return {table:db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
                for table in ('factures','lignes_facture','ecritures','lignes_ecriture','reglements')}


def telecharger(page,format,tmp_path,nom):
    with page.expect_download() as sortie:
        page.get_by_role('button',name='Exporter '+format,exact=True).click()
    doc=sortie.value; chemin=tmp_path/(nom+{'CSV':'.csv','Excel':'.xlsx','PDF':'.pdf'}[format])
    doc.save_as(chemin)
    assert chemin.stat().st_size>50
    return chemin


@pytest.mark.parametrize('largeur',[1365,390])
@pytest.mark.parametrize('inconnu',[False,True])
def test_ras_indeterminate_pilotage_agee_et_exports_reels(application,tmp_path,largeur,inconnu):
    api,email,password=client(application)
    try:
        sid=ok(api.get('/api/societe/moi'))['id']; annee=date.today().year
        noms,refs={},{}
        for sens,prix in [('vente',1000),('achat',500)]:
            nom='Tiers connu '+sens+' fictif'; noms[sens]=nom
            tiers=ok(api.post('/api/tiers',json={'nom':nom,'type':'client' if sens=='vente' else 'fournisseur'}),201)
            f=ok(api.post('/api/factures',json={'type':sens,'date':f'{annee}-03-15','date_echeance':f'{annee}-03-20',
                'tiers':nom,'tiers_id':tiers['id'],'reference':'FACT-KNOWN-'+sens,'ras_taux':0,
                'lignes':[{'description':'Service fictif','quantite':1,'prix_unitaire':prix,'tva':20}]}),201)
            ok(api.post(f"/api/factures/{f['id']}/valider"))
            if inconnu:
                refs[sens]='LEG-RAS-'+sens+'-'+uuid.uuid4().hex[:6]
                with Session(application['engine']) as db:
                    # Nouvel historique fictif préparé avant fixation de son état.
                    hist=models.Facture(societe_id=sid,numero=refs[sens],reference=refs[sens],type=sens,date=date(annee,3,15),
                        date_echeance=date(annee,3,20),exercice=annee,tiers=nom,tiers_id=tiers['id'],
                        statut='en_attente',est_validee=False,ras_taux=float('nan'))
                    hist.lignes=[models.LigneFacture(description='Service historique fictif',quantite=1,prix_unitaire=1000,tva=20)]
                    db.add(hist); db.flush(); hist.est_validee=True; db.flush(); db.commit()
        data=ok(api.get('/api/dashboard/commercial',params={'exercice':annee}))
        resume=data['resume']
        assert resume['ca_ht']==(2000 if inconnu else 1000)
        assert resume['achats_ht']==(1500 if inconnu else 500)
        assert resume['encours_clients']==(None if inconnu else 1200)
        assert resume['encours_fournisseurs']==(None if inconnu else 600)
        assert resume['calcul_incomplet_clients'] is inconnu
        assert resume['calcul_incomplet_fournisseurs'] is inconnu
        avant=photographie(application)
        pw=pytest.importorskip('playwright.sync_api')
        with pw.sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
                page.set_default_timeout(20000); erreurs,serveur=observer(page,application['api_url'])
                mutations=[]
                page.on('request',lambda r:mutations.append((r.method,r.url)) if r.method in ('POST','PATCH','DELETE') and any(t in r.url for t in ('/api/factures','/api/reglements','/api/ecritures')) else None)
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/dashboard')
                pilotage=page.locator('section').filter(has=page.get_by_role('heading',name='Pilotage commercial',exact=True))
                client_kpi=pilotage.get_by_role('button').filter(has_text='Encours clients')
                fournisseur_kpi=pilotage.get_by_role('button').filter(has_text='Encours fournisseurs')
                taux=pilotage.get_by_role('button').filter(has_text='Taux de recouvrement')
                if inconnu:
                    pw.expect(client_kpi).to_contain_text('À vérifier')
                    pw.expect(fournisseur_kpi).to_contain_text('À vérifier')
                    pw.expect(taux).to_contain_text('À vérifier')
                    pw.expect(client_kpi).not_to_contain_text('0,00')
                    pw.expect(taux).not_to_contain_text('0.0')
                    for ref in refs.values(): pw.expect(pilotage.get_by_role('alert')).to_contain_text(ref)
                else:
                    pw.expect(client_kpi).to_contain_text('1.200,00')
                    pw.expect(fournisseur_kpi).to_contain_text('600,00')
                    pw.expect(taux).to_contain_text('0.0')
                    pw.expect(pilotage.get_by_role('alert')).to_have_count(0)
                page.goto(application['web_url']+'/balances')
                page.get_by_role('button',name='Balance Âgée',exact=False).click()
                for sens,montant in [('vente',1200),('achat',600)]:
                    if sens=='achat': page.get_by_role('button',name='Fournisseurs (4411)',exact=True).click()
                    rows=page.locator('tbody tr'); pw.expect(rows).to_have_count(2 if inconnu else 1)
                    total=page.locator('tfoot tr').filter(has_text='TOTAL GÉNÉRAL')
                    if inconnu:
                        row=rows.filter(has_text=refs[sens])
                        pw.expect(row).to_contain_text('historique invalide')
                        pw.expect(row.locator('td').nth(4)).to_have_text('À vérifier')
                        pw.expect(total).to_contain_text('À vérifier')
                        pw.expect(page.get_by_role('alert')).to_contain_text('incomplète')
                    else:
                        pw.expect(total).to_contain_text('1.200,00' if sens=='vente' else '600,00')
                    csv_path=telecharger(page,'CSV',tmp_path,sens+'-agee')
                    with csv_path.open(encoding='utf-8-sig',newline='') as fichier: csv_rows=list(csv.reader(fichier,delimiter=';'))
                    assert 'Reste dû' in csv_rows[0]
                    xlsx=load_workbook(telecharger(page,'Excel',tmp_path,sens+'-agee'))
                    valeurs=list(xlsx['Balance'].values)
                    ligne_total=next(r for r in valeurs if r[0]=='TOTAL GÉNÉRAL')
                    if inconnu:
                        unknown_csv=next(r for r in csv_rows[1:] if r[1]==refs[sens])
                        assert unknown_csv[4:10]==['']*6
                        assert 'historique invalide' in unknown_csv[10]
                        unknown_xlsx=next(r for r in valeurs[7:] if r[1]==refs[sens])
                        assert unknown_xlsx[4:10]==(None,)*6
                        assert 'historique invalide' in unknown_xlsx[10]
                        assert ligne_total[4:10]==(None,)*6
                    else:
                        assert ligne_total[4]==montant
                        assert len(csv_rows[0])==10
                    pdf=PdfReader(telecharger(page,'PDF',tmp_path,sens+'-agee'))
                    texte=' '.join(p.extract_text() or '' for p in pdf.pages)
                    assert noms[sens] in texte
                    if inconnu:
                        assert refs[sens] in texte and 'vérifier' in texte
                    else:
                        assert ('1 200,00' if sens=='vente' else '600,00') in texte
                assert mutations==[]
                assert not erreurs and not serveur,(erreurs,serveur)
            finally: browser.close()
        assert photographie(application)==avant
    finally: api.close()
