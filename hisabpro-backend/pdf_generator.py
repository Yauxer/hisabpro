# -*- coding: utf-8 -*-
"""Génération PDF HisabPro.

FACT.9 harmonise tous les documents commerciaux : Devis, BC, BL/BR, Factures
et Avoirs. La couche ReportLab reste volontairement sans logique comptable :
les routes/services lui transmettent des montants déjà calculés par les moteurs
HisabPro.
"""
from __future__ import annotations

import math
import os
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape
from services.logo_export_service import logo_pdf, ajouter_logo_pdf

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    PageBreak, Image,
)

# ── Palette ────────────────────────────────────────────────────────────────────
FONCE   = colors.HexColor("#182230")
BLEU    = colors.HexColor("#1769AA")
BLEU_C  = colors.HexColor("#EAF3FB")
GRIS    = colors.HexColor("#667085")
GRIS_C  = colors.HexColor("#98A2B3")
LIGNE   = colors.HexColor("#E4E7EC")
FOND    = colors.HexColor("#F8FAFC")
VERT_C  = colors.HexColor("#EAF4DF")
ROUGE_C = colors.HexColor("#FCEBEB")

HISABPRO_VERSION = os.getenv("HISABPRO_VERSION", "0.1.0")

S_TITRE   = ParagraphStyle("titre", fontName="Helvetica-Bold", fontSize=17, textColor=FONCE, leading=20)
S_SOC     = ParagraphStyle("soc", fontName="Helvetica-Bold", fontSize=11, textColor=FONCE, leading=14)
S_NORMAL  = ParagraphStyle("normal", fontName="Helvetica", fontSize=8.5, textColor=FONCE, leading=12)
S_GRIS    = ParagraphStyle("gris", fontName="Helvetica", fontSize=8, textColor=GRIS, leading=11)
S_LABEL   = ParagraphStyle("label", fontName="Helvetica-Bold", fontSize=7.4, textColor=GRIS, leading=9)
S_CELL    = ParagraphStyle("cell", fontName="Helvetica", fontSize=8.2, textColor=FONCE, leading=10.5)
S_CELL_D  = ParagraphStyle("cellD", parent=S_CELL, alignment=TA_RIGHT)
S_LETTRES = ParagraphStyle("lettres", fontName="Helvetica-Oblique", fontSize=8.3, textColor=FONCE, leading=12)
S_EXEMPL  = ParagraphStyle("exempl", fontName="Helvetica-Bold", fontSize=7.5, textColor=GRIS, alignment=TA_RIGHT)

QUALIF_COURT = {
    "taxable": None,
    "exonere_droit_deduction": "Exon. avec DD",
    "exonere_sans_deduction": "Exon. sans DD",
    "hors_champ": "Hors champ",
    "suspension": "Suspension",
}

# ── Montant en lettres (français) ─────────────────────────────────────────────
_UNITES = ["", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
           "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
           "dix-sept", "dix-huit", "dix-neuf"]
_DIZAINES = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante",
             "soixante", "quatre-vingt", "quatre-vingt"]

def _moins_de_cent(n):
    if n < 20:
        return _UNITES[n]
    d, u = divmod(n, 10)
    if d in (7, 9):
        u += 10
    mot = _DIZAINES[d]
    if u == 0:
        return "quatre-vingts" if d == 8 else mot
    if (u == 1 and d not in (8, 9)) or (u == 11 and d == 7):
        return f"{mot} et {_UNITES[u]}"
    return f"{mot}-{_UNITES[u]}"

def _moins_de_mille(n):
    c, r = divmod(n, 100)
    if c == 0:
        return _moins_de_cent(r)
    prefixe = "cent" if c == 1 else f"{_UNITES[c]} cent" + ("s" if r == 0 else "")
    return prefixe if r == 0 else f"{prefixe} {_moins_de_cent(r)}"

def _entier_en_lettres(n):
    if n == 0:
        return "zéro"
    parts = []
    milliards, n = divmod(n, 1_000_000_000)
    millions, n = divmod(n, 1_000_000)
    milliers, n = divmod(n, 1_000)
    if milliards:
        parts.append(f"{_moins_de_mille(milliards)} milliard" + ("s" if milliards > 1 else ""))
    if millions:
        parts.append(f"{_moins_de_mille(millions)} million" + ("s" if millions > 1 else ""))
    if milliers:
        parts.append("mille" if milliers == 1 else f"{_moins_de_mille(milliers)} mille")
    if n:
        parts.append(_moins_de_mille(n))
    return " ".join(parts)

def montant_en_lettres(montant):
    montant = float(montant or 0)
    diagnostic = "Montant en lettres indisponible : consulter le montant chiffré."
    if not math.isfinite(montant):
        return diagnostic
    dirhams = int(montant)
    centimes = int(round((montant - dirhams) * 100))
    if centimes == 100:
        dirhams += 1; centimes = 0
    # Le convertisseur traite au plus 999 milliards. Cette capacité de texte
    # ne limite pas les montants du document et ne remplace aucun chiffre.
    if dirhams < 0 or dirhams >= 1_000_000_000_000:
        return diagnostic
    txt = f"{_entier_en_lettres(dirhams)} dirham" + ("s" if dirhams > 1 else "")
    if centimes:
        txt += f" et {_entier_en_lettres(centimes)} centime" + ("s" if centimes > 1 else "")
    return txt

# ── Helpers ────────────────────────────────────────────────────────────────────
def fmt_mad(v):
    return f"{float(v or 0):,.2f}".replace(",", " ").replace(".", ",")

def fmt_date(d):
    if not d:
        return "-"
    return f"{d.day:02d}/{d.month:02d}/{d.year}"

def _txt(v):
    return escape(str(v if v not in (None, "") else ""))

def _logo_flowable(societe):
    return logo_pdf(societe)

def _pied_de_page(societe):
    morceaux = []
    nom = getattr(societe, "raison_sociale", "") if societe else ""
    fj = getattr(societe, "forme_juridique", None) if societe else None
    cap = getattr(societe, "capital_social", None) if societe else None
    entete = nom
    if fj: entete += f" - {fj}"
    if cap: entete += f" au capital de {fmt_mad(cap)} MAD"
    if entete: morceaux.append(entete)
    ids = []
    if societe:
        if getattr(societe, "ice", None): ids.append(f"ICE : {societe.ice}")
        if getattr(societe, "identifiant_fiscal", None): ids.append(f"IF : {societe.identifiant_fiscal}")
        if getattr(societe, "rc", None): ids.append(f"RC : {societe.rc}" + (f" {societe.ville}" if getattr(societe, "ville", None) else ""))
        if getattr(societe, "patente", None): ids.append(f"TP : {societe.patente}")
        if getattr(societe, "cnss_numero", None): ids.append(f"CNSS : {societe.cnss_numero}")
    if ids: morceaux.append(" | ".join(ids))
    coords = []
    if societe:
        adr = " ".join(x for x in [getattr(societe, "adresse", None), getattr(societe, "ville", None), getattr(societe, "pays", None)] if x)
        if adr: coords.append(adr)
        if getattr(societe, "telephone", None): coords.append(f"Tél : {societe.telephone}")
        if getattr(societe, "email", None): coords.append(societe.email)
        if getattr(societe, "site_web", None): coords.append(societe.site_web)
    if coords: morceaux.append(" | ".join(coords))
    return morceaux

def _tiers_dict(tiers, tiers_infos=None):
    if tiers_infos:
        d = dict(tiers_infos)
        d.setdefault("nom", tiers if isinstance(tiers, str) else "")
        return d
    if isinstance(tiers, dict):
        return dict(tiers)
    return {"nom": tiers or ""}

def _bloc_tiers(tiers, label):
    d = tiers
    elems = [Paragraph(_txt(label), S_LABEL), Paragraph(f"<b>{_txt(d.get('nom') or '-')}</b>", S_SOC)]
    adresse = " ".join(x for x in [d.get("adresse"), d.get("ville")] if x)
    if adresse: elems.append(Paragraph(_txt(adresse), S_GRIS))
    ids = []
    if d.get("ice"): ids.append(f"ICE : {d['ice']}")
    if d.get("if"): ids.append(f"IF : {d['if']}")
    if d.get("rc"): ids.append(f"RC : {d['rc']}")
    if ids: elems.append(Paragraph(_txt(" | ".join(ids)), S_GRIS))
    contacts = []
    if d.get("telephone"): contacts.append(f"Tél : {d['telephone']}")
    if d.get("email"): contacts.append(d["email"])
    if contacts: elems.append(Paragraph(_txt(" | ".join(contacts)), S_GRIS))
    return elems

def _reduction_ligne(l):
    parts = []
    if float(l.get("remise") or 0): parts.append(f"R1 {float(l['remise']):g}%")
    if float(l.get("remise2") or 0): parts.append(f"R2 {float(l['remise2']):g}%")
    if float(l.get("rabais") or 0): parts.append(f"Rab. {fmt_mad(l['rabais'])}/u")
    return "<br/>".join(parts) if parts else "-"

def _tva_ligne(l):
    q = (l.get("qualification_tva") or "taxable").strip().lower()
    if q == "taxable":
        return f"{float(l.get('tva') or 0):g}%"
    return QUALIF_COURT.get(q, q)

def _resume_tva_table(resume_tva):
    if not resume_tva:
        return None
    data = [["Traitement TVA", "Base HT", "TVA"]]
    for r in resume_tva:
        data.append([
            Paragraph(_txt(r.get("label") or "TVA"), S_CELL),
            Paragraph(fmt_mad(r.get("base")), S_CELL_D),
            Paragraph(fmt_mad(r.get("tva")), S_CELL_D),
        ])
    t = Table(data, colWidths=[39 * mm, 23 * mm, 22 * mm], hAlign="LEFT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), FOND),
        ("TEXTCOLOR", (0,0), (-1,0), GRIS),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 7.2),
        ("ALIGN", (1,0), (-1,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), .35, LIGNE),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def _echeancier_table(echeancier):
    if not echeancier or len(echeancier) <= 1:
        return None
    data = [["#", "Échéance", "Libellé", "Montant"]]
    for i, e in enumerate(echeancier, start=1):
        data.append([
            str(e.get("ordre") or i),
            fmt_date(e.get("date_echeance")),
            Paragraph(_txt(e.get("libelle") or f"Échéance {i}"), S_CELL),
            Paragraph(f"{fmt_mad(e.get('montant'))} MAD", S_CELL_D),
        ])
    t = Table(data, colWidths=[10*mm, 28*mm, 58*mm, 34*mm], hAlign="RIGHT", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLEU_C),
        ("TEXTCOLOR", (0,0), (-1,0), BLEU),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 7.4),
        ("ALIGN", (0,0), (1,-1), "CENTER"),
        ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ("GRID", (0,0), (-1,-1), .35, LIGNE),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    return t


def generer_document(societe, *, titre, numero, date_doc, tiers, label_tiers,
                     meta=None, lignes=None, colonnes="prix", totaux=None,
                     mention_lettres=None, rib=False, notes=None, exemplaire=None,
                     exemplaires=None, tiers_infos=None, resume_tva=None,
                     echeancier=None, conditions=None, mentions=None,
                     signature_labels=None, libelles_livraison=None, statut=None,
                     objet=None):
    """Construit un document commercial A4 professionnel et retourne les bytes.

    API compatible avec l'ancien générateur ; FACT.9 ajoute identité détaillée du
    tiers, synthèse TVA, échéancier, conditions de paiement et signatures.
    """
    buf = BytesIO()
    pied = _pied_de_page(societe)
    def on_page(canv, doc):
        canv.saveState()
        canv.setStrokeColor(LIGNE); canv.setLineWidth(0.5)
        y = 17 * mm
        canv.line(15 * mm, y + 3 * mm, A4[0] - 15 * mm, y + 3 * mm)
        canv.setFillColor(GRIS)
        for i, ligne in enumerate(pied[:3]):
            canv.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 6.6)
            canv.drawCentredString(A4[0] / 2, y - i * 3.3 * mm, str(ligne)[:180])
        canv.setFont("Helvetica", 6.5)
        canv.drawRightString(A4[0] - 15 * mm, 5.5 * mm, f"Page {doc.page}")
        canv.restoreState()

    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
        topMargin=13*mm, bottomMargin=30*mm,
        title=f"{titre} {numero}", author=getattr(societe, "raison_sociale", "HisabPro") if societe else "HisabPro",
    )
    liste_exemplaires = exemplaires if exemplaires else [exemplaire]
    story = []
    for idx_ex, ex in enumerate(liste_exemplaires):
        if idx_ex > 0: story.append(PageBreak())
        story.extend(_construire_story(
            societe, titre=titre, numero=numero, date_doc=date_doc, tiers=_tiers_dict(tiers, tiers_infos),
            label_tiers=label_tiers, meta=meta, lignes=lignes, colonnes=colonnes,
            totaux=totaux, mention_lettres=mention_lettres, rib=rib, notes=notes,
            exemplaire=ex, resume_tva=resume_tva, echeancier=echeancier,
            conditions=conditions, mentions=mentions, signature_labels=signature_labels,
            libelles_livraison=libelles_livraison, statut=statut, objet=objet,
        ))
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()


def _construire_story(societe, *, titre, numero, date_doc, tiers, label_tiers,
                      meta, lignes, colonnes, totaux, mention_lettres, rib,
                      notes, exemplaire, resume_tva, echeancier, conditions,
                      mentions, signature_labels, libelles_livraison, statut, objet):
    story = []

    # En-tête société + document
    logo = _logo_flowable(societe)
    soc_txt = [Paragraph(_txt(getattr(societe, "raison_sociale", "") if societe else ""), S_SOC)]
    if societe:
        adr = " ".join(x for x in [getattr(societe, "adresse", None), getattr(societe, "ville", None)] if x)
        if adr: soc_txt.append(Paragraph(_txt(adr), S_GRIS))
        contacts = " | ".join(x for x in [getattr(societe, "telephone", None), getattr(societe, "email", None)] if x)
        if contacts: soc_txt.append(Paragraph(_txt(contacts), S_GRIS))
    gauche = Table([[logo if logo else "", soc_txt]], colWidths=[30*mm if logo else 0, 66*mm if logo else 96*mm]) if logo else soc_txt
    if logo:
        gauche.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 4)]))

    droite = [Paragraph(_txt(titre), ParagraphStyle("docTitle", parent=S_TITRE, alignment=TA_RIGHT))]
    droite.append(Paragraph(f"N° <b>{_txt(numero or '-')}</b>", ParagraphStyle("num", parent=S_NORMAL, alignment=TA_RIGHT, fontSize=10)))
    if statut:
        droite.append(Paragraph(_txt(statut), ParagraphStyle("status", parent=S_EXEMPL, alignment=TA_RIGHT, textColor=BLEU)))
    if exemplaire: droite.append(Paragraph(_txt(exemplaire), S_EXEMPL))
    entete = Table([[gauche, droite]], colWidths=[96*mm, 84*mm])
    entete.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("ALIGN", (1,0), (1,0), "RIGHT"), ("LEFTPADDING", (0,0), (-1,-1), 0), ("RIGHTPADDING", (0,0), (-1,-1), 0)]))
    story += [entete, Spacer(1, 5*mm)]

    if objet:
        story.append(Table([[Paragraph(f"<b>Objet :</b> {_txt(objet)}", S_NORMAL)]], colWidths=[180*mm], style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), BLEU_C), ("BOX", (0,0), (-1,-1), .4, colors.HexColor("#B7D7EF")),
            ("LEFTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ])))
        story.append(Spacer(1, 4*mm))

    # Tiers + métadonnées
    bloc_tiers = _bloc_tiers(tiers, label_tiers)
    bloc_meta = []
    for label, valeur in [("Date", fmt_date(date_doc))] + (meta or []):
        bloc_meta.append(Paragraph(f"<font color='#667085' size='7.5'><b>{_txt(label)}</b></font>&nbsp;&nbsp;{_txt(valeur)}", ParagraphStyle("m", parent=S_NORMAL, alignment=TA_RIGHT)))
    t = Table([[bloc_tiers, bloc_meta]], colWidths=[102*mm, 78*mm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("BACKGROUND", (0,0), (0,0), FOND), ("BOX", (0,0), (-1,-1), .4, LIGNE), ("LEFTPADDING", (0,0), (-1,-1), 8), ("RIGHTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
    story += [t, Spacer(1, 5*mm)]

    # Lignes
    if colonnes == "prix":
        headers = ["Désignation", "Qté", "P.U. HT", "Réductions", "TVA", "Total HT"]
        widths = [68*mm, 13*mm, 25*mm, 24*mm, 18*mm, 32*mm]
        data = [headers]
        for l in (lignes or []):
            data.append([
                Paragraph(_txt(l.get("description") or ""), S_CELL),
                Paragraph(f"{float(l.get('quantite') or 0):g}", ParagraphStyle("c", parent=S_CELL, alignment=TA_CENTER)),
                Paragraph(fmt_mad(l.get("prix_unitaire")), S_CELL_D),
                Paragraph(_reduction_ligne(l), ParagraphStyle("red", parent=S_CELL, alignment=TA_CENTER, fontSize=7.2)),
                Paragraph(_txt(_tva_ligne(l)), ParagraphStyle("tvac", parent=S_CELL, alignment=TA_CENTER, fontSize=7.3)),
                Paragraph(fmt_mad(l.get("total_ht")), S_CELL_D),
            ])
    else:
        l1, l2 = libelles_livraison or ("Qté prévue", "Qté livrée")
        headers = ["Désignation", l1, l2]
        widths = [110*mm, 35*mm, 35*mm]
        data = [headers]
        for l in (lignes or []):
            data.append([
                Paragraph(_txt(l.get("description") or ""), S_CELL),
                Paragraph(f"{float(l.get('quantite_prevue') or 0):g}", ParagraphStyle("lc1", parent=S_CELL, alignment=TA_CENTER)),
                Paragraph(f"{float(l.get('quantite_livree') or 0):g}", ParagraphStyle("lc2", parent=S_CELL, alignment=TA_CENTER)),
            ])
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), FONCE), ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("FONTSIZE", (0,0), (-1,0), 7.8),
        ("ALIGN", (1,0), (-1,0), "CENTER"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("LINEBELOW", (0,1), (-1,-1), .35, LIGNE), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#FCFCFD")]),
    ]))
    story += [table, Spacer(1, 4*mm)]

    # Totaux + TVA : côte à côte si possible
    resume_table = _resume_tva_table(resume_tva)
    total_table = None
    if totaux:
        rows=[]; styles_tot=[("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),3.4),("BOTTOMPADDING",(0,0),(-1,-1),3.4)]
        for i,(label,valeur,gras) in enumerate(totaux):
            sl=ParagraphStyle(f"tl{i}", parent=S_CELL, fontName="Helvetica-Bold" if gras else "Helvetica", fontSize=9 if gras else 8)
            sv=ParagraphStyle(f"tv{i}", parent=sl, alignment=TA_RIGHT)
            rows.append([Paragraph(_txt(label), sl), Paragraph(f"{fmt_mad(valeur)} MAD", sv)])
            if gras:
                styles_tot += [("BACKGROUND",(0,i),(-1,i),FOND),("LINEABOVE",(0,i),(-1,i),.7,FONCE)]
        total_table=Table(rows,colWidths=[48*mm,42*mm],hAlign="RIGHT"); total_table.setStyle(TableStyle(styles_tot))
    if resume_table and total_table:
        duo=Table([[resume_table,total_table]], colWidths=[86*mm,94*mm])
        duo.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),0),("RIGHTPADDING",(0,0),(-1,-1),0)]))
        story.append(duo)
    elif total_table: story.append(total_table)
    elif resume_table: story.append(resume_table)
    if resume_table or total_table: story.append(Spacer(1,4*mm))

    if mention_lettres is not None:
        story.append(KeepTogether(Paragraph(f"Arrêté le présent document à la somme de : <b>{_txt(montant_en_lettres(mention_lettres))}</b>.", S_LETTRES)))
        story.append(Spacer(1, 3*mm))

    echeance_table = _echeancier_table(echeancier)
    if echeance_table:
        story += [Paragraph("ÉCHÉANCIER DE PAIEMENT", S_LABEL), Spacer(1, 1.5*mm), echeance_table, Spacer(1, 3*mm)]
    if conditions:
        story.append(Paragraph(f"<b>Conditions de règlement :</b> {_txt(conditions)}", S_GRIS))
        story.append(Spacer(1, 2*mm))
    if rib and societe and (getattr(societe, "rib", None) or getattr(societe, "banque", None)):
        infos = " - ".join(x for x in [f"Banque : {societe.banque}" if getattr(societe,'banque',None) else None, f"Agence : {societe.agence}" if getattr(societe,'agence',None) else None, f"RIB : {societe.rib}" if getattr(societe,'rib',None) else None] if x)
        story.append(Paragraph(f"<b>Règlement par virement :</b> {_txt(infos)}", S_GRIS)); story.append(Spacer(1,2*mm))

    for m in mentions or []:
        if m: story.append(Paragraph(f"• {_txt(m)}", S_GRIS))
    if mentions: story.append(Spacer(1, 2*mm))
    if notes:
        story.append(Paragraph(f"<b>Notes :</b> {_txt(notes)}", S_GRIS)); story.append(Spacer(1, 2*mm))

    if signature_labels:
        a,b=signature_labels
        sig=Table([[Paragraph(_txt(a), S_LABEL), Paragraph(_txt(b), S_LABEL)], ["",""]], colWidths=[88*mm,88*mm], rowHeights=[8*mm,18*mm])
        sig.setStyle(TableStyle([("BOX",(0,0),(0,-1),.4,LIGNE),("BOX",(1,0),(1,-1),.4,LIGNE),("VALIGN",(0,0),(-1,-1),"TOP"),("LEFTPADDING",(0,0),(-1,-1),7),("TOPPADDING",(0,0),(-1,-1),6)]))
        story += [Spacer(1,3*mm), KeepTogether(sig)]
    return story

# ─── États financiers (Bilan, CPC, ESG...) — rendu générique ──────────────────
def generer_etat_financier(societe, *, titre, sous_titre=None, exercice,
                           colonnes, lignes, periode_debut=None, periode_fin=None,
                           logiciel_version=None, paysage=False):
    """
    Rend un état financier tabulaire en PDF.
    - colonnes : liste d'en-têtes de colonnes numériques (ex: ["Brut", "Amort.", "Net"]
      ou ["Montant"])
    - lignes : liste de dicts {type: 'titre'|'ligne'|'total', label, valeurs: [floats],
      niveau: int (indentation), numero: str optionnel (rubrique CPC)}
    Les montants négatifs sont rendus entre parenthèses.
    """
    buf = BytesIO()
    taille_page = landscape(A4) if paysage else A4
    pied = _pied_de_page(societe)
    version = str(logiciel_version or HISABPRO_VERSION)
    date_edition = datetime.now().strftime("%d/%m/%Y %H:%M")
    periode = ""
    if periode_debut or periode_fin:
        periode = f"Période : {periode_debut or '—'} au {periode_fin or '—'}"

    def on_page(canv, doc):
        canv.saveState()
        canv.setStrokeColor(LIGNE)
        canv.setLineWidth(0.5)
        y = 16 * mm
        canv.line(15 * mm, y + 3.5 * mm, taille_page[0] - 15 * mm, y + 3.5 * mm)
        canv.setFillColor(GRIS)
        for i, ligne in enumerate(pied[:3]):
            canv.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 6.8)
            canv.drawCentredString(taille_page[0] / 2, y - i * 3.4 * mm, ligne)
        canv.setFont("Helvetica", 6.6)
        canv.drawString(15 * mm, 6 * mm, f"Édité le {date_edition} — HisabPro v{version}")
        canv.drawRightString(taille_page[0] - 15 * mm, 6 * mm, f"Page {doc.page}")
        canv.restoreState()

    doc = SimpleDocTemplate(
        buf, pagesize=taille_page,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=30 * mm,
        title=f"{titre} — Exercice {exercice}",
    )
    story = []

    # En-tête : société + titre de l'état
    ajouter_logo_pdf(story, societe)
    soc_lines = [Paragraph(_txt(societe.raison_sociale if societe else ""), S_SOC)]
    if societe:
        sous = " ".join(x for x in [societe.adresse, societe.ville] if x)
        if sous: soc_lines.append(Paragraph(_txt(sous), S_GRIS))
    droite = [
        Paragraph(_txt(titre), ParagraphStyle("t", parent=S_TITRE, fontSize=14, alignment=TA_RIGHT)),
        Paragraph(f"Exercice {exercice}", ParagraphStyle("e", parent=S_NORMAL, alignment=TA_RIGHT, fontSize=9.5)),
    ]
    if periode:
        droite.append(Paragraph(_txt(periode), ParagraphStyle("p", parent=S_GRIS, alignment=TA_RIGHT)))
    if sous_titre:
        droite.append(Paragraph(_txt(sous_titre), ParagraphStyle("st", parent=S_GRIS, alignment=TA_RIGHT)))
    entete = Table([[soc_lines, droite]], colWidths=[95 * mm, 85 * mm])
    entete.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(entete)
    story.append(Spacer(1, 6 * mm))

    def fmt_val(v):
        if v is None or abs(v) < 0.005:
            return "—"
        return f"({fmt_mad(-v)})" if v < 0 else fmt_mad(v)

    # Largeurs : libellé flexible + colonnes numériques
    nb_num = len(colonnes)
    largeur_num = (24 * mm if nb_num == 4 and not paysage else
                   ((31 if paysage else 30) * mm if nb_num >= 3 else 38 * mm))
    largeur_label = (taille_page[0] - 30 * mm) - nb_num * largeur_num
    widths = [largeur_label] + [largeur_num] * nb_num

    entete_num = ParagraphStyle('entete_num', parent=S_CELL, fontName='Helvetica-Bold',
                                fontSize=7.2, leading=8.5, alignment=TA_RIGHT,
                                textColor=colors.white)
    data = [[""] + [Paragraph(_txt(col), entete_num) for col in colonnes]]  # en-tête
    styles_t = [
        ("BACKGROUND",    (0, 0), (-1, 0), FONCE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 8),
        ("ALIGN",         (1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]

    for idx, l in enumerate(lignes, start=1):
        typ = l.get("type", "ligne")
        label = l.get("label", "")
        numero = l.get("numero")
        niveau = l.get("niveau", 0)
        if numero:
            label = f"{numero} — {label}"
        label = _txt(label)
        if typ == "titre":
            data.append([Paragraph(f"<b>{label}</b>",
                ParagraphStyle("ti", parent=S_CELL, fontSize=8, textColor=GRIS))] + [""] * nb_num)
            styles_t.append(("BACKGROUND", (0, idx), (-1, idx), FOND))
            styles_t.append(("TOPPADDING", (0, idx), (-1, idx), 6))
        else:
            gras = typ in ("total", "rubrique")
            style_lbl = ParagraphStyle("l", parent=S_CELL,
                fontName="Helvetica-Bold" if gras else "Helvetica",
                leftIndent=niveau * 10, fontSize=7 if typ == "detail" else 8.2)
            style_num = ParagraphStyle("n", parent=style_lbl, alignment=TA_RIGHT, leftIndent=0)
            valeurs = l.get("valeurs", [])
            cellules = [Paragraph(label, style_lbl)]
            for v in valeurs[:nb_num]:
                txt = fmt_val(v)
                couleur = " color='#A32D2D'" if (v is not None and v < 0) else ""
                cellules.append(Paragraph(f"<font{couleur}>{txt}</font>", style_num))
            while len(cellules) < nb_num + 1:
                cellules.append("")
            data.append(cellules)
            if typ == "total":
                styles_t.append(("LINEABOVE", (0, idx), (-1, idx), 0.6, FONCE))
            elif typ == "rubrique":
                styles_t.append(("BACKGROUND", (0, idx), (-1, idx), FOND))
            else:
                styles_t.append(("LINEBELOW", (0, idx), (-1, idx), 0.3, LIGNE))

    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle(styles_t))
    story.append(table)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buf.getvalue()
