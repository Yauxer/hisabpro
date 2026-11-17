"""980 — remarques du partenaire du 17/11/2026, rejouées sur PostgreSQL nonce avec des données fictives.

1. Un BL tiré d'une facture est déjà facturé : il ne peut pas redonner une facture.
   Une facture tirée d'un BL ou d'un BC ne redonne pas de BL.
2. Les modes de règlement de l'interface sont ceux de l'API (une seule liste).
3. Volet Trésorerie : soldes banques / caisses à une date.
4. Alimenter la caisse depuis la banque : deux écritures via 5115, contrôle de la caisse.
"""
import re
from datetime import date
from decimal import Decimal as D
from pathlib import Path
from sqlalchemy import text
from test_e2e_facturation_isole import application  # noqa: F401
from test_ras_lecture_conservation import client
from test_e2e_ras_capture_isole import ok

ROOT = Path(__file__).resolve().parents[1]
JOUR = date.today().isoformat()
LIGNE = {'description': 'Prestation fictive980', 'quantite': 2, 'prix_unitaire': 500, 'tva': 20}


def facture_validee(api, tiers, **extra):
    f = ok(api.post('/api/factures', json={'type': 'vente', 'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'date': JOUR,
                                           'ras_taux': 0, 'lignes': [LIGNE], **extra}), 201)
    return valider(api, f['id'])


def valider(api, fid):
    ok(api.post(f"/api/factures/{fid}/valider"))
    return next(x for x in ok(api.get('/api/factures', params={'exercice': date.today().year})) if x['id'] == fid)


def test_980_bl_issu_de_facture_non_refacturable(application):
    api, _, _ = client(application)
    try:
        t = ok(api.post('/api/tiers', json={'nom': 'Client fictif980', 'type': 'client'}), 201)
        f = facture_validee(api, t)
        bl = ok(api.post(f"/api/factures/{f['id']}/convertir-bl", json={'date': JOUR}))
        liste = ok(api.get('/api/bons-livraison', params={'exercice': date.today().year}))
        vu = next(x for x in liste if x['id'] == bl['id'])
        assert vu['facturation_pct'] == 100 and vu['facture_numeros'] == [f['numero']], vu
        r = api.post(f"/api/bons-livraison/{bl['id']}/convertir-facture", json={'date': JOUR})
        assert r.status_code == 409 and 'créé depuis la facture' in r.json()['detail'], r.text

        # Un BL ordinaire facturé : la facture obtenue ne redonne pas de BL.
        bl2 = ok(api.post('/api/bons-livraison', json={'date': JOUR, 'tiers': t['nom'], 'tiers_id': t['id'], 'type': 'vente',
                 'lignes': [{**LIGNE, 'quantite_prevue': 2, 'quantite_livree': 2}]}), 201)
        ligne_bl = bl2['lignes'][0]['id']
        fa = ok(api.post(f"/api/bons-livraison/{bl2['id']}/convertir-facture", json={'date': JOUR, 'lignes': [{'ligne_bl_id': ligne_bl, 'quantite': 1}]}))
        fa = valider(api, fa['id'])
        r = api.post(f"/api/factures/{fa['id']}/convertir-bl", json={'date': JOUR})
        assert r.status_code == 400 and 'existe déjà' in r.json()['detail'], r.text   # première facture : lien direct
        f2 = ok(api.post(f"/api/bons-livraison/{bl2['id']}/convertir-facture", json={'date': JOUR}))
        f2 = valider(api, f2['id'])   # seconde facture du même BL : pas de lien direct, refus par l'origine des lignes
        r = api.post(f"/api/factures/{f2['id']}/convertir-bl", json={'date': JOUR})
        assert r.status_code == 409 and 'établie depuis le bon de livraison' in r.json()['detail'], r.text
        # Un second bon de livraison ne peut toujours pas être refacturé depuis bl2 (déjà soldé).
        r = api.post(f"/api/bons-livraison/{bl2['id']}/convertir-facture", json={'date': JOUR})
        assert r.status_code == 409, r.text

        # Facture directe d'un BC : la livraison se fait depuis le BC, pas depuis la facture.
        bc = ok(api.post('/api/bons-commande', json={'date': JOUR, 'tiers': t['nom'], 'tiers_id': t['id'], 'type': 'vente',
                                                      'lignes': [LIGNE]}), 201)
        f3 = ok(api.post(f"/api/bons-commande/{bc['id']}/convertir-facture", json={'date': JOUR}))
        f3 = valider(api, f3['id'])
        r = api.post(f"/api/factures/{f3['id']}/convertir-bl", json={'date': JOUR})
        assert r.status_code == 409 and 'depuis ce bon de commande' in r.json()['detail'], r.text
    finally:
        api.close()


def test_980_modes_de_reglement_une_seule_liste():
    api = re.search(r'ModeReglement = Literal\[([^\]]+)\]', (ROOT / 'hisabpro-backend/schemas.py').read_text(encoding='utf-8')).group(1)
    attendus = re.findall(r'"(\w+)"', api)
    js = (ROOT / 'src/utils/modesReglement.js').read_text(encoding='utf-8')
    assert re.findall(r"val: '(\w+)'", js) == attendus
    for page in ('src/pages/Factures.jsx', 'src/pages/Commercial.jsx', 'src/pages/Avoirs.jsx', 'src/pages/Acomptes.jsx',
                 'src/components/ReglementParTiers.jsx'):
        source = (ROOT / page).read_text(encoding='utf-8')
        assert 'modesReglement.js' in source, page
        assert "'prelevement', 'autre'" not in source and "prelevement: 'Prélèvement'" not in source, page


def soldes_ecriture(app, eid):
    with app['engine'].connect() as db:
        return {c: D(str(s)) for c, s in db.execute(text(
            'SELECT compte, sum(debit - credit) FROM lignes_ecriture WHERE ecriture_id = :i GROUP BY compte'), {'i': eid})}


def solde(situation, compte):
    return next((x['solde'] for c in situation['categories'] for x in c['comptes'] if x['compte'] == compte), None)


def test_980_tresorerie_et_alimentation_caisse(application):
    api, _, _ = client(application)
    try:
        # Apport en banque de 50 000.
        ok(api.post('/api/ecritures', json={'date': JOUR, 'journal': 'BQ', 'libelle': 'Apport fictif980', 'est_validee': True, 'reference': 'APP-980',
               'lignes': [{'compte': '5141', 'debit': 50000, 'credit': 0}, {'compte': '1111', 'debit': 0, 'credit': 50000}]}), 201)
        s = ok(api.get('/api/tresorerie/situation'))
        assert solde(s, '5141') == 50000 and solde(s, '5161') == 0 and s['disponibilites'] == 50000, s

        # Caisse vide : un versement caisse → banque est refusé (une caisse ne devient jamais créditrice).
        r = api.post('/api/tresorerie/virements', json={'date': JOUR, 'montant': '100.00', 'compte_source': '5161', 'compte_destination': '5141'})
        assert r.status_code == 409 and 'Caisse insuffisante' in r.json()['detail'], r.text
        # Comptes hors disponibilités refusés.
        r = api.post('/api/tresorerie/virements', json={'date': JOUR, 'montant': '100.00', 'compte_source': '5141', 'compte_destination': '6111'})
        assert r.status_code == 422, r.text

        # Alimenter la caisse : 8 000 de la banque vers la caisse.
        v = ok(api.post('/api/tresorerie/virements', json={'date': JOUR, 'montant': '8000.00', 'compte_source': '5141',
                                                             'compte_destination': '5161', 'reference': 'CHQ-RETRAIT-980'}), 201)
        assert v['sens'] == "Retrait d'espèces pour la caisse" and v['valide'] is True
        sortie, entree = v['ecritures']
        assert (sortie['journal'], entree['journal']) == ('BQ', 'CA')
        assert soldes_ecriture(application, sortie['id']) == {'5115': D('8000.00'), '5141': D('-8000.00')}
        assert soldes_ecriture(application, entree['id']) == {'5161': D('8000.00'), '5115': D('-8000.00')}
        assert sortie['reference'] == entree['reference'] == 'CHQ-RETRAIT-980'

        s = ok(api.get('/api/tresorerie/situation'))
        assert (solde(s, '5141'), solde(s, '5161'), solde(s, '5115')) == (42000, 8000, 0), s
        assert s['disponibilites'] == 50000 and s['tresorerie_nette'] == 50000
        assert s['mouvements'][0]['date'] == JOUR

        # La caisse alimentée permet maintenant un versement en banque de 3 000, référence générée.
        v = ok(api.post('/api/tresorerie/virements', json={'date': JOUR, 'montant': '3000.00', 'compte_source': '5161', 'compte_destination': '5141'}), 201)
        assert v['sens'] == "Versement d'espèces en banque" and v['ecritures'][0]['journal'] == 'CA'
        assert v['ecritures'][0]['reference'].startswith('VF-') and v['ecritures'][0]['reference'] == v['ecritures'][1]['reference']
        s = ok(api.get('/api/tresorerie/situation'))
        assert (solde(s, '5141'), solde(s, '5161')) == (45000, 5000)
        # Les à-nouveaux générés par une clôture reprennent l'historique : ils ne sont pas recomptés.
        with application['engine'].begin() as db:
            sid = db.scalar(text('SELECT societe_id FROM ecritures WHERE id = :i'), {'i': sortie['id']})
            eid = db.scalar(text("""INSERT INTO ecritures (societe_id, date, journal, libelle, exercice, source, est_validee)
                                    VALUES (:s, :d, 'AN', 'À-nouveaux fictifs980', :a, 'cloture', false) RETURNING id"""),
                            {'s': sid, 'd': JOUR, 'a': date.today().year})
            db.execute(text("""INSERT INTO lignes_ecriture (ecriture_id, compte, libelle, debit, credit)
                               VALUES (:e, '5161', 'AN', 99999, 0), (:e, '1111', 'AN', 0, 99999)"""), {'e': eid})
        s = ok(api.get('/api/tresorerie/situation'))
        caisse = next(x for c in s['categories'] for x in c['comptes'] if x['compte'] == '5161')
        assert (caisse['solde'], caisse['brouillons']) == (5000, 0), caisse
        r = api.post('/api/tresorerie/virements', json={'date': JOUR, 'montant': '5000.01', 'compte_source': '5161', 'compte_destination': '5141'})
        assert r.status_code == 409, r.text
        # Une situation antérieure à l'apport est vide.
        s = ok(api.get('/api/tresorerie/situation', params={'au': '2000-01-01'}))
        assert not solde(s, '5141') and s['disponibilites'] == 0 and not s['mouvements']
    finally:
        api.close()
