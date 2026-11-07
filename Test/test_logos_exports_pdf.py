"""Vrais rendus PDF : logo intégré, données et archives conservées."""
from copy import deepcopy
from datetime import date
from io import BytesIO
from types import SimpleNamespace
import pytest
from pypdf import PdfReader
from test_logo_societe import image_data
from test_fact9_documents_pdf import _societe
from test_patch09_3_liasse_fiscale import _dummy_liasse
from services.liasse_pdf import generer_liasse_pdf
from services.balance_preparation_pdf import generer_preparation_pdf
from services.balance_import_service import preparer_balance_liasse
from services.livre_inventaire_pdf import generer_livre_inventaire_pdf
from pdf_generator import generer_etat_financier, generer_document


@pytest.mark.parametrize('format',['PNG','JPEG'])
@pytest.mark.parametrize('genre',['commercial','financier','liasse','preparation','inventaire'])
def test_logo_reel_sur_premiere_page_et_sources_intactes(genre,format):
    soc=_societe();soc.logo_url=image_data(format)
    if genre=='commercial':
        pdf=generer_document(soc,titre='FACTURE',numero='LOGO-FICTIF',date_doc=date(2026,10,15),
            tiers='Client fictif',label_tiers='CLIENT',lignes=[],totaux=[])
    elif genre=='financier':
        pdf=generer_etat_financier(soc,titre='Bilan fictif',exercice=2026,colonnes=['Net'],
            lignes=[{'label':'Matériel fictif','valeurs':[1234.56]}])
    elif genre=='liasse':
        data=_dummy_liasse();data['societe']['logo_url']=soc.logo_url
        avant=deepcopy(data);pdf=generer_liasse_pdf(data);assert data==avant
    elif genre=='preparation':
        contenu={'preparation':preparer_balance_liasse([
            {'compte':'1111','credit':'1000'},{'compte':'5141','debit':'1000'}],None,{'1111','5141'}),
            'periode':{'debut':'2026-01-01','fin':'2026-12-31'},'sources':{'noms_fichiers':{'n':'FICTIF.csv'}}}
        data={'exercice':2026,'version':1,'contenu':contenu,'empreinte_sha256':'a'*64}
        avant=deepcopy(data);pdf=generer_preparation_pdf(data,soc);assert data==avant
    else:
        data={'exercice':{'annee':2026,'date_debut':'2026-01-01','date_fin':'2026-12-31','statut':'ouvert'},
            'bilan':{},'cpc':{},'stocks':{}}
        avant=deepcopy(data);pdf=generer_livre_inventaire_pdf(soc,data);assert data==avant
    reader=PdfReader(BytesIO(pdf))
    assert len(reader.pages[0].images)==1
    if genre=='financier':
        texte=' '.join(p.extract_text() for p in reader.pages)
        assert 'Matériel fictif' in texte and '1 234,56' in texte


def test_archive_ancienne_sans_logo_reste_sans_logo():
    data=_dummy_liasse();avant=deepcopy(data)
    assert not PdfReader(BytesIO(generer_liasse_pdf(data))).pages[0].images
    assert data==avant


@pytest.mark.parametrize('logo',[None,'','https://example.com/logo.png','C:/secret.png','data:image/png;base64,aW52YWxpZA=='])
def test_logo_historique_absent_ou_invalide_ne_bloque_pas_pdf(logo):
    soc=_societe();soc.logo_url=logo
    pdf=generer_etat_financier(soc,titre='Test fictif',exercice=2026,colonnes=['Net'],lignes=[])
    assert not PdfReader(BytesIO(pdf)).pages[0].images
