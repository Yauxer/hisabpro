from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import pytest
from pypdf import PdfReader
from test_patch09_3_liasse_fiscale import _dummy_liasse
from services.liasse_pdf import generer_liasse_pdf

ROOT = Path(__file__).resolve().parents[1]


def section(code="B6"):
    return {"code": code, "titre": "État", "mode": "assiste", "complete": False,
            "automatique": {"colonnes": ["compte", "montant"], "lignes": [
                {"compte": "3421", "montant": 120, "echeance_auto_total": 120,
                 "echeance_auto_ecart": 0, "echeance_auto_non_qualifie": 40,
                 "echeance_auto_anomalies_sources": [{"facture_id": 1, "numero": "02",
                    "reste_du": 40, "motifs": ["Écriture <absente> & échéance inconnue."]}]}]},
            "ventilation": [{"compte": "3421", "intitule": "Clients <test> & associés",
                "total": 120, "plus_un_an": 0, "moins_un_an": None, "echues": 80,
                "devises": 0, "etat_organismes_publics": 0, "entreprises_liees": 0, "effets": 0}],
            "erreurs_ventilation": ["Ventilation incomplète : 40 MAD à compléter."],
            "contenu": {"notes": "Pièce <02> & référence <002> à revoir."}}


@pytest.mark.parametrize("code", ["B6", "B7"])
def test_pdf_conserve_ventilation_et_diagnostics_avec_caracteres_speciaux(code):
    data = _dummy_liasse()
    data["etic"]["sections"] = [section(code)]
    reader = PdfReader(BytesIO(generer_liasse_pdf(data)))
    texte = " ".join("\n".join(page.extract_text() for page in reader.pages).split())
    assert "Échues non recouvrées" in texte if code == "B6" else "Échues non payées" in texte
    assert "Clients <test> & associés" in texte
    assert "source non qualifiée 40.00" in texte
    assert "Écriture <absente> & échéance inconnue." in texte
    assert "Ventilation incomplète" in texte
    assert "Pièce <02> & référence <002>" in texte


@pytest.mark.skipif(not shutil.which("node"), reason="Node absent")
def test_export_excel_reel_preserve_zero_inconnus_et_diagnostics():
    script = r'''
const assert=require('node:assert/strict');
const fs=require('node:fs');
const XLSX=require('xlsx');
const source=fs.readFileSync('src/pages/LiasseFiscale.jsx','utf8');
const code=source.slice(source.indexOf('function flattenBilan(data, side)'),source.indexOf('export default function'));
const capture=require('./Test/liasse_xlsx_capture.cjs').capturerXlsx();
const numerotation=JSON.parse(fs.readFileSync('hisabpro-backend/services/liasse_numerotation_interne.json','utf8'));
const helper=fs.readFileSync('src/utils/liassePresentation.js','utf8').replace(/^import .*\n/,'').replaceAll('export ','');
const presentation=new Function('numerotation',helper+'; return {numeroTableau,referenceEtic,NOTE_NUMEROTATION};')(numerotation);
const exporter=new Function('XLSX','numeroTableau','referenceEtic','NOTE_NUMEROTATION','telechargerXlsxAvecLogo',code+'; return exporterExcel;')(XLSX,presentation.numeroTableau,presentation.referenceEtic,presentation.NOTE_NUMEROTATION,capture.telecharger);
const section={code:'B7',titre:'Dettes',automatique:{colonnes:['compte','montant'],lignes:[
 {compte:'4411',montant:120,echeance_auto_total:120,echeance_auto_ecart:0,echeance_auto_non_qualifie:40,
  echeance_auto_anomalies_sources:[{numero:'002',reste_du:40,motifs:['Écriture absente']}],
  echeance_auto_sources_hors_solde:[{compte:'44110001',total_source:960,anomalies_sources:[{numero:'FA-016',motifs:['Compte divergent']}]}]}]},
 ventilation:[{compte:'4411',intitule:'Fournisseurs',total:120,plus_un_an:0,moins_un_an:null,echues:80,
 devises:0,etat_organismes_publics:0,entreprises_liees:0,effets:0}],erreurs_ventilation:['40 MAD à compléter']};
exporter({exercice:2026,statut:'brouillon',etic:{sections:[section]}});
const reloaded=XLSX.read(capture.lire(),{type:'array'});
const rows=XLSX.utils.sheet_to_json(reloaded.Sheets.ETIC,{header:1});
const header=rows.findIndex(r=>r[0]==='Compte' && r[5]==='Échues non payées');
assert.ok(header>=0);
assert.deepEqual(rows[header+1],['4411','Fournisseurs',120,0,'À compléter',80,0,0,0,0]);
assert.ok(rows.some(r=>r[0]==='Source à vérifier' && r[2]==='002'));
assert.ok(rows.some(r=>r[0]==='Contrôle de ventilation' && r[1]==='40 MAD à compléter'));
assert.ok(rows.some(r=>r[0]==='Compte source absent des soldes' && r[1]==='44110001' && r[2]===960));
console.log('OK Excel B7 ventilation, zéros, inconnus et diagnostics');
'''
    result = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0, result.stderr
    assert "OK Excel" in result.stdout
