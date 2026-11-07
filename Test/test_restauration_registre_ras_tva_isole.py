"""Registre099 et exports après pg_dump/pg_restore natifs sur deux cibles nonce."""
from datetime import date
from io import BytesIO
from pathlib import Path
import json
from openpyxl import load_workbook
from pypdf import PdfReader
import test_restauration_ras_tva_capture_isole as precedente
from test_logo_societe import image_data

ROOT = Path(__file__).resolve().parents[1]


def lecture(api):
    base = f'/api/tva/ras/registre/{date.today().year}'
    d = precedente.recette.ok(api.get(base))
    assert len(d['lignes']) == 2 and d['disponible']
    vente = d['totaux']['vente']
    assert vente['actives_validees']['montant'] == '75.00'
    assert vente['annulees']['montant'] == '75.00'
    sorties = {}
    for fmt in ('csv', 'xlsx', 'pdf'):
        r = api.get(base + '/export/' + fmt, params={'empreinte': d['empreinte_sha256']})
        assert r.status_code == 200, r.text[:200]
        sorties[fmt] = r.content
    pdf = PdfReader(BytesIO(sorties['pdf']))
    assert any(p.images for p in pdf.pages)
    texte = '\n'.join(p.extract_text() or '' for p in pdf.pages)
    assert '75,00' in texte and 'Annulée' in texte
    w = load_workbook(BytesIO(sorties['xlsx']))
    assert len(w['Logo société']._images) == 1
    valeurs = {s.title: list(s.values) for s in w}
    return d, sorties['csv'], texte, valeurs, sorties['pdf']


def test_581_registre_et_exports_restitues_sans_mutation(monkeypatch, tmp_path):
    preparer_orig, situation_orig = precedente.preparer, precedente.situation
    historique = ROOT / '.codex-tests/restauration575_preuve.json'
    ancien = historique.read_bytes() if historique.exists() else None
    memo, preuve = {}, {'erreur': None}

    def preparer_avec_logo(api, *args, **kwargs):
        resultat = preparer_orig(api, *args, **kwargs)
        precedente.recette.ok(api.patch('/api/societe/moi', json={'logo_url': image_data('PNG')}))
        return resultat

    def situation_avec_registre(api, rids):
        resultat = situation_orig(api, rids)
        d, csv, texte, valeurs, pdf = lecture(api)
        if not memo:
            memo.update(data=d, csv=csv, texte=texte, valeurs=valeurs, lectures=1)
        else:
            assert (d, csv, texte, valeurs) == (memo['data'], memo['csv'], memo['texte'], memo['valeurs'])
            memo['lectures'] += 1
            (tmp_path / 'registre581_restaure_fictif.pdf').write_bytes(pdf)
        return resultat

    monkeypatch.setattr(precedente, 'preparer', preparer_avec_logo)
    monkeypatch.setattr(precedente, 'situation', situation_avec_registre)
    try:
        precedente.test_restauration099_dossiers_actif_annule_acl_et_rejeu_identiques(monkeypatch, tmp_path)
        p = json.loads(historique.read_text(encoding='utf-8'))
        assert p['erreur'] is None and p['source_preservee'] and p['cibles_supprimees']
        assert memo['lectures'] == 2
        preuve.update(p, registre_csv_pdf_xlsx_logo_identiques=True, lectures_source_cible=2)
    except BaseException as exc:
        preuve['erreur'] = repr(exc)
        raise
    finally:
        (ROOT / '.codex-tests/restauration581_preuve.json').write_text(
            json.dumps(preuve, ensure_ascii=False, indent=2), encoding='utf-8')
        if ancien is not None:
            historique.write_bytes(ancien)
