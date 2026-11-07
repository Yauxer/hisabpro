"""Copies comptables fictives du cahier avant IS ; aucun dossier utilisateur restauré."""
from collections import defaultdict
from decimal import Decimal as D
from pathlib import Path
import hashlib
import json

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


def ecriture(api, ref, lignes, jour='2025-12-31', journal='OD', piece=False):
    body = {'date': jour, 'journal': journal, 'reference': ref,
            'libelle': ref + ' — copie FICTIVE947', 'lignes': lignes}
    if piece:
        body['date_piece'] = jour  # Note de synthèse fictive explicitement datée.
    e = ok(api.post('/api/ecritures', json=body), 201)
    ok(api.post(f'/api/ecritures/{e["id"]}/valider'))
    return e


def lire(api):
    return ok(api.get('/api/fiscalite/is/2025'))


def qualifier(api):
    for compte, montant, ref in [('61955', 1500, 'REC-LIT01'), ('61964', 2000, 'REC-DEP01')]:
        ok(api.post('/api/fiscalite/is/2025/retraitements', json={'type': 'reintegration',
            'categorie': 'provisions_non_deductibles', 'compte_source': compte, 'montant': montant,
            'libelle': ref + ' non admise selon hypothèse explicite du cahier', 'reference': ref}))
    assert D(str(lire(api)['calcul']['benefice_fiscal_imposable'])) == D('133830')


def credit(api):
    return ok(api.post('/api/fiscalite/is/2025/credits', json={'type': 'pprf',
        'montant': 200, 'montant_deja_impute_acomptes': 0, 'date_retenue': '2025-11-30',
        'reference': 'INT-PPRF', 'commentaire': 'Crédit FICTIF du cahier, pas de retenue réelle.'}))


def copie(api, app, *, reprise=False, minimale=False, qualifie=True, avec_credit=True):
    c = app['cluster']
    verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
    s = DATA['societe']
    profil = {k: s[k] for k in ['forme_juridique', 'ville', 'adresse', 'devise', 'regime_fiscal', 'regime_tva']}
    profil.update(raison_sociale='Copie FICTIVE947 — ' + ('reprise2024' if reprise else 'variante2025'),
                  exercice_debut=2024 if reprise else 2025)
    sid = ok(api.patch('/api/societe/moi', json=profil))['id']
    ops = [o for o in DATA['operations'] if o['reference_recette'] not in ('IS-2025', 'PPRF-IMP')]
    assert len(ops) == 48
    if minimale:
        # Note de synthèse du seul résultat, réservée aux refus fiscaux isolés.
        # Aucun prétendu stock/registre d'immobilisations ou dossier annuel complet.
        comptes = defaultdict(D)
        for o in sorted(ops, key=lambda o: o['date']):
            for l in o['lignes']:
                if l['compte'][0] in '67':
                    comptes[l['compte']] += D(l['debit']) - D(l['credit'])
        lignes = [{'compte': n, 'debit': str(max(v, 0)), 'credit': str(max(-v, 0))}
                  for n, v in comptes.items() if v]
        solde = -sum(comptes.values())
        assert solde == D('129830')
        lignes.append({'compte': '5141', 'debit': str(solde), 'credit': '0'})
        ecriture(api, 'NOTE-RESULTAT-FICTIVE947', lignes, piece=True)
    else:
        tiers = {}
        for t in DATA['tiers']:
            cle = 'compte_client' if t['type'] == 'client' else 'compte_fournisseur'
            tiers[t['code']] = ok(api.post('/api/tiers', json={
                'nom': t['nom'], 'type': t['type'], cle: t['compte']}), 201)['id']
        for o in sorted(ops, key=lambda o: o['date']):
            lignes = [{k: l[k] for k in ['compte', 'debit', 'credit']} |
                      ({'tiers_id': tiers[l['tiers']]} if l.get('tiers') else {}) for l in o['lignes']]
            ecriture(api, o['reference_recette'], lignes, o['date'], o['journal'])
    debut = lire(api)
    assert D(str(debut['calcul']['resultat_comptable_avant_is'])) == D('129830')
    assert D(str(debut['calcul']['reintegrations'])) == D('500')
    if qualifie:
        qualifier(api)
    if avec_credit:
        credit(api)
    return sid


def preuve(nom, **donnees):
    (ROOT/f'.codex-tests/fiscal947_{nom}.json').write_text(json.dumps(donnees,
        ensure_ascii=False, indent=2, default=str), encoding='utf8')


def ajouter_deficit(api):
    return ok(api.post('/api/fiscalite/deficits', json={'exercice_origine': 2024,
        'montant_ordinaire': 10000, 'montant_amortissements': 2000,
        'commentaire': 'DEF-2024 : attestation FICTIVE de reprise prévue par HP-FIS-031 ; aucune société réelle.'}))


def reprise_provision(api):
    # 71955 est une subdivision du scénario, pas un compte standard à imposer
    # globalement. Précondition explicite, via le paramétrage normal administrateur.
    compte = ok(api.post('/api/plan-comptable', json={'numero': '71955',
        'libelle': 'Reprise de provision REC-REPRISE — subdivision FICTIVE947'}), 201)
    assert compte['numero'] == '71955'
    return ecriture(api, 'REC-REPRISE', [{'compte': '1518', 'debit': 1000},
        {'compte': '71955', 'credit': 1000}], piece=True)


def deduction(api):
    return ok(api.post('/api/fiscalite/is/2025/retraitements', json={'type': 'deduction',
        'categorie': 'reprises_provisions_taxees', 'libelle': 'REC-REPRISE : taxation antérieure FICTIVE explicitement justifiée',
        'compte_source': '71955', 'montant': 1000, 'reference': 'REC-REPRISE',
        'commentaire': 'Variante HP-FIS-032 ; aucune déduction automatique d’une reprise probable.'}))
