"""Oracle indépendant des exports de préparation ; aucune base réelle."""
from copy import deepcopy
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import text, update

import models
from services.balance_import_service import preparer_balance_liasse, empreinte_preparation
from services.balance_preparation_export_service import presentation_bilan, generer_preparation_xlsx
from services.balance_preparation_pdf import generer_preparation_pdf
from test_balance_preparations import api, donnees
from test_logo_societe import image_data


def lignes(diviseur=1):
    debit = {'2311':1000, '2321':2000, '2331':3000, '2340':4000, '2351':5000,
             '2380':6000, '3111':7000, '3421':8000, '5141':14000, '6111':1000}
    credit = {'28321':300, '1111':44700, '7111':6000}
    return ([{'compte': c, 'debit': str(Decimal(v) / diviseur), 'credit':'0.00'} for c, v in debit.items()] +
            [{'compte': c, 'debit':'0.00', 'credit':str(Decimal(v) / diviseur)} for c, v in credit.items()])


def dossier(comparatif=True):
    n, n1 = lignes(), lignes(2) if comparatif else None
    contenu = {'schema_version':1, 'exercice':2026,
        'periode':{'debut':'2025-07-01', 'fin':'2026-06-30'},
        'sources':{'n':n, 'n1':n1, 'noms_fichiers':{'n':'=SOURCE("N")', 'n1':'<historique> & N-1.xlsx'}},
        'preparation':preparer_balance_liasse(n, n1, {r['compte'] for r in n})}
    return {'id':42, 'exercice':2026, 'version':3, 'created_at':'2026-10-20T12:30:00',
            'contenu':contenu, 'empreinte_sha256':empreinte_preparation(contenu)}


def societe(logo=False):
    return SimpleNamespace(raison_sociale='=SOCIETE <fictive> & associés',
                           logo_url=image_data('PNG', (20,12)) if logo else None)


def test_677_detail_brut_amort_net_et_comparatif_sans_recalcul_mutation():
    row = dossier(); avant = deepcopy(row)
    detail = presentation_bilan(row)['actif']
    assert detail[-1]['valeurs'] == [50000, 300, 49700, 24850]
    assert next(r for r in detail if r.get('numero') == 'C')['valeurs'] == [21000, 300, 20700, 10350]
    for code, brut in [('231',1000),('232',2000),('233',3000),('234',4000),('235',5000),('238',6000)]:
        assert next(r for r in detail if r.get('numero') == code)['valeurs'] == [brut, None, None, None]
    assert row['contenu']['preparation']['etats']['cpc']['resultat_net'] == 5000
    assert row == avant and empreinte_preparation(row['contenu']) == row['empreinte_sha256']


@pytest.mark.parametrize('comparatif', [True, False])
def test_677_excel_sources_chiffres_provenance_logo_et_formules_inertes(comparatif):
    row = dossier(comparatif); avant = deepcopy(row)
    contenu = generer_preparation_xlsx(row, societe(True))
    wb = load_workbook(BytesIO(contenu), data_only=False)
    infos = list(wb['Dossier'].values)
    assert ('Version conservée','3') in infos
    assert ('Période déclarée N','2025-07-01 au 2026-06-30') in infos
    assert ('Empreinte des données normalisées', row['empreinte_sha256']) in infos
    assert ('Source déclarée N','=SOURCE("N")') in infos
    assert ('Société (identité actuelle)', societe().raison_sociale) in infos
    assert all(c.data_type != 'f' for ws in wb for row_ in ws for c in row_)
    actif = list(wb['Bilan actif'].values)
    assert (None, 'TOTAL GÉNÉRAL ACTIF', 50000, 300, 49700, 24850 if comparatif else 'Indisponible') in actif
    assert next(r for r in actif if r[0] == '232')[2:] == (2000,'Indisponible','Indisponible','Indisponible')
    for cle, suffixe in [('n','N'), ('n1','N-1')]:
        sources = row['contenu']['sources'][cle]
        if sources is None:
            assert 'Balance source '+suffixe not in wb.sheetnames
        else:
            values = list(wb['Balance source '+suffixe].values)[1:]
            assert len(values) == len(sources)
            assert sum(Decimal(str(r[1])) for r in values) == sum(Decimal(str(r[2])) for r in values)
            assert values[0] == ('2311', 1000 if cle == 'n' else 500, 0)
    assert ("Résultat net de l'exercice",5000) in list(wb['CPC N'].values)
    with ZipFile(BytesIO(contenu)) as z:
        assert any(n.startswith('xl/media/') for n in z.namelist())
    assert row == avant


@pytest.mark.parametrize('comparatif', [True, False])
def test_677_pdf_details_sources_logo_et_absence_n1_explicite(comparatif):
    row = dossier(comparatif); avant = deepcopy(row)
    reader = PdfReader(BytesIO(generer_preparation_pdf(row, societe(True))))
    texte = ' '.join(' '.join(p.extract_text() for p in reader.pages).split())
    assert all(m in texte for m in ('50 000,00','49 700,00','300,00','Brut N MAD','Amort. / prov.',
        'Sous-postes pour mémoire', 'Balance source normalisée N', '28321', row['empreinte_sha256']))
    assert ('Balance source normalisée N-1' in texte) is comparatif
    assert ('24 850,00' in texte) is comparatif
    assert any(page.images for page in reader.pages)
    assert row == avant


def test_677_ancien_snapshot_sans_sources_garde_agregats_sans_sous_postes_inventes():
    row = dossier(); row['contenu']['sources'].pop('n'); row['contenu']['sources'].pop('n1')
    avant = deepcopy(row)
    detail = presentation_bilan(row)
    assert all(r['type'] != 'detail' for r in detail['actif'])
    assert detail['actif'][-1]['valeurs'] == [50000,300,49700,24850]
    texte = ' '.join(p.extract_text() for p in PdfReader(BytesIO(generer_preparation_pdf(row, societe()))).pages)
    assert 'Sources détaillées indisponibles' in texte
    wb = load_workbook(BytesIO(generer_preparation_xlsx(row,societe())))
    assert not any(n.startswith('Balance source') for n in wb.sheetnames)
    assert row == avant


def test_677_sources_n1_absentes_ne_fabriquent_pas_de_sous_postes_n1():
    row = dossier(); row['contenu']['sources'].pop('n1')
    detail = presentation_bilan(row)['actif']
    assert detail[-1]['valeurs'] == [50000,300,49700,24850]
    assert all(r['valeurs'][-1] is None for r in detail if r['type'] == 'detail')


def test_677_cpc_apres_solde_technique_reste_indisponible():
    row = dossier(False)
    n1 = [{'compte':'1111','debit':'0','credit':'100'}, {'compte':'1191','debit':'0','credit':'20'},
          {'compte':'5141','debit':'120','credit':'0'}]
    row['contenu']['preparation'] = preparer_balance_liasse(lignes(), n1, {r['compte'] for r in lignes()} | {'1191'})
    row['contenu']['sources']['n1'] = n1
    wb = load_workbook(BytesIO(generer_preparation_xlsx(row,societe())))
    rows = list(wb['CPC N-1'].values)
    assert len(rows) == 2 and rows[1][1] == 'Indisponible' and 'Classes 6/7 soldées' in rows[1][0]


def test_677_api_excel_lecture_cloisonnement_et_integrite(api):
    client, engine, identity = api
    row = client.post('/api/etats/liasse/balance/dossiers',json=donnees()).json()
    identity['role'] = 'lecture'
    path = f'/api/etats/liasse/balance/dossiers/{row["id"]}/xlsx'
    assert client.post('/api/etats/liasse/balance/dossiers',json=donnees()).status_code == 403
    with engine.connect() as db:
        avant = db.execute(text('SELECT contenu,empreinte_sha256 FROM liasse_balances_preparation')).all()
    response = client.get(path)
    assert response.status_code == 200 and response.content.startswith(b'PK')
    assert 'v1.xlsx' in response.headers['Content-Disposition']
    assert response.headers['Access-Control-Expose-Headers'] == 'Content-Disposition'
    with engine.connect() as db:
        assert db.execute(text('SELECT contenu,empreinte_sha256 FROM liasse_balances_preparation')).all() == avant
    identity.update(id=2,societe_id=2)
    assert client.get(path).status_code == 404
    identity.update(id=1,societe_id=1)
    contenu = deepcopy(row['contenu']); contenu['preparation']['pret_a_deposer'] = True
    with engine.begin() as db:
        db.execute(update(models.LiasseBalancePreparation).values(contenu=contenu))
    assert client.get(path).status_code == 409


def test_677_precision_excel_ne_tronque_pas_source_exacte():
    row = dossier(False)
    row['contenu']['sources']['n'][0]['debit'] = '1234567890123456.78'
    # Test pur du transport exact ; une telle balance est refusée à l'import.
    wb = load_workbook(BytesIO(generer_preparation_xlsx(row,societe())))
    assert wb['Balance source N']['B2'].value == '1234567890123456.78'
    assert wb['Balance source N']['B2'].data_type == 's'
