"""Une ligne de relevé historique non finie ne devient pas zéro ou un match certain."""
from contextlib import closing
from datetime import date,timedelta
import pytest
from playwright.sync_api import sync_playwright,expect
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion,observer
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_rapprochement_ventilation_isole import migration
from test_rapprochement_propositions_isole import deux_propositions,proposer,flags
from test_lecture_reglements_historiques import photo
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible

@pytest.mark.parametrize('valeur',['NaN','Infinity','-Infinity','0','-10'])
def test_historique_non_fini_ignore_sans_reparation_et_lot_certain_conserve(application,migration,valeur):
    with closing(client(application)[0]) as api:
        rid,simple=deux_propositions(application,api);cible(application)
        lid=next(p['ecriture_ligne_id'] for p in proposer(api)['propositions'] if p['releve_id']==simple)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE rapprochement_lignes SET montant=CAST(:v AS double precision) WHERE id=:id'),{'v':valeur,'id':simple})
            avant=db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t ORDER BY id')).scalars().all()
        lecture=api.get('/api/rapprochement/5141');assert lecture.status_code==200,lecture.text
        ligne=next(x for x in lecture.json() if x['id']==simple)
        assert ligne['montant'] is None and not ligne['montant_valide'] and ligne['montant_anomalie']
        r=api.get('/api/rapprochement/5141/propositions',params={'date_debut':f'{date.today().year}-01-01','date_fin':f'{date.today().year}-12-31'})
        assert r.status_code==200,r.text
        assert [p['releve_id'] for p in r.json()['propositions']]==[rid]
        refus=api.post(f'/api/rapprochement/{simple}/rapprocher',json={'ecriture_ligne_id':lid})
        assert refus.status_code==409,refus.text
        with application['engine'].connect() as db:
            assert db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t ORDER BY id')).scalars().all()==avant


@pytest.mark.parametrize('largeur',[1365,390])
def test_releve_inconnu_ui_ne_devient_pas_zero_et_proposition_certaine_possible(application,migration,largeur):
    api,email,password=client(application)
    try:
        rid,simple=deux_propositions(application,api);cible(application)
        with application['engine'].begin() as db:
            db.execute(text("UPDATE rapprochement_lignes SET montant='NaN'::float8 WHERE id=:id"),{'id':simple})
            avant=db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t ORDER BY id')).scalars().all()
            ligne_avant=db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t WHERE id=:id'),{'id':simple}).scalar_one()
        compta_avant=photo(application)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
                errors,server=observer(page,application['api_url']);connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/rapprochement')
                ref=api.get('/api/rapprochement/5141').json()[-1]['libelle']
                row=page.locator('tbody tr').filter(has_text=ref).filter(has=page.locator('select'))
                expect(row).to_contain_text('À vérifier')
                expect(row).not_to_contain_text('+0,00')
                expect(row.locator('select')).to_be_disabled()
                expect(page.get_by_role('alert')).to_contain_text('Totaux du relevé à vérifier')
                page.get_by_placeholder('Début de période',exact=True).fill('0')
                with page.expect_response(lambda r:r.url.endswith('/5141/etat') and r.request.method=='PUT'):
                    page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).click()
                page.get_by_placeholder('Facultatif : solde indiqué par la banque',exact=True).fill('300')
                with page.expect_response(lambda r:r.url.endswith('/5141/etat') and r.request.method=='PUT'):
                    page.get_by_role('heading',name='Rapprochement bancaire',exact=True).click()
                expect(page.get_by_text('✓ Équilibré',exact=True)).to_have_count(0)
                expect(page.get_by_text('✓ Initial + mouvements = final',exact=True)).to_have_count(0)
                page.get_by_role('button',name='Proposer les rapprochements',exact=True).click()
                modal=page.get_by_role('dialog',name='Propositions de rapprochement')
                expect(modal.locator('input[type=checkbox]')).to_have_count(1)
                expect(modal).to_contain_text('sans correspondance')
                with application['engine'].connect() as db:
                    assert db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t ORDER BY id')).scalars().all()==avant
                with page.expect_response(lambda r:r.url.endswith('/5141/rapprocher-propositions')) as pointage:
                    modal.get_by_role('button',name='Rapprocher la sélection',exact=True).click()
                assert pointage.value.status==200,pointage.value.text()
                assert flags(api)=={rid:True,simple:False}
                with application['engine'].connect() as db:
                    assert db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t WHERE id=:id'),{'id':simple}).scalar_one()==ligne_avant
                assert photo(application)==compta_avant
                assert not errors and not server,(errors,server)
            finally:browser.close()
    finally:api.close()


def test_reprise_solde_avec_mouvement_non_fini_reste_inconnue(application,migration):
    with closing(client(application)[0]) as api:
        _,simple=deux_propositions(application,api);cible(application);annee=date.today().year
        r=api.put('/api/rapprochement/5141/etat',json={'date_debut':f'{annee}-01-01',
            'date_fin':f'{annee}-12-31','solde_initial':0,'solde_final':None})
        assert r.status_code==200,r.text
        with application['engine'].begin() as db:
            db.execute(text("UPDATE rapprochement_lignes SET montant='NaN'::float8 WHERE id=:id"),{'id':simple})
            avant=db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t ORDER BY id')).scalars().all()
        demain=date.today()+timedelta(days=1)
        r=api.get('/api/rapprochement/5141/situation',params={'date_debut':demain.isoformat(),'date_fin':max(demain,date(annee,12,31)).isoformat()})
        assert r.status_code==200,r.text
        assert r.json()['solde_initial_suggere'] is None
        with application['engine'].connect() as db:
            assert db.execute(text('SELECT row_to_json(t)::text FROM rapprochement_lignes t ORDER BY id')).scalars().all()==avant
