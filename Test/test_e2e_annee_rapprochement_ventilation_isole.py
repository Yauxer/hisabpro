"""Variante annuelle bancaire réelle ; oracle380 et écritures inchangés."""
from decimal import Decimal
from uuid import UUID
from playwright.sync_api import expect
from test_e2e_facturation_isole import application
from test_rapprochement_ventilation_isole import migration
from test_e2e_annee_ventilation_inter_exercices_isole import test_annee_ventilation_cloture_an_reglements_anciens_lettrage_et_exports as scenario
from test_e2e_annee_connectee_isole import ok,lignes_comptables

def test_annee_banque_1000_ventilations240_cloture_an_paiements120(application,migration,tmp_path):
    def banque(phase,api,page,paiements,sid,app):
        annee=2026 if phase=='apres_paiements' else 2025
        avant=lignes_comptables(app,sid)
        if phase!='apres_cloture':
            lignes=[]
            if annee==2025:
                lignes.append({'date':'2025-01-01','libelle':'BANK-ANN-CAP','montant':1000,'sens':'credit'})
            for sens in ['vente','achat']:
                lignes.append({'date':f'{annee}-06-15' if annee==2025 else '2026-02-15',
                    'libelle':f'BANK-ANN-{annee}-{sens}','montant':240 if annee==2025 else 120,
                    'sens':'credit' if sens=='vente' else 'debit'})
            result=ok(api.post('/api/rapprochement/import',json={'compte':'5141','lignes':lignes}),201)
            assert result['nb_creees']==len(lignes)
        page.goto(app['web_url']+'/rapprochement')
        select_annee=page.locator('select').filter(has=page.locator(f'option[value="{annee}"]')).first
        select_annee.select_option(str(annee))
        params={'date_debut':f'{annee}-01-01','date_fin':f'{annee}-12-31'}
        data=ok(api.get('/api/rapprochement/5141/situation',params=params))
        assert Decimal(str(data['solde_comptable_final']))==1000
        if phase=='apres_cloture':
            assert data['lecture_seule'] and len(data['lignes_releve'])==3
            assert sum(l['rapprochee'] for l in data['ecritures'])==5
            for l in data['lignes_releve']:
                row=page.locator('tbody tr').filter(has_text=l['libelle']).filter(has=page.locator('select'))
                expect(row.locator('select')).to_be_disabled()
                r=api.post(f"/api/rapprochement/{l['id']}/derapprocher",json={})
                assert r.status_code==409,r.text
        else:
            for l in data['lignes_releve']:
                row=page.locator('tbody tr').filter(has_text=l['libelle']).filter(has=page.locator('select'))
                if l['libelle']=='BANK-ANN-CAP':
                    cible=next(e for e in data['ecritures'] if e['reference']=='CAP-VENT-ANNUEL')
                    valeur=str(cible['ligne_id']);route='rapprocher'
                else:
                    sens='vente' if l['sens']=='credit' else 'achat'
                    if annee==2025:
                        valeur='VT:'+str(UUID(paiements[sens][0]['numero'].split('-')[1]));route='rapprocher-ventilation'
                    else:
                        cible=next(e for e in data['ecritures'] if e['ecriture_id']==paiements[sens]['ecriture_id'])
                        valeur=str(cible['ligne_id']);route='rapprocher'
                with page.expect_response(lambda r:r.url.endswith(f"/api/rapprochement/{l['id']}/{route}") and r.request.method=='POST') as response:
                    row.locator('select').select_option(valeur)
                assert response.value.status==200,response.value.text()
                expect(row.locator('select')).to_have_value(valeur)
            page.get_by_placeholder('Début de période',exact=True).fill('0' if annee==2025 else '1000')
            with page.expect_response(lambda r:r.url.endswith('/api/rapprochement/5141/etat') and r.request.method=='PUT') as initial:
                page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).click()
            assert initial.value.status==200,initial.value.text()
            page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).fill('1000')
            with page.expect_response(lambda r:r.url.endswith('/api/rapprochement/5141/etat') and r.request.method=='PUT') as final:
                page.get_by_role('heading',name='Rapprochement bancaire',exact=True).click()
            assert final.value.status==200,final.value.text()
            page.get_by_text('✓ Équilibré',exact=True).wait_for()
            page.get_by_text('✓ Initial + mouvements = final',exact=True).wait_for()
            page.reload()
            expect(page.get_by_text('Rapprochée',exact=True)).to_have_count(5 if annee==2025 else 2)
            data=ok(api.get('/api/rapprochement/5141/situation',params=params))
            assert all(l['rapprochee'] for l in data['lignes_releve'])
            assert sum(Decimal(str(l['montant'])) for l in data['lignes_releve'])==(1480 if annee==2025 else 240)
        assert avant==lignes_comptables(app,sid)
    scenario(application,tmp_path,banque)
