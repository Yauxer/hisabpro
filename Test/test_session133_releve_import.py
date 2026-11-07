"""Lecteur JS réel : exactitude des dates/montants, rejet intégral et CSV."""
from pathlib import Path
import json
import os
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def lire(*, csv=None, rows=None, timezone="Europe/Paris"):
    script = """import {lignesDepuisTableauReleve,tableauDepuisCsv} from './src/utils/releveImport.js';
const args=JSON.parse(await new Promise(r=>{let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>r(s))}));
try {console.log(JSON.stringify({lignes:lignesDepuisTableauReleve(args.csv==null?args.rows:tableauDepuisCsv(args.csv))}))}
catch(e) {console.log(JSON.stringify({erreur:e.message}))} """
    env = {**os.environ, "TZ": timezone}
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT,
        input=json.dumps({"csv": csv, "rows": rows}, ensure_ascii=False), text=True,
        encoding="utf-8", capture_output=True, timeout=15, env=env)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize("espace", [" ", "\u00a0", "\u202f"])
@pytest.mark.parametrize("fuseau", ["Europe/Paris", "America/Los_Angeles"])
def test_csv_fr_preserve_centimes_dates_et_reference_litterale(espace, fuseau):
    resultat = lire(csv=f"\ufeffDate;Libellé;Débit;Crédit\r\n03/04/2025;002;;1{espace}234,56\r\n2025-04-04;Frais;34,56;", timezone=fuseau)
    assert resultat == {"lignes": [{"date": "2025-04-03", "libelle": "002", "montant": 1234.56, "sens": "credit"},
                                 {"date": "2025-04-04", "libelle": "Frais", "montant": 34.56, "sens": "debit"}]}
    assert 10000 + sum(l["montant"] * (1 if l["sens"] == "credit" else -1) for l in resultat["lignes"]) == 11200


@pytest.mark.parametrize("csv,attendu", [
    ('Date,Libellé,Montant\n2025-01-01,"Virement, recette","123,45"\n2025-01-02,Frais,-10.50', [123.45, 10.50]),
    ('sep=;\nDate;Libellé;Montant;Sens\n01/01/2025;"Note; avec ""guillemets""";50;Crédit', [50]),
    ('Date\tMontant\n2025-01-01\t-10', [10]),
    ('Date;Montant;Sens\n2025-01-01;20;D\n2025-01-02;20;C', [20, 20]),
    ('Date;Libellé;Montant\n2025-01-01;"Libellé\nmultiligne";20', [20]),
])
def test_variantes_csv_documentees(csv, attendu):
    resultat = lire(csv=csv)
    assert "erreur" not in resultat, resultat
    assert [l["montant"] for l in resultat["lignes"]] == attendu


@pytest.mark.parametrize("date", ["31/02/2025", "2025-02-29", "04-03-2025", "03/04/25", "", "2025-13-01"])
def test_date_invalide_refuse_tout_le_fichier(date):
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], [date, 50]])
    assert "erreur" in resultat and "Ligne 3" in resultat["erreur"]
    assert "lignes" not in resultat


@pytest.mark.parametrize("montant", ["12x", "NaN", "Infinity", "1.234", "1,234.56", "1 23,45", "", "0", True, "1e100"])
def test_montant_invalide_non_tronque_et_aucun_import_partiel(montant):
    resultat = lire(rows=[["Date", "Montant"], ["2025-01-01", 100], ["2025-01-02", montant]])
    assert "erreur" in resultat and "Ligne 3" in resultat["erreur"]
    assert "lignes" not in resultat


@pytest.mark.parametrize("rows", [
    [["Date valeur", "Montant"], ["2025-01-01", 100]],
    [["Date", "Date opération", "Montant"], ["2025-01-01", "2025-02-01", 100]],
    [["Date", "Débit"], ["2025-01-01", 100]],
    [["Date", "Débit", "Crédit", "Montant"], ["2025-01-01", 100, "", 100]],
    [["Date", "Débit", "Crédit"], ["2025-01-01", 100, 100]],
    [["Date", "Débit", "Crédit"], ["2025-01-01", -100, ""]],
    [["Date", "Montant", "Sens"], ["2025-01-01", -100, "Débit"]],
    [["Date", "Montant", "Sens"], ["2025-01-01", 100, "inconnu"]],
])
def test_ambiguite_et_double_sens_refuses(rows):
    assert "erreur" in lire(rows=rows)


def test_date_operation_expresse_prime_sur_colonne_valeur_non_utilisee():
    resultat = lire(rows=[["Date opération", "Date valeur", "Débit", "Crédit", "Solde"],
                         ["03/04/2025", "05/04/2025", "", "100,01", "9000"]])
    assert resultat["lignes"] == [{"date": "2025-04-03", "libelle": "", "montant": 100.01, "sens": "credit"}]


def test_excel_reel_et_csv_windows1252():
    script = """import * as XLSX from 'xlsx';import {dateReleve,lignesDepuisTableauReleve,decoderCsv,tableauDepuisCsv} from './src/utils/releveImport.js';
const jour=new Date(2025,3,3),wb=XLSX.utils.book_new();XLSX.utils.book_append_sheet(wb,XLSX.utils.aoa_to_sheet([['Date','Débit','Crédit'],[jour,0,1234.56]]),'Relevé');
const buf=XLSX.write(wb,{type:'buffer',bookType:'xlsx',cellDates:true});const lu=XLSX.read(buf,{type:'buffer',cellDates:true});
const rows=XLSX.utils.sheet_to_json(lu.Sheets[lu.SheetNames[0]],{header:1,defval:''});
const latin=Buffer.from('Date;Libellé;Montant\\n03/04/2025;Déjà réglé;12,34','latin1');
console.log(JSON.stringify({excel:lignesDepuisTableauReleve(rows),csv:lignesDepuisTableauReleve(tableauDepuisCsv(decoderCsv(latin)))}));"""
    result = subprocess.run(["node", "--input-type=module", "-e", script], cwd=ROOT, text=True,
                            encoding="utf-8", capture_output=True, timeout=15, env={**os.environ, "TZ": "Europe/Paris"})
    assert result.returncode == 0, result.stderr
    valeurs = json.loads(result.stdout)
    assert valeurs["excel"][0]["date"] == valeurs["csv"][0]["date"] == "2025-04-03"
    assert valeurs["excel"][0]["montant"] == 1234.56
    assert valeurs["csv"][0]["libelle"] == "Déjà réglé"


@pytest.mark.parametrize("csv", ['Date;Montant\n2025-01-01;"20', 'Date;Montant\n2025-01-01;"20"x', 'texte sans en-tête'])
def test_csv_malforme_refuse(csv):
    assert "erreur" in lire(csv=csv)
