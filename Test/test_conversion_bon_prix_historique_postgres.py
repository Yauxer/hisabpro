"""Prix de conversion BL/BR : API réelle, PostgreSQL éphémère vérifié."""
from contextlib import closing
from datetime import date
from pathlib import Path
import uuid
import json
import pytest
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_mutations_stock_historique_postgres import article
from test_articles_alertes_stock_historique_postgres import cible, photo


def photographie(application):
    result = photo(application)
    with application['engine'].connect() as db:
        for table in ('societes', 'bons_livraison', 'lignes_bon_livraison',
                      'factures', 'lignes_facture'):
            result[table] = db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
    return result


def bon(api, type_bon, aid, prix=0, quantite=2, nombre_lignes=1):
    r = api.post('/api/tiers', json={'nom': 'Conversion fictive '+uuid.uuid4().hex[:8],
                                    'type': 'fournisseur' if type_bon == 'achat' else 'client'})
    assert r.status_code == 201, r.text
    tiers = r.json()
    r = api.post('/api/bons-reception' if type_bon == 'achat' else '/api/bons-livraison',
                 json={'type': type_bon, 'date': date.today().isoformat(),
                       'tiers': tiers['nom'], 'tiers_id': tiers['id'], 'lignes': [
                           {'article_id': aid, 'description': 'Article fictif à facturer',
                            'quantite_prevue': quantite, 'quantite_livree': quantite,
                            'prix_unitaire': prix, 'tva': 20} for _ in range(nombre_lignes)]})
    assert r.status_code == 201, r.text
    return r.json()['id']


def modifier_prix(application, aid, type_bon, prix):
    cible(application)
    champ = 'prix_achat_ht' if type_bon == 'achat' else 'prix_vente_ht'
    with application['engine'].begin() as db:
        db.execute(text(f'UPDATE articles SET {champ}=:prix WHERE id=:id'), {'prix': prix, 'id': aid})


def convertir(application, api, bid):
    r = api.post(f'/api/bons-livraison/{bid}/convertir-facture', json={'date': date.today().isoformat()})
    if r.status_code == 500:
        log = application['api_log'].read_text(encoding='utf-8', errors='replace')
        path = Path(__file__).resolve().parents[1]/'.codex-tests'/('conversion343_api_'+uuid.uuid4().hex[:8]+'.log')
        path.write_text(log, encoding='utf-8')
        print(path, log[-9000:])
    return r


@pytest.mark.parametrize('type_bon', ['achat', 'vente'])
@pytest.mark.parametrize('prix', [None, float('nan'), float('inf'), float('-inf')])
def test_prix_article_requis_inconnu_refuse_sans_facture(application, type_bon, prix):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = bon(api, type_bon, aid)
        modifier_prix(application, aid, type_bon, prix)
        avant = photographie(application)
        r = convertir(application, api, bid)
        apres = photographie(application)
        if r.status_code != 409:
            path = Path(__file__).resolve().parents[1]/'.codex-tests'/('conversion343_persistance_'+uuid.uuid4().hex[:8]+'.json')
            path.write_text(json.dumps({'status': r.status_code, 'avant': avant, 'apres': apres}), encoding='utf-8')
            print('Photographies de persistance baseline conservées :', path)
        assert r.status_code == 409, r.text
        assert r.json()['detail']
        assert apres == avant


@pytest.mark.parametrize('type_bon', ['achat', 'vente'])
@pytest.mark.parametrize('prix', [float('nan'), float('inf'), float('-inf')])
def test_prix_bon_nonfini_refuse_sans_facture(application, type_bon, prix):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = bon(api, type_bon, aid, prix=32)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE lignes_bon_livraison SET prix_unitaire=:prix WHERE bon_livraison_id=:id'),
                       {'prix': prix, 'id': bid})
        avant = photographie(application)
        r = convertir(application, api, bid)
        assert r.status_code == 409, r.text
        assert photographie(application) == avant


@pytest.mark.parametrize('type_bon', ['achat', 'vente'])
@pytest.mark.parametrize('prix_article,prix_bon,attendu', [(0, 0, 0), (None, 32, 32), (20, 0, 20)])
def test_prix_connu_zero_et_priorite_bon_conserves(application, type_bon, prix_article, prix_bon, attendu):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = bon(api, type_bon, aid, prix_bon)
        modifier_prix(application, aid, type_bon, prix_article)
        stocks = photo(application)
        r = convertir(application, api, bid)
        assert r.status_code == 200, r.text
        f = r.json()
        assert f['lignes'][0]['prix_unitaire'] == attendu
        assert f['total_ht'] == 2*attendu
        assert f['total_tva'] == pytest.approx(2*attendu*.2)
        assert f['total_ttc'] == pytest.approx(2*attendu*1.2)
        assert f['est_validee'] is False
        assert photo(application) == stocks


@pytest.mark.parametrize('type_bon', ['achat', 'vente'])
def test_conversion_autre_societe404_sans_mutation(application, type_bon):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        aid, _ = article(application, api)
        bid = bon(api, type_bon, aid)
        modifier_prix(application, aid, type_bon, None)
        avant = photographie(application)
        assert convertir(application, autre, bid).status_code == 404
        assert photographie(application) == avant


@pytest.mark.parametrize('type_bon', ['achat', 'vente'])
@pytest.mark.parametrize('prix,quantite,nombre_lignes', [(1e308, 2, 1), (8e307, 1, 2)])
def test_totaux_conversion_depassement_refuses_avant_commit(application, type_bon, prix, quantite, nombre_lignes):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = bon(api, type_bon, aid, prix=32, quantite=quantite, nombre_lignes=nombre_lignes)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE lignes_bon_livraison SET prix_unitaire=:prix WHERE bon_livraison_id=:id'),
                       {'prix': prix, 'id': bid})
        avant = photographie(application)
        r = convertir(application, api, bid)
        apres = photographie(application)
        if r.status_code != 409:
            path = Path(__file__).resolve().parents[1]/'.codex-tests'/('conversion343_totaux_'+uuid.uuid4().hex[:8]+'.json')
            path.write_text(json.dumps({'status': r.status_code, 'avant': avant, 'apres': apres}), encoding='utf-8')
            print('Photographies avant/après conservées :', path)
        assert r.status_code == 409, r.text
        assert apres == avant


@pytest.mark.parametrize('type_bon', ['achat', 'vente'])
@pytest.mark.parametrize('partiel', [False, True])
def test_conversion_seconde_ligne_invalide_selection_et_rollback(application, type_bon, partiel):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = bon(api, type_bon, aid, prix=32, quantite=1, nombre_lignes=2)
        cible(application)
        with application['engine'].begin() as db:
            ids = db.execute(text('SELECT id FROM lignes_bon_livraison WHERE bon_livraison_id=:id ORDER BY id'), {'id': bid}).scalars().all()
            db.execute(text('UPDATE lignes_bon_livraison SET prix_unitaire=:prix WHERE id=:id'), {'prix': float('nan'), 'id': ids[1]})
        avant = photographie(application)
        payload = {'date': date.today().isoformat()}
        if partiel:
            payload['lignes'] = [{'ligne_bl_id': ids[0], 'quantite': 1}]
        r = api.post(f'/api/bons-livraison/{bid}/convertir-facture', json=payload)
        if partiel:
            assert r.status_code == 200, r.text
            assert len(r.json()['lignes']) == 1
            assert r.json()['total_ttc'] == pytest.approx(38.4)
            assert photo(application) == {k: avant[k] for k in photo(application)}
        else:
            assert r.status_code == 409, r.text
            assert photographie(application) == avant
