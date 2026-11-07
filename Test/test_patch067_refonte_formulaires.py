"""067 — édition des brouillons et tableaux de lignes adaptatifs sans backend."""
from pathlib import Path
from browser_support import chromium_executable
import asyncio
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_067_facture_editee_regroupe_les_champs_sans_changer_la_sauvegarde():
    source = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
    edit = source.split('function FormulaireEditionFacture(', 1)[1].split('// ─── Page Factures', 1)[0]
    assert 'hp-document-editor' in edit
    assert 'title="Informations de la facture"' in edit
    assert 'title="Conditions de règlement"' in edit
    assert 'title="Lignes de facture"' in edit
    assert 'title="Frais et retenues"' in edit
    assert 'styles.editSummaryIntro' in edit
    assert '<ActionBar>' in edit
    assert 'largeur="xl"' in edit
    for field in ('setDate(', 'setTiersId(', 'setReference(', 'setDelaiPaiement(',
                  'setDateEcheanceEdit(', 'setModeReglementPrevu(', 'setReferenceReglementPrevue(',
                  'setRasTaux(', 'setTransportHT(', 'setEmballageHT(', 'majLigne(', 'handleSave'):
        assert field in edit, field
    assert 'disabled={verrouille}' in edit
    assert 'verrouille = !!facture.est_validee' in edit


def test_067_tableaux_reutilisables_facture_avoir_reception():
    invoice = (ROOT / 'src/pages/Factures.jsx').read_text(encoding='utf-8')
    commercial = (ROOT / 'src/pages/Commercial.jsx').read_text(encoding='utf-8')
    css = (ROOT / 'src/styles/forms.css').read_text(encoding='utf-8')
    assert invoice.count('hp-line-editor') == 2
    assert commercial.count('hp-line-editor') == 1
    assert 'hp-commercial-line-editor' in commercial
    assert 'hp-invoice-line-editor' in invoice
    assert '@container (max-width: 760px)' in (ROOT / 'src/pages/Commercial.module.css').read_text(encoding='utf-8')
    assert '@container (max-width: 850px)' in (ROOT / 'src/pages/Factures.module.css').read_text(encoding='utf-8')
    for label in ('Désignation', 'Quantité', 'Prix HT', 'TVA', 'Total HT'):
        assert f'data-label="{label}"' in invoice
    for label in ('Article', 'Reliquat à recevoir', 'Quantité reçue', 'Écart'):
        assert f'data-label="{label}"' in commercial
    assert 'container-type: inline-size' in css
    assert '@container (max-width: 880px)' in css
    assert 'content: attr(data-label)' in css
    assert '@container (max-width: 410px)' in css


def fixture(kind):
    css = (ROOT/'src/styles/global.css').read_text() + '\n'
    css += (ROOT/'src/components/Modal.module.css').read_text() + '\n'
    css += (ROOT/'src/styles/forms.css').read_text() + '\n'
    css += (ROOT/('src/pages/Commercial.module.css' if kind == 'reception' else 'src/pages/Factures.module.css')).read_text()
    # Tests HTML autonomes : CSS Modules n'est pas traité par Vite ici.
    css = css.replace(':global(.hp-document-editor)', '.hp-document-editor')
    if kind == 'reception':
        cols = [('Article','Réception d’une grande quantité de marchandises'), ('Reliquat à recevoir','15'),
                ('Quantité reçue','<input type="number" value="12">'), ('Écart','−3')]
    elif kind == 'avoir':
        cols = [('Sélection','<input type="checkbox" checked>'), ('Article','Marchandise retournée'),
                ('Quantité facturée','12'), ('Quantité concernée','<input type="number" value="1">'),
                ('Montant HT','1 250,00 MAD'), ('Avoir HT net','1 250,00 MAD')]
    else:
        cols = [('Désignation','<input value="Conseil et prestations de services">'),
                ('Quantité','<input type="number" value="2">'),
                ('Prix HT','<input type="number" value="1250">'),
                ('TVA','<select><option>20%</option></select>'),
                ('Total HT','2 500,00 MAD'), ('Supprimer','<button>Supprimer la ligne</button>')]
    tds = ''.join(f'<td data-label="{name}">{val}</td>' for name,val in cols)
    table = f'<div class="lignesTable hp-line-editor"><table class="tableLignes"><thead><tr>{"".join(f"<th>{name}</th>" for name,_ in cols)}</tr></thead><tbody><tr>{tds}</tr></tbody></table><button>Ajouter une ligne</button></div>'
    if kind == 'facture':
        fields = '<div class="editFields"><div class="formGroup"><label>Date</label><input type="date" value="2026-09-20"></div><div class="formGroup"><label>Statut</label><select><option>En attente</option></select></div><div class="formGroup editFullField"><label>Tiers</label><input value="ATLAS CONSEIL SARL"></div><div class="formGroup"><label>Numéro</label><input value="Brouillon #73"></div><div class="formGroup"><label>Référence</label><input value="FA-73"></div></div>'
        extras = '<div class="editExtras"><div class="editOption"><label class="editOptionLabel"><input type="checkbox" checked> Transport</label><input type="number" value="200" style="width:100px"><select class="inputSm"><option>Prestation distincte</option></select></div><div class="editRetenue"><label class="editOptionLabel">Retenue à la source (sur HT)</label><select class="inputSm"><option>Aucune</option></select></div></div>'
        total = '<div class="totauxZone"><div class="editSummaryIntro"><strong>Récapitulatif</strong><span>Montants calculés à partir des lignes et options.</span></div><div class="totauxGrid"><span>Total HT</span><span>2 500,00 MAD</span><span>TVA</span><span>500,00 MAD</span><span class="totalTTCLabel">Total TTC</span><span class="totalTTCValeur">3 000,00 MAD</span></div></div>'
        body = f'<div class="formContenu hp-document-editor"><section class="hp-form-section"><div class="hp-form-section__head">Informations de la facture</div><div class="hp-form-section__body">{fields}</div></section><section class="hp-form-section"><div class="hp-form-section__head">Lignes</div><div class="hp-form-section__body">{table}</div></section><section class="hp-form-section"><div class="hp-form-section__head">Options</div><div class="hp-form-section__body">{extras}</div></section>{total}<div class="hp-action-bar"><button>Annuler</button><button>Enregistrer les modifications</button></div></div>'
        size='xl'
    else:
        body=f'<div class="formContenu">{table}<div class="formActions"><button>Annuler</button><button>Enregistrer</button></div></div>'
        size='lg'
    return f'<!doctype html><html lang="fr"><meta name="viewport" content="width=device-width, initial-scale=1"><style>{css}</style><body><div class="overlay"><div class="modal {size}"><div class="header"><span class="titre">Formulaire</span></div><div class="corps" data-form-surface>{body}</div></div></div></body></html>'


async def verify_geometry():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, executable_path=chromium_executable(), args=['--no-sandbox'])
        try:
            for kind in ('facture', 'avoir', 'reception'):
                for width in (1440, 1058, 768, 620, 390, 320):
                    page = await browser.new_page(viewport={'width': width, 'height': 800})
                    try:
                        await page.set_content(fixture(kind))
                        result = await page.evaluate('''() => {
                          const body=document.querySelector('.corps'), modal=document.querySelector('.modal');
                          const outer=body.getBoundingClientRect();
                          const table=document.querySelector('.hp-line-editor');
                          const row=table.querySelector('tbody tr');
                          const cells=[...row.querySelectorAll('td')];
                          const controls=[...document.querySelectorAll('.corps input,.corps select,.corps button')];
                          const outside=controls.map(el=>({html:el.outerHTML.slice(0,60), r:el.getBoundingClientRect()}))
                            .filter(({r})=> r.left<outer.left-2 || r.right>outer.right+2);
                          const expectedLabels=cells.map(td=>getComputedStyle(td,'::before').content);
                          return {bodyScroll:body.scrollWidth,bodyClient:body.clientWidth,
                            modalLeft:modal.getBoundingClientRect().left,modalRight:modal.getBoundingClientRect().right,
                            containerWidth:table.clientWidth,rowWidth:row.getBoundingClientRect().width,
                            rowColumns:getComputedStyle(row).gridTemplateColumns,
                            visibleLabels:expectedLabels, controls:controls.length,outside:outside.map(x=>x.html)};
                        }''')
                        assert result['modalLeft'] >= -1 and result['modalRight'] <= width+1, (kind,width,result)
                        assert result['bodyScroll'] <= result['bodyClient']+1, (kind,width,result)
                        assert not result['outside'], (kind,width,result)
                        assert result['controls'] >= 3, (kind,width,result)
                        if result['containerWidth'] <= 880:
                            assert all('none' != x for x in result['visibleLabels']), (kind,width,result)
                    finally:
                        await page.close()
        finally:
            await browser.close()


def test_067_chromium_fiches_et_actions_sans_scroll_horizontal():
    pytest.importorskip('playwright.async_api')
    if not chromium_executable():
        pytest.skip('Chromium absent')
    asyncio.run(verify_geometry())
