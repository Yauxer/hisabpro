"""Variante annuelle chiffrée indépendante : vrais écrans, HTTP et PostgreSQL nonce."""
from contextlib import contextmanager
from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path
import hashlib
import json

from test_e2e_cahier_tva_echeances795_isole import (
    pytest, application, application103, application102, application101,
    application100, application099, application098, application097,
    application093, application092, application091, application090,
    application089, application087, migration, laboratoire, referentiels,
    DATA, ok, capital, acquisition, semestre, annuel, cloturer_cahier, tva_mensuelle,
)
from cahier_cycle775_support import OPS, payer, identifiants, valider_journal
from cahier_semestre789_support import manuelle
from cahier_suite777_support import core

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/recette/jeu_donnees_recette.json'
VARIANTE = ROOT / 'docs/recette/DONNEES_ENCAISSEMENTS_953.json'


@contextmanager
def donnees_encaissements():
    """Remplace seulement les entrées/oracles du banc, jamais le calcul applicatif."""
    empreinte = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    original, operations = deepcopy(DATA), deepcopy(OPS)
    try:
        DATA.clear(); DATA.update(json.loads(VARIANTE.read_text(encoding='utf8')))
        OPS.clear(); OPS.update({o['reference_recette']: o for o in DATA['operations']})
        yield
    finally:
        DATA.clear(); DATA.update(original)
        OPS.clear(); OPS.update(operations)
        assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == empreinte


def verifier_mois(api, mois, annee=2025):
    return ok(api.get('/api/tva/declaration', params={'exercice': annee, 'mois': mois}))


@pytest.mark.parametrize('largeur', [1440, 390])
def test_953_annee_encaissements_cloture_et_recouvrement_suivant(application, largeur, tmp_path):
    with donnees_encaissements(), laboratoire(application, largeur, tmp_path, 'encaissements953') as (api, page, sid, preuve):
        preuve['variante953_sha256'] = hashlib.sha256(VARIANTE.read_bytes()).hexdigest()
        tiers, articles = referentiels(api, page, application, sid, preuve)
        b = DATA['banque']
        banque = ok(api.post('/api/banques', json={'banque': b['banque'], 'rib': b['rib'], 'compte_comptable': '5141', 'devise': 'MAD'}), 201)
        capital(page, application, sid, preuve)
        immo = acquisition(api, page, application, sid, tiers['F-IMMO'], preuve)
        semestre(api, page, application, sid, tiers, articles, banque, preuve, tmp_path,
                 apres_effet_client=lambda: manuelle(page, application, sid, 'TVA-05', preuve),
                 accord_compensation='REC-COMP01')
        # Refuser de continuer l'année si le calendrier indépendant ne recoupe pas l'API.
        for attendu in DATA['tva_mois'][:6]:
            mois = int(attendu['mois']); declaration = verifier_mois(api, mois)
            assert D(str(declaration['collectee']['total'])) == D(attendu['collectee']), (mois, declaration['collectee'], attendu)
        annuel(api, page, application, sid, tiers, articles, banque, immo, preuve)
        cloturer_cahier(api, page, application, sid, preuve)
        tva_mensuelle(api, page, application, sid, preuve, tmp_path)
        factures = ok(api.get('/api/factures', params={'exercice': 2025}))
        assert all(f['regime_tva'] == 'encaissement' for f in factures if f['type'] == 'vente')
        avant = core(application, sid)
        snapshot = ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot']
        # La facture appartient à2025 ; le règlement est daté en2026 ouvert.
        page.goto(application['web_url'] + '/cloture')
        page.get_by_label('Exercice actif', exact=True).select_option('2025')
        impayee = next(f for f in factures if f['tiers_id'] == tiers['C-IMPAYE']['id'])
        ids = identifiants(application, sid)
        payer(page, application, impayee, tiers['C-IMPAYE'], 14400, '2026-01-15', 'REC953-IMPAYEE', banque)
        page.goto(application['web_url'] + '/cloture')
        page.get_by_label('Exercice actif', exact=True).select_option('2026')
        valider_journal(page, application, 1)
        assert len(identifiants(application, sid) - ids) == 1
        situation = ok(api.get(f'/api/factures/{impayee["id"]}/reglements'))
        assert situation['solde_restant'] == 0 and situation['total_encaisse'] == 14400
        jan = verifier_mois(api, 1, 2026); dec = verifier_mois(api, 12)
        assert D(str(jan['collectee']['total'])) == D('2400') and D(str(jan['tva_due'])) == D('2400')
        assert D(str(dec['collectee']['total'])) == D(str(dec['tva_due'])) == 0
        assert all(e in core(application, sid) for e in avant)
        assert ok(api.get('/api/fiscalite/is/2025'))['liquidation']['snapshot'] == snapshot
        preuve['encaissements953'] = {'operations2025': 50, 'lignes2025': 118, 'collectee2025': '31500.00',
            'recuperable2025': '11600.00', 'due2025': '19900.00', 'recouvrement2026': situation,
            'janvier2026': jan, 'decembre2025': dec, 'originaux_inchanges': True, 'snapshot_inchange': True}
