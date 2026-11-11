"""977 — une caisse ne peut jamais être créditrice. Scénario du partenaire rejoué sur PostgreSQL nonce, données fictives."""
from decimal import Decimal
from test_e2e_facturation_isole import application  # noqa: F401
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hisabpro-backend'))
from services.liasse_service import calculer_bilan, caisses_creditrices  # noqa: E402

JOUR = '2026-11-11'


def ecriture(api, montant, *, debit, credit, valider, journal='CA', jour=JOUR):
    return api.post('/api/ecritures', json={'date': jour, 'journal': journal, 'libelle': f'Mouvement fictif977 {montant}', 'est_validee': valider,
                                           'lignes': [{'compte': debit, 'libelle': 'Débit fictif', 'debit': montant, 'credit': 0},
                                                      {'compte': credit, 'libelle': 'Crédit fictif', 'debit': 0, 'credit': montant}]})


def reglement(api, f, montant):
    return api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': f['tiers'], 'date': JOUR, 'montant': montant,
                                             'mode': 'especes', 'reference': f'ESP-977-{montant}', 'comptabiliser': True})


def test_977_caisse_jamais_creditrice(application):
    api, _, _ = client(application)
    try:
        t = ok(api.post('/api/tiers', json={'nom': 'Hamid Bois fictif977', 'type': 'fournisseur'}), 201)
        f = ok(api.post('/api/factures', json={'type': 'achat', 'tiers': t['nom'], 'tiers_id': t['id'], 'date': JOUR, 'ras_taux': 0, 'reference': 'FA-HB-977',
               'lignes': [{'description': 'Bois fictif977', 'quantite': 1, 'prix_unitaire': 50000, 'tva': 20}]}), 201)
        ok(api.post(f"/api/factures/{f['id']}/valider")); ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
        # Scénario du partenaire : caisse vide, règlement en espèces de 60 000 → refusé avec un message clair.
        r = reglement(api, f, 60000)
        assert r.status_code == 409 and 'Caisse insuffisante (5161)' in r.json()['detail'] and 'solde disponible 0,00 DH' in r.json()['detail'], r.text
        # Alimentation de la caisse (apport de 100 000), puis le même règlement passe et se valide.
        ok(ecriture(api, 100000, debit='5161', credit='1111', valider=True), 201)
        reg = ok(reglement(api, f, 60000), 201)
        ecr = reg.get('ecriture_id') or ok(api.get(f"/api/reglements/{reg['id']}")).get('ecriture_id')
        ok(api.post(f'/api/ecritures/{ecr}/valider'))
        # Solde 40 000 : une sortie manuelle validée de 50 000 est refusée, une de 40 000 passe.
        r = ecriture(api, 50000, debit='6111', credit='5161', valider=True)
        assert r.status_code == 409 and 'solde disponible 40 000,00 DH' in r.json()['detail'], r.text
        # Un brouillon qui viderait trop la caisse est refusé à la validation en lot, avec le motif.
        b = ok(ecriture(api, 45000, debit='6111', credit='5161', valider=False), 201)
        lot = ok(api.post('/api/ecritures/valider-lot', json={'ids': [b['id']]}))
        assert lot['nb_validees'] == 0 and 'Caisse insuffisante' in str(lot['refusees']), lot
        ok(ecriture(api, 40000, debit='6111', credit='5161', valider=True), 201)
        # Une sortie antérieure qui rendrait la caisse créditrice plus tard est aussi refusée.
        r = ecriture(api, 1, debit='6111', credit='5161', valider=True, jour='2026-11-12')
        assert r.status_code == 409
        # Une entrée reste toujours possible.
        ok(ecriture(api, 500, debit='5161', credit='1111', valider=True), 201)
    finally:
        api.close()


def test_977_bilan_banque_creditrice_au_passif_et_caisse_signalee():
    soldes = {'5141': {'debit': Decimal('0'), 'credit': Decimal('3000')}, '51411': {'debit': Decimal('2000'), 'credit': Decimal('0')},
              '5161': {'debit': Decimal('0'), 'credit': Decimal('600')}, '1111': {'debit': Decimal('0'), 'credit': Decimal('0')}}
    b = calculer_bilan(soldes, Decimal('0'))
    treso = {l['code']: l for l in b['actif']['tresorerie']}
    passif = {l['code']: l for l in b['passif']['tresorerie']}
    assert Decimal(str(treso['514']['brut'])) == Decimal('2000.00')       # banque débitrice seule à l'actif
    assert Decimal(str(passif['554']['montant'])) == Decimal('3000.00')   # banque à découvert au passif
    assert caisses_creditrices(soldes) == {'5161': Decimal('600.00')}
    assert caisses_creditrices({'5161': {'debit': Decimal('10'), 'credit': Decimal('0')}}) == {}
