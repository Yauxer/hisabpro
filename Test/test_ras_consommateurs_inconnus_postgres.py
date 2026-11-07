"""Les consommateurs ne transforment pas une RAS historique inconnue en zéro."""
from contextlib import closing
from datetime import date
from io import BytesIO
import pytest
from pypdf import PdfReader
from sqlalchemy.orm import Session
import models
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_e2e_acompte_fournisseur_isole import ok
from test_e2e_avoir_fournisseur_isole import originaux


@pytest.mark.parametrize('nature', ['vente', 'achat'])
def test_dashboard_pdf_gardent_solde_inconnu(application, nature):
    with closing(client(application)[0]) as api:
        ec = ok(api.post('/api/ecritures', json={'date': date.today().isoformat(), 'journal': 'OD',
            'reference': 'DIAGNOSTIC-CAPITAL-FICTIF', 'libelle': 'Capital fictif de contrôle',
            'lignes': [{'compte': '5141', 'debit': 100}, {'compte': '1111', 'credit': 100}]}), 201)
        ok(api.post(f"/api/ecritures/{ec['id']}/valider"))
        tid = ok(api.post('/api/tiers', json={'nom': 'Tiers diagnostic fictif', 'type': 'les_deux'}), 201)['id']
        f = ok(api.post('/api/factures', json={'type': nature, 'date': date.today().isoformat(),
            'tiers': 'Tiers diagnostic fictif', 'tiers_id': tid, 'reference': 'LEGACY-DIAGNOSTIC',
            'lignes': [{'description': 'Service fictif', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}]}), 201)
        with Session(application['engine']) as db:
            legacy = db.get(models.Facture, f['id'])
            legacy.ras_taux = float('nan'); legacy.numero = 'LEGACY-DIAGNOSTIC-' + str(f['id'])
            legacy.est_validee = True; sid = legacy.societe_id; db.commit()
        avant = originaux(application, sid)
        dashboard = ok(api.get('/api/dashboard/commercial', params={'exercice': date.today().year}))
        domaine = 'clients' if nature == 'vente' else 'fournisseurs'
        assert dashboard['resume']['encours_' + domaine] is None
        assert dashboard['resume']['retard_' + domaine] is None
        assert dashboard['resume']['calcul_incomplet_' + domaine]
        if nature == 'vente':
            assert dashboard['resume']['taux_recouvrement_clients'] is None
            assert dashboard['resume']['nb_clients_en_retard'] is None
        top = next(x for x in dashboard['top_' + domaine] if x['tiers_id'] == tid)
        assert top['encours'] is None and top['retard_max'] is None and top['encours_anomalie']
        assert any(x['id'] == f['id'] and x['ras_anomalie'] for x in dashboard['diagnostics_ras'])
        pdf = api.get('/api/ecritures/reporting/balance/pdf', params={'exercice': date.today().year,
            'genre': 'agee', 'date_from': f'{date.today().year}-01-01', 'date_to': date.today().isoformat(),
            'type_tiers': 'client' if nature == 'vente' else 'fournisseur'})
        assert pdf.status_code == 200, pdf.text
        texte = ' '.join(' '.join(p.extract_text() or '' for p in PdfReader(BytesIO(pdf.content)).pages).split())
        assert 'LEGACY-DIAGNOSTIC-' in texte and 'RAS historique invalide' in texte
        assert 'À vérifier' in texte and 'TOTAL GÉNÉRAL' in texte
        assert 'Aucune ligne pour cette sélection' not in texte
        generale = api.get('/api/ecritures/reporting/balance/pdf', params={'exercice': date.today().year,
            'genre': 'generale', 'date_from': f'{date.today().year}-01-01', 'date_to': date.today().isoformat()})
        assert generale.status_code == 200
        normal = ' '.join(p.extract_text() or '' for p in PdfReader(BytesIO(generale.content)).pages)
        assert '100,00' in normal and 'À vérifier' not in normal
        assert originaux(application, sid) == avant
        with Session(application['engine']) as db:
            import math
            assert math.isnan(db.get(models.Facture, f['id']).ras_taux)
