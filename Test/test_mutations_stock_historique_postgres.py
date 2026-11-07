"""Mutations sur sources historiques : API et moteur PostgreSQL nonce uniquement."""
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import photo, cible
from services import stock_movement_service as stock


def article(application, api, quantite=10, cmup=20, prix=20):
    cible(application)
    r = api.post('/api/articles', json={'code': 'MUT-'+uuid.uuid4().hex[:10],
        'designation': 'Mutation fictive', 'stock_actuel': 0, 'is_stockable': True,
        'prix_achat_ht': 20, 'prix_vente_ht': 30, 'tva': 20})
    assert r.status_code == 201, r.text
    aid = r.json()['id']
    with application['engine'].begin() as db:
        db.execute(text('UPDATE articles SET stock_actuel=:q,cmup=:c,prix_achat_ht=:p WHERE id=:id'),
                   {'q': quantite, 'c': cmup, 'p': prix, 'id': aid})
    with application['engine'].connect() as db:
        sid = db.execute(text('SELECT societe_id FROM articles WHERE id=:id'), {'id': aid}).scalar_one()
    return aid, sid


def trace(application, response):
    if response.status_code == 500:
        log = application['api_log'].read_text(encoding='utf-8', errors='replace')
        path = Path(__file__).resolve().parents[1]/'.codex-tests'/('mutations_335_api_'+uuid.uuid4().hex[:8]+'.log')
        path.write_text(log, encoding='utf-8')
        print(path, log[-10000:])


@pytest.mark.parametrize('valeur', [None, float('nan'), float('inf'), float('-inf')])
@pytest.mark.parametrize('action', ['delete', 'archive', 'service'])
def test_source_stock_inconnue_refuse_archive_conversion_sans_mutation(application, valeur, action):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api, valeur)
        avant = photo(application)
        r = (api.delete(f'/api/articles/{aid}') if action == 'delete' else
             api.patch(f'/api/articles/{aid}', json={('actif' if action == 'archive' else 'is_stockable'): False}))
        trace(application, r)
        assert r.status_code == 409, r.text
        assert photo(application) == avant


@pytest.mark.parametrize('champ,valeur', [('stock_actuel', None), ('cmup', None),
    ('cmup', float('nan')), ('cmup', float('inf')), ('cmup', -1)])
@pytest.mark.parametrize('cible_stock', [10, 8])
def test_correction_refuse_source_inconnue_meme_sans_delta(application, champ, valeur, cible_stock):
    with closing(client(application)[0]) as api:
        aid, _ = article(application, api, None if champ == 'stock_actuel' else 10,
                         valeur if champ == 'cmup' else 20)
        avant = photo(application)
        r = api.patch(f'/api/articles/{aid}/stock', json={'stock_actuel': cible_stock})
        trace(application, r)
        assert r.status_code == 409, r.text
        assert photo(application) == avant


@pytest.mark.parametrize('champ,valeur', [('stock_actuel', None), ('cmup', None),
    ('cmup', float('nan')), ('cmup', float('-inf')), ('cmup', -1)])
@pytest.mark.parametrize('sens', ['entree', 'sortie'])
def test_moteur_refuse_sources_historiques_meme_cout_explicite(application, champ, valeur, sens):
    with closing(client(application)[0]) as api:
        aid, sid = article(application, api, None if champ == 'stock_actuel' else 10,
                           valeur if champ == 'cmup' else 20)
        avant = photo(application)
        with Session(application['engine']) as db:
            with pytest.raises(ValueError):
                stock.enregistrer_mouvement(db, sid, aid, sens, 1, cout_unitaire=30)
            db.rollback()
        assert photo(application) == avant


@pytest.mark.parametrize('helper,cmup,prix', [(stock.cout_sortie, None, 20),
    (stock.cout_sortie, 0, None), (stock.cout_sortie, None, 0),
    (stock.cout_entree_par_defaut, 20, None), (stock.cout_entree_par_defaut, None, 0),
    (stock.cout_entree_par_defaut, 0, None)])
def test_cout_par_defaut_ne_confond_pas_absent_et_zero(helper, cmup, prix):
    with pytest.raises(ValueError):
        helper(SimpleNamespace(cmup=cmup, prix_achat_ht=prix))


def test_correction_saine_trace_cmup20_et_zero_connu(application):
    with closing(client(application)[0]) as api:
        aid, sid = article(application, api)
        r = api.patch(f'/api/articles/{aid}/stock', json={'stock_actuel': 8})
        assert r.status_code == 200, r.text
        assert r.json()['stock_actuel'] == 8 and r.json()['cmup'] == 20
        with Session(application['engine']) as db:
            import models
            m = db.query(models.MouvementStock).filter_by(article_id=aid).one()
            assert (m.stock_avant, m.stock_apres, m.quantite, m.cout_unitaire) == (10, 8, 2, 20)
        zero, _ = article(application, api, 0, 0, 0)
        assert api.patch(f'/api/articles/{zero}', json={'is_stockable': False}).status_code == 200
        assert stock.cout_sortie(SimpleNamespace(cmup=0, prix_achat_ht=0)) == 0
        assert stock.cout_entree_par_defaut(SimpleNamespace(cmup=0, prix_achat_ht=0)) == 0


@pytest.mark.parametrize('champ', ['stock_actuel', 'cmup'])
def test_compensation_refuse_fiche_inconnue_sans_modifier_chaine(application, champ):
    with closing(client(application)[0]) as api:
        aid, sid = article(application, api)
        with Session(application['engine']) as db:
            stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                cout_unitaire=20, source_type='recette335', source_id=335)
            db.commit()
        with application['engine'].begin() as db:
            db.execute(text(f'UPDATE articles SET {champ}=NULL WHERE id=:id'), {'id': aid})
        avant = photo(application)
        with Session(application['engine']) as db:
            with pytest.raises(ValueError):
                stock.annuler_mouvements_source(db, sid, source_type='recette335', source_id=335)
            db.rollback()
        assert photo(application) == avant


def test_description_seule_et_autre_societe_preservent_sources(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        aid, _ = article(application, api, None, None)
        r = api.patch(f'/api/articles/{aid}', json={'description': 'Information indépendante'})
        assert r.status_code == 200, r.text
        assert r.json()['stock_actuel'] is None and r.json()['cmup'] is None
        avant = photo(application)
        assert autre.delete(f'/api/articles/{aid}').status_code == 404
        assert autre.patch(f'/api/articles/{aid}', json={'actif': False}).status_code == 404
        assert autre.patch(f'/api/articles/{aid}/stock', json={'stock_actuel': 0}).status_code == 404
        assert photo(application) == avant
        assert api.patch(f'/api/articles/{aid}/stock', json={}).status_code == 409
        assert photo(application) == avant


def test_cout_explicite_idempotence_et_verrouillage_periode_preserves(application):
    with closing(client(application)[0]) as api:
        aid, sid = article(application, api, 10, 20, None)
        with Session(application['engine']) as db:
            m = stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                cout_unitaire=32, cle_idempotence='recette335:explicite')
            assert (m.stock_apres, m.cmup_apres) == (12, 22)
            assert stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                cout_unitaire=32, cle_idempotence='recette335:explicite').id == m.id
            db.commit()
        with application['engine'].begin() as db:
            db.execute(text("UPDATE periodes_comptables SET statut='fermee' WHERE exercice_id IN "
                            "(SELECT id FROM exercices_comptables WHERE societe_id=:sid)"), {'sid': sid})
        avant = photo(application)
        r = api.patch(f'/api/articles/{aid}/stock', json={'stock_actuel': 8})
        assert r.status_code == 409, r.text
        assert photo(application) == avant
        with Session(application['engine']) as db:
            # Une reprise identique retrouve la preuve créée, sans nouveau mouvement.
            stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                cout_unitaire=32, cle_idempotence='recette335:explicite')
            db.rollback()
        assert photo(application) == avant


def test_deux_articles_compensation_qualifie_toutes_fiches_avant_mutation(application):
    import models
    with closing(client(application)[0]) as api:
        sain, sid = article(application, api)
        inconnu, _ = article(application, api)
        with Session(application['engine']) as db:
            for aid in (sain, inconnu):
                stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                    cout_unitaire=20, source_type='recette335', source_id=336)
            db.commit()
        with application['engine'].begin() as db:
            db.execute(text('UPDATE articles SET cmup=NULL WHERE id=:id'), {'id': inconnu})
        avant = photo(application)
        with Session(application['engine']) as db:
            nombre = db.query(models.MouvementStock).count()
            with pytest.raises(ValueError):
                stock.annuler_mouvements_source(db, sid, source_type='recette335', source_id=336)
            assert not db.dirty, 'Même la fiche saine ne doit pas avoir été modifiée avant le refus.'
            assert db.query(models.MouvementStock).count() == nombre
            db.rollback()
        assert photo(application) == avant


def test_source_cout_inutilisee_et_repli_zero_connus_preserves():
    assert stock.cout_sortie(SimpleNamespace(cmup=20, prix_achat_ht=None)) == 20
    assert stock.cout_entree_par_defaut(SimpleNamespace(cmup=None, prix_achat_ht=20)) == 20
    assert stock.cout_sortie(SimpleNamespace(cmup=0, prix_achat_ht=20)) == 20
    assert stock.cout_entree_par_defaut(SimpleNamespace(cmup=20, prix_achat_ht=0)) == 20
    assert stock.D(None) == 0  # Remises facultatives : contrat général inchangé.


@pytest.mark.parametrize('champ,valeur', [('cout_unitaire', None), ('cmup_apres', None),
    ('quantite', float('nan')), ('stock_avant', float('inf')),
    ('stock_apres', float('-inf')), ('cmup_avant', float('nan'))])
def test_origine_compensation_inconnue_refuse_avant_ligne_saine(application, champ, valeur):
    import models
    with closing(client(application)[0]) as api:
        mauvais, sid = article(application, api)
        sain, _ = article(application, api)
        with Session(application['engine']) as db:
            for aid in (mauvais, sain):
                stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                    cout_unitaire=20, source_type='recette335origine', source_id=337)
            db.commit()
        with application['engine'].begin() as db:
            db.execute(text(f'UPDATE mouvements_stock SET {champ}=:val WHERE article_id=:id'),
                       {'val': valeur, 'id': mauvais})
        avant = photo(application)
        with Session(application['engine']) as db:
            nombre = db.query(models.MouvementStock).count()
            with pytest.raises(ValueError):
                stock.annuler_mouvements_source(db, sid, source_type='recette335origine', source_id=337)
            assert not db.dirty
            assert db.query(models.MouvementStock).count() == nombre
            db.rollback()
        assert photo(application) == avant


def test_cmup_avant_legacy_absent_reste_derivable_sans_reparer_origine(application):
    import models
    with closing(client(application)[0]) as api:
        aid, sid = article(application, api)
        with Session(application['engine']) as db:
            m = stock.enregistrer_mouvement(db, sid, aid, 'entree', 2,
                cout_unitaire=32, source_type='recette335legacy', source_id=338)
            mid = m.id
            db.commit()
        with application['engine'].begin() as db:
            db.execute(text('UPDATE mouvements_stock SET cmup_avant=NULL WHERE id=:id'), {'id': mid})
        with Session(application['engine']) as db:
            corrections = stock.annuler_mouvements_source(db, sid, source_type='recette335legacy', source_id=338)
            assert len(corrections) == 1
            assert (corrections[0].stock_apres, corrections[0].cmup_apres) == (10, 20)
            assert db.get(models.MouvementStock, mid).cmup_avant is None
            db.commit()
