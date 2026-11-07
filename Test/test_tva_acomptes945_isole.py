"""TVA des acomptes : vraie API et PostgreSQL nonce, aucune base utilisateur."""
from contextlib import closing
from decimal import Decimal
import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session
import models
from test_balance_etic_notes693_isole import (
    application, application103, application102, application101, application100,
    application099, application098, application097, application093, application092,
    application091, application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from cahier_formulaires773_support import DATA, ok
from cahier_suite777_support import core
from postgres_isole import verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]


def dossier(api, app, regime='encaissement', nature='client'):
    c = app['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    sid = ok(api.patch('/api/societe/moi', json={'exercice_debut': 2025, 'regime_tva': regime}))['id']
    tiers = ok(api.post('/api/tiers', json={'nom': 'Tiers FICTIF945',
        'type': nature, 'categorie_fiscale': 'particulier' if nature == 'client' else 'professionnel'}), 201)
    banque = ok(api.post('/api/banques', json={**DATA['banque'], 'compte_comptable': '5141', 'devise': 'MAD'}), 201)
    return sid, tiers, banque


def acompte(api, tiers, banque, mode='cheque', jour='2025-06-01', montant=24000, nature='client'):
    return ok(api.post('/api/acomptes', json={'type': nature, 'tiers': tiers['nom'],
        'tiers_id': tiers['id'], 'date': jour, 'montant': montant, 'mode': mode,
        'compte_bancaire_id': banque['id'], 'reference': 'AC-FICTIF945', 'taux_tva': 20,
        'date_echeance': '2025-07-05' if mode == 'effet' else None}), 201)


def declaration(api, mois=None):
    return ok(api.get('/api/tva/declaration', params={'exercice': 2025, **({'mois': mois} if mois else {})}))


def montant(data, nature='collectee'):
    return Decimal(str(data[nature]['total']))


@pytest.mark.parametrize('mode', ['cheque', 'effet'])
def test_945_acompte_en_attente_puis_encaisse_dans_le_bon_mois(application, mode):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application)
        ac = acompte(api, tiers, banque, mode)
        assert ac['statut_paiement'] == 'en_attente' and ac['date_encaissement'] is None
        avant = core(application, sid)
        juin = declaration(api, 6)
        assert montant(juin) == 0, juin
        assert core(application, sid) == avant
        ok(api.post(f'/api/acomptes/{ac["id"]}/statut-paiement',
                    json={'statut': 'encaisse', 'date_operation': '2025-07-05'}))
        apres_encaissement = core(application, sid)
        assert montant(declaration(api, 6)) == 0
        juillet = declaration(api, 7)
        assert montant(juillet) == 4000 and montant(declaration(api)) == 4000
        assert core(application, sid) == apres_encaissement
        (ROOT/f'.codex-tests/tva945_{mode}.json').write_text(json.dumps({
            'nonce': application['cluster']['nonce'], 'juin': juin, 'juillet': juillet,
            'montant_ttc': 24000, 'date_reception': '2025-06-01', 'date_effective': '2025-07-05',
            'lectures_sans_mutation_comptable': True,
        }, ensure_ascii=False, indent=2), encoding='utf8')


def test_945_acompte_rejete_sans_encaissement_non_taxable(application):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application)
        ac = acompte(api, tiers, banque)
        ok(api.post(f'/api/acomptes/{ac["id"]}/statut-paiement',
                    json={'statut': 'rejete', 'date_operation': '2025-06-05'}))
        avant = core(application, sid)
        assert montant(declaration(api, 6)) == 0
        assert montant(declaration(api)) == 0 and core(application, sid) == avant


def test_945_virement_immediat_conserve_tva_acompte(application):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application)
        ac = acompte(api, tiers, banque, mode='virement')
        assert ac['statut_paiement'] == 'encaisse' and ac['date_encaissement'] == '2025-06-01'
        avant = core(application, sid)
        assert montant(declaration(api, 6)) == 4000
        assert montant(declaration(api, 7)) == 0 and core(application, sid) == avant


@pytest.mark.parametrize('mode,attendu', [('cheque', 0), ('virement', 4000)])
def test_945_date_historique_inconnue_signalee_sans_reparation(application, mode, attendu):
    with closing(client(application)[0]) as api:
        sid, tiers, banque = dossier(api, application)
        ac = acompte(api, tiers, banque, mode=mode)
        if mode == 'cheque':
            ok(api.post(f'/api/acomptes/{ac["id"]}/statut-paiement',
                        json={'statut': 'encaisse', 'date_operation': '2025-06-05'}))
        # Simulation explicite d'une ancienne source incomplète, uniquement nonce.
        with Session(application['engine']) as db:
            source = db.get(models.Acompte, ac['id'])
            source.date_encaissement = None
            db.commit()
        avant = core(application, sid)
        vue = declaration(api, 6)
        assert montant(vue) == attendu
        if mode == 'cheque':
            assert any(ac['numero'] in a and 'date' in a and 'qualifier' in a for a in vue['alertes'])
        with Session(application['engine']) as db:
            source = db.get(models.Acompte, ac['id'])
            assert source.date_encaissement is None and source.statut_paiement == 'encaisse'
        assert core(application, sid) == avant
