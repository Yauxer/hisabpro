"""Ventes/RAS après restauration froide098 : deux API et pg_dump/restore natifs."""
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
import hashlib
import json
import httpx
from pypdf import PdfReader
from openpyxl import load_workbook
from sqlalchemy import create_engine

import test_restauration_justificatifs_acl_isole as recette
from test_ventes_raccordement_isole import facture, manuel
from test_ras_tva_simulation import donnees as simulation
from test_logo_societe import image_data
from test_permissions_tva_runtime_isole import donnees_metier
from postgres_isole import verifier_cible_isolee

ROOT = Path(__file__).resolve().parents[1]


def resultat(api):
    d = recette.ok(api.get('/api/etats/ventes/preparation/2025'))
    assert d['comptabilite']['ca_net'] == '150.00' and d['comptabilite']['ecart_ca_moins_ht'] == '50.00'
    r = recette.ok(api.post('/api/tva/ras/simulation', json=simulation()))
    assert r['retenue_tva'] == '75.00' and r['net_apres_cette_ras_tva'] == '525.00'
    contenu = api.get('/api/etats/ventes/preparation/2025/export/pdf', params={'empreinte': d['empreinte_sha256']})
    assert contenu.status_code == 200, contenu.text[:200]
    pdf = PdfReader(BytesIO(contenu.content))
    assert any(p.images for p in pdf.pages)
    texte = '\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert 'RACCORDEMENT COMPTABLE' in texte
    excel = api.get('/api/etats/ventes/preparation/2025/export/xlsx', params={'empreinte': d['empreinte_sha256']})
    assert excel.status_code == 200
    w = load_workbook(BytesIO(excel.content))
    assert len(w['Logo société']._images) == 1 and w['Comptabilité'].max_row == 3
    assert w['Synthèse']['B26'].value == 150 and w['Synthèse']['B28'].value == 50
    return {k: v for k, v in d.items() if k != 'constate_le'}, r, texte, contenu.content


def test_restauration_froide_ventes_ras_logo_et_invariants(monkeypatch, tmp_path):
    application_orig = recette.application_isolee
    client_orig = recette.client
    lancer_orig = recette.lancer_cible
    preparer_orig = recette.preparer091
    memo, preuve = {}, {'erreur': None}
    ancien = ROOT / '.codex-tests/restauration452_preuve.json'
    historique = ancien.read_bytes() if ancien.exists() else None

    def preparer098(engine, c):
        preparer_orig(engine, c)
        for nom in sorted(recette.BACK.glob('09*.sql')):
            if 92 <= int(nom.name[:3]) <= 98:
                assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
                raw = engine.raw_connection()
                try:
                    raw.autocommit = True
                    with raw.cursor() as cur: cur.execute(nom.read_text(encoding='utf8'))
                finally:
                    raw.close()

    @contextmanager
    def application098(**kwargs):
        kwargs['preparer_runtime'] = preparer098
        with application_orig(**kwargs) as app:
            yield app

    def client_ventes(app):
        api, email, password = client_orig(app)
        if not memo:
            facture(api); manuel(api)
            recette.ok(api.patch('/api/societe/moi', json={'logo_url': image_data('PNG')}))
            avant = donnees_metier(app)
            d, r, texte, pdf = resultat(api)
            assert donnees_metier(app) == avant
            memo.update(email=email, password=password, data=d, ras=r, texte=texte)
            (ROOT / '.codex-tests/ventes567_logo_fictif.pdf').write_bytes(pdf)
        return api, email, password

    def cible_ventes(c, uploads):
        assert verifier_cible_isolee(c['url'], c['directory'], c['nonce'])
        proc, url, log = lancer_orig(c, uploads)
        engine = create_engine(c['url'])
        try:
            with httpx.Client(base_url=url) as api:
                recette.connecter(api, memo['email'], memo['password'])
                avant = donnees_metier({'engine': engine})
                d, r, texte, _ = resultat(api)
                assert d == memo['data'] and r == memo['ras'] and texte == memo['texte']
                assert donnees_metier({'engine': engine}) == avant
            preuve['ventes_csv_pdf_logo_et_simulation_identiques'] = True
            return proc, url, log
        except BaseException:
            recette.arreter_processus_cree(proc)
            raise
        finally:
            engine.dispose()

    monkeypatch.setattr(recette, 'application_isolee', application098)
    monkeypatch.setattr(recette, 'client', client_ventes)
    monkeypatch.setattr(recette, 'lancer_cible', cible_ventes)
    try:
        recette.test_dump_restore_pieces_justificatifs_decision091_et_acl_natives(tmp_path)
        p = json.loads(ancien.read_text(encoding='utf8'))
        assert p['erreur'] is None and p['source_preservee'] and p['cibles_supprimees']
        assert p['tables'] == 74 and p['schema_donnees_acl_sequences_identiques']
        preuve.update(source_preservee=True, cibles_supprimees=True, tables=74,
            schema_donnees_acl_sequences_identiques=True,
            source_empreinte=memo['data']['empreinte_sha256'])
    except BaseException as exc:
        preuve['erreur'] = repr(exc)
        raise
    finally:
        (ROOT / '.codex-tests/restauration567_preuve.json').write_text(json.dumps(preuve, ensure_ascii=False, indent=2), encoding='utf8')
        if historique is not None:
            ancien.write_bytes(historique)
