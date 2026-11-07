"""PDF de préparation externe depuis le snapshot vérifié, sans liquidation supposée."""
from io import BytesIO
from decimal import Decimal
from xml.sax.saxutils import escape
from services.logo_export_service import ajouter_logo_pdf
from services.balance_preparation_export_service import presentation_bilan, NOTE_DETAIL
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, PageBreak, Spacer


def generer_preparation_pdf(dossier, societe):
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=12*mm,
        rightMargin=12*mm, topMargin=12*mm, bottomMargin=15*mm,
        title=f"Préparation balances {dossier['exercice']} version {dossier['version']}")
    styles = getSampleStyleSheet()
    p = lambda value: Paragraph(escape(str(value)), styles['BodyText'])
    f = lambda value: 'Indisponible' if value is None else f'{Decimal(str(value)):,.2f}'.replace(',', ' ').replace('.', ',')
    contenu = dossier['contenu']; current = contenu['preparation']['etats']
    previous = contenu['preparation']['etats_n1']
    story = [Paragraph('Préparation indépendante depuis balances', styles['Title']),
        p(societe.raison_sociale), p(f"Exercice {dossier['exercice']} · Version {dossier['version']}"),
        p(f"Période déclarée : {contenu['periode']['debut']} au {contenu['periode']['fin']}"),
        p('À compléter — aucune écriture ni archive fiscale définitive créée.'),
        p('Identité et logo actuels, hors empreinte du contenu conservé.'),
        p('Empreinte des données normalisées : ' + dossier['empreinte_sha256']), Spacer(1, 8*mm)]
    ajouter_logo_pdf(story, societe)
    for note in contenu['preparation']['avertissements']:
        story.append(p(note))
    for note in contenu['preparation']['a_completer']:
        story.append(p('À compléter : ' + note))
    for key, value in contenu['sources']['noms_fichiers'].items():
        story.append(p(f'Source déclarée {key.upper()} : {value}'))

    def tableau(titre, rows, entetes=None, largeurs=None):
        story.extend([PageBreak(), Paragraph(titre, styles['Heading1'])])
        data = [[p(v) for v in (entetes or ['Rubrique', 'Montant N (MAD)', 'Montant N-1 (MAD)'])]]
        data += [[p(label), *[f(v) for v in montants]] for label, *montants in rows]
        table = Table(data, colWidths=largeurs or [165*mm, 53*mm, 53*mm], repeatRows=1)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef5')),
            ('GRID',(0,0),(-1,-1),0.25,colors.lightgrey), ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('ALIGN',(1,1),(-1,-1),'RIGHT'), ('FONTSIZE',(0,0),(-1,-1),9),
            ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        story.append(table)

    detail = presentation_bilan(dossier)
    for side, title in [('actif', 'Bilan — actif détaillé'), ('passif', 'Bilan — passif')]:
        rows = [(('Pour mémoire · ' if r['type'] == 'detail' else '') +
                 (r.get('numero', '') + ' ' + r['label']).strip(), *r['valeurs'])
                for r in detail[side] if r['valeurs']]
        if side == 'actif':
            tableau(title, rows, ['Rubrique', 'Brut N MAD', 'Amort. / prov. N MAD', 'Net N MAD', 'Net N-1 MAD'],
                    [139*mm, 33*mm, 33*mm, 33*mm, 33*mm])
            story.append(p(NOTE_DETAIL))
            if contenu['sources'].get('n') is None:
                story.append(p('Sources détaillées indisponibles dans cette ancienne version ; agrégats conservés seulement.'))
        else:
            tableau(title, rows)
    for key, title in [('cpc','Compte de Produits et Charges'), ('esg','État des Soldes de Gestion')]:
        source = current[key]; old = previous[key] if previous else None
        old_rows = {(r.get('code'), r['libelle']): r['montant'] for r in old['lignes'] if r.get('montant') is not None} if old else {}
        now_rows = {(r.get('code'), r['libelle']): r['montant'] for r in source['lignes'] if r.get('montant') is not None}
        keys = list(now_rows) + [key for key in old_rows if key not in now_rows]
        rows = [(key[1], now_rows.get(key), old_rows.get(key)) for key in keys]
        tableau(title, rows or [('Indisponible', None, None)])
        if source.get('disponible') is False:
            story.append(p('N : ' + source['motif']))
        if old and old.get('disponible') is False:
            story.append(p('N-1 : ' + old['motif']))
    for cle, suffixe in [('n', 'N'), ('n1', 'N-1')]:
        source = contenu['sources'].get(cle)
        if source is not None:
            tableau('Balance source normalisée ' + suffixe,
                    [(r['compte'], r['debit'], r['credit']) for r in source],
                    ['Compte', 'Débit MAD', 'Crédit MAD'])
    if contenu.get('echeances_documentaires'):
        from services.balance_echeances_service import presentation
        vue = presentation(dossier)
        tableau('Échéances documentaires — préparation à compléter',
            [(r['section'] + ' · ' + r['compte'], r['total'], r['plus_un_an'], r['moins_un_an'],
              r['echues'], r['reliquat']) for r in vue['lignes']],
            ['Section / compte', 'Solde N MAD', 'Plus d’un an', 'Moins d’un an', 'Échues', 'Non qualifié'],
            [76*mm, 39*mm, 39*mm, 39*mm, 39*mm, 39*mm])
        story += [p(vue['note']), p(f"Version source {vue['parent']['version']} · Empreinte source : {vue['parent']['empreinte_sha256']}")]
        tableau('Analyses complémentaires documentaires',
            [(r['section'] + ' · ' + r['compte'], r['devises'], r['etat_organismes_publics'],
              r['entreprises_liees'], r['effets']) for r in vue['lignes']],
            ['Section / compte', 'En devises MAD', 'État / organismes publics', 'Entreprises liées', 'Effets'],
            [91*mm, 45*mm, 45*mm, 45*mm, 45*mm])
        story.append(p('Analyses susceptibles de se recouper : ne pas les additionner. Les soldes de sens inverse ne sont pas ventilés dans cette préparation.'))
        for r in vue['lignes']:
            story.append(p(r['section'] + ' · ' + r['compte'] + ' — Justification / référence : ' + (r['justification'] or 'À compléter')))
    if contenu.get('notes_etic_documentaires'):
        from services.balance_etic_notes_service import presentation, STATUTS
        vue = presentation(dossier)
        story += [PageBreak(), Paragraph('Notes documentaires ETIC', styles['Heading1']),
                  p(vue['note']), p('Auteur : ' + vue['auteur']['nom']),
                  p('Conservé le UTC : ' + vue['conserve_le_utc']),
                  p(f"Version source {vue['parent']['version']} · Empreinte source : {vue['parent']['empreinte_sha256']}")]
        for r in vue['lignes']:
            story += [Spacer(1, 4*mm), p(r['code'] + ' · ' + r['titre']),
                      p('État de la note : ' + STATUTS[r['statut']]),
                      Paragraph(escape('Texte : ' + (r['texte'] or 'À compléter')).replace('\n', '<br/>'), styles['BodyText']),
                      Paragraph(escape('Référence / justification : ' + (r['justification'] or 'À compléter')).replace('\n', '<br/>'), styles['BodyText'])]
    if contenu.get('tables_etic_documentaires'):
        from services.balance_etic_tables_service import presentation, STATUTS
        vue = presentation(dossier)
        story += [PageBreak(), Paragraph('Tableaux documentaires ETIC B8/B9', styles['Heading1']),
            p(vue['note']), p('Auteur : ' + vue['auteur']['nom']),
            p('Conservé le UTC : ' + vue['conserve_le_utc']),
            p(f"Version source {vue['parent']['version']} · Empreinte source : {vue['parent']['empreinte_sha256']}")]
        story += [p(a) for a in vue['alertes']]
        for r in vue['tables']:
            story += [Spacer(1, 4*mm), Paragraph(escape(r['code'] + ' · ' + r['titre']), styles['Heading2']),
                      p(STATUTS[r['statut']]), p('Justification : ' + (r['justification'] or 'À compléter'))]
            if not r['lignes']:
                story.append(p('Aucune ligne saisie ; ne pas assimiler à néant sans déclaration explicite.'))
            for i, ligne in enumerate(r['lignes'], 1):
                story.append(Paragraph('Ligne ' + str(i), styles['Heading3']))
                for c in r['colonnes_saisie']:
                    v = ligne[c['cle']]
                    valeur = f(v) + ' MAD' if c['type'] == 'number' else (v or 'À compléter')
                    story.append(Paragraph(escape(c['label'] + ' : ' + valeur).replace('\n', '<br/>'), styles['BodyText']))
                story.append(Paragraph(escape('Référence de source : ' + (ligne['reference_source'] or 'À compléter')).replace('\n', '<br/>'), styles['BodyText']))
    if contenu.get('annexes_etic_documentaires'):
        from services.balance_etic_annexes_service import presentation, STATUTS
        vue = presentation(dossier)
        story += [PageBreak(), Paragraph('Annexes documentaires ETIC', styles['Heading1']),
            p(vue['note']), p('Auteur : ' + vue['auteur']['nom']),
            p('Conservé le UTC : ' + vue['conserve_le_utc']),
            p(f"Version source {vue['parent']['version']} · Empreinte source : {vue['parent']['empreinte_sha256']}")]
        story += [p(a) for a in vue['alertes']]
        for r in vue['tables']:
            story += [Spacer(1, 4*mm), Paragraph(escape(r['code'] + ' · ' + r['titre']), styles['Heading2']),
                      p(STATUTS[r['statut']]), p('Justification : ' + (r['justification'] or 'À compléter'))]
            if not r['lignes']:
                story.append(p('Aucune ligne saisie ; ne pas assimiler à néant sans déclaration explicite.'))
            for i, ligne in enumerate(r['lignes'], 1):
                story.append(Paragraph('Ligne ' + str(i), styles['Heading3']))
                for c in r['colonnes_saisie']:
                    v = ligne[c['cle']]
                    unite = c.get('unite', 'MAD')
                    valeur = ((f(v) + ' MAD' if unite == 'MAD' else ('Indisponible' if v is None else str(v)) + ' ' + unite) if c['type'] == 'number' else (v or 'À compléter'))
                    story.append(Paragraph(escape(c['label'] + ' : ' + valeur).replace('\n', '<br/>'), styles['BodyText']))
                story.append(Paragraph(escape('Référence de source : ' + (ligne['reference_source'] or 'À compléter')).replace('\n', '<br/>'), styles['BodyText']))
    if contenu.get('annexes_etic_documentaires', {}).get('controle_capital'):
        from services.balance_capital_controle_service import lignes_export
        controle = contenu['annexes_etic_documentaires']['controle_capital']
        story += [PageBreak(), Paragraph('Contrôles arithmétiques du capital déclaré', styles['Heading1'])]
        for label, valeur, unite in lignes_export(controle):
            story.append(p(label + ' : ' + ('Indisponible' if valeur is None else str(valeur) + ' ' + unite)))
    if contenu.get('detail_cpc_documentaire'):
        bloc = contenu['detail_cpc_documentaire']; vue = bloc['vue']
        story += [PageBreak(), Paragraph(escape(vue['code'] + ' · ' + vue['titre']), styles['Heading1']),
            p(vue['note']), p('Méthode : ' + vue['methode']), p('Auteur : ' + bloc['auteur']['nom']),
            p('Conservé le UTC : ' + bloc['conserve_le_utc']),
            p('Empreinte source : ' + bloc['parent']['empreinte_sha256'])]
        for periode, libelle in [('n', 'N'), ('n1', 'N-1')]:
            detail = vue['periodes'][periode]
            story.append(Paragraph('Détail CPC ' + libelle, styles['Heading2']))
            if not detail['disponible']:
                story.append(p(detail['motif']))
                continue
            tableau('Soldes signés du CPC ' + libelle,
                [(r['compte'] + ' · ' + r['nature'] + ' · Libellé non conservé', r['montant']) for r in detail['lignes']],
                ['Compte / nature', 'Solde signé MAD'], [210*mm, 61*mm])
            if not detail['lignes']:
                story.append(p('Aucun solde non nul des classes 6 et 7 dans cette source.'))
            for k in ('charges', 'produits', 'resultat'):
                story.append(p(k.capitalize() + ' · Détail : ' + f(detail[k]) + ' MAD · CPC figé : ' +
                    f(detail['cpc_' + k]) + ' MAD · Écart détail moins CPC : ' + f(detail['ecart_' + k]) + ' MAD'))
    if contenu.get('non_valeurs_documentaires'):
        bloc = contenu['non_valeurs_documentaires']; vue = bloc['vue']
        story += [PageBreak(), Paragraph(escape(vue['code'] + ' · ' + vue['titre']), styles['Heading1']),
            p(vue['note']), p('Méthode : ' + vue['methode']), p('Auteur : ' + bloc['auteur']['nom']),
            p('Conservé le UTC : ' + bloc['conserve_le_utc']),
            p('Empreinte source : ' + bloc['parent']['empreinte_sha256'])]
        for periode, libelle in [('n', 'N'), ('n1', 'N-1')]:
            detail = vue['periodes'][periode]
            story.append(Paragraph('Non-valeurs ' + libelle, styles['Heading2']))
            if not detail['disponible']:
                story.append(p(detail['motif']))
                continue
            tableau('Soldes des non-valeurs ' + libelle,
                [(r['compte'] + ' · ' + r['nature'] + ' · Libellé non conservé', r['montant']) for r in detail['lignes']],
                ['Compte / nature', 'Solde signé MAD'], [210*mm, 61*mm])
            if not detail['lignes']:
                story.append(p('Aucun solde non nul des comptes21 et281 dans cette source.'))
            for k in ('brut', 'amortissements', 'net'):
                story.append(p(k.capitalize() + ' · Détail : ' + f(detail[k]) + ' MAD · Bilan figé : ' +
                    f(detail['bilan_' + k]) + ' MAD · Écart détail moins bilan : ' + f(detail['ecart_' + k]) + ' MAD'))
    if contenu.get('extra_c3_documentaire'):
        from services.balance_c3_extra_service import presentation,CHAMPS
        vue=presentation(dossier)
        story += [PageBreak(),Paragraph('Déclarations extra-comptables C3',styles['Heading1']),p(vue['note']),
            p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Version parent : '+str(vue['parent']['version'])),p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        for t in vue['tables']:
            periode={'C3-N':'n','C3-N1':'n1','C3-N2':'n2'}[t['code']];r=vue['declarations_c3'][periode]
            story += [Paragraph(t['titre'],styles['Heading2']),p('Déclaration : '+t['statut']),p('Justification : '+t['justification']),
                p('Désignation : '+r['nature']),p('Référence de source : '+r['reference_source']),p('Décisions et affectations : '+(r['affectations_justifiees'] or 'À documenter'))]
            tableau('Valeurs déclarées '+t['titre'],
                [(label+' ('+unite+')',r[k]) for k,(label,unite,_) in CHAMPS.items()],
                ['Information et unité','Valeur déclarée'],[210*mm,61*mm])
    if contenu.get('comparatif_n2_documentaire'):
        bloc=contenu['comparatif_n2_documentaire'];source=bloc['source_preparation'];totaux=bloc['totaux_exacts']
        story += [PageBreak(),Paragraph('Source comparative N-2 rattachée',styles['Heading1']),p(bloc['note']),
            p('Exercice source : '+str(source['exercice'])),p('Préparation source : '+str(source['id'])+' · version '+str(source['version'])),
            p('Empreinte source : '+source['empreinte_sha256']),p('Référence de source : '+bloc['reference_source']),
            p('Fichier source : '+str(bloc['nom_fichier_source'] or 'Non renseigné')),
            p('Rattachée par : '+bloc['auteur']['nom']+' · '+bloc['conserve_le_utc']),
            p('Version parent : '+str(bloc['parent']['version'])),p('Empreinte parent : '+bloc['parent']['empreinte_sha256']),
            p('Nombre de comptes : '+str(totaux['comptes']))]
        tableau('Balance source N-2',[(r['compte'],r['debit'],r['credit']) for r in bloc['sources_n2']],
            ['Compte','Débit MAD','Crédit MAD'],[149*mm,61*mm,61*mm])
        tableau('Totaux N-2',[('Débit = crédit',totaux['debit'],totaux['credit'])],
            ['Contrôle','Débit MAD','Crédit MAD'],[149*mm,61*mm,61*mm])
    if contenu.get('indicateurs_comptables_documentaires'):
        bloc=contenu['indicateurs_comptables_documentaires'];vue=bloc['vue']
        story += [PageBreak(),Paragraph('C3 — Indicateurs comptables indépendants',styles['Heading1']),
            p(vue['note']),p('Méthode : '+vue['methode']),p('Auteur : '+bloc['auteur']['nom']),
            p('Conservé le UTC : '+bloc['conserve_le_utc']),p('Version source : '+str(bloc['parent']['version'])),
            p('Empreinte source : '+bloc['parent']['empreinte_sha256']),
            p('À documenter : '+' ; '.join(vue['informations_a_completer']))]
        labels=[('situation_nette','Situation nette'),('chiffre_affaires_ht','Chiffre d’affaires711/712'),
            ('resultat_avant_impots','Résultat avant impôts'),('impots_resultats','Impôts comptabilisés'),
            ('resultat_net','Résultat net comptable'),('salaires_bruts','Rémunérations comptabilisées6171')]
        for periode,libelle in [('n','N'),('n1','N-1'),('n2','N-2')]:
            d=vue['periodes'][periode]
            tableau('Indicateurs C3 '+libelle,[(label,d[k],d['reference_'+k],d['ecart_'+k]) for k,label in labels],
                ['Indicateur','Détail MAD','États figés MAD','Écart MAD'],[124*mm,49*mm,49*mm,49*mm])
            if not d['disponible']:story.append(p(d['motif']))
            story += [p(a) for a in d['avertissements']]
            from services.balance_c3_extra_service import CHAMPS as champs_extra_c3
            tableau('Déclarations extra-comptables C3 '+libelle,
                [(label+' ('+unite+')',d[k]) for k,(label,unite,_) in champs_extra_c3.items()],
                ['Information et unité','Déclaration explicite'],[210*mm,61*mm])
            story += [p('Référence extra-comptable : '+(d.get('reference_extra_c3') or 'À documenter')),
                p('Décisions et affectations : '+(d.get('affectations_justifiees') or 'À documenter'))]

            tableau('Comptes sources C3 '+libelle,[(row['compte']+' · '+row['nature']+' · Libellé non conservé',row['montant']) for row in d['lignes']]
                or [('Source détaillée indisponible ou sans solde du périmètre',None)],['Compte','MAD'],[210*mm,61*mm])
    if contenu.get('tva_documentaire'):
        from services.balance_tva_documentaire_service import presentation,CHAMPS
        vue=presentation(dossier);ctrl=vue['controle_tva'];table=vue['tables'][0]
        story += [PageBreak(),Paragraph('B14 — Flux TVA documentaires',styles['Heading1']),p(vue['note']),
            p('Méthode : '+ctrl['methode']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Version source : '+str(vue['parent']['version'])),p('Empreinte source : '+vue['parent']['empreinte_sha256']),
            p('Déclaration : '+table['statut']),p('Justification : '+table['justification'])]
        for r in ctrl['lignes']:
            tableau(r['titre'],[(label,r['montants'][k]) for k,label in CHAMPS.items()],['Indicateur','MAD'],[210*mm,61*mm])
            if r['references_declarations']:story.append(p('Références des déclarations : '+r['references_declarations']))
            if r['reference_source']:story.append(p('Référence de source : '+r['reference_source']))
        story += [p(a) for a in ctrl['alertes']]
        for periode,nom in [('n','N'),('n1','N-1')]:
            d=ctrl['sources'][periode]
            if not d['disponible']:story.append(p(nom+' : '+d['motif']))
            tableau('Comptes sources TVA '+nom,[(r['compte']+' · '+r['famille']+' · Libellé non conservé',r['montant']) for r in d['lignes']]
                or [('Aucun solde détaillé du périmètre',None)],['Compte','MAD'],[210*mm,61*mm])
        story.append(p('Aucun dépôt confirmé, aucune liquidation ni aucun paiement déduit.'))
    if contenu.get('passage_fiscal_documentaire'):
        from services.balance_passage_fiscal_service import presentation,LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_passage_fiscal'];table=vue['tables'][0]
        story += [PageBreak(),Paragraph('B12 — Passage fiscal documentaire',styles['Heading1']),
            p(vue['note']),p('Méthode : '+ctrl['methode']),p('Auteur : '+vue['auteur']['nom']),
            p('Conservé le UTC : '+vue['conserve_le_utc']),p('Version source : '+str(vue['parent']['version'])),
            p('Empreinte source : '+vue['parent']['empreinte_sha256'])]
        tableau('B12 N — montants',[(LIBELLES[k],v) for k,v in ctrl['montants'].items() if k!='taux_is_declare'],
            ['Indicateur','MAD'],[210*mm,61*mm])
        story += [p('Taux IS déclaré : '+(ctrl['montants']['taux_is_declare']+' %' if ctrl['montants']['taux_is_declare'] is not None else 'Indisponible')),
            p('Déclaration : '+table['statut']),p('Justification : '+table['justification']),
            p('À compléter : '+' ; '.join(ctrl['a_completer'])),p('CM, CSS, crédits, acomptes, solde final : Indisponibles.')]
        if not ctrl['disponible']:story.append(p(ctrl['motif']))
        story += [p(a) for a in ctrl['alertes']]
        for row in table['lignes']:
            story += [p('Désignation : '+row['nature']),p('Référence de source : '+row['reference_source']),
                p('Régime/avantages déclarés : '+(row['regime_avantages'] or 'À documenter'))]
        tableau('Comptes sources B12 N',[(r['compte']+' · '+r['nature']+' · Libellé non conservé',r['montant']) for r in ctrl['lignes']]
            or [('Aucun solde détaillé disponible',None)],['Compte','MAD'],[210*mm,61*mm])
    if contenu.get('liquidation_is_documentaire'):
        from services.balance_liquidation_is_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_liquidation'];table=vue['tables'][0]
        story += [PageBreak(),Paragraph('Proposition conditionnelle IS/CM2026',styles['Heading1']),
            p(vue['note']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Empreinte parent : '+vue['parent']['empreinte_sha256']),
            p('Proposition conditionnelle disponible : '+('Oui' if ctrl['proposition_disponible'] else 'Non'))]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        story += [p('Déclaration : '+table['statut']),p('Justification : '+table['justification'])]
        for r in table['lignes']:
            story += [p(c['label']+' : '+str(r[c['cle']] if r[c['cle']] is not None else 'À qualifier')) for c in table['colonnes_saisie']]
            story.append(p('Référence de source : '+r['reference_source']))
        tableau('Simulation conservée, CSS séparée',[(LIBELLES[k],v) for k,v in ctrl['montants'].items()],['Information','MAD'],[210*mm,61*mm])
        story += [p('Source '+k+' : '+str((v or {}).get('cle') or 'Absente')) for k,v in ctrl['sources_conservees'].items()]
    if contenu.get('acomptes_is_documentaires'):
        from services.balance_acomptes_is_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_acomptes']
        story += [PageBreak(),Paragraph('Acomptes IS — versements et affectations justifiés2026',styles['Heading1']),
            p(vue['note']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Date de contrôle : '+str(ctrl['date_controle'] or 'À qualifier')),p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        for table in vue['tables']:
            story += [Paragraph(table['titre'],styles['Heading2']),p('Déclaration : '+table['statut']),p('Justification : '+table['justification'])]
            for i,r in enumerate(table['lignes'],1):
                story.append(Paragraph('Ligne '+str(i),styles['Heading3']))
                story += [p(c['label']+' : '+str(r[c['cle']] if r[c['cle']] is not None else 'À qualifier')) for c in table['colonnes_saisie']]
                story.append(p('Référence de source : '+r['reference_source']))
        tableau('Acomptes IS conservés',[(LIBELLES[k],v) for k,v in ctrl['montants'].items()],['Information','MAD'],[210*mm,61*mm])
        for r in ctrl['rapprochement_retenues']:
            story.append(p(r['reference']+' · Déjà utilisé : '+f(r['attendu'])+'MAD · Affecté : '+f(r['affecte'])+'MAD · Cohérent : '+('Oui' if r['coherent'] else 'Non')))
        for r in ctrl['echeancier']:
            story.append(p('Acompte'+str(r['numero'])+' · '+r['date_echeance']+' · Dû : '+f(r['du'])+'MAD · Couvert déclaré : '+f(r['couverture_declaree'])+'MAD · Reste : '+f(r['reste'])+'MAD · '+r['statut']))
    if contenu.get('taxe_professionnelle_documentaire'):
        from services.balance_taxe_professionnelle_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_tp']
        story += [PageBreak(),Paragraph('Taxe professionnelle — simulation brute interne',styles['Heading1']),p(vue['note']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        tableau('TP — calculs documentaires, sans montant dû confirmé',[(LIBELLES[k],v) for k,v in ctrl['montants'].items()],['Information','MAD'],[210*mm,61*mm])
        for table in vue['tables']:
            story += [Paragraph(table['titre'],styles['Heading2']),p('Déclaration : '+table['statut']),p('Justification : '+table['justification'])]
            for i,a in enumerate(table['lignes'],1):
                story.append(Paragraph('Ligne '+str(i),styles['Heading3']))
                story += [p(c['label']+' : '+str(a[c['cle']] if a[c['cle']] is not None else 'À qualifier')) for c in table['colonnes_saisie']]
                story.append(p('Référence source : '+a['reference_source']))
        for a in ctrl['etablissements']:
            story += [p(a['etablissement_ref']+' · Classe '+a['classe']+' · Brut exact '+str(a['brut_exact'])+' · À revoir : '+(', '.join(a['points_a_revoir']) or 'Revue déclarée'))]
    if contenu.get('remunerations_tiers_documentaires'):
        from services.balance_remunerations_tiers_service import presentation, MONTANTS
        vue=presentation(dossier);ctrl=vue['controle_tiers']
        story += [PageBreak(),Paragraph('Rémunérations des tiers — préparation interne',styles['Heading1']),p(vue['note']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        tableau('Totaux documentaires nets',[(label,ctrl['montants'][k]) for k,label in MONTANTS.items()],['Information','MAD'],[210*mm,61*mm])
        for table in vue['tables']:
            story += [Paragraph(table['titre'],styles['Heading2']),p('Déclaration : '+table['statut']),p('Justification : '+table['justification'])]
            for i,a in enumerate(table['lignes'],1):
                story.append(Paragraph('Ligne '+str(i),styles['Heading3']))
                story += [p(c['label']+' : '+str(a[c['cle']] if a[c['cle']] is not None else 'À qualifier')) for c in table['colonnes_saisie']]
                story.append(p('Référence de source : '+a['reference_source']))
        story += [p('Identité '+b['reference']+' : '+(', '.join(b['points_a_revoir']) or 'Renseignée et revue déclarée')) for b in ctrl['beneficiaires']]
        story += [p('Mouvement '+l['reference_source']+' : '+(', '.join(l['points_a_revoir']) or 'Renseigné et revue déclarée')) for l in ctrl['lignes']]
        for g in ctrl['regroupements']:
            story.append(p('Bénéficiaire '+g['beneficiaire_ref']+' · '+g['categorie']))
            tableau('Totaux déclarés par bénéficiaire/catégorie',[(label,g['montants'][k]) for k,label in MONTANTS.items()],['Information','MAD'],[210*mm,61*mm])
    if contenu.get('credits_is_documentaires'):
        from services.balance_credits_is_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_credits']
        story += [PageBreak(),Paragraph('Crédits IS — justificatifs qualifiés2026',styles['Heading1']),
            p(vue['note']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        for table in vue['tables']:
            story += [Paragraph(table['titre'],styles['Heading2']),p('Déclaration : '+table['statut']),p('Justification : '+table['justification'])]
            for i,r in enumerate(table['lignes'],1):
                story.append(Paragraph('Ligne '+str(i),styles['Heading3']))
                story += [p(c['label']+' : '+str(r[c['cle']] if r[c['cle']] is not None else 'À qualifier')) for c in table['colonnes_saisie']]
                story.append(p('Référence de source : '+r['reference_source']))
        tableau('Crédits IS conservés',[(LIBELLES[k],v) for k,v in ctrl['montants'].items()],['Information','MAD'],[210*mm,61*mm])
        story += [p('Ligne '+str(r['ligne'])+' · '+r['type_credit']+' · '+r['statut']) for r in ctrl['lignes']]
    if contenu.get('css_documentaire'):
        from services.balance_css_service import presentation, LIBELLES
        vue=presentation(dossier);ctrl=vue['controle_css'];t=vue['tables'][0]
        story += [PageBreak(),Paragraph('CSS — dernier exercice clos déclaré, année2026',styles['Heading1']),
            p(vue['note']),p('Méthode : '+ctrl['methode']),p('Auteur : '+vue['auteur']['nom']),
            p('Conservé le UTC : '+vue['conserve_le_utc']),p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        story += [p('Exercice de référence déclaré : '+str(ctrl['exercice_reference_declare'] or 'À qualifier')),
            p('Taux proportionnel (%) : '+str(ctrl['taux_proportionnel'] if ctrl['taux_proportionnel'] is not None else 'Indisponible')),
            p('Déclaration : '+t['statut']),p('Justification : '+t['justification'])]
        for r in t['lignes']:
            story += [p(c['label']+' : '+str(r[c['cle']] if r[c['cle']] is not None else 'À qualifier')) for c in t['colonnes_saisie']]
            story.append(p('Référence de source : '+r['reference_source']))
        tableau('CSS conservée',[(LIBELLES[k],v) for k,v in ctrl['montants'].items()],['Information','MAD'],[210*mm,61*mm])
    if contenu.get('cotisation_minimale_documentaire'):
        from services.balance_cotisation_minimale_service import presentation, LIBELLES
        vue = presentation(dossier); ctrl = vue['controle_cm']; t = vue['tables'][0]
        story += [PageBreak(), Paragraph('Cotisation minimale — calcul qualifié N2026', styles['Heading1']),
            p(vue['note']), p('Méthode : '+ctrl['methode']), p('Auteur : '+vue['auteur']['nom']),
            p('Conservé le UTC : '+vue['conserve_le_utc']), p('Empreinte parent : '+vue['parent']['empreinte_sha256'])]
        story += [p(k+' : '+v) for k,v in ctrl['reference_juridique'].items()]
        story += [p(a) for a in vue['alertes']+ctrl['alertes']]
        story += [p('Référence B12 conservée : '+str((ctrl['source_b12'] or {}).get('cle') or 'Absente')),
            p('Déclaration : '+t['statut']), p('Justification : '+t['justification'])]
        for r in t['lignes']:
            story += [p(c['label']+' : '+str(r[c['cle']] if r[c['cle']] is not None else 'À qualifier')) for c in t['colonnes_saisie']]
            story.append(p('Référence de source : '+r['reference_source']))
        tableau('Calcul CM conservé', [(LIBELLES[k],v) for k,v in ctrl['montants'].items()],
            ['Information','MAD'],[210*mm,61*mm])
        tableau('Comptes sources CM', [(r['compte']+' · '+('Dans la base' if r['retenu_base'] else 'Hors base')+' · '+r['famille'],r['montant']) for r in ctrl['lignes_sources']]
            or [('Aucune source disponible',None)],['Compte','MAD'],[210*mm,61*mm])
    if contenu.get('contexte_fiscal_documentaire'):
        from services.balance_contexte_fiscal_service import presentation, LIBELLES
        vue = presentation(dossier); ctrl = vue['controle_contexte_fiscal']
        story += [PageBreak(), Paragraph('Contexte fiscal documentaire interne', styles['Heading1']),
            p(vue['note']), p('Auteur : ' + vue['auteur']['nom']), p('Conservé le UTC : ' + vue['conserve_le_utc']),
            p('Empreinte parent : ' + vue['parent']['empreinte_sha256']),
            p('Référence B12 conservée : ' + ((ctrl['source_b12'] or {}).get('cle') or 'Absente')),
            p('IS théorique B12 pour mémoire : ' + f((ctrl['source_b12'] or {}).get('is_theorique_taux_declare'))),
            p('Impôt dû et solde final : Indisponibles. Aucune liquidation ni paiement confirmé.')]
        story += [p(a) for a in vue['alertes'] + ctrl['alertes']]
        tableau('Totaux documentaires, exhaustivité à vérifier',
            [(LIBELLES[k], v) for k, v in ctrl['montants'].items()], ['Information', 'MAD'], [210*mm, 61*mm])
        for t in vue['tables']:
            story += [Paragraph(escape(t['code'] + ' · ' + t['titre']), styles['Heading2']),
                p('Déclaration : ' + t['statut']), p('Justification : ' + t['justification'])]
            lignes = []
            for i, r in enumerate(t['lignes'], 1):
                story += [p('Ligne ' + str(i) + ' · ' + r['nature']), p('Référence de source : ' + r['reference_source'])]
                for c in t['colonnes_saisie']:
                    if c['type'] == 'number':
                        lignes.append((str(i) + ' · ' + c['label'], r[c['cle']]))
            tableau(t['code'] + ' · Montants déclarés', lignes or [('Déclaration sans ligne', None)],
                ['Information', 'MAD'], [210*mm, 61*mm])
    if contenu.get('resultat_courant_documentaire'):
        from services.balance_resultat_courant_service import presentation
        vue = presentation(dossier); ctrl = vue['controle_resultat_courant']
        story += [PageBreak(), Paragraph('B13 — Résultat courant documentaire', styles['Heading1']),
            p(vue['note']), p('Méthode : ' + ctrl['methode']), p('Auteur : ' + vue['auteur']['nom']),
            p('Conservé le UTC : ' + vue['conserve_le_utc']), p('Version source : ' + str(vue['parent']['version'])),
            p('Empreinte source : ' + vue['parent']['empreinte_sha256'])]
        labels = [('resultat_courant','Résultat courant source71/73 moins61/63'),
            ('cpc_resultat_courant','Résultat courant CPC VII figé'), ('ecart_courant','Écart source moins CPC VII'),
            ('impots_comptabilises_67','Impôts comptabilisés67 pour mémoire'),
            ('reintegrations','Réintégrations courantes déclarées'), ('deductions','Déductions courantes déclarées'),
            ('base_courante_documentaire','Base courante documentaire'), ('impot_theorique_declare','Impôt théorique courant déclaré'),
            ('courant_apres_impot_declare','Courant après impôt déclaré')]
        for table in vue['tables']:
            libelle = 'N' if table['code'] == 'B13-N' else 'N-1'
            d = ctrl['periodes']['n' if libelle == 'N' else 'n1']
            tableau('B13 ' + libelle, [(label, d[k]) for k,label in labels], ['Indicateur', 'MAD'], [210*mm,61*mm])
            story += [p('Déclaration : ' + table['statut']), p('Justification : ' + table['justification'])]
            if not d['disponible']: story.append(p(d['motif']))
            story += [p(a) for a in d['alertes']]
            for row in table['lignes']:
                story += [p('Désignation : ' + row['nature']), p('Référence de source : ' + row['reference_source']),
                    p('Régime/avantages déclarés : ' + (row['regime_avantages'] or 'À documenter'))]
            tableau('Comptes sources B13 ' + libelle,
                [(row['compte'] + ' · ' + row['nature'] + ' · Libellé non conservé', row['montant']) for row in d['lignes']]
                or [('Aucun solde détaillé disponible', None)], ['Compte', 'MAD'], [210*mm,61*mm])
    if contenu.get('participations_documentaires'):
        bloc = contenu['participations_documentaires']; vue = bloc['vue']
        story += [PageBreak(), Paragraph(escape(vue['code'] + ' · ' + vue['titre']), styles['Heading1']),
            p(vue['note']), p('Méthode : ' + vue['methode']), p('Auteur : ' + bloc['auteur']['nom']),
            p('Conservé le UTC : ' + bloc['conserve_le_utc']),
            p('Empreinte source : ' + bloc['parent']['empreinte_sha256']),
            p('Informations à documenter séparément : ' + ' ; '.join(vue['informations_a_completer']))]
        for periode, libelle in [('n', 'N'), ('n1', 'N-1')]:
            detail = vue['periodes'][periode]
            story.append(Paragraph('Participations ' + libelle, styles['Heading2']))
            if not detail['disponible']:
                story.append(p(detail['motif']))
                continue
            tableau('Soldes251 ' + libelle,
                [(r['compte'] + ' · Libellé non conservé', r['montant']) for r in detail['lignes']],
                ['Compte', 'Solde signé MAD'], [210*mm, 61*mm])
            if not detail['lignes']:
                story.append(p('Aucun solde251 non nul dans cette source ; aucune exhaustivité juridique présumée.'))
            story += [p('Émetteur, capital, quote-part et produits reçus : à compléter séparément, sans déduction des comptes.'),
                p('Titres251 : ' + f(detail['participations']) + ' MAD'),
                p('Autres soldes24/25 : ' + f(detail['autres_financieres']) + ' MAD'),
                p('Brut financier entier24/25 : ' + f(detail['financieres_brut']) + ' MAD · Bilan figé : ' +
                    f(detail['bilan_financieres_brut']) + ' MAD · Écart sur le même périmètre : ' + f(detail['ecart_financieres_brut']) + ' MAD')]
    if contenu.get('raccords_mouvements_documentaires'):
        from services.balance_raccords_mouvements_service import presentation
        vue=presentation(dossier);snap=vue['snapshot'];ctrl=snap['controle_raccords']
        story += [PageBreak(),Paragraph('Rattachements des clôtures de mouvements',styles['Heading1']),p(vue['note']),
            p('Raccord actuel : '+('Oui' if vue['actuel'] else 'À refaire après changement de mouvements ou sources')),
            p('Auteur : '+snap['auteur']['nom']),p('Conservé le UTC : '+snap['conserve_le_utc']),
            p('Empreinte mouvements contrôlés : '+snap['empreinte_mouvements']),p('Empreinte balance N contrôlée : '+snap['empreinte_source_n']),
            p('Version préparation source : '+str(snap['parent']['version']))]
        if not ctrl['source_disponible']:story.append(p('Source détaillée indisponible ; aucun solde nul fabriqué.'))
        for table in snap['catalogue']:
            code=table['code'];liens={r['ligne']:r['compte'] for t in snap['tables'] if t['code']==code for r in t['lignes']};controle=ctrl['tableaux'][code]
            story.append(Paragraph(escape(code+' · '+table['titre']),styles['Heading2']))
            for r in table['lignes']:
                story += [p('Ligne '+str(r['ligne'])+' · '+(r['nature'] or 'À compléter')+' · Clôture déclarée conservée : '+f(r['fin'])+' MAD'),
                    p('Compte : '+(liens[r['ligne']] or 'Non rattachée')+' · Source conservée : '+(r['reference_source'] or 'À compléter'))]
            for r in controle['comptes']:
                story.append(p('Compte '+r['compte']+' · Solde source : '+f(r['solde_source'])+' MAD · Somme déclarée : '+f(r['somme_clotures_declarees'])+' MAD · Écart : '+f(r['ecart'])+' MAD'))
            story.append(p('Lignes non rattachées du contrôle conservé : '+(', '.join(str(i) for i in controle['non_rattachees']) or 'Aucune')))
    if contenu.get('mouvements_documentaires'):
        from services.balance_mouvements_service import presentation
        from services.balance_etic_tables_service import STATUTS
        vue=presentation(dossier)
        story += [PageBreak(),Paragraph('Mouvements B2, B2bis et B5 déclarés',styles['Heading1']),p(vue['note']),
            p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),p('Empreinte source : '+vue['parent']['empreinte_sha256'])]
        story += [p(a) for a in vue['alertes']]
        for table in vue['tables']:
            c=vue['controle_mouvements']['tableaux'][table['code']]
            story += [Paragraph(escape(table['code']+' · '+table['titre']),styles['Heading2']),p(STATUTS[table['statut']]),p('Justification : '+table['justification'])]
            for i,r in enumerate(table['lignes'],1):
                story.append(Paragraph('Ligne '+str(i),styles['Heading3']))
                for col in table['colonnes_saisie']:
                    val=r[col['cle']];txt=(('Indisponible' if val is None else str(val))+' MAD') if col['type']=='number' else (val or 'À compléter')
                    story.append(Paragraph(escape(col['label']+' : '+txt).replace('\n','<br/>'),styles['BodyText']))
                story.append(p('Référence de source : '+r['reference_source']))
                ctrl=c['lignes'][i-1]
                story.append(p('Clôture reconstituée : '+f(ctrl['fin_reconstituee'])+' MAD · Déclarée : '+f(ctrl['fin_declaree'])+' MAD · Écart : '+f(ctrl['ecart_fin'])+' MAD'))
            story.append(p('Total des écarts : '+f(c['totaux']['ecart_fin'])+' MAD'))
    if contenu.get('cessions_documentaires'):
        from services.balance_cessions_service import presentation
        from services.balance_etic_tables_service import STATUTS
        vue=presentation(dossier);table=vue['tables'][0];controle=vue['controle_cessions']
        story += [PageBreak(),Paragraph('Cessions et retraits B3 déclarés',styles['Heading1']),
            p(vue['note']),p('Auteur : '+vue['auteur']['nom']),p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Empreinte source : '+vue['parent']['empreinte_sha256']),p(STATUTS[table['statut']]),p('Justification : '+table['justification'])]
        for i,r in enumerate(table['lignes'],1):
            story.append(Paragraph('Ligne '+str(i),styles['Heading3']))
            for col in table['colonnes_saisie']:
                val=r[col['cle']]
                txt=(('Indisponible' if val is None else str(val))+' MAD') if col['type']=='number' else (val or 'À compléter')
                story.append(Paragraph(escape(col['label']+' : '+txt).replace('\n','<br/>'),styles['BodyText']))
            story.append(p('Référence de source : '+r['reference_source']))
            story.append(p('Différence prix moins VNA : '+f(controle['lignes'][i-1]['difference_prix_vna'])+' MAD'))
        story.append(p('Total des différences : '+f(controle['total_difference_prix_vna'])+' MAD'))
        story += [p(a) for a in vue['alertes']+controle['alertes']]
    if contenu.get('declarations_emetteurs'):
        from services.balance_emetteurs_service import presentation, PERIODES
        from services.balance_etic_tables_service import STATUTS
        vue = presentation(dossier)
        story += [PageBreak(), Paragraph('Déclarations des émetteurs B4', styles['Heading1']),
            p(vue['note']), p('Auteur : '+vue['auteur']['nom']), p('Conservé le UTC : '+vue['conserve_le_utc']),
            p('Empreinte source : '+vue['parent']['empreinte_sha256'])]
        story += [p(a) for a in vue['alertes']]
        for table in vue['tables']:
            story += [Spacer(1,4*mm), Paragraph(escape(table['titre']), styles['Heading2']),
                p(STATUTS[table['statut']]), p('Justification : '+(table['justification'] or 'À compléter'))]
            for i,r in enumerate(table['lignes'],1):
                story.append(Paragraph('Ligne '+str(i), styles['Heading3']))
                for col in table['colonnes_saisie']:
                    val=r[col['cle']]
                    texte=(('Indisponible' if val is None else str(val))+' '+col.get('unite','')) if col['type']=='number' else (val or 'À compléter')
                    story.append(Paragraph(escape(col['label']+' : '+texte).replace('\n','<br/>'), styles['BodyText']))
                story.append(p('Référence de source : '+(r['reference_source'] or 'À compléter')))
            c = vue['controle_emetteurs']['periodes'][PERIODES[table['code']]]
            if not c['disponible']:story.append(p('Source détaillée indisponible ; aucun contrôle nul fabriqué.'))
            for r in c['comptes']:
                story.append(p('Compte '+r['compte']+' · Brut source : '+f(r['solde_brut_source'])+' MAD · Somme brute déclarée : '+f(r['somme_brute_declaree'])+' MAD · Écart : '+f(r['ecart_brut'])+' MAD'))
            story += [p(a) for a in c['alertes']]
    if contenu.get('financement_documentaire'):
        from services.balance_financement_service import presentation
        vue = presentation(dossier)
        story += [PageBreak(), Paragraph('Financement documentaire', styles['Heading1']),
            p(vue['note']), p('Auteur : ' + vue['auteur']['nom']),
            p('Conservé le UTC : ' + vue['conserve_le_utc']),
            p(f"Version source {vue['parent']['version']} · Empreinte source : {vue['parent']['empreinte_sha256']}"),
            p('CAF N : ' + f(vue['caf']['n']) + ' MAD · CAF N-1 : ' + f(vue['caf']['n1']) + ' MAD')]
        if vue.get('motif_precision'):
            story.append(p(vue['motif_precision']))
        tf = vue['tableau']
        if tf:
            tableau('Financement — synthèse des masses', [(r['libelle'], r['n'], r['n1']) for r in tf['synthese']])
            tableau('Financement — ressources stables', [(r['libelle'], r['montant'], r['n1']) for r in tf['ressources']])
            tableau('Financement — emplois stables', [(r['libelle'], r['montant'], r['n1']) for r in tf['emplois']])
            story += [p('Total ressources N : ' + f(tf['total_ressources']) + ' MAD'),
                      p('Total emplois N : ' + f(tf['total_emplois']) + ' MAD'),
                      p('Total ressources N-1 : ' + f(tf['total_ressources_n1']) + ' MAD'),
                      p('Total emplois N-1 : ' + f(tf['total_emplois_n1']) + ' MAD'),
                      p('Variation du fonds de roulement : ' + f(tf['variation_fonds_roulement']) + ' MAD'),
                      p('Écart de rapprochement : ' + f(tf['ecart_controle']) + ' MAD'),
                      p('Écart total général : ' + f(tf['ecart_total_general']) + ' MAD')]
            story += [p(v) for v in tf['avertissements']]
        tableau('Flux explicitement documentés', [(r['titre'], r['n'], r['n1']) for r in vue['lignes']])
        for r in vue['lignes']:
            story += [p(r['titre'] + ' · Source N : ' + (r['justification_n'] or 'À compléter')),
                      p('Source N-1 : ' + (r['justification_n1'] or 'À compléter'))]
    def footer(canvas, doc):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(12*mm, 7*mm, 'HisabPro · Préparation indépendante · À compléter')
        canvas.drawRightString(285*mm, 7*mm, str(doc.page))
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
