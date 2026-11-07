# -*- coding: utf-8 -*-
"""Patch 061 — suppression du blocage global d'identité à la validation.

Les avis ne valent pas attestation de conformité de la facture à la loi.
"""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
BACK = ROOT / 'hisabpro-backend'
sys.path.insert(0, str(BACK))
from services.mentions_identite_facture_service import mentions_identite_manquantes


def societe_complete():
    return SimpleNamespace(raison_sociale='HISABPRO TEST', identifiant_fiscal='12345678',
                           ice='123456789012345', patente='123456',
                           adresse='1 rue exemple', ville='Rabat')


def client_complet():
    return SimpleNamespace(adresse='2 rue exemple', categorie_fiscale='professionnel',
                           ice='123456789012346')


def test_061_complet_aucun_avis():
    assert mentions_identite_manquantes(societe_complete(), client_complet()) == []


def test_061_mentions_societe_absentes_sont_signalees_sans_exception():
    s = societe_complete()
    s.identifiant_fiscal = None
    s.ice = ''
    s.patente = None
    s.adresse = None
    avis = mentions_identite_manquantes(s, client_complet())
    assert avis == ['Société : IF', 'Société : ICE', 'Société : TP/patente', 'Société : adresse']


def test_061_ice_adresse_client_professionnel_avertissements():
    c = client_complet()
    c.ice = None
    c.adresse = ''
    avis = mentions_identite_manquantes(societe_complete(), c)
    assert avis == ['Client : adresse', 'Client professionnel : ICE']


def test_061_facture_achat_sans_avertissement_identite_de_vente():
    assert mentions_identite_manquantes(SimpleNamespace(), est_vente=False) == []


def test_061_validation_et_conversion_fournissent_avis_sans_blocage():
    src = (BACK / 'routers' / 'factures.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    func = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_figer_identites_facture')
    bloc = ast.get_source_segment(src, func)
    assert 'Complétez l\'identité de la société avant d\'émettre' not in bloc
    assert "L'ICE est requis sur la fiche d'un client professionnel" not in bloc
    assert 'mentions_identite_manquantes(' in bloc
    assert 'societe_snapshot_json = json.dumps(' in bloc
    assert 'Sélectionnez un client enregistré avant de valider' in bloc
    assert src.count('"avertissements_mentions": avertissements_mentions') == 3
    assert '_verifier_date_facture_finale' in src
    assert 'figer_comptes_facture' in src


def test_061_ui_affiche_un_avis_non_bloquant_apres_validation():
    src = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
    assert 'const validation = await validerFacture(facture.id)' in src
    assert 'setAvertissementsMentions' in src
    assert 'mentions à compléter avant envoi' in src
    assert 'Vérifiez la fiche société et la fiche client' in src
    assert "le brouillon a bien été enregistré" not in src.lower() or 'finalisation' in src
