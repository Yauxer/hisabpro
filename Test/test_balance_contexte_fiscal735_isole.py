"""Contexte fiscal externe : exactitude, inconnus, isolation et versions natives."""
from contextlib import closing
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from uuid import uuid4
from zipfile import ZipFile
import hashlib
import json

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy.orm import Session
from test_balance_passage_fiscal725_isole import (
    application, application103, application102, application101, application100, application099,
    application098, application097, application093, application092, application091, application090,
    application089, application087, migration, client, ok, BASE, donnees_metier, source,
    creer as creer_base, body as b12_body, url as b12_url, image_data)


def url(v):
    return BASE + f'/{v["id"]}/contexte-fiscal'


def creer(api, b12=True):
    v = creer_base(api, False)
    return ok(api.post(b12_url(v), json=b12_body(v)), 201) if b12 else v


def body(v):
    def ligne(nature, ref, **kw):
        return {'nature': nature, 'reference_source': ref, **kw}
    return {'cle': str(uuid4()), 'empreinte_parent': v['empreinte_sha256'], 'tables': [
        {'code': code, 'statut': 'documente', 'justification': 'Déclaration fictive735, à revoir', 'lignes': rows}
        for code, rows in [
            ('CF-CM', [ligne('CM fictive sans qualification automatique', 'NOTE-CM735', montant='3000')]),
            ('CF-CSS', [ligne('CSS fictive explicitement nulle', 'NOTE-CSS735', montant='0')]),
            ('CF-CREDITS', [
                ligne('Crédit A fictif', 'CERT-A735', montant='300', deja_impute='100'),
                ligne('Crédit B fictif', 'CERT-B735', montant='200', deja_impute='50'),
                ligne('Crédit C fictif', 'CERT-C735', montant='100', deja_impute='0')]),
            ('CF-ACOMPTES', [ligne('Acompte fictif', 'QUITTANCE735', verse='1000',
                                  credit_anterieur='100', credits_deja_imputes='150')]),
        ]]}


def controles(v):
    return v['contenu']['contexte_fiscal_documentaire']['controle_contexte_fiscal']


@pytest.mark.parametrize('cas', ['normal', 'vide', 'neant', 'zero', 'partiel', 'ecart', 'grand', 'sans_b12'])
def test_735_oracles_exactitude_et_inconnus(cas):
    from services.balance_contexte_fiscal_service import calculer_controles
    d = source(); q = body({'empreinte_sha256': 'a' * 64})
    if cas in ('vide', 'neant'):
        for t in q['tables']:
            t.update(lignes=[], statut='a_completer' if cas == 'vide' else 'neant_declare')
    elif cas == 'zero':
        for t in q['tables']:
            for r in t['lignes']:
                for k in set(r) - {'nature', 'reference_source'}:
                    r[k] = '0'
    elif cas == 'partiel':
        q['tables'][2]['lignes'][0]['deja_impute'] = None
    elif cas == 'ecart':
        q['tables'][3]['lignes'][0]['credits_deja_imputes'] = '149.99'
    elif cas == 'grand':
        for r in q['tables'][2]['lignes']:
            r['montant'] = '9999999999999.99'
    avant = deepcopy(d); c = calculer_controles(d, q); m = c['montants']
    assert d == avant and c['solde_final'] is c['impot_du'] is None
    assert not any(c[k] for k in ('pret_a_deposer', 'liquidation_confirmee', 'paiement_confirme'))
    json.dumps(c, allow_nan=False)
    if cas in ('vide', 'neant'):
        assert all(v is None for v in m.values())
    elif cas == 'zero':
        assert all(v == '0.00' for v in m.values())
    else:
        assert m['cm_declaree'] == '3000.00' and m['css_declaree'] == '0.00'
        assert m['acomptes_verses'] == '1000.00' and m['credit_anterieur_impute'] == '100.00'
        if cas == 'partiel':
            assert m['credits_total'] == '600.00'
            assert m['credits_deja_imputes'] is m['credits_restants'] is m['ecart_imputations'] is None
        elif cas == 'grand':
            assert m['credits_total'] == '29999999999999.97' and m['credits_restants'] == '29999999999849.97'
        else:
            assert m['credits_total'] == '600.00' and m['credits_restants'] == '450.00'
            assert m['ecart_imputations'] == ('-0.01' if cas == 'ecart' else '0.00')
            assert bool(c['alertes']) == (cas == 'ecart')


def test_735_versions_rejeu_sans_recalcul_et_metier(application, monkeypatch):
    from services import balance_contexte_fiscal_service as s
    from routers.etats import BalanceContexteFiscalIn
    with closing(client(application)[0]) as api:
        v = creer(api); avant = donnees_metier(application)
        assert ok(api.get(url(v)))['controle_contexte_fiscal'] is None
        b = body(v); r = ok(api.post(url(v), json=b), 201)
        vue = ok(api.get(url(r))); c = controles(r)
        assert c['source_b12']['is_theorique_taux_declare'] == '1460.00'
        assert c['montants']['credits_restants'] == '450.00'
        assert ok(api.get(BASE + f'/{v["id"]}')) == v
        assert all(r['contenu'][k] == x for k, x in v['contenu'].items())
        def interdit(*a, **kw):
            raise AssertionError('Pas de recalcul à la lecture, au rejeu ou à l’export')
        monkeypatch.setattr(s, 'calculer_controles', interdit)
        with Session(application['engine']) as db:
            assert s.conserver(db, ok(api.get('/api/auth/me')), v['id'], BalanceContexteFiscalIn.model_validate(b)) == r
        assert ok(api.get(url(r))) == vue and api.get(BASE + f'/{r["id"]}/zip').status_code == 200
        apres = donnees_metier(application)
        assert all(apres[k] == x for k, x in avant.items() if k != 'liasse_balances_preparation')


@pytest.mark.parametrize('champ,valeur', [
    ('montant', 'NaN'), ('montant', 'Infinity'), ('montant', True), ('montant', '-1'),
    ('montant', '0.001'), ('montant', '1e9999'), ('montant', '10000000000000'),
    ('deja_impute', '301'), ('deja_impute', '-0.01'), ('deja_impute', False),
    ('reference_source', ''), ('nature', ''), ('nature', 'X' * 2001), ('inconnu', '1')])
def test_735_rejets_sans_mutation(application, champ, valeur):
    with closing(client(application)[0]) as api:
        v = creer(api, False); b = body(v)
        b['tables'][2]['lignes'][0][champ] = valeur
        avant = donnees_metier(application)
        assert api.post(url(v), json=b).status_code == 422 and donnees_metier(application) == avant


@pytest.mark.parametrize('cas', ['omission', 'doublon_table', 'doublon_credit', 'deux_cm', '51credits', '21acomptes', 'solde_injecte'])
def test_735_structures_et_limites(application, cas):
    with closing(client(application)[0]) as api:
        v = creer(api, False); b = body(v)
        if cas == 'omission': b['tables'].pop()
        elif cas == 'doublon_table': b['tables'][3] = deepcopy(b['tables'][0])
        elif cas == 'doublon_credit': b['tables'][2]['lignes'] *= 2
        elif cas == 'deux_cm': b['tables'][0]['lignes'] *= 2
        elif cas in ('51credits', '21acomptes'):
            t = b['tables'][2 if cas == '51credits' else 3]
            t['lignes'] = [{**t['lignes'][0], 'nature': str(i)} for i in range(51 if cas == '51credits' else 21)]
        else: b['solde_final'] = '0'
        avant = donnees_metier(application)
        assert api.post(url(v), json=b).status_code == 422 and donnees_metier(application) == avant


@pytest.mark.parametrize('initial', [True, False])
def test_735_b12_modifie_restant_fige_et_actualisation_explicite(application, initial):
    with closing(client(application)[0]) as api:
        v = creer(api, initial); r = ok(api.post(url(v), json=body(v)), 201)
        ancien = deepcopy(controles(r)); b = b12_body(r); b['tables'][0]['lignes'][0]['taux_is'] = '10'
        v2 = ok(api.post(b12_url(r), json=b), 201)
        vue = ok(api.get(url(v2)))
        assert vue['source_b12_modifiee'] and vue['alertes'] and controles(v2) == ancien
        assert ok(api.get(url(r)))['source_b12_modifiee'] is False
        nouveau = ok(api.post(url(v2), json=body(v2)), 201)
        assert not ok(api.get(url(nouveau)))['source_b12_modifiee']
        assert controles(nouveau)['source_b12']['is_theorique_taux_declare'] == '730.00'
        assert controles(r) == ancien


def test_735_droits_societes_devise_hash_concurrence(application):
    with closing(client(application)[0]) as api, closing(client(application)[0]) as autre:
        v = creer(api); b = body(v)
        assert autre.get(url(v)).status_code == autre.post(url(v), json=b).status_code == 404
        assert api.post(url(v), json={**b, 'empreinte_parent': 'a' * 64}).status_code == 409
        sid = ok(api.get('/api/auth/me'))['societe_id']; email = ok(autre.get('/api/auth/me'))['email']
        ok(api.post(f'/api/societes/{sid}/inviter', params={'email': email, 'role': 'lecture'}))
        autre.headers['Authorization'] = 'Bearer ' + ok(autre.post(f'/api/societes/switcher/{sid}'))['access_token']
        assert autre.get(url(v)).status_code == 200 and autre.post(url(v), json=b).status_code == 403
        with ThreadPoolExecutor(max_workers=2) as pool:
            rs = list(pool.map(lambda _: api.post(url(v), json=b), range(2)))
        assert [r.status_code for r in rs] == [201, 201] and rs[0].json() == rs[1].json()
        b['tables'][0]['lignes'][0]['montant'] = '3001'
        assert api.post(url(v), json=b).status_code == 409
        ok(api.patch('/api/societe/moi', json={'devise': 'EUR'}))
        assert api.post(url(v), json=body(v)).status_code == 422
        assert api.get(url(rs[0].json())).status_code == 200


def test_735_exports_logo_inconnus_formules_et_manifestes(application, tmp_path):
    with closing(client(application)[0]) as api:
        v = creer(api); b = body(v)
        b['tables'][2]['lignes'][0]['reference_source'] = '=CERT-FICTIF735'
        b['tables'][0]['lignes'][0]['montant'] = None
        b['tables'][2]['lignes'][0]['nature'] = 'Source longue ' + 'texte justifié ' * 90
        r = ok(api.post(url(v), json=b), 201)
        ok(api.patch('/api/societe/moi', json={'logo_url': image_data('PNG')}))
        avant = donnees_metier(application); rep = api.get(BASE + f'/{r["id"]}/zip')
        assert rep.status_code == 200, rep.text[:300] if rep.status_code != 200 else ''
        with ZipFile(BytesIO(rep.content)) as z:
            assert z.testzip() is None
            vue = json.loads(z.read('contexte_fiscal_documentaire.json'))
            assert vue['controle_contexte_fiscal'] == controles(r)
            m = json.loads(z.read('MANIFESTE_SHA256.json'))
            assert set(z.namelist()) == set(m['fichiers']) | {'MANIFESTE_SHA256.json'}
            for n, h in m['fichiers'].items():
                assert len(z.read(n)) == h['taille'] and hashlib.sha256(z.read(n)).hexdigest() == h['sha256']
            w = load_workbook(BytesIO(z.read('preparation.xlsx')))
            totaux = dict(list(w['Totaux contexte fiscal'].values)[1:])
            assert totaux['CM déclarée'] == 'Indisponible' and totaux['Crédits déclarés moins part déjà imputée'] == 450
            assert w['CF-CREDITS']['F2'].value == '=CERT-FICTIF735' and w['CF-CREDITS']['F2'].data_type == 's'
            with ZipFile(BytesIO(z.read('preparation.xlsx'))) as x:
                assert any(p.startswith('xl/media/') for p in x.namelist())
            pdf = PdfReader(BytesIO(z.read('preparation.pdf')))
            texte = '\n'.join(p.extract_text() or '' for p in pdf.pages)
            assert 'CF-CREDITS' in texte and '=CERT-FICTIF735' in texte and '450,00' in texte
            assert any(p.images for p in pdf.pages)
            (tmp_path / 'contexte735.pdf').write_bytes(z.read('preparation.pdf'))
        assert donnees_metier(application) == avant
