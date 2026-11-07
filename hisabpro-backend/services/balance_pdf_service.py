"""PDF de balances depuis les moteurs existants ; aucun montant reçu du client."""
from decimal import Decimal
from calendar import monthrange
from html import escape
from io import BytesIO

from fastapi import HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import models
from services.logo_export_service import ajouter_logo_pdf


def decaler_annee(date_source):
    annee = date_source.year - 1
    return date_source.replace(year=annee, day=min(date_source.day, monthrange(annee, date_source.month)[1]))


def nombre(value):
    return Decimal(str(value or 0)).quantize(Decimal('0.01'))


def positions(row):
    initial, debit, credit, final = [nombre(row.get(k)) for k in ('solde_initial', 'debit', 'credit', 'solde_final')]
    return [max(initial, 0), max(-initial, 0), debit, credit, max(final, 0), max(-final, 0)]


def format_mad(value):
    return f'{value:,.2f}'.replace(',', ' ').replace('.', ',')


def exporter_balance_pdf(db, user, exercice, genre, date_from, date_to, type_tiers):
    from routers.ecritures import reporting_balance
    from services.recouvrement_service import construire_situation
    sid = user['societe_id']
    societe = db.query(models.Societe).filter_by(id=sid).first()
    if not societe:
        raise HTTPException(404, 'Société introuvable')
    lignes, colonnes = [], ['Initial D', 'Initial C', 'Mvt débit', 'Mvt crédit', 'Final D', 'Final C']
    titres = {'generale': 'Balance générale', 'auxiliaire': 'Balance auxiliaire', 'agee': 'Balance âgée',
              'resultat': 'Balance résultat', 'comparative': 'Balance comparative des mouvements'}
    synthese = []
    calcul_incomplet = False
    if genre in ('generale', 'auxiliaire'):
        rapport = reporting_balance(exercice, date_from, date_to, user, db)
        if genre == 'generale':
            for row in rapport['comptes']:
                lignes.append((f"{row['compte']} — {row['libelle']}", positions(row)))
        else:
            prefixe = '3421' if type_tiers == 'client' else '4411'
            for row in rapport['auxiliaire'].get(prefixe, []):
                nom = f"{row.get('compte_auxiliaire') or prefixe} — {row['tiers']}"
                if row.get('identifie') is False:
                    nom += ' (Non identifié)'
                lignes.append((nom, positions(row)))
    elif genre == 'resultat':
        rapport = reporting_balance(exercice, date_from, date_to, user, db)
        colonnes = ['Charges', 'Produits']
        for row in rapport['comptes']:
            compte = row['compte']
            if compte.startswith(('6', '7')):
                net = nombre(row['debit']) - nombre(row['credit'])
                valeurs = [net, Decimal(0)] if compte.startswith('6') else [Decimal(0), -net]
                lignes.append((f"{compte} — {row['libelle']}", valeurs))
        charges = sum((r[1][0] for r in lignes), Decimal(0))
        produits = sum((r[1][1] for r in lignes), Decimal(0))
        resultat = produits - charges
        synthese = [f"Total charges : {format_mad(charges)} MAD", f"Total produits : {format_mad(produits)} MAD",
                    f"Résultat net signé : {format_mad(resultat)} MAD"]
    elif genre == 'comparative':
        rapport = reporting_balance(exercice, date_from, date_to, user, db)
        rapport_n1 = reporting_balance(exercice - 1, decaler_annee(date_from), decaler_annee(date_to), user, db)
        colonnes = [f'Solde {exercice - 1}', f'Solde {exercice}', 'Variation MAD', 'Variation %']
        comptes_n = {r['compte']: r for r in rapport['comptes']}
        comptes_n1 = {r['compte']: r for r in rapport_n1['comptes']}
        for compte in sorted(set(comptes_n) | set(comptes_n1)):
            n, n1 = comptes_n.get(compte, {}), comptes_n1.get(compte, {})
            solde_n = nombre(n.get('debit')) - nombre(n.get('credit'))
            solde_n1 = nombre(n1.get('debit')) - nombre(n1.get('credit'))
            variation = ((solde_n - solde_n1) / abs(solde_n1) * 100) if solde_n1 else None
            label = n.get('libelle') or n1.get('libelle') or 'Compte non référencé'
            lignes.append((f'{compte} — {label}', [solde_n1, solde_n, solde_n - solde_n1, variation]))
    else:
        rapport = construire_situation(db, sid, exercice, date_reference=date_to)
        colonnes = ['Reste dû', 'Non échu', '1-30 j', '31-60 j', '61-90 j', '>90 j']
        cles = ['non_echu', '1_30', '31_60', '61_90', 'plus_90']
        domaine = 'vente' if type_tiers == 'client' else 'achat'
        calcul_incomplet = bool(rapport.get('resume', {}).get(domaine, {}).get('calcul_incomplet'))
        if calcul_incomplet:
            synthese.append('Calcul incomplet : soldes et totaux à vérifier. Aucune valeur indéterminable n’est assimilée à zéro.')
        for facture in rapport.get('factures', []):
            if facture['type'] != domaine:
                continue
            if facture.get('reste_du') is None:
                lignes.append((f"{facture.get('tiers') or 'Tiers non renseigné'} — {facture['numero']} · {facture['date']} · {facture.get('ras_anomalie') or 'Solde indéterminable'}", [None] * len(colonnes)))
                continue
            if nombre(facture.get('reste_du')) <= Decimal('.01'):
                continue
            valeurs = [nombre(facture['reste_du'])] + [Decimal(0)] * 5
            echeances = [e for e in facture.get('echeances', []) if nombre(e.get('reste_du')) > Decimal('.01')]
            for row in echeances or [facture]:
                tranche = row.get('tranche_age')
                index = cles.index(tranche) if tranche in cles else 0
                valeurs[index + 1] += nombre(row['reste_du'])
            nom = f"{facture.get('tiers') or 'Tiers non renseigné'} — {facture['numero']} · {facture['date']} · Échéance {facture.get('date_echeance') or '—'}"
            lignes.append((nom, valeurs))
    totaux = [] if genre == 'comparative' else ([None] * len(colonnes) if calcul_incomplet else [sum((r[1][i] for r in lignes), Decimal(0)) for i in range(len(colonnes))])
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=14*mm, rightMargin=14*mm,
                           topMargin=14*mm, bottomMargin=16*mm, title=titres[genre])
    style = ParagraphStyle('balance', fontName='Helvetica', fontSize=8, leading=10)
    titre = ParagraphStyle('balance-titre', parent=style, fontName='Helvetica-Bold', fontSize=14, leading=18)
    p = lambda texte: Paragraph(escape(str(texte)), style)
    periode = f"Date d’arrêté : {date_to}" if genre == 'agee' else f"Période : {date_from} au {date_to}"
    if genre == 'comparative':
        periode += f' · Comparé au {decaler_annee(date_from)} au {decaler_annee(date_to)}'
    filtre = '' if genre in ('generale', 'resultat', 'comparative') else f" · {'Clients (3421)' if type_tiers == 'client' else 'Fournisseurs (4411)'}"
    source = 'Factures et échéanciers, règlements et crédits actifs' if genre == 'agee' else 'Écritures définitives uniquement'
    story = [Paragraph(escape(titres[genre] + filtre), titre), p(societe.raison_sociale), p(periode),
             p(f'Exercice {exercice} · MAD · {source}'), Spacer(1, 5*mm)]
    ajouter_logo_pdf(story, societe)
    if genre in ('resultat', 'comparative'):
        story.append(p('Soldes des mouvements de la période, hors soldes d’ouverture.'))
    story += [p(texte) for texte in synthese]
    def fmt(value):
        return format_mad(value)
    data = [[p('Compte / tiers / référence')] + [p(c) for c in colonnes]]
    def cellule(value, index):
        if value is None:
            return p('À vérifier' if genre == 'agee' else 'N/A')
        if genre == 'comparative' and index == 3:
            return p(f'{value:.1f}%')
        return p(fmt(value))
    data += [[p(label)] + [cellule(v, i) for i, v in enumerate(valeurs)] for label, valeurs in lignes]
    if not lignes:
        data.append([p('Aucune ligne pour cette sélection')] + [p('0,00')] * len(colonnes))
    if genre != 'comparative':
        data.append([p('TOTAL GÉNÉRAL')] + [cellule(v, i) for i, v in enumerate(totaux)])
    largeur_compte = 103 if len(colonnes) > 4 else 117
    largeur_montant = (265 - largeur_compte) / len(colonnes)
    table = Table(data, colWidths=[largeur_compte*mm] + [largeur_montant*mm]*len(colonnes), repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E6F1FB')),
        ('GRID',(0,0),(-1,-1),.25,colors.HexColor('#DDDDDD')),
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),5),
        ('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    if genre != 'comparative':
        table.setStyle(TableStyle([('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E6F1FB'))]))
    story.append(table)
    def pied(canvas, document):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(14*mm, 8*mm, 'HisabPro · Balance comptable · MAD')
        canvas.drawRightString(283*mm, 8*mm, f'Page {document.page}')
    doc.build(story, onFirstPage=pied, onLaterPages=pied)
    return buf.getvalue()
