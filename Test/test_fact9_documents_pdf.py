from datetime import date
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
if str(BACK) not in sys.path:
    sys.path.insert(0, str(BACK))

from pdf_generator import generer_document
from services.document_pdf_service import resume_tva_depuis_lignes


def _societe():
    return SimpleNamespace(
        raison_sociale='HisabPro Démo SARL', forme_juridique='SARL', capital_social=100000,
        ice='001234567890123', identifiant_fiscal='12345678', rc='12345', patente='98765432',
        cnss_numero='1234567', adresse='12 rue Exemple', ville='Casablanca', pays='Maroc',
        telephone='+212500000000', email='contact@example.ma', site_web='example.ma',
        banque='Banque Démo', agence='Centre', rib='011 000 000000000000000000', logo_url=None,
    )


def test_pdf_facture_professionnel_genere_et_lisible():
    pdf = generer_document(
        _societe(), titre='FACTURE', numero='FA-2026-001', date_doc=date(2026, 9, 11),
        tiers='Client & Fils', label_tiers='CLIENT',
        tiers_infos={'nom': 'Client & Fils', 'ice': '009876543210123', 'adresse': '1 avenue Test', 'ville': 'Rabat', 'email': 'client@test.ma'},
        meta=[('Référence', 'CMD-001'), ('Échéance', '11/10/2026')],
        lignes=[
            {'description': 'Service <Conseil>', 'quantite': 2, 'prix_unitaire': 1000, 'remise': 5, 'remise2': 2, 'rabais': 0, 'tva': 20, 'qualification_tva': 'taxable', 'total_ht': 1862},
            {'description': 'Prestation exonérée', 'quantite': 1, 'prix_unitaire': 500, 'remise': 0, 'remise2': 0, 'rabais': 0, 'tva': 0, 'qualification_tva': 'exonere_sans_deduction', 'total_ht': 500},
        ],
        totaux=[('Net commercial HT', 2362, False), ('Total TVA', 372.4, False), ('TOTAL TTC', 2734.4, True)],
        resume_tva=[{'label': 'TVA 20 %', 'base': 1862, 'tva': 372.4}, {'label': 'Exonérée sans droit à déduction', 'base': 500, 'tva': 0}],
        echeancier=[
            {'ordre': 1, 'date_echeance': date(2026, 9, 11), 'libelle': 'Acompte', 'montant': 1000},
            {'ordre': 2, 'date_echeance': date(2026, 10, 11), 'libelle': 'Solde', 'montant': 1734.4},
        ],
        conditions='Paiement en deux échéances', rib=True, mention_lettres=2734.4,
        mentions=['Exonérée sans droit à déduction'], notes='Merci pour votre confiance.', statut='VALIDÉE',
    )
    assert pdf.startswith(b'%PDF')
    assert len(pdf) > 3000


def test_pdf_bl_double_exemplaire_produit_deux_pages_minimum():
    from pypdf import PdfReader
    pdf = generer_document(
        _societe(), titre='BON DE LIVRAISON', numero='BL-2026-001', date_doc=date(2026, 9, 11),
        tiers='Client', label_tiers='CLIENT', lignes=[{'description': 'Article A', 'quantite_prevue': 3, 'quantite_livree': 2}],
        colonnes='livraison', exemplaires=['EXEMPLAIRE CLIENT', 'EXEMPLAIRE ARCHIVE'],
        libelles_livraison=('Qté commandée', 'Qté livrée'), signature_labels=('Livré par', 'Reçu par'),
    )
    reader = PdfReader(BytesIO(pdf))
    assert len(reader.pages) >= 2


def test_resume_tva_pdf_ne_confond_pas_zero_et_exoneration():
    rows = resume_tva_depuis_lignes([
        {'total_ht': 100, 'tva': 20, 'qualification_tva': 'taxable'},
        {'total_ht': 50, 'tva': 0, 'qualification_tva': 'hors_champ'},
    ])
    labels = {r['label'] for r in rows}
    assert 'TVA 20 %' in labels
    assert 'Hors champ TVA' in labels


def test_routes_pdf_fact9_couvrent_tous_documents_commerciaux():
    commercial = (BACK / 'routers' / 'commercial.py').read_text(encoding='utf-8')
    factures = (BACK / 'routers' / 'factures.py').read_text(encoding='utf-8')
    avoirs = (BACK / 'avoirs.py').read_text(encoding='utf-8')
    assert '@router_devis.get("/{devis_id}/pdf")' in commercial
    assert '@router_bc.get("/{bc_id}/pdf")' in commercial
    assert '@router_bl.get("/{bl_id}/pdf")' in commercial
    assert '@router_br.get("/{br_id}/pdf")' in commercial
    assert '@router.get("/{facture_id}/pdf")' in factures
    assert '@router.get("/{avoir_id}/pdf")' in avoirs


def test_facture_pdf_inclut_echeancier_et_resume_tva():
    src = (BACK / 'routers' / 'factures.py').read_text(encoding='utf-8')
    assert 'echeances_persistantes_ou_defaut(facture, total_ttc)' in src
    assert 'resume_tva_depuis_ventilation(ventilation_pdf)' in src
    assert 'conditions_paiement(facture.delai_paiement, date_echeance,' in src
    assert 'mode_reglement_prevu' in src
    assert 'reference_reglement_prevue' in src


def test_bc_et_br_ne_sont_plus_marques_pdf_bientot_disponible():
    src = (ROOT / 'src' / 'pages' / 'Commercial.jsx').read_text(encoding='utf-8')
    assert '/api/bons-commande/${bc.id}/pdf' in src
    assert '/api/bons-reception/${br.id}/pdf' in src
    assert 'Imprimer PDF — bientôt disponible' not in src


def test_preparation_email_telecharge_dabord_le_pdf():
    src = (ROOT / 'src' / 'services' / 'documentsCommerciaux.js').read_text(encoding='utf-8')
    assert 'await telechargerDocumentPDF(endpoint, nomFichier)' in src
    assert 'mailto:' in src
    assert '/api/tiers/${tiersId}' in src


def test_avoirs_exposent_tiers_id_et_pdf():
    schemas = (BACK / 'schemas.py').read_text(encoding='utf-8')
    avoirs = (BACK / 'avoirs.py').read_text(encoding='utf-8')
    front = (ROOT / 'src' / 'pages' / 'Avoirs.jsx').read_text(encoding='utf-8')
    section = schemas[schemas.index('class AvoirOut'):schemas.index('class FactureOut')]
    assert 'tiers_id:' in section
    assert '"tiers_id": facture_tiers_id' in avoirs
    assert '/api/avoirs/${selectionne.id}/pdf' in front
