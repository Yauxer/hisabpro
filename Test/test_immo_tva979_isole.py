"""979 — achats d'immobilisations par facture : compte 2xxx, TVA 34551 / 34552, dette 4481, fiche sans double comptage.

PostgreSQL nonce, données fictives (remarque du partenaire du 13/11/2026).
"""
from decimal import Decimal as D
from sqlalchemy import text
from test_e2e_facturation_isole import application  # noqa: F401
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok

JOUR = '2026-11-05'


def soldes(app, ecriture_id):
    with app['engine'].connect() as db:
        return {c: D(str(s)) for c, s in db.execute(text(
            'SELECT compte, sum(debit - credit) FROM lignes_ecriture WHERE ecriture_id = :i GROUP BY compte'), {'i': ecriture_id})}


def nb_ecritures(app):
    with app['engine'].connect() as db:
        return db.scalar(text('SELECT count(*) FROM ecritures'))


def facture(api, tiers, ref, lignes):
    f = ok(api.post('/api/factures', json={'type': 'achat', 'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'date': JOUR, 'ras_taux': 0,
                                           'reference': ref, 'lignes': lignes}), 201)
    ok(api.post(f"/api/factures/{f['id']}/valider"))
    e = ok(api.post(f"/api/factures/{f['id']}/comptabiliser"))
    ok(api.post(f"/api/ecritures/{e['ecriture_id']}/valider"))
    return f, e['ecriture_id']


def regler(api, f, montant):
    r = ok(api.post('/api/reglements', json={'facture_id': f['id'], 'tiers': f['tiers'], 'date': JOUR, 'montant': montant,
                                             'mode': 'virement', 'reference': f"VIR-{f['reference']}", 'comptabiliser': True}), 201)
    return r.get('ecriture_id') or ok(api.get(f"/api/reglements/{r['id']}")).get('ecriture_id')


def tva_novembre(api):
    r = ok(api.get('/api/tva/declaration', params={'exercice': 2026, 'mois': 11}))
    return D(str(r['recuperable_immobilisations']['total'])), D(str(r['recuperable_charges']['total']))


def test_979_facture_immobilisation_tva_34551_et_fiche(application):
    api, _, _ = client(application)
    try:
        t = ok(api.post('/api/tiers', json={'nom': 'Info Équipement fictif979', 'type': 'fournisseur'}), 201)
        pc = ok(api.post('/api/articles', json={'code': 'PC-979', 'designation': 'Ordinateur fictif979', 'prix_achat': 10000,
                                                'tva': 20, 'compte_achat': '2355', 'stock_actuel': 0}), 201)
        papier = ok(api.post('/api/articles', json={'code': 'PAP-979', 'designation': 'Papier fictif979', 'prix_achat': 1000,
                                                    'tva': 20, 'compte_achat': '6125', 'stock_actuel': 0}), 201)

        # 1. Facture 100 % immobilisation : 2355 / 34551 / 4481.
        f1, e1 = facture(api, t, 'FA-INFO-979', [{'article_id': pc['id'], 'description': 'Ordinateur fictif979', 'quantite': 1,
                                                 'prix_unitaire': 10000, 'tva': 20}])
        assert soldes(application, e1) == {'2355': D('10000.00'), '34551': D('2000.00'), '4481': D('-12000.00')}

        # 2. Facture mixte : chaque TVA dans son compte, le fournisseur reste en 4411.
        f2, e2 = facture(api, t, 'FA-MIX-979', [
            {'article_id': pc['id'], 'description': 'Ordinateur fictif979', 'quantite': 1, 'prix_unitaire': 5000, 'tva': 20},
            {'article_id': papier['id'], 'description': 'Papier fictif979', 'quantite': 1, 'prix_unitaire': 1000, 'tva': 20}])
        assert soldes(application, e2) == {'2355': D('5000.00'), '6125': D('1000.00'), '34551': D('1000.00'),
                                           '34552': D('200.00'), '4411': D('-7200.00')}

        # 3. Le règlement de la facture d'immobilisation solde 4481.
        r1 = regler(api, f1, 12000)
        assert soldes(application, r1).get('4481') == D('12000.00'), soldes(application, r1)
        regler(api, f2, 7200)

        # 4. Déclaration de TVA (encaissement) : récupérable sur immobilisations / sur charges.
        assert tva_novembre(api) == (D('3000.00'), D('200.00'))

        # 5. Avoir partiel sur la ligne d'immobilisation de la facture mixte : la TVA reprise sort de 34551.
        ligne_pc = next(l for l in f2['lignes'] if l['article_id'] == pc['id'])
        a = ok(api.post('/api/avoirs', json={'facture_id': f2['id'], 'date': JOUR, 'motif': 'Retour fictif979',
                                             'lignes': [{'facture_ligne_id': ligne_pc['id'], 'quantite': 1}]}), 201)
        ea = ok(api.post(f"/api/avoirs/{a['id']}/comptabiliser"))
        ea_id = ea.get('ecriture_id') or ea.get('ecriture', {}).get('id')
        s = soldes(application, ea_id)
        assert s.get('34551') == D('-1000.00') and '34552' not in s and s.get('2355') == D('-5000.00'), s

        # 6. Lignes à transformer en fiche : les deux lignes d'immobilisation, pas le papier.
        a_creer = ok(api.get('/api/immobilisations/a-creer-depuis-factures'))
        assert sorted((x['facture'], x['compte'], x['montant_ht']) for x in a_creer) == [
            ('FA-INFO-979', '2355', 10000.0), ('FA-MIX-979', '2355', 5000.0)], a_creer

        # 7. Création de la fiche : aucune nouvelle écriture, TVA non recomptée, paiement via la facture seulement.
        avant = nb_ecritures(application)
        x = next(x for x in a_creer if x['facture'] == 'FA-INFO-979')
        immo = ok(api.post(f"/api/immobilisations/depuis-facture/{f1['id']}", json={'ligne_id': x['ligne_id'], 'duree_amort': 5}), 201)
        assert nb_ecritures(application) == avant
        assert immo['reference'] == f"FA-{f1['id']}-L{x['ligne_id']}" and D(str(immo['valeur_brute'])) == D('10000.00'), immo
        assert immo['compte_immo'] == '2355' and immo['ecriture_acquisition_id'] == e1, immo
        assert tva_novembre(api) == (D('2000.00'), D('200.00'))   # avoir sur l'immobilisation : 34551 seule réduite ; la fiche n'ajoute rien
        r = api.post(f"/api/immobilisations/depuis-facture/{f1['id']}", json={'ligne_id': x['ligne_id'], 'duree_amort': 5})
        assert r.status_code == 409, r.text
        r = api.post(f"/api/immobilisations/{immo['id']}/payer", json={'date_paiement': JOUR})
        assert r.status_code == 409 and 'règlements de la facture' in r.json()['detail'], r.text
        assert [y['facture'] for y in ok(api.get('/api/immobilisations/a-creer-depuis-factures'))] == ['FA-MIX-979']
    finally:
        api.close()
