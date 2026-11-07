"""Patch 065 — régression des formulaires et test géométrique Chromium sans backend."""
from pathlib import Path
from browser_support import chromium_executable
import asyncio
R=Path(__file__).resolve().parents[1]
base=(R/'src/styles/global.css').read_text()
forms=(R/'src/styles/forms.css').read_text()
modal=(R/'src/components/Modal.module.css').read_text()
journal=(R/'src/components/FormulaireEcriture.module.css').read_text()
invoice=(R/'src/pages/Factures.module.css').read_text()
commercial=(R/'src/pages/Commercial.module.css').read_text()
# Test separate CSS-module contexts to avoid artificial collision of names.
def make_fixture(variant):
    css=base+'\n'+modal+'\n'+forms+'\n'+{'journal':journal,'invoice':invoice,'commercial':commercial}[variant]
    header='''<div class="header"><div class="headerLeft"><span class="titre">Nouvelle écriture comptable</span></div><button class="btnFermer">x</button></div>'''
    if variant=='journal':
        cells=''.join('''<tr><td><input class="inputSm" placeholder="Ex : 6111"></td><td><input class="inputSm" placeholder="Libellé ligne"></td><td data-label="Débit (MAD)"><input class="inputSm num" placeholder="0,00"></td><td data-label="Crédit (MAD)"><input class="inputSm num" placeholder="0,00"></td><td><button class="btnSuppr">x</button></td></tr>''' for i in range(3))
        form='''<div class="contenu"><div class="actionsRapides"><button class="btnModele">Choisir un modèle d’écriture</button></div><div class="entete"><div class="formGroup"><label>Date comptable</label><input type="date" class="input"></div><div class="formGroup"><label>Journal</label><select class="input"><option>AC — Achats</option></select></div><div class="formGroup"><label>N° écriture</label><input class="input" value="AC-2026-0001"></div><div class="formGroup libelleGroup"><label>Libellé de l’écriture</label><input class="input" value="Achat fournisseur"><select class="input"><option>Choisir un libellé type</option></select></div><div class="formGroup dateJustificatifGroup"><label>Date justificatif</label><input type="date" class="input"></div><div class="formGroup referenceGroup"><label>Référence du justificatif</label><input class="input"></div></div><div class="lignesSection"><div class="lignesHeader"><span>Lignes d’écriture</span><button>Ajouter une ligne</button></div><table class="lignesTable"><thead><tr><th style="width:180px">Compte</th><th>Libellé / Tiers</th><th style="width:140px">Débit (MAD)</th><th style="width:140px">Crédit (MAD)</th><th style="width:36px"></th></tr></thead><tbody>'''+cells+'''</tbody><tfoot><tr class="totauxRow"><td colspan="2">Total</td><td>0,00</td><td>0,00</td><td></td></tr></tfoot></table></div><div class="equilibre">Écart : 0,00 MAD</div><div class="actions"><button>Annuler</button><button>Enregistrer l’écriture</button></div></div>'''
        size='xl'
    elif variant=='invoice':
        form='''<div class="formContenu"><div class="formGrid4"><div class="formGroup" style="grid-column:span 2"><label>Numéro</label><input class="input"></div><div class="formGroup" style="grid-column:span 2"><label>Référence</label><input class="input"></div></div><div class="lignesHeader">Détail facture</div><div class="lignesColHeaders"><span>Famille→Article</span><span>Qté</span><span>PU HT</span><span>Remise</span><span>TVA</span><span>Total HT</span><span></span></div><div class="ligneFactRow"><div><input class="inputSm" value="Produit" /></div><div style="display:flex;flex-direction:column"><input class="inputSm" value="1"/></div><label class="ligneChampMobile"><span>Prix unitaire HT</span><input class="inputSm" value="1000" /></label><div style="position:relative;display:flex;align-items:center"><input class="inputSm" value="0"/><span style="position:absolute;right:6px">%</span></div><div><select class="inputSm"><option>20 %</option></select></div><span class="inputSm num" style="display:flex;align-items:center;justify-content:flex-end">1000,00</span><button class="btnSuppr">x</button><div class="reducLigne">Réductions</div></div><div class="formActions"><button>Annuler</button><button>Enregistrer</button></div></div>'''
        size='lg'
    else:
        form='''<div class="formContenu"><div class="formGrid4"><div class="formGroup"><label>Référence</label><input class="input"></div><div class="formGroup"><label>Client</label><input class="input"></div></div><div class="lignesColHeaders" style="grid-template-columns:1fr 70px 100px 70px 90px 28px"><span>Description</span><span>Qté</span><span>PU HT</span><span>TVA</span><span>Total</span><span></span></div><div class="ligneRow ligneAvecTVA" style="grid-template-columns:1fr 70px 100px 70px 90px 28px"><div><input class="inputSm" value="Produit" /></div><label class="champLigneMobile"><span>Quantité</span><input class="inputSm" value="1" /></label><label class="champLigneMobile"><span>Prix unitaire HT</span><input class="inputSm" value="1000"/></label><div><select class="inputSm"><option>20 %</option></select></div><span class="inputSm num" style="display:flex;align-items:center;justify-content:flex-end">1000,00</span><button class="btnSuppr">x</button></div><div class="formActions"><button>Annuler</button><button>Enregistrer</button></div></div>'''
        size='lg'
    return '<!doctype html><html lang="fr"><meta charset="utf-8"><style>'+css+'</style><body><div class="overlay"><div class="modal '+size+'">'+header+'<div class="corps" data-form-surface>'+form+'</div></div></div></body></html>'
async def main():
    from playwright.async_api import async_playwright
    import shutil
    chromium_bin = chromium_executable()
    assert chromium_bin, 'Chromium non disponible'
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path=chromium_bin,args=['--no-sandbox'])
        for variant in ('journal','invoice','commercial'):
            for width in (1440,1058,768,620,390):
                page=await browser.new_page(viewport={'width':width,'height':800},device_scale_factor=1)
                await page.set_content(make_fixture(variant))
                data=await page.evaluate('''() => {const q=s=>document.querySelector(s);const m=q('.modal'),c=q('.corps'); const a=Array.from(c.querySelectorAll('input,select,button')).map(el=>{const r=el.getBoundingClientRect();return {name:el.outerHTML.slice(0,45),left:r.left,right:r.right}}); const r=m.getBoundingClientRect(),b=c.getBoundingClientRect();return {modal:[r.left,r.right],body:[b.left,b.right],scrollWidth:c.scrollWidth,clientWidth:c.clientWidth,overflowing:a.filter(x=>x.left < b.left-1 || x.right > b.right+1)};}''')
                ok=(data['scrollWidth']<=data['clientWidth']+1 and data['modal'][0]>=-1 and data['modal'][1]<=width+1 and not data['overflowing'])
                assert ok, f'{variant} {width}: {data}'
                await page.close()
        await browser.close()
def test_065_affichage_des_formulaires_sans_scroll_horizontal():
    import pytest
    import shutil
    pytest.importorskip('playwright.async_api')
    if not (chromium_executable()):
        pytest.skip('Chromium local absent : recette visuelle sur navigateur à faire')
    asyncio.run(main())


def test_065_le_formulaire_journal_preserve_les_champs_debit_credit():
    source = (R / 'src/components/FormulaireEcriture.jsx').read_text(encoding='utf-8')
    css = (R / 'src/components/FormulaireEcriture.module.css').read_text(encoding='utf-8')
    assert 'data-label="Débit (MAD)"' in source
    assert 'data-label="Crédit (MAD)"' in source
    assert '.lignesTable { table-layout: fixed;' in css
    assert '.lignesTable tbody tr' in css


def test_065_toutes_les_modales_partagent_un_conteneur_responsif():
    component = (R / 'src/components/Modal.jsx').read_text(encoding='utf-8')
    css = (R / 'src/components/Modal.module.css').read_text(encoding='utf-8')
    assert 'data-form-surface' in component
    assert '--modal-width: 480px' in css
    assert '--modal-width: 700px' in css
    assert '--modal-width: 900px' in css
    assert '--modal-width: 1100px' in css
    assert '100dvh' in css


def test_065_la_saisie_de_facture_et_commerciale_s_adapte():
    facture = (R / 'src/pages/Factures.module.css').read_text(encoding='utf-8')
    commercial = (R / 'src/pages/Commercial.module.css').read_text(encoding='utf-8')
    source = (R / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
    assert '.ligneFactRow > :nth-child(7)' in facture
    assert '.tableLignes tbody td[data-label]::before' in facture
    assert 'className={styles.ligneChampMobile}' in source
    assert '.ligneRow, .ligneAvecTVA' in commercial
    assert 'grid-template-columns: repeat(2, minmax(0, 1fr)) !important;' in commercial


def test_065_modales_autonomes_immobilisations_tiers_delais():
    for rel in ('src/pages/Immobilisations.module.css', 'src/pages/Tiers.module.css', 'src/pages/DelaisPaiement.module.css'):
        assert '065' in (R/rel).read_text(encoding='utf-8')



def test_065_facturation_bl_et_reconciliation_immobilisations_sans_table_large():
    cycle = (R / 'src/pages/Commercial.module.css').read_text(encoding='utf-8')
    cycle_jsx = (R / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
    immo_css = (R / 'src/pages/Immobilisations.module.css').read_text(encoding='utf-8')
    immo_jsx = (R / 'src/pages/Immobilisations.jsx').read_text(encoding='utf-8')
    assert '.cycleLineRow, .facturationRow {' in cycle
    assert '.cycleLineRow > span[data-label]::before' in cycle
    assert '<span data-label="À facturer">' in cycle_jsx
    assert '.reconciliationTable tbody tr {' in immo_css
    assert '.reconciliationTable tbody td[data-label]::before' in immo_css
    assert 'data-label="Catégorie cible"' in immo_jsx
    assert 'data-label="Compte de contrepartie"' in immo_jsx
