"""Contrôles des livrables et de l'oracle fictif, sans connexion PostgreSQL."""
import csv
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("cahier_recette",ROOT/"Test"/"generer_cahier_recette.py")
cahier=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cahier)


@pytest.fixture(scope="module")
def data():
    return cahier.build_data()


@pytest.fixture(scope="module")
def artifacts(tmp_path_factory):
    out=tmp_path_factory.mktemp("cahier")
    data,cases=cahier.generate(out)
    return out,data,cases


def test_chaque_piece_est_equilibree_et_les_references_sont_uniques(data):
    refs=[]
    for entry in data["operations"]:
        refs.append(entry["reference_recette"])
        assert sum(Decimal(row["debit"])-Decimal(row["credit"]) for row in entry["lignes"])==0
    assert len(set(refs))==len(refs)
    assert len(refs)==50


def test_oracle_resultat_et_fiscalite_calcules_independamment(data):
    expected=data["attendus"]
    soldes=cahier.balances(data["operations"])
    signed=lambda c:Decimal(soldes.get(c,{"debit":"0"})["debit"])-Decimal(soldes.get(c,{"credit":"0"})["credit"])
    result=sum((-signed(c) for c in soldes if c.startswith("7")),Decimal(0))-sum((signed(c) for c in soldes if c.startswith("6") and not c.startswith("67")),Decimal(0))
    assert result==Decimal("129830")
    tax_profit=result+Decimal("500")+Decimal("1500")+Decimal("2000")
    assert tax_profit==Decimal(expected["benefice_fiscal"])==Decimal("133830")
    assert cahier.dec(tax_profit*Decimal("0.175"))==Decimal(expected["is_theorique"])==Decimal("23420.25")
    assert result-Decimal(expected["is_theorique"])==Decimal(expected["resultat_net"])==Decimal("106409.75")
    assert Decimal(expected["is_theorique"])-Decimal(expected["credit_is"])==Decimal(expected["solde_is"])==Decimal("23220.25")


def test_stock_physique_cmup_marge_et_caf_independants(data):
    expected=data["attendus"]
    quantity=Decimal("100")+Decimal("100")-Decimal("100")+Decimal("10")-Decimal("50")
    cmup=(Decimal("100")*100+Decimal("100")*120)/200
    assert quantity==Decimal(expected["stock_quantite"])==60
    assert cmup==Decimal(expected["stock_cmup"])==110
    assert quantity*cmup==Decimal(expected["stock_valeur"])==6600
    assert Decimal("25000")-2500+15000-(Decimal("22000")-quantity*cmup)==Decimal(expected["marge_brute"])==22100
    assert Decimal(expected["resultat_net"])+4800+1500==Decimal(expected["caf"])==Decimal("112709.75")


def test_tva_douze_mois_credits_reports_et_pieces_impayees(data):
    rows=data["tva_mois"]
    assert [r["mois"] for r in rows]==[f"{i:02}" for i in range(1,13)]
    previous=Decimal(0)
    for row in rows:
        assert Decimal(row["credit_ouverture"])==previous
        net=Decimal(row["collectee"])-Decimal(row["recuperable"])-previous
        assert Decimal(row["due"])==max(net,0)
        assert Decimal(row["credit_fin"])==max(-net,0)
        previous=Decimal(row["credit_fin"])
    assert sum(Decimal(r["collectee"]) for r in rows)==33900
    assert sum(Decimal(r["recuperable"]) for r in rows)==11600
    assert sum(Decimal(r["due"]) for r in rows)==22300
    balance=cahier.balances(data["operations"])
    assert Decimal(balance["34552"]["debit"])-Decimal(balance["34552"]["credit"])==80
    assert Decimal(balance["4456"]["credit"])-Decimal(balance["4456"]["debit"])==2400


def test_releve_bancaire_ne_contient_pas_les_transferts_effets(data):
    movements=data["releve_bancaire"]
    credit=sum(Decimal(r["Crédit"]) for r in movements)
    debit=sum(Decimal(r["Débit"]) for r in movements)
    assert credit-debit==Decimal("287730")
    assert all(not r["Libellé"].startswith(("CHQ-01 —","CHQ-01-REM","CHQ-REJET","EFF-C01 —","EFF-C01-REM","EFF-F01 —")) for r in movements)
    assert any("EFF-C01-ENC" in r["Libellé"] and r["Crédit"]=="9990.00" for r in movements)


def test_references_02_et_002_distinctes_meme_tiers_date_montant(data):
    entries={e["reference_recette"]:e for e in data["operations"]}
    first,second=entries["REF-02"],entries["REF-002"]
    assert first["date"]==second["date"]=="2025-12-02"
    assert first["lignes"]==second["lignes"]
    assert first["lignes"][-1]["credit"]=="240.00"
    assert "exactement 02," in first["actions"]
    assert "exactement 002," in second["actions"]


def test_dates_historique_effets_explicites_et_journaux_reels(data):
    entries={e["reference_recette"]:e for e in data["operations"]}
    assert entries["CHQ-01"]["journal"]=="AE"
    assert entries["CHQ-01-REM"]["date"]=="2025-02-01"
    assert "Date réelle de l'opération 01/02/2025" in entries["CHQ-01-REM"]["actions"]
    assert entries["CHQ-REJET-INV"]["journal"]=="OD"
    assert "Date réelle de l'opération 15/12/2025" in entries["CHQ-REJET-INV"]["actions"]
    assert entries["EFF-C01-REM"]["lignes"][0]["compte"]=="51132"
    assert "Date réelle de l'opération 15/05/2025" in entries['EFF-C01-REM']['actions']
    assert not any("simulé" in e.get("actions","") for e in entries.values())


def test_balance_an_et_paiements_n1_restent_equilibres(data):
    before=cahier.balance_rows(data)
    opening=cahier.balance_rows(data,True)
    for rows in (before,opening):
        assert sum(Decimal(r["debit"])-Decimal(r["credit"]) for r in rows)==0
    assert not any(r["compte"].startswith(("6","7")) for r in opening)
    assert next(r for r in opening if r["compte"]=="1191")["credit"]=="106409.75"
    assert Decimal(data["attendus"]["banque"])-2400-Decimal("23220.25")==Decimal("262109.75")
    assert cahier.dec(Decimal("133830")*Decimal("0.20")/4)==Decimal("6691.50")


def test_oracle_compare_aux_moteurs_reels_cpc_bilan_esg_et_09d(data):
    sys.path.insert(0,str(ROOT/"hisabpro-backend"))
    from services.liasse_service import calculer_bilan,calculer_cpc,calculer_esg
    from services.balance_import_service import preparer_balance_liasse
    balances=cahier.balances(data["operations"])
    cpc=calculer_cpc(balances)
    bilan=calculer_bilan(balances,cpc["resultat_net"])
    esg=calculer_esg(balances)
    assert cpc["XI"]==129830
    assert cpc["resultat_net"]==106409.75
    assert bilan["actif"]["total"]["net"]==bilan["passif"]["total"]==337010
    assert bilan["equilibre"]
    assert esg["caf"]==112709.75
    imported=preparer_balance_liasse(cahier.balance_rows(data),None,set(balances))
    assert imported["etats"]["bilan"]["actif"]["total"]["net"]==337010
    assert imported["etats"]["cpc"]["resultat_net"]==106409.75
    assert imported["pret_a_deposer"] is False
    paired=preparer_balance_liasse(cahier.balance_rows(data,True),cahier.balance_rows(data),set(balances)|{'1191'})
    assert paired['etats']['bilan']['actif']['total']['net']==337010
    assert paired['etats']['cpc']['resultat_net'] is None
    assert paired['etats_n1']['cpc']['resultat_net']==106409.75
    assert paired['etats_n1']['esg']['caf']==112709.75


def test_tous_les_cas_ont_champs_obligatoires_sans_reussite_predeclaree(data):
    cases=cahier.build_cases(data)
    assert len(cases)>=190
    assert len({c["id"] for c in cases})==len(cases)
    assert {c["module"] for c in cases}==set(cahier.DOMAINS)
    assert [c["ordre"] for c in cases]==list(range(1,len(cases)+1))
    for c in cases:
        assert set(c)=={key for key,_ in cahier.CASE_COLUMNS}
        assert c["statut"] in {"Non testé","Bloqué"}
        assert not c["resultat_reel"] and not c["anomalies"] and not c["preuve_reelle"]
        assert all(c[k] for k in ("objectif","prerequis","donnees","actions","attendu","ecritures","fiscal","controles","preuve"))
    assert all(c["statut"]=="Bloqué" for c in cases if c["objectif"].startswith(("09B","09C","09E","09F","09G","09H")))


def test_excel_reel_dashboard_statuts_domaines_et_champs(artifacts):
    out,data,cases=artifacts
    wb=load_workbook(out/"CAHIER_RECETTE_HISABPRO.xlsx",data_only=False)
    assert all(domain in wb.sheetnames for domain in cahier.DOMAINS)
    assert "Ordre de passage" in wb.sheetnames
    assert len(wb["Synthèse"]._charts)==1
    count=0
    for domain in cahier.DOMAINS:
        ws=wb[domain]
        assert [c.value for c in ws[1]]==[label for _,label in cahier.CASE_COLUMNS]
        assert ws.freeze_panes=="A2"
        assert ws.data_validations.count==1
        assert all(ws.cell(row,12).value in {"Non testé","Bloqué"} for row in range(2,ws.max_row+1))
        count+=ws.max_row-1
    assert count==len(cases)
    assert all(wb["Synthèse"].cell(row,4).value.startswith("=COUNTIF(") for row in range(6,6+len(cahier.DOMAINS)))
    assert wb["Identité et paramètres"].cell(14,2).value is not None
    expected=wb['Résultats chiffrés']
    assert all(isinstance(expected.cell(row,2).value,(int,float)) for row in range(2,expected.max_row+1))
    assert all(expected.cell(row,4).value==f'=IF(C{row}="","",C{row}-B{row})' for row in range(2,expected.max_row+1))
    assert all(expected.cell(row,3).value is None for row in range(2,expected.max_row+1))


def test_pdf_reel_contient_tous_cas_chiffres_et_sources(artifacts):
    out,data,cases=artifacts
    reader=PdfReader(out/"CAHIER_RECETTE_HISABPRO.pdf")
    assert len(reader.pages)>40
    text=" ".join("\n".join(p.extract_text() or "" for p in reader.pages).split())
    assert "CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE" in text
    assert all(c["id"] in text for c in cases)
    assert "337 010" in text and "106 409,75" in text
    assert "casainvest.ma" in text
    assert "Aucun cas prérempli comme réussi" in text
    assert "Bloqué" in text
    assert "HisabPro" in text
    outlines=reader.outline
    assert sum(len(item) for item in outlines if isinstance(item,list))==len(cases)
    assert len([item for item in outlines if not isinstance(item,list)])==6


def test_fichiers_entree_csv_xlsx_et_json_sont_reellement_ouvrables(artifacts):
    out,data,cases=artifacts
    parsed=json.loads((out/"jeu_donnees_recette.json").read_text(encoding="utf-8"))
    assert parsed["societe"]["ice"]=="009900000000001"
    assert parsed["societe"]["password_test"]=="Recette!Atlas2025"
    assert len(parsed["cas_recette"])==len(cases)
    with (out/"balance_attendue_2025.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f,delimiter=";"))
    assert rows==cahier.balance_rows(data)
    wb=load_workbook(out/"balance_attendue_2025.xlsx")
    assert [c.value for c in wb.active[1]]==["compte","debit","credit"]
    assert all(isinstance(wb.active.cell(row,1).value,str) for row in range(2,wb.active.max_row+1))
    bank=load_workbook(out/"releve_banque_recette_2025.xlsx")
    assert bank.active.max_row==len(data["releve_bancaire"])+1


def test_normalisation_ne_change_pas_donnees_exactes_identite_passwords():
    assert cahier.texte_lisible("HisabPro Recette!Atlas2025 admin@hisabpro-recette.example 02 002") == "HisabPro Recette!Atlas2025 admin@hisabpro-recette.example 02 002"
    assert cahier.texte_lisible("TVA20 %, compte2355, date01/01/2025") == "TVA 20 %, compte 2355, date 01/01/2025"


def test_fae_est_variante_bloquee_et_ne_change_pas_l_oracle_principal(data):
    assert not any(e["reference_recette"].startswith("FAE") for e in data["operations"])
    assert not any(r["compte"]=="3427" for r in cahier.balance_rows(data))
    variant=data["variantes_independantes"][0]
    assert variant["statut"]=="Bloqué" and variant["exclue_du_scenario_principal"]
    entries=[e for e in data["operations"] if e["reference_recette"] not in {"IS-2025","PPRF-IMP"}]
    entries.append(variant["ecriture_conditionnelle"])
    entries.append({"reference_recette":"TVA-FAE-VARIANTE","date":"2025-12-31","journal":"OD","lignes":[cahier.line("4455",1200),cahier.line("4456",credit=1200)]})
    tax=cahier.oracle(entries)["is_theorique"]
    entries.extend([{"reference_recette":"IS-VARIANTE","lignes":[cahier.line("6701",tax),cahier.line("4453",credit=tax)]},{"reference_recette":"PPRF-VARIANTE","lignes":[cahier.line("4453",200),cahier.line("3453",credit=200)]}])
    # Ces deux écritures n'ont aucun compte4455/3455 : elles n'entrent pas dans
    # l'agrégation TVA et n'ont pas besoin d'une date de déclaration.
    oracle=cahier.oracle(entries)
    for key,expected in variant["attendus_conditionnels"].items():
        assert oracle[key]==expected
    assert cahier.build_data()["attendus"]==data["attendus"]


def test_balance_avant_is_distincte_de_la_balance_pre_cloture(data):
    before={r["compte"]:r for r in cahier.balance_avant_is(data)}
    after={r["compte"]:r for r in cahier.balance_rows(data)}
    assert before["3453"]["debit"]=="200.00"
    assert "6701" not in before and "4453" not in before
    assert "3453" not in after
    assert Decimal(after["6701"]["debit"])-Decimal(after["4453"]["credit"])==Decimal("200")


def test_nombre_cas_coherent_readme_pdf_excel_json(artifacts):
    out,data,cases=artifacts
    count=len(cases)
    assert f"suivre les {count} cas" in (out/"README.md").read_text(encoding="utf-8")
    assert len(json.loads((out/"jeu_donnees_recette.json").read_text(encoding="utf-8"))["cas_recette"])==count
    workbook=load_workbook(out/"CAHIER_RECETTE_HISABPRO.xlsx")
    assert workbook["Ordre de passage"].max_row-1==count
    text=" ".join(" ".join(p.extract_text() or "" for p in PdfReader(out/"CAHIER_RECETTE_HISABPRO.pdf").pages).split())
    assert f"{count} cas de test" in text
    assert "+ FAE 6 000 + intérêts" not in text
    assert "Variante de FAE" in text
    assert "TVA_FAIT_GENERATEUR" in text


def test_procedures_powershell_syntaxe_analysee_sans_execution():
    import os
    import subprocess
    if os.name!='nt':
        pytest.skip('Analyseur PowerShell natif Windows indisponible sur cette plateforme.')
    command=r"""
$document = Get-Content -LiteralPath 'docs/EXPLOITATION_HISABPRO.md' -Raw -Encoding UTF8
$blocs = [regex]::Matches($document, '(?s)```powershell\r?\n(.*?)```')
if ($blocs.Count -lt 10) { throw 'Blocs de procédure manquants.' }
foreach ($bloc in $blocs) {
    $tokensRecette = $null
    $erreursRecette = $null
    $null = [System.Management.Automation.Language.Parser]::ParseInput($bloc.Groups[1].Value, [ref]$tokensRecette, [ref]$erreursRecette)
    if ($erreursRecette.Count) { throw ($erreursRecette | Out-String) }
}
Write-Output ('Syntaxe analysée : ' + $blocs.Count + ' blocs ; aucune commande métier exécutée.')
"""
    result=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',command],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    assert result.returncode==0,result.stderr
    assert 'blocs' in result.stdout


def test_procedure_python_restore_compile_sans_connexion():
    import re
    document=(ROOT/'docs'/'EXPLOITATION_HISABPRO.md').read_text(encoding='utf-8')
    embedded=re.findall(r"@'\n(.*?)\n'@",document,re.S)
    assert len(embedded)==1
    compile(embedded[0],'<procedure-restauration-isolee>','exec')
    assert 'with cluster_isole() as cluster:' in embedded[0]
    assert 'verifier_cible_isolee' in embedded[0]
    assert 'restaurer_isole' in embedded[0]
    assert 'hisabpro-backend/uploads/{societe_id}/{doc_type}/{doc_id}/' in document


def test_mot_de_passe_personnel_decrit_ui_disponible_sans_reussite_predeclaree(data):
    cases=cahier.build_cases(data)
    screen=next(c for c in cases if c['objectif']=='Changement de mot de passe dans l’interface' or c['objectif']=="Changement de mot de passe dans l'interface")
    technical=next(c for c in cases if c['objectif']=='Révocation technique après changement de mot de passe')
    assert screen['statut']=='Non testé'
    assert technical['statut']=='Non testé'
    assert 'Mon compte' in screen['actions']
    assert 'Recette!Incorrect2025' in screen['donnees']
    assert 'confirmation différente' in screen['actions']
    assert 'Revenir à la connexion' in screen['actions']
    assert 'rôle lecteur' in screen['actions']
    assert 'POST /api/auth/mot-de-passe' in technical['actions']


def test_recouvrement_decrit_creation_historique_existants_sans_inventer_envoi(data):
    case=next(c for c in cahier.build_cases(data) if c['objectif']=="Recouvrement et relances dans l'interface")
    assert case['id']=='HP-FAC-012'
    assert case['statut']=='Non testé'
    assert 'Situation financière' in case['actions']
    assert 'Relancer' in case['actions'] and "onglet Relances" in case['actions']
    assert '22/12/2025' in case['donnees'] and '31/01/2026' in case['donnees']
    assert 'vider Prochaine relance' in case['actions']
    assert "action effectuée hors application" in case['actions']
    assert "Envoi externe automatique non implémenté" in case['observations']
    assert 'aucune écriture comptable' in case['attendu']
    assert 'Cliquer Modifier' in case['actions']
    assert '15/02/2026' in case['donnees']
    assert 'Annuler la relance' in case['actions']
    assert 'statut Annulée' in case['attendu']


def test_parcours_ne_demande_jamais_imputation_avant_creation_facture(data):
    cases=cahier.build_cases(data)
    order_by_reference={}
    for case in cases:
        match=__import__('re').match(r'Repère ([A-Z0-9-]+) ;',case['donnees'])
        if match:
            order_by_reference[match.group(1)]=case['ordre']
    assert order_by_reference['ACH-01']<order_by_reference['AC-F01-IMP']
    assert order_by_reference['VENTE-SERVICE']<order_by_reference['AC-C01-IMP']
    assert order_by_reference['IMMO-ACQ']<order_by_reference['IMMO-PAY']
    assert order_by_reference['CHQ-01']<order_by_reference['CHQ-01-REM']<order_by_reference['CHQ-01-ENC']


def test_fiches_fictives_pdf_et_manifest_reellement_ouvrables(artifacts):
    import hashlib
    out,data,cases=artifacts
    with (out/'justificatifs'/'manifest.csv').open(encoding='utf-8-sig',newline='') as stream:
        manifest=list(csv.DictReader(stream,delimiter=';'))
    assert len(manifest)==len(data['operations'])==50
    for row in manifest:
        path=out/'justificatifs'/row['fichier']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        text=' '.join(PdfReader(path).pages[0].extract_text().split())
        assert 'FICHE DE RECETTE FICTIVE' in text
        assert row['reference'] in text and row['date_piece_fictive'] in text
        assert 'ni une facture authentique ni une attestation fiscale' in text


def test_fichiers_negatifs_fournis_refuses_par_le_moteur_sans_db(artifacts):
    out,data,cases=artifacts
    sys.path.insert(0,str(ROOT/'hisabpro-backend'))
    from services.balance_import_service import preparer_balance_liasse
    allowed=set(cahier.balances(data['operations']))|{'1191'}
    for filename,(headers,expected) in cahier.negative_inputs().items():
        with (out/'negatifs'/filename).open(encoding='utf-8-sig',newline='') as stream:
            rows=list(csv.DictReader(stream,delimiter=';'))
        assert rows==expected
        if filename.startswith('balance_'):
            with pytest.raises(ValueError):
                preparer_balance_liasse(rows,None,allowed)
