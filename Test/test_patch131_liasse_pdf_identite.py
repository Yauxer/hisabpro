from io import BytesIO
from pypdf import PdfReader
from test_patch09_3_liasse_fiscale import _dummy_liasse
from services.liasse_pdf import generer_liasse_pdf


def test_raison_sociale_reste_litterale_dans_le_titre_et_le_pied_de_page():
    data = _dummy_liasse()
    nom = 'Atlas <SARL> & associés'
    data['societe']['raison_sociale'] = nom
    texte = ' '.join(PdfReader(BytesIO(generer_liasse_pdf(data))).pages[0].extract_text().split())
    assert texte.count(nom) >= 2
