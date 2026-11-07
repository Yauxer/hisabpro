"""Entrée réception : navigation sans création, puis vraie commande et vrai BR."""
from contextlib import closing
from datetime import date
from decimal import Decimal
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import text
from playwright.sync_api import sync_playwright, expect
from test_e2e_runtime_session_isole import application, application090, application089, application087, migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_administration_isole import connexion, observer
from test_e2e_receptions_lecture667_isole import ouvrir
from browser_support import chromium_executable


def compteurs(app, sid, aid):
    with app['engine'].connect() as db:
        return (db.scalar(text('SELECT stock_actuel FROM articles WHERE id=:a'), {'a': aid}),
            *(db.scalar(text(f'SELECT count(*) FROM {t} WHERE societe_id=:s'), {'s': sid})
                for t in ('bons_commande','bons_livraison','mouvements_stock','ecritures')))


@pytest.mark.parametrize('role,largeur', [('admin',1440),('comptable',390),('lecture',1440),('lecture',390)])
def test_669_entree_claire_roles_et_bc_puis_br(application, role, largeur, tmp_path):
    api, email, password = client(application)
    with closing(api), sync_playwright() as p:
        suffix = uuid4().hex[:8]
        soc = ok(api.get('/api/societe/moi'));sid = soc['id']
        assert (soc.get('stock_declencheur_achat') or 'facture') == 'facture'
        nom, article = 'FOURNISSEUR FICTIF669 '+suffix, 'ARTICLE FICTIF669 '+suffix
        tiers = ok(api.post('/api/tiers', json={'nom': nom, 'type':'fournisseur'}),201)
        aid = ok(api.post('/api/articles', json={'code':'FICTIF669-'+suffix, 'designation':article,
            'prix_achat_ht':500, 'prix_vente_ht':700, 'tva':20, 'compte_achat':'6111',
            'stock_actuel':0, 'is_stockable':True}),201)['id']
        if role != 'admin':
            email, password = f'{role}669-{suffix}@example.com', 'ReceptionFictive669!'
            ok(api.post('/api/utilisateurs',json={'nom':role+' fictif669','email':email,
                'mot_de_passe':password,'role':role}),201)
        avant = compteurs(application,sid,aid);assert avant == (0,0,0,0,0)
        browser = p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page = browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
            erreurs,serveur = observer(page,application['api_url']);mutations=[]
            page.on('request',lambda r:mutations.append(r.url) if '/api/bons-' in r.url and r.method in ('POST','PATCH','DELETE') else None)
            connexion(page,application['web_url'],email,password)
            ouvrir(page,application)
            expect(page.get_by_text('Aucun bon de réception',exact=True)).to_be_visible()
            for mode in ('Vente','Achat'):
                assert page.get_by_role('button',name=mode,exact=True).evaluate('e=>{const b=e.getBoundingClientRect(),p=e.parentElement.getBoundingClientRect();return b.left>=p.left&&b.right<=p.right&&b.left>=0&&b.right<=innerWidth}')
            expect(page.get_by_role('button',name='Nouveau BR',exact=True)).to_have_count(0)
            preparer = page.get_by_role('button',name='Préparer depuis une commande',exact=True)
            if role == 'lecture':
                expect(preparer).to_have_count(0)
                with httpx.Client(base_url=application['api_url']) as lecteur:
                    auth=ok(lecteur.post('/api/auth/login',json={'email':email,'password':password}))
                    lecteur.headers['Authorization']='Bearer '+auth['access_token']
                    assert lecteur.post('/api/bons-commande',json={'type':'achat','date':date.today().isoformat(),
                        'tiers':nom,'tiers_id':tiers['id'],'lignes':[{'description':'INTERDIT FICTIF669','quantite':1,'prix_unitaire':500,'tva':20}]}).status_code==403
                assert compteurs(application,sid,aid)==avant and not mutations
            else:
                preparer.click()
                expect(page.get_by_role('button',name='Nouveau BC',exact=True)).to_be_visible()
                expect(page.get_by_role('dialog')).to_have_count(0)
                assert compteurs(application,sid,aid)==avant and not mutations
                page.get_by_role('button',name='Nouveau BC',exact=True).click()
                modal=page.get_by_role('dialog',name='Nouveau bon de commande',exact=True)
                modal.get_by_placeholder('Nom du fournisseur...',exact=True).fill(nom)
                modal.get_by_role('option').filter(has_text=nom).click()
                modal.get_by_placeholder('Article ou description...',exact=True).fill(article)
                modal.locator('li').filter(has_text=article).click()
                modal.get_by_label('Quantité',exact=True).fill('2')
                with page.expect_response(lambda r:r.url.endswith('/api/bons-commande') and r.request.method=='POST') as cree:
                    modal.get_by_role('button',name='Créer la commande',exact=True).click()
                assert cree.value.status==201,cree.value.text()
                bc=cree.value.json();assert bc['type']=='achat' and Decimal(str(bc['total_ttc']))==Decimal('1200')
                modal.wait_for(state='hidden')
                assert compteurs(application,sid,aid)==(0,1,0,0,0)
                row=page.locator('tbody tr').filter(has_text=nom)
                row.get_by_title('Créer un bon de réception sur le reliquat',exact=True).click()
                modal=page.get_by_role('dialog',name='Nouveau bon de réception',exact=True)
                expect(modal.locator('input[type=number]')).to_have_value('2')
                with page.expect_response(lambda r:r.url.endswith(f"/api/bons-commande/{bc['id']}/convertir-bl") and r.request.method=='POST') as recu:
                    modal.get_by_role('button',name='Créer le bon de réception',exact=True).click()
                assert recu.value.status==200,recu.value.text()
                br=recu.value.json();assert br['type']=='achat' and br['bon_commande_id']==bc['id']
                modal.wait_for(state='hidden')
                page.get_by_role('button',name='Bons de réception',exact=True).click()
                expect(page.get_by_text(br['numero'],exact=True)).to_be_visible()
                assert compteurs(application,sid,aid)==(0,1,1,0,0)
                assert len(mutations)==2
            page.screenshot(path=str(tmp_path/f'entree669_{role}_{largeur}.png'),full_page=True)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:browser.close()
