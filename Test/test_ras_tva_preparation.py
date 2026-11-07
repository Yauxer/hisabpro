"""Calendrier et montants attendus indépendants, sans accès à une base."""
from copy import deepcopy
import pytest
from services.ras_tva_preparation_service import selectionner, mois_paiement


def ligne(identifiant=1, **kw):
    return {'capture_id': identifiant, 'nature': 'achat', 'date_paiement': '2026-12-31',
        'retenue_tva': '75.00', 'od_validee': True, 'annulation_id': None,
        'mois_reversement_prevu': '2027-01', 'diagnostics': [], **kw}


def source(rows, disponible=True):
    return {'societe_id': 3, 'societe': {'raison_sociale': 'Fictif593'},
        'disponible': disponible, 'migration_requise': None if disponible else '099_ras_tva_details.sql', 'lignes': rows}


@pytest.mark.parametrize('annee,mois,attendu', [(2027,1,'2026-12'),(2026,11,'2026-10'),(2028,3,'2028-02')])
def test_calendrier_paiements_du_mois_precedent(annee,mois,attendu):
    assert mois_paiement(annee,mois)==attendu


def test_decembre_janvier_pas_de_vente_ni_deduction_automatique_annulation():
    s=source([ligne(),ligne(2,retenue_tva='0.01',od_validee=False),
        ligne(3,annulation_id=7,date_annulation='2027-04-01'),ligne(4,nature='vente'),
        ligne(5,date_paiement='2026-11-30',mois_reversement_prevu='2026-12')])
    avant=deepcopy(s);d=selectionner(s,2027,1)
    assert s==avant
    assert [r['capture_id'] for r in d['lignes']]==[1,2,3]
    assert {k:v['montant'] for k,v in d['totaux']['achat'].items()}=={
        'saisies':'150.01','actives':'75.01','validees':'75.00','annulees':'75.00'}
    assert 'vente' not in d['totaux'] and 'postérieures' in d['note']
    assert selectionner(s,2027,2)['totaux']['achat']['actives']['montant']=='0.00'


def test_inconnu_ne_devient_pas_zero_et_mois_incoherent_visible():
    d=selectionner(source([ligne(retenue_tva=None,mois_reversement_prevu='2027-02'),ligne(2)]),2027,1)
    assert d['totaux']['achat']['actives']=={'montant':None,'partie_certaine':'75.00','nombre':2}
    assert d['lignes'][0]['diagnostics'] and d['lignes'][0]['mois_reversement_prevu']=='2027-02'
    assert selectionner(source([],False),2027,1)['totaux'] is None


def test_empreinte_portee_identite_periode_et_etat():
    s=source([ligne()]);a=selectionner(s,2027,1)['empreinte_sha256']
    assert selectionner(deepcopy(s),2027,1)['empreinte_sha256']==a
    assert selectionner(s,2027,2)['empreinte_sha256']!=a
    s['lignes'][0]['od_validee']=False
    assert selectionner(s,2027,1)['empreinte_sha256']!=a
    s['lignes'][0]['od_validee']=True;s['societe_id']=4
    assert selectionner(s,2027,1)['empreinte_sha256']!=a
