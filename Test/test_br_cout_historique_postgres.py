"""Lot341 : propagation409 des coûts historiques au BR, vraie API PG nonce."""
from contextlib import closing
from datetime import date
from pathlib import Path
import uuid
import pytest
from sqlalchemy import text
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_mutations_stock_historique_postgres import article
from test_articles_alertes_stock_historique_postgres import cible, photo


def photographie(application):
    result = photo(application)
    with application['engine'].connect() as db:
        for table in ('societes', 'bons_livraison', 'lignes_bon_livraison'):
            result[table] = db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
    return result


def reception(application, api, articles, prix=0):
    assert api.patch('/api/societe/moi', json={'stock_declencheur_achat': 'br'}).status_code == 200
    tiers = 'Fournisseur BR fictif '+uuid.uuid4().hex[:8]
    r = api.post('/api/tiers', json={'nom': tiers, 'type': 'fournisseur'})
    assert r.status_code == 201, r.text
    r = api.post('/api/bons-reception', json={'type': 'achat', 'date': date.today().isoformat(),
        'tiers': tiers, 'tiers_id': r.json()['id'], 'lignes': [
            {'article_id': aid, 'description': 'Réception fictive', 'quantite_prevue': 2,
             'quantite_livree': 2, 'prix_unitaire': prix, 'tva': 20} for aid in articles]})
    assert r.status_code == 201, r.text
    bid = r.json()['id']
    assert api.patch(f'/api/bons-reception/{bid}', json={'statut': 'expedie'}).status_code == 200
    return bid


def modifier_source(application, aid, champ, valeur):
    cible(application)
    with application['engine'].begin() as db:
        if champ == 'cmup':
            db.execute(text('UPDATE articles SET prix_achat_ht=0 WHERE id=:id'), {'id': aid})
        db.execute(text(f'UPDATE articles SET {champ}=:val WHERE id=:id'), {'val': valeur, 'id': aid})


def livrer(application, api, bid):
    r = api.patch(f'/api/bons-reception/{bid}', json={'statut': 'livre'})
    if r.status_code == 500:
        journal = application['api_log'].read_text(encoding='utf-8', errors='replace')
        p = Path(__file__).resolve().parents[1]/'.codex-tests'/('br_cout_341_api_'+uuid.uuid4().hex[:8]+'.log')
        p.write_text(journal, encoding='utf-8')
        print(p, journal[-12000:])
    return r


@pytest.mark.parametrize('champ', ['prix_achat_ht', 'cmup'])
@pytest.mark.parametrize('valeur', [None, float('nan'), float('inf'), float('-inf')])
def test_br_cout_historique_inconnu_refuse409_sans_mutation(application, champ, valeur):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = reception(application, api, [aid])
        modifier_source(application, aid, champ, valeur)
        avant = photographie(application)
        r = livrer(application, api, bid)
        assert r.status_code == 409, r.text
        assert r.json()['detail']
        assert photographie(application) == avant


def test_br_seconde_ligne_inconnue_annule_premiere_entree(application):
    with closing(client(application)[0]) as api:
        sain, _ = article(application, api)
        mauvais, _ = article(application, api)
        bid = reception(application, api, [sain, mauvais])
        modifier_source(application, mauvais, 'prix_achat_ht', None)
        avant = photographie(application)
        r = livrer(application, api, bid)
        assert r.status_code == 409, r.text
        assert photographie(application) == avant


@pytest.mark.parametrize('cmup,prix_source,prix_br,cout,cmup_apres', [
    (20, 20, 0, 20, 20), (0, 0, 0, 0, 0), (20, None, 32, 32, 22)])
def test_br_couts_connus_et_priorite_explicite_preserves(application, cmup, prix_source, prix_br, cout, cmup_apres):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api)
        bid = reception(application, api, [aid], prix=prix_br)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text('UPDATE articles SET cmup=:cmup,prix_achat_ht=:prix WHERE id=:id'),
                       {'cmup': cmup, 'prix': prix_source, 'id': aid})
        r = livrer(application, api, bid)
        assert r.status_code == 200, r.text
        with application['engine'].connect() as db:
            m = db.execute(text('SELECT stock_avant,stock_apres,quantite,cout_unitaire,cmup_apres FROM mouvements_stock WHERE article_id=:id'), {'id': aid}).one()
        assert tuple(m) == (10, 12, 2, cout, cmup_apres)


def test_br_autre_societe404_preserve_sources(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        aid, _ = article(application, api)
        bid = reception(application, api, [aid])
        modifier_source(application, aid, 'prix_achat_ht', None)
        avant = photographie(application)
        assert livrer(application, autre, bid).status_code == 404
        assert photographie(application) == avant
