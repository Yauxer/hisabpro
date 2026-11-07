from io import BytesIO
from types import SimpleNamespace
from pypdf import PdfReader
from services.balance_import_service import preparer_balance_liasse, empreinte_preparation
from services.balance_preparation_pdf import generer_preparation_pdf
from test_balance_preparations import api, donnees


def test_pdf_literal_comparatif_et_pas_de_fiscalite_zero_supposee():
    n = [{'compte': '1111', 'credit': '100000'}, {'compte': '5141', 'debit': '150000'}, {'compte': '7111', 'credit': '50000'}]
    n1 = [{'compte': '1111', 'credit': '100000'}, {'compte': '1191', 'credit': '20000'}, {'compte': '5141', 'debit': '120000'}]
    contenu = {'preparation': preparer_balance_liasse(n, n1, {'1111','5141','7111','1191'}),
               'periode': {'debut':'2025-01-01','fin':'2025-12-31'}, 'sources': {'noms_fichiers':{'n':'<balance> & test.xlsx'}}}
    dossier = {'id':1,'exercice':2025,'version':2,'contenu':contenu,'empreinte_sha256':empreinte_preparation(contenu)}
    pdf = generer_preparation_pdf(dossier, SimpleNamespace(raison_sociale='Atlas <SARL> & associés'))
    reader = PdfReader(BytesIO(pdf)); texte = ' '.join(' '.join(p.extract_text() for p in reader.pages).split())
    assert len(reader.pages) >= 5
    assert 'Atlas <SARL> & associés' in texte and '<balance> & test.xlsx' in texte
    assert '150 000,00' in texte and '120 000,00' in texte and '50 000,00' in texte
    assert 'Indisponible' in texte and 'Classes 6/7 soldées' in texte
    assert dossier['empreinte_sha256'] in texte
    assert 'IS théorique' not in texte and 'Solde à payer' not in texte


def test_api_pdf_scope_societe_et_lecture_autorisee(api):
    client, _, identity = api
    row = client.post('/api/etats/liasse/balance/dossiers', json=donnees()).json()
    identity['role'] = 'lecture'
    response = client.get(f"/api/etats/liasse/balance/dossiers/{row['id']}/pdf")
    assert response.status_code == 200 and response.headers['content-type'] == 'application/pdf'
    assert response.content.startswith(b'%PDF-')
    identity.update(id=2, societe_id=2)
    assert client.get(f"/api/etats/liasse/balance/dossiers/{row['id']}/pdf").status_code == 404
