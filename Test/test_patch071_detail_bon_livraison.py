"""071 — fiche de lecture des bons de livraison et liaison à leur commande."""
import ast
import asyncio
import shutil
from pathlib import Path
from browser_support import chromium_executable
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / 'src/pages/Commercial.jsx'
CSS = ROOT / 'src/pages/Commercial.module.css'
BACKEND = ROOT / 'hisabpro-backend/routers/commercial.py'
SCHEMAS = ROOT / 'hisabpro-backend/schemas.py'


def _bloc_onglet():
    source = UI.read_text(encoding='utf-8')
    return source.split('function OngletBonsLivraison({ annee }) {', 1)[1].split('function FormulaireReglementComplet', 1)[0]


def test_071_numero_bl_cliquable_et_modale_lecture_seule():
    src = UI.read_text(encoding='utf-8')
    onglet = _bloc_onglet()
    detail = src.split('function DetailBonLivraison(', 1)[1].split('function OngletBonsLivraison(', 1)[0]
    assert 'className={styles.blDetailTrigger}' in onglet
    assert 'onClick={() => setBlDetailId(bl.id)}' in onglet
    assert 'aria-label={`Consulter le bon ${bl.numero}`}' in onglet
    assert 'const blDetail = bls.find(bl => bl.id === blDetailId)' in onglet
    assert '<DetailBonLivraison bl={blDetail} onFermer={() => setBlDetailId(null)} />' in onglet
    assert 'largeur="lg"' in detail
    for expected in ('bl.bon_commande_numero', 'bl.tiers', 'bl.statut', 'bl.lignes',
                     'ligne.quantite_livree', 'ligne.prix_unitaire', 'ligne.reste_a_facturer',
                     'bl.montant_facture_ht', 'bl.reste_a_facturer_ht', 'bl.facture_numeros'):
        assert expected in detail, expected
    assert 'onClick={onFermer}' in detail
    assert 'method: ' not in detail and 'apiFetch(' not in detail  # Consultation sans mutation.
    assert 'ouvrirFacturationBL(bl)' in onglet  # Parcours existant préservé.
    assert "changerStatut(bl, 'expedie')" in onglet
    assert "changerStatut(bl, 'livre')" in onglet


def test_071_numero_bc_fourni_par_api_sans_changement_de_base():
    src = BACKEND.read_text(encoding='utf-8')
    schema = SCHEMAS.read_text(encoding='utf-8')
    listing = src.split('@router_bl.get("",', 1)[1].split('@router_bl.post("",', 1)[0]
    assert 'joinedload(models.BonLivraison.bon_commande)' in listing
    assert 'societe_id=current_user["societe_id"]' in listing
    assert 'bon_commande_numero: Optional[str] = None' in schema

    tree = ast.parse(src)
    fmt = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_fmt_bl')
    context = {'_situation_facturation_bl': lambda db, sid, bl: {'reste_a_facturer_ht': 2000.0}}
    exec(compile(ast.Module(body=[fmt], type_ignores=[]), str(BACKEND), 'exec'), context)
    ligne = SimpleNamespace(id=5, description='Prestation', quantite_livree=2)
    bl = SimpleNamespace(societe_id=1, bon_commande=SimpleNamespace(numero='BC-2026-001'), lignes=[ligne])
    formatted = context['_fmt_bl'](bl, db=object())
    assert formatted['bon_commande_numero'] == 'BC-2026-001'
    assert formatted['lignes'][0]['quantite_livree'] == 2
    assert formatted['reste_a_facturer_ht'] == 2000.0
    bl.bon_commande = None
    assert context['_fmt_bl'](bl)['bon_commande_numero'] is None


def test_071_separation_statut_logistique_et_avancement_commande():
    src = BACKEND.read_text(encoding='utf-8')
    create = src.split('@router_bc.post("/{bc_id}/convertir-bl"', 1)[1].split('# BON DE LIVRAISON', 1)[0]
    detail = UI.read_text(encoding='utf-8').split('function DetailBonLivraison(', 1)[1].split('function OngletBonsLivraison(', 1)[0]
    assert 'statut="en_preparation"' in create
    assert 'bc.statut = "livre" if solde else "partiel"' in create
    assert "bl.statut === 'en_preparation'" in detail
    assert 'son expédition ou sa remise effective n’a pas encore été confirmée' in detail


def _html_fixture():
    css = CSS.read_text(encoding='utf-8')
    modal = (ROOT / 'src/components/Modal.module.css').read_text(encoding='utf-8')
    return '''<!doctype html><html lang="fr"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>*{box-sizing:border-box}body{margin:0;font-family:Arial;--bg-primary:#fff;--bg-secondary:#f7f7f7;--border-light:#ddd;--text-primary:#222;--text-secondary:#666;--text-tertiary:#777;--blue:#1262ad;--blue-dark:#10518a;--radius-lg:10px;--radius-xl:15px;--radius-md:6px;--radius-sm:4px}
    ''' + modal + css + '''</style><body><div class="overlay"><div class="modal lg" role="dialog">
      <div class="header"><span class="titre">Bon de livraison BL-2026-001</span><button>Fermer</button></div>
      <div class="corps"><div class="blDetail">
        <section class="blDetailSection"><h3>Informations du document</h3><dl class="blDetailFields">
          <div><dt>Client</dt><dd>CLIENT RECETTE ALPHA</dd></div>
          <div><dt>Bon de commande d’origine</dt><dd>BC-2026-001</dd></div></dl></section>
        <section class="blDetailSection"><h3>Lignes du document</h3><div class="blDetailLines" role="list">
          <div class="blDetailLine" role="listitem"><div class="blDetailDescription"><span class="blDetailLabel">Désignation</span><strong>Prestation de conseil — recette HisabPro</strong></div>
            <div><span class="blDetailLabel">Qté inscrite</span><span>2</span></div>
            <div><span class="blDetailLabel">Prix unitaire HT</span><span>1 000,00 MAD</span></div>
            <div><span class="blDetailLabel">TVA</span><span>20 %</span></div>
            <div><span class="blDetailLabel">Qté facturée</span><span>0</span></div>
            <div><span class="blDetailLabel">Reste à facturer</span><span>2</span></div></div></div></section>
        <section class="blDetailSection"><h3>Suivi de facturation</h3><dl class="blDetailFields">
          <div><dt>Montant des lignes HT</dt><dd>2 000,00 MAD</dd></div>
          <div><dt>Reste à facturer HT</dt><dd>2 000,00 MAD</dd></div></dl></section>
        <p class="blDetailNotice">Son statut En préparation signifie que sa remise effective n’a pas encore été confirmée.</p>
        <div class="formActions"><button class="btnSec">Fermer</button></div>
      </div></div></div></body></html>'''


async def _chromium_check():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=chromium_executable(), args=['--no-sandbox'])
        try:
            for width in (1440, 768, 520, 390, 320):
                page = await browser.new_page(viewport={'width': width, 'height': 780})
                try:
                    await page.set_content(_html_fixture())
                    geometry = await page.evaluate('''() => {
                      const dialog=document.querySelector('.modal');const body=document.querySelector('.corps');
                      const dialogBox=dialog.getBoundingClientRect();
                      const outside=[...document.querySelectorAll('.blDetailLine span, .blDetailLine strong, .blDetailFields dd, button')]
                        .filter(el=>{const r=el.getBoundingClientRect();return r.left<dialogBox.left-1||r.right>dialogBox.right+1;})
                        .map(el=>el.textContent);
                      return {dialogLeft:dialogBox.left,dialogRight:dialogBox.right,
                        scrollWidth:body.scrollWidth,clientWidth:body.clientWidth,outside};
                    }''')
                    assert geometry['dialogLeft'] >= -1 and geometry['dialogRight'] <= width+1, (width, geometry)
                    assert geometry['scrollWidth'] <= geometry['clientWidth']+1, (width, geometry)
                    assert not geometry['outside'], (width, geometry)
                finally:
                    await page.close()
        finally:
            await browser.close()


def test_071_modal_bl_responsive_chromium():
    pytest.importorskip('playwright.async_api')
    if not chromium_executable():
        pytest.skip('Chromium absent')
    asyncio.run(_chromium_check())
