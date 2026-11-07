# -*- coding: utf-8 -*-
"""Rendu PDF du Livre d'inventaire à partir d'un snapshot figé."""
from io import BytesIO
import math
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak


def _mad(v):
    try:
        if v is None or isinstance(v, bool) or not math.isfinite(float(v)):
            return "À vérifier"
        return f"{float(v):,.2f}".replace(",", " ").replace(".", ",")
    except (TypeError, ValueError, OverflowError):
        return "À vérifier"


def _quantite(v):
    try:
        if v is None or isinstance(v, bool) or not math.isfinite(float(v)):
            return "À vérifier"
        return f"{float(v):g}"
    except (TypeError, ValueError, OverflowError):
        return "À vérifier"




def _date_fr(value):
    if not value:
        return "—"
    raw = str(value)[:10]
    parts = raw.split("-")
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return str(value)


def _datetime_fr(value):
    if not value:
        return "—"
    raw = str(value)
    date_part = _date_fr(raw[:10])
    time_part = ""
    if "T" in raw:
        time_part = raw.split("T", 1)[1][:5]
    elif " " in raw:
        time_part = raw.split(" ", 1)[1][:5]
    return f"{date_part}{(' ' + time_part) if time_part else ''}"


def _statut_fr(value):
    return {
        "cloture": "Clôturé",
        "ouvert": "Ouvert",
        "a_venir": "À venir",
        "prepare": "Préparé",
    }.get(value, value or "—")

def _table(rows, widths=None, repeat=1):
    t = Table(rows, colWidths=widths, repeatRows=repeat)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E2A3A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.2),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8DDE5")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def generer_livre_inventaire_pdf(societe, snapshot: dict, archive_meta: dict | None = None) -> bytes:
    from services.logo_export_service import ajouter_logo_pdf
    buf = BytesIO()
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1x", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, textColor=colors.HexColor("#1E2A3A"))
    h2 = ParagraphStyle("h2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11, textColor=colors.HexColor("#1E2A3A"), spaceBefore=8, spaceAfter=5)
    normal = ParagraphStyle("nx", parent=styles["BodyText"], fontSize=8.5, leading=11)
    small = ParagraphStyle("sx", parent=normal, fontSize=7.4, textColor=colors.HexColor("#6B7280"))
    right = ParagraphStyle("rx", parent=normal, alignment=TA_RIGHT)
    center = ParagraphStyle("cx", parent=normal, alignment=TA_CENTER)

    ex = snapshot["exercice"]
    title = f"Livre d'inventaire — Exercice {ex['annee']}"
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14*mm, rightMargin=14*mm, topMargin=14*mm, bottomMargin=18*mm, title=title)

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 6.8)
        canvas.setFillColor(colors.HexColor("#6B7280"))
        canvas.drawString(14*mm, 8*mm, f"HisabPro — {getattr(societe, 'raison_sociale', '')}")
        canvas.drawRightString(A4[0]-14*mm, 8*mm, f"Page {doc_.page}")
        canvas.restoreState()

    story = [Paragraph(title, h1), Spacer(1, 3*mm)]
    ajouter_logo_pdf(story, societe)
    story.append(Paragraph(escape(str(getattr(societe, "raison_sociale", "") or "")), ParagraphStyle("soc", parent=normal, fontName="Helvetica-Bold", fontSize=10)))
    story.append(Paragraph(
        f"Période : {_date_fr(ex['date_debut'])} au {_date_fr(ex['date_fin'])} — Statut : {_statut_fr(ex['statut'])}",
        normal,
    ))
    story.append(Paragraph(f"Généré le : {_datetime_fr(snapshot.get('genere_le'))}", small))
    if archive_meta:
        story.append(Paragraph(
            f"Archive v{archive_meta.get('version', snapshot.get('version', '—'))} figée le {_datetime_fr(archive_meta.get('date_etablissement'))} — "
            f"SHA-256 : {archive_meta.get('empreinte_sha256', '—')}",
            small,
        ))
    story.append(Spacer(1, 5*mm))

    ctrl = snapshot.get("controles", {})
    story.append(Paragraph("Contrôles de cohérence", h2))
    controls = [
        ["Contrôle", "État"],
        ["Exercice clôturé", "OK" if ctrl.get("exercice_cloture") else "À finaliser"],
        ["Aucun brouillon", "OK" if ctrl.get("aucun_brouillon") else "À corriger"],
        ["Balance débit/crédit", "OK" if ctrl.get("balance_equilibree") else "Écart"],
        ["Bilan équilibré", "OK" if ctrl.get("bilan_equilibre") else "Écart"],
        ["Inventaire physique de stock", "OK" if ctrl.get("inventaire_stock_valide") else "À valider"],
        ["Stock physique / comptabilité", "OK" if ctrl.get("stock_rapproche") else "Écart à analyser"],
        ["Immobilisations / comptabilité", "OK" if ctrl.get("immobilisations_rapprochees") else "Écart à analyser"],
    ]
    story.append(_table(controls, [105*mm, 65*mm]))

    bilan = snapshot["bilan"]
    story.append(Paragraph("Bilan synthétique", h2))
    rows = [["Rubrique", "Montant net (MAD)"]]
    for key, label in [("actif_immobilise", "Actif immobilisé"), ("actif_circulant", "Actif circulant"), ("tresorerie_actif", "Trésorerie-actif")]:
        total = sum(float(x.get("net", 0)) for x in bilan.get(key, []))
        rows.append([label, _mad(total)])
    total_tresorerie_passif = sum(float(x.get("montant", 0)) for x in bilan.get("tresorerie_passif", []))
    rows += [
        ["Trésorerie-passif", _mad(total_tresorerie_passif)],
        ["TOTAL ACTIF", _mad(bilan.get("total_actif"))],
        ["TOTAL PASSIF", _mad(bilan.get("total_passif"))],
    ]
    story.append(_table(rows, [115*mm, 55*mm]))

    cpc = snapshot["cpc"]
    story.append(Paragraph("Compte de produits et charges — synthèse", h2))
    rows = [["Rubrique", "Montant (MAD)"],
            ["Produits d'exploitation", _mad(cpc.get("total_produits_exploitation"))],
            ["Charges d'exploitation", _mad(cpc.get("total_charges_exploitation"))],
            ["Résultat d'exploitation", _mad(cpc.get("resultat_exploitation"))],
            ["Résultat financier", _mad(cpc.get("resultat_financier"))],
            ["Résultat non courant", _mad(cpc.get("resultat_non_courant"))],
            ["Impôt sur les résultats", _mad(cpc.get("impot_resultat"))],
            ["RÉSULTAT NET", _mad(cpc.get("resultat_net"))]]
    story.append(_table(rows, [115*mm, 55*mm]))

    story.append(PageBreak())
    story.append(Paragraph("Inventaire des stocks", h2))
    st = snapshot.get("stocks", {})
    if st.get("valorisation_complete") is False:
        story.append(Paragraph("Valorisation du stock à vérifier : des quantités ou des coûts sont inconnus. Le total physique et son rapprochement ne sont pas déterminables.", normal))
        for diagnostic in st.get("diagnostics", []):
            story.append(Paragraph(escape(f"{diagnostic.get('code') or diagnostic.get('article_id') or 'Stock'} : {diagnostic.get('message') or 'Valeur à vérifier'}"), small))
    rows = [["Code", "Désignation", "Qté", "CMUP", "Valeur"]]
    for x in st.get("lignes", []):
        rows.append([x.get("code") or "", Paragraph(x.get("designation") or "", small), _quantite(x.get('quantite')), _mad(x.get("cmup")), _mad(x.get("valeur"))])
    if len(rows) == 1:
        rows.append(["—", "Aucun article stockable", "", "", ""])
    story.append(_table(rows, [22*mm, 77*mm, 20*mm, 24*mm, 27*mm]))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Physique brut : {_mad(st.get('valeur_physique'))} MAD — "
        f"Comptable brut : {_mad(st.get('valeur_comptable_brute'))} MAD — "
        f"Dépréciations : {_mad(st.get('depreciations'))} MAD — "
        f"Comptable net : {_mad(st.get('valeur_comptable_nette'))} MAD — "
        f"Écart brut : {_mad(st.get('ecart_physique_comptable'))} MAD", small))

    story.append(Paragraph("Inventaire des immobilisations", h2))
    im = snapshot.get("immobilisations", {})
    rows = [["Réf.", "Désignation", "Compte", "Brut", "Amort. cumulés", "VNC"]]
    for x in im.get("lignes", []):
        rows.append([x.get("reference") or "—", Paragraph(x.get("designation") or "", small), x.get("compte_immo") or "", _mad(x.get("valeur_brute")), _mad(x.get("amortissements_cumules")), _mad(x.get("vnc"))])
    if len(rows) == 1:
        rows.append(["—", "Aucune immobilisation", "", "", "", ""])
    story.append(_table(rows, [20*mm, 57*mm, 18*mm, 25*mm, 27*mm, 23*mm]))
    rap = im.get("rapprochement", {})
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        f"Rapprochement immobilisations : registre brut {_mad(rap.get('brut_module'))} MAD / "
        f"comptabilité {_mad(rap.get('brut_comptable'))} MAD — amortissements registre "
        f"{_mad(rap.get('amortissements_module'))} MAD / comptabilité {_mad(rap.get('amortissements_comptables'))} MAD — "
        f"VNC registre {_mad(rap.get('vnc_module'))} MAD / comptabilité {_mad(rap.get('vnc_comptable'))} MAD.",
        small,
    ))
    ecarts_immos = [x for x in rap.get("details_comptes", []) if abs(float(x.get("ecart", 0) or 0)) > 0.009]
    if ecarts_immos:
        rows_rap = [["Nature", "Compte", "Registre", "Comptabilité", "Écart"]]
        for x in ecarts_immos:
            rows_rap.append([
                "Brut" if x.get("nature") == "brut" else "Amort.",
                x.get("compte") or "",
                _mad(x.get("module")),
                _mad(x.get("comptable")),
                _mad(x.get("ecart")),
            ])
        story.append(Spacer(1, 2*mm))
        story.append(_table(rows_rap, [28*mm, 25*mm, 39*mm, 39*mm, 39*mm]))

    story.append(Paragraph("Écritures d'inventaire / cut-off", h2))
    rows = [["Type", "Libellé", "Comptes", "Montant"]]
    for x in snapshot.get("ajustements_inventaire", []):
        rows.append([x.get("type") or "", Paragraph(x.get("libelle") or "", small), f"{x.get('compte_activite')} / {x.get('compte_contrepartie')}", _mad(x.get("montant"))])
    if len(rows) == 1:
        rows.append(["—", "Aucun ajustement", "", ""])
    story.append(_table(rows, [26*mm, 82*mm, 34*mm, 28*mm]))

    story.append(PageBreak())
    story.append(Paragraph("Balance des comptes de bilan à la clôture", h2))
    rows = [["Compte", "Débit", "Crédit", "Sens"]]
    for x in snapshot.get("comptabilite", {}).get("balance_comptes_bilan", []):
        rows.append([x.get("compte"), _mad(x.get("debit")), _mad(x.get("credit")), x.get("sens")])
    story.append(_table(rows, [40*mm, 50*mm, 50*mm, 30*mm]))

    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Note : ce document constitue l'archive numérique interne générée par HisabPro. Les formalités externes de conservation, cotation ou paraphe applicables à l'entreprise restent à accomplir selon son régime juridique.", small))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()
