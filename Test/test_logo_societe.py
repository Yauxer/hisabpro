import base64
from io import BytesIO

import pytest
from PIL import Image
from pydantic import ValidationError
from pypdf import PdfReader

from routers.societe import SocieteUpdate
from services.logo_societe_service import normaliser_logo, MAX_LOGO_BYTES
from pdf_generator import generer_document
from test_fact9_documents_pdf import _societe
from datetime import date


def image_data(format='PNG', size=(20, 12)):
    buf = BytesIO()
    Image.new('RGB', size, '#185FA5').save(buf, format=format)
    mime = 'png' if format == 'PNG' else 'jpeg'
    return f'data:image/{mime};base64,' + base64.b64encode(buf.getvalue()).decode()


@pytest.mark.parametrize('format', ['PNG', 'JPEG'])
def test_logo_valide_et_image_reelle_dans_pdf(format):
    data = image_data(format)
    assert SocieteUpdate(logo_url=data).logo_url == data
    societe = _societe(); societe.logo_url = data
    pdf = generer_document(societe, titre='FACTURE', numero='LOGO-FICTIF', date_doc=date(2026, 10, 7),
                           tiers='Client fictif', label_tiers='CLIENT', lignes=[], totaux=[])
    assert len(PdfReader(BytesIO(pdf)).pages[0].images) == 1


@pytest.mark.parametrize('value', [
    'http://127.0.0.1/logo.png', 'https://example.com/logo.png',
    'C:/secret/logo.png', '/etc/logo.png', 'file:///logo.png',
    'data:image/svg+xml;base64,PHN2Zz4=', 'data:image/png;base64,invalid',
    'data:image/png;base64,' + base64.b64encode(b'not an image').decode(),
])
def test_logo_nouveau_url_chemin_et_image_invalide_refuses(value):
    with pytest.raises(ValidationError):
        SocieteUpdate(logo_url=value)


def test_logo_limites_format_et_effacement():
    with pytest.raises(ValueError, match='512 Ko'):
        normaliser_logo('data:image/png;base64,' + 'A' * (MAX_LOGO_BYTES * 2))
    with pytest.raises(ValueError, match='millions de pixels'):
        normaliser_logo(image_data(size=(2001, 2000)))
    with pytest.raises(ValueError, match='correspond pas'):
        normaliser_logo(image_data('JPEG').replace('image/jpeg', 'image/png'))
    assert SocieteUpdate(logo_url='  ').logo_url == ''
    assert SocieteUpdate(raison_sociale='Autre titre').model_dump(exclude_unset=True) == {'raison_sociale': 'Autre titre'}


def test_jpeg_tronque_refuse_avant_pdf():
    raw = base64.b64decode(image_data('JPEG').split(',')[1])[:-2]
    with pytest.raises(ValueError, match='illisible'):
        normaliser_logo('data:image/jpeg;base64,' + base64.b64encode(raw).decode())
