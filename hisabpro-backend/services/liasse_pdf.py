# -*- coding: utf-8 -*-
"""Export PDF de contrôle de la liasse fiscale HisabPro (Patch 09.3)."""
from io import BytesIO
from xml.sax.saxutils import escape
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from services.liasse_presentation import numero_tableau, reference_etic, NOTE_NUMEROTATION
from services.logo_export_service import ajouter_logo_pdf


def _f(v):
    try: return f"{float(v):,.2f}".replace(","," ")
    except Exception: return "-"


def _p(v, style): return Paragraph(escape(str(v if v not in (None,"") else "-")),style)


def generer_liasse_pdf(data):
    buf=BytesIO(); doc=SimpleDocTemplate(buf,pagesize=landscape(A4),rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=18*mm)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name="HPTitle",parent=styles["Title"],fontName="Helvetica-Bold",fontSize=16,leading=19,alignment=TA_CENTER,spaceAfter=8))
    styles.add(ParagraphStyle(name="HPH2",parent=styles["Heading2"],fontName="Helvetica-Bold",fontSize=11,leading=14,spaceBefore=5,spaceAfter=5))
    styles.add(ParagraphStyle(name="HPSmall",parent=styles["BodyText"],fontSize=7.5,leading=9))
    styles.add(ParagraphStyle(name="HPNum",parent=styles["HPSmall"],alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name="HPDetail",parent=styles["HPSmall"],leftIndent=10))
    story=[]; soc=data.get("societe",{}); ex=data.get("exercice")
    version=os.getenv("HISABPRO_VERSION","0.1.0"); edition=datetime.now().strftime("%d/%m/%Y %H:%M")
    periode=data.get("exercice_comptable",{}) or {}

    def on_page(canv, doc_obj):
        canv.saveState(); w,h=landscape(A4)
        canv.setStrokeColor(colors.lightgrey); canv.setLineWidth(0.3); canv.line(12*mm,10*mm,w-12*mm,10*mm)
        canv.setFont("Helvetica",6.5); canv.setFillColor(colors.grey)
        canv.drawString(12*mm,5.5*mm,f"{soc.get('raison_sociale','')} — Exercice {ex} — {periode.get('date_debut','')} au {periode.get('date_fin','')}")
        canv.drawCentredString(w/2,5.5*mm,f"Édité le {edition} — HisabPro v{version}")
        canv.drawRightString(w-12*mm,5.5*mm,f"Page {doc_obj.page}")
        canv.restoreState()
    story += [Paragraph("LIASSE FISCALE - DOSSIER DE CONTROLE HISABPRO",styles["HPTitle"]),_p(f"{soc.get('raison_sociale','')} - Exercice {ex}",styles["Heading2"])]
    ajouter_logo_pdf(story, soc)
    story.append(_p(NOTE_NUMEROTATION, styles["HPSmall"]))
    info=[["IF",soc.get("identifiant_fiscal") or "-","ICE",soc.get("ice") or "-","RC",soc.get("rc") or "-"],["Période",f"{data.get('exercice_comptable',{}).get('date_debut','')} au {data.get('exercice_comptable',{}).get('date_fin','')}","Statut",data.get("statut",""),"Devise",soc.get("devise","MAD")]]
    t=Table(info,colWidths=[22*mm,48*mm,22*mm,48*mm,22*mm,48*mm]); t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.grey),("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),("BACKGROUND",(2,0),(2,-1),colors.whitesmoke),("BACKGROUND",(4,0),(4,-1),colors.whitesmoke),("FONTSIZE",(0,0),(-1,-1),8),("VALIGN",(0,0),(-1,-1),"MIDDLE") ])); story += [t,Spacer(1,5*mm)]
    controls=data.get("controles",{}); story.append(Paragraph("Contrôles de finalisation",styles["HPH2"])); rows=[["État","Contrôle","Détail"]]
    for c in controls.get("items",[]): rows.append(["OK" if c.get("ok") else ("BLOQUANT" if c.get("bloquant") else "ALERTE"),_p(c.get("libelle"),styles["HPSmall"]),_p(c.get("details"),styles["HPSmall"])])
    tb=Table(rows,colWidths=[25*mm,95*mm,135*mm],repeatRows=1); tb.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAECEF")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7.5),("VALIGN",(0,0),(-1,-1),"TOP") ])); story += [tb,PageBreak()]

    def money_table(title, headers, rows, widths=None):
        story.append(Paragraph(title,styles["HPH2"])); data_rows=[[ _p(h,styles["HPSmall"]) for h in headers]]+rows
        tab=Table(data_rows,colWidths=widths,repeatRows=1); tab.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAECEF")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP"),("ALIGN",(-3,1),(-1,-1),"RIGHT") ])); story.extend([tab,Spacer(1,4*mm)])

    bilan=data.get("etats",{}).get("bilan",{})
    ar=[]
    for sec in ("immobilise","circulant","tresorerie"):
        for r in bilan.get("actif",{}).get(sec,[]): ar.append([r.get("code",""),_p(r.get("libelle"),styles["HPSmall"]),_f(r.get("brut")),_f(r.get("amort_prov")),_f(r.get("net")),_f(r.get("net_n1"))])
    detail=bilan.get("detail",{})
    if detail:
        story.append(_p("Sous-postes pour mémoire : non additionnés aux rubriques. Amortissements et nets non ventilés : -.",styles["HPSmall"]))
    if detail.get("actif"):
        ar=[[r.get("numero",""),_p(r.get("label",""),styles["HPDetail"] if r.get("type")=="detail" else styles["HPSmall"]),
             *([_f(v) for v in r.get("valeurs",[])] if r.get("type")!="titre" else ["","","",""])] for r in detail["actif"]]
    money_table(f"{numero_tableau('BILAN')} - Bilan - Actif",["Réf.","Libellé","Brut N","Amort./Prov.","Net N","Net N-1"],ar,[20*mm,105*mm,30*mm,30*mm,30*mm,30*mm])
    pr=[]
    for sec in ("capitaux_propres","financement_permanent","passif_circulant","tresorerie"):
        for r in bilan.get("passif",{}).get(sec,[]): pr.append([r.get("code",""),_p(r.get("libelle"),styles["HPSmall"]),_f(r.get("montant")),_f(r.get("n1"))])
    if detail.get("passif"):
        pr=[[r.get("numero",""),_p(r.get("label",""),styles["HPSmall"]),
             *([_f(v) for v in r.get("valeurs",[])] if r.get("type")!="titre" else ["",""])] for r in detail["passif"]]
    money_table(f"{numero_tableau('BILAN')} - Bilan - Passif",["Réf.","Libellé","N","N-1"],pr,[25*mm,145*mm,38*mm,38*mm]); story.append(PageBreak())

    cpc=[]
    for r in data.get("etats",{}).get("cpc",{}).get("lignes",[]):
        cpc.append([r.get("code",""),_p(r.get("libelle"),styles["HPSmall"]),"" if r.get("montant") is None else _f(r.get("montant")),"" if r.get("n1") is None else _f(r.get("n1"))])
    money_table(f"{numero_tableau('CPC')} - Compte de Produits et Charges",["Réf.","Libellé","N","N-1"],cpc,[25*mm,145*mm,38*mm,38*mm]); story.append(PageBreak())

    passage=[[ _p(r.get("rubrique"),styles["HPSmall"]),_f(r.get("montant"))] for r in data.get("fiscal",{}).get("passage_resultat_fiscal",[])]
    money_table("Passage du résultat comptable au résultat fiscal",["Rubrique","Montant"],passage,[180*mm,55*mm])
    fisc=data.get("fiscal",{}).get("situation",{}); liq=fisc.get("liquidation",{}) if isinstance(fisc,dict) else {}; cm=fisc.get("cotisation_minimale",{}) if isinstance(fisc,dict) else {}
    fs=[[_p("IS théorique",styles["HPSmall"]),_f(liq.get("is_theorique"))],[_p("Cotisation minimale exigible",styles["HPSmall"]),_f(liq.get("cm_exigible"))],[_p("Impôt dû avant acomptes",styles["HPSmall"]),_f(liq.get("impot_du_avant_acomptes"))],[_p("Solde à payer",styles["HPSmall"]),_f(liq.get("solde_a_payer"))],[_p("Excédent total",styles["HPSmall"]),_f(liq.get("excedent_total"))]]
    money_table("Synthèse IS / CM / liquidation",["Rubrique","Montant"],fs,[180*mm,55*mm]); story.append(PageBreak())

    esg=[[r.get("code",""),_p(r.get("libelle"),styles["HPSmall"]),_f(r.get("montant")),_f(r.get("n1"))] for r in data.get("etats",{}).get("esg",{}).get("lignes",[])]
    money_table("État des Soldes de Gestion",["Réf.","Libellé","N","N-1"],esg,[25*mm,145*mm,38*mm,38*mm])
    tf=data.get("etats",{}).get("tableau_financement",{})
    if tf.get("applicable", True) is False:
        story.append(Paragraph("Tableau de financement", styles["HPH2"]))
        story.append(Paragraph(tf.get("motif_non_applicable") or "Comparatif N-1 indisponible : le tableau de financement ne peut pas être établi.", styles["BodyText"]))
    else:
        tfr=[[ _p(r.get("libelle"),styles["HPSmall"]),_f(r.get("n")),_f(r.get("n1")),_f(r.get("emploi")),_f(r.get("ressource"))] for r in tf.get("synthese",[])]
        money_table("Tableau de financement - Synthèse",["Masse","N","N-1","Emploi","Ressource"],tfr,[115*mm,32*mm,32*mm,32*mm,32*mm])
    story.append(PageBreak())

    story.append(Paragraph("ETIC - État des Informations Complémentaires",styles["HPH2"])); etic=data.get("etic",{}); prog=etic.get("progression",{}); story.append(Paragraph(f"Progression : {prog.get('completes',0)}/{prog.get('total',0)} sections complètes.",styles["BodyText"])); story.append(Spacer(1,3*mm))
    erows=[["Tableau / ETIC","Section","Mode","État"]]
    for s in etic.get("sections",[]): erows.append([reference_etic(s.get("code","")),_p(s.get("titre"),styles["HPSmall"]),s.get("mode",""),"Complet" if s.get("complete") else "À compléter"])
    te=Table(erows,colWidths=[22*mm,150*mm,35*mm,35*mm],repeatRows=1); te.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.25,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAECEF")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),7),("VALIGN",(0,0),(-1,-1),"TOP") ])); story.append(te)

    # Contenu complet ETIC : données automatiques + compléments saisis.
    for sec in etic.get("sections", []):
        story.append(PageBreak())
        story.append(_p(f"{reference_etic(sec.get('code',''))} - ETIC - {sec.get('titre','')}", styles["HPH2"]))
        auto = sec.get("automatique") or {}; cols = auto.get("colonnes") or []; lignes = auto.get("lignes") or []
        if cols and lignes:
            table_rows = [[_p(c, styles["HPSmall"]) for c in cols]]
            for ligne in lignes:
                table_rows.append([_p(ligne.get(c, "-"), styles["HPSmall"]) for c in cols])
            w = 245*mm/max(len(cols),1)
            ta = Table(table_rows, colWidths=[w]*len(cols), repeatRows=1)
            ta.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.2,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAECEF")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),6.5),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story.append(ta)
        elif not lignes:
            story.append(Paragraph("Aucune donnée automatique pour cette section.", styles["HPSmall"]))
        if auto.get("avertissement"):
            story += [Spacer(1,2*mm), Paragraph(f"Contrôle : {auto.get('avertissement')}", styles["HPSmall"])]
        contenu = sec.get("contenu") or {}
        if contenu.get("neant"):
            story += [Spacer(1,2*mm), Paragraph("Complément déclaré : Néant pour l'exercice.", styles["HPSmall"])]
        if contenu.get("texte"):
            story += [Spacer(1,2*mm), _p(contenu.get("texte"), styles["HPSmall"])]
        if contenu.get("notes"):
            story += [Spacer(1,2*mm), _p(f"Notes : {contenu.get('notes')}", styles["HPSmall"])]
        if sec.get("code") in ("B6", "B7") and sec.get("ventilation"):
            echues_label = "Échues non recouvrées" if sec.get("code") == "B6" else "Échues non payées"
            headers = ["Compte", "Intitulé", "Total", "+ 1 an", "- 1 an", echues_label, "Devises", "État / org. publics", "Entreprises liées", "Effets"]
            vrows = [[_p(h, styles["HPSmall"]) for h in headers]]
            for row in sec.get("ventilation") or []:
                vals = [row.get("compte"), row.get("intitule"), row.get("total"), row.get("plus_un_an"), row.get("moins_un_an"), row.get("echues"), row.get("devises"), row.get("etat_organismes_publics"), row.get("entreprises_liees"), row.get("effets")]
                vrows.append([_p("-" if v is None else v, styles["HPSmall"]) for v in vals])
            widths = [18*mm, 55*mm] + [21.5*mm]*8
            tv = Table(vrows, colWidths=widths, repeatRows=1)
            tv.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.2,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAECEF")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),5.6),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story += [Spacer(1,2*mm), tv]
        if sec.get("code") in ("B6", "B7"):
            for erreur in sec.get("erreurs_ventilation") or []:
                story.append(_p(f"Contrôle de ventilation : {erreur}", styles["HPSmall"]))
            for ligne in lignes:
                if ligne.get("echeance_auto_total") is not None:
                    story.append(_p(
                        f"Rapprochement {ligne.get('compte')} : comptabilité {_f(ligne.get('montant'))} MAD ; "
                        f"source factures {_f(ligne.get('echeance_auto_total'))} MAD ; "
                        f"écart {_f(ligne.get('echeance_auto_ecart'))} MAD ; "
                        f"source non qualifiée {_f(ligne.get('echeance_auto_non_qualifie', 0))} MAD.", styles["HPSmall"]
                    ))
                for anomalie in ligne.get("echeance_auto_anomalies_sources") or []:
                    story.append(_p(
                        f"Source à vérifier {anomalie.get('numero') or anomalie.get('facture_id')} : "
                        + " ".join(anomalie.get("motifs") or []), styles["HPSmall"]
                    ))
                for source in ligne.get("echeance_auto_sources_hors_solde") or []:
                    story.append(_p(
                        f"Compte source absent des soldes : {source.get('compte')} ; "
                        f"{_f(source.get('total_source'))} MAD à vérifier sans reclassification automatique.", styles["HPSmall"]
                    ))
                    for anomalie in source.get("anomalies_sources") or []:
                        story.append(_p(
                            f"Source à vérifier {anomalie.get('numero') or anomalie.get('facture_id')} : "
                            + " ".join(anomalie.get("motifs") or []), styles["HPSmall"]
                        ))
        if contenu.get("lignes"):
            keys=[]
            for line in contenu.get("lignes") or []:
                for k in line:
                    if k not in keys: keys.append(k)
            if keys:
                manual=[[ _p(k,styles["HPSmall"]) for k in keys]]
                for line in contenu.get("lignes") or []: manual.append([_p(line.get(k,"-"),styles["HPSmall"]) for k in keys])
                w=245*mm/max(len(keys),1); tm=Table(manual,colWidths=[w]*len(keys),repeatRows=1); tm.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.2,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),6.5),("VALIGN",(0,0),(-1,-1),"TOP") ])); story += [Spacer(1,2*mm),tm]

    if data.get("archive"): story += [Spacer(1,5*mm),Paragraph(f"Empreinte SHA-256 : {data['archive'].get('empreinte_sha256','')}",styles["HPSmall"])]
    else: story += [Spacer(1,5*mm),Paragraph("DOCUMENT PROVISOIRE - NON ARCHIVÉ - À CONTRÔLER AVANT DÉPÔT SIMPL-IS",styles["HPSmall"])]
    doc.build(story,onFirstPage=on_page,onLaterPages=on_page); return buf.getvalue()
