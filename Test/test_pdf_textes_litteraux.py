"""Données textuelles littérales : pas d'image chargée depuis un libellé."""
from io import BytesIO
import pytest
from PIL import Image
from pypdf import PdfReader
from pdf_generator import generer_etat_financier
from services.livre_inventaire_pdf import generer_livre_inventaire_pdf
from test_fact9_documents_pdf import _societe


@pytest.mark.parametrize('genre',['financier','inventaire'])
def test_nom_societe_avec_balises_reste_litteral(genre):
    soc=_societe();soc.raison_sociale='Atlas <SARL> & associés'
    if genre=='financier':
        pdf=generer_etat_financier(soc,titre='État fictif',exercice=2026,colonnes=['Net'],lignes=[])
    else:
        pdf=generer_livre_inventaire_pdf(soc,{'exercice':{'annee':2026,'date_debut':'2026-01-01',
            'date_fin':'2026-12-31','statut':'ouvert'},'bilan':{},'cpc':{},'stocks':{}})
    texte=PdfReader(BytesIO(pdf)).pages[0].extract_text()
    # L'identité existe aussi au pied ; au moins deux occurrences prouvent
    # que le nom n'a pas perdu sa partie<SARL>dans l'en-tête.
    assert texte.count(soc.raison_sociale)>=2


@pytest.mark.parametrize('champ',['raison_sociale','adresse','titre','sous_titre','label'])
def test_texte_ne_charge_pas_une_image_locale_fictive(tmp_path,champ):
    path=tmp_path/'IMAGE-FICTIVE-NE-PAS-CHARGER.png'
    Image.new('RGB',(20,10),'red').save(path)
    valeur=f'<img src="{path.as_posix()}"/>'
    soc=_societe()
    kwargs={'titre':'État fictif','sous_titre':'Sous-titre fictif','exercice':2026,
            'colonnes':['Net'],'lignes':[{'type':'ligne','label':'Matériel fictif','valeurs':[1234.56]}]}
    if champ in ('raison_sociale','adresse'):setattr(soc,champ,valeur)
    elif champ=='label':kwargs['lignes'][0]['label']=valeur
    else:kwargs[champ]=valeur
    pdf=generer_etat_financier(soc,**kwargs)
    reader=PdfReader(BytesIO(pdf))
    assert not any(p.images for p in reader.pages)
    texte=' '.join(p.extract_text() for p in reader.pages)
    assert '<img src=' in texte and '1 234,56' in texte
