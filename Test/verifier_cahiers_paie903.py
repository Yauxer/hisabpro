"""Contrôle documentaire portable, sans base, réseau, .env ou modification Excel.

--vierge vérifie une livraison initiale : tous les cas humains Non testé.
Sans ce drapeau, les résultats saisis par le recettant sont acceptés et conservés.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,re
from urllib.parse import unquote
from openpyxl import load_workbook
from pypdf import PdfReader

R=Path(__file__).resolve().parents[1];D=R/'docs/personnel-paie'
CAHIERS=[
 ('SUIVI_RECETTE_PERSONNEL_887.xlsx','CAHIER_RECETTE_PERSONNEL_HISABPRO_887.pdf',59),
 ('SUIVI_CATALOGUE_PAIE_889.xlsx','RECETTE_CATALOGUE_PAIE_889.pdf',12),
 ('SUIVI_VARIABLES_PAIE_891.xlsx','RECETTE_VARIABLES_PAIE_891.pdf',10),
 ('SUIVI_CAMPAGNES_PAIE_893.xlsx','RECETTE_CAMPAGNES_PAIE_893.pdf',6),
 ('SUIVI_SOCIAL_PAIE_897.xlsx','RECETTE_SOCIAL_PAIE_897.pdf',6),
 ('SUIVI_CALCUL_SOCIAL_PAIE_899.xlsx','RECETTE_CALCUL_SOCIAL_PAIE_899.pdf',6),
 ('SUIVI_IR_ANNUEL_PAIE_901.xlsx','RECETTE_IR_ANNUEL_PAIE_901.pdf',6),
 ('SUIVI_QUALIFICATIONS_IR_PAIE_907.xlsx','RECETTE_QUALIFICATIONS_IR_PAIE_907.pdf',6),
 ('SUIVI_BASES_FISCALES_PAIE_909.xlsx','RECETTE_BASES_FISCALES_PAIE_909.pdf',6),
 ('SUIVI_ARRONDI_ANNUEL_PAIE_911.xlsx','RECETTE_ARRONDI_ANNUEL_PAIE_911.pdf',6),
 ('SUIVI_FRAIS_ANNUELS_PAIE_913.xlsx','RECETTE_FRAIS_ANNUELS_PAIE_913.pdf',6),
 ('SUIVI_IR_SOURCE_PAIE_915.xlsx','RECETTE_IR_SOURCE_PAIE_915.pdf',6),
 ('SUIVI_DOC_IR_PAIE_917.xlsx','RECETTE_DOC_IR_PAIE_917.pdf',6),
 ('SUIVI_RATTACHEMENT_PAIE_919.xlsx','RECETTE_RATTACHEMENT_PAIE_919.pdf',6),
 ('SUIVI_RNI_MENSUEL_PAIE_921.xlsx','RECETTE_RNI_MENSUEL_PAIE_921.pdf',6)]
GUIDES=['MODE_EMPLOI_PERSONNEL_PAIE.md','REFERENTIEL_SOCIAL_897.md','SIMULATIONS_SOCIALES_899.md',
        'CONTROLE_IR_ANNUEL_901.md','SOURCES_IR_ANNUEL_901.md','RESULTATS_PAIE_897.md','RESULTATS_PAIE_899.md','RESULTATS_PAIE_901.md',
        'INSTALLATION_COPIE_PAIE_116_118.md','REPRISE_IR_MENSUEL_3C2_903.md','BILAN_SESSION_PAIE_897_903.md',
        'QUALIFICATIONS_FISCALES_907.md','SOURCES_FISCALES_907.md','BASES_FISCALES_CONNECTEES_909.md',
        'REPRISE_PAIE_APRES_BASES_909.md','BILAN_SESSION_PAIE_907_909.md','RESULTATS_PAIE_909.md',
        'ARRONDI_BASE_ANNUELLE_911.md','CUMULS_FRAIS_ANNUELS_913.md','IR_ANNUEL_SOURCE_915.md','INSTALLATION_COPIE_PAIE_119_122.md','DOCUMENTS_IR_ANNUEL_917.md','REPRISE_PAIE_MENSUELLE_917.md','RATTACHEMENT_REVENUS_919.md','RNI_MENSUEL_PREPARATOIRE_921.md']


def verifier(vierge=False):
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    livres=[];identifiants=set();statuts=Counter();liens=[]
    for x,pdf,attendu in CAHIERS:
        wx=D/x;pp=D/pdf;wb=load_workbook(wx,read_only=True);ids=[];etats=Counter()
        for s in wb.worksheets:
            rows=s.iter_rows(values_only=True);header=list(next(rows,[]))
            if 'ID' not in header:continue
            positions=[i for i,v in enumerate(header) if isinstance(v,str) and v.casefold().startswith('statut')]
            assert len(positions)==1,(x,s.title,'Statut absent ou ambigu')
            assert all(c in header for c in ['Résultat réel','Anomalies']) and any(isinstance(c,str) and 'preuve' in c.casefold() for c in header)
            for row in rows:
                ident=row[header.index('ID')]
                if not ident:continue
                ident=str(ident);etat=row[positions[0]]
                assert etat in ['Non testé','Réussi','Échoué','Bloqué'],(x,ident,etat)
                if vierge:assert etat=='Non testé',(x,ident,'Ne pas effacer un résultat humain ; examiner la différence.')
                assert ident not in identifiants,(x,ident,'Identifiant réutilisé')
                identifiants.add(ident);ids.append(ident);etats[etat]+=1
        wb.close();assert len(ids)==attendu,(x,len(ids),attendu)
        reader=PdfReader(pp);texte='\n'.join(page.extract_text() or '' for page in reader.pages)
        assert all(i in texte for i in ids),(pdf,'Un cas du classeur manque dans le PDF')
        statuts.update(etats);livres.append({'excel':x,'pdf':pdf,'cas':len(ids),'pages':len(reader.pages),'statuts':dict(etats),'excel_sha256':sha(wx),'pdf_sha256':sha(pp)})
    for nom in GUIDES:
        p=D/nom;s=p.read_text(encoding='utf8')
        for cible in re.findall(r'\]\(([^)]+)\)',s):
            cible=cible.strip('<>')
            if cible.startswith(('https://','http://','#')):continue
            q=(p.parent/unquote(cible.split('#')[0])).resolve()
            assert q.is_relative_to(R.resolve()) and q.is_file(),(nom,cible)
            liens.append({'depuis':nom,'cible':q.relative_to(R).as_posix()})
    assert len(identifiants)==sum(c[2] for c in CAHIERS)
    return {'controle':'Documentaire uniquement ; aucune recette humaine ou conformité validée','cas':len(identifiants),'statuts':dict(statuts),'classeur_pdf':livres,'liens_locaux_valides':len(liens),'guides_verifies':GUIDES,'fichiers_excel_modifies':False,'reseau_ou_base_utilises':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--vierge',action='store_true');parser.add_argument('--sortie',type=Path);args=parser.parse_args()
    preuve=verifier(args.vierge)
    if args.sortie:
        p=args.sortie.resolve();assert p.is_relative_to(R.resolve()) and p.suffix=='.json';p.write_text(json.dumps(preuve,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'cas':preuve['cas'],'statuts':preuve['statuts'],'PDF_Excel':len(preuve['classeur_pdf']),'liens_locaux_valides':preuve['liens_locaux_valides'],'excel_modifies':False},ensure_ascii=False))
