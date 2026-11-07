"""Historiques invalides simulés uniquement sur brouillons PostgreSQL nonce."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from playwright.sync_api import sync_playwright,expect
from test_e2e_runtime_session_isole import application,application090,application089,application087,migration
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_justificatifs_modeles_runtime_isole import ecriture,original
from test_e2e_administration_isole import connexion,observer
from browser_support import chromium_executable


def historique(application,api,valeur):
    eid=ecriture(api,validee=False,reference='HISTORIQUE-FICTIF470')
    with application['engine'].begin() as db:
        # Une ancienne anomalie de brouillon : les contrôles des écritures
        # définitives restent actifs et ne sont jamais contournés.
        db.execute(text('UPDATE lignes_ecriture SET debit=CAST(:v AS numeric) WHERE ecriture_id=:id AND debit>0'),{'v':valeur,'id':eid})
    return eid,original(application,eid)


@pytest.mark.parametrize('valeur',['NaN','0'])
def test_lecture409_detail_par_piece_et_saisie422_sans_reparation(application,valeur):
    with closing(client(application)[0]) as api,closing(client(application)[0]) as autre:
        eid,avant=historique(application,api,valeur)
        for path,params in [('/api/ecritures',{'exercice':date.today().year}),
                            (f'/api/ecritures/{eid}',{}),
                            ('/api/ecritures/par-piece',{'reference':'HISTORIQUE-FICTIF470'})]:
            r=api.get(path,params=params)
            assert r.status_code==409,r.text
            detail=r.json()['detail']
            assert str(eid) in detail['msg']
            assert [e['id'] for e in detail['ecritures']]==[eid]
            assert detail['ecritures'][0]['erreurs']
        r=api.post(f'/api/ecritures/{eid}/valider')
        assert r.status_code in (400,422),r.text
        assert original(application,eid)==avant
        assert ok(autre.get('/api/ecritures',params={'exercice':date.today().year}))==[]
        assert autre.get(f'/api/ecritures/{eid}').status_code==404


def test_montant_negatif_deja_refuse_par_la_base_sans_contournement(application):
    with closing(client(application)[0]) as api:
        eid=ecriture(api,validee=False);avant=original(application,eid)
        with pytest.raises(IntegrityError) as error:
            with application['engine'].begin() as db:
                db.execute(text('UPDATE lignes_ecriture SET debit=-1 WHERE ecriture_id=:id AND debit>0'),{'id':eid})
        assert error.value.orig.pgcode=='23514'
        assert original(application,eid)==avant


@pytest.mark.parametrize('largeur',[1440,390])
def test_journal_erreur_visible_pas_de_faux_total_ni_export(application,largeur):
    api,email,password=client(application)
    try:
        eid,avant=historique(application,api,'NaN')
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=chromium_executable(),headless=True)
            try:
                page=browser.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(15000)
                errors,server_errors=observer(page,application['api_url'])
                connexion(page,application['web_url'],email,password)
                page.goto(application['web_url']+'/journal')
                alerte=page.get_by_role('alert')
                expect(alerte).to_contain_text(str(eid))
                expect(page.get_by_role('button',name='Réessayer',exact=True)).to_be_enabled()
                expect(page.get_by_role('table')).to_have_count(0)
                expect(page.get_by_role('button',name='Exporter CSV',exact=True)).to_have_count(0)
                expect(page.get_by_role('button',name='Imprimer',exact=True)).to_have_count(0)
                with page.expect_response(lambda r:'/api/ecritures?' in r.url and r.request.method=='GET') as retry:
                    page.get_by_role('button',name='Réessayer',exact=True).click()
                assert retry.value.status==409
                expect(alerte).to_contain_text(str(eid))
                assert original(application,eid)==avant
                assert not errors,errors
                assert not server_errors,server_errors
            finally:browser.close()
    finally:api.close()
