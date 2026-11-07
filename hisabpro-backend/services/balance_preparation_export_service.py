"""Exports de la version conservée : agrégats figés et sources normalisées.

Les calculs métier ne sont pas relancés lors de la lecture d'une ancienne
version. Les sous-postes sont pour mémoire, sans ventilation des amortissements.
"""
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from services.bilan_presentation import lignes_bilan_detaille
from services.logo_export_service import ajouter_logo_xlsx


NOTE_DETAIL = ('Sous-postes pour mémoire : ne pas les additionner aux rubriques. '
               'Amortissements/provisions non ventilés sans source certaine ; '
               'Indisponible ne signifie pas zéro.')


def presentation_bilan(dossier):
    contenu = dossier['contenu']
    preparation = contenu['preparation']
    bilan = preparation['etats']['bilan']
    precedent = preparation.get('etats_n1')
    bilan_n1 = precedent['bilan'] if precedent else bilan
    sources = contenu.get('sources', {})
    n, n1 = sources.get('n'), sources.get('n1')

    def soldes(rows):
        return {r['compte']: {'debit': r['debit'], 'credit': r['credit']} for r in rows or []}

    resultat = {}
    for cote in ('actif', 'passif'):
        # Sans source N-1, garder les totaux figés mais ne pas fabriquer de
        # ventilation N-1 depuis des comptes à zéro.
        detail_n1 = precedent is not None and n1 is not None
        lignes = lignes_bilan_detaille(bilan, soldes(n), bilan_n1, soldes(n1), cote, detail_n1)
        parents_n1 = [r for r in lignes_bilan_detaille(
            bilan, {}, bilan_n1, {}, cote, precedent is not None) if r['type'] != 'detail']
        index = 0
        sortie = []
        for ligne in lignes:
            if ligne['type'] == 'detail':
                if n is None:
                    continue
            else:
                if ligne['valeurs']:
                    ligne['valeurs'][-1] = parents_n1[index]['valeurs'][-1]
                index += 1
            sortie.append(ligne)
        resultat[cote] = sortie
    return resultat


def generer_preparation_xlsx(dossier, societe):
    """Aucun accès au plan courant ni aux écritures ; données du snapshot seul."""
    wb = Workbook()
    wb.remove(wb.active)
    contenu = dossier['contenu']
    preparation = contenu['preparation']

    def feuille(nom, entetes, lignes, montants=()):
        ws = wb.create_sheet(nom)
        for i, row in enumerate([entetes, *lignes], 1):
            for j, valeur in enumerate(row, 1):
                cell = ws.cell(i, j)
                if i > 1 and j in montants and valeur is not None:
                    exact = Decimal(str(valeur))
                    if len(exact.normalize().as_tuple().digits) <= 15 and Decimal(str(float(exact))) == exact:
                        cell.value = float(exact)
                        cell.number_format = '#,##0.00'
                        continue
                # Les noms de fichiers / société ne deviennent jamais des formules.
                cell.value = 'Indisponible' if valeur is None else str(valeur)
                cell.data_type = 's'
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        for cell in ws[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='185FA5')
        for row in ws:
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 24
        ws.column_dimensions['A'].width = 42
        return ws

    identite = societe.get('raison_sociale', '') if isinstance(societe, dict) else societe.raison_sociale
    infos = [
        ('Document', 'Préparation indépendante depuis balances — à compléter'),
        ('Société (identité actuelle)', identite),
        ('Exercice', dossier['exercice']), ('Version conservée', dossier['version']),
        ('ID préparation', dossier['id']), ('Conservée le', dossier.get('created_at')),
        ('Période déclarée N', contenu['periode']['debut'] + ' au ' + contenu['periode']['fin']),
        ('Empreinte des données normalisées', dossier['empreinte_sha256']),
        ('Portée de l’empreinte', 'Contenu conservé ; identité/logo actuels hors empreinte.'),
        ('Statut', 'À compléter — aucune écriture ni archive fiscale définitive créée.'),
        ('Lecture du bilan', NOTE_DETAIL),
    ]
    infos += [('Source déclarée ' + k.upper(), v) for k, v in contenu['sources']['noms_fichiers'].items()]
    infos += [('Avertissement', v) for v in preparation['avertissements']]
    infos += [('À compléter', v) for v in preparation['a_completer']]
    if contenu['sources'].get('n') is None:
        infos.append(('Sources détaillées', 'Indisponibles dans cette ancienne version ; agrégats conservés seulement.'))
    ws = feuille('Dossier', ['Information', 'Valeur'], infos)
    ws.column_dimensions['B'].width = 100
    for row in range(2, ws.max_row + 1):
        ws.row_dimensions[row].height = 45

    detail = presentation_bilan(dossier)
    for cote, nom, entetes in [
        ('actif', 'Bilan actif', ['Code', 'Rubrique', 'Brut N MAD', 'Amort. provisions N MAD', 'Net N MAD', 'Net N-1 MAD']),
        ('passif', 'Bilan passif', ['Code', 'Rubrique', 'N MAD', 'N-1 MAD']),
    ]:
        ws = feuille(nom, entetes, [
            [r.get('numero', ''), ('    ' if r['type'] == 'detail' else '') + r['label'], *r['valeurs']]
            for r in detail[cote]], range(3, len(entetes) + 1))
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 65
        for i, r in enumerate(detail[cote], 2):
            if r['type'] in ('titre', 'total', 'rubrique'):
                for cell in ws[i]:
                    cell.font = Font(bold=True)
    for suffixe, etats in [('N', preparation['etats']), ('N-1', preparation.get('etats_n1'))]:
        if etats is None:
            continue
        for code in ('cpc', 'esg'):
            source = etats[code]
            lignes = ([['Indisponible : ' + source['motif'], None]] if source.get('disponible') is False else
                      [[r['libelle'], r['montant']] for r in source['lignes'] if r.get('montant') is not None])
            feuille(code.upper() + ' ' + suffixe, ['Libellé', 'Montant MAD'], lignes, (2,))
    for cle, suffixe in [('n', 'N'), ('n1', 'N-1')]:
        lignes = contenu['sources'].get(cle)
        if lignes is not None:
            feuille('Balance source ' + suffixe, ['Compte', 'Débit MAD', 'Crédit MAD'],
                    [[r['compte'], r['debit'], r['credit']] for r in lignes], (2, 3))
    if contenu.get('echeances_documentaires'):
        from services.balance_echeances_service import presentation, CHAMPS, LIBELLES
        vue = presentation(dossier)
        parent = vue['parent']
        feuille('Origine du complément', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Version source', parent['version']],
            ['Empreinte source', parent['empreinte_sha256']],
            ['Prêt à déposer', 'Non — préparation documentaire seulement']])
        feuille('Échéances documentaires',
            ['Section interne', 'Compte', 'Solde N MAD', *LIBELLES,
             'Ventilé par échéance', 'Reliquat non qualifié', 'Justification / référence'],
            [[r['section'], r['compte'], r['total'], *[r[k] for k in CHAMPS],
              r['qualifie'], r['reliquat'], r['justification']] for r in vue['lignes']],
            range(3, 13))
    if contenu.get('notes_etic_documentaires'):
        from services.balance_etic_notes_service import presentation, STATUTS
        vue = presentation(dossier)
        feuille('Origine notes ETIC', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Version source', vue['parent']['version']],
            ['Empreinte source', vue['parent']['empreinte_sha256']],
            ['Auteur', vue['auteur']['nom']], ['Conservé le UTC', vue['conserve_le_utc']],
            ['Prêt à déposer', 'Non']])
        ws = feuille('Notes ETIC documentaires', ['Code', 'Rubrique', 'État de la note', 'Texte', 'Référence / justification'],
            [[r['code'], r['titre'], STATUTS[r['statut']], r['texte'], r['justification']] for r in vue['lignes']])
        for col in ('B', 'D', 'E'):
            ws.column_dimensions[col].width = 65
    if contenu.get('tables_etic_documentaires'):
        from services.balance_etic_tables_service import presentation, STATUTS
        vue = presentation(dossier)
        feuille('Origine tableaux ETIC', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Version source', vue['parent']['version']],
            ['Empreinte source', vue['parent']['empreinte_sha256']], ['Auteur', vue['auteur']['nom']],
            ['Conservé le UTC', vue['conserve_le_utc']], ['Prêt à déposer', 'Non'],
            *[['Alerte', a] for a in vue['alertes']],
            *[[r['code'] + ' · ' + r['titre'], STATUTS[r['statut']] + ' · ' + r['justification']] for r in vue['tables']]])
        for r in vue['tables']:
            colonnes = r['colonnes_saisie']
            ws = feuille('ETIC documentaire ' + r['code'],
                [c['label'] + (' MAD' if c['type'] == 'number' else '') for c in colonnes] + ['Référence de source'],
                [[*[ligne[c['cle']] for c in colonnes], ligne['reference_source']] for ligne in r['lignes']],
                [i for i, c in enumerate(colonnes, 1) if c['type'] == 'number'])
            for row in range(2, ws.max_row + 1):
                ws.row_dimensions[row].height = 60
    if contenu.get('annexes_etic_documentaires'):
        from services.balance_etic_annexes_service import presentation, STATUTS
        vue = presentation(dossier)
        feuille('Origine annexes ETIC', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Version source', vue['parent']['version']],
            ['Empreinte source', vue['parent']['empreinte_sha256']], ['Auteur', vue['auteur']['nom']],
            ['Conservé le UTC', vue['conserve_le_utc']], ['Prêt à déposer', 'Non'],
            *[['Alerte', a] for a in vue['alertes']],
            *[[r['code'] + ' · ' + r['titre'], STATUTS[r['statut']] + ' · ' + r['justification']] for r in vue['tables']]])
        for r in vue['tables']:
            colonnes = r['colonnes_saisie']
            ws = feuille('ETIC documentaire ' + r['code'],
                [c['label'] + (' ' + c.get('unite', 'MAD') if c['type'] == 'number' else '') for c in colonnes] + ['Référence de source'],
                [[*[ligne[c['cle']] for c in colonnes], ligne['reference_source']] for ligne in r['lignes']],
                [i for i, c in enumerate(colonnes, 1) if c['type'] == 'number' and c.get('unite', 'MAD') == 'MAD'])
            for row in range(2, ws.max_row + 1):
                ws.row_dimensions[row].height = 60
    if contenu.get('annexes_etic_documentaires', {}).get('controle_capital'):
        from services.balance_capital_controle_service import lignes_export
        controle = contenu['annexes_etic_documentaires']['controle_capital']
        ws = feuille('Contrôles capital', ['Contrôle', 'Valeur conservée exacte', 'Unité'], lignes_export(controle))
        ws.column_dimensions['A'].width = 70
        ws.column_dimensions['B'].width = 85
        ws.column_dimensions['C'].width = 15
    if contenu.get('detail_cpc_documentaire'):
        bloc = contenu['detail_cpc_documentaire']; vue = bloc['vue']
        feuille('Origine détail CPC', ['Information', 'Valeur'], [
            ['Titre conservé', vue['code'] + ' · ' + vue['titre']], ['Portée', vue['note']],
            ['Méthode', vue['methode']], ['Auteur', bloc['auteur']['nom']],
            ['Conservé le UTC', bloc['conserve_le_utc']], ['Version source', bloc['parent']['version']],
            ['Empreinte source', bloc['parent']['empreinte_sha256']]])
        for periode, libelle in [('n', 'N'), ('n1', 'N-1')]:
            detail = vue['periodes'][periode]
            feuille('Détail CPC ' + libelle, ['Compte', 'Libellé', 'Nature', 'Solde signé MAD'],
                [[r['compte'], 'Libellé non conservé', r['nature'], r['montant']] for r in detail['lignes']]
                if detail['disponible'] else [['Indisponible', detail['motif'], '', None]], (4,))
            feuille('Rapprochement CPC ' + libelle, ['Indicateur', 'Détail MAD', 'CPC figé MAD', 'Écart détail moins CPC MAD'],
                [[k.capitalize(), detail[k], detail['cpc_' + k], detail['ecart_' + k]] for k in ('charges','produits','resultat')], (2,3,4))
    if contenu.get('non_valeurs_documentaires'):
        bloc = contenu['non_valeurs_documentaires']; vue = bloc['vue']
        feuille('Origine non-valeurs', ['Information', 'Valeur'], [
            ['Titre conservé', vue['code'] + ' · ' + vue['titre']], ['Portée', vue['note']],
            ['Méthode', vue['methode']], ['Auteur', bloc['auteur']['nom']],
            ['Conservé le UTC', bloc['conserve_le_utc']], ['Version source', bloc['parent']['version']],
            ['Empreinte source', bloc['parent']['empreinte_sha256']]])
        for periode, libelle in [('n', 'N'), ('n1', 'N-1')]:
            detail = vue['periodes'][periode]
            feuille('Non-valeurs ' + libelle, ['Compte', 'Libellé', 'Nature', 'Solde signé MAD'],
                [[r['compte'], 'Libellé non conservé', r['nature'], r['montant']] for r in detail['lignes']]
                if detail['disponible'] else [['Indisponible', detail['motif'], '', None]], (4,))
            feuille('Contrôle non-valeurs ' + libelle, ['Indicateur', 'Détail MAD', 'Bilan figé MAD', 'Écart détail moins bilan MAD'],
                [[k.capitalize(), detail[k], detail['bilan_' + k], detail['ecart_' + k]] for k in ('brut','amortissements','net')], (2,3,4))
    if contenu.get('extra_c3_documentaire'):
        from services.balance_c3_extra_service import presentation,CHAMPS
        vue=presentation(dossier)
        feuille('Origine déclarations C3',['Information','Valeur'],[['Portée',vue['note']],['Auteur',vue['auteur']['nom']],
            ['Conservé le UTC',vue['conserve_le_utc']],['Version parent',vue['parent']['version']],
            ['Empreinte parent',vue['parent']['empreinte_sha256']]])
        for t in vue['tables']:
            nom={'C3-N':'N','C3-N1':'N-1','C3-N2':'N-2'}[t['code']];cols=t['colonnes_saisie']
            feuille('Déclarations C3 '+nom,['État','Justification',*[c['label']+(' ('+c['unite']+')' if c.get('unite') else '') for c in cols],'Référence de source'],
                [[t['statut'],t['justification'],*[r[c['cle']] for c in cols],r['reference_source']] for r in t['lignes']]
                or [[t['statut'],t['justification'],*[None for c in cols],'']],(4,5,6,7))
    if contenu.get('comparatif_n2_documentaire'):
        bloc=contenu['comparatif_n2_documentaire'];source=bloc['source_preparation'];totaux=bloc['totaux_exacts']
        feuille('Origine N-2',['Information','Valeur'],[['Portée',bloc['note']],['Référence de source',bloc['reference_source']],
            ['Exercice source',source['exercice']],['Préparation source',source['id']],['Version source',source['version']],
            ['Empreinte source',source['empreinte_sha256']],['Fichier source',bloc['nom_fichier_source']],
            ['Auteur du rattachement',bloc['auteur']['nom']],['Conservé le UTC',bloc['conserve_le_utc']],
            ['Version parent',bloc['parent']['version']],['Empreinte parent',bloc['parent']['empreinte_sha256']],
            ['Comptes',totaux['comptes']],['Débit exact MAD',totaux['debit']],['Crédit exact MAD',totaux['credit']]])
        feuille('Balance N-2 rattachée',['Compte','Débit MAD','Crédit MAD'],
            [[r['compte'],r['debit'],r['credit']] for r in bloc['sources_n2']],(2,3))
    if contenu.get('indicateurs_comptables_documentaires'):
        from services.balance_indicateurs_service import CHAMPS
        bloc=contenu['indicateurs_comptables_documentaires'];vue=bloc['vue']
        feuille('Origine C3',['Information','Valeur'],[['Portée',vue['note']],['Méthode',vue['methode']],
            ['Auteur',bloc['auteur']['nom']],['Conservé le UTC',bloc['conserve_le_utc']],
            ['Version source',bloc['parent']['version']],['Empreinte source',bloc['parent']['empreinte_sha256']],
            ['À documenter',' ; '.join(vue['informations_a_completer'])]])
        for p,libelle in [('n','N'),('n1','N-1'),('n2','N-2')]:
            d=vue['periodes'][p]
            feuille('Indicateurs C3 '+libelle,['Indicateur','Détail MAD','États figés MAD','Écart détail moins référence MAD'],
                [[k,d[k],d['reference_'+k],d['ecart_'+k]] for k in CHAMPS],(2,3,4))
            feuille('Sources C3 '+libelle,['Compte','Libellé','Nature','Solde signé MAD'],
                [[row['compte'],'Libellé non conservé',row['nature'],row['montant']] for row in d['lignes']],(4,))
            feuille('Diagnostic C3 '+libelle,['Information','Valeur'],[['Disponible','Oui' if d['disponible'] else 'Non'],
                ['Motif',d['motif']]]+[['Avertissement',a] for a in d['avertissements']]+
                [[label,d.get(k)] for k,label in [('effectif_moyen','Effectif moyen déclaré (personnes)'),('benefices_distribues','Bénéfices distribués déclarés (MAD)'),('resultat_par_titre','Résultat par titre déclaré (MAD/titre)'),('distribution_par_titre','Distribution par titre déclarée (MAD/titre)'),('reference_extra_c3','Référence extra-comptable'),('affectations_justifiees','Décisions et affectations')]])
    if contenu.get('tva_documentaire'):
        from services.balance_tva_documentaire_service import presentation,CHAMPS
        vue=presentation(dossier);ctrl=vue['controle_tva'];table=vue['tables'][0];cols=table['colonnes_saisie']
        feuille('Origine B14',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],
            ['Version source',vue['parent']['version']],['Empreinte source',vue['parent']['empreinte_sha256']],
            ['Dépôt confirmé','Non'],['Liquidation calculée','Non']])
        feuille('Déclaration B14 N',['État','Justification',*[c['label'] for c in cols],'Référence de source'],
            [[table['statut'],table['justification'],*[row[c['cle']] for c in cols],row['reference_source']] for row in table['lignes']]
            or [[table['statut'],table['justification'],*[None for c in cols],'']],(4,5,6))
        feuille('Contrôle B14 N',['Famille TVA',*CHAMPS.values(),'Références des déclarations','Référence de source'],
            [[r['titre'],*[r['montants'][k] for k in CHAMPS],r['references_declarations'],r['reference_source']] for r in ctrl['lignes']],tuple(range(2,9)))
        feuille('Diagnostic B14',['Information','Valeur'],[['Alerte',a] for a in ctrl['alertes']]+
            [[p+' source disponible','Oui' if d['disponible'] else 'Non'] for p,d in ctrl['sources'].items()]+
            [[p+' motif',d['motif']] for p,d in ctrl['sources'].items()])
        for p,nom in [('n','N'),('n1','N-1')]:
            feuille('Sources B14 '+nom,['Compte','Libellé','Famille TVA','Solde signé MAD'],
                [[r['compte'],'Libellé non conservé',r['famille'],r['montant']] for r in ctrl['sources'][p]['lignes']],(4,))
    if contenu.get('passage_fiscal_documentaire'):
        from services.balance_passage_fiscal_service import presentation,LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_passage_fiscal'];table=vue['tables'][0];cols=table['colonnes_saisie']
        feuille('Origine B12',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],
            ['Version source',vue['parent']['version']],['Empreinte source',vue['parent']['empreinte_sha256']]])
        feuille('Déclaration B12 N',['État','Justification',*[c['label'] for c in cols],'Référence de source'],
            [[table['statut'],table['justification'],*[row[c['cle']] for c in cols],row['reference_source']] for row in table['lignes']]
            or [[table['statut'],table['justification'],*[None for c in cols],'']],(4,5,6,7))
        feuille('Contrôle B12 N',['Information','Valeur MAD ou diagnostic'],
            [['Source disponible','Oui' if ctrl['disponible'] else 'Non'],['Motif',ctrl['motif']]]+
            [[LIBELLES[k],v] for k,v in ctrl['montants'].items()]+[[{'cm':'Cotisation minimale','css':'CSS','credits':'Crédits','acomptes':'Acomptes','solde_final':'Solde final'}[k],v] for k,v in ctrl['liquidation'].items()]+
            [['Alerte',a] for a in ctrl['alertes']]+[['À compléter',a] for a in ctrl['a_completer']])
        feuille('Sources B12 N',['Compte','Libellé','Nature','Solde signé MAD'],
            [[r['compte'],'Libellé non conservé',r['nature'],r['montant']] for r in ctrl['lignes']],(4,))
    if contenu.get('liquidation_is_documentaire'):
        from services.balance_liquidation_is_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_liquidation'];table=vue['tables'][0];cols=table['colonnes_saisie']
        feuille('Origine proposition IS',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],['Empreinte parent',vue['parent']['empreinte_sha256']],
            ['Sources IS modifiées','Oui' if vue['sources_is_modifiees'] else 'Non'],['Source CSS modifiée','Oui' if vue['source_css_modifiee'] else 'Non'],
            ['Proposition conditionnelle disponible','Oui' if ctrl['proposition_disponible'] else 'Non'],
            *[[k,v] for k,v in ctrl['reference_juridique'].items()],['Liquidation confirmée','Non'],['Paiement confirmé','Non']])
        feuille('Proposition IS CM',['Information','Valeur MAD'],[[LIBELLES[k],v] for k,v in ctrl['montants'].items()],(2,))
        feuille('Revue proposition IS',['État','Justification',*[c['label'] for c in cols],'Référence de source'],
            [[table['statut'],table['justification'],*[r[c['cle']] for c in cols],r['reference_source']] for r in table['lignes']]
            or [[table['statut'],table['justification'],*[None for c in cols],'']],tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Sources proposition IS',['Contrôle source','Clé conservée'],[[k,(v or {}).get('cle')] for k,v in ctrl['sources_conservees'].items()])
        if ctrl['detail_simulation']:
            d=ctrl['detail_simulation']
            feuille('Répartition simulation IS',['Crédit regroupé dans le calcul','Appliqué MAD'],list(d['credits_is_appliques_detail'].items()),(2,))
        feuille('Alertes proposition IS',['Information','Valeur'],[['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('acomptes_is_documentaires'):
        from services.balance_acomptes_is_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_acomptes']
        feuille('Origine acomptes IS',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],['Date de contrôle',ctrl['date_controle']],
            ['Empreinte parent',vue['parent']['empreinte_sha256']],*[[k,v] for k,v in ctrl['reference_juridique'].items()],
            ['Crédits modifiés','Oui' if vue['source_credits_modifiee'] else 'Non'],['Paiement confirmé','Non']])
        feuille('Contrôle acomptes IS',['Information','Valeur MAD'],[[LIBELLES[k],v] for k,v in ctrl['montants'].items()],(2,))
        for table in vue['tables']:
            cols=table['colonnes_saisie']
            feuille(table['code'],['État','Justification',*[c['label'] for c in cols],'Référence de source'],
                [[table['statut'],table['justification'],*[r[c['cle']] for c in cols],r['reference_source']] for r in table['lignes']]
                or [[table['statut'],table['justification'],*[None for c in cols],'']],tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Rapprochement retenues IS',['Justificatif crédit','Déjà utilisé côté crédits MAD','Affecté aux acomptes MAD','Cohérent'],
            [[r['reference'],r['attendu'],r['affecte'],'Oui' if r['coherent'] else 'Non'] for r in ctrl['rapprochement_retenues']],(2,3))
        feuille('Échéancier acomptes IS',['Numéro','Échéance','Montant dû MAD','Couverture déclarée MAD','Reste MAD','État déclaré'],
            [[r[k] for k in ('numero','date_echeance','du','couverture_declaree','reste','statut')] for r in ctrl['echeancier']],(3,4,5))
        feuille('Alertes acomptes IS',['Information','Valeur'],[['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('taxe_professionnelle_documentaire'):
        from services.balance_taxe_professionnelle_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_tp']
        feuille('Origine TP',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],['Empreinte parent',vue['parent']['empreinte_sha256']],['Imposition confirmée','Non'],*[[k,v] for k,v in ctrl['reference_juridique'].items()]])
        feuille('Simulation brute TP',['Information','Valeur MAD'],[[LIBELLES[k],v] for k,v in ctrl['montants'].items()],(2,))
        for table in vue['tables']:
            cols=table['colonnes_saisie']
            feuille(table['code'],['État','Justification',*[c['label'] for c in cols],'Référence source'],[[table['statut'],table['justification'],*[a[c['cle']] for c in cols],a['reference_source']] for a in table['lignes']] or [[table['statut'],table['justification'],*[None for c in cols],'']],tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Revue établissements TP',['Établissement','Classe','Taux normal lu %','Brut exact MAD','Brut centime MAD','Écart avis MAD','Points à revoir'],[[a['etablissement_ref'],a['classe'],a['taux_normal'],a['brut_exact'],a['brut_arithmetique'],a['ecart_avis'],', '.join(a['points_a_revoir'])] for a in ctrl['etablissements']],(5,6))
        feuille('Alertes TP',['Information','Valeur'],[['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('remunerations_tiers_documentaires'):
        from services.balance_remunerations_tiers_service import presentation, MONTANTS
        vue=presentation(dossier);ctrl=vue['controle_tiers']
        feuille('Origine rémunérations tiers',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],['Empreinte parent',vue['parent']['empreinte_sha256']],['Déclaration officielle','Non'],*[[k,v] for k,v in ctrl['reference_juridique'].items()]])
        feuille('Contrôle rémunérations tiers',['Information','Valeur MAD'],[[label,ctrl['montants'][k]] for k,label in MONTANTS.items()],(2,))
        for table in vue['tables']:
            cols=table['colonnes_saisie']
            feuille(table['code'],['État','Justification',*[c['label'] for c in cols],'Référence de source'],[[table['statut'],table['justification'],*[a[c['cle']] for c in cols],a['reference_source']] for a in table['lignes']] or [[table['statut'],table['justification'],*[None for c in cols],'']],tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Regroupements tiers',['Bénéficiaire','Catégorie',*MONTANTS.values()],[[g['beneficiaire_ref'],g['categorie'],*[g['montants'][k] for k in MONTANTS]] for g in ctrl['regroupements']],(3,4,5))
        feuille('Revue identités tiers',['Bénéficiaire','Nom conservé','Champs à compléter'],[[b['reference'],b['nom'],', '.join(b['points_a_revoir'])] for b in ctrl['beneficiaires']])
        feuille('Revue mouvements tiers',['Référence source','Bénéficiaire','Points à revoir'],[[l['reference_source'],l['beneficiaire_ref'],', '.join(l['points_a_revoir'])] for l in ctrl['lignes']])
        feuille('Alertes rémunérations tiers',['Information','Valeur'],[['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('credits_is_documentaires'):
        from services.balance_credits_is_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_credits']
        feuille('Origine crédits IS',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],
            ['Empreinte parent',vue['parent']['empreinte_sha256']],*[[k,v] for k,v in ctrl['reference_juridique'].items()],
            ['Contexte modifié','Oui' if vue['source_contexte_modifiee'] else 'Non'],['Liquidation confirmée','Non']])
        feuille('Contrôle crédits IS',['Information','Valeur MAD'],[[LIBELLES[k],v] for k,v in ctrl['montants'].items()],(2,))
        for table in vue['tables']:
            cols=table['colonnes_saisie']
            feuille(table['code'],['État','Justification',*[c['label'] for c in cols],'Référence de source'],
                [[table['statut'],table['justification'],*[r[c['cle']] for c in cols],r['reference_source']] for r in table['lignes']]
                or [[table['statut'],table['justification'],*[None for c in cols],'']],tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Qualification crédits IS',['Ligne','Type juridique','Référence','Qualification','Reliquat arithmétique MAD'],
            [[r['ligne'],r['type_credit'],r['reference_source'],r['statut'],r['disponible_arithmetique']] for r in ctrl['lignes']],(5,))
        feuille('Alertes crédits IS',['Information','Valeur'],[['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('css_documentaire'):
        from services.balance_css_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_css'];t=vue['tables'][0];cols=t['colonnes_saisie']
        feuille('Origine CSS',['Information','Valeur'],[['Portée',vue['note']],['Méthode',ctrl['methode']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],
            ['Empreinte parent',vue['parent']['empreinte_sha256']],*[[k,v] for k,v in ctrl['reference_juridique'].items()],
            ['Exercice de référence déclaré',ctrl['exercice_reference_declare']],
            ['Référence contexte conservée',(ctrl['source_contexte_fiscal'] or {}).get('cle')],
            ['Contexte modifié','Oui' if vue['source_contexte_modifiee'] else 'Non'],['Liquidation confirmée','Non']])
        feuille('Calcul CSS',['Information','Valeur','Unité'],[[LIBELLES[k],v,'MAD'] for k,v in ctrl['montants'].items()]
            +[['Taux proportionnel',ctrl['taux_proportionnel'],'%']],(2,))
        feuille('Qualification CSS',['État','Justification',*[c['label'] for c in cols],'Référence de source'],
            [[t['statut'],t['justification'],*[r[c['cle']] for c in cols],r['reference_source']] for r in t['lignes']]
            or [[t['statut'],t['justification'],*[None for c in cols],'']],tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Alertes CSS',['Information','Valeur'],[['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('cotisation_minimale_documentaire'):
        from services.balance_cotisation_minimale_service import presentation, LIBELLES
        vue = presentation(dossier); ctrl = vue['controle_cm']; table = vue['tables'][0]; cols = table['colonnes_saisie']
        feuille('Origine CM', ['Information', 'Valeur'], [['Portée', vue['note']], ['Méthode', ctrl['methode']],
            ['Auteur', vue['auteur']['nom']], ['Conservé le UTC', vue['conserve_le_utc']],
            ['Empreinte parent', vue['parent']['empreinte_sha256']],
            *[[k,v] for k,v in ctrl['reference_juridique'].items()],
            ['Référence B12 conservée', (ctrl['source_b12'] or {}).get('cle')],
            ['Référence B12 modifiée', 'Oui' if vue['source_b12_modifiee'] else 'Non'], ['Liquidation confirmée', 'Non']])
        feuille('Calcul CM', ['Information', 'Valeur MAD'], [[LIBELLES[k],v] for k,v in ctrl['montants'].items()], (2,))
        feuille('Sources CM', ['Compte','Solde créditeur net MAD','Dans la base comptable','Famille'],
            [[r['compte'],r['montant'],'Oui' if r['retenu_base'] else 'Non',r['famille']] for r in ctrl['lignes_sources']], (2,))
        feuille('Qualification CM', ['État','Justification',*[c['label'] for c in cols],'Référence de source'],
            [[table['statut'],table['justification'],*[r[c['cle']] for c in cols],r['reference_source']] for r in table['lignes']]
            or [[table['statut'],table['justification'],*[None for c in cols],'']],
            tuple(i+3 for i,c in enumerate(cols) if c['type']=='number'))
        feuille('Alertes CM', ['Information','Valeur'], [['Alerte',a] for a in vue['alertes']+ctrl['alertes']])
    if contenu.get('contexte_fiscal_documentaire'):
        from services.balance_contexte_fiscal_service import presentation, LIBELLES
        vue = presentation(dossier); ctrl = vue['controle_contexte_fiscal']
        feuille('Origine contexte fiscal', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Méthode', ctrl['methode']], ['Auteur', vue['auteur']['nom']],
            ['Conservé le UTC', vue['conserve_le_utc']], ['Empreinte parent', vue['parent']['empreinte_sha256']],
            ['Référence B12 conservée', (ctrl['source_b12'] or {}).get('cle')],
            ['IS théorique B12 pour mémoire', (ctrl['source_b12'] or {}).get('is_theorique_taux_declare')],
            ['Référence B12 modifiée', 'Oui' if vue['source_b12_modifiee'] else 'Non'],
            ['Solde final', ctrl['solde_final']], ['Liquidation confirmée', 'Non']])
        feuille('Totaux contexte fiscal', ['Information', 'Valeur MAD'],
            [[LIBELLES[k], v] for k, v in ctrl['montants'].items()], (2,))
        feuille('Alertes contexte fiscal', ['Information', 'Valeur'],
            [['Alerte', a] for a in vue['alertes'] + ctrl['alertes']])
        for t in vue['tables']:
            cols = t['colonnes_saisie']
            feuille(t['code'], ['État', 'Justification', *[c['label'] for c in cols], 'Référence de source'],
                [[t['statut'], t['justification'], *[r[c['cle']] for c in cols], r['reference_source']] for r in t['lignes']]
                or [[t['statut'], t['justification'], *[None for c in cols], '']],
                tuple(i + 3 for i, c in enumerate(cols) if c['type'] == 'number'))
    if contenu.get('resultat_courant_documentaire'):
        from services.balance_resultat_courant_service import presentation
        vue = presentation(dossier); ctrl = vue['controle_resultat_courant']
        feuille('Origine courant', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Méthode', ctrl['methode']], ['Auteur', vue['auteur']['nom']],
            ['Conservé le UTC', vue['conserve_le_utc']], ['Version source', vue['parent']['version']],
            ['Empreinte source', vue['parent']['empreinte_sha256']]])
        for table in vue['tables']:
            libelle = 'N' if table['code'] == 'B13-N' else 'N-1'
            d = ctrl['periodes']['n' if libelle == 'N' else 'n1']; cols = table['colonnes_saisie']
            feuille('Déclaration B13 ' + libelle, ['État', 'Justification', *[c['label'] for c in cols], 'Référence de source'],
                [[table['statut'], table['justification'], *[row[c['cle']] for c in cols], row['reference_source']] for row in table['lignes']]
                or [[table['statut'], table['justification'], *[None for c in cols], '']], (4,5,6))
            feuille('Contrôle B13 ' + libelle, ['Information', 'Valeur MAD ou diagnostic'],
                [['Source disponible', 'Oui' if d['disponible'] else 'Non'], ['Motif', d['motif']]] +
                [[k, d[k]] for k in ('resultat_courant','cpc_resultat_courant','ecart_courant','impots_comptabilises_67',
                 'reintegrations','deductions','impot_theorique_declare','base_courante_documentaire','courant_apres_impot_declare')]
                + [['Alerte', a] for a in d['alertes']])
            feuille('Sources B13 ' + libelle, ['Compte', 'Libellé', 'Nature', 'Solde signé MAD'],
                [[row['compte'], 'Libellé non conservé', row['nature'], row['montant']] for row in d['lignes']], (4,))
    if contenu.get('participations_documentaires'):
        bloc = contenu['participations_documentaires']; vue = bloc['vue']
        feuille('Origine participations', ['Information', 'Valeur'], [
            ['Titre conservé', vue['code'] + ' · ' + vue['titre']], ['Portée', vue['note']],
            ['Méthode', vue['methode']], ['Auteur', bloc['auteur']['nom']],
            ['Conservé le UTC', bloc['conserve_le_utc']], ['Version source', bloc['parent']['version']],
            ['Empreinte source', bloc['parent']['empreinte_sha256']],
            ['Informations à documenter', ' ; '.join(vue['informations_a_completer'])]])
        for periode, libelle in [('n', 'N'), ('n1', 'N-1')]:
            detail = vue['periodes'][periode]
            feuille('Participations ' + libelle,
                ['Compte', 'Libellé', 'Solde signé MAD', 'Émetteur', 'Capital émetteur MAD', 'Quote-part %', 'Produits reçus MAD'],
                [[r['compte'], 'Libellé non conservé', r['montant'], r['emetteur'], r['capital_emetteur'], r['quote_part'], r['produits_recus']] for r in detail['lignes']]
                if detail['disponible'] else [['Indisponible', detail['motif'], None, None, None, None, None]], (3,5,7))
            feuille('Contrôle financier ' + libelle, ['Indicateur', 'Détail MAD', 'Bilan figé MAD', 'Écart détail moins bilan MAD'], [
                ['Titres251 uniquement', detail['participations'], 'Sans rubrique isolée au bilan', 'Non comparable au24/25'],
                ['Autres24/25', detail['autres_financieres'], 'Sans rubrique isolée au bilan', 'Non comparable au24/25'],
                ['Brut entier24/25', detail['financieres_brut'], detail['bilan_financieres_brut'], detail['ecart_financieres_brut']]], (2,))
    if contenu.get('raccords_mouvements_documentaires'):
        from services.balance_raccords_mouvements_service import presentation
        vue=presentation(dossier);snap=vue['snapshot'];ctrl=snap['controle_raccords']
        feuille('Origine raccords',['Information','Valeur'],[['Portée',vue['note']],['Raccord actuel','Oui' if vue['actuel'] else 'À refaire après changement de mouvements ou sources'],
            ['Version source',snap['parent']['version']],['Empreinte source',snap['parent']['empreinte_sha256']],
            ['Empreinte mouvements contrôlés',snap['empreinte_mouvements']],['Empreinte balance N contrôlée',snap['empreinte_source_n']],
            ['Auteur',snap['auteur']['nom']],['Conservé le UTC',snap['conserve_le_utc']],['Source détaillée disponible',str(ctrl['source_disponible'])]])
        diagnostic=[]
        for table in snap['catalogue']:
            code=table['code'];liens={r['ligne']:r['compte'] for t in snap['tables'] if t['code']==code for r in t['lignes']};controle=ctrl['tableaux'][code]
            feuille('Raccord '+code,['Ligne','Nature déclarée conservée','Clôture déclarée conservée MAD','Compte rattaché','Référence de source conservée'],
                [[r['ligne'],r['nature'],r['fin'],liens[r['ligne']] or 'Non rattachée',r['reference_source']] for r in table['lignes']],(3,))
            feuille('Contrôle raccord '+code,['Compte','Solde source MAD','Somme clôtures déclarées MAD','Écart déclaré moins source MAD','Lignes'],
                [[r['compte'],r['solde_source'],r['somme_clotures_declarees'],r['ecart'],r['lignes']] for r in controle['comptes']],(2,3,4))
            diagnostic.append([code,', '.join(str(i) for i in controle['non_rattachees']) or 'Aucune'])
        feuille('Diagnostic raccords',['Tableau conservé','Lignes non rattachées du contrôle conservé'],diagnostic)
    if contenu.get('mouvements_documentaires'):
        from services.balance_mouvements_service import presentation
        from services.balance_etic_tables_service import STATUTS
        vue=presentation(dossier)
        feuille('Origine mouvements',['Information','Valeur'],[['Portée',vue['note']],['Version source',vue['parent']['version']],
            ['Empreinte source',vue['parent']['empreinte_sha256']],['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],
            *[['Alerte',a] for a in vue['alertes']]])
        feuille('Déclaration mouvements',['Tableau','État','Justification'],[[t['code'],STATUTS[t['statut']],t['justification']] for t in vue['tables']])
        for table in vue['tables']:
            cols=table['colonnes_saisie'];c=vue['controle_mouvements']['tableaux'][table['code']]
            feuille('Mouvements '+table['code'],[col['label']+(' MAD' if col['type']=='number' else '') for col in cols]+['Référence de source'],
                [[*[r[col['cle']] for col in cols],r['reference_source']] for r in table['lignes']],(2,3,4,5))
            feuille('Contrôle MV '+table['code'],['Ligne','Clôture reconstituée MAD','Clôture déclarée MAD','Écart déclaré moins reconstitué MAD'],
                [[r['ligne'],r['fin_reconstituee'],r['fin_declaree'],r['ecart_fin']] for r in c['lignes']]+
                [['Total',c['totaux']['fin_reconstituee'],c['totaux']['fin_declaree'],c['totaux']['ecart_fin']]],(2,3,4))
    if contenu.get('cessions_documentaires'):
        from services.balance_cessions_service import presentation
        from services.balance_etic_tables_service import STATUTS
        vue=presentation(dossier);table=vue['tables'][0];cols=table['colonnes_saisie'];controle=vue['controle_cessions']
        feuille('Origine cessions',['Information','Valeur'],[
            ['Portée',vue['note']],['Version source',vue['parent']['version']],['Empreinte source',vue['parent']['empreinte_sha256']],
            ['Auteur',vue['auteur']['nom']],['Conservé le UTC',vue['conserve_le_utc']],
            *[['Alerte',a] for a in vue['alertes']+controle['alertes']]])
        feuille('Cessions déclarées N',[c['label']+(' MAD' if c['type']=='number' else '') for c in cols]+['Référence de source'],
            [[*[r[c['cle']] for c in cols],r['reference_source']] for r in table['lignes']],(4,5,6))
        feuille('Déclaration cessions',['État','Justification'],[[STATUTS[table['statut']],table['justification']]])
        feuille('Contrôle cessions',['Ligne','Différence prix moins VNA MAD'],
            [[r['ligne'],r['difference_prix_vna']] for r in controle['lignes']]+[['Total',controle['total_difference_prix_vna']]],(2,))
    if contenu.get('declarations_emetteurs'):
        from services.balance_emetteurs_service import presentation, PERIODES
        from services.balance_etic_tables_service import STATUTS
        vue = presentation(dossier)
        feuille('Origine émetteurs', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Version source', vue['parent']['version']],
            ['Empreinte source', vue['parent']['empreinte_sha256']], ['Auteur', vue['auteur']['nom']],
            ['Conservé le UTC', vue['conserve_le_utc']], *[['Alerte', a] for a in vue['alertes']]])
        for table in vue['tables']:
            p = PERIODES[table['code']]; suffixe = 'N' if p == 'n' else 'N-1'; cols = table['colonnes_saisie']
            feuille('Émetteurs ' + suffixe, [c['label'] + (' ' + c.get('unite','') if c['type']=='number' else '') for c in cols] + ['Référence de source'],
                [[*[r[c['cle']] for c in cols], r['reference_source']] for r in table['lignes']],
                [i for i,c in enumerate(cols,1) if c['type']=='number' and c.get('unite')=='MAD'])
            feuille('Déclaration émetteurs '+suffixe, ['État', 'Justification'], [[STATUTS[table['statut']], table['justification']]])
            controle = vue['controle_emetteurs']['periodes'][p]
            feuille('Contrôle émetteurs '+suffixe, ['Compte251', 'Brut source MAD', 'Somme brute déclarée MAD', 'Écart déclaré moins source MAD', 'Lignes'],
                [[r['compte'], r['solde_brut_source'], r['somme_brute_declaree'], r['ecart_brut'], r['lignes']] for r in controle['comptes']], (2,3,4))
            for a in controle['alertes']:wb['Origine émetteurs'].append(['Alerte '+suffixe,a])
    if contenu.get('financement_documentaire'):
        from services.balance_financement_service import presentation
        vue = presentation(dossier)
        feuille('Origine financement', ['Information', 'Valeur'], [
            ['Portée', vue['note']], ['Version source', vue['parent']['version']],
            ['Empreinte source', vue['parent']['empreinte_sha256']], ['Auteur', vue['auteur']['nom']],
            ['Conservé le UTC', vue['conserve_le_utc']], ['Prêt à déposer', 'Non'],
            ['CAF N MAD', vue['caf']['n']], ['CAF N-1 MAD', vue['caf']['n1']],
            ['Flux connus N', vue['flux_renseignes']['n']], ['Flux connus N-1', vue['flux_renseignes']['n1']]])
        if vue.get('motif_precision'):
            wb['Origine financement'].append(['Limite technique', vue['motif_precision']])
        feuille('Flux documentaires', ['Flux', 'Libellé', 'N MAD', 'N-1 MAD', 'Justification N', 'Justification N-1'],
            [[r['code'], r['titre'], r['n'], r['n1'], r['justification_n'], r['justification_n1']] for r in vue['lignes']], (3, 4))
        tf = vue['tableau']
        if tf:
            feuille('Financement totaux', ['Information', 'N MAD', 'N-1 MAD'], [
                ['Ressources stables', tf['total_ressources'], tf['total_ressources_n1']],
                ['Emplois stables', tf['total_emplois'], tf['total_emplois_n1']]], (2, 3))
            feuille('Financement masses', ['Rubrique', 'N MAD', 'N-1 MAD'],
                [[r['libelle'], r['n'], r['n1']] for r in tf['synthese']], (2, 3))
            feuille('Financement flux', ['Nature', 'Rubrique', 'N MAD', 'N-1 MAD'],
                [[nature, r['libelle'], r['montant'], r['n1']] for nature, rows in
                 [('Ressources stables', tf['ressources']), ('Emplois stables', tf['emplois'])] for r in rows], (3, 4))
            feuille('Financement contrôle', ['Information', 'Montant N MAD'], [
                ['Total ressources stables', tf['total_ressources']], ['Total emplois stables', tf['total_emplois']],
                ['Variation fonds de roulement', tf['variation_fonds_roulement']],
                ['Variation BFG', tf['variation_bfg']], ['Variation trésorerie', tf['variation_tresorerie']],
                ['Écart de rapprochement', tf['ecart_controle']],
                ['Écart total général', tf['ecart_total_general']]], (2,))
    ajouter_logo_xlsx(wb, societe)
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
