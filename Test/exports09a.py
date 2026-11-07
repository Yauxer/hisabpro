"""Contrôle des vrais exports en mémoire, sans archive ni fichier comptable."""
from io import BytesIO
from pathlib import Path
import json
import subprocess


def verifier_exports(data):
    from pypdf import PdfReader
    from services.liasse_pdf import generer_liasse_pdf
    from services.liasse_service import contenu_canonique, _json_default
    original = contenu_canonique(data)
    reader = PdfReader(BytesIO(generer_liasse_pdf(data)))
    texte = ' '.join(' '.join(p.extract_text() for p in reader.pages).split())
    for code in ('B6', 'B7'):
        assert code in texte, f'Section {code} absente du PDF'
    script = r'''
const fs=require('node:fs'), assert=require('node:assert/strict'), XLSX=require('xlsx');
(async()=>{
const data=JSON.parse(fs.readFileSync(0,'utf8'));
const original=JSON.stringify(data);
// Charger les fonctions réelles et leur JSON canonique ; adapter uniquement
// l'import JSON géré par Vite à un module en mémoire compris par Node.
const canon=fs.readFileSync('hisabpro-backend/services/liasse_numerotation_interne.json','utf8');
const presentation=fs.readFileSync('src/utils/liassePresentation.js','utf8').replace(
 "import numerotation from '../../hisabpro-backend/services/liasse_numerotation_interne.json'",
 'const numerotation = JSON.parse('+JSON.stringify(canon)+');');
const {numeroTableau,referenceEtic,NOTE_NUMEROTATION}=await import('data:text/javascript;base64,'+Buffer.from(presentation).toString('base64'));
const source=fs.readFileSync('src/pages/LiasseFiscale.jsx','utf8');
const code=source.slice(source.indexOf('function flattenBilan(data, side)'),source.indexOf('export default function'));
const capture=require('./Test/liasse_xlsx_capture.cjs').capturerXlsx();
new Function('XLSX','numeroTableau','referenceEtic','NOTE_NUMEROTATION','telechargerXlsxAvecLogo',code+';return exporterExcel;')(
 XLSX,numeroTableau,referenceEtic,NOTE_NUMEROTATION,capture.telecharger)(data);
assert.equal(JSON.stringify(data),original,'L’export Excel a modifié sa source');
const reloaded=XLSX.read(capture.lire(),{type:'array'});
assert.ok(reloaded.SheetNames.includes(numeroTableau('BILAN')+' Bilan Actif'));
assert.ok(reloaded.SheetNames.includes(numeroTableau('CPC')+' CPC'));
const synthese=XLSX.utils.sheet_to_json(reloaded.Sheets.Synthese,{header:1});
assert.ok(synthese.some(r=>r[0]==='Repérage des tableaux' && r[1]===NOTE_NUMEROTATION));
const rows=XLSX.utils.sheet_to_json(reloaded.Sheets.ETIC,{header:1});
const keys=['compte','intitule','total','plus_un_an','moins_un_an','echues','devises','etat_organismes_publics','entreprises_liees','effets'];
let lignes=0;
const references=new Set(data.etic.sections.map(s=>referenceEtic(s.code)));
for (const sec of data.etic.sections.filter(s=>['B6','B7'].includes(s.code))) {
 const start=rows.findIndex(r=>r[0]===referenceEtic(sec.code));
 assert.ok(start>=0,'Code original '+sec.code+' absent de sa référence interne');
 const end=rows.findIndex((r,i)=>i>start && references.has(r[0]));
 const block=rows.slice(start,end<0?rows.length:end);
 const header=block.findIndex(r=>r[0]==='Compte' && r[5]===(sec.code==='B6'?'Échues non recouvrées':'Échues non payées'));
 assert.ok(header>=0);
 for (const [i,v] of (sec.ventilation||[]).entries()) {
  assert.deepEqual(block[header+1+i],keys.map(k=>v[k]??'À compléter')); lignes++;
 }
 for (const error of sec.erreurs_ventilation||[]) assert.ok(block.some(r=>r[0]==='Contrôle de ventilation'&&r[1]===error));
}
console.log(JSON.stringify({feuilles:reloaded.SheetNames.length,ventilations:lignes}));
})().catch(e=>{console.error(e);process.exitCode=1});
'''
    result = subprocess.run(['node', '-e', script], input=json.dumps(data, default=_json_default),
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, encoding='utf-8', timeout=60)
    if result.returncode:
        raise RuntimeError('Échec de la vérification XLSX : ' + result.stderr)
    assert contenu_canonique(data) == original, 'Un export a modifié la liasse source'
    return {'pdf_pages': len(reader.pages), **json.loads(result.stdout)}
