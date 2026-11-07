"""087 : banque et relevés avec JWT réels et LOGIN PostgreSQL non propriétaire."""
from datetime import date
import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

import models
from postgres_isole import cluster_isole, verifier_cible_isolee
from recette_installation_vierge import BACK
from routers import banque, rapprochement
from test_complements_structure_postgres import refuser
from test_permissions_acomptes_avoirs_postgres import (
    cible as cible_commerciale, cible_documents, dossier, valider,
    originaux, conserver, solde, bilan,
)
from test_permissions_documents_commerciaux_postgres import acl, inscrire, ok

SQL = '087_permissions_banque_releves.sql'
TABLES = ('comptes_bancaires', 'rapprochement_lignes')


@pytest.fixture(scope='module')
def cible(cible_commerciale):
    c = cible_commerciale
    c['avant087'] = acl(c['owner'])
    for table in TABLES:
        refuser(c['runtime'], f'INSERT INTO public.{table} DEFAULT VALUES', '42501')
    if (BACK / SQL).is_file():
        c['migration'](SQL)
        c['migration'](SQL)
    c['client'].app.include_router(banque.router)
    c['client'].app.include_router(rapprochement.router)
    yield c


def periode():
    return {'date_debut': f'{date.today().year}-01-01',
            'date_fin': f'{date.today().year}-12-31'}


def proposer(api):
    return ok(api.get('/api/rapprochement/5141/propositions', params=periode()))


def confirmer(api, preview):
    return api.post('/api/rapprochement/5141/rapprocher-propositions', json={
        **periode(), 'empreinte': preview['empreinte'],
        'releve_ids': [r['releve_id'] for r in preview['propositions']]})


def ligne(montant=120, libelle='Relevé fictif087', sens='credit'):
    return {'date': date.today().isoformat(), 'libelle': libelle,
            'montant': montant, 'sens': sens}


def photo(cible):
    with cible['owner'].connect() as db:
        return {t: db.execute(text(f'SELECT row_to_json(t)::text FROM {t} t ORDER BY 1'))
                    .scalars().all()
                for t in (*TABLES, 'rapprochement_etats', 'rapprochement_ventilations',
                          'factures', 'reglements', 'ecritures', 'lignes_ecriture')}


@pytest.mark.parametrize('sens', ['vente', 'achat'])
@pytest.mark.parametrize('lot', [False, True], ids=['simple', 'ventile'])
def test087_cycle_reglement_import_proposition_pointage(cible, sens, lot):
    api, user, tier, fs = dossier(cible, sens)
    sid = user['societe_id']
    bank = ok(api.post('/api/banques', json={
        'banque': 'Banque fictive087', 'compte_comptable': '5141', 'devise': 'MAD'}), 201)
    ok(api.patch(f"/api/banques/{bank['id']}", json={'agence': 'Agence fictive'}))
    assert [b['id'] for b in ok(api.get('/api/banques'))] == [bank['id']]
    montant = 240 if lot else 120
    ref = 'VIR087-' + uuid.uuid4().hex[:12]
    body = {'tiers_id': tier['id'], 'date': date.today().isoformat(),
            'montant': montant, 'mode': 'virement', 'reference': ref,
            'banque': bank['banque'], 'comptabiliser': True}
    if lot:
        operation = str(uuid.uuid4())
        rows = ok(api.post('/api/reglements/par-tiers', json={**body,
            'operation_id': operation,
            'ventilations': [{'facture_id': f['id'], 'montant': 120} for f in fs]}), 201)
    else:
        rows = [ok(api.post('/api/reglements', json={**body,
            'facture_id': fs[0]['id'], 'tiers': tier['nom']}), 201)]
    assert len(rows) == (2 if lot else 1)
    valider(api)
    assert [solde(api, f['id']) for f in fs] == ([0, 0] if lot else [0, 120])
    bilan(cible, sid, [120, 120] + [120] * len(rows))
    avant = originaux(cible, sid)
    payload = {'compte': '5141', 'lignes': [ligne(montant, ref,
        'credit' if sens == 'vente' else 'debit')]}
    imported = ok(api.post('/api/rapprochement/import', json=payload), 201)
    assert (imported['nb_creees'], imported['nb_ignorees']) == (1, 0)
    rid = imported['lignes'][0]['id']
    replay = ok(api.post('/api/rapprochement/import', json=payload), 201)
    assert (replay['nb_creees'], replay['nb_ignorees']) == (0, 1)
    final = montant if sens == 'vente' else -montant
    ok(api.put('/api/rapprochement/5141/etat', json={
        **periode(), 'solde_initial': 0, 'solde_final': final}))
    situation = ok(api.get('/api/rapprochement/5141/situation', params=periode()))
    assert situation['solde_comptable_final'] == situation['solde_final'] == final
    assert situation['solde_initial'] == 0 and not situation['lecture_seule']
    p = proposer(api)
    assert len(p['propositions']) == 1
    assert p['propositions'][0]['releve_id'] == rid
    assert ok(confirmer(api, p))['nb_rapprochees'] == 1
    assert confirmer(api, p).status_code == 409
    situation = ok(api.get('/api/rapprochement/5141/situation', params=periode()))
    assert sum(e['rapprochee'] for e in situation['ecritures']) == len(rows)
    r = situation['lignes_releve'][0]
    assert r['rapprochee']
    if lot:
        assert len(r['ecriture_ligne_ids']) == 2
        assert r['ventilation_operation_id'] == operation
    else:
        assert r['ecriture_ligne_id'] is not None
    assert api.delete(f'/api/rapprochement/{rid}').status_code == 409
    assert api.patch(f'/api/rapprochement/{rid}', json={'montant': montant + 1}).status_code == 409
    ok(api.post(f'/api/rapprochement/{rid}/derapprocher', json={}))
    assert len(proposer(api)['propositions']) == 1
    ok(confirmer(api, proposer(api)))
    # La suppression publique d'une banque est une désactivation, sans DELETE SQL.
    assert api.delete(f"/api/banques/{bank['id']}").status_code == 204
    assert ok(api.get('/api/banques')) == []
    with cible['runtime'].connect() as db:
        assert db.scalar(text('SELECT actif FROM comptes_bancaires WHERE id=:id'),
                         {'id': bank['id']}) is False
        assert db.scalar(text('SELECT count(*) FROM reglements WHERE societe_id=:sid AND banque=:banque'),
                         {'sid': sid, 'banque': bank['banque']}) == len(rows)
    assert originaux(cible, sid) == avant


def test087_releve_crud_import_atomique_et_doublons(cible):
    api = cible['client']
    inscrire(cible, 'crud087')
    body = {'compte': '5141', 'lignes': [ligne(12, 'A087'), ligne(24, 'B087')]}
    result = ok(api.post('/api/rapprochement/import', json=body), 201)
    assert result['nb_creees'] == 2
    assert ok(api.post('/api/rapprochement/import', json=body), 201)['nb_ignorees'] == 2
    rid = result['lignes'][0]['id']
    edited = ok(api.patch(f'/api/rapprochement/{rid}', json={'montant': 13, 'libelle': 'Corrigé087'}))
    assert edited['montant'] == 13 and edited['libelle'] == 'Corrigé087'
    assert api.delete(f'/api/rapprochement/{rid}').status_code == 204
    assert len(ok(api.get('/api/rapprochement/5141'))) == 1
    before = photo(cible)
    invalid = {'compte': '5141', 'lignes': [ligne(10, 'Ne pas insérer'), ligne(20, sens='invalide')]}
    assert api.post('/api/rapprochement/import', json=invalid).status_code == 400
    assert photo(cible) == before
    row = ok(api.post('/api/rapprochement', json={'compte': '5141', **ligne(5, 'Manuel087')}), 201)
    assert api.delete(f"/api/rapprochement/{row['id']}").status_code == 204


def test087_acl_fermees_et_rejeu_sans_mutation(cible):
    assert (BACK / SQL).is_file()
    before, seq_before = cible['avant087']
    after, seq_after = acl(cible['owner'])
    assert seq_after == seq_before  # Aucun nouveau UPDATE de séquence, héritage005 préservé.
    assert all(after[t] == before[t] for t in before if t not in TABLES)
    for table in TABLES:
        assert after[table] == {'SELECT': True, 'INSERT': True, 'UPDATE': True,
                               'DELETE': table == 'rapprochement_lignes', 'TRUNCATE': False}
        refuser(cible['runtime'], f'TRUNCATE public.{table}', '42501')
        with cible['runtime'].connect() as db:
            seq = db.scalar(text("SELECT pg_get_serial_sequence(:table,'id')"), {'table': table})
            for op in ('USAGE', 'SELECT'):
                assert db.scalar(text('SELECT has_sequence_privilege(current_user,:seq,:op)'),
                                 {'seq': seq, 'op': op})
    refuser(cible['runtime'], 'DELETE FROM public.comptes_bancaires', '42501')
    refuser(cible['runtime'], 'CREATE TABLE public.interdit087(id integer)', '42501')
    snapshot = photo(cible)
    cible['migration'](SQL)
    assert photo(cible) == snapshot and acl(cible['owner']) == (after, seq_after)


def test087_rbac_et_isolation_societes(cible):
    api = cible['client']
    _, user = inscrire(cible, 'rbac087')
    bank = ok(api.post('/api/banques', json={'banque': 'Banque RBAC fictive087'}), 201)
    row = ok(api.post('/api/rapprochement', json={'compte': '5141', **ligne()}), 201)
    with Session(cible['owner']) as db:
        admin = db.get(models.Utilisateur, user['id'])
        email = f'lecture087-{uuid.uuid4().hex[:8]}@example.invalid'
        db.add(models.Utilisateur(societe_id=user['societe_id'], nom='Lecture fictive087',
            email=email, hashed_password=admin.hashed_password, role='lecture', actif=True))
        db.commit()
    login = ok(api.post('/api/auth/login', json={'email': email, 'password': 'Documents085!Sure'}))
    header = {'Authorization': 'Bearer ' + login['access_token']}
    assert ok(api.get('/api/banques', headers=header))
    assert ok(api.get('/api/rapprochement/5141', headers=header))
    assert api.post('/api/banques', json={'banque': 'Refus'}, headers=header).status_code == 403
    assert api.post('/api/rapprochement/import', json={'compte': '5141', 'lignes': [ligne()]}, headers=header).status_code == 403
    assert api.delete(f"/api/rapprochement/{row['id']}", headers=header).status_code == 403
    inscrire(cible, 'autre087')
    assert ok(api.get('/api/banques')) == []
    assert ok(api.get('/api/rapprochement/5141')) == []
    assert api.patch(f"/api/banques/{bank['id']}", json={'agence': 'Interdit'}).status_code == 404
    assert api.post(f"/api/rapprochement/{row['id']}/derapprocher", json={}).status_code == 404


def test087_garde_exercice_clos_aucune_mutation(cible):
    api = cible['client']
    _, user = inscrire(cible, 'clos087')
    row = ok(api.post('/api/rapprochement', json={'compte': '5141', **ligne()}), 201)
    # État fictif de garde uniquement ; ceci n'est pas une recette de clôture complète.
    with cible['owner'].begin() as db:
        db.execute(text("UPDATE exercices_comptables SET statut='cloture' WHERE societe_id=:sid AND annee=:an"),
                   {'sid': user['societe_id'], 'an': date.today().year})
    before = photo(cible)
    assert proposer(api)['lecture_seule'] is True
    assert api.post('/api/rapprochement/import', json={'compte': '5141', 'lignes': [ligne(50)]}).status_code == 409
    assert api.patch(f"/api/rapprochement/{row['id']}", json={'montant': 121}).status_code == 409
    assert api.delete(f"/api/rapprochement/{row['id']}").status_code == 409
    assert api.put('/api/rapprochement/5141/etat', json={**periode(), 'solde_initial': 0, 'solde_final': 120}).status_code == 409
    assert photo(cible) == before


def test087_role_absent_ne_cree_aucun_objet():
    with cluster_isole() as cluster:
        assert verifier_cible_isolee(cluster['url'], cluster['directory'], cluster['nonce'])
        engine = create_engine(cluster['url'])
        try:
            for _ in range(2):
                raw = engine.raw_connection()
                try:
                    with raw.cursor() as cursor:
                        cursor.execute((BACK / SQL).read_text(encoding='utf-8'))
                    raw.commit()
                finally:
                    raw.close()
            with engine.connect() as db:
                assert not db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='hisabpro')"))
                assert not db.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace"))
        finally:
            engine.dispose()
    assert not cluster['directory'].exists()
