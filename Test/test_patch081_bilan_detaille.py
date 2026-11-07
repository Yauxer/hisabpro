"""081 : bilan détaillé, totaux conservés, comparatif absent et export PDF."""
import json
import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from jsx_syntax import assert_jsx
from browser_support import chromium_executable
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / 'hisabpro-backend'
sys.path.insert(0, str(BACKEND))
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from services.bilan_presentation import SPEC, lignes_bilan_detaille
from services.liasse_service import calculer_bilan, calculer_cpc
from pdf_generator import generer_etat_financier


@pytest.fixture
def etats():
    # Cinq écritures validées de la recette facturation + comptabilité.
    soldes = {
        '3421': {'debit': 2400, 'credit': 2400},
        '34552': {'debit': 100, 'credit': 0},
        '4455': {'debit': 200, 'credit': 400},
        '5141': {'debit': 1200, 'credit': 600},
        '6126': {'debit': 500, 'credit': 0},
        '7124': {'debit': 1000, 'credit': 2000},
        '4411': {'debit': 600, 'credit': 600},
    }
    cpc = calculer_cpc(soldes)
    bilan = calculer_bilan(soldes, cpc['resultat_net'])
    return soldes, cpc, bilan, calculer_bilan({}, 0)


def test_081_specification_unique_ecran_pdf_et_tous_groupes(etats):
    spec_front = json.loads((ROOT / 'src/data/bilanRubriques.json').read_text(encoding='utf-8'))
    assert spec_front == SPEC
    _, _, bilan, _ = etats
    for section in SPEC:
        assert len(bilan[section['side']][section['key']]) == len(section['groups']), section['key']
    assert sum(s['side'] == 'actif' for s in SPEC) == 3
    assert sum(s['side'] == 'passif' for s in SPEC) == 4
    assert sum(len(g['details']) for section in SPEC for g in section['groups']) >= 20


def test_081_totaux_du_scenario_et_non_double_comptage(etats):
    soldes, cpc, bilan, n1 = etats
    assert cpc['resultat_net'] == 500
    assert bilan['actif']['total']['net'] == bilan['passif']['total'] == 700
    for cote in ('actif', 'passif'):
        lignes = lignes_bilan_detaille(bilan, soldes, n1, {}, cote, False)
        assert lignes[-1]['label'] == f'TOTAL GÉNÉRAL {cote.upper()}'
        assert lignes[-1]['valeurs'][-2:] == ([700, None] if cote == 'passif' else [700, None])
        assert len([x for x in lignes if x['type'] == 'rubrique']) == sum(len(s['groups']) for s in SPEC if s['side'] == cote)
    actif = lignes_bilan_detaille(bilan, soldes, n1, {}, 'actif', False)
    assert next(x for x in actif if x.get('numero') == '3455')['valeurs'][0] == 100
    assert next(x for x in actif if x.get('numero') == '514')['valeurs'][2] == 600
    passif = lignes_bilan_detaille(bilan, soldes, n1, {}, 'passif', False)
    assert next(x for x in passif if x.get('numero') == 'R')['valeurs'][0] == 500
    assert next(x for x in passif if x.get('numero') == '445')['valeurs'][0] == 200


def test_081_comparatif_vide_non_remplace_par_zero(etats):
    soldes, _, bilan, n1 = etats
    for cote in ('actif', 'passif'):
        lignes = lignes_bilan_detaille(bilan, soldes, n1, {}, cote, False)
        assert all(l['valeurs'][-1] is None for l in lignes if l['type'] in ('rubrique', 'total'))
    n1_soldes = {'5141': {'debit': 75, 'credit': 0}, '1111': {'debit': 0, 'credit': 75}}
    bilan_n1 = calculer_bilan(n1_soldes, 0)
    actif = lignes_bilan_detaille(bilan, soldes, bilan_n1, n1_soldes, 'actif', True)
    assert actif[-1]['valeurs'][-1] == 75
    assert next(l for l in actif if l.get('numero') == '514')['valeurs'][-1] == 75


def test_081_depreciations_pas_de_net_detail_invente(etats):
    soldes, _, _, n1 = etats
    soldes = {**soldes, '2311': {'debit': 1000, 'credit': 0}, '28311': {'debit': 0, 'credit': 300}}
    bilan = calculer_bilan(soldes, calculer_cpc(soldes)['resultat_net'])
    actif = lignes_bilan_detaille(bilan, soldes, n1, {}, 'actif', False)
    parent = next(x for x in actif if x.get('numero') == 'C')
    sous_poste = next(x for x in actif if x.get('numero') == '231')
    assert parent['valeurs'][:3] == [1000, 300, 700]
    assert sous_poste['valeurs'][:3] == [1000, None, None]


def test_081_pdf_actif_passif_lisibles_et_complete(etats):
    from pypdf import PdfReader
    soldes, _, bilan, n1 = etats
    societe = SimpleNamespace(raison_sociale='RECETTE HISABPRO 2026', adresse='', ville='Casablanca')
    for cote in ('actif', 'passif'):
        lignes = lignes_bilan_detaille(bilan, soldes, n1, {}, cote, False)
        pdf = generer_etat_financier(
            societe, titre=f'BILAN — {cote.upper()}', exercice=2026,
            colonnes=['Brut 2026', 'Amort. & prov.', 'Net 2026', 'Net 2025']
            if cote == 'actif' else ['2026', '2025'], lignes=lignes,
            paysage=False,
        )
        lecteur = PdfReader(BytesIO(pdf))
        texte = '\n'.join(p.extract_text() or '' for p in lecteur.pages)
        assert len(lecteur.pages) >= 1
        assert 'TOTAL GÉNÉRAL' in texte and '700,00' in texte
        assert 'Brut 2026' in texte if cote == 'actif' else 'CAPITAUX PROPRES' in texte
        page = lecteur.pages[0]
        assert float(page.mediabox.width) < float(page.mediabox.height)


def test_081_projection_frontend_reelle_sans_total_double(etats):
    soldes, cpc, bilan, n1 = etats
    script = (ROOT / 'src/data/bilanPresentation.js').read_text(encoding='utf-8')
    # Exécute le module pur dans Node, sans dépendances React / Vite.
    # Les formes front sont les mêmes agrégats mais avec des clés camelCase.
    front = {
        'actifImmobilise': [{**{'label': x['libelle'], 'amort': x['amort_prov']},
                             **{k: x[k] for k in ('brut', 'net')}} for x in bilan['actif']['immobilise']],
        'actifCirculant': [{**{'label': x['libelle'], 'amort': x['amort_prov']},
                           **{k: x[k] for k in ('brut', 'net')}} for x in bilan['actif']['circulant']],
        'tresorerieActif': [{**{'label': x['libelle'], 'amort': x['amort_prov']},
                            **{k: x[k] for k in ('brut', 'net')}} for x in bilan['actif']['tresorerie']],
        'capitauxPropres': [{'label': x['libelle'], 'montant': x['montant']} for x in bilan['passif']['capitaux_propres']],
        'financementPermanent': [{'label': x['libelle'], 'montant': x['montant']} for x in bilan['passif']['financement_permanent']],
        'passifCirculant': [{'label': x['libelle'], 'montant': x['montant']} for x in bilan['passif']['passif_circulant']],
        'tresoreriePassif': [{'label': x['libelle'], 'montant': x['montant']} for x in bilan['passif']['tresorerie']],
        'totalActifImmobilise': _total_front(bilan['actif']['immobilise']),
        'totalActifCirculant': _total_front(bilan['actif']['circulant']),
        'totalTresorerieActif': _total_front(bilan['actif']['tresorerie']),
        'totalActif': {**bilan['actif']['total'], 'amort': bilan['actif']['total']['amort_prov']},
        'totalCapitauxPropres': sum(x['montant'] for x in bilan['passif']['capitaux_propres']),
        'totalFinancementPermanent': sum(x['montant'] for x in bilan['passif']['capitaux_propres'] + bilan['passif']['financement_permanent']),
        'totalPassifCirculant': sum(x['montant'] for x in bilan['passif']['passif_circulant']),
        'totalTresoreriePassif': sum(x['montant'] for x in bilan['passif']['tresorerie']),
        'totalPassif': bilan['passif']['total'],
    }
    # Comme l'année précédente n'existe pas, ses mêmes agrégats peuvent être
    # passés sans conséquence : le flag interdit d'afficher des zéros fictifs.
    runner = '''const fs=require('fs'), vm=require('vm');
    const src=fs.readFileSync(process.argv[1],'utf8')
      .replace(/import rubriques from '.\\/bilanRubriques.json'/, '')
      .replace('export function presenterBilan', 'function presenterBilan');
    const scope={rubriques:JSON.parse(fs.readFileSync(process.argv[2],'utf8'))};
    vm.createContext(scope);vm.runInContext(src+';this.presenterBilan=presenterBilan',scope);
    const a=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
    const r=scope.presenterBilan(a.front,a.soldes,a.front,{},false);
    process.stdout.write(JSON.stringify(r.map(s=>({key:s.key,side:s.side,total:s.total,n1:s.totalN1}))));'''
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp) / 'data.json'; data.write_text(json.dumps({'front': front, 'soldes': soldes}), encoding='utf8')
        result = subprocess.run(['node', '-e', runner, str(ROOT / 'src/data/bilanPresentation.js'),
                                 str(ROOT / 'src/data/bilanRubriques.json'), str(data)],
                                capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    sections = json.loads(result.stdout)
    assert next(x for x in sections if x['key'] == 'tresorerie' and x['side'] == 'actif')['total']['net'] == 600
    assert next(x for x in sections if x['key'] == 'financement_permanent')['total'] == 500
    assert all(x['n1'] is None for x in sections)


def _total_front(rows):
    return {key: sum(row[key] for row in rows) for key in ('brut', 'net')} | {
        'amort': sum(row['amort_prov'] for row in rows)
    }


def test_081_jsx_syntaxe_transpilation():
    assert_jsx(['src/pages/Bilan.jsx'])

@pytest.mark.parametrize('largeur', [1440, 1024, 768, 390])
def test_081_lecture_responsive_sans_defilement_horizontal(largeur):
    playwright = pytest.importorskip('playwright.sync_api')
    css = (ROOT / 'src/pages/Bilan.module.css').read_text(encoding='utf8')
    rows = '<tr class="rowSousTitre"><td colspan="6">ACTIF IMMOBILISÉ</td></tr>'
    rows += '<tr class="bilanGroup"><td>A</td><td>Immobilisations en non-valeurs</td>' + ''.join('<td class="colNum">700,00</td>' for _ in range(4)) + '</tr>'
    rows += '<tr class="bilanDetail"><td>211</td><td>Frais préliminaires et autres charges à répartir</td>' + ''.join('<td class="colNum">—</td>' for _ in range(4)) + '</tr>'
    rows += '<tr class="rowTotal"><td></td><td>TOTAL I — ACTIF IMMOBILISÉ</td>' + ''.join('<td class="colNum">700,00</td>' for _ in range(4)) + '</tr>'
    html = f'''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>*{{box-sizing:border-box}} body{{margin:0}} .shell{{display:flex;max-width:100vw;}}
    .sidebar{{width:188px;flex:none}} .main{{flex:1;min-width:0}} @media(max-width:650px){{.sidebar{{display:none}}}}
    {css}</style></head><body><div class="shell"><aside class="sidebar"></aside>
    <main class="main"><div class="page"><div class="content"><div class="bilanColonne"><div class="card">
    <div class="bilanTableScroll"><table class="table bilanDetailTable bilanActif"><colgroup>
    <col class="bilanRefCol"><col class="bilanLibelleCol"><col><col><col><col></colgroup>
    <thead><tr class="rowEntete"><th>Réf.</th><th>ACTIF</th><th>Brut</th><th>Amort.</th><th>Net N</th><th>Net N-1</th></tr></thead>
    <tbody>{rows}</tbody></table></div></div></div></div></div></main></div></body></html>'''
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch(executable_path=chromium_executable(), headless=True, args=['--no-sandbox'])
        except Exception as exc:
            pytest.skip(f'Chromium indisponible : {exc}')
        try:
            page = browser.new_page(viewport={'width': largeur, 'height': 800})
            page.set_content(html)
            geometrie = page.evaluate('''() => ({
                doc:document.documentElement.scrollWidth, viewport:innerWidth,
                scroll:document.querySelector('.bilanTableScroll').scrollWidth,
                disponible:document.querySelector('.bilanTableScroll').clientWidth,
                dernier:document.querySelector('.rowTotal .colNum:last-child').getBoundingClientRect().right,
                largeur:document.querySelector('.bilanTableScroll').getBoundingClientRect().right
            })''')
            assert geometrie['doc'] <= geometrie['viewport'] + 2, geometrie
            assert geometrie['scroll'] <= geometrie['disponible'] + 2, geometrie
            assert geometrie['dernier'] <= geometrie['largeur'] + 2, geometrie
        finally:
            browser.close()
