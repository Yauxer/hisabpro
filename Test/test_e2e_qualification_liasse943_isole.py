"""Exports du vrai cahier annuel ; aucune finalisation forcée de ses sources incomplètes."""
import hashlib
from decimal import Decimal
from zipfile import ZipFile

from openpyxl import load_workbook
from playwright.sync_api import expect
from pypdf import PdfReader

from test_e2e_cahier_etic805_isole import (
    pytest, application, application103, application102, application101,
    application100, application099, application098, application097,
    application093, application092, application091, application090,
    application089, application087, migration, laboratoire, referentiels,
    DATA, ok, capital, acquisition, semestre, annuel, cloturer_cahier,
    echeances_2026, completer_etic,
)
from cahier_etats803_support import telecharger, valeurs_pdf
from cahier_suite777_support import core
from test_logo_societe import image_data


@pytest.mark.parametrize('largeur', [1440, 390])
def test_943_exports_annuels_fideles_et_finalisation_non_forcee(application, largeur, tmp_path):
    with laboratoire(application, largeur, tmp_path, 'liasse943') as (api, page, sid, preuve):
        tiers, articles = referentiels(api, page, application, sid, preuve)
        b = DATA['banque']
        banque = ok(api.post('/api/banques', json={
            'banque': b['banque'], 'rib': b['rib'], 'compte_comptable': '5141', 'devise': 'MAD',
        }), 201)
        capital(page, application, sid, preuve)
        immo = acquisition(api, page, application, sid, tiers['F-IMMO'], preuve)
        semestre(api, page, application, sid, tiers, articles, banque, preuve, tmp_path)
        annuel(api, page, application, sid, tiers, articles, banque, immo, preuve)
        cloturer_cahier(api, page, application, sid, preuve)
        echeances_2026(api, page, application, sid, preuve)
        completer_etic(api, page, application, sid, preuve, tmp_path)

        # Seule l'identité de la société fictive change après les saisies du cahier.
        nom = 'ATLAS <RECETTE> & associés FICTIFS 943'
        ok(api.patch('/api/societe/moi', json={'raison_sociale': nom, 'logo_url': image_data('PNG')}))
        avant = core(application, sid)
        snapshot = ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']
        data = ok(api.get('/api/etats/liasse/2025'))
        page.reload(wait_until='domcontentloaded')
        expect(page.get_by_role('button', name='Finaliser', exact=True)).to_be_disabled()
        assert not data['controles']['pret_a_finaliser']
        assert data['etic']['progression']['completes'] == 20
        assert data['etic']['progression']['total'] == 23
        refus = api.post('/api/etats/liasse/2025/finaliser')
        assert refus.status_code == 409, refus.text
        assert data['archive'] is None

        excel = telecharger(page, 'Excel', tmp_path, 'liasse943.xlsx')
        pdf = telecharger(page, 'PDF', tmp_path, 'liasse943.pdf')
        w = load_workbook(excel, data_only=True)
        assert {'Synthese', 'T1 Bilan Actif', 'T1 Bilan Passif', 'T2 CPC', 'ESG',
                'Financement', 'Fiscal', 'ETIC'} <= set(w.sheetnames)
        synthese = list(w['Synthese'].values)
        for label, val in [('Raison sociale', nom), ('IF', data['societe']['identifiant_fiscal']),
                           ('ICE', data['societe']['ice'])]:
            assert any(r[0] == label and r[1] == val for r in synthese), (label, val)
        assert any('numérotation interne' in str(v).lower() for r in synthese for v in r)
        assert any('BLOQUANT' in r for r in synthese)

        actif = list(w['T1 Bilan Actif'].values)
        immo_row = next(r for r in actif if r[1] == 'Immobilisations corporelles')
        assert list(immo_row[2:5]) == [24000, 4800, 19200]
        assert any(r[0] == 'XV' and r[2] == 106409.75 for r in w['T2 CPC'].values)
        assert any(r[0] == 'CAF' and r[2] == 112709.75 for r in w['ESG'].values)
        assert any(r[0] == 'Non applicable' for r in w['Financement'].values)

        etic_rows = [list(r) for r in w['ETIC'].values]
        keys = ['compte', 'intitule', 'total', 'plus_un_an', 'moins_un_an', 'echues',
                'devises', 'etat_organismes_publics', 'entreprises_liees', 'effets']
        sections = {s['code']: s for s in data['etic']['sections']}
        for code in ('B6', 'B7'):
            for row in sections[code]['ventilation']:
                attendu = [row.get(k) if row.get(k) is not None else 'À compléter' for k in keys]
                assert any(r[:len(keys)] == attendu for r in etic_rows), (code, attendu)
            for erreur in sections[code]['erreurs_ventilation']:
                assert any(r[0] == 'Contrôle de ventilation' and r[1] == erreur for r in etic_rows)
        for row in sections['B12']['automatique']['lignes']:
            assert any(r[0] == row['rubrique'] and r[1] == row['montant'] for r in etic_rows), row
        assert any('À compléter' in r for r in etic_rows)
        assert any(r[0] == '4411' and r[2:6] == [480, 0, 0, 480] for r in etic_rows)
        assert {f['reference'] for f in ok(api.get('/api/factures', params={'exercice': 2025}))
                if f.get('reference') in ('02', '002')} == {'02', '002'}
        assert any('Références 02 et 002 distinctes' in str(v) for r in etic_rows for v in r)
        w.close()

        reader = PdfReader(pdf)
        texte = '\n'.join(p.extract_text() or '' for p in reader.pages)
        assert nom in texte and data['societe']['identifiant_fiscal'] in texte and data['societe']['ice'] in texte
        assert 'BLOQUANT' in texte and '20/23' in texte and 'REC-ASSOC01' in texte
        assert '02 et 002 distinctes' in ' '.join(texte.split())
        assert {Decimal(x) for x in ['337010', '106409.75', '112709.75', '24000', '4800',
                                    '19200', '133830', '27420.25']} <= valeurs_pdf(texte)
        assert any(p.images for p in reader.pages)
        with ZipFile(excel) as z:
            assert z.testzip() is None and any(n.startswith('xl/media/') for n in z.namelist())
        assert core(application, sid) == avant
        assert ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'] == snapshot
        assert ok(api.get('/api/etats/liasse/2025'))['archive'] is None
        preuve['qualification943'] = {
            'HP-LIA-001': 'Bloqué (source) : ETIC 20/23, aucune ventilation ou méthode inventée ;409.',
            'HP-LIA-002': 'Téléchargements PDF/Excel réels ;valeurs,identité,logo,notes,zéros/inconnus conservés.',
            'controles': data['controles'], 'ecritures_et_snapshot_inchanges': True,
            'exports': {p.suffix: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                                 'octets': p.stat().st_size} for p in (excel, pdf)},
        }
