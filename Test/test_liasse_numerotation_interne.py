"""Présentation T1–T25 partagée ; archives et données comptables préservées."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import json
import shutil
import subprocess

import pytest
from pypdf import PdfReader
from services.etic_service import CATALOGUE_ETIC
from services.liasse_presentation import NUMEROTATION_INTERNE, numero_tableau, reference_etic
from services.liasse_pdf import generer_liasse_pdf
from services.liasse_service import empreinte_liasse
from test_patch09_3_liasse_fiscale import _dummy_liasse

ROOT = Path(__file__).resolve().parents[1]


def test_catalogue_complet_et_code_inconnu_preserve():
    codes = [s['code'] for s in CATALOGUE_ETIC]
    assert len(codes) == 23
    assert [numero_tableau(c) for c in ['BILAN', 'CPC', *codes]] == [f'T{i}' for i in range(1, 26)]
    assert numero_tableau('ancien-code') == 'ancien-code'
    assert reference_etic('ancien-code') == 'ancien-code'
    assert numero_tableau(None) == ''
    assert reference_etic('B2bis') == 'T8 / B2bis'


def test_pdf_ancien_snapshot_sections_desordonnees_conserve_empreinte():
    data = _dummy_liasse()
    data['etic']['sections'] = [dict(s, contenu={'texte': 'Justificatif conservé'}) for s in reversed(CATALOGUE_ETIC)]
    data['etic']['sections'].append({'code': 'ancien-code', 'titre': 'Ancien <libellé> & texte', 'contenu': {}})
    before = deepcopy(data)
    empreinte = empreinte_liasse(data)
    texte = ' '.join(page.extract_text() or '' for page in PdfReader(BytesIO(generer_liasse_pdf(data))).pages)
    for code in (s['code'] for s in CATALOGUE_ETIC):
        assert reference_etic(code) in texte
    assert 'T1 - Bilan - Actif' in texte and 'T2 - Compte de Produits et Charges' in texte
    assert 'ancien-code - ETIC - Ancien <libellé> & texte' in texte
    assert 'numérotation interne HisabPro' in texte
    assert data == before and empreinte_liasse(data) == empreinte


@pytest.mark.skipif(not shutil.which('node'), reason='Node absent')
@pytest.mark.parametrize("avec_logo", [False, True])
def test_excel_reel_toutes_sections_archives_et_inconnus(avec_logo):
    script = r'''
const assert=require('node:assert/strict'), fs=require('node:fs'), XLSX=require('xlsx');
const numerotation=JSON.parse(fs.readFileSync('hisabpro-backend/services/liasse_numerotation_interne.json','utf8'));
const helper=fs.readFileSync('src/utils/liassePresentation.js','utf8').replace(/^import .*\n/,'').replaceAll('export ','');
const p=new Function('numerotation',helper+'; return {numeroTableau,referenceEtic,NOTE_NUMEROTATION};')(numerotation);
assert.equal(p.referenceEtic('B2bis'),'T8 / B2bis');
assert.equal(p.referenceEtic('ancien-code'),'ancien-code');
const source=fs.readFileSync('src/pages/LiasseFiscale.jsx','utf8');
const code=source.slice(source.indexOf('function flattenBilan(data, side)'),source.indexOf('export default function'));
const capture=require('./Test/liasse_xlsx_capture.cjs').capturerXlsx();
const exporter=new Function('XLSX','numeroTableau','referenceEtic','NOTE_NUMEROTATION','telechargerXlsxAvecLogo',code+'; return exporterExcel;')(
 XLSX,p.numeroTableau,p.referenceEtic,p.NOTE_NUMEROTATION,capture.telecharger);
const codes=Object.keys(numerotation).filter(c=>!['BILAN','CPC'].includes(c)).reverse();
const data={societe:__SOCIETE__,exercice:2026,statut:'finalisee',archive:{version:1,empreinte_sha256:'ancienne-empreinte'},
 etic:{sections:[...codes,'ancien-code'].map(code=>({code,titre:'Tableau conservé',contenu:{texte:'Justificatif'}}))},
 etats:{cpc:{lignes:[{code:'XV',libelle:'Résultat',montant:-3000,n1:0}]}}};
const before=JSON.stringify(data); exporter(data); assert.equal(JSON.stringify(data),before);
const bytes=capture.lire(), reloaded=XLSX.read(bytes,{type:'array'});
assert.equal(capture.nom(),'HISABPRO_LIASSE_2026_FINAL.xlsx');
const zip=XLSX.CFB.read(new Uint8Array(bytes),{type:'array'});
assert.equal(Boolean(XLSX.CFB.find(zip,'/xl/media/hisabpro-logo.png')),Boolean(data.societe.logo_url));
assert.equal(reloaded.SheetNames[0]==='Logo société',Boolean(data.societe.logo_url));
assert.ok(reloaded.SheetNames.includes('T1 Bilan Actif')); assert.ok(reloaded.SheetNames.includes('T1 Bilan Passif'));
const cpc=XLSX.utils.sheet_to_json(reloaded.Sheets['T2 CPC'],{header:1});
assert.deepEqual(cpc[1],['XV','Résultat',-3000,0]);
const rows=XLSX.utils.sheet_to_json(reloaded.Sheets.ETIC,{header:1});
codes.forEach(c=>assert.ok(rows.some(r=>r[0]===`${numerotation[c]} / ${c}`)));
assert.ok(rows.some(r=>r[0]==='ancien-code')); assert.ok(rows.some(r=>r[1]==='Justificatif'));
const synthese=XLSX.utils.sheet_to_json(reloaded.Sheets.Synthese,{header:1});
assert.ok(synthese.some(r=>r[0]==='Empreinte SHA-256' && r[1]==='ancienne-empreinte'));
assert.ok(synthese.some(r=>r[0]==='Repérage des tableaux' && r[1].includes('numérotation interne')));
console.log('OK T1–T25 Excel réel, montants et archive inchangés');
'''
    from test_logo_societe import image_data
    script = script.replace('__SOCIETE__', json.dumps({'raison_sociale': 'Société fictive', 'logo_url': image_data() if avec_logo else None}))
    result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True,
                            text=True, encoding='utf-8', timeout=30)
    assert result.returncode == 0, result.stderr
    assert 'OK T1–T25' in result.stdout
