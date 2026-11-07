"""068 — consultation des tiers : présentation et cloisonnement des rôles."""
from pathlib import Path
from browser_support import chromium_executable
import asyncio
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_068_fiche_en_modale_liste_non_retrecie_et_actions_conservees():
    src = (ROOT / 'src/pages/Tiers.jsx').read_text(encoding='utf-8')
    detail = src.split('function DetailTiers(', 1)[1].split('// ─── Page Tiers', 1)[0]
    assert '<Modal titre={tiers.nom}' in detail
    assert 'largeur="md"' in detail
    assert 'onFermer={onFermer}' in detail
    assert 'onClick={onEdit}' in detail
    assert 'onClick={onFermer}' in detail
    assert '<div className={styles.fullWidth}>' in src
    assert "panneau?.mode === 'detail' && (" in src
    assert "setPanneau({ mode: 'edit', tiers: panneau.tiers })" in src
    assert 'styles.twoCols' not in src


def test_068_client_fournisseur_roles_et_champs_optionnels():
    src = (ROOT / 'src/pages/Tiers.jsx').read_text(encoding='utf-8')
    detail = src.split('function DetailTiers(', 1)[1].split('// ─── Page Tiers', 1)[0]
    assert "tiers.type === 'client' || tiers.type === 'les_deux'" in detail
    assert "tiers.type === 'fournisseur' || tiers.type === 'les_deux'" in detail
    assert "...(estClient ? [" in detail
    assert "...(estFournisseur ? [" in detail
    for field in ('tiers.code_aux_client', 'tiers.code_aux_fournisseur', 'tiers.delai_paiement',
                  'tiers.assujetti_tva', 'tiers.taux_ras', 'tiers.ice', 'tiers.identifiant_fiscal'):
        assert field in detail
    assert 'valeur !== null && valeur !== undefined && valeur !==' in detail
    assert 'Aucune information renseignée.' in detail


def _fixture(width):
    css = (ROOT / 'src/pages/Tiers.module.css').read_text(encoding='utf-8')
    modal = (ROOT / 'src/components/Modal.module.css').read_text(encoding='utf-8')
    # Test de géométrie autonome avec la structure et les styles effectifs,
    # sans prétendre exécuter l'ensemble du frontend React.
    return f'''<!doctype html><html lang="fr"><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>*{{box-sizing:border-box}}body{{margin:0;font-family:Arial;--bg-primary:#fff;--bg-secondary:#f7f7f7;--border-light:#ddd;--text-primary:#222;--text-secondary:#666;--blue:#1262ad;--blue-light:#eef4fb;--radius-lg:10px;--radius-xl:15px;--radius-md:6px}}
    {modal}\n{css}</style><body><div class="overlay"><div class="modal md" role="dialog">
    <div class="header"><div class="headerLeft"><span class="titre">CLIENT RECETTE ALPHA</span></div><button class="btnFermer">×</button></div>
    <div class="corps"><div class="detailSheet"><div class="detailIntro"><span>Client</span><span>Fiche du tiers</span></div>
    <section class="detailSection"><h3 class="detailSectionTitle">Identité</h3><dl class="detailFields">
    <div class="detailField"><dt>Profil de facturation</dt><dd>Professionnel / entreprise</dd></div>
    <div class="detailField"><dt>ICE</dt><dd>123456789012345</dd></div></dl></section>
    <section class="detailSection"><h3 class="detailSectionTitle">Coordonnées</h3><dl class="detailFields">
    <div class="detailField"><dt>Adresse</dt><dd>Une adresse de contrôle volontairement très longue pour vérifier que les informations restent visibles</dd></div>
    <div class="detailField"><dt>Ville</dt><dd>Casablanca</dd></div></dl></section>
    <section class="detailSection"><h3 class="detailSectionTitle">Comptabilité et règlement</h3><dl class="detailFields">
    <div class="detailField"><dt>Compte client</dt><dd>3421</dd></div>
    <div class="detailField"><dt>Auxiliaire client</dt><dd>C00000014</dd></div>
    <div class="detailField"><dt>Délai de paiement</dt><dd>30 jours</dd></div>
    <div class="detailField"><dt>TVA</dt><dd>Assujetti</dd></div></dl></section>
    <div class="detailActions"><button class="btnSec">Fermer</button><button class="btnPrim">Modifier le tiers</button></div>
    </div></div></div></div></body></html>'''


async def _check_geometry():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=chromium_executable(), args=['--no-sandbox'])
        try:
            for width in (1440, 768, 560, 390, 320):
                page = await browser.new_page(viewport={'width': width, 'height': 750})
                try:
                    await page.set_content(_fixture(width))
                    result = await page.evaluate('''() => {
                      const modal=document.querySelector('.modal');
                      const body=document.querySelector('.corps');
                      const r=modal.getBoundingClientRect();
                      const controls=[...document.querySelectorAll('button')];
                      const overflow=controls.filter(el=>{const q=el.getBoundingClientRect();return q.left<r.left-1||q.right>r.right+1;});
                      return {left:r.left,right:r.right,viewport:innerWidth,bodyScroll:body.scrollWidth,
                        bodyClient:body.clientWidth,overflow:overflow.length,
                        columns:getComputedStyle(document.querySelector('.detailFields')).gridTemplateColumns};
                    }''')
                    assert result['left'] >= -1 and result['right'] <= width + 1, (width, result)
                    assert result['bodyScroll'] <= result['bodyClient'] + 1, (width, result)
                    assert result['overflow'] == 0, (width, result)
                    if width <= 560:
                        assert len(result['columns'].split()) == 1, (width, result)
                finally:
                    await page.close()
        finally:
            await browser.close()


def test_068_chromium_fiche_sans_debordement_horizontal():
    pytest.importorskip('playwright.async_api')
    if not chromium_executable():
        pytest.skip('Chromium absent')
    asyncio.run(_check_geometry())
