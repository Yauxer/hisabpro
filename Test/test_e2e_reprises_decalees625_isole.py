"""Source2025 close, reprise2026 date2025, inverse2027 date2026, vrai cycle."""
from contextlib import closing
from decimal import Decimal
from io import BytesIO
import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from playwright.sync_api import sync_playwright,expect
from test_reprises_provisions615_isole import (
    application,application099,application098,application097,application093,application092,
    application091,application090,application089,application087,migration,corps,demande,PATH)
from test_ajustements_inventaire_isole import exercice,donnees
from test_ras_lecture_conservation import client
from test_multi_societes_runtime_isole import ok
from test_permissions_tva_runtime_isole import donnees_metier
from test_e2e_prorata_inventaire_isole import ecriture,photo
from test_e2e_administration_isole import connexion,observer
from test_e2e_annee_connectee_isole import ORACLE as PROFIL,valider_brouillons_ui
from test_logo_societe import image_data
from browser_support import chromium_executable


@pytest.mark.parametrize('largeur',[1440,390])
def test_625_source_decalee_deux_clotures_inverse_ouvert_et_exports(application,largeur,tmp_path):
    api,email,password=client(application)
    with closing(api),sync_playwright() as p:
        exercice(api,'2024-07-01','2025-06-30')
        ok(api.patch('/api/exercices/2026',json={'date_debut':'2025-07-01','date_fin':'2026-06-30'}))
        ok(api.patch('/api/societe/moi',json={'raison_sociale':'Provisions décalées fictives625','forme_juridique':'SARL',
            'regime_fiscal':'is','exercice_debut':2020,'capital_social':20000,'logo_url':image_data('PNG')}))
        for annee in (2025,2026):ok(api.put(f'/api/fiscalite/is/{annee}/parametres',json=PROFIL['profil']['parametres_is']))
        capital=ecriture(api,'2025-01-02',[('5141','20000',0),('1111',0,'20000')],'CAPITAL-FICTIF625')
        a=ok(api.post('/api/cloture/ajustements?exercice=2025',json=donnees('provision_risque','6195','1518',montant='1000',libelle='DOSSIER-FICTIF625')))
        ok(api.post(f"/api/ecritures/{a['ecriture_id']}/valider"))
        # Hypothèse fiscale explicitement fictive du banc : le calcul propose
        # un déficit1000. Enregistrer ce stock puis confirmer son utilisation,
        # jamais supprimer un contrôle pour permettre la seconde clôture.
        deficit=ok(api.post('/api/fiscalite/is/2025/deficits/enregistrer-genere'))
        assert Decimal(str(deficit['montant_ordinaire']))==1000
        source=photo(application,[capital,a['ecriture_id']])
        clos=ok(api.post('/api/cloture/cloturer?exercice=2025'))
        assert Decimal(str(clos['resultat_net']))==Decimal('-4000')
        c=corps(api,a['id'],demande('400',date='2025-07-01',reference='REP-FICTIVE625',date_piece='2025-07-01'))
        s=ok(api.post(f"{PATH}/{a['id']}",json=c));r=s['reprises'][0]
        assert r['date']=='2025-07-01' and r['exercice']==2026
        ok(api.post(f"/api/ecritures/{r['ecriture_id']}/valider"))
        original_reprise=photo(application,[r['ecriture_id']])
        avant=donnees_metier(application)
        refuse=api.post('/api/cloture/cloturer?exercice=2026')
        assert refuse.status_code==409 and 'déficit' in refuse.text.lower(),refuse.text
        assert donnees_metier(application)==avant
        confirme=ok(api.post('/api/fiscalite/is/2026/deficits/confirmer-imputation'))
        assert Decimal(str(confirme['montant_confirme']))==400
        clos=ok(api.post('/api/cloture/cloturer?exercice=2026'))
        assert Decimal(str(clos['resultat_net']))==Decimal('-2600')
        fiscal2026=ok(api.get('/api/fiscalite/is/2026'))
        assert photo(application,[r['ecriture_id']])==original_reprise
        assert api.patch(f"/api/ecritures/{r['ecriture_id']}",json={'libelle':'Interdit'}).status_code==409
        navigateur=p.chromium.launch(executable_path=chromium_executable(),headless=True)
        try:
            page=navigateur.new_page(viewport={'width':largeur,'height':1000});page.set_default_timeout(20000)
            page.on('dialog',lambda d:d.accept());erreurs,serveur=observer(page,application['api_url'])
            connexion(page,application['web_url'],email,password)
            page.goto(application['web_url']+'/cloture');page.get_by_label('Exercice actif',exact=True).select_option('2027')
            expect(page.get_by_role('heading',name="Clôture de l'exercice 2027",exact=True)).to_be_visible()
            page.get_by_text('Reprises partielles de provisions',exact=True).click()
            region=page.get_by_role('region',name='Reprises partielles de provisions',exact=True)
            region.get_by_label('Dotation source',exact=True).select_option(str(a['id']))
            expect(region).to_contain_text('2025-07-01 · Exercice 2026')
            region.get_by_role('button',name=f"Annuler la reprise {r['id']}",exact=True).click()
            ann=region.get_by_role('form',name='Annulation de reprise',exact=True)
            ann.get_by_label('Date d’annulation',exact=True).fill('2026-07-01')
            ann.get_by_label('Motif d’annulation',exact=True).fill('Correction fictive sur exercice ouvert625')
            with page.expect_response(lambda rep:rep.request.method=='POST' and rep.url.endswith('/annuler')) as sortie:
                ann.get_by_role('button',name='Créer l’inverse de reprise',exact=True).click()
            assert sortie.value.status==200,sortie.value.text()
            d=sortie.value.json();inverse=d['reprises'][0]
            assert inverse['inverse_date']=='2026-07-01' and inverse['inverse_exercice']==2027
            assert d['disponible']=='600.00'
            valider_brouillons_ui(page,application,1)
            page.goto(application['web_url']+'/cloture');page.get_by_text('Reprises partielles de provisions',exact=True).click()
            region=page.get_by_role('region',name='Reprises partielles de provisions',exact=True)
            region.get_by_label('Dotation source',exact=True).select_option(str(a['id']))
            expect(region).to_contain_text('2026-07-01 · Exercice 2027')
            expect(region).to_contain_text('Capacité libérée.')
            assert ok(api.get(f"{PATH}/{a['id']}"))['disponible']=='1000.00'
            for fmt,label in [('pdf','PDF'),('xlsx','Excel')]:
                with page.expect_download() as telechargement:region.get_by_role('button',name='Télécharger le suivi '+label,exact=True).click()
                fichier=tmp_path/f'reprises625_{largeur}.{fmt}';telechargement.value.save_as(fichier)
                if fmt=='pdf':
                    pdf=PdfReader(fichier);texte=' '.join('\n'.join(x.extract_text() or '' for x in pdf.pages).split())
                    assert 'Exercice de reprise : 2026' in texte and 'Exercice de l’inverse : 2027' in texte
                else:
                    w=load_workbook(fichier);assert w['Reprises']['N2'].value=='2026' and w['Reprises']['O2'].value=='2027'
            etats=ok(api.get('/api/etats/liasse/2027'))['etats']
            assert Decimal(str(etats['cpc']['resultat_net']))==Decimal('-400') and etats['bilan']['equilibre']
            assert Decimal(str(etats['bilan']['actif']['total']['net']))==20000
            for annee,date_attendue in [(2026,b'20250701'),(2027,b'20260701')]:
                fec=api.get('/api/fec/export',params={'exercice':annee});assert fec.status_code==200,fec.text
                assert date_attendue in fec.content
                (tmp_path/f'FEC625_{annee}.txt').write_bytes(fec.content)
            assert photo(application,[capital,a['ecriture_id']])==source
            assert photo(application,[r['ecriture_id']])==original_reprise
            apres=ok(api.get('/api/fiscalite/is/2026'))
            assert apres['deficits']==fiscal2026['deficits']
            assert apres['source_comptable']==fiscal2026['source_comptable']
            assert not erreurs and not serveur,(erreurs,serveur)
        finally:navigateur.close()
