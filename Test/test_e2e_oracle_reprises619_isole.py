"""Scénario619 : oracle centimes indépendant -> interface -> cinq pièces réelles."""
from contextlib import closing
from decimal import Decimal
from io import BytesIO,StringIO
import csv
import json
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright,expect
from sqlalchemy import text
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,PATH)
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_e2e_prorata_inventaire_isole import ecriture,photo
from test_e2e_administration_isole import connexion,observer
from test_e2e_annee_connectee_isole import valider_brouillons_ui
from test_logo_societe import image_data
from browser_support import chromium_executable

ROOT=Path(__file__).resolve().parents[1]
JEU=json.loads((ROOT/'docs/recette/donnees_recette_reprises_20261019.json').read_text(encoding='utf8'))


def ouvrir2025(page,app,aid):
    page.goto(app['web_url']+'/cloture')
    page.get_by_label('Exercice actif',exact=True).select_option('2025')
    expect(page.get_by_role('heading',name="Clôture de l'exercice 2025",exact=True)).to_be_visible()
    page.get_by_text('Reprises partielles de provisions',exact=True).click()
    region=page.get_by_role('region',name='Reprises partielles de provisions',exact=True)
    expect(region.get_by_label('Dotation source',exact=True).locator(f'option[value="{aid}"]')).to_have_count(1)
    region.get_by_label('Dotation source',exact=True).select_option(str(aid))
    return region


@pytest.mark.parametrize('largeur',[1440,390])
def test_619_oracle_cpc_bilan_fec_et_reprises_interface(application,largeur,tmp_path):
    api,email,password=client(application);o=JEU['oracle']
    with closing(api),sync_playwright() as p:
        ok(api.patch('/api/societe/moi',json={'raison_sociale':JEU['societe']['nom'],
            'exercice_debut':2025,'forme_juridique':'SARL','devise':'MAD','logo_url':image_data('PNG')}))
        ok(api.post('/api/plan-comptable/initialiser'))
        cap=ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAP-PV01')
        a=ok(api.post('/api/cloture/ajustements?exercice=2025',json=JEU['dotation']))
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        originaux=photo(application,[cap,a['ecriture_id']]);sid=ok(api.get('/api/societe/moi'))['id']
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            page.on('dialog',lambda d:d.accept());erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password);reprises=[]
            for i,r in enumerate(JEU['reprises']):
                region=ouvrir2025(page,application,a['id'])
                region.get_by_label('Date de reprise',exact=True).fill('2025-12-31')
                region.get_by_label('Montant de reprise (MAD)',exact=True).fill(r['montant'])
                region.get_by_label('Justification de la reprise',exact=True).fill(r['justification'])
                region.get_by_label('Référence de pièce (facultative)',exact=True).fill(r['reference'])
                region.get_by_label('Date de pièce (facultative)',exact=True).fill('2025-12-31')
                region.get_by_role('button',name='Vérifier la reprise',exact=True).click()
                region.get_by_label('J’ai vérifié les mouvements du compte et les justificatifs de la reprise.',exact=True).check()
                with page.expect_response(lambda rep:rep.request.method=='POST' and rep.url.endswith(f"{PATH}/{a['id']}")) as sortie:
                    region.get_by_role('button',name='Créer le brouillon de reprise',exact=True).click()
                assert sortie.value.status==200,sortie.value.text()
                reprises.append(sortie.value.json()['reprises'][0])
                assert sortie.value.json()['disponible']==o['capacites']['premier_brouillon' if i==0 else 'deux_reprises']
                valider_brouillons_ui(page,application,1)
            etats=ok(api.get('/api/etats/liasse/2025'))['etats']
            assert Decimal(str(etats['cpc']['resultat_net']))==Decimal(o['apres_deux_reprises']['resultat_avant_impot'])
            region=ouvrir2025(page,application,a['id'])
            region.get_by_role('button',name=f"Annuler la reprise {reprises[0]['id']}",exact=True).click()
            ann=region.get_by_role('form',name='Annulation de reprise',exact=True)
            ann.get_by_label('Date d’annulation',exact=True).fill(JEU['annulation']['date'])
            ann.get_by_label('Motif d’annulation',exact=True).fill(JEU['annulation']['motif'])
            with page.expect_response(lambda rep:rep.request.method=='POST' and rep.url.endswith('/annuler')) as sortie:
                ann.get_by_role('button',name='Créer l’inverse de reprise',exact=True).click()
            assert sortie.value.status==200 and sortie.value.json()['disponible']==o['capacites']['inverse_brouillon']
            valider_brouillons_ui(page,application,1)
            region=ouvrir2025(page,application,a['id']);expect(region).to_contain_text('800,00 MAD')
            d=ok(api.get(f"{PATH}/{a['id']}"));assert d['disponible']==o['disponible_final']
            assert d['reprises_validees']==o['reprises_actives'] and d['reservations_brouillons']=='0.00'
            with application['engine'].connect() as db:
                soldes=db.execute(text('''SELECT l.compte,sum(l.debit-l.credit) AS solde
                    FROM lignes_ecriture l JOIN ecritures e ON e.id=l.ecriture_id
                    WHERE e.societe_id=:s AND e.exercice=2025 GROUP BY l.compte'''),{'s':sid}).all()
                assert {r.compte:int(r.solde*100) for r in soldes}==o['soldes_cents']
                pieces=db.execute(text('SELECT count(*),bool_and(est_validee) FROM ecritures WHERE societe_id=:s AND exercice=2025'),{'s':sid}).one()
                assert tuple(pieces)==(o['journal']['pieces'],True)
            etats=ok(api.get('/api/etats/liasse/2025'))['etats']
            assert etats['bilan']['equilibre']
            assert Decimal(str(etats['bilan']['actif']['total']['net']))==Decimal(o['actif'])
            assert Decimal(str(etats['bilan']['passif']['total']))==Decimal(o['passif'])
            assert Decimal(str(etats['cpc']['resultat_net']))==Decimal(o['resultat_avant_impot'])
            fec=api.get('/api/fec/export',params={'exercice':2025});assert fec.status_code==200,fec.text
            lignes=list(csv.DictReader(StringIO(fec.content.decode('utf-8-sig')),delimiter='\t'))
            assert len(lignes)==o['journal']['lignes'],lignes[:2]
            # Noms des colonnes de l'Avis24 réel, conservés par l'export.
            debit='Montant_Debit';credit='Montant_Credit'
            assert sum(Decimal(r[debit].replace(',','.')) for r in lignes)==Decimal(o['journal']['debit'])
            assert sum(Decimal(r[credit].replace(',','.')) for r in lignes)==Decimal(o['journal']['credit'])
            (tmp_path/'FEC619_fictif2025.txt').write_bytes(fec.content)
            with page.expect_download() as telechargement:region.get_by_role('button',name='Télécharger le suivi PDF',exact=True).click()
            telechargement.value.save_as(tmp_path/'suivi619_fictif.pdf')
            assert photo(application,[cap,a['ecriture_id']])==originaux
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
