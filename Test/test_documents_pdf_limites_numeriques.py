"""PDF de devis/BC : chiffres et diagnostic sans erreur, API/PG nonce réels."""
from datetime import date
from io import BytesIO
import pytest
from pypdf import PdfReader
from test_devis_stock_diagnostic import application, dossier, etat
from test_bc_bl_totaux_finis import snapshot


@pytest.mark.parametrize('route', ['/api/devis', '/api/bons-commande'])
@pytest.mark.parametrize('ht', [100, 1e13, 1e308])
def test_pdf_chiffres_finis_lisible_sans_mutation(application, dossier, route, ht):
    api = dossier[0]
    r = api.post(route, json={'date': date.today().isoformat(), 'tiers': 'Tiers fictif PDF',
        'lignes': [{'description': 'Prestation fictive PDF limites', 'quantite': 1,
                    'prix_unitaire': ht, 'tva': 20}]})
    assert r.status_code == 201, r.text
    avant = etat(application), snapshot(application)
    pdf = api.get(route + '/' + str(r.json()['id']) + '/pdf')
    assert pdf.status_code == 200, pdf.text if pdf.status_code != 200 else ''
    assert pdf.content.startswith(b'%PDF') and 'application/pdf' in pdf.headers['Content-Type']
    texte = ' '.join(' '.join(p.extract_text() for p in PdfReader(BytesIO(pdf.content)).pages).split())
    assert 'TOTAL TTC' in texte and 'Total TVA' in texte
    assert 'nan' not in texte.lower() and 'infini' not in texte.lower()
    if ht == 100:
        assert '120,00' in texte and 'cent vingt dirhams' in texte
    else:
        assert 'Montant en lettres indisponible' in texte
    # Chiffres affichés : comparaison à l'oracle float finie existante,
    # sans recomposer le montant depuis un texte en lettres indisponible.
    from pdf_generator import fmt_mad
    sans_espaces = ''.join(texte.split())
    assert ''.join(fmt_mad(ht).split()) in sans_espaces
    assert ''.join(fmt_mad(ht * .2).split()) in sans_espaces
    assert ''.join(fmt_mad(ht + ht * .2).split()) in sans_espaces
    assert (etat(application), snapshot(application)) == avant


@pytest.mark.parametrize('montant,attendu', [(0, 'zéro dirham'), (100, 'cent dirhams'),
                                           (120, 'cent vingt dirhams'), (120.25, 'cent vingt dirhams et vingt-cinq centimes')])
def test_lettres_montants_usuels_conservent_texte_exact(montant, attendu):
    from pdf_generator import montant_en_lettres
    assert montant_en_lettres(montant) == attendu


@pytest.mark.parametrize('montant', [1e13, 1e308])
def test_grande_magnitude_diagnostic_sans_texte_invente(montant):
    from pdf_generator import montant_en_lettres
    assert montant_en_lettres(montant).startswith('Montant en lettres indisponible')


def test_limite_convertisseur_historique_normale_conservee():
    from pdf_generator import montant_en_lettres
    texte = montant_en_lettres(999999999999)
    assert texte.startswith('neuf cent quatre-vingt-dix-neuf milliards')
    assert texte.endswith('dirhams') and 'indisponible' not in texte


@pytest.mark.parametrize('montant', [float('nan'), float('inf'), float('-inf')])
def test_non_fini_diagnostic_pas_zero_invente(montant):
    from pdf_generator import montant_en_lettres
    texte = montant_en_lettres(montant)
    assert texte.startswith('Montant en lettres indisponible')
    assert 'zéro' not in texte
