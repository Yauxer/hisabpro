"""981 — paiements en espèces aux fournisseurs, CGI 2026 art. 11-II (IS) et 106-II (TVA).

PostgreSQL nonce, données fictives. Le paiement reste possible ; HisabPro avertit,
chiffre le dépassement (candidat IS à confirmer) et le signale dans la TVA.
"""
from decimal import Decimal as D
from test_journal_cloture_concurrente_isole import (  # noqa: F401  base avec les migrations d'acomptes (041+)
    application, application097, application093, application092, application091,
    application090, application089, application087, migration,
)
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok


def fournisseur(api, nom):
    return ok(api.post('/api/tiers', json={'nom': nom, 'type': 'fournisseur'}), 201)


def facture(api, t, ref, jour, ht):
    f = ok(api.post('/api/factures', json={'type': 'achat', 'tiers': t['nom'], 'tiers_id': t['id'], 'date': jour, 'ras_taux': 0,
                                           'reference': ref, 'lignes': [{'description': f'Achat {ref}', 'quantite': 1, 'prix_unitaire': ht, 'tva': 20}]}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider")); ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
    return f


def payer(api, f, jour, montant, mode='especes'):
    return ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': f['tiers'], 'date': jour, 'montant': montant,
                                                'mode': mode, 'reference': f'P-{jour}-{montant}', 'comptabiliser': True}), 201)


def cumul(api, t, jour, montant):
    return ok(api.get('/api/tresorerie/especes-fournisseur', params={'date': jour, 'tiers_id': t['id'], 'montant': montant}))


def test_981_especes_fournisseurs(application):
    api, _, _ = client(application)
    try:
        ok(api.post('/api/ecritures', json={'date': '2026-11-01', 'journal': 'CA', 'libelle': 'Apport en caisse fictif981', 'est_validee': True,
               'reference': 'APP-981', 'lignes': [{'compte': '5161', 'debit': 200000, 'credit': 0}, {'compte': '1111', 'debit': 0, 'credit': 200000}]}), 201)
        a, b, c = fournisseur(api, 'Atlas Bois fictif981'), fournisseur(api, 'Batiplus fictif981'), fournisseur(api, 'Cimenterie fictive981')
        fa = facture(api, a, 'FA-A-981', '2026-11-02', 10000)      # TTC 12 000
        fb = facture(api, b, 'FA-B-981', '2026-11-01', 50000)      # TTC 60 000
        fc = facture(api, c, 'FA-C-981', '2026-11-01', 10000)

        # Avant le paiement : 4 000 passe sous la limite, puis 2 000 le même jour la dépasse (non bloquant).
        assert cumul(api, a, '2026-11-03', 4000)['depassement'] is False
        payer(api, fa, '2026-11-03', 4000)
        info = cumul(api, a, '2026-11-03', 2000)
        assert info['depassement'] and info['jour_deja_paye'] == 4000 and info['total_jour'] == 6000, info
        assert 'au-delà de 5 000 DH par jour' in info['alertes'][0] and 'Le paiement reste possible' in info['consequence']
        payer(api, fa, '2026-11-03', 2000)                         # accepté
        # B : 11 jours à 5 000, jamais au-delà par jour, mais 55 000 sur le mois.
        for jour in range(1, 12):
            payer(api, fb, f'2026-11-{jour:02d}', 5000)
        assert cumul(api, b, '2026-11-12', 1)['total_mois'] == 55001
        # C : virement de 10 000 (moyen admis) + acompte en espèces de 6 000.
        payer(api, fc, '2026-11-05', 10000, mode='virement')
        ok(api.post('/api/acomptes', json={'type': 'fournisseur', 'tiers': c['nom'], 'tiers_id': c['id'], 'date': '2026-11-06', 'montant': 6000,
                                           'taux_tva': 20, 'mode': 'especes', 'reference': 'AC-C-981'}), 201)

        dep = ok(api.get('/api/tresorerie/especes-fournisseurs', params={'debut': '2026-01-01', 'fin': '2026-12-31'}))['depassements']
        par = {x['fournisseur']: x for x in dep}
        assert set(par) == {a['nom'], b['nom'], c['nom']}, dep
        assert (par[a['nom']]['total_especes'], par[a['nom']]['montant_admis'], par[a['nom']]['montant_au_dela']) == (6000, 5000, 1000)
        assert par[a['nom']]['jours_au_dela'] == [{'date': '2026-11-03', 'total': 6000.0}]
        assert (par[b['nom']]['total_especes'], par[b['nom']]['montant_au_dela'], par[b['nom']]['mois_au_dela']) == (55000, 5000, True)
        assert par[b['nom']]['jours_au_dela'] == []
        assert par[c['nom']]['montant_au_dela'] == 1000 and par[c['nom']]['paiements'][0]['origine'] == 'acompte'

        # IS : candidat à confirmer, sans effet sur le calcul.
        is_ = ok(api.get('/api/fiscalite/is/2026'))
        cand = next(x for x in is_['retraitements_a_confirmer'] if x['id'] == 'candidat:paiements_especes')
        assert D(str(cand['montant_detecte'])) == D('7000.00') and cand['impacte_calcul'] is False and cand['reference'] == 'CGI 2026 art. 11-II'

        # TVA : alerte chiffrée par fournisseur (TVA comprise dans les espèces versées), montants non modifiés d'office.
        tva = ok(api.get('/api/tva/declaration', params={'exercice': 2026, 'mois': 11}))
        alertes = [x for x in tva['alertes'] if x.startswith('Espèces versées')]
        assert len(alertes) == 3, tva['alertes']
        texte_a = next(x for x in alertes if a['nom'] in x)
        assert 'CGI art. 106-II' in texte_a and 'TVA comprise dans ces paiements 1 000,00 DH' in texte_a, texte_a
        assert 'TVA comprise dans ces paiements 9 166,67 DH' in next(x for x in alertes if b['nom'] in x)
        assert 'TVA comprise dans ces paiements 1 000,00 DH' in next(x for x in alertes if c['nom'] in x)
        # Octobre : aucun paiement, aucune alerte.
        assert not [x for x in ok(api.get('/api/tva/declaration', params={'exercice': 2026, 'mois': 10}))['alertes'] if x.startswith('Espèces versées')]
    finally:
        api.close()
