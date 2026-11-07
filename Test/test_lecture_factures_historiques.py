"""Lecture qualifiée : contrats réels API/PostgreSQL nonce, sans réparer l'historique."""
from contextlib import closing
from datetime import date
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import models

from test_e2e_facturation_isole import application
from test_ras_lecture_conservation import client
from test_articles_alertes_stock_historique_postgres import cible
from test_validation_facture_montants_historiques_postgres import creer, photographie


@pytest.mark.parametrize('type_facture', ['vente', 'achat'])
@pytest.mark.parametrize('proforma', [False, True])
@pytest.mark.parametrize('champ,valeur', [
    ('prix_unitaire', float('nan')), ('prix_unitaire', float('inf')),
    ('prix_unitaire', float('-inf')), ('prix_unitaire', 1e308), ('quantite', None),
], ids=['nan', 'inf', 'moins-inf', 'depassement', 'quantite-null'])
def test_sources_inconnues_lisibles_et_finances_refusees(application, type_facture, proforma, champ, valeur):
    with closing(client(application)[0]) as api:
        sain = creer(api, type_facture, False, 100)
        fid = creer(api, type_facture, proforma, 100)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text(f'UPDATE lignes_facture SET {champ}=:v WHERE facture_id=:id'), {'v': valeur, 'id': fid})
            ligne = db.execute(text('SELECT id FROM lignes_facture WHERE facture_id=:id'), {'id': fid}).scalar_one()
        avant = photographie(application)
        r = api.get('/api/factures', params={'exercice': date.today().year})
        assert r.status_code == 200, r.text
        rows = {f['id']: f for f in r.json()}
        assert set(rows) == {sain, fid}
        assert rows[sain]['montants_valides'] is True
        assert (rows[sain]['total_ht'], rows[sain]['total_tva'], rows[sain]['total_ttc']) == (100, 20, 120)
        f = rows[fid]
        assert f['montants_valides'] is False and f['anomalies_montants']
        assert f['lignes'][0]['id'] == ligne
        for champ_calcule in ('total_ht', 'total_tva', 'total_ttc', 'montant_ras', 'net_a_payer', 'total_encaisse', 'total_avoirs', 'statut_credit'):
            assert f[champ_calcule] is None, champ_calcule
        assert f['lignes'][0]['montant_ht'] is None
        assert f['echeances'] == []  # Aucun échéancier artificiel à zéro.
        if champ == 'quantite' or valeur != 1e308:
            assert f['lignes'][0][champ] is None
        assert api.get(f'/api/factures/{fid}/reglements').status_code == 422
        assert api.get(f'/api/factures/{fid}/echeancier').status_code == (409 if proforma else 422)
        assert api.get(f'/api/factures/{fid}/pdf').status_code == (422 if proforma else 409)
        route = 'convertir-definitive' if proforma else 'valider'
        assert api.post(f'/api/factures/{fid}/{route}', json={}).status_code == 422
        assert photographie(application) == avant
        with closing(client(application)[0]) as autre:
            # L'inscription crée son propre exercice fictif ; figer après ce prérequis.
            avant_autre = photographie(application)
            assert autre.get('/api/factures', params={'exercice': date.today().year}).json() == []
            for suffixe in ('reglements', 'echeancier', 'pdf'):
                assert autre.get(f'/api/factures/{fid}/{suffixe}').status_code == 404
            assert photographie(application) == avant_autre


@pytest.mark.parametrize('prix', [0, 100])
def test_zero_explicitement_connu_reste_un_nombre(application, prix):
    with closing(client(application)[0]) as api:
        fid = creer(api, 'vente', False, prix)
        avant = photographie(application)
        rows = api.get('/api/factures', params={'exercice': date.today().year}).json()
        f = next(f for f in rows if f['id'] == fid)
        assert f['montants_valides'] is True and not f['anomalies_montants']
        assert f['total_ht'] == prix and f['total_ttc'] == prix * 1.2
        assert f['lignes'][0]['prix_unitaire'] == prix
        assert f['echeances'][0]['montant'] == prix * 1.2
        assert photographie(application) == avant


@pytest.mark.parametrize('champ', ['remise_globale', 'frais_transport_ht', 'escompte'])
def test_source_globale_nan_conserve_les_deux_pieces(application, champ):
    with closing(client(application)[0]) as api:
        sain = creer(api, 'vente', False)
        fid = creer(api, 'vente', False)
        cible(application)
        with application['engine'].begin() as db:
            db.execute(text(f'UPDATE factures SET {champ}=:v WHERE id=:id'), {'v': float('nan'), 'id': fid})
        avant = photographie(application)
        r = api.get('/api/factures', params={'exercice': date.today().year})
        assert r.status_code == 200, r.text
        rows = {f['id']: f for f in r.json()}
        assert rows[sain]['total_ttc'] == 120
        assert rows[fid]['montants_valides'] is False
        assert rows[fid][champ] is None and rows[fid]['total_ttc'] is None
        assert photographie(application) == avant


@pytest.mark.parametrize('prix', [float('nan'), float('inf'), 1e308])
def test_avoir_historique_invalide_ne_cache_pas_facture_saine(application, prix):
    with closing(client(application)[0]) as api:
        sain = creer(api, 'vente', False)
        fid = creer(api, 'vente', False)
        cible(application)
        # Création d'une source historique fictive défaillante sur le seul banc nonce.
        with Session(application['engine']) as db:
            f = db.get(models.Facture, fid)
            a = models.Avoir(societe_id=f.societe_id, facture_id=fid, numero='FICT-AV-'+str(fid),
                type='vente', date=date.today(), exercice=date.today().year, tiers=f.tiers,
                statut='emis', est_comptabilisee=False,
                lignes=[models.LigneAvoir(description='Avoir historique fictif', quantite=1, prix_unitaire=prix, tva=20)])
            db.add(a)
            db.commit()
        def photo():
            result = photographie(application)
            with application['engine'].connect() as db:
                for table in ('avoirs', 'lignes_avoir'):
                    result[table] = db.execute(text(f'SELECT row_to_json(t)::text FROM {table} t ORDER BY id')).scalars().all()
            return result
        avant = photo()
        r = api.get('/api/factures', params={'exercice': date.today().year})
        assert r.status_code == 200, r.text
        rows = {f['id']: f for f in r.json()}
        assert rows[sain]['montants_valides'] is True and rows[sain]['total_ttc'] == 120
        assert rows[fid]['montants_valides'] is False and rows[fid]['total_avoirs'] is None
        assert api.get(f'/api/factures/{fid}/reglements').status_code == 422
        assert photo() == avant
