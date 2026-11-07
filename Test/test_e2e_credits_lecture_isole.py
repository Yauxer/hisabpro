"""Avoirs et acomptes : lecteur/comptable réels, historiques et PDF conservés."""
from contextlib import closing
from datetime import date
from pathlib import Path
import httpx
import pytest
from test_journal_cloture_concurrente_isole import (
    application,application097,application093,application092,application091,
    application090,application089,application087,migration,
)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_reglements_par_tiers_isole import dossier
from test_permissions_acomptes_avoirs_postgres import valider
from test_reglement_comptabilisation_concurrente_isole import metier
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def preparer(api,sens):
    tid,ids,p=dossier(api,sens);jour=p['date']
    fs=ok(api.get('/api/factures',params={'exercice':date.today().year}))
    f=next(x for x in fs if x['id']==ids[0])
    ok(api.post('/api/reglements',json={'facture_id':f['id'],'tiers':f['tiers'],
        'date':jour,'montant':120,'mode':'virement'}),201)
    av=[]
    for q in (0.5,0.25):
        av.append(ok(api.post('/api/avoirs',json={'facture_id':f['id'],'date':jour,
            'motif':'Crédit fictif545','retour_stock':False,
            'lignes':[{'facture_ligne_id':f['lignes'][0]['id'],'quantite':q}]}),201))
    ok(api.post(f"/api/avoirs/{av[0]['id']}/comptabiliser"))
    valider(api)
    ok(api.post(f"/api/avoirs/{av[0]['id']}/utiliser",json={'type_utilisation':'imputation',
        'facture_id':ids[1],'date_utilisation':jour,'montant':20}))
    ac=[]
    for montant,mode,compta in ((120,'virement',False),(60,'virement',True),(80,'cheque',False)):
        ac.append(ok(api.post('/api/acomptes',json={'type':'client' if sens=='vente' else 'fournisseur',
            'date':jour,'tiers':f['tiers'],'tiers_id':tid,'montant':montant,'mode':mode,
            'reference':'FICT545-'+str(montant),'comptabiliser':compta}),201))
    ok(api.post(f"/api/acomptes/{ac[1]['id']}/imputer",json={'facture_id':ids[1],
        'montant':30,'date_imputation':jour,'comptabiliser':True}))
    valider(api)
    av=sorted(ok(api.get('/api/avoirs',params={'exercice':date.today().year})),key=lambda x:x['id'])
    ac=sorted(ok(api.get('/api/acomptes',params={'exercice':date.today().year})),key=lambda x:x['id'])
    assert [x['total_ttc'] for x in av]==[60,30]
    assert av[0]['montant_disponible']==40 and len(av[0]['utilisations'])==1
    assert [x['montant_disponible'] for x in ac]==[120,30,80]
    assert ac[2]['statut_paiement']=='en_attente' and ac[1]['imputations'][0]['statut']=='active'
    return av,ac,ids


@pytest.mark.parametrize('sens',['vente','achat'])
@pytest.mark.parametrize('role,largeur',[('lecture',390),('lecture',1440),('comptable',1440)])
def test_credits_consultation_actions_historiques_et_pdf(application,sens,role,largeur,tmp_path):
    playwright=pytest.importorskip('playwright.sync_api')
    admin,email,password=client(application)
    with closing(admin),playwright.sync_playwright() as p:
        av,ac,fids=preparer(admin,sens)
        email=email.replace('@','-'+role+'@')
        ok(admin.post('/api/utilisateurs',json={'nom':'Utilisateur fictif545','email':email,
            'mot_de_passe':password,'role':role}),201)
        browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=browser.new_page(viewport={'width':largeur,'height':1000},accept_downloads=True)
            page.set_default_timeout(15000);erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            requetes=[]
            page.on('request',lambda r:requetes.append((r.method,r.url)) if r.url.startswith(application['api_url']) else None)
            avant=metier(application);ecarts=[];ecrire=role=='comptable'
            def controle(locator,nb,libelle):
                reel=locator.count()
                if reel!=(nb if ecrire else 0):ecarts.append((libelle,reel,nb if ecrire else 0))
            page.goto(application['web_url']+'/acomptes',wait_until='domcontentloaded')
            playwright.expect(page.get_by_role('button',name="Voir le détail et l'historique",exact=True)).to_have_count(3)
            if page.get_by_role('button',name='Nouvel acompte',exact=True).is_disabled()==ecrire:
                ecarts.append(('Nouvel acompte désactivé',not ecrire))
            for titre,nb in [('Imputer sur une facture',2),('Comptabiliser',1),("Annuler l'acompte",2)]:
                controle(page.get_by_role('button',name=titre,exact=True),nb,titre)
            def detail(a):
                page.locator('tbody tr').filter(has_text=a['numero']).get_by_role('button',name="Voir le détail et l'historique",exact=True).click()
                return page.get_by_role('dialog',name='Acompte '+a['numero'],exact=True)
            modal=detail(ac[1]);playwright.expect(modal.get_by_text('Active',exact=True)).to_be_visible()
            controle(modal.get_by_title('Annuler cette imputation',exact=True),1,'annuler imputation')
            page.keyboard.press('Escape')
            modal=detail(ac[2]);playwright.expect(modal.get_by_text('En attente',exact=True)).to_be_visible()
            controle(modal.get_by_role('button',name="Confirmer l'encaissement" if sens=='vente' else 'Confirmer le paiement',exact=True),1,'confirmer chèque')
            controle(modal.get_by_role('button',name='Marquer rejeté',exact=True),1,'rejeter chèque')
            page.keyboard.press('Escape')
            page.goto(application['web_url']+'/avoirs',wait_until='domcontentloaded')
            playwright.expect(page.get_by_title('Télécharger PDF',exact=True)).to_have_count(2)
            controle(page.get_by_title('Comptabiliser',exact=True),1,'comptabiliser avoir liste')
            row=page.locator('tbody tr').filter(has_text=av[0]['numero'])
            with page.expect_download() as dl:row.get_by_title('Télécharger PDF',exact=True).click()
            assert Path(dl.value.path()).read_bytes().startswith(b'%PDF')
            row.click();modal=page.get_by_role('dialog',name='Avoir '+av[0]['numero'],exact=True)
            playwright.expect(modal.get_by_text('Historique du crédit',exact=True)).to_be_visible()
            playwright.expect(modal).to_contain_text('40,00')
            assert modal.get_by_text('Annulée',exact=True).count()==0
            for titre in ('Imputer sur une facture','Rembourser'):
                controle(modal.get_by_role('button',name=titre,exact=True),1,titre+' avoir')
            controle(modal.get_by_title('Annuler cette utilisation',exact=True),1,'annuler utilisation avoir')
            page.keyboard.press('Escape')
            page.locator('tbody tr').filter(has_text=av[1]['numero']).click()
            modal=page.get_by_role('dialog',name='Avoir '+av[1]['numero'],exact=True)
            for titre in ('Comptabiliser',"Annuler l'avoir"):
                controle(modal.get_by_role('button',name=titre,exact=True),1,titre+' détail')
            assert metier(application)==avant
            assert not erreurs and not serveur,(erreurs,serveur)
            if not ecrire:
                assert not [(m,u) for m,u in requetes if m not in ('GET','OPTIONS')],requetes
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    lecteur.headers['Authorization']='Bearer '+ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))['access_token']
                    avant=metier(application)
                    appels=[(f"/api/acomptes/{ac[0]['id']}/comptabiliser",{}),
                        (f"/api/acomptes/{ac[1]['id']}/imputations/{ac[1]['imputations'][0]['id']}/annuler",{}),
                        (f"/api/acomptes/{ac[2]['id']}/statut-paiement",{'statut':'encaisse','date_operation':date.today().isoformat()}),
                        (f"/api/avoirs/{av[1]['id']}/comptabiliser",{}),
                        (f"/api/avoirs/{av[0]['id']}/utiliser",{'type_utilisation':'imputation','facture_id':fids[1],'date_utilisation':date.today().isoformat(),'montant':10}),
                        (f"/api/avoirs/{av[0]['id']}/utilisations/{av[0]['utilisations'][0]['id']}/annuler",{})]
                    for url,body in appels:assert lecteur.post(url,json=body).status_code==403,url
                    assert metier(application)==avant
            assert not ecarts,ecarts
        except BaseException:
            print(sens,role,page.locator('body').inner_text()[-6000:])
            page.screenshot(path=str(tmp_path/f'credits545-{sens}-{role}-{largeur}.png'),full_page=True)
            raise
        finally:browser.close()
