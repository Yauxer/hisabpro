"""Référentiel AV et libellés : vraie UI/API, écritures définitives PG nonce."""
from datetime import date
from decimal import Decimal
import uuid

import httpx
import pytest
from sqlalchemy.orm import Session

import models
from browser_support import chromium_executable
from test_e2e_administration_isole import connexion, observer
from test_e2e_facturation_isole import application, champ


def photographie(application, sid):
    with Session(application['engine']) as db:
        return [(e.id, e.journal, e.date, e.reference, e.libelle, e.est_validee, e.date_validation,
                 [(l.id, l.compte, l.libelle, l.debit, l.credit, l.tiers_id, l.compte_auxiliaire_snapshot) for l in e.lignes])
                for e in db.query(models.Ecriture).filter_by(societe_id=sid).order_by(models.Ecriture.id)]


@pytest.mark.parametrize('largeur', [1365, 390])
def test_av_unique_filtre_selecteur_libelles_et_dates_sources(application, largeur):
    suffix = uuid.uuid4().hex[:8]
    email, password = f'journaux-av-{suffix}@example.com', 'JournauxAV2026!'
    annee = date.today().year
    sources = []
    with httpx.Client(base_url=application['api_url']) as api:
        r = api.post('/api/auth/register', json={'nom': 'Administration avoirs fictive', 'email': email, 'password': password, 'raison_sociale': 'Journaux fictifs ' + suffix})
        assert r.status_code == 200, r.text
        api.headers['Authorization'] = 'Bearer ' + r.json()['access_token']
        sid = api.get('/api/societe/moi').json()['id']
        for index, ht in enumerate((100, 200), start=1):
            nom = f'Client avoir {index} fictif {suffix}'
            r = api.post('/api/tiers', json={'nom': nom, 'type': 'client'})
            assert r.status_code == 201, r.text
            tid = r.json()['id']
            jour = f'{annee}-03-{index+4:02d}'
            r = api.post('/api/factures', json={'type': 'vente', 'date': jour, 'tiers': nom, 'tiers_id': tid, 'reference': f'FACT-AV-{index}-{suffix}', 'lignes': [{'description': f'Vente fictive {index}', 'quantite': 1, 'prix_unitaire': ht, 'tva': 20}]})
            assert r.status_code == 201, r.text
            facture = r.json()
            fid = facture['id']
            assert api.post(f'/api/factures/{fid}/valider').status_code == 200
            r = api.post(f'/api/factures/{fid}/comptabiliser')
            assert r.status_code == 200, r.text
            assert api.post(f"/api/ecritures/{r.json()['ecriture_id']}/valider").status_code == 200
            r = api.post('/api/avoirs', json={'facture_id': fid, 'date': jour, 'motif': 'Annulation fictive sans retour physique', 'retour_stock': False, 'nature_avoir': 'retour_annulation', 'lignes': [{'facture_ligne_id': facture['lignes'][0]['id'], 'quantite': 1}]})
            assert r.status_code == 201, r.text
            avoir = r.json()
            assert Decimal(str(avoir['total_ttc'])) == Decimal(ht) * Decimal('1.20')
            r = api.post(f"/api/avoirs/{avoir['id']}/comptabiliser")
            assert r.status_code == 200, r.text
            eid = r.json()['ecriture_id']
            assert api.post(f'/api/ecritures/{eid}/valider').status_code == 200
            with Session(application['engine']) as db:
                e = db.get(models.Ecriture, eid)
                assert e.source == 'avoir' and e.journal == 'AV' and e.est_validee
                assert {l.compte: (l.debit, l.credit) for l in e.lignes} == {'7111': (ht, 0), '4455': (ht * .2, 0), '3421': (0, ht * 1.2)}
                sources.append({'id': eid, 'reference': e.reference, 'date': jour, 'libelle': e.libelle,
                                'lignes': [(l.compte, l.libelle) for l in e.lignes]})
        avant = photographie(application, sid)
        assert len(avant) == 4 and sum(len(e[-1]) for e in avant) == 12
        assert sum(Decimal(str(l[3])) for e in avant for l in e[-1]) == Decimal(720)
        assert sum(Decimal(str(l[4])) for e in avant for l in e[-1]) == Decimal(720)
        playwright = pytest.importorskip('playwright.sync_api')
        executable = chromium_executable()
        if not executable:
            pytest.skip('Chromium / Edge requis')
        with playwright.sync_playwright() as p:
            browser = p.chromium.launch(executable_path=executable, headless=True)
            try:
                page = browser.new_page(viewport={'width': largeur, 'height': 1000})
                page.set_default_timeout(20000)
                errors, server_errors = observer(page, application['api_url'])
                mutations = []
                page.on('request', lambda r: mutations.append((r.method, r.url)) if '/api/ecritures' in r.url and r.method in {'POST', 'PATCH', 'PUT', 'DELETE'} else None)
                connexion(page, application['web_url'], email, password)
                page.goto(application['web_url'] + '/journal', wait_until='domcontentloaded')
                page.locator('tbody tr').filter(has=page.locator(f'td[title="{sources[0]["reference"]}"]')).wait_for()
                filtre = page.get_by_role('button', name='AV — Avoirs', exact=True)
                playwright.expect(filtre).to_have_count(1)
                filtre.click()
                playwright.expect(page.locator('tbody tr[class*="rowMvt"]')).to_have_count(6)
                assert page.locator('tbody tr[class*="rowTotalGeneral"]').inner_text().count('360,00') == 2
                for source in sources:
                    ligne = page.locator('tbody tr').filter(has=page.locator(f'td[title="{source["reference"]}"]'))
                    playwright.expect(ligne).to_have_count(1)
                    cellules_fusion = ligne.locator('td[rowspan]')
                    assert cellules_fusion.nth(0).get_attribute('rowspan') == '3'
                    assert cellules_fusion.nth(0).inner_text().replace('\u200f', '') == f'{int(source["date"][-2:]):02d}/03/{str(annee)[-2:]}'
                    assert cellules_fusion.nth(1).inner_text() == 'AV'
                # Pas de mot « Avoir » ajouté artificiellement devant les libellés.
                libelles_visibles = page.locator('tbody td[class*="tdLibelle"] span[class*="libTexte"]').all_text_contents()
                attendus = sorted(label for source in sources for compte, label in source['lignes'])
                assert sorted(libelles_visibles) == attendus, (libelles_visibles, attendus)
                assert len(set(source['id'] for source in sources)) == 2
                assert len(set(source['reference'] for source in sources)) == 2
                page.get_by_role('button', name='Nouvelle écriture', exact=True).click()
                modal = page.get_by_role('dialog', name='Nouvelle écriture comptable', exact=True)
                select = champ(modal, 'Journal', 'select')
                options = select.locator('option').evaluate_all('(options) => options.map(o => ({code: o.value, label: o.textContent}))')
                assert len([o for o in options if o['code'] == 'AV']) == 1
                assert len({o['code'] for o in options}) == len(options)
                assert next(o for o in options if o['code'] == 'AV')['label'] == 'AV — Avoirs'
                select.select_option('AV')
                assert select.input_value() == 'AV'
                # Les autres codes distincts restent présents, sans fusion.
                for code in ('AC', 'VT', 'BQ', 'CA', 'OD', 'AN', 'EN', 'AE', 'AM', 'SA', 'TV', 'PR'):
                    assert sum(o['code'] == code for o in options) == 1
                modal.get_by_role('button', name='Annuler', exact=True).click()
                assert mutations == []
                assert not errors and not server_errors, (errors, server_errors)
            finally:
                browser.close()
        assert photographie(application, sid) == avant
