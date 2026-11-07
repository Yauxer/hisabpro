"""Classeur de saisie de la variante953, sans écraser les résultats d'un utilisateur."""
from pathlib import Path
from decimal import Decimal
import argparse
import json
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/recette/DONNEES_ENCAISSEMENTS_953.json'
CIBLE = ROOT / 'docs/recette/JEU_RECETTE_ENCAISSEMENTS_953.xlsx'


def generer(remplacer=False):
    if CIBLE.exists() and not remplacer:
        raise FileExistsError('Classeur existant :conserver les annotations ;--remplacer est explicite.')
    x = json.loads(SOURCE.read_text(encoding='utf8')); w = Workbook(); w.remove(w.active)

    def feuille(nom, titres, lignes):
        s = w.create_sheet(nom); s.append(titres)
        for ligne in lignes: s.append(ligne)
        s.freeze_panes = 'A2'; s.auto_filter.ref = s.dimensions
        for c in s[1]:
            c.fill = PatternFill('solid',fgColor='24589C'); c.font = Font(bold=True,color='FFFFFF')
        for row in s:
            for c in row: c.alignment = Alignment(vertical='top',wrap_text=True)
            s.row_dimensions[row[0].row].height = 38
        for col in s.columns: s.column_dimensions[col[0].column_letter].width = 25
        return s

    feuille('Mode d’emploi',['Point','Instruction'],[
        ['Périmètre','Nouvelle société fictive surbaseisolée,TVAencaissements dèscréation. Aucun statut humain prérempli.'],
        ['Guide','TVA_ENCAISSEMENTS_953.md,complément du cahierprincipal conservé.'],
        ['Installation','Backend/frontend953 et migration126 à valider ensemble surcopie restaurable.'],
        ['Accord de compensation','AV-01→VENTE-02 :3000 MAD,date01/03/2025 ;cocheraccordsigné etréférenceREC-COMP01,justificatif fictif du scénario.'],
        ['Différences TVA','TVA01/02/03 adaptés,TVA05 ajoutée,TVA12 supprimée ;ne pas payer2400 enjanvier2026 au titrede décembre2025.'],
        ['Recouvrement suivant','Afficherfacture2025impayée,payer14400au15/01/2026,référenceREC953-IMPAYEE ;validerécriture dans2026. TVAjanvier2026=2400.'],
        ['Limites','Dateshistoriques inconnues àqualifier,recettehumaine et dépôtDGI nonvalidés.']])
    feuille('Société',['Champ','Valeur exacte'],list(x['societe'].items())+list(x['banque'].items()))
    feuille('Tiers',['Code','Nom','Type','Compte','Auxiliaire'],[[t.get(k,'') for k in ['code','nom','type','compte','auxiliaire']] for t in x['tiers']])
    keys=list(dict.fromkeys(k for a in x['articles'] for k in a))
    feuille('Articles',keys,[[a.get(k,'') for k in keys] for a in x['articles']])
    operations=sorted(x['operations'],key=lambda o:o['date'])
    s=feuille('Opérations 2025',['Ordre','Référence','Date','Journal','Description','Actions exactes','Résultat réel','Anomalie','Preuve'],[
        [i,o['reference_recette'],o['date'],o['journal'],o['description'],o.get('actions','Journal :saisir les lignes de cette référence dans Journal attendu, puis valider.'),'','','']
        for i,o in enumerate(operations,1)])
    s.column_dimensions['F'].width=100
    feuille('Journal attendu',['Référence','Date','Journal','Libellé','Compte','Débit MAD','Crédit MAD','Tiers'],[
        [o['reference_recette'],o['date'],o['journal'],o['description'],l['compte'],float(Decimal(l['debit'])),float(Decimal(l['credit'])),l.get('tiers')]
        for o in operations for l in o['lignes']])
    feuille('TVA 2025',['Mois','Collectée','Récupérable','Crédit ouverture','Crédit fin','Due','Résultat réel','Anomalie','Preuve'],[
        [m['mois']]+[float(Decimal(m[k])) for k in ['collectee','recuperable','credit_ouverture','credit_fin','due']]+['','',''] for m in x['tva_mois']])
    feuille('Contrôles',['Grandeur','Montant attendu','Résultat réel','Anomalie','Preuve'],[[k,v,'','',''] for k,v in x['attendus'].items()])
    clefs=list(dict.fromkeys(k for r in x['releve_bancaire'] for k in r))
    feuille('Relevé fictif',clefs,[[r.get(k,'') for k in clefs] for r in x['releve_bancaire']])
    w.save(CIBLE); w.close()
    controle=load_workbook(CIBLE,read_only=True)
    try:
        assert controle['Opérations 2025'].max_row==51 and controle['Journal attendu'].max_row==119
        assert controle['TVA 2025'].max_row==13
        for nom,colonnes in [('Opérations 2025',[6,7,8]),('TVA 2025',[6,7,8]),('Contrôles',[2,3,4])]:
            for row in list(controle[nom].values)[1:]:assert all(row[i] is None for i in colonnes)
    finally:controle.close()
    return CIBLE


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--remplacer',action='store_true');a=p.parse_args()
    print(generer(a.remplacer))
