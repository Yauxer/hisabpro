# -*- coding: utf-8 -*-
"""Cahier de recette reproductible, sans connexion ni écriture en base.

L'oracle comptable utilise Decimal et les opérations du scénario fictif. Il
n'importe aucun calcul HisabPro : ses attentes restent indépendantes du produit.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "recette"
TITLE = "CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO"
VERSION = "Révision du 7 octobre 2026 — scénario 2025 / ouverture 2026"
STATUSES = ("Non testé", "Réussi", "Échoué", "Bloqué")
DOMAINS = ("Administration", "Facturation", "Paiements", "Comptabilité", "Banques", "Stocks", "Immobilisations", "Fiscalité", "Inventaire clôture", "États ETIC", "Liasse exports", "Sécurité UX", "Exploitation", "Scénarios négatifs")
SOURCES = [
    {"id": "IS", "titre": "MEF/DGI — dispositif fiscal 2025, tableau de transition IS de droit commun", "url": "https://www.finances.gov.ma/Publication/dgi/2025/secteur-transport-incitations-fiscales2025.pdf", "verification": "Tableau consulté : bénéfice ≤ 300 000 MAD, 17,5 % en 2025 et 20 % en 2026. Le scénario ne relève pas d'un régime sectoriel privilégié."},
    {"id": "TVA", "titre": "MEF/DGI — CGI 2026, article 99", "url": "https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf", "verification": "Extrait indexé officiel consulté : taux normal 20 %. Les articles complets restent à vérifier selon la qualification de chaque opération ; aucune exonération n'est déduite d'un nom d'article."},
    {"id": "CM_ACOMPTES", "titre": "MEF/DGI — note circulaire 733 (2023), transition 2023–2026", "url": "https://www.finances.gov.ma/Publication/dgi/2023/NoteCirculaireN733-2023.pdf", "verification": "Exemples officiels consultés : CM au taux de 0,25 % ; acomptes 25 % de la référence annuelle ajustée au taux de l'exercice pendant la transition. L'exonération de démarrage est également documentée par le CGI complet, référence CM_CGI ; les faits du dossier restent à justifier."},
    {"id": "RAS_IS", "titre": "MEF/DGI — tableau des mesures fiscales de la LF 2023", "url": "https://www.finances.gov.ma/Publication/dgi/2023/tableau-mesures-lf2023.pdf", "verification": "RAS de 5 % pour rémunérations concernées versées aux personnes morales par les organismes publics ; ne pas appliquer ce taux aux ventes de marchandises. Variante distincte du parcours principal."},
    {"id": "RAS_TVA", "titre": "MEF/DGI — rappel officiel des retenues TVA, 23 août 2024", "url": "https://www.finances.gov.ma/fr/pages/detail-actualite.aspx?fiche=6947", "verification": "Retenues TVA 75 % / 100 % selon opérations et justificatifs ; le moteur actuel ne les automatise pas. Le scénario correspondant reste bloqué pour une déclaration complète."},
    {"id": "CSS", "titre": "MEF — Al Maliya, dispositions LF 2026, page 50", "url": "https://www.finances.gov.ma/Maliya%20tawassol/SLF2026-Fr.pdf", "verification": "Prorogation 2026–2028 ; seuil un million MAD et taux 1,5 %, 2,5 %, 3,5 %, 5 %. La référence N-1 ne doit jamais être inventée."},
    {"id": "COMPTABILITE", "titre": "MEF — normes du CNC", "url": "https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx", "verification": "Portail de référence CGNC/Avis n°24. Le cahier décrit des comportements à recetter, sans certification ni homologation."},
    {"id": "CM_CGI", "titre": "DGI — CGI 2026, reproduction institutionnelle CRI Casablanca, article 144, pages imprimées 268–270", "url": "https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf", "verification": "PDF complet effectivement téléchargé et lu. Article 144-I-C : hors concessionnaires de service public, exonération pendant 36 mois d'exploitation, limitée à 60 mois depuis constitution. Article 144-I-D : taux normal 0,25 %, minimum IS 3 000. La qualification d'un dossier réel exige les dates et justificatifs. Le lien DGI direct n'a pas été accessible pendant cette vérification."},
    {"id": "TVA_FAIT_GENERATEUR", "titre": "DGI — CGI 2026, reproduction institutionnelle CRI, article 95, page imprimée 175", "url": "https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf", "verification": "Texte complet lu : encaissement comme fait générateur ; en option débit, facturation ou inscription comptable de la créance. Une FAE ne peut donc pas être réputée sans TVA du seul fait que sa facture arrive en N+1. Sa qualification est isolée dans une variante bloquée, exclue des totaux principaux."},
]


def dec(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def mad(value):
    return f"{dec(value):,.2f}".replace(",", " ").replace(".", ",") + " MAD"


def libelle_controle(key):
    labels={
        'produits':'Produits', 'charges_hors_is':'Charges hors IS', 'resultat_avant_is':'Résultat avant IS',
        'reintegrations':'Réintégrations', 'deductions':'Déductions', 'deficits_imputes':'Déficits imputés', 'benefice_fiscal':'Bénéfice fiscal imposable',
        'is_theorique':'IS théorique', 'credit_is':'Crédit imputable IS', 'solde_is':'Solde IS', 'taux_is':'Taux IS', 'acomptes_2025':'Acomptes versés en 2025',
        'resultat_net':'Résultat net', 'stock_quantite':'Quantité du stock final', 'stock_valeur':'Valeur du stock final', 'stock_cmup':'Coût moyen unitaire pondéré',
        'banque':'Solde bancaire', 'creances_clients_brutes':'Créances clients brutes', 'fournisseurs':'Dettes fournisseurs',
        'tva_collectee_annuelle':'TVA collectée annuelle', 'tva_recuperable_annuelle':'TVA récupérable annuelle', 'tva_nette_annuelle':'TVA nette annuelle', 'tva_payee_N':'TVA payée en N', 'tva_due_fin_N':'TVA due en fin de N',
        'marge_brute':'Marge brute', 'production':'Production', 'valeur_ajoutee':'Valeur ajoutée / EBE', 'resultat_exploitation':"Résultat d'exploitation", 'resultat_financier':'Résultat financier', 'resultat_non_courant':'Résultat non courant',
        'caf':"Capacité d'autofinancement", 'cm_base':'Base de cotisation minimale', 'cm_calculee_sans_exoneration':'CM calculée hors exonération', 'cm_minimum_sans_exoneration':'Minimum de CM hors exonération',
        'total_actif_net':'Total actif net', 'dettes_et_provisions':'Dettes et provisions', 'total_passif_net':'Total passif',
    }
    return labels.get(key,key.replace('_',' ').capitalize())


def texte_lisible(value):
    """Normalisation éditoriale seulement ; conserve les références de pièces."""
    substitutions = {
        "Journalattendu":"Journal attendu", "dueselonmoteur":"due selon le moteur", "quatreacomptes":"quatre acomptes", "sauvegardeautomatique":"sauvegarde automatique",
        "tant queleformat":"tant que le format", "leparcoursne":"le parcours ne", "d'exportoud'obligation":"d'export ou d'obligation",
        "avec cetemail":"avec cet email", "motpassword":"mot de passe password", "surcopie":"sur copie", "Refusdu":"Refus du", "pasdebanque":"pas de banque", "pasd'":"pas d'", "pasde ":"pas de ",
        "mêmemontant":"même montant", "Refusécart":"Refus de l'écart", "etcrédit":"et crédit", "outexte":"ou texte", "champvide":"champ vide", "saveencopie":"enregistrer sur copie", "avecref":"avec référence", "avecpièce":"avec pièce", "avecpiece":"avec pièce",
        "encoreen":"encore en", "coursàdate":"cours à la date", "danslab":"dans le laboratoire", "età-nouveaux":"et à-nouveaux", "déjàclôturé":"déjà clôturé", "Refusserveur":"Refus serveur", "Accèsrefusé":"Accès refusé", "Jetonexpiré":"Jeton expiré", "Grandlivre":"Grand livre",
        "Factureet":"Facture et", "soldeàjour":"solde à jour", "misencache":"mis en cache", "avoirimputé":"avoir imputé", "eterreurs":"et erreurs", "ouvrirpage":"ouvrir la page", "n'estpasune":"n'est pas une", "surbase":"sur base", "logsutiles":"logs utiles", "motsdepasse":"mots de passe", "unefois":"une fois",
        "créeravoir":"créer un avoir", "undossier":"un dossier", "factureimpayée":"facture impayée", "surl'acompte":"sur l'acompte", "netbancaire":"net bancaire", "amortcumul":"amortissement cumulé", "RASIS":"RAS IS", "TVARAS":"TVA RAS", "Bautorisés":"B autorisés",
        "Copieindépendanteavantcréationdesfactures":"Copie indépendante avant création des factures",
        "Créerundossierdevariantedistinctsansmodifierlasociétéprincipalepremierexercice":"Créer un dossier de variante distinct sans modifier la société principale du premier exercice",
        "Rejouerledossierdevariantedepuisparamétrageencaissement":"Rejouer le dossier de variante depuis le paramétrage encaissement",
        "MoteuractuelneréconciliepastoutesretenuesTVAarticle":"Moteur actuel ne réconcilie pas toutes les retenues TVA article",
        "Annexedéclarativecomplèteetmodèleofficiel":"Annexe déclarative complète et modèle officiel",
        "ArchiveinternedisponiblemaisannexesofficiellesetEDI":"Archive interne disponible mais annexes officielles et EDI",
        "ScénariobloquépourpréparationcomplètedéclarationTVA":"Scénario bloqué pour la préparation complète de la déclaration TVA",
        "Montantsdenettechnologiquesseulement":"Montants nets de contrôle seulement",
        "Pasdeparcoursdédiécompletvérifiédanscedépôt":"Pas de parcours dédié complet vérifié dans ce dépôt",
        "Catalogueofficielcourant":"Catalogue officiel courant",
        "Schémaofficielapplicable":"Schéma officiel applicable",
        "Valeurlocative":"Valeur locative", "qualificationetschémaannexe":"qualification et schéma annexe",
        "domaineetconditionsapplicables":"domaine et conditions applicables", "XSDetrecettedépôt":"XSD et recette de dépôt",
        "boutondésactivé":"bouton désactivé", "ne sontpas":"ne sont pas", "nesontpasunétatDGIofficiel":"ne sont pas un état DGI officiel",
        "créditsaIS":"crédits IS", "nesuffisentpas":"ne suffisent pas", "nondéterminablesavec":"non déterminables avec",
        "lespiècesprincipales":"les pièces principales", "impossibledevaliderundépôtcomplet":"impossible de valider un dépôt complet",
        "Consulterlamatricedecouverture":"Consulter la matrice de couverture", "enregistrerleblocage":"enregistrer le blocage",
        "pasinventerd":"pas inventer d", "obligationpour":"obligation pour", "terminercecas":"terminer ce cas",
        "Limiteexpliquée":"Limite expliquée", "parcoursàreprendre":"parcours à reprendre", "développementetvérificationofficielle":"développement et vérification officielle",
        "Entréeduregistredeslimites":"Entrée du registre des limites", "etréférenceofficiellequanddisponible":"et référence officielle quand disponible",
        "Copieindépendanteavantliquidation":"Copie indépendante avant liquidation", "Copieindépendante":"Copie indépendante",
        "Nouvellecopieindépendante":"Nouvelle copie indépendante", "Dossierfictifvariantdereprise":"Dossier fictif de variante de reprise",
        "derepriseayantattestation":"de reprise avec attestation", "avantdéficit":"avant déficit", "FiscalitéIS":"Fiscalité IS",
        "Ajoutermillésime":"Ajouter le millésime", "avecmontants":"avec les montants", "etréférence":"et référence",
        "contrôlerpropositionFIFO":"contrôler la proposition FIFO", "puisconfirmer":"puis confirmer",
        "Déficitimputé":"Déficit imputé", "bénéficefiscal":"bénéfice fiscal", "aucuneconsommationduplicat":"aucune consommation en doublon",
        "aprèsrechargement":"après rechargement", "preuvefiscaleantérieureexplicitementfournie":"preuve fiscale antérieure explicitement fournie",
        "nepasinventer":"ne pas inventer", "déficitdanslasociéténouvelle":"déficit dans la société nouvelle",
        "reporteteligibilitéàvaliderparresponsablefiscal":"report et éligibilité à valider par le responsable fiscal",
        "surtexteofficiel":"sur le texte officiel", "lecasvérifiela":"le cas vérifie la", "imputationsourcedocumentée":"imputation issue d'une source documentée",
        "reprisesdeprovisions":"reprises de provisions", "antérieurementtaxées":"antérieurement taxées", "réintégrationsprincipal":"réintégrations principales",
        "Danscopievariante":"Dans la copie de variante", "uniquementaprèsjustificationdetaxationantérieure":"uniquement après justification de taxation antérieure",
        "contrôlernouveaucalcul":"contrôler le nouveau calcul", "RésultatcomptableavantISaugmente":"Résultat comptable avant IS augmente de",
        "puisdéduction":"puis déduction", "déductionautomatique":"déduction automatique", "unerepriseprobable":"une reprise probable",
        "provisionexistante":"provision existante", "etjustificationdetaxationantérieure":"et justification de taxation antérieure",
        "piècefictive":"pièce fictive", "régimesociétéencaissement":"régime société encaissement",
        "réellementencaisséeaprèsrejet":"réellement encaissée après rejet", "contrôlermoisdécembreetfactureimpayée":"contrôler le mois de décembre et la facture impayée",
        "acomptesetdatesbank":"acomptes et dates bancaires", "paschangerlerégimed":"pas changer le régime d",
        "unepiècevalidéepour":"une pièce validée pour", "altérerunsnapshot":"altérer un snapshot",
        "TVAdefactureimpayée":"TVA de la facture impayée", "exigibleavantencaissementdocumenté":"exigible avant encaissement documenté",
        "pasdedoublonTVA":"pas de doublon TVA", "rejetnelaissepasunencaissementfictif":"le rejet ne laisse pas un encaissement fictif",
        "optionrégime":"option de régime", "Clientpublicfiction":"Client public fictif", "siqualificationapplicable":"si qualification applicable",
        "pasexécuterune":"pas exécuter une", "déclarationautomatiquefinale":"déclaration automatique finale",
        "aveclerégimeincomplet":"avec le régime incomplet", "Vérifierlesarticlesapplicables":"Vérifier les articles applicables",
        "attestationetletypede":"attestation et le type de", "prestationavec":"prestation avec", "responsableréglementaire":"responsable réglementaire",
        "enregistrerlimitationdu":"enregistrer la limitation du", "aucunpaiement":"aucun paiement", "annoncésoldé":"annoncé soldé",
        "enoubliantlaTVARAS":"en oubliant la TVA RAS", "sousqualification":"sous qualification", "nepasappliquerRASauxmarchandises":"ne pas appliquer la RAS aux marchandises",
        "Danscopieisolée":"Dans la copie isolée", "paslasociétéprincipale":"pas la société principale",
        "payéeacquisitionetdotation":"acquisition payée et dotation", "contrôleretvaliderlesécrituresgénérées":"contrôler et valider les écritures générées",
        "etproduitcession":"et produit de cession", "plusvaluecomptable":"plus-value comptable",
        "traitementfiscal":"traitement fiscal", "TVArégularisationàdocumenter":"TVA de régularisation à documenter",
        "comptecréancecessionàconfirmerdansparamétrage":"compte créance de cession à confirmer dans le paramétrage",
        "QualificationetrégularisationTVAimmobilisationsarticle":"Qualification et régularisation TVA immobilisations article",
        "nonautomatiquementvalidées":"non automatiquement validées", "Créeruncompteavec":"Créer un compte avec",
        "Créationrefusée":"Création refusée", "unesociétéutilisateurpréservée":"une seule société et son utilisateur préservés",
        "CréercompteCopieFaibleavec":"Créer le compte Copie Faible avec", "sociétéorpheline":"société orpheline",
        "saisirICEinvalide":"saisir un ICE invalide", "Erreurclaire":"Erreur claire", "aucuneidentitécorrompue":"aucune identité corrompue",
        "Créercesdatesavec":"Créer ces dates avec", "Refusdechevauchement":"Refus de chevauchement",
        "Créerexercicetreizemois":"Créer un exercice de treize mois", "Refusdeladurée":"Refus de la durée",
        "bornesexistantespréservées":"bornes existantes préservées", "nouvelleécriture":"nouvelle écriture",
        "Validationrefusée":"Validation refusée", "aucunnumérodéfinitifindûmentcréé":"aucun numéro définitif indûment créé",
        "Facturebrouilloncopietest":"Facture brouillon sur copie de test", "Refusdesaisieouvalidation":"Refus de saisie ou validation",
        "écritureautomatique":"écriture automatique", "immobilisationcopietest":"immobilisation sur copie de test",
        "Erreurdetaux":"Erreur de taux", "pasdecontournementparréductionautomatique":"pas de contournement par réduction automatique",
        "Mêmejour":"Même jour", "Consulterlignesdéjàcréées":"Consulter les lignes déjà créées",
        "récupérationFEC":"récupération FEC", "Deuxsourcesdistinctes":"Deux sources distinctes",
        "référencesrestenttexte":"références restent du texte", "Doublecomptabilisation":"Double comptabilisation",
        "déjàcomptabilisée":"déjà comptabilisée", "Cliquercomptabiliser":"Cliquer sur Comptabiliser",
        "denouveau":"de nouveau", "sicommandedisponible":"si la commande est disponible",
        "Tenteréditiondepiècedéfinitive":"Tenter l'édition de la pièce définitive",
        "correctionparavoir":"correction par avoir", "annulationtraçable":"annulation traçable",
        "tiersmodifiés":"tiers modifiés", "imputerdenouveau":"imputer de nouveau",
        "écrituresinchangées":"écritures inchangées", "Créditavoir":"Crédit d'avoir",
        "tenterimputationcréditversautretiersetavantutilisationencopie":"tenter l'imputation du crédit vers un autre tiers, avant utilisation sur une copie",
        "aucuneallocationarbitraire":"aucune allocation arbitraire", "Copieavantimputation":"Copie avant imputation",
        "Refusplafond":"Refus du plafond", "pasdedetteclientfictive":"pas de dette client fictive",
        "Refusdequantité":"Refus de quantité", "stocknoncrééindûment":"stock non créé indûment",
        "Copieavantencaissement":"Copie avant encaissement", "entréebanqueantérieure":"entrée en banque antérieure",
        "encaissementfrais":"encaissement avec frais", "pasdebanquenégativecréée":"pas de banque négative créée",
        "déjàencaissé":"déjà encaissé", "TentertransitionRejeter":"Tenter la transition Rejeter",
        "Refusstatutincompatible":"Refus du statut incompatible", "correctioncontrôlée":"correction contrôlée",
        "Dateeffectivefutureoudatéeavantémission":"Date effective future ou datée avant émission",
        "Transitioncopie":"Transition sur copie", "saisirdateinvalide":"saisir une date invalide",
        "Refusdocumenté":"Refus documenté", "pasdemouvementfuturouantérieuràsonorigine":"pas de mouvement futur ou antérieur à son origine",
        "SélectionnerauLettrageenlaboratoire":"Sélectionner au Lettrage en laboratoire", "mélangeauxiliaire":"mélange d'auxiliaires",
        "Copiebrouillonsvalidésdecontrôle":"Copie avec écritures validées de contrôle", "aucunelettrageforcé":"aucun lettrage forcé",
        "LignebancaireCAP":"Ligne bancaire CAP", "déjàrapprochée":"déjà rapprochée",
        "Tenterliaisonàsecondécriture":"Tenter la liaison à une seconde écriture",
        "devoirdérapprochercontrôlé":"dérapprochement préalable contrôlé", "CSVlignedébit":"CSV avec ligne débit",
        "Importerdanscopie":"Importer dans une copie", "fichiernégatifgénérépartechnicien":"fichier négatif généré par le technicien",
        "ambigüeimportée":"ambiguë importée", "Inventairecopie":"Inventaire sur copie",
        "inventairefinalnégatif":"inventaire final négatif", "Éditerarticleservice":"Éditer un article de service",
        "Stockservice":"Stock de service", "aucunmouvementstockparprestation":"aucun mouvement de stock par prestation",
        "existevalidé":"existe et est validé", "Générerdotationdenouveau":"Générer la dotation de nouveau",
        "Créerimmobilisationtest":"Créer une immobilisation de test", "amortissementnoncorrompus":"amortissement non corrompus",
        "fiscalenonconfirmée":"fiscale non confirmée", "Hypothèseprovision":"Hypothèse provision",
        "nonqualifiée":"non qualifiée", "AfficherFiscalitéavantconfirmation":"Afficher Fiscalité avant confirmation",
        "Diagnosticàconfirmer":"Diagnostic à confirmer", "pasderéintégrationchoisie":"pas de réintégration choisie",
        "Fiscalitécopie":"Fiscalité sur copie", "ajoutercrédit":"ajouter un crédit",
        "pasdecréditnégatif":"pas de crédit négatif", "oudoubledéduction":"ou double déduction",
        "Référenceacomptes":"Référence des acomptes", "justificationvide":"justification vide",
        "Paramètresfiscalitécopie":"Paramètres fiscaux sur copie", "Refusdejustification":"Refus sans justification",
        "pasdereclassement":"pas de reclassement", "pourcontrôlevert":"pour obtenir un contrôle vert",
        "avantclôture":"avant clôture", "ouvertencopie":"ouvert sur la copie", "ConfirmerliquidationIS":"Confirmer la liquidation IS",
        "simulationconsultablesanssnapshotfinal":"simulation consultable sans snapshot final",
        "comptabiliséincohérent":"comptabilisé incohérent", "chargejournal":"charge au Journal",
        "confirmationencopie":"confirmation sur copie", "Blocagecohérence":"Blocage de cohérence",
        "nepasadapterlecalculfiscalpouraccepter":"ne pas adapter le calcul fiscal pour accepter",
        "Valeurnégative":"Valeur négative", "nonnumériquerefusée":"non numérique refusée",
        "videÀcompléter":"vide = À compléter", "zérovalideetprioritaire":"zéro valide et prioritaire",
        "confirmersectionencopie":"confirmer la section sur copie", "Incohérencede":"Incohérence de",
        "pasdefinalisationdeliasse":"pas de finalisation de la liasse",
        "datepièceabsents":"date de pièce absents", "sourcesambigües":"sources ambiguës",
        "Technicienpréparelabuniquement":"Le technicien prépare uniquement le laboratoire",
        "Anomaliesvisibles":"Anomalies visibles", "aucuneidentité":"aucune identité", "échéanceinventée":"échéance inventée",
        "fermémanuellementencopie":"fermé manuellement sur copie", "Tenterécriture":"Tenter une écriture",
        "puisadminrouvrepériode":"puis l'administrateur rouvre la période", "Écriturerefuséequandfermée":"Écriture refusée quand la période est fermée",
        "réouvertureadminauditéeavantclôture":"réouverture administrateur auditée avant clôture",
        "Tenterclôture":"Tenter la clôture", "Refusdateavantfindexercice":"Refus avant la fin de l'exercice",
        "aucuncontournement":"aucun contournement", "exerciceclôturé":"exercice clôturé", "aprèsclôture":"après clôture",
        "Tentercréation":"Tenter une création", "reouverturepériode":"réouverture de période",
        "correctiondanspériodeouverteultérieure":"correction dans une période ouverte ultérieure", "pisteauditpréservée":"piste d'audit préservée",
        "Relancerclôture":"Relancer la clôture", "générationAN":"génération des AN", "unseulreport":"un seul report",
        "ModifierETIC":"Modifier ETIC", "exporterarchiveaprèsmutation":"exporter l'archive après mutation",
        "Refusmodificationarchive":"Refus de modification de l'archive", "Utilisateurlecture":"Utilisateur en lecture",
        "TenterAPIdecréationetboutonfacture":"Tenter l'API de création et le bouton facture", "etcontrôlesUI":"et contrôles UI",
        "aucunécriturenew":"aucune nouvelle écriture", "IDdocumentdeB":"ID du document de B",
        "TechnicientesteAPIGET":"Le technicien teste l'API GET", "PATCHpièceBavecjetonA":"PATCH de pièce B avec le jeton A",
        "sansdonnéesfuitées":"sans fuite de données", "écritureinter":"écriture inter", "IDfichierdeB":"ID du fichier de B",
        "TenterlienfichieravecjetonA":"Tenter le lien du fichier avec le jeton A", "autresasociétés":"autres sociétés",
        "RechargerdétailfactureouappelAPIprotégé":"Recharger le détail facture ou appeler une API protégée",
        "etretourconnexion":"et retour à la connexion", "secretsnonaffichés":"secrets non affichés",
        "surcopieavantl":"sur copie avant l", "étatrequissi":"état requis si",
        "Cyclecommercial":"Cycle commercial", "ParcourirFactures":"Parcourir Factures", "ouvriresdétails":"ouvrir les détails",
        "scrolllocalseulementsinécessaire":"scroll local seulement si nécessaire", "essentieltronqué":"essentiel tronqué",
        "règlementdujeu":"règlement du jeu", "Enregistreropération":"Enregistrer une opération",
        "observerlistes":"observer les listes", "JournalavantF":"Journal avant F", "Étatlocalactualisé":"État local actualisé",
        "Ouvrirselectcompte":"Ouvrir la sélection de compte", "saisirnuméroetchoisir":"saisir le numéro et choisir",
        "Libelléautomatique":"Libellé automatique", "attenteanormalementlongue":"attente anormalement longue",
        "SociétévarianteAtlas":"Société variante Atlas", "ExportPDFsurcopieavecidentitélittérale":"Export PDF sur copie avec identité littérale",
        "Titreexactavec":"Titre exact avec", "texteéchappé":"texte échappé", "Virementpartiel":"Virement partiel",
        "effetnonencaissé":"effet non encaissé", "ComparerFactures":"Comparer Factures", "Situationfinancière":"Situation financière",
        "Soldecommercialdistinctdesvaleursencoursbanque":"Solde commercial distinct des valeurs en cours en banque",
        "aucunstatutpayéavantétapeeffective":"aucun statut payé avant l'étape effective",
        "Réseauindisponiblepuisrétabli":"Réseau indisponible puis rétabli", "SurcopiecouperaccèsAPI":"Sur copie couper l'accès API",
        "puisrestaurer":"puis restaurer", "Erreurcompréhensible":"Erreur compréhensible", "donnéesmensongères":"données mensongères",
        "ouactiondoubledéclenchée":"ou action déclenchée deux fois", "DeuxcomptesA":"Deux comptes A",
        "Changersociétédanssélecteuravec":"Changer de société dans le sélecteur avec", "formulaireouvert":"formulaire ouvert",
        "Contexteactualisé":"Contexte actualisé", "enregistrementdanserreursociété":"enregistrement dans la mauvaise société",
        "droitsrechargésdu":"droits rechargés du", "Baseisoléeseule":"Base isolée seule",
        "schémaobtenuauxmodèlesetmigrations":"schéma obtenu aux modèles et migrations", "testercontraintesavec":"tester les contraintes avec",
        "Historiquenonréécrit":"Historique non réécrit", "migrationsrequisesidentifiées":"migrations requises identifiées",
        "aucunevalidationPostgreSQLremplacéeparSQLite":"aucune validation PostgreSQL remplacée par SQLite",
        "Baseisoléerecette":"Base isolée de recette", "répertoirepiècesjointes":"répertoire des pièces jointes",
        "configurationhorssecrets":"configuration sans secrets", "Effectuersauvegardeselonprocédure":"Effectuer la sauvegarde selon la procédure",
        "empreinteetlistefichiers":"empreinte et liste des fichiers", "Archivefermée":"Archive fermée",
        "snapshotsinclus":"snapshots inclus", "ceZIPdifférentieln":"ce ZIP différentiel n", "sauvegardeDB":"sauvegarde DB",
        "Backupprécédent":"Sauvegarde précédente", "nouvellebaseisolée":"nouvelle base isolée",
        "Restaurersurbasedédiéedifférentedeproduction":"Restaurer sur une base dédiée différente de production",
        "reconnecterapplicationdedicace":"reconnecter l'application dédiée", "etempreintearchiveidentiques":"et empreinte d'archive identiques",
        "justificatifsouvrables":"justificatifs ouvrables", "aucunrestaurationsurbase":"aucune restauration sur base",
        "aprèsincident":"après incident", "Copieserveurisolée":"Copie de serveur isolée",
        "Arrêterbackendentrebrouillonetvalidation":"Arrêter le backend entre brouillon et validation",
        "puisredémarrer":"puis redémarrer", "Aucunécriturepartielledéfinitive":"Aucune écriture définitive partielle",
        "validationauditstable":"validation et audit stables", "Paramètresréseaudéploiementisolé":"Paramètres réseau du déploiement isolé",
        "secretJWTnonlivré":"secret JWT non livré", "VérifierHTTPS":"Vérifier HTTPS", "originesCORS":"origines CORS",
        "permissionsfichiers":"permissions des fichiers", "absenceendpointsadminpublics":"absence d'endpoints admin publics",
        "Pointsgouvernés":"Points gérés", "nepasmarquerprêtproductionavantrevuesréelles":"ne pas marquer prêt pour la production avant les revues réelles",
        "Exécutercommandesdocumentéesunitaires":"Exécuter les commandes unitaires documentées",
        "bancPostgreSQLisolé":"banc PostgreSQL isolé", "consignerdate":"consigner la date", "logetfailures":"logs et échecs",
        "réellementobservés":"réellement observés", "aucuneassimilationàrecetteutilisateur":"aucune assimilation à la recette utilisateur",
        "Sourcesofficiellesetversion":"Sources officielles et version", "Responsablefiscalcontrôlequalifications":"Le responsable fiscal contrôle les qualifications",
        "modalitésdépôt":"modalités de dépôt", "CSSetarchivage":"CSS et archivage", "Avisdevalidationdocumenté":"Avis de validation documenté",
        "oublocageexplicite":"ou blocage explicite", "aucunecertificationannoncéeparautomatisation":"aucune certification annoncée par automatisation",
        "Aucunecontrepassationnonjustifiée":"Aucune contrepassation non justifiée", "Capturecontrôles":"Capture des contrôles",
        "Contrôlerlemontantetabsence":"Contrôler le montant et l'absence", "Dettesreportéessoldées":"Dettes reportées soldées",
        "Identifiantassocié":"Identifiant associé", "Liquidationconfirmée":"Liquidation confirmée",
        "Livrecohérentavec":"Livre cohérent avec", "Lorsquecontrôles":"Lorsque les contrôles",
        "Premierexercice":"Premier exercice", "Provisiondurable":"Provision durable", "Provisionrisque":"Provision risque",
        "Référencetransitoirevérifiée":"Référence transitoire vérifiée", "Résultatcourant":"Résultat courant",
        "Siunseulbloquantsubsiste":"Si un seul contrôle bloquant subsiste", "antérioritésabsentes":"antériorités absentes",
        "aucuncomplémentautomatique":"aucun complément automatique", "aucuneaffectationantérieure":"aucune affectation antérieure",
        "aucuneinformationprobable":"aucune information probable", "aucuneprésentationcommefichier":"aucune présentation comme fichier",
        "aucuneréférenceforcée":"aucune référence forcée", "autresvariations":"autres variations",
        "avantautresopérations":"avant les autres opérations", "banqueaprèscesdeuxpaiements":"banque après ces deux paiements",
        "boutonaccessible":"bouton accessible", "brutimmobilisation":"brut immobilisation",
        "comparatifabsent":"comparatif absent", "confirmationnéant":"confirmation néant",
        "conformitéofficielle":"conformité officielle", "consignerempreinte":"consigner l'empreinte",
        "contrepassationscut":"contrepassations cut", "conversionautomatique":"conversion automatique",
        "datepièceetauxiliairesissusdesvraiestiersfiction":"date de pièce et auxiliaires issus des véritables tiers fictifs",
        "decontrepassation":"de contrepassation", "depaiementpourmontantzéro":"de paiement pour un montant zéro",
        "despagescomparées":"des pages comparées", "diagnosticsnonmasqués":"diagnostics non masqués",
        "distinctesdujournal":"distinctes du journal", "dotationsdurables":"dotations durables",
        "déjàimputéacomptes":"déjà imputé aux acomptes", "dépréciationclient":"dépréciation client",
        "empreintecomplète":"empreinte complète", "encaissementimmédiat":"encaissement immédiat",
        "engagementhorsbilan":"engagement hors bilan", "enregistreracompte":"enregistrer l'acompte",
        "facturesfournisseurs":"factures fournisseurs", "fictifsrenseignés":"fictifs renseignés",
        "fiscalefabriquée":"fiscale fabriquée", "fiscalitécohérente":"fiscalité cohérente",
        "inférieureauseuild":"inférieure au seuil d", "journaldistinct":"journal distinct",
        "lesavisbancairesfictifs":"les avis bancaires fictifs", "lesbrouillonsdecontrepassationscréésparajustements":"les brouillons de contrepassations créés par les ajustements",
        "lesdeuxfichiers":"les deux fichiers", "lesstatistiquescommerciales":"les statistiques commerciales",
        "lignesetmontantsaucentime":"lignes et montants au centime", "liquidationconfirmée":"liquidation confirmée",
        "liquidationprévisionnelle":"liquidation prévisionnelle", "mouvementseffet":"mouvements d'effet",
        "nedéduireaucuneabsenced":"ne déduire aucune absence d", "numérosordonnés":"numéros ordonnés",
        "publiécommehistorique":"publié comme historique", "reprendreunversementdesoldede":"reprendre un versement de solde de",
        "référenceannuelle":"référence annuelle", "référencesetsource":"références et source",
        "référenceslittérales":"références littérales", "référentielfiscal":"référentiel fiscal",
        "réglagesbloquésaprèsconfirmation":"réglages bloqués après confirmation", "simpledatecomptable":"simple date comptable",
        "sourceliquidation":"source liquidation", "sursourceofficielle":"sur source officielle",
        "tousmontantscopiésdanspreuves":"tous les montants copiés dans les preuves", "valeursautomatiques":"valeurs automatiques",
        "vérifierqueleréférentielest":"vérifier que le référentiel est", "vérifierréférenceissue":"vérifier la référence issue de",
        "échéancesdocumentées":"échéances documentées", "écriturepouracomptesnonpayés":"écriture pour les acomptes non payés",
        "écrituresdéfinitives":"écritures définitives", "événementpostérieur":"événement postérieur",
        "nonpayée":"non payée", "clientsbruts":"clients bruts", "avantIS":"avant IS",
        "rôlecomptable":"rôle comptable", "rôlelecture":"rôle lecture", "réservéeadmin":"réservée à l'administrateur",
        "aucunbrouillon":"aucun brouillon", "montantsfigés":"montants figés", "montantszéro":"montants zéro",
        "nonapplicables":"non applicables", "chargeISdéjàconstatée":"charge IS déjà constatée",
        "exercice2025":"exercice 2025", "soldeinitial":"solde initial", "soldefinal":"solde final",
        "créditrelevé":"crédit relevé", "débitrelevé":"débit relevé", "soldecomptable":"solde comptable",
        "soldebancaire":"solde bancaire", "dette transferrée":"dette transférée", "donnéesoracle":"données oracle",
        "mêmeschiffres":"mêmes chiffres", "mêmesvaleurs":"mêmes valeurs", "analysesnéant":"analyses néant",
        "aucunecession":"aucune cession", "résultatavant":"résultat avant", "résultatfiscal":"résultat fiscal",
        "résultatnet":"résultat net", "stockphysique":"stock physique", "noteLitige":"note Litige",
        "retourstock":"retour stock", "actifnet":"actif net", "avantref":"avant référence",
        "Étatpréparé":"État préparé", "annonceravant":"annoncer avant", "créditdisponible":"crédit disponible",
        "enretardaprès":"en retard après", "partielreste":"partiel reste", "créditnéant":"crédit néant",
        "comptesgestion":"comptes de gestion", "reprisebilan":"reprise bilan", "clôtureunique":"clôture unique",
        "Clôtureunique":"Clôture unique", "Aucunsecond":"Aucun second", "crééoucréable":"créé ou créable",
        "soldercharges":"solder les charges", "TVAcollectée":"TVA collectée", "titrepréserve":"titre préserve",
        "datecourante":"date courante", "titreprêt":"titre prêt", "nonéchu":"non échu",
        "article101":"article 101", "horsbilan":"hors bilan", "dépôtcomplet":"dépôt complet",
    }
    text=str(value)
    protected=[]
    def protect(match):
        protected.append(match.group(0))
        return f"§§{len(protected)-1}§§"
    text=re.sub(r"HisabPro|PostgreSQL|NaN|Recette![A-Za-z0-9]+|https?://\S+|[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+",protect,text)
    for old,new in sorted(substitutions.items(),key=lambda p:-len(p[0])):
        text=text.replace(old,new)
    # Noms comptables et mots accolés à un nombre sont séparés sans toucher aux
    # références REC/IF/ICE ni aux dates, URL ou adresses électroniques.
    text=re.sub(r"(?<=[a-zà-ÿ])(?=[A-Z])"," ",text)
    text=re.sub(r"\b(TVA|CSS|CPC|ETIC|CMUP|IS|CM|IF|ICE|TP|BQ|OD|AN|CL|PDF|FEC|HT|TTC)(?=[a-zà-ÿ0-9])",r"\1 ",text)
    text=re.sub(r"(?<=[a-zà-ÿ])(?=\d)"," ",text)
    text=re.sub(r"(?<=\d)(?=[a-zà-ÿ])"," ",text)
    text=re.sub(r"\b(le|au|sur|de|puis|et|en|à)(?=\d)",r"\1 ",text)
    text=text.replace(" ;", " ;").replace("→"," → ")
    text=re.sub(r"[ \t]{2,}"," ",text)
    text=re.sub(r",(?=[^\s\d])",", ",text)
    for i,original in enumerate(protected):
        text=text.replace(f"§§{i}§§",original)
    return text


def line(compte, debit=0, credit=0, tiers=None):
    return {"compte": str(compte), "debit": str(dec(debit)), "credit": str(dec(credit)), "tiers": tiers}


def operations():
    """Journal attendu ; les références REC sont celles du cahier, pas des ID DB."""
    rows = []
    def add(ref, day, journal, description, lines, domaine, actions, tax="Sans incidence fiscale directe."):
        rows.append({"reference_recette": ref, "date": day, "journal": journal, "description": description,
                     "lignes": lines, "domaine": domaine, "actions": actions, "impact_fiscal": tax})
    add("CAP-01", "2025-01-01", "BQ", "Apport en capital versé", [line("5141", 200000), line("1111", credit=200000)], "Comptabilité", "Journal → Nouvelle écriture ; date et date de pièce 01/01/2025, journal BQ, référence CAP-01, libellé Apport associé Recette. Saisir les deux lignes ci-contre ; enregistrer le brouillon puis le valider.")
    add("IMMO-ACQ", "2025-01-01", "AC", "Acquisition ordinateur de recette", [line("2355", 24000), line("34551", 4800), line("4481", credit=28800, tiers="F-IMMO")], "Immobilisations", "Immobilisations → Nouvelle immobilisation. Référence IMMO-01, Matériel informatique, fournisseur F-IMMO, acquisition et mise en service 01/01/2025, prix HT 24 000, TVA20 %, récupérable100 %, linéaire5 ans, valeur résiduelle0 ; comptes2355/28355/61935/34551/4481. Cocher acquisition payée le01/01/2025 sur5141. Enregistrer ; valider les écritures générées au Journal.", "TVA sur immobilisation documentée4 800 ; coût amortissable24 000.")
    add("IMMO-PAY", "2025-01-01", "BQ", "Paiement acquisition (généré avec IMMO-ACQ)", [line("4481", 28800, tiers="F-IMMO"), line("5141", credit=28800)], "Immobilisations", "Consulter le paiement créé par IMMO-ACQ ; ne pas saisir une deuxième acquisition ou un deuxième règlement. Valider cette écriture au Journal si elle est en brouillon.")
    add("AC-F01", "2025-01-04", "BQ", "Acompte fournisseur marchandises", [line("3411", 6000, tiers="F-MARCH"), line("5141", credit=6000)], "Paiements", "Acomptes → Nouveau → Fournisseur F-MARCH ; date04/01/2025 ; montant6 000 ; virement Banque Recette ; référence AC-F01 ; comptabilisation cochée. Aucun droit à déduction TVA avant facture justificative.", "Aucune TVA déduite avant rattachement à la facture.")
    add("ACH-01", "2025-01-05", "AC", "Achat100 marchandises à100HT", [line("6111", 10000), line("34552", 2000), line("4411", credit=12000, tiers="F-MARCH")], "Facturation", "Factures → Nouvelle facture achat ; F-MARCH ; date05/01/2025 ; référence fournisseur ACH-01 ; échéance07/01/2025 ; article M-01, quantité100, PU100HT, TVA20 %, aucune remise/frais/RAS. Valider définitivement puis Comptabiliser ; ouvrir le Journal et valider l'écriture. Ce lot est reçu directement par cette facture : ne pas créer un BR supplémentaire.", "TVA facturée2 000 ; déduction après paiements/acomptes justifiés.")
    add("AC-F01-IMP", "2025-01-05", "OD", "Imputation acompte fournisseur sur ACH-01", [line("4411", 6000, tiers="F-MARCH"), line("3411", credit=6000, tiers="F-MARCH")], "Paiements", "Acomptes → AC-F01 → Imputer ; sélectionner ACH-01, montant6 000, date05/01/2025, comptabilisation cochée. Valider l'écriture générée ; reste ACH-01=6 000.")
    add("ACH-01-PAY", "2025-01-07", "BQ", "Solde fournisseur ACH-01", [line("4411", 6000, tiers="F-MARCH"), line("5141", credit=6000)], "Paiements", "Factures → ACH-01 → Payer ; virement6 000 le07/01/2025, Banque Recette, référence PAY-ACH01 ; valider l'écriture générée. Facture soldée12 000 incluant l'acompte.")
    add("ACH-02", "2025-01-10", "AC", "Achat100 marchandises à120HT", [line("6111", 12000), line("34552", 2400), line("4411", credit=14400, tiers="F-MARCH")], "Facturation", "Factures → Achat ; F-MARCH ; date10/01/2025 ; référence ACH-02 ; échéance20/03/2025 ; M-01 quantité100 PU120 TVA20 %. Valider, comptabiliser, valider l'écriture. Stock attendu200 unités, CMUP110.")
    add("VENTE-01", "2025-01-20", "VT", "Vente100 marchandises à250HT via devis/BC/BL", [line("3421", 30000, tiers="C-MARCH"), line("7111", credit=25000), line("4455", credit=5000)], "Facturation", "Après le devis et BC REC-DV01/REC-BC01, créer BL100 unités le20/01/2025, puis facture depuis ce BL. Date20/01/2025, échéance26/01/2025, quantité100 PU250 TVA20 %, aucune remise/frais/RAS. Dans Factures valider puis Comptabiliser ; au Journal valider. Stock100 ; le BL et sa facture ne doivent sortir que100 unités au total.", "TVA collectée au débit5 000.")
    add("VENTE-01-PAY", "2025-01-25", "BQ", "Paiement client partiel", [line("5141", 10000), line("3421", credit=10000, tiers="C-MARCH")], "Paiements", "Factures → VENTE-01 → Encaisser ; virement10 000,25/01/2025, référence PAY-V01 ; valider l'écriture générée. Reste20 000.")
    add("CHQ-01", "2025-01-26", "BQ", "Chèque client20000 en portefeuille", [line("51111", 20000), line("3421", credit=20000, tiers="C-MARCH")], "Paiements", "Factures → VENTE-01 → Encaisser ; Chèque20 000, date26/01/2025, numéro CHQ-01, Banque Recette. Effets & Chèques : statut En portefeuille ; valider l'écriture générée.", "Au régime débit, pas de seconde TVA à l'encaissement.")
    add("CHQ-01-REM", "2025-02-01", "BQ", "Remise chèque en banque", [line("51112", 20000), line("51111", credit=20000)], "Paiements", "Effets & Chèques → CHQ-01 → Remettre ; dans la modale saisir Date réelle de l'opération 01/02/2025, frais 0 ; confirmer puis valider l'écriture au Journal. La date de remise diffère de la date de réception et de celle d'encaissement.")
    add("CHQ-01-ENC", "2025-02-05", "BQ", "Chèque encaissé", [line("5141", 20000), line("51112", credit=20000)], "Paiements", "Effets & Chèques → CHQ-01 → Confirmer l'encaissement ; date effective05/02/2025, frais0 ; valider l'écriture. Banque+20 000 ; comptes51111/51112 soldés.")
    add("ACH-SERVICE", "2025-02-10", "AC", "Prestation fournisseur12000HT", [line("6125", 12000), line("34552", 2400), line("4411", credit=14400, tiers="F-SERVICE")], "Facturation", "Factures → Achat ; F-SERVICE ;10/02/2025 ; référence ACH-SERVICE ; échéance15/02/2025 ; article S-ACH quantité1 PU12 000 TVA20 %, compte achat6125 confirmé. Valider, comptabiliser, valider l'écriture.")
    add("AV-01", "2025-02-10", "AV", "Retour10 unités après règlement intégral VENTE-01", [line("7111", 2500), line("4455", 500), line("3421", credit=3000, tiers="C-MARCH")], "Facturation", "Factures → VENTE-01 → Créer un avoir ;10/02/2025 ; nature Retour, quantité10 PU250, TVA20 %, retour stock coché. Valider/comptabiliser l'avoir, puis valider l'écriture AV au Journal. Crédit disponible3 000 ; stock110 unités, CMUP110. Aucun remboursement dans ce parcours.", "Réduction TVA facturée500 et ventes2 500.")
    add("ACH-SERVICE-PAY", "2025-02-15", "BQ", "Règlement fournisseur services", [line("4411", 14400, tiers="F-SERVICE"), line("5141", credit=14400)], "Paiements", "Factures → ACH-SERVICE → Payer14 400 le15/02/2025, virement, référence PAY-SERVICE ; valider l'écriture. TVA déductible2 400 en février.")
    add("VENTE-02", "2025-03-01", "VT", "Vente50 marchandises à300HT", [line("3421", 18000, tiers="C-MARCH"), line("7111", credit=15000), line("4455", credit=3000)], "Facturation", "Factures → Vente ; C-MARCH ;01/03/2025 ; référence VENTE-02 ; échéance15/05/2025 ; M-01 quantité50 PU300 TVA20 %. Valider/comptabiliser et valider au Journal. Stock60 unités.", "TVA collectée3 000 ; application du crédit d'avoir n'ajoute aucune TVA.")
    add("EFF-F01", "2025-03-01", "BQ", "Effet fournisseur14400", [line("4411", 14400, tiers="F-MARCH"), line("4415", credit=14400, tiers="F-MARCH")], "Paiements", "Factures → ACH-02 → Payer ; Effet14 400,01/03/2025, échéance20/03/2025, référence EFF-F01. Valider l'écriture ; dette transférée4415, aucune sortie banque avant paiement.")
    add("VENTE-02-PAY", "2025-03-05", "BQ", "Virement client après imputation créditAV01", [line("5141", 5000), line("3421", credit=5000, tiers="C-MARCH")], "Paiements", "D'abord Avoirs → AV-01 → Imputer crédit3 000 sur VENTE-02 le01/03/2025 : aucune nouvelle écriture si même compte/tiers ; l'avoir avait déjà réduit3421. Puis Factures → VENTE-02 → Encaisser5 000 le05/03/2025 ; reste10 000 ; valider l'écriture.")
    add("EFF-F01-PAY", "2025-03-20", "BQ", "Paiement effet fournisseur", [line("4415", 14400, tiers="F-MARCH"), line("5141", credit=14400)], "Paiements", "Effets & Chèques → EFF-F01 → Confirmer paiement ; date effective20/03/2025 ; valider l'écriture. Dette4415 soldée ; TVA ACH-02 récupérable2 400 en mars.")
    add("EFF-C01", "2025-04-01", "BQ", "Effet client10000", [line("3425", 10000, tiers="C-MARCH"), line("3421", credit=10000, tiers="C-MARCH")], "Paiements", "Factures → VENTE-02 → Encaisser ; Effet10 000,01/04/2025, échéance15/05/2025, référence EFF-C01 ; valider l'écriture. Contrôler3425, pas de banque.")
    add("EFF-C01-REM", "2025-05-15", "AE", "Remise effet client", [line("51132", 10000), line("3425", credit=10000, tiers="C-MARCH")], "Paiements", "Effets & Chèques → EFF-C01 → Remettre ; dans la modale saisir Date réelle de l'opération 15/05/2025, frais 0 ; confirmer puis valider l'écriture ; vérifier le compte 51132 effectivement utilisé par le produit.")
    add("EFF-C01-ENC", "2025-05-16", "BQ", "Encaissement effet avec frais10", [line("5141", 9990), line("61472", 10), line("51132", credit=10000)], "Paiements", "Effets & Chèques → EFF-C01 → Confirmer encaissement ; date16/05/2025, frais10 ; valider l'écriture. Banque9 990, frais10, créance commerciale soldée.")
    add("AC-C01", "2025-06-01", "BQ", "Acompte client prestations24000TTC", [line("5141", 24000), line("4421", credit=24000, tiers="C-SERVICE")], "Paiements", "Acomptes → Client C-SERVICE,01/06/2025,24 000 TTC, virement, référence AC-C01, TVA applicable20 %, comptabiliser. Valider au Journal.", "Acompte20 000HT+4 000TVA ; pas de double taxation après facture finale.")
    add("VENTE-SERVICE", "2025-06-15", "VT", "Prestation client120000HT", [line("3421", 144000, tiers="C-SERVICE"), line("7124", credit=120000), line("4455", credit=24000)], "Facturation", "Factures → Vente ; C-SERVICE personne morale privée ;15/06/2025 ; référence VENTE-SERVICE ; échéance30/06/2025 ; S-VTE quantité1 PU120 000 TVA20 %, compte7124, RAS0. Valider/comptabiliser puis valider au Journal.", "TVA totale de l'opération24 000, acompte compris.")
    add("AC-C01-IMP", "2025-06-15", "OD", "Imputation acompte client", [line("4421", 24000, tiers="C-SERVICE"), line("3421", credit=24000, tiers="C-SERVICE")], "Paiements", "Acomptes → AC-C01 → Imputer sur VENTE-SERVICE,24 000,15/06/2025, comptabilisation cochée ; valider l'écriture. Reste120 000.")
    add("VENTE-SERVICE-PAY", "2025-06-30", "BQ", "Solde client prestation", [line("5141", 120000), line("3421", credit=120000, tiers="C-SERVICE")], "Paiements", "Factures → VENTE-SERVICE → Encaisser120 000 le30/06/2025, virement, référence PAY-VS ; valider l'écriture ; facture soldée.")
    add("TVA-06-PAY", "2025-07-20", "BQ", "Paiement TVA juin19900", [line("4456", 19900), line("5141", credit=19900)], "Fiscalité", "Après préparation et comptabilisation TVA de janvier à juin selon la feuille TVA, Journal → BQ20/07/2025, référence TVA-06-PAY ; saisir D4456=19 900 C5141=19 900 ; valider. La déclaration ne génère pas ce paiement à elle seule.")
    add("INT-PPRF", "2025-11-30", "BQ", "Intérêts bancaires selon attestation fictive", [line("5141", 800), line("3453", 200), line("7381", credit=1000)], "Fiscalité", "Journal → BQ30/11/2025 référence INT-PPRF ; avis banque fictif : intérêts bruts1 000, retenue200, net800 ; saisir les trois lignes puis valider. Ces montants viennent du justificatif du jeu de recette, aucun taux n'est extrapolé à un dossier réel.", "Produit financier1 000 ; crédit IS documentaire200 à enregistrer séparément dans Fiscalité IS.")
    add("ASS-01", "2025-12-01", "BQ", "Assurance12000 couvrant décembre2025 à novembre2026", [line("6134", 12000), line("5141", credit=12000)], "Comptabilité", "Journal → BQ01/12/2025 référence ASS-01 ; contrat fictif couvrant01/12/2025–30/11/2026, prime12 000, aucune TVA sur cet avis. Saisir D6134 C5141 puis valider.")
    for ref in ("02", "002"):
        add("REF-"+ref, "2025-12-02", "AC", "Achat de contrôle référence littérale"+ref, [line("6125", 200), line("34552", 40), line("4411", credit=240, tiers="F-CONTROLE")], "Facturation", f"Factures → Achat F-CONTROLE ; date02/12/2025, référence fournisseur exactement {ref}, échéance31/12/2025 ; S-ACH quantité1 PU200 TVA20 %. Valider/comptabiliser, valider au Journal. Ne pas payer. Les deux pièces ont même tiers/date/TTC mais des références distinctes.", "TVA comptabilisée40 par facture ; non récupérée tant que non payée dans ce scénario.")
    add("VENTE-IMPAYEE", "2025-12-10", "VT", "Prestation12000HT laissée impayée", [line("3421", 14400, tiers="C-IMPAYE"), line("7124", credit=12000), line("4455", credit=2400)], "Facturation", "Factures → Vente C-IMPAYE ;10/12/2025 ; référence VENTE-IMPAYEE ; échéance20/12/2025 ; S-VTE quantité1 PU12 000 TVA20 % RAS0 ; valider/comptabiliser, valider au Journal.", "Régime débit : TVA2 400 due même sans encaissement ; variante encaissement sur copie séparée.")
    add("CHQ-REJET", "2025-12-12", "BQ", "Chèque2000 provisoire sur facture impayée", [line("51111", 2000), line("3421", credit=2000, tiers="C-IMPAYE")], "Paiements", "Factures → VENTE-IMPAYEE → Encaisser ; chèque2 000,12/12/2025, numéro CHQ-REJET. Valider au Journal ; puis utiliser le cas suivant de rejet.")
    add("CHQ-REJET-INV", "2025-12-15", "BQ", "Rejet documenté chèque sans frais", [line("3421", 2000, tiers="C-IMPAYE"), line("51111", credit=2000)], "Paiements", "Effets & Chèques → CHQ-REJET → Rejeter ; dans la modale saisir Date réelle de l'opération 15/12/2025, motif Provision insuffisante, frais 0 ; confirmer. Valider l'écriture ; solde facture 14 400, banque inchangée.")
    add("AMENDE", "2025-12-20", "BQ", "Amende fiscale documentée500", [line("6583", 500), line("5141", credit=500)], "Fiscalité", "Journal → BQ20/12/2025 référence AMENDE ; D6583=500 C5141=500 ; valider. Contrôler dans Fiscalité IS que la réintégration automatique500 existe ; ne pas la saisir une deuxième fois.", "Réintégration automatique500 ; aucune TVA.")
    add("FRAIS-BQ", "2025-12-31", "BQ", "Frais bancaires60 sans TVA selon avis", [line("61473", 60), line("5141", credit=60)], "Banques", "Depuis l'avis fictif, constater Journal → BQ31/12/2025 référence FRAIS-BQ, D61473=60 C5141=60 ; valider. Rapprocher la ligne débit 60 seulement au cas de rapprochement, après import du relevé. Le scénario avis ne comporte aucune TVA ; ne pas appliquer une exclusion générale à tous les frais réels.")
    add("STOCK-FIN", "2025-12-31", "OD", "Stock final60 unités àCMUP110", [line("3111", 6600), line("6114", credit=6600)], "Stocks", "Inventaire & stock → Inventaire physique au 31/12/2025 ; M-01 quantité physique 60, CMUP 110, stock théorique 60 ; valider. Onglet Rapprochement → Comptabilisation du stock final ; vérifier exercice 2025, date 31/12/2025, comptes 3111/6114 et montant 6 600 ; générer puis valider l'écriture au Journal. Ne pas générer deux fois la variation.", "Achats revendus22 000−6 600=15 400.")
    add("AMORT-2025", "2025-12-31", "AM", "Dotation annuelle ordinateur4800", [line("61935", 4800), line("28355", credit=4800)], "Immobilisations", "Immobilisations → IMMO-01 → plan annuel2025 → Générer l'écriture ; valider au Journal. Contrôler dotation4 800, brut24 000, VNC19 200. Ne pas relancer la génération si la dotation existe.", "Durée de test5 ans, linéaire ; hypothèse fiscale déductible documentée du scénario.")
    add("CCA-2025", "2025-12-31", "OD", "Charge constatée d'avance11000", [line("3491", 11000), line("6134", credit=11000)], "Inventaire clôture", "Clôture → Ajouter un ajustement → CCA ; montant11 000 ; charge6134 ; contrepartie3491 ; libellé Assurance ASS-01,11 mois2026 ; enregistrer puis valider au Journal. Conserver la contrepassation prévue2026 en brouillon jusqu'à vérification.", "Charge assurance de l'exercice1 000, pas12 000.")
    add("FNP-2025", "2025-12-31", "OD", "Facture non parvenue3000", [line("6125", 3000), line("4417", credit=3000)], "Inventaire clôture", "Clôture → Ajustement FNP ; montant3 000HT ; charge6125 ; contrepartie4417 ; libellé Service livré décembre, contrat FNP-01 ; enregistrer/valider. Aucune TVA forcée par l'assistant.", "Charge2025=3 000 ; TVA à traiter avec la vraie facture2026.")
    add("PROV-RISQUE", "2025-12-31", "OD", "Provisiondurable litige1500", [line("61955", 1500), line("1518", credit=1500)], "Inventaire clôture", "Clôture → Provision risques et charges ; montant1 500 ; dotation61955 ; contrepartie1518 ; noteLitige REC-LIT01 probable mais conditions fiscales non satisfaites dans ce cas fictif ; enregistrer/valider.", "Réintégration manuelle1 500, seulement après confirmation du cas fictif ; aucune déduction automatique.")
    add("DEPR-CLIENT", "2025-12-31", "OD", "Dépréciation créance2000", [line("61964", 2000), line("3942", credit=2000)], "Inventaire clôture", "Clôture → Dépréciation client ; montant2 000 ; dotation61964 ; contrepartie3942 ; libelléDépréciation VENTE-IMPAYEE selon justificatifREC-DEP01 ; enregistrer/valider. La créance brute reste14 400.", "Scénario : dépréciation comptable justifiée mais conditions fiscales non satisfaites ; réintégration2 000 confirmée manuellement.")
    # Journaux réellement utilisés par le cycle du règlement (routers/commercial.py).
    for e in rows:
        if e["reference_recette"] in {"CHQ-01", "CHQ-01-REM", "EFF-F01", "EFF-C01", "CHQ-REJET"}:
            e["journal"] = "AE"
        if e["reference_recette"] == "CHQ-REJET-INV":
            e["journal"] = "OD"
    # La FAE est une variante indépendante : l'assistant et la préparation TVA
    # ne prouvent pas sa qualification. Aucun montant incertain n'entre dans
    # l'oracle principal et aucun résultat attendu n'impose de masquer ce manque.
    return rows


def tva_operations():
    return [
        {"reference_recette":"TVA-01", "date":"2025-01-31", "journal":"OD", "description":"Crédit TVA janvier1 800", "lignes":[line("4455",5000),line("3456",1800),line("34551",credit=4800),line("34552",credit=2000)]},
        {"reference_recette":"TVA-02", "date":"2025-02-28", "journal":"OD", "description":"Augmentation crédit TVA février2 900", "lignes":[line("3456",2900),line("4455",credit=500),line("34552",credit=2400)]},
        {"reference_recette":"TVA-03", "date":"2025-03-31", "journal":"OD", "description":"Consommation crédit TVA mars600", "lignes":[line("4455",3000),line("34552",credit=2400),line("3456",credit=600)]},
        {"reference_recette":"TVA-06", "date":"2025-06-30", "journal":"OD", "description":"TVA nette juin19 900", "lignes":[line("4455",24000),line("3456",credit=4100),line("4456",credit=19900)]},
        {"reference_recette":"TVA-12", "date":"2025-12-31", "journal":"OD", "description":"TVA nette décembre2 400", "lignes":[line("4455",2400),line("4456",credit=2400)]},
    ]


def balances(entries):
    result = defaultdict(lambda:{"debit":Decimal(0),"credit":Decimal(0)})
    for entry in entries:
        d = sum((dec(x["debit"]) for x in entry["lignes"]), Decimal(0))
        c = sum((dec(x["credit"]) for x in entry["lignes"]), Decimal(0))
        if d != c:
            raise ValueError(f"Écriture déséquilibrée {entry['reference_recette']} : {d} / {c}")
        for x in entry["lignes"]:
            result[x["compte"]]["debit"] += dec(x["debit"])
            result[x["compte"]]["credit"] += dec(x["credit"])
    return dict(result)


def oracle(entries):
    """Calculs pédagogiques indépendants, vérifiables avec la balance jointe."""
    b = balances(entries)
    net = lambda c: b.get(c,{"debit":0,"credit":0})["debit"]-b.get(c,{"debit":0,"credit":0})["credit"]
    produits = -sum((x["debit"]-x["credit"] for c,x in b.items() if c.startswith("7")), Decimal(0))
    charges = sum((x["debit"]-x["credit"] for c,x in b.items() if c.startswith("6") and not c.startswith("67")), Decimal(0))
    avant_is = produits-charges
    reintegrations = Decimal("4000.00")
    fiscal = avant_is+reintegrations
    is_due = dec(fiscal*Decimal("0.175"))
    resultat_net = avant_is-is_due
    stock_qty = Decimal("200")-Decimal("100")+Decimal("10")-Decimal("50")
    cmup = (Decimal("100")*Decimal("100")+Decimal("100")*Decimal("120"))/Decimal("200")
    actif = net("2355")+net("28355")+net("3111")+net("3421")+net("3427")+net("3942")+net("34552")+net("3491")+net("5141")+net("3453")
    dettes = -sum((net(c) for c in ("1518","4411","4417","4453","4456")),Decimal(0))
    marge = -net("7111")-net("6111")-net("6114")
    production = -net("7124")
    va = marge+production-sum((net(c) for c in ("6125","6134","61472","61473")),Decimal(0))
    exploitation = va-sum((net(c) for c in ("61935","61955","61964")),Decimal(0))
    tva_collectee = sum((dec(l["credit"])-dec(l["debit"]) for e in entries if not e["reference_recette"].startswith("TVA-") for l in e["lignes"] if l["compte"]=="4455"),Decimal(0))
    tva_recuperable = sum((dec(l["credit"])-dec(l["debit"]) for e in entries if e["reference_recette"].startswith("TVA-") and e["journal"]=="OD" for l in e["lignes"] if l["compte"] in ("34551","34552")),Decimal(0))
    cm_base = -net("7111")-net("7124")-net("7381")
    return {"produits":str(dec(produits)),"charges_hors_is":str(dec(charges)),"resultat_avant_is":str(dec(avant_is)),
            "reintegrations":str(reintegrations),"deductions":"0.00","deficits_imputes":"0.00","benefice_fiscal":str(dec(fiscal)),
            "taux_is":"17.50","is_theorique":str(is_due),"credit_is":"200.00","acomptes_2025":"0.00","solde_is":str(is_due-Decimal("200")),
            "resultat_net":str(dec(resultat_net)),"stock_quantite":str(stock_qty),"stock_cmup":str(cmup),"stock_valeur":str(dec(stock_qty*cmup)),
            "banque":str(dec(net("5141"))),"creances_clients_brutes":str(dec(net("3421"))),"fournisseurs":str(dec(-net("4411"))),
            "tva_collectee_annuelle":str(dec(tva_collectee)),"tva_recuperable_annuelle":str(dec(tva_recuperable)),"tva_nette_annuelle":str(dec(tva_collectee-tva_recuperable)),"tva_payee_N":"19900.00","tva_due_fin_N":str(dec(-net("4456"))),
            "marge_brute":str(dec(marge)),"production":str(dec(production)),"valeur_ajoutee":str(dec(va)),"resultat_exploitation":str(dec(exploitation)),"resultat_financier":str(dec(-net("7381"))),"resultat_non_courant":str(dec(-net("6583"))),
            "caf":str(dec(resultat_net+net("61935")+net("61955"))),"cm_base":str(dec(cm_base)),"cm_calculee_sans_exoneration":str(dec(cm_base*Decimal("0.0025"))),"cm_minimum_sans_exoneration":"3000.00",
            "total_actif_net":str(dec(actif)),"dettes_et_provisions":str(dec(dettes)),"total_passif_net":str(dec(Decimal("200000")+resultat_net+dettes))}


def build_data():
    entries = operations()+tva_operations()
    o = oracle(entries)
    # La clôture sait générer l'IS si absent ; le parcours le constate une fois
    # avant fermeture pour permettre le contrôle des soldes puis la liquidation.
    entries += [{"reference_recette":"IS-2025", "date":"2025-12-31", "journal":"OD", "description":"IS attendu à constater une seule fois", "lignes":[line("6701",o["is_theorique"]),line("4453",credit=o["is_theorique"])]},
                {"reference_recette":"PPRF-IMP", "date":"2025-12-31", "journal":"OD", "description":"Imputation documentaire retenue200", "lignes":[line("4453",200),line("3453",credit=200)]}]
    o = oracle(entries)
    company = {"raison_sociale":"ATLAS RECETTE HISABPRO SARL — FICTIVE", "forme_juridique":"SARL", "ville":"Casablanca", "adresse":"1 rue du Scénario, adresse fictive", "capital_social":"200000.00", "devise":"MAD", "identifiant_fiscal":"99000001", "ice":"009900000000001", "rc":"RECETTE-2025", "patente":"99000002", "exercice_debut":2025, "regime_fiscal":"is", "regime_tva":"debit", "periodicite_tva":"mensuelle", "email":"admin@hisabpro-recette.example", "password_test":"Recette!Atlas2025", "nom_admin":"Administrateur Recette", "avertissement":"Identité, identifiants et justificatifs entièrement fictifs, réservés à une base isolée. Aucune preuve d'attribution par une administration ; aucun dépôt réel."}
    tiers = [
        {"code":"C-MARCH","nom":"Client Marchandises Recette","type":"client","compte":"3421","auxiliaire":"C-MARCH"},
        {"code":"C-SERVICE","nom":"Client Services Recette","type":"client","compte":"3421","auxiliaire":"C-SERVICE"},
        {"code":"C-IMPAYE","nom":"Client Impayé Recette","type":"client","compte":"3421","auxiliaire":"C-IMPAYE"},
        {"code":"F-MARCH","nom":"Fournisseur Marchandises Recette","type":"fournisseur","compte":"4411","auxiliaire":"F-MARCH"},
        {"code":"F-SERVICE","nom":"Fournisseur Services Recette","type":"fournisseur","compte":"4411","auxiliaire":"F-SERVICE"},
        {"code":"F-CONTROLE","nom":"Fournisseur Contrôle Références Recette","type":"fournisseur","compte":"4411","auxiliaire":"F-CONTROLE"},
        {"code":"F-IMMO","nom":"Fournisseur Informatique Recette","type":"fournisseur","compte":"4481","auxiliaire":"F-IMMO"},
    ]
    articles = [
        {"code":"M-01","designation":"Marchandise de recette","type":"produit","stock_initial":0,"prix_achat":100,"prix_vente":250,"tva":20,"compte_achat":"6111","compte_vente":"7111","compte_stock":"3111","compte_variation":"6114"},
        {"code":"S-VTE","designation":"Prestation de recette","type":"service","stock_initial":0,"prix_vente":120000,"tva":20,"compte_vente":"7124"},
        {"code":"S-ACH","designation":"Fourniture/service non stocké recette","type":"service","stock_initial":0,"prix_achat":12000,"tva":20,"compte_achat":"6125"},
    ]
    for e in entries:
        for key in ("description","actions","impact_fiscal"):
            if key in e:e[key]=texte_lisible(e[key])
    for t in tiers:
        t["auxiliaire"]="Attribué automatiquement par HisabPro ; consigner le code réel."
    company["date_constitution_fictive"]="2025-01-01"
    company["date_debut_exploitation_fictive"]="2025-01-01"
    company["concession_service_public"]="Non, hypothèse explicite du scénario"
    journal = []
    for e in sorted(entries,key=lambda x:(x["date"],x["reference_recette"])):
        for x in e["lignes"]:
            journal.append({"reference_recette":e["reference_recette"],"date":e["date"],"journal":e["journal"],"libelle":e["description"],**x})
    bank = [{"Date":e["date"],"Libellé":e["reference_recette"]+" — "+e["description"],"Débit":x["credit"],"Crédit":x["debit"]} for e in entries for x in e["lignes"] if x["compte"]=="5141"]
    bank.sort(key=lambda x:(x["Date"],x["Libellé"]))
    variant_fae={"reference":"FAE-01","statut":"Bloqué","exclue_du_scenario_principal":True,"condition":"Qualification documentée préalable : prestation taxable à 20 %, régime débit et fait générateur en 2025 ; aucun montant n'est applicable avant cette décision.","ecriture_conditionnelle":{"reference_recette":"FAE-VARIANTE","date":"2025-12-31","journal":"OD","description":"FAE taxable sous qualification explicite","lignes":[line("3427",7200),line("7124",credit=6000),line("4455",credit=1200)]},"deltas_conditionnels":{"produits":"6000.00","tva_collectee":"1200.00","is_theorique":"1050.00","resultat_net":"4950.00","total_actif_net":"7200.00"},"attendus_conditionnels":{"resultat_avant_is":"135830.00","benefice_fiscal":"139830.00","is_theorique":"24470.25","solde_is":"24270.25","resultat_net":"111359.75","tva_collectee_annuelle":"35100.00","tva_due_fin_N":"3600.00","total_actif_net":"344210.00","caf":"117659.75"}}
    return {"titre":TITLE,"version":VERSION,"societe":company,"tiers":tiers,"articles":articles,"banque":{"banque":"Banque Recette","compte_comptable":"5141","rib":"000000000000000000000001","rib_fictif":True,"solde_initial":"0.00","solde_final":o["banque"]},"operations":entries,"journal_attendu":journal,"releve_bancaire":bank,"attendus":o,"variantes_independantes":[variant_fae],"references_officielles":SOURCES,
            "tva_mois":[{"mois":"01","credit_ouverture":"0.00","collectee":"5000.00","recuperable":"6800.00","credit_fin":"1800.00","due":"0.00"},{"mois":"02","credit_ouverture":"1800.00","collectee":"-500.00","recuperable":"2400.00","credit_fin":"4700.00","due":"0.00"},{"mois":"03","credit_ouverture":"4700.00","collectee":"3000.00","recuperable":"2400.00","credit_fin":"4100.00","due":"0.00"},*[{"mois":m,"credit_ouverture":"4100.00","collectee":"0.00","recuperable":"0.00","credit_fin":"4100.00","due":"0.00"} for m in ("04","05")],{"mois":"06","credit_ouverture":"4100.00","collectee":"24000.00","recuperable":"0.00","credit_fin":"0.00","due":"19900.00"},*[{"mois":m,"credit_ouverture":"0.00","collectee":"0.00","recuperable":"0.00","credit_fin":"0.00","due":"0.00"} for m in ("07","08","09","10","11")],{"mois":"12","credit_ouverture":"0.00","collectee":"2400.00","recuperable":"0.00","credit_fin":"0.00","due":"2400.00"}]}


def entry_text(e):
    return "; ".join(f"{x['compte']} {'D '+mad(x['debit']) if dec(x['debit']) else 'C '+mad(x['credit'])}"+(f" [tiers {x['tiers']}]" if x.get("tiers") else "") for x in e["lignes"])


def build_cases(data):
    cases = []
    counts = defaultdict(int)
    prefixes = dict(zip(DOMAINS,("ADM","FAC","PAY","CPT","BNQ","STK","IMM","FIS","CLO","ETA","LIA","SEC","EXP","NEG")))
    def add(module, objectif, donnees, actions, attendu, prerequis="Base de recette isolée ; suivre les cas dans l'ordre.", ecritures="Aucune nouvelle écriture.", fiscal="Sans incidence fiscale directe.", controles="Vérifier écran, sauvegarde puis rechargement ; consigner toute différence.", statut="Non testé", observations="", preuve="Capture du résultat et référence de la pièce."):
        if statut=='Bloqué' and controles=="Vérifier écran, sauvegarde puis rechargement ; consigner toute différence.":
            controles="Consigner le motif de blocage et le prérequis manquant ; aucune saisie ou validation définitive avant résolution documentée."
        counts[module] += 1
        cases.append({"ordre":len(cases)+1,"id":f"HP-{prefixes[module]}-{counts[module]:03}","module":module,"objectif":objectif,"prerequis":prerequis,"donnees":donnees,"actions":actions,"attendu":attendu,"ecritures":ecritures,"fiscal":fiscal,"controles":controles,"statut":statut,"observations":observations,"preuve":preuve,"resultat_reel":"","anomalies":"","preuve_reelle":""})
    add("Exploitation","Préparer un environnement vierge isolé","Base PostgreSQL dédiée hisabpro_recette ; aucun identifiant de production ; fichiers joints fictifs uniquement.","Administrateur technique : suivre la procédure d'installation livrée, vérifier la cible de connexion et appliquer uniquement les migrations nécessaires dans la copie isolée. Lancer backend/frontend ; transmettre une URL de recette à l'utilisateur.","Application accessible, aucune société métier réelle, migrations effectivement appliquées et répertoriées.",controles="Contrôler nom de base, paramètres de connexion sans partager les secrets ; sauvegarde initiale ; aucune commande DROP/TRUNCATE contre une base réelle.",preuve="Capture URL de recette + rapport des migrations, identifiants masqués.")
    add("Administration","Créer société et administrateur",json.dumps(data["societe"],ensure_ascii=False,indent=2),"Connexion → Créer un compte ; nom Administrateur Recette, raison sociale ATLAS RECETTE HISABPRO SARL — FICTIVE, ville Casablanca, email admin@hisabpro-recette.example, mot de passe Recette!Atlas2025 ; enregistrer.","Connexion immédiate avec rôle administrateur ; société sélectionnée ; modules facturation/comptabilité disponibles. Mot de passe réservé au laboratoire.")
    add("Administration","Compléter identité et paramètres", "IF99000001, ICE009900000000001, TP99000002, RC RECETTE-2025 ; SARL ; capital200000 ; adresse fictive ; MAD ; premier exercice2025 ; IS ; TVA au débit ; périodicité mensuelle.","Paramètres → Fiche société ; saisir toutes ces valeurs et enregistrer. Quitter la page puis revenir. Préparer et sélectionner l'exercice 2025 au cas suivant, s'il n'existe pas encore.","Valeurs persistantes, zéros de l'ICE conservés. La modification du paramètre premier exercice ne prouve pas la création d'un exercice comptable. Identifiants fictifs ne valent pas attribution fiscale.",fiscal="Le régime au débit est une hypothèse explicite du laboratoire ; sur dossier réel, vérifier l'option applicable.")
    add("Administration","Exercices et périodes", "2025 : 01/01/2025–31/12/2025 ; 2026 : 01/01/2026–31/12/2026.","Comptabilité → Clôture → Gestion des exercices ; vérifier 2025 et 2026. Si 2025 absent : Créer un exercice ; année de clôture 2025, début 01/01/2025, clôture 31/12/2025 ; Créer cet exercice. Sélectionner 2025 ; Préparer l'exercice suivant seulement si 2026 absent. Vérifier les 12 périodes ouvertes.","Dates exactes, 12 périodes, pas de chevauchement. L'exercice 2026 éventuellement créé à l'inscription n'est pas recréé.")
    add("Administration","Plan comptable et journaux", "Comptes du journal_attendu.csv ; journauxAC,VT,AV,BQ,AE,OD,AM,CL,AN.","Plan de comptes : contrôler chaque compte de l'annexe Balance ; activer un compte existant s'il manque au plan société. Journal → Nouvelle écriture : vérifier liste des journaux et libellé du compte après sélection ; annuler ce brouillon de contrôle.","Tous les comptes du scénario disponibles ; subdivisions51111/51112/51132 identifiables ; aucune suppression de comptes utilisés.")
    add("Administration","Compte bancaire",json.dumps(data["banque"],ensure_ascii=False),"Paramètres → Comptes bancaires → Ajouter ; Banque Recette, RIB000000000000000000000001, compte5141, actif ; enregistrer et rouvrir.","Compte5141 disponible pour règlements et rapprochement. RIB purement fictif.")
    for t in data["tiers"]:
        add("Administration","Créer tiers "+t["code"],json.dumps(t,ensure_ascii=False),f"Clients / Fournisseurs → Nouveau ; nom {t['nom']}, type {t['type']}, code de recette {t['code']} dans notes si aucun champ code ; Paramétrage comptable → compte {t['compte']} ; enregistrer. Consigner son identifiant et son code auxiliaire automatiquement attribué.","Tiers de cette société uniquement ; compte correct ; auxiliaire généré par HisabPro. Les codes C-MARCH/F-MARCH du cahier sont des repères symboliques, pas des auxiliaires imposés.")
    for a in data["articles"]:
        add("Administration","Créer article "+a["code"],json.dumps(a,ensure_ascii=False),f"Articles → Nouvel article ; code {a['code']}, désignation {a['designation']}, prix/TVA/comptes indiqués ; choisir {'Article stockable, stock initial0' if a['type']=='produit' else 'Service / frais, unité forfait'} ; enregistrer puis rouvrir.","Comptes et TVA persistants ; S-VTE/S-ACH non stockables ; M-01 stock0 avant achats.")
    add("Administration","Créer utilisateurs de recette", "comptable@hisabpro-recette.example rôlecomptable ; lecture@hisabpro-recette.example rôlelecture ; mots de passe Recette!Compta2025 et Recette!Lecture2025.","Paramètres → Utilisateurs → Ajouter un utilisateur ; créer les deux comptes. Se déconnecter puis vérifier chaque connexion, revenir à l'administrateur.","Rôles reçus du serveur ; lecteur consulte, comptable saisit ; administration utilisateurs réservéeadmin.")
    add("Administration","Seconde société isolée", "ATLAS RECETTE B — FICTIVE ; adminb@hisabpro-recette.example ; Recette!AtlasB2025 ; aucune transaction.","Créer cette société avec un autre compte depuis Créer un compte, puis reconnecter l'administrateur A. Vérifier le sélecteur et les seuls accès autorisés ; ne pas partager un accès sans action explicitement disponible.","Aucun tiers, facture, pièce jointe ou solde deA visible dansB et inversement.")
    add("Facturation","Devis et conversionBC", "Date15/01/2025 ; clientC-MARCH ; M-01 quantité100 PU250 TVA20 % ; validité30 jours ; note REC-DV01.","Cycle commercial → Devis → Nouveau devis ; saisir la ligne, enregistrer et ouvrir PDF. Marquer accepté si ce statut est exposé ; Créer BC depuis le devis ; date18/01/2025, conserver lignes, noteREC-BC01.","Devis/BC : HT25 000, TVA5 000, TTC30 000 ; liens sources présents ; aucune écriture et aucun stock au devis/BC.",ecritures="Aucune à cette étape ; l'écriture intervient à la facture comptabilisée.")
    core_ops=[e for e in data["operations"] if e.get("actions") and e["reference_recette"]!="TVA-06-PAY"]
    # Actions d'inventaire / fiscalité sont placées après le cycle courant.
    end_refs={"STOCK-FIN","AMORT-2025","CCA-2025","FNP-2025","PROV-RISQUE","DEPR-CLIENT"}
    # Le tri stable conserve l'ordre métier des opérations du même jour :
    # créer la facture avant d'imputer son acompte, puis contrôler le solde.
    core_ops.sort(key=lambda e:(e["reference_recette"] in end_refs,e["date"]))
    for e in core_ops:
        expected=entry_text(e)
        add(e["domaine"],e["description"],f"Repère {e['reference_recette']} ; date comptable/date de pièce {e['date']} ; journal {e['journal']}. {expected}",e["actions"],"Écriture conforme : "+expected+". Une seule génération, montants égaux au centime ; pièce/source et tiers conservés.",ecritures=expected,fiscal=e["impact_fiscal"],controles="Comparer total débit/crédit, date, journal, référence justificative, tiers/auxiliaire ; vérifier statut validé au Journal. La validation commerciale et la validation comptable sont deux opérations distinctes quand le produit les expose.",observations="Numéros internes attribués par le logiciel : les recopier dans la preuve. Ne jamais forcer un ID technique pour égaler le repère du cahier.")
    for r in data["tva_mois"]:
        add("Fiscalité","Déclaration TVA mois "+r["mois"],f"Exercice 2025 ; mois {r['mois']} ; crédit d'ouverture {mad(r['credit_ouverture'])} ; prorata 100 %. Collectée {mad(r['collectee'])}, récupérable {mad(r['recuperable'])}, crédit fin {mad(r['credit_fin'])}, due {mad(r['due'])}.",f"Déclaration TVA → 2025 → Mensuelle → mois {r['mois']}. Lire Synthèse puis Détail/DGI ; contrôler les pièces sources, les dates effectives et le crédit reporté ; télécharger l'export disponible. Ne pas déposer auprès de la DGI depuis ce laboratoire.","Montants exactement indiqués ; les mois intermédiaires sans mouvement conservent le crédit et n'ajoutent aucune taxe.",fiscal="Calcul TVA du laboratoire ; aucun RAS TVA article117, aucune déduction sur02/002 non payées. Ne pas interpréter la simulation annuelle comme une déclaration annuelle obligatoire.")
    for e in tva_operations():
        add("Fiscalité","Comptabiliser "+e["description"],f"Date{e['date']}, journalOD, référence{e['reference_recette']}. "+entry_text(e),"Journal → Nouvelle écriture ; saisir les lignes exactes, date de pièce=date comptable, référence de recette ; enregistrer et valider. Ne pas reconstituer une taxe déjà comptabilisée par un autre flux.","Comptes TVA concordants avec le détail mensuel ; au31/12 :4455=0,34551=0,34552 débiteur80,3456=0,4456 créditeur2 400 après paiement juin.",ecritures=entry_text(e),fiscal="Constat comptable des déclarations de contrôle ; la page TVA ne remplace pas ces écritures.")
    e=next(x for x in data["operations"] if x["reference_recette"]=="TVA-06-PAY")
    add("Fiscalité",e["description"],"BQ20/07/2025 ; référenceTVA-06-PAY ;19 900.",e["actions"],"Banque287 730 après toutes les opérations du parcours ; TVA restant due au31/12=2 400.",ecritures=entry_text(e))
    add("Banques","Importer relevé Excel/CSV fourni", "releve_banque_recette_2025.xlsx ou .csv ; période01/01/2025–31/12/2025 ; soldeinitial0 ; soldefinal287 730 ; Banque Recette5141.","Rapprochement bancaire → compte5141 → dates annuelles ; saisir soldes0/287730 ; onglet Import Excel / CSV → sélectionner le fichier XLSX fourni, prévisualiser et Enregistrer. Pour CSV utiliser l'import si la bibliothèque le lit ; sinon consigner la limitation sans convertir arbitrairement les montants.","Une ligne par mouvement bancaire réel du jeu ; créditrelevé=entrée banque (débit5141), débitrelevé=sortie banque (crédit5141) ; écartfinal0.",controles="Comparer nombre de lignes et sommes avec Relevé ; les transferts511/3425/4415 ne sont pas des mouvements banque.")
    add("Banques","Rapprocher toutes les lignes", "Références et montants du relevé joint ; une ligne bancaire par ligne5141.","Rapprochement → filtrer Non rapprochées ; sélectionner chaque mouvement et sa contrepartie du même montant/date/référence ; valider. Pour frais60, créer d'abord FRAIS-BQ selon le cas dédié. Recharger l'écran.","Toutes les lignes justifiées sont rapprochées ; aucun débit/crédit inverse ; soldecomptable=soldebancaire287 730 ; aucune écriture comptable supplémentaire au seul rapprochement.")
    add("Banques","Réimporter le relevé", "Même fichier et mêmes dates.","Import Excel → sélectionner le fichier une seconde fois → Enregistrer ; noter lignes créées/ignorées.","Doublons détectés/ignorés ; pas de double mouvement, soldes287 730 inchangés.")
    add("Comptabilité","Lettrer clients et fournisseurs soldés", "Compte3421 :C-MARCH,C-SERVICE ; compte4411 :F-MARCH,F-SERVICE ; exclure02/002 etC-IMPAYE.","Lettrage → exercice2025 →3421 → tiersC-MARCH ; sélectionner facture(s), règlement(s), avoir et mouvementseffet correspondant au groupe équilibré, puis Lettrer. RépéterC-SERVICE et4411 pour fournisseurs soldés ; vérifier somme sélectionnée0 avant chaque validation.","Groupes lettrés équilibrés et codes persistants ; C-IMPAYE reste14 400 ouvert, F-CONTROLE reste480 ; pas de lettrage entre tiers différents.")
    add("Comptabilité","Balance et grand livre avant constat d'IS", "balance_avant_is_2025.csv ; banque 287 730, clients 14 400, fournisseurs 480, stock 6 600, VNC ordinateur 19 200 ; crédit IS comptable 3453 = 200 avant imputation.","Balances → Générale → 2025 ; exporter. Grand livre → 5141 puis 3421/4411 ; comparer les lignes et soldes à balance_avant_is_2025.csv ; afficher les auxiliaires. Journal → filtre Brouillons : aucune écriture avant fermeture. Après les cas de constat d'IS et imputation, utiliser balance_attendue_2025.csv.","Total débit = crédit ; soldes au centime ; documents commerciaux, comptes collectifs et auxiliaires concordent. Avant IS, résultat 129 830.",controles="Ne pas comparer le TTC commercial au HT du CPC ; distinguer la dette transférée en 4415 de celle restant sur 4411.")
    add("Comptabilité","Joindre un justificatif sans modifier l'écriture définitive", "Fichier fourni justificatifs/CAP-01.pdf ; écriture CAP-01 validée : D5141 C1111 = 200 000, date 01/01/2025.","Journal → CAP-01 → Justificatifs → Joindre un fichier ; choisir CAP-01.pdf. Recharger le panneau puis télécharger la pièce, vérifier la fiche fictive et la référence CAP-01. Constater que la suppression d'une pièce d'écriture définitive n'est pas proposée.","Fichier conservé et téléchargeable ; trace documentaire ajoutée ; date, lignes, numéro et soldes de l'écriture définitive inchangés.",ecritures="Aucune nouvelle écriture ; simple complément documentaire distinct des lignes comptables.",preuve="Fiche fictive jointe, capture du panneau et comparaison avant/après des lignes définitives.")
    add("Fiscalité","Retraitements confirmés avant clôture", "Amende500 automatiquement ; provision61955=1 500 et dépréciation61964=2 000 non admises fiscalement dans les notes fictives ; déductions0 ; déficit0.","Résultat fiscal / IS →2025 : contrôler amende500 automatique ; dans Éléments à confirmer préparer/saisir uniquement les deux réintégrations1 500 et2 000, catégorie Provisions, comptes exacts61955/61964 et notes justifiant la décision du scénario. Ne pas doubler500.","Réintégrations4 000 ; résultatavantIS129 830 ; résultatfiscal133 830 ; taux17,5 % ; IS23 420,25.",fiscal="La non-déductibilité des provisions est une donnée explicite du scénario, pas une règle générale sur toutes les provisions.")
    add("Fiscalité","Enregistrer crédit PPRF", "TypePPRF,200 MAD, déjàimputéacomptes0, date30/11/2025, référenceINT-PPRF, attestation fictive intérêtsbruts1 000/net800/retenue200.","Résultat fiscal / IS → Retenues & crédits → saisir ces champs → Ajouter. Vérifier son justificatif et que l'ajout ne recrée pas INT-PPRF dans le Journal.","Crédit disponible200 ; liquidationprévisionnelle=23 420,25−200=23 220,25 ; aucune seconde écriture de produit.",fiscal="Montant repris de l'attestation fictive ; aucun crédit réel sans justificatif.")
    add("Fiscalité","Premier exercice : acomptes etCSS", "Premierexercice2025, aucune liquidation2024.","Résultat fiscal / IS → Acomptes puisCSS ; ne pas forcer une référence annuelle N-1 fictive. Vérifier les libellés et capturer les limitations.","Acomptes2025 : Non applicable / premier exercice selon le produit ;0 versement. CSS : référence historique manquante explicitement signalée ; ne pas la transformer en non due sans source.",fiscal="CSS premier exercice demeure une validation fiscale de dossier ; son absence de référence n'est pas une preuve de zéro légal.")
    add("Fiscalité","CM et qualification d'exonération", "Base CM 170 500 ; calcul 0,25 % = 426,25 ; minimum 3 000 hors exonération. Hypothèse explicite : constitution et début d'exploitation 01/01/2025, aucun service public concédé.","Résultat fiscal / IS → Paramètres → CM : vérifier base et calcul. Dans le laboratoire, cocher Exonération totale de cotisation minimale et saisir la justification : CGI article 144-I-C-1 ; constitution et exploitation 01/01/2025 ; hors concession de service public ; justificatif REC-CM01. Enregistrer. Sur copie de contrôle non exonérée seulement, décocher et vérifier 3 000.","CM scénario = 0 sous ces hypothèses documentées ; copie non exonérée = 3 000. IS 23 420,25 supérieur dans les deux hypothèses. L'exonération réelle ne se déduit jamais du seul libellé Premier exercice.",observations="CGI 2026 complet lu sur reproduction institutionnelle CRI, article 144 pages imprimées 268–270. Qualification de chaque dossier réel à faire valider.",fiscal="Exonération 36 mois d'exploitation, limite 60 mois de constitution, hors concessionnaires de service public ; aucune modification réglementaire codée par le cahier.")
    for e in [x for x in data["operations"] if x["reference_recette"] in ("IS-2025","PPRF-IMP")]:
        add("Fiscalité",e["description"],entry_text(e),f"Journal → OD31/12/2025, référence{e['reference_recette']}, datepièce31/12/2025 ; saisir les lignes, enregistrer et valider. Contrôler la situation IS ; ne pas ajouter un second impôt si une écriture équivalente existe.","ChargeIS23 420,25 une seule fois ; detteIS nette23 220,25, compte3453 soldé, résultatnet106 409,75.",ecritures=entry_text(e),fiscal="La chargeIS ne diminue pas le bénéfice fiscal : ajout dans le passage résultat net → fiscal, sans doubler les réintégrations horsIS.")
    add("États ETIC","Bilan/CPC/ESG indépendants", "Actif = passif 337 010 ; résultat net 106 409,75 ; résultat avant IS 129 830 ; marge 22 100 ; production 132 000 ; VA/EBE 137 630 ; exploitation 129 330 ; financier 1 000 ; non courant −500 ; CAF 112 709,75.","Bilan, CPC puis Liasse fiscale → ESG ; sélectionner 2025, comparer ces valeurs, exporter PDF/Excel. Vérifier brut 24 000, amortissement 4 800, stock 6 600, clients bruts 14 400, dépréciation 2 000. Le scénario principal ne contient aucune FAE ; sa variante bloquée est indépendante.","Même résultat et mêmes soldes entre états, fiscalité, balances ; aucune inclusion des brouillons ou soldages techniques.",controles="Somme actif net = passif au centime ; la CAF ajoute ici 4 800 + 1 500 de dotations durables, pas la dépréciation circulante 2 000.")
    add("États ETIC","Tableau de financement premier exercice", "2025 sans2024 comptable documenté.","Liasse fiscale → Financement ; contrôler le message de comparatifabsent et l'avertissementN-1.","VariationN/N-1 explicitement non applicable ; aucune balance2024 fabriquée. Les flux ne peuvent pas être déduits d'une balance seule.")
    add("États ETIC","ETIC B6/B7 et références 02/002", "B6 : 3421 = 14 400 échus au 20/12/2025 ; 3427 = 0 dans le principal. B7 : 4411 = 480 échus au 31/12/2025 (02 = 240 et 002 = 240) ; 4417 = 3 000, échéance contractuelle FNP-01 31/01/2026, moins d'un an. Toutes devises et entreprises liées du scénario sont explicitement néant.","ETIC → B6 puis B7 ; déplier Sources à vérifier ; rechercher les deux références littérales 02/002 et leurs pièces distinctes. Vérifier la partie certaine sur les factures impayées. Compléter la FNP uniquement avec l'échéance documentée dans FNP-01 ; confirmer les analyses néant seulement selon le dossier fictif.","02 et 002 restent deux sources ; aucun reliquat classé par simple date comptable ; B6/B7 totalisent leur solde exact ; diagnostics incomplets visibles.",controles="TVA non encore récupérable 34552 = 80, CCA 3491 = 11 000 et dettes État ont leurs propres lignes ; ne jamais recopier le solde d'une ligne sur une autre.")
    etic_cases=[("A1","CMUP des marchandises ; coûts historiques ; informatique linéaire5 ans ; cut-off CCA/FNP ; FAE seulement en variante ; provisions documentées."), ("A2","Néant : aucune dérogation dans les hypothèses du scénario."),("A3","Néant : aucun changement de méthode."),("B1","Néant : pas de non-valeurs."),("B2","IMMO-01 acquisition24 000, aucunecession/réévaluation."),("B2bis","Dotation4 800, cumul4 800, VNC19 200."),("B3","Néant : aucunecession principale."),("B4","Néant : aucune participation."),("B5","Provisionrisque1 500 et dépréciationclient2 000, autresvariations0."),("B8","Néant : aucune sûreté contractuelle dans ce laboratoire."),("B9","Néant : aucun engagementhorsbilan stipulé."),("B10","Néant : aucun créditbail."),("B11","Vérifier détailCPC avec l'oracle."),("B12","Résultatnet106 409,75 +IS23 420,25 +réintégrations4 000 =133 830 ; déductions/déficits0."),("B13","Résultatcourant130 330 ; impôt attribué àdocumenter selon méthode choisie, noninventé."),("B14","TVAcollectée33 900, récupérable11 600, duefinN2 400,34552nonpayée80."),("C1","Associé Recette unique ;2 000parts nominal100 ; capital200 000 ;100 %. Identifiantassocié fictifREC-ASSOC01."),("C2","Premierexercice : aucuneaffectationantérieure ; décisionN+1 distincte."),("C3","2025 donnéesoracle ; antérioritésabsentes, pas de faux zéro publiécommehistorique."),("C4","Néant : toutes opérationsMAD, aucundevise."),("C5","Étatpréparé06/10/2026 en laboratoire ; événementpostérieur connu : paiementTVAdécembre2025 le20/01/2026 et paiementIS le31/03/2026 uniquement après exécution des casN+1. Ne pas les annonceravant exécution.")]
    for code,content in etic_cases:
        add("États ETIC","Compléter ETIC "+code,content,"ETIC → section"+code+" ; contrôler les valeursautomatiques ; compléter le texte/table/notes avec les données du scénario seulement, confirmer/enregistrer puis quitter et revenir.","Contenu conservé ; si table sans ligne, utiliser la confirmationnéant disponible ; aucuneinformationprobable inventée.",preuve="Capture section"+code+", contenu enregistré et statut après rechargement.")
    add("Inventaire clôture","Livre d'inventaire et contrôle final", "2025 ; brutimmobilisation24 000,amort4 800 ; stockphysique60×110=6 600 ; provisions3 500 ; chargeIS23 420,25 ; résultatnet106 409,75.","Livre d'inventaire →2025 → vérifier lescontrôles, tableaux et export ; Clôture → contrôles : stock et immobilisations recoupés, écritures équilibrées/validées, fiscalitécohérente. Corriger l'anomalie sur sa source avant de continuer.","LivrecohérentavecBalance/CPC/Bilan ; aucune clôture avant résolution des contrôles bloquants.")
    add("Inventaire clôture","Clôturer définitivement2025", "Résultatnet106 409,75 ; chargeISdéjàconstatée ;2026 crééoucréable ; aucunbrouillonN, FECsansbloquant.","Clôture →2025 → relire résumé et montantIS restant àcomptabiliser0 ; Clôturer l'exercice ; confirmer uniquement dans le laboratoire. OuvrirJournal2025 filtreCL etJournal2026 filtreAN.","Clôtureunique, résultatC1191=106 409,75, journaldédiéCL, comptesgestion soldés techniquement ; AN2026reprisebilan seulement ; exercice2025 verrouillé. AucunsecondIS ni secondstock.",ecritures="CL : soldercharges/produits, résultat1191 créditeur106 409,75 ; AN : reprise des soldesbilan annexés (sansclasses6/7).",fiscal="Liquidationconfirmée seulement aprèsclôture ; le référentielfiscal2025 couvert est requis.")
    add("Fiscalité","Confirmer liquidation après clôture", "Bénéficefiscal133 830 ; IS23 420,25 ; crédit200 ; acomptes2025 nonapplicables ; solde23 220,25.","Résultat fiscal / IS →2025 → Liquidation → Confirmer ; relire le snapshot et sa référence, recharger la page.","Snapshot cohérent auditable, montantsfigés ; aucune dette fiscalefabriquée ; réglagesbloquésaprèsconfirmation.")
    add("Liasse exports","Finaliser dossier fiscal existant09A", "2025clôturé,IF/ICEfictifsrenseignés,FECsansbloquant,ETIC23/23complète,liquidationconfirmée.","Liasse fiscale → Synthèse ; vérifier chaquecontrôle. Siunseulbloquantsubsiste, marquer ce casBloqué et documenter. LorsquecontrôlesOK, Finaliser ; consignerempreinteSHA-256, version,date,auteur.","Archive interne immuable ; mêmeschiffres que l'oracle. StatutPrêtdeHisabPro ne vaut ni dépôtDGI, ni conformitéofficielle, ni roadmap09B-Hterminée.",preuve="Capturecontrôles,empreintecomplète et archive.")
    add("Liasse exports","PDF et Excel de liasse", "2025 ; Bilan,CPC,ESG,Financement,ETIC,Fiscal ; mêmesvaleurs etnotes que les pages.","Liasse fiscale → PDF puisExcel ; ouvrir lesdeuxfichiers, comparer B6/B7,B12, titre,IF/ICE,références02/002 et résultat. Vérifier les montantszéro et À compléter.","Exports lisibles, valeurs identiques, titrepréserve<>&, zéro nonperdu, diagnosticsnonmasqués ; aucuneprésentationcommefichierEDIofficiel.",preuve="FichiersPDF/XLSXetcaptures despagescomparées.")
    add("Liasse exports","Exporter FEC complet", "Exercice2025 ; référenceslittérales02et002 ; datepièceetauxiliairesissusdesvraiestiersfiction.","Journal → contrôleFEC/Avis24 puis ExportFEC (si boutonaccessible via cetécran) ; ouvrir le fichieren mode texteUTF-8, pas une conversionautomatiqueExcel desréférences. Comparer chaquelignedeJournalattendu et soldes.","Débit=crédit ; écrituresdéfinitives seulement, numérosordonnés, références02/002distinctes, lienspièces/tiers conservés ; aucuncomplémentautomatique ambigu.",controles="Présence des16colonnes attendues par produit, lignesetmontantsaucentime ; fichierdujeu de testuniquement.")
    add("Inventaire clôture","Ouverture 2026 et contrepassations de cut-off", "AN 2026 : bilan annexé ; CCA 11 000, FNP 3 000 ; aucune FAE dans le principal ; aucune classe 6/7 importée dans les AN.","Sélectionner 2026 ; Journal → AN ; comparer les soldes. Repérer les brouillons de contrepassations créés par les ajustements ; contrôler la date 01/01/2026, les références et la source puis les valider après vérification.","AN unique équilibré ; CCA D6134 C3491 = 11 000 ; FNP D4417 C6125 = 3 000. Aucune contrepassation non justifiée.",ecritures="Deux OD de contrepassation, distinctes du journal AN.")
    add("Inventaire clôture","Variante indépendante de facture à établir", "Copie avant clôture ; contrat FAE-01 : prestation réceptionnée le 31/12/2025, HT 6 000, facture et échéance 31/01/2026. Qualification de l'opération et fait générateur TVA à documenter avant saisie définitive.","Ne pas ajouter cette FAE au scénario principal. Vérifier le contrat, le régime TVA et l'article 95 avec le responsable fiscal. L'assistant Clôture → FAE prépare un cut-off mais ne prouve pas la taxe. Après qualification seulement, contrôler le schéma comptable, la préparation TVA et la contrepassation 2026 dans cette copie.","Cas bloqué jusqu'à qualification ; aucun solde fiscal principal n'intègre 6 000 incertains. Sous hypothèse documentée de prestation taxable à 20 % avec fait générateur en N : D3427 7 200, C7124 6 000, C4455 1 200 ; l'effet sur la TVA doit alors apparaître explicitement dans la déclaration.",statut="Bloqué",observations="La préparation TVA actuelle est issue des flux de facturation/paiement ; l'ajustement FAE ne démontre pas le rapprochement des taxes. L'absence de facture en N ne suffit pas à exclure la TVA au débit. Variante exclue de tous les totaux principaux.",ecritures="Schéma conditionnel seulement après qualification : OD D3427=7 200 C7124=6 000 C4455=1 200 ; à défaut de qualification, aucune écriture à exécuter.",fiscal="CGI article 95, source TVA_FAIT_GENERATEUR. Ne jamais choisir l'absence de taxe pour faire passer un contrôle.")
    add("Fiscalité","Paiements de soldeN dansN+1", "TVAdécembre2025 :2 400le20/01/2026 ; IS2025 :23 220,25le31/03/2026 ; référencesTVA-12-PAY/IS-2025-PAY.","Journal2026 → BQ : saisir/valider D4456 C5141=2 400 puisD4453 C5141=23 220,25. VérifierGrandlivre et rapprocher lesavisbancairesfictifsN+1.","Dettesreportéessoldées ; banqueaprèscesdeuxpaiements262 109,75 (avantautresopérationsN+1). Archive2025 inchangée.",ecritures="BQ20/01/2026 D4456=2400 C5141=2400 ; BQ31/03/2026 D4453=23220,25 C5141=23220,25.")
    add("Fiscalité","Acomptes2026 depuis vraie référence2025", "Bénéfice2025confirmé133 830 ; taux2026decontrôle20 % ; référenceannuelle26 766 ; quatreacomptes6 691,50 ; dates31/03,30/06,30/09,31/12/2026.","Résultat fiscal / IS →2026 → acomptes ; vérifierréférenceissue2025. Enlaboratoire enregistreracompte1=6 691,50le31/03,2=2 000le30/06,3et4nonpayés ; référencesAP1-2026/AP2-2026 ; journaldistinctD3453 C5141pourpaiements réelsfictifs. Ne pas reprendreunversementdesoldede2025commeacompte2026.","Acompte1soldé ;2partielreste4 691,50 et,après30/06,Partiel—enretard ;3enretardaprès30/09 ;4nonéchu avant31/12. État dépend de la datecourante ; tousmontantscopiésdanspreuves.",ecritures="BQ2026D3453 C5141=6 691,50puis2 000 ; pasd'écriturepouracomptesnonpayés.",fiscal="Référencetransitoirevérifiée sursourceofficielle ; cettevariante modifiel'exercice2026 uniquement.")
    add("Fiscalité","CSS2026 référence documentée", "Liquidation2025confirmée133 830, inférieureauseuild'unmillion.","Résultat fiscal / IS →2026 → CSS ; vérifierqueleréférentielest2025confirmé,aucuneréférenceforcée. Contrôlerlemontantetabsence de formulaire depaiementpourmontantzéro.","CSSdueselonmoteur=0,sourceliquidationN-1identifiée ; nedéduireaucuneabsenced'obligationdéclarative duseulzéro.")
    blocked=[("09B — référentiel exhaustif DGI","Catalogueofficielcourant,version,domaineetconditionsapplicables non exhaustivement intégrés."), ("09C — XML/EDI SIMPL-IS","Schémaofficielapplicable,version,XSDetrecettedépôt nonvalidés ; boutondésactivé."),("09E — état des ventes DGI","Pasdeparcoursdédiécompletvérifiédanscedépôt ; lesstatistiquescommerciales nesontpasunétatDGIofficiel."),("09F — rémunérations allouées aux tiers","Annexedéclarativecomplèteetmodèleofficiel non implémentés ; créditsaIS nesuffisentpas."),("09G — taxe professionnelle et annexes","Valeurlocative,qualificationetschémaannexe nondéterminablesavec certitude depuis lespiècesprincipales."),("09H — prêt à déposer complet","ArchiveinternedisponiblemaisannexesofficiellesetEDI non terminés ; impossibledevaliderundépôtcomplet.")]
    for label,reason in blocked:
        add("Liasse exports",label,"Aucune donnée à saisir tant queleformat et leparcoursne sontpas implémentés.","Consulterlamatricedecouverture ; enregistrerleblocage. Ne pasinventerd'écran,d'exportoud'obligationpour terminercecas.","Limiteexpliquée ; parcoursàreprendre après développementetvérificationofficielle.",statut="Bloqué",observations=reason,preuve="Entréeduregistredeslimites etréférenceofficiellequanddisponible.")
    add("Liasse exports","09D — import balance N/N-1 indépendant", "balance_attendue_2025.csv ou .xlsx ; colonnes compte/debit/credit ; balance AVANT soldage technique ; N-1 absent pour ce premier exercice ; exercice 2025 existant dans cette société.","Liasse fiscale → Préparer depuis des balances externes → Importer N / N-1 ; choisir la balance N fournie, laisser N-1 absent ; Contrôler et préparer. Vérifier le plan comptable de la société. Lire l'aperçu Bilan/CPC/ESG, exporter Excel et comparer à l'oracle. Constater que le nombre d'écritures au Journal reste inchangé.","Aperçu équilibré identique ; N-1 absent = Indisponible ; extra-comptable inconnu reste inconnu. Aucun import d'écritures, aucune génération automatique de fiscalité/ETIC/flux de financement.",observations="09D partiel : préparation indépendante avec versions conservées, distincte d'un dossier fiscal complet.")
    add("Liasse exports","09D — conserver et relire une préparation versionnée", "Préparation du cas précédent ; données sources normalisées et période 2025.","Cliquer Conserver une nouvelle version ; consigner version et empreinte SHA-256. Recharger la page, ouvrir Préparations conservées et sélectionner cette version sans recharger de fichier. Exporter Excel puis Exporter la préparation PDF et comparer à la première préparation. Conserver une deuxième version distincte ; relire la première.","Sources, période, états et empreinte conservés ; versions précédentes immuables. Le PDF indique préparation indépendante et limites, avec les mêmes montants. Aucune écriture de grand livre ni archive fiscale produite. Un lecteur peut consulter/exporter avec Consulter les préparations, sans conserver de nouvelle version.",observations="Migration additive 071 et API de préparation indépendante ; conservation versionnée ne signifie pas archivage fiscal annuel.")
    add("Liasse exports","09D — dossier fiscal complet en mode Liasse seule", "Aucune saisie supplémentaire.","Documenter les limites : fiscalité, ETIC, financement et annexes ne se reconstituent pas depuis une simple balance. Reprendre quand un dossier autonome complet applicable est implémenté.","La préparation conservée ne prétend pas être un dossier complet prêt à déposer.",statut="Bloqué",observations="Mode Liasse seule complet non terminé ; préparation de balances disponible.")
    add("Liasse exports","09D — balance techniquement soldée", "Fichier a_nouveaux_attendus_2026.csv : comptes de bilan et résultat 1191, aucune classe 6/7.","Sur copie de contrôle, importer ce fichier et lire l'aperçu et l'export. Vérifier les indicateurs de disponibilité ; ne pas saisir des produits fictifs pour reconstruire le CPC.","Bilan disponible ; CPC/CAF indisponibles faute de comptes de gestion, sans remplacement par des zéros. Aucun succès fiscal ou comptable extrapolé.",ecritures="Aucune écriture créée par cette préparation indépendante.")
    add("Liasse exports","09D — comparer deux millésimes sans inventer l'antériorité", "Exercice de contrôle 2026 existant ; N = a_nouveaux_attendus_2026.csv, uniquement état d'ouverture avant mouvements N ; N-1 = balance_attendue_2025.csv avant soldage technique.","Sur une copie de contrôle, sélectionner 2026. Importer les deux fichiers distincts dans N et N-1 ; Contrôler et préparer. Comparer les colonnes de chaque état et les exports Excel/PDF. Ne jamais utiliser une balance 2024 fictive dans le scénario de société créée en 2025.","Bilan N et N-1 : actif/passif 337 010. CPC/CAF N indisponibles, puisque l'AN ne décrit pas les flux 2026 ; CPC N-1 net 106 409,75 et CAF N-1 112 709,75. Les deux disponibilités sont affichées séparément.",observations="Préparation de contrôle à partir des données d'ouverture ; elle ne constitue pas une liasse annuelle 2026 complète.")
    add("Inventaire clôture","Archiver définitivement le livre d'inventaire", "2025 clôturé ; inventaire physique final validé ; stock 6 600 comptabilisé ; acquisition et amortissement rapprochés ; aucune ligne brouillon.","Livre d'inventaire → 2025 → Archiver définitivement ; relire les contrôles. Capturer version, auteur et empreinte ; télécharger le PDF archivé. Revenir après ouverture de 2026 et comparer l'empreinte.","Livre figé, bilan 337 010, stock 6 600, VNC 19 200, même empreinte après opérations 2026. Un blocage source reste visible jusqu'à correction autorisée.")
    add("Facturation","Recouvrement et relances dans l'interface", "VENTE-IMPAYEE 14 400 ; date de relance 22/12/2025 ; niveau 1, canal E-mail, date promise 31/01/2026 ; prochaine relance laissée vide ; commentaire Suivi fictif du laboratoire, sans envoi externe. Pour la modification : date promise 15/02/2026 et commentaire Promesse fictive modifiée ; annuler ensuite cette relance de test.","Facturation → Situation financière → Échéances & impayés : retrouver VENTE-IMPAYEE et cliquer Relancer. Choisir Niveau 1 — rappel et Canal E-mail ; saisir Date de relance 22/12/2025, Date promise 31/01/2026 et le commentaire indiqué ; vider Prochaine relance préremplie. Enregistrer la relance. Ouvrir l'onglet Relances, comparer facture, niveau, canal, dates et commentaire puis recharger pour vérifier la conservation. Cliquer Modifier sur cette ligne ; remplacer la date promise par 15/02/2026 et le commentaire par Promesse fictive modifiée ; enregistrer et recharger. Cliquer Annuler la relance, confirmer puis recharger : vérifier la ligne et le statut Annulée conservés. Dans ce laboratoire, ne pas envoyer de message externe : la fiche journalise normalement une action effectuée hors application, simulée et identifiée comme fictive ici.","Relance créée, modification conservée et statut Annulée visible dans l'historique après rechargement ; bonne facture et solde client inchangé à 14 400. L'annulation conserve la trace. L'enregistrement ne prouve aucun envoi d'e-mail et ne génère aucune écriture comptable.",observations="Création, historique, modification et annulation disponibles dans Situation financière ; recette utilisateur Non testé. Envoi externe automatique non implémenté. Les actions de mutation restent réservées aux rôles autorisés ; le lecteur consulte l'historique.",preuve="Captures de la création, de la promesse modifiée et du statut Annulée après rechargement, montrant référence, niveau, canal et dates ; aucune preuve d'envoi externe inventée.")
    add("Facturation","Archivage individuel des factures", "Facture VENTE-01 validée et soldée ; PDF de pièce.","Contrôler conservation du PDF et historique ; documenter la limite d'archivage individuel si aucun parcours dédié n'est proposé.","Conservation/export disponibles mais pas de statut d'archive définitive individuel inventé.",statut="Bloqué",observations="Archive annuelle liasse/livre disponible ; workflow dédié d'archivage individuel des factures non établi.")
    add("Facturation","Variante achat BC → BR → facture", "Copie indépendante avant achats ; F-MARCH ; M-01 10 unités × 100 HT, TVA 20 % ; BC 01/02/2025, BR 02/02, facture 03/02, échéance 10/02 ; total 1 200.","Cycle commercial → Bons de commande → Nouveau, type Achat, fournisseur F-MARCH, lignes indiquées. Créer BR de 10 unités ; Bons de réception → Facturer ce BR. Valider/comptabiliser la facture puis valider au Journal. Ne pas facturer aussi le BC directement.","Stock +10 une seule fois ; lien BC/BR/facture ; fournisseur 1 200, achat 1 000, TVA 200 ; facture depuis BR sans double entrée stock.",ecritures="AC D6111=1 000 D34552=200 C4411=1 200 ; aucune écriture à la seule création BC/BR.",prerequis="Copie indépendante, opérations exclues des totaux principaux.")
    add("Facturation","Variante échéancier contractuel", "Copie indépendante ; client C-SERVICE ; facture du 01/04/2025, HT 1 000, TVA 200, TTC 1 200 ; 50 % le 30/04 et 50 % le 31/05 ; deux montants 600.","Factures → Nouvelle vente de prestation ; sélectionner Échéancier puis 50/50 ; remplacer les deux dates par celles indiquées. Valider/comptabiliser ; payer 600 le 30/04 ; relire le détail de l'échéancier et ETIC à la date de contrôle.","Deux échéances exactes, somme 1 200 ; paiement réduit seulement le disponible documenté ; reliquat 600 dû au 31/05. Aucun classement par date comptable à la place de l'échéance.",ecritures="VT D3421=1 200 C7124=1 000 C4455=200 ; BQ D5141=600 C3421=600.",prerequis="Copie indépendante ; exclure des totaux principaux.")
    add("Facturation","Variante annulation par avoir intégral", "Copie indépendante avant avoir VENTE-01 ; facture soldée 30 000, 100 unités ; avoir intégral daté 10/02/2025, HT 25 000, TVA 5 000, TTC 30 000.","Créer un avoir Retour / annulation intégral, retour stock confirmé ; valider/comptabiliser. Rembourser le crédit 30 000 par virement daté 11/02/2025 dans cette copie ; valider les écritures et conserver facture/avoir/règlement initiaux.","Piste d'audit conservée ; ventes et TVA annulées, stock +100 une seule fois ; remboursement bancaire 30 000 ; aucun effacement d'écriture validée.",ecritures="AV D7111=25 000 D4455=5 000 C3421=30 000 ; remboursement D3421=30 000 C5141=30 000.",prerequis="Copie indépendante avec crédit d'avoir disponible ; aucune imputation antérieure.")
    add("Paiements","Variante annulation de règlement", "Copie indépendante avant clôture ; paiement VENTE-01-PAY 10 000 du 25/01/2025 ; date d'annulation réelle 06/10/2026 dans une période 2026 ouverte.","Cycle commercial → Règlements → paiement concerné → Annuler par contrepassation. Lire la date d'annulation affichée ; ne jamais effacer le règlement historique. Au Journal 2026 vérifier puis valider la contrepassation.","Paiement annulé de manière tracée ; créance commerciale réouverte de 10 000 ; contrepassation datée dans la période ouverte. Aucun effet ajouté aux totaux 2025 du scénario principal.",ecritures="Contrepassation D3421=10 000 C5141=10 000.",prerequis="Copie indépendante et exercice de date d'annulation ouvert ; flux actuel date l'annulation au jour de l'opération.")
    add("Facturation","Délais de paiement et pièces contractuelles", "Exercice 2025 ; factures fournisseurs 02 et 002 du 02/12, échéance 31/12, service réceptionné 02/12/2025 ; pas de litige judiciaire dans ces deux pièces.","Délais de paiement → 2025 ; rechercher les deux références ; Compléter : saisir date de service 02/12/2025, ne cocher ni litige ni hors champ sans justificatif. Télécharger la préparation disponible et vérifier les sources.","Deux factures distinctes et échéances exactes ; informations manquantes visibles. L'éligibilité à une obligation déclarative se qualifie sur le texte et les seuils du dossier, pas sur le seul impayé.",fiscal="Aucun calcul d'amende ou dépôt réel extrapolé sans qualification réglementaire.")
    add("Comptabilité","Exports des livres et balances", "Exercice 2025 ; compte 5141 solde 287 730, 3421 solde 14 400, 4411 solde 480 ; balance avant soldage technique fournie.","Journal, Grand livre, Balances générale/auxiliaire : utiliser chaque export PDF/Excel/CSV réellement proposé. Ouvrir les fichiers et vérifier filtres, dates, tiers et totaux ; conserver le fichier et une capture de comparaison.","Montants exportés identiques aux pages et à l'oracle ; écritures brouillon exclues et clôture technique identifiée ; aucun arrondi ou conversion 02/002.")
    add("Sécurité UX","Révocation des accès invités", "Compte lecture@hisabpro-recette.example connecté dans une seconde fenêtre ; administrateur dans la première.","Paramètres → Utilisateurs : désactiver l'accès invité ou le supprimer dans le laboratoire. Dans la fenêtre invitée, recharger puis tenter un appel protégé ; réactiver uniquement si le parcours le prévoit et consigner la nouvelle connexion.","Accès révoqué immédiatement sur le serveur ; aucune donnée de société visible grâce à un ancien jeton. Le compte principal de l'utilisateur n'est pas supprimé arbitrairement.")
    add("Sécurité UX","Changement de mot de passe dans l'interface", "Copie du compte de test ; ancien mot de passe Recette!Atlas2025, nouveau Recette!Atlas2025Long ; saisie erronée de contrôle Recette!Incorrect2025.","Paramètres → Mon compte → Mot de passe personnel. Saisir Recette!Incorrect2025 comme mot de passe actuel, le nouveau secret et sa confirmation ; Modifier mon mot de passe : vérifier le refus. Saisir ensuite le bon mot de passe actuel et une confirmation différente : vérifier le refus sans changement. Corriger la confirmation et enregistrer. Cliquer Revenir à la connexion ; vérifier que l'ancien secret est refusé puis se reconnecter avec le nouveau. Répéter sur une copie avec le rôle lecteur, sans modifier les permissions.","Les saisies incorrectes ne changent pas le compte. Le changement confirmé affiche la demande de reconnexion ; ancien secret refusé, nouveau accepté. Mon compte reste accessible à tous les rôles. Aucune donnée comptable modifiée.",controles="Ne jamais enregistrer les mots de passe ou les jetons dans les captures ; vérifier compte et sociétés inchangés après reconnexion.",observations="Parcours personnel présent ; tests automatisés distincts de cette recette utilisateur, qui reste Non testé.",preuve="Captures expurgées des refus, du message de reconnexion et de la session reconnectée, sans aucun secret.")
    add("Sécurité UX","Révocation technique après changement de mot de passe", "Copie du compte de test ; nouveau secret Recette!Atlas2025Long ; jeton émis après mise à jour du mécanisme versionné, conservé uniquement en mémoire par le technicien.","Sur une copie distincte, le technicien change le mot de passe via Paramètres → Mon compte (POST /api/auth/mot-de-passe), puis appelle une API protégée avec l'ancien jeton et reconnecte avec le nouveau secret. Conserver seulement les codes HTTP et expurger tous les secrets des preuves.","Ancien jeton versionné refusé ; nouveau mot de passe utilisable, ancien secret refusé. Les jetons historiques sans version peuvent rester compatibles jusqu'à expiration.",observations="Contrôle technique de révocation complémentaire au parcours personnel dans l'interface ; aucune réussite utilisateur préremplie.",preuve="Journal technique expurgé : changement personnel autorisé, ancien jeton refusé, nouvelle connexion réussie.")
    # Variantes : copies indépendantes, jamais cumulées aux totaux principaux.
    add("Fiscalité","Variante déficit antérieur documenté", "Copieindépendante d'undossier derepriseayantattestation2024 ; ordinaire10 000,amortissement2 000 ; base2025avantdéficit133 830.","Créerundossierdevariantedistinctsansmodifierlasociétéprincipalepremierexercice. FiscalitéIS → Ajoutermillésime2024avecmontants10 000/2 000etréférence DEF-2024 ; contrôlerpropositionFIFO puisconfirmer l'imputation.","Déficitimputé12 000 ; bénéfice121 830 ; IS17,5 %=21 320,25 ; crédit200 → solde21 120,25 ; aucuneconsommationduplicat aprèsrechargement.",prerequis="Dossierfictifvariantdereprise, preuvefiscaleantérieureexplicitementfournie ; nepasinventer un déficitdanslasociéténouvelle.",fiscal="Duréesde reporteteligibilitéàvaliderparresponsablefiscal surtexteofficiel ; lecasvérifiela mécanique d'une imputationsourcedocumentée.")
    add("Fiscalité","Variante déduction documentée", "Copieindépendanteavantliquidation ; reprisesdeprovisions antérieurementtaxées1 000,produit comptabilisé71955 ; réintégrationsprincipal4 000.","Danscopievariante,JournalD1518 C71955=1 000avecpiecede repriseREC-REPRISE ; FiscalitéIS → déduction1 000uniquementaprèsjustificationdetaxationantérieure ; contrôlernouveaucalcul.","RésultatcomptableavantISaugmente1 000 puisdéduction1 000 : bénéfice fiscal133 830inchangé. Aucune déductionautomatique d'unerepriseprobable.",prerequis="Copieindépendante, provisionexistante etjustificationdetaxationantérieure ; piècefictive spécifiée.",ecritures="ODD1518 C71955=1000.")
    add("Fiscalité","Variante TVA encaissement", "Copieindépendanteavantcréationdesfactures ; régimesociétéencaissement ; factureimpayée14 400, aucune somme réellementencaisséeaprèsrejet.","Rejouerledossierdevariantedepuisparamétrageencaissement ; contrôlermoisdécembreetfactureimpayée, acomptesetdatesbank. Ne paschangerlerégimed'unepiècevalidéepour altérerunsnapshot.","TVAdefactureimpayée non exigibleavantencaissementdocumenté ; pasdedoublonTVA surl'acompte20 000HT/4 000TVA ; rejetnelaissepasunencaissementfictif.",prerequis="Nouvellecopieindépendante ; règles/optionrégime documentées.")
    add("Fiscalité","Variante honoraires public etRAS TVA", "Clientpublicfiction ; honoraires10 000HT,TVA2 000,RASIS5 %=500 ; retenueTVA75 %=1 500siqualificationapplicable ; netbancaire10 000.","Ne pasexécuterune déclarationautomatiquefinale aveclerégimeincomplet. Vérifierlesarticlesapplicables,l'attestationetletypede prestationavec responsableréglementaire ; enregistrerlimitationdu moteurTVA.","ScénariobloquépourpréparationcomplètedéclarationTVA ; aucunpaiement11 500annoncésoldé enoubliantlaTVARAS1 500.",statut="Bloqué",observations="MoteuractuelneréconciliepastoutesretenuesTVAarticle117. Montantsdenettechnologiquesseulement sousqualification légale explicite.",fiscal="SourcesRAS_ISetRAS_TVA officielles ; nepasappliquerRASauxmarchandises.")
    add("Immobilisations","Variante cession surcopie", "IMMO-01brut24 000,amortcumul4 800,VNC19 200 ;cession01/01/2026pour20 000HT,TVA4 000,encaissement24 000.","Danscopieisolée2026,paslasociétéprincipale,payéeacquisitionetdotation2025validées : Immobilisations → IMMO-01 → Cession ; date01/01/2026,PU20 000TVA20 %,encaissementimmédiat5141 ; contrôleretvaliderlesécrituresgénérées.","Sortie2355,C28355soldé,VNA19 200 etproduitcession20 000 ; plusvaluecomptable800 ; banque+24 000 ; traitementfiscal/TVArégularisationàdocumenter.",ecritures="ODD28355=4800 D6513=19200 C2355=24000 ; VTD3481=24000 C7513=20000 C4455=4000 ; BQD5141 C3481=24000 (comptecréancecessionàconfirmerdansparamétrage).",fiscal="QualificationetrégularisationTVAimmobilisationsarticle104nonautomatiquementvalidées.")
    negatives=[
        ("Email déjà utilisé","admin@hisabpro-recette.example","Créeruncompteavec cetemail","Créationrefusée ; unesociétéutilisateurpréservée."),
        ("Mot de passe trop court","court (5 caractères)","Créer le compte Copie Faible avec le mot de passe court, inférieur au minimum applicatif de 8 caractères.","Refus serveur ; aucune société orpheline."),
        ("ICE incorrect","ABC123 ou14chiffres","Paramètres→saisirICEinvalide→enregistrer","Erreurclaire ; aucuneidentitécorrompue."),
        ("Exercice chevauché","01/07/2025–30/06/2026","Créercesdatesavec2025existant","Refusdechevauchement ; aucune suppression."),
        ("Exercice trop long","01/01/2027–31/01/2028","Créerexercicetreizemois","Refusdeladurée ; bornesexistantespréservées."),
        ("Écriture déséquilibrée","D5141=100,C1111=99","Journal→nouvelleécriture→valider","Validationrefusée,écart1signalé ; aucunnumérodéfinitifindûmentcréé."),
        ("Montant négatif","PU−10,quantité1","Facturebrouilloncopietest→enregistrer","Refusdesaisieouvalidation ; pasd'écritureautomatique."),
        ("TVA invalide","taux101 %","Facture/immobilisationcopietest→enregistrer","Erreurdetaux ; pasdecontournementparréductionautomatique."),
        ("Référence02/002","Mêmejour,TTC240,F-CONTROLE","Consulterlignesdéjàcréées,récupérationFEC/ETIC","Deuxsourcesdistinctes ; référencesrestenttexte."),
        ("Doublecomptabilisation facture","VENTE-01déjàcomptabilisée","Cliquercomptabiliser denouveau sicommandedisponible","Refus/idempotence ; aucune deuxième principale."),
        ("Édition après validation","VENTE-01PU250→251","Tenteréditiondepiècedéfinitive","Refus ; correctionparavoir/annulationtraçable."),
        ("Surpaiement","Solde02=240,paiement241","Facture02→Payer241surcopie","Refus ; pasdebanque/tiersmodifiés."),
        ("Acompte surconsommé","AC-C01disponible0,imputer1","Acomptes→imputerdenouveau","Refusdu disponible ; écrituresinchangées."),
        ("Créditavoir mauvais tiers","AV-01surC-IMPAYE","Avoirs→tenterimputationcréditversautretiersetavantutilisationencopie","Refus ; aucuneallocationarbitraire."),
        ("Créditavoir surconsommé","AV-01crédit3000,imputation3001","Copieavantimputation→imputer3001","Refusplafond ; pasdedetteclientfictive."),
        ("Retour excessif","VENTE-01vendu100,retour101","Copie→créeravoir101","Refusdequantité ; stocknoncrééindûment."),
        ("Effet encaissé avant échéance","EFF-C01 échéance15/05/2025,date14/05/2025","Copieavantencaissement→confirmer14/05","Refus ; pasd'entréebanqueantérieure."),
        ("Frais supérieurs au règlement","EFF-C01 montant10000,frais10001","Copie→encaissementfrais10001","Refus ; pasdebanquenégativecréée."),
        ("Rejet après encaissement définitif","CHQ-01déjàencaissé","TentertransitionRejeter","Refusstatutincompatible ; correctioncontrôlée si nécessaire."),
        ("Dates bancaires impossibles","Dateeffectivefutureoudatéeavantémission","Transitioncopie→saisirdateinvalide","Refusdocumenté ;pasdemouvementfuturouantérieuràsonorigine."),
        ("Lettrage entre tiers","DébitC-MARCH,créditC-SERVICE,mêmemontant","SélectionnerauLettrageenlaboratoire","Refusdu mélangeauxiliaire."),
        ("Lettrage déséquilibré","Débit100,crédit99","Copiebrouillonsvalidésdecontrôle→lettrer","Refusécart1 ; aucunelettrageforcé."),
        ("Double rapprochement","LignebancaireCAP-01déjàrapprochée","Tenterliaisonàsecondécriture","Refus/devoirdérapprochercontrôlé ; liens1:1."),
        ("Relevé montant invalide","Fichier fourni negatifs/releve_debit_credit_simultanes.csv ; 31/12/2025, débit 1 000 et crédit 1 000.","Rapprochement bancaire → Import Excel / CSV ; importer ce fichier sur copie ; lire le numéro de ligne et le diagnostic.","Refus de tout le lot ; aucune ligne ambiguë importée silencieusement."),
        ("Inventaire négatif","M-01physique−1","Inventairecopie→valider","Refus ; pasd'inventairefinalnégatif."),
        ("Service avec faux stock","S-VTEstock10","Éditerarticleservice","Stockservice reste0/refus ; aucunmouvementstockparprestation."),
        ("Dotation doublée","AMORT-2025existevalidé4800","Générerdotationdenouveau","Refus/idempotence ; dotation4800unefois."),
        ("Valeur résiduelle excessive","IMMOcopieHT1000,résiduelle1001","Créerimmobilisationtest","Refus ; coût/amortissementnoncorrompus."),
        ("Provision fiscalenonconfirmée","Hypothèseprovision1500nonqualifiée","AfficherFiscalitéavantconfirmation","Diagnosticàconfirmer ; pasderéintégrationchoisie arbitrairement."),
        ("CréditIS déjà imputé excessif","Crédit200,déjàimputé201","Fiscalitécopie→ajoutercrédit","Refus ; pasdecréditnégatif oudoubledéduction."),
        ("Référence fiscale forcée sans preuve","Référenceacomptes20000,justificationvide","Paramètresfiscalitécopie→enregistrer","Refusdejustification ; pasdereclassement pourcontrôlevert."),
        ("Liquidation avantclôture","Exercice2025ouvertencopie","ConfirmerliquidationIS","Refus ; simulationconsultablesanssnapshotfinal."),
        ("IS comptabiliséincohérent","IS attendu 23420,25,chargejournal1","Clôture/confirmationencopie","Blocagecohérence ; nepasadapterlecalculfiscalpouraccepter1."),
        ("ETIC montants invalides","B6 :−1,puisNaN,champvide","Saisir/saveencopie","Valeurnégative/nonnumériquerefusée ; videÀcompléter ; zérovalideetprioritaire."),
        ("ETIC ventilation incohérente","B7total480,somme479","Enregistrer/confirmersectionencopie","Incohérencede1visible ;pasdefinalisationdeliasse."),
        ("Pièce manquante historique","ODde3421avecref/datepièceabsents,sourcesambigües","Technicienpréparelabuniquement ; contrôleFEC/ETIClecture","Anomaliesvisibles ; aucuneidentité/date/échéanceinventée."),
        ("Période fermée","Janvier2025fermémanuellementencopie","Tenterécriture15/01/2025, puisadminrouvrepériode","Écriturerefuséequandfermée ; réouvertureadminauditéeavantclôture."),
        ("Clôture prématurée","Exercice2027 encoreen coursàdate réelle2026","Tenterclôture2027danslab","Refusdateavantfindexercice ;aucuncontournement système."),
        ("Modification exerciceclôturé","Facture/Journal2025aprèsclôture","Tentercréation/édition/suppression/reouverturepériode","Refus ; correctiondanspériodeouverteultérieure, pisteauditpréservée."),
        ("Double clôture età-nouveaux","2025déjàclôturé","Relancerclôture/générationAN","Refus/idempotence ; unseulreport2026."),
        ("Archive immuable","Liasse2025finalisée","ModifierETIC/Fiscalité2025, exporterarchiveaprèsmutation2026","Refusmodificationarchive ;empreinte2025identique."),
        ("Accès lecture","Utilisateurlecture","TenterAPIdecréationetboutonfacture/journal/ETIC","Refusserveur403etcontrôlesUI ; aucunécriturenew."),
        ("Accès société tierce","CompteA,IDdocumentdeB","TechnicientesteAPIGET/PATCHpièceBavecjetonA","404/403sansdonnéesfuitées ; pasd'écritureinter-société."),
        ("Pièce jointe société tierce","IDfichierdeB","TenterlienfichieravecjetonA","Accèsrefusé ; aucunPDFd'autresasociétés."),
        ("Session expirée","Jetonexpiré/déconnecté","RechargerdétailfactureouappelAPIprotégé","401etretourconnexion ; secretsnonaffichés."),
    ]
    for title,values,actions,expected in negatives:
        add("Scénarios négatifs",title,values,actions+". Exécuter uniquement surcopieavantl'étatrequissi nécessaire.",expected,prerequis="Copie de laboratoire isolée ; restaurer l'instantané adapté au cas ; ne jamais altérer les soldes principaux pour produire un cas négatif.",controles="Vérifier code/message, absence de mutation non autorisée et intégrité des totaux ; associer anomalie au cas si comportement diverge.")
    for filename,expected in [('balance_desequilibree.csv','Écart de 1 MAD identifié ; aucune préparation conservée.'),('balance_compte_inconnu.csv','Compte 7999999999 absent du plan refusé ; aucun compte créé automatiquement.'),('balance_compte_double.csv','Compte 5141 en doublon refusé ; aucune agrégation arbitraire.'),('balance_montant_nan.csv','Montant NaN refusé ; aucun montant remplacé par zéro.'),('balance_resultat_et_gestion.csv','Résultat technique 1191 et comptes de gestion simultanés refusés ; aucun double résultat.')]:
        add('Scénarios négatifs','09D — fichier invalide '+filename,'Fichier fourni negatifs/'+filename+'. Copie de contrôle avec plan initialisé.',"Liasse fiscale → Préparer depuis des balances externes → Importer N / N-1 ; choisir ce fichier en N ; Contrôler et préparer. Lire l'erreur ; vérifier le nombre d'écritures et de versions conservées avant/après.",expected,controles="Lot refusé entièrement ; aucune conservation, aucune écriture et aucune suppression d'une version précédente.")
    ux=[("Navigation complète","1366×768et390×844","ParcourirFactures,Cyclecommercial,Journal,Grandlivre,Bilan,ETIC,Paramètres ; ouvriresdétails/modales","Titres/actions visibles, scrolllocalseulementsinécessaire, aucun contenu essentieltronqué."), ("Rafraîchissement mutation","Factureet règlementdujeu","Enregistreropération puis observerlistes/JournalavantF5","Étatlocalactualisé,montant/soldeàjour, aucuneF5requise."),("Plan comptable immédiat","Compte3421puis2355","Ouvrirselectcompte,saisirnuméroetchoisir","Libelléautomatique, comptes misencache, aucune attenteanormalementlongue."),("Exports caractères littéraux","SociétévarianteAtlas <SARL> & associés","ExportPDFsurcopieavecidentitélittérale","Titreexactavec<SARL>&, texteéchappé, pasd'erreurPDF."),("Statuts cohérents","Virementpartiel,effetnonencaissé,avoirimputé","ComparerFactures,Effets,Situationfinancière,Journal,ETIC","Soldecommercialdistinctdesvaleursencoursbanque ; aucunstatutpayéavantétapeeffective."),("Chargement eterreurs","Réseauindisponiblepuisrétabli","SurcopiecouperaccèsAPI,ouvrirpage,puisrestaurer et recharger","Erreurcompréhensible,pasde donnéesmensongères ouactiondoubledéclenchée."),("Consentement session multi-société","DeuxcomptesA/Bautorisés","Changersociétédanssélecteuravec formulaireouvert,sans sauvegardeautomatique","Contexteactualisé, pasd'enregistrementdanserreursociété, droitsrechargésdu serveur.")]
    for title,values,actions,expected in ux:
        add("Sécurité UX",title,values,actions,expected)
    exploitation=[("Migrations effectives","Baseisoléeseule","Comparer schémaobtenuauxmodèlesetmigrations ; testercontraintesavec rollback lab","Historiquenonréécrit, migrationsrequisesidentifiées ; aucunevalidationPostgreSQLremplacéeparSQLite."), ("Sauvegarde intégrale","Baseisoléerecette+répertoirepiècesjointes+configurationhorssecrets","Effectuersauvegardeselonprocédure,empreinteetlistefichiers","Archivefermée lisible, compte/lignes/pièces/snapshotsinclus ; ceZIPdifférentieln'estpasune sauvegardeDB."),("Restauration surbase vierge dédiée","Backupprécédent,nouvellebaseisolée","Restaurersurbasedédiéedifférentedeproduction ; reconnecterapplicationdedicace","Soldes337010/287730etempreintearchiveidentiques ; justificatifsouvrables ; aucunrestaurationsurbase réelle."),("Reprise aprèsincident","Copieserveurisolée","Arrêterbackendentrebrouillonetvalidation,puisredémarrer/recharger","Aucunécriturepartielledéfinitive, numérotation/validationauditstable ; logsutiles sans motsdepasse."),("Sécurité déploiement","Paramètresréseaudéploiementisolé,secretJWTnonlivré","VérifierHTTPS,originesCORS,secret,rotation/sessions,permissionsfichiers et absenceendpointsadminpublics","Pointsgouvernés/documentés ; nepasmarquerprêtproductionavantrevuesréelles."),("Recette automatisée reproductible",".venv+Test/requirements.txt,node_modules,Edge","Exécutercommandesdocumentéesunitaires/build/bancPostgreSQLisolé/E2E ; consignerdate,version,logetfailures","Compter succès/échecs/ignorés réellementobservés ; aucuneassimilationàrecetteutilisateur."),("Validation réglementaire finale","Sourcesofficiellesetversion2025/2026complètes","Responsablefiscalcontrôlequalifications,annexes,modalitésdépôt,RAS/CM/CSSetarchivage","Avisdevalidationdocumenté oublocageexplicite ; aucunecertificationannoncéeparautomatisation.")]
    for title,values,actions,expected in exploitation:
        add("Exploitation",title,values,actions,expected,preuve="Rapport technique, logs expurgés, empreintes et captures de l'environnement isolé.")
    for c in cases:
        for key in ("objectif","prerequis","donnees","actions","attendu","ecritures","fiscal","controles","observations","preuve"):
            if not c[key].lstrip().startswith("{"):
                c[key]=texte_lisible(c[key])
    return cases


CASE_COLUMNS = [("ordre", "Ordre"), ("id", "Identifiant"), ("module", "Module"), ("objectif", "Objectif"),
                ("prerequis", "Prérequis"), ("donnees", "Données exactes"), ("actions", "Actions dans l'interface"),
                ("attendu", "Résultat attendu"), ("ecritures", "Écritures attendues"), ("fiscal", "Impacts fiscaux"),
                ("controles", "Contrôles"), ("statut", "Statut"), ("resultat_reel", "Résultat réel"),
                ("anomalies", "Anomalies constatées"), ("observations", "Observations / limites"),
                ("preuve", "Preuve attendue"), ("preuve_reelle", "Preuves / captures obtenues")]


def balance_rows(data, opening=False):
    rows = []
    for account, values in sorted(balances(data["operations"]).items()):
        if opening and account[0] in "67":
            continue
        signed = dec(values["debit"])-dec(values["credit"])
        if signed:
            rows.append({"compte": account, "debit": str(max(signed, dec(0))), "credit": str(max(-signed, dec(0)))})
    if opening:
        rows.append({"compte": "1191", "debit": "0.00", "credit": data["attendus"]["resultat_net"]})
    assert sum((dec(r["debit"])-dec(r["credit"]) for r in rows), dec(0)) == 0
    return sorted(rows, key=lambda r:r["compte"])


def balance_avant_is(data):
    source={**data,"operations":[e for e in data["operations"] if e["reference_recette"] not in {"IS-2025","PPRF-IMP"}]}
    return balance_rows(source)


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer=csv.DictWriter(f, fieldnames=fields, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def make_xlsx(data, cases, destination):
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.worksheet.table import Table, TableStyleInfo
    from openpyxl.utils import get_column_letter
    wb=Workbook()
    dash=wb.active
    dash.title="Synthèse"
    navy="16324F"
    blue="EAF1F8"
    def sheet(title, headers, rows, widths=None):
        ws=wb.create_sheet(title)
        ws.append(headers)
        for row in rows:
            ws.append(row)
        ws.freeze_panes="A2"
        ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:
            c.fill=PatternFill("solid",fgColor=navy)
            c.font=Font(color="FFFFFF",bold=True)
            c.alignment=Alignment(wrap_text=True,vertical="center")
        ws.row_dimensions[1].height=34
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment=Alignment(vertical="top",wrap_text=True)
                if c.row%2==0:
                    c.fill=PatternFill("solid",fgColor="F3F7FB")
        for i in range(1,len(headers)+1):
            ws.column_dimensions[get_column_letter(i)].width=(widths or {}).get(i,22)
        ws.sheet_properties.pageSetUpPr.fitToPage=True
        ws.page_setup.orientation="landscape"
        ws.page_setup.paperSize=ws.PAPERSIZE_A3
        ws.page_setup.fitToWidth=1
        ws.page_setup.fitToHeight=0
        ws.print_title_rows="1:1"
        ws.oddFooter.center.text="HisabPro — recette isolée — &P / &N"
        return ws
    dash.append([TITLE])
    dash.append([VERSION])
    dash.append(["Recette utilisateur à effectuer. Aucun succès prérempli."])
    dash.append(["Les tests automatisés et la recette utilisateur sont deux validations distinctes."])
    dash.append(["Domaine","Total","Non testé","Réussi","Échoué","Bloqué","Avancement","Évalués hors blocages"])
    domain_rows={}
    for index, domain in enumerate(DOMAINS,start=6):
        subset=[c for c in cases if c["module"]==domain]
        ws=sheet(domain,[label for _,label in CASE_COLUMNS],[[c[key] for key,_ in CASE_COLUMNS] for c in subset],
                 {1:8,2:19,3:22,4:35,5:42,6:55,7:76,8:68,9:54,10:49,11:49,12:16,13:48,14:45,15:45,16:44,17:42})
        validation=DataValidation(type="list",formula1='"'+",".join(STATUSES)+'"',allow_blank=False)
        validation.errorTitle="Statut de recette"
        validation.error="Choisir Non testé, Réussi, Échoué ou Bloqué."
        validation.showErrorMessage=True
        ws.add_data_validation(validation)
        validation.add(f"L2:L{len(subset)+1}")
        for status, color in [("Réussi","DFF1DE"),("Échoué","FCDDDD"),("Bloqué","FFF0CF")]:
            ws.conditional_formatting.add(f"L2:L{len(subset)+1}",CellIsRule(operator="equal",formula=['"'+status+'"'],fill=PatternFill("solid",fgColor=color)))
        for row in range(2,len(subset)+2):
            ws.row_dimensions[row].height=180
        end=len(subset)+1
        dash.append([domain,f"=COUNTA('{domain}'!B2:B{end})",*[f'=COUNTIF(\'{domain}\'!L2:L{end},"{s}")' for s in STATUSES],f"=IFERROR((D{index}+E{index})/B{index},0)",f"=IFERROR((D{index}+E{index})/(B{index}-F{index}),0)"])
        domain_rows[domain]=index
    total=6+len(DOMAINS)
    dash.append(["TOTAL",*[f"=SUM({get_column_letter(col)}6:{get_column_letter(col)}{total-1})" for col in range(2,7)],f"=IFERROR((D{total}+E{total})/B{total},0)",f"=IFERROR((D{total}+E{total})/(B{total}-F{total}),0)"])
    dash.append(["Avancement = (réussis + échoués) / total. Une anomalie bloquante ne vaut jamais une réussite."])
    dash.append(["Ouvrir l'onglet Ordre de passage, suivre ses identifiants, puis renseigner les résultats dans l'onglet du domaine."])
    for i in range(1,5):
        dash.merge_cells(start_row=i,start_column=1,end_row=i,end_column=8)
        dash.cell(i,1).alignment=Alignment(wrap_text=True)
        dash.row_dimensions[i].height=32
    dash.cell(1,1).font=Font(bold=True,size=17,color=navy)
    for c in dash[5]:
        c.fill=PatternFill("solid",fgColor=navy);c.font=Font(color="FFFFFF",bold=True)
    dash.column_dimensions["A"].width=29
    for col in "BCDEF":dash.column_dimensions[col].width=14
    for col in "GH":dash.column_dimensions[col].width=23
    for row in range(6,total+1):
        dash.cell(row,7).number_format="0.0%";dash.cell(row,8).number_format="0.0%"
    dash.freeze_panes="B6"
    chart=BarChart()
    chart.type="bar";chart.grouping="stacked";chart.overlap=100
    chart.title="Progression de la recette par domaine"
    chart.add_data(Reference(dash,min_col=3,max_col=6,min_row=5,max_row=total-1),titles_from_data=True)
    chart.set_categories(Reference(dash,min_col=1,min_row=6,max_row=total-1))
    chart.height=14;chart.width=26
    dash.add_chart(chart,"A25")
    order=sheet("Ordre de passage",["Ordre","Identifiant","Domaine","Objectif","Onglet à renseigner"],[[c["ordre"],c["id"],c["module"],c["objectif"],c["module"]] for c in cases],{1:8,2:20,3:23,4:65,5:24})
    for row,c in enumerate(cases,start=2):
        order.cell(row,5).hyperlink=f"#'{c['module']}'!A1"
        order.cell(row,5).style="Hyperlink"
    results=sheet("Résultats chiffrés",["Contrôle indépendant","Valeur attendue","Résultat réel","Écart réel − attendu","Preuve"],[[libelle_controle(k),float(dec(v)),"","",""] for k,v in data["attendus"].items()],{1:43,2:24,3:24,4:24,5:60})
    for row,(key,value) in enumerate(data['attendus'].items(),start=2):
        results.cell(row,4).value=f'=IF(C{row}="","",C{row}-B{row})'
        for column in (2,3,4):
            results.cell(row,column).number_format='0.00" %"' if key=='taux_is' else '#,##0.00'
    sheet("Journal attendu",["Référence recette","Date","Journal","Libellé","Compte","Débit","Crédit","Tiers symbolique"],[[x[k] for k in ("reference_recette","date","journal","libelle","compte","debit","credit","tiers")] for x in data["journal_attendu"]],{1:24,2:15,3:12,4:54,5:15,6:19,7:19,8:23})
    sheet("Balance N",["compte","debit","credit"],[[r[k] for k in ("compte","debit","credit")] for r in balance_rows(data)],{1:18,2:22,3:22})
    sheet("À-nouveaux 2026",["Compte","Débit","Crédit"],[[r[k] for k in ("compte","debit","credit")] for r in balance_rows(data,True)],{1:18,2:22,3:22})
    sheet("Relevé bancaire",["Date","Libellé","Débit","Crédit"],[[r[k] for k in ("Date","Libellé","Débit","Crédit")] for r in data["releve_bancaire"]],{1:16,2:65,3:23,4:23})
    sheet("Balance avant IS",["compte","debit","credit"],[[r[k] for k in ("compte","debit","credit")] for r in balance_avant_is(data)],{1:18,2:22,3:22})
    sheet("TVA mensuelle",["Mois","Crédit ouverture","Collectée","Récupérable","Crédit fin","Due"],[[r[k] for k in ("mois","credit_ouverture","collectee","recuperable","credit_fin","due")] for r in data["tva_mois"]],{1:15,2:23,3:23,4:23,5:23,6:23})
    sheet("Variantes conditionnelles",["Référence","Statut","Condition préalable","Deltas / données","Attendus conditionnels"],[[v["reference"],v["statut"],v["condition"],json.dumps(v["deltas_conditionnels"],ensure_ascii=False),json.dumps(v["attendus_conditionnels"],ensure_ascii=False)] for v in data["variantes_independantes"]],{1:20,2:18,3:90,4:70,5:85})
    sheet("Identité et paramètres",["Champ","Valeur exacte"],[[k,str(v)] for k,v in data["societe"].items()],{1:35,2:100})
    sheet("Sources officielles",["Référence","Document","URL","Vérification / limites"],[[s[k] for k in ("id","titre","url","verification")] for s in SOURCES],{1:23,2:55,3:95,4:100})
    limits=[c for c in cases if c["statut"]=="Bloqué"]
    sheet("Limites restantes",["Identifiant","Domaine","Fonction","Motif","Action suivante","Statut"],[[c["id"],c["module"],c["objectif"],c["observations"],c["actions"],"Bloqué"] for c in limits],{1:20,2:25,3:48,4:75,5:85,6:16})
    # Les écritures/refs et comptes restent du texte ; les références 02/002 ne
    # subissent donc jamais la conversion Excel en nombre.
    from openpyxl.workbook.properties import CalcProperties
    wb.calculation=CalcProperties(calcMode="auto",fullCalcOnLoad=True)
    wb.save(destination)


def make_pdf(data,cases,destination):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_root=Path("C:/Windows/Fonts")
    if (font_root/"arial.ttf").is_file():
        pdfmetrics.registerFont(TTFont("RecetteArial",str(font_root/"arial.ttf")))
        pdfmetrics.registerFont(TTFont("RecetteArialBold",str(font_root/"arialbd.ttf")))
        pdfmetrics.registerFontFamily("RecetteArial",normal="RecetteArial",bold="RecetteArialBold")
        normal,bold="RecetteArial","RecetteArialBold"
    else:
        normal,bold="Helvetica","Helvetica-Bold"
    navy=colors.HexColor("#16324F")
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle("CoverRecette",fontName=bold,fontSize=24,leading=30,textColor=navy,spaceAfter=20))
    styles.add(ParagraphStyle("HeaderRecette",fontName=bold,fontSize=15,leading=20,textColor=navy,spaceBefore=15,spaceAfter=10))
    styles.add(ParagraphStyle("CaseRecette",fontName=bold,fontSize=12,leading=16,textColor=navy,spaceBefore=14,spaceAfter=7,keepWithNext=True))
    styles.add(ParagraphStyle("BodyRecette",fontName=normal,fontSize=9,leading=13,spaceAfter=7))
    styles.add(ParagraphStyle("SmallRecette",fontName=normal,fontSize=7.5,leading=10,spaceAfter=3))
    styles.add(ParagraphStyle("LabelRecette",fontName=bold,fontSize=8.5,leading=12,textColor=navy))
    story=[]
    def para(text,style="BodyRecette"):
        return Paragraph(escape(str(text)).replace("\n","<br/>"),styles[style])
    def table(headers,rows,widths):
        content=[[para(v,"SmallRecette") for v in headers]]+[[para(v,"SmallRecette") for v in row] for row in rows]
        t=Table(content,colWidths=widths,repeatRows=1,hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#EAF1F8")),("TEXTCOLOR",(0,0),(-1,0),navy),("VALIGN",(0,0),(-1,-1),"TOP"),("LINEBELOW",(0,0),(-1,0),.8,navy),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F5F8FB")]),("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        return t
    story.extend([Spacer(1,22*mm),para(TITLE,"CoverRecette"),para(VERSION,"HeaderRecette"),Spacer(1,10*mm),para("Du premier compte utilisateur à la clôture, aux à-nouveaux et au dossier fiscal annuel."),para("ATLAS RECETTE HISABPRO SARL — FICTIVE","HeaderRecette"),para("Jeu exclusivement destiné à un environnement isolé. Les identités, identifiants et justificatifs sont fictifs. Aucun dépôt réel ni modification des données de production."),para(f"{len(cases)} cas de test · {len(DOMAINS)} domaines · {len(data['operations'])} écritures attendues avant clôture."),para("État de départ : recette utilisateur à effectuer. Aucun cas prérempli comme réussi. Les contrôles automatisés des fichiers ne constituent pas une recette fonctionnelle ni une validation réglementaire."),PageBreak()])
    story.extend([para("1. Mode d'emploi et critères d'acceptation","HeaderRecette"),para("Le technicien prépare une base PostgreSQL vierge isolée et transmet l'URL à la personne chargée de recette. Celle-ci suit les identifiants dans l'ordre du parcours ci-dessous et dans l'onglet Ordre de passage. Les résultats sont saisis dans les onglets de domaine du classeur : Statut, Résultat réel, Anomalies, Preuves / captures."),para("À chaque cas, enregistrer puis recharger la page, comparer au résultat attendu et joindre la capture/document demandé. Une différence ouvre une anomalie ; un prérequis indisponible donne Bloqué. Arrêter le parcours dépendant et poursuivre les cas indépendants. Les cas négatifs et variantes sont exécutés sur une copie adaptée, sans altérer les soldes du scénario principal."),para("Les opérations 2025 sont saisies historiquement dans un exercice encore ouvert. La date réelle d'opération des chèques/effets est explicitement renseignée. Les dates d'échéance proviennent des contrats du scénario ; aucune date comptable n'est utilisée comme échéance par défaut."),para("Les numéros de factures et écritures attribués par l'application peuvent différer des repères REC. Reporter les véritables numéros dans les preuves et conserver la relation avec le repère du cahier. C-MARCH et F-MARCH désignent des tiers fictifs ; leur auxiliaire technique est généré par HisabPro."),para("Développement terminé : fonctionnalités présentes et limites classées. Tests automatisés validés : exécutions réellement réussies avec logs. Recette utilisateur : chaque parcours réellement exécuté et accepté. Prêt pour mise en production : ces étapes, les validations PostgreSQL/navigateur et la revue réglementaire/déploiement sont satisfaites. Aucun de ces statuts ne découle automatiquement d'un test unitaire."),para("Limites de périmètre","HeaderRecette"),para("La paie/CNSS n'est pas rendue obligatoire par la roadmap actuelle. La consolidation, les connecteurs bancaires et un dépôt automatique sont hors de ce scénario. Les étapes 09B/09C/09E/09F/09G/09H restent bloquées pour leur portée complète. 09D permet une préparation indépendante de balances conservée en versions immuables ; il ne constitue pas un dossier Liasse seule fiscal complet. L'archive existante est une archive interne, pas une preuve de dépôt DGI."),para("Validation fiscale avant clôture","HeaderRecette"),para("Taux IS du scénario de droit commun : 17,5 % en 2025 pour ce niveau de bénéfice, 20 % pour la référence des acomptes 2026. TVA normale : 20 %. Les qualifications d'exonération CM/CSS, les cut-off TVA, les exclusions de déduction et retenues doivent être revus avec le texte applicable complet. Le calcul IS du scénario est supérieur à la CM de contrôle même sans exonération ; la qualification CM reste signalée sans être fabriquée."),PageBreak()])
    story.append(para("2. Données exactes à préparer","HeaderRecette"))
    story.append(table(["Champ","Valeur"],[[k,v] for k,v in data["societe"].items()],[55*mm,120*mm]))
    story.append(para("Tiers et articles","HeaderRecette"))
    story.append(table(["Repère tiers","Nom","Type / compte"],[[t["code"],t["nom"],t["type"]+" / "+t["compte"]] for t in data["tiers"]],[33*mm,90*mm,52*mm]))
    story.append(table(["Article","Données exactes"],[[a["code"],json.dumps(a,ensure_ascii=False)] for a in data["articles"]],[25*mm,150*mm]))
    story.append(para("Pièces justificatives fictives","HeaderRecette"))
    story.append(para("Pour chaque opération : facture/contrat/avis portant le repère indiqué et les montants exacts. Assurance ASS-01 : couverture 01/12/2025–30/11/2026, prime 12 000 sans TVA sur cet avis. FNP-01 : service achevé en décembre, 3 000 HT. FAE-01 : uniquement dans la variante indépendante bloquée, exclue de tous les totaux principaux. REC-LIT01 : risque probable 1 500, conditions fiscales non satisfaites dans ce test. REC-DEP01 : perte probable client 2 000, conditions fiscales non satisfaites. INT-PPRF : intérêt brut 1 000, retenue documentaire 200, net bancaire 800. Les justificatifs à joindre sont énumérés dans le fichier justificatifs_fictifs.md."))
    story.append(para("3. Oracle financier indépendant","HeaderRecette"))
    story.append(table(["Contrôle","Valeur attendue"],[[libelle_controle(k),v.replace('.',',')+' unités' if k=='stock_quantite' else v.replace('.',',')+' %' if k=='taux_is' else mad(v)] for k,v in data["attendus"].items()],[115*mm,60*mm]))
    story.append(para("Calculs essentiels","HeaderRecette"))
    story.append(para("Achats marchandises : 100 × 100 + 100 × 120 = 22 000. Stock : 200 achetés − 100 vendus + 10 retournés − 50 vendus = 60 ; CMUP = 110 ; stock final = 6 600. Ventes marchandises nettes : 25 000 − 2 500 + 15 000 = 37 500 ; marge brute = 37 500 − (22 000 − 6 600) = 22 100."))
    story.append(para("Produits : marchandises 37 500 + prestations 120 000 + impayé 12 000 + intérêts 1 000 = 170 500. Charges hors IS : achats nets de variation 15 400 + services 12 000 + contrôles 400 + FNP 3 000 + assurance de décembre 1 000 + amortissement 4 800 + provision durable 1 500 + dépréciation 2 000 + frais 70 + amende 500 = 40 670. Résultat avant IS = 129 830. Réintégrations = 500 + 1 500 + 2 000 = 4 000 ; bénéfice fiscal = 133 830 ; IS = 133 830 × 17,5 % = 23 420,25. Crédit IS = 200 ; solde = 23 220,25 ; résultat net = 106 409,75."))
    story.append(para("CAF : résultat net 106 409,75 + dotation immobilisation 4 800 + provision durable 1 500 = 112 709,75. La dépréciation circulante 2 000 n'est pas ajoutée à cette CAF. Actif net : ordinateur 19 200 + stock 6 600 + clients nets 12 400 + TVA non encore récupérable 80 + CCA 11 000 + banque 287 730 = 337 010. Passif : capital 200 000 + résultat net 106 409,75 + provision 1 500 + fournisseurs 480 + FNP 3 000 + dette IS 23 220,25 + dette TVA 2 400 = 337 010."))
    story.append(table(["Mois","Collectée","Récupérable","Crédit fin","Due"],[[r['mois']]+[mad(r[k]) for k in ('collectee','recuperable','credit_fin','due')] for r in data["tva_mois"]],[20*mm,39*mm,39*mm,39*mm,38*mm]))
    story.append(para("Variante de FAE : effet distinct et conditionnel","HeaderRecette"))
    story.append(para("La version initiale incluait une FAE de 6 000 sans preuve du traitement TVA. Elle est désormais exclue du principal : produits et bénéfice fiscal diminuent de 6 000, IS de 1 050, résultat net de 4 950, actif de 6 000. Sous hypothèse qualifiée d'une FAE taxable à 20 % au débit en N, la variante porterait une créance TTC de 7 200 et TVA de 1 200 : résultat avant IS 135 830, bénéfice fiscal 139 830, IS 24 470,25, résultat net 111 359,75, actif/passif 344 210 et TVA finale due 3 600. Ces chiffres conditionnels ne sont jamais à ajouter au principal tant que la qualification et le rapprochement TVA sont bloqués."))
    story.append(PageBreak())
    story.append(para("4. Parcours de recette dans l'ordre","HeaderRecette"))
    for c in cases:
        story.append(para(f"{c['ordre']:03} · {c['id']} · {c['module']}\n{c['objectif']}","CaseRecette"))
        for label,key in [("Prérequis","prerequis"),("Données exactes","donnees"),("Actions","actions"),("Résultat attendu","attendu"),("Écritures attendues","ecritures"),("Impacts fiscaux","fiscal"),("Contrôles","controles"),("Statut initial","statut"),("Observations / limites","observations"),("Preuve attendue","preuve")]:
            if c[key]:
                story.append(Paragraph("<b>"+escape(label)+" :</b> "+escape(str(c[key])).replace("\n","<br/>"),styles["BodyRecette"]))
        story.append(para("Résultat réel / anomalie / lien de preuve : à renseigner dans le classeur Excel.","SmallRecette"))
    story.append(PageBreak())
    story.append(para("5. Journal indépendant et à-nouveaux","HeaderRecette"))
    for e in sorted(data["operations"],key=lambda x:x["date"]):
        story.append(para(f"{e['date']} · {e['journal']} · {e['reference_recette']} · {e['description']}","CaseRecette"))
        story.append(para(entry_text(e)))
    story.append(para("À-nouveaux 2026 : reprise des comptes de bilan","HeaderRecette"))
    story.append(table(["Compte","Débit","Crédit"],[[r[k] for k in ("compte","debit","credit")] for r in balance_rows(data,True)],[55*mm,60*mm,60*mm]))
    story.append(para("Contrepassations distinctes au 01/01/2026 : CCA D6134/C3491 11 000 ; FNP D4417/C6125 3 000. Aucune FAE dans le principal. Paiements N+1 : TVA 2 400 le 20/01, IS 23 220,25 le 31/03 ; banque résiduelle 262 109,75 avant toute autre opération 2026. Acomptes 2026 : référence 133 830 × 20 % = 26 766 ; quart 6 691,50 ; versements du cas 6 691,50 puis 2 000, à comptabiliser séparément D3453/C5141."))
    story.append(PageBreak())
    story.append(para("6. Sources officielles et limites de vérification","HeaderRecette"))
    for s in SOURCES:
        story.append(para(s["id"]+" — "+s["titre"],"CaseRecette"))
        story.append(para(s["verification"]))
        story.append(Paragraph('<link href="'+escape(s["url"])+ '">'+escape(s["url"])+"</link>",styles["SmallRecette"]))
    story.append(para("Les références ne dispensent pas de vérifier le millésime, les qualifications et les versions applicables. Les limites restantes sont listées dans l'onglet Limites restantes et le registre Markdown. Le dossier est un instrument de recette ; sa génération ne valide ni les soldes réels ni la conformité réglementaire."))
    def decorate(canvas,doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#CAD8E6"))
        canvas.line(18*mm,16*mm,192*mm,16*mm)
        canvas.setFont(normal,7)
        canvas.setFillColor(navy)
        canvas.drawString(18*mm,11*mm,"HisabPro · Recette isolée · 2025 / 2026")
        canvas.drawRightString(192*mm,11*mm,str(doc.page))
        canvas.restoreState()
    class RecetteDocument(SimpleDocTemplate):
        def afterFlowable(self, flowable):
            if isinstance(flowable, Paragraph):
                text=flowable.getPlainText()
                if flowable.style.name=="HeaderRecette" and re.match(r"^[1-6]\. ",text):
                    key="section-"+text[0]
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(text,key,level=0,closed=False)
                elif flowable.style.name=="CaseRecette" and re.match(r"^\d{3} · HP-",text):
                    key=re.search(r"HP-[A-Z]+-\d{3}",text).group(0)
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(text,key,level=1,closed=True)
    doc=RecetteDocument(str(destination),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=22*mm,title=TITLE,author="HisabPro — Cahier de recette",subject="Scénario fictif et oracle indépendant")
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)


def make_proofs(data, destination):
    """Fiches fictives téléversables ; jamais des factures ou attestations réelles."""
    import hashlib
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.pdfbase import pdfmetrics
    font='RecetteArial' if 'RecetteArial' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
    bold='RecetteArialBold' if font=='RecetteArial' else 'Helvetica-Bold'
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for entry in data['operations']:
        reference=entry['reference_recette']
        assert re.fullmatch(r'[A-Z0-9-]+',reference)
        path=destination/(reference+'.pdf')
        header=ParagraphStyle('ProofHeader',fontName=bold,fontSize=16,leading=22,textColor=colors.HexColor('#16324F'),spaceAfter=18)
        body=ParagraphStyle('ProofBody',fontName=font,fontSize=10,leading=15,spaceAfter=12)
        paragraphs=[
            'FICHE DE RECETTE FICTIVE — '+reference,
            'ATLAS RECETTE HISABPRO SARL — FICTIVE',
            'Données de test réservées à une base isolée. Ce document ne constitue ni une facture authentique ni une attestation fiscale ou bancaire. Aucun justificatif réel ne peut en être déduit.',
            'Date de la pièce fictive : '+entry['date']+' ; journal attendu : '+entry['journal']+'.',
            entry['description'],
            'Schéma attendu dans le laboratoire : '+entry_text(entry),
            'La référence de la fiche désigne le repère du cahier ; les numéros attribués par l’application doivent être consignés séparément dans les preuves de recette.',
        ]
        story=[Paragraph(escape(paragraphs[0]),header),Spacer(1,12)]
        story.extend(Paragraph(escape(text),body) for text in paragraphs[1:])
        SimpleDocTemplate(str(path),pagesize=A4,title=paragraphs[0],author='HisabPro — données fictives de recette').build(story)
        manifest.append({'reference':reference,'fichier':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'date_piece_fictive':entry['date']})
    write_csv(destination/'manifest.csv',manifest,('reference','fichier','sha256','date_piece_fictive'))


def negative_inputs():
    return {
        'balance_desequilibree.csv':(('compte','debit','credit'),[{'compte':'5141','debit':'100','credit':'0'},{'compte':'1111','debit':'0','credit':'99'}]),
        'balance_compte_inconnu.csv':(('compte','debit','credit'),[{'compte':'5141','debit':'100','credit':'0'},{'compte':'7999999999','debit':'0','credit':'100'}]),
        'balance_compte_double.csv':(('compte','debit','credit'),[{'compte':'5141','debit':'50','credit':'0'},{'compte':'5141','debit':'50','credit':'0'},{'compte':'1111','debit':'0','credit':'100'}]),
        'balance_montant_nan.csv':(('compte','debit','credit'),[{'compte':'5141','debit':'NaN','credit':'0'},{'compte':'1111','debit':'0','credit':'100'}]),
        'balance_resultat_et_gestion.csv':(('compte','debit','credit'),[{'compte':'5141','debit':'200','credit':'0'},{'compte':'1191','debit':'0','credit':'100'},{'compte':'7124','debit':'0','credit':'100'}]),
        'releve_debit_credit_simultanes.csv':(('Date','Libellé','Débit','Crédit'),[{'Date':'31/12/2025','Libellé':'ERREUR-TEST','Débit':'1000','Crédit':'1000'}]),
    }


def generate(destination=OUT):
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    data=build_data()
    cases=build_cases(data)
    data["cas_recette"]=cases
    (destination/"jeu_donnees_recette.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    write_csv(destination/"journal_attendu_2025.csv",data["journal_attendu"],("reference_recette","date","journal","libelle","compte","debit","credit","tiers"))
    write_csv(destination/"balance_attendue_2025.csv",balance_rows(data),("compte","debit","credit"))
    write_csv(destination/"balance_avant_is_2025.csv",balance_avant_is(data),("compte","debit","credit"))
    write_csv(destination/"a_nouveaux_attendus_2026.csv",balance_rows(data,True),("compte","debit","credit"))
    write_csv(destination/"releve_banque_recette_2025.csv",data["releve_bancaire"],("Date","Libellé","Débit","Crédit"))
    from openpyxl import Workbook
    for filename,headers,rows in [("releve_banque_recette_2025.xlsx",("Date","Libellé","Débit","Crédit"),data["releve_bancaire"]),("balance_attendue_2025.xlsx",("compte","debit","credit"),balance_rows(data)),("balance_avant_is_2025.xlsx",("compte","debit","credit"),balance_avant_is(data))]:
        wb=Workbook();ws=wb.active;ws.title="Relevé" if "releve" in filename else "Balance N"
        ws.append(headers)
        for row in rows:
            ws.append([row[h] if h not in ("Débit","Crédit","debit","credit") else float(dec(row[h])) for h in headers])
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=65 if col[0].value=="Libellé" else 23
        wb.save(destination/filename)
    make_xlsx(data,cases,destination/"CAHIER_RECETTE_HISABPRO.xlsx")
    make_pdf(data,cases,destination/"CAHIER_RECETTE_HISABPRO.pdf")
    make_proofs(data,destination/'justificatifs')
    (destination/'negatifs').mkdir(exist_ok=True)
    for filename,(headers,rows) in negative_inputs().items():
        write_csv(destination/'negatifs'/filename,rows,headers)
    readme=f"""# {TITLE}

Version : {VERSION}.

## Utilisation

1. Faire préparer une base PostgreSQL isolée et vierge par le technicien.
2. Lire le PDF puis suivre les {len(cases)} cas dans l'ordre. Le classeur contient une feuille par domaine et un tableau de bord calculé depuis les statuts.
3. Saisir les résultats dans les colonnes Statut, Résultat réel, Anomalies, Preuves / captures. Tous les cas sont initialement Non testé ou Bloqué.
4. Comparer les valeurs aux annexes calculées indépendamment par `Decimal`, sans importer les calculs métier de HisabPro.
5. Utiliser une copie pour les variantes et cas négatifs ; ne jamais altérer la société principale pour provoquer une erreur.

Le PDF et le classeur sont les livrables de recette. Les CSV/XLSX de balance et relevé sont des fichiers d'entrée ; le journal attendu est une annexe de contrôle, pas un import automatique. Utiliser `balance_avant_is_2025` avant constat/imputation d'IS, puis `balance_attendue_2025` après ces deux écritures et avant le soldage technique. Les références fournisseurs `02` et `002` restent textuelles et désignent deux pièces distinctes.

Le dossier `justificatifs/` contient une fiche PDF fictive par opération et un manifeste SHA-256. Ces fiches servent à tester le téléversement et la restitution des pièces ; elles ne sont pas des justificatifs authentiques ni des modèles de factures réglementaires. Le cas de complément documentaire au Journal utilise `justificatifs/CAP-01.pdf`.

**Développement terminé**, **tests automatisés validés**, **recette utilisateur effectuée** et **prêt pour mise en production** sont quatre décisions distinctes. Ce dossier ne préremplit aucun succès utilisateur et ne prétend pas à une certification officielle.

## Chiffres centraux

- Actif net / passif : 337 010 MAD.
- Banque : 287 730 MAD ; stock : 60 × 110 = 6 600 MAD.
- Résultat avant IS : 129 830 MAD ; bénéfice fiscal : 133 830 MAD.
- IS 2025 : 23 420,25 MAD ; crédit documentaire : 200 MAD ; solde : 23 220,25 MAD.
- Résultat net : 106 409,75 MAD ; CAF : 112 709,75 MAD.
- TVA collectée : 33 900 MAD ; récupérable : 11 600 MAD ; dette finale : 2 400 MAD après paiement 19 900 MAD.

La FAE de 6 000 HT a été isolée dans une variante indépendante bloquée : elle ne fait pas partie de ces totaux. Le contrat et le fait générateur TVA doivent être qualifiés avant saisie. Sous hypothèse qualifiée taxable à 20 % au débit, sa créance TTC serait 7 200 et TVA 1 200 ; le JSON et l'onglet Variantes conditionnelles précisent les effets financiers. La version initiale qui la comprenait sans preuve de TVA ne doit plus servir de référence.

## Génération reproductible, sans connexion DB

```powershell
& '.\\hisabpro-backend\\.venv\\Scripts\\python.exe' 'Test/generer_cahier_recette.py'
& '.\\hisabpro-backend\\.venv\\Scripts\\python.exe' -m pytest 'Test/test_session132_cahier_recette.py' -q
```

Dépendances : `openpyxl`, `reportlab`, `pypdf` pour les tests PDF. Le générateur n'ouvre aucune connexion PostgreSQL. Les procédures d'installation/sauvegarde/restauration/déploiement sont livrées séparément avec l'audit de session ; ces cas figurent dans l'onglet Exploitation.

## Limites

Les étapes 09B/09C/09E/09F/09G/09H ne permettent pas une validation complète du dépôt fiscal. Le parcours 09D est décrit comme une préparation indépendante, sans création d'écritures et sans déclaration prête à déposer. La retenue TVA article 117 n'est pas entièrement automatisée. La CM du jeu fictif est documentée sous les dates explicites du scénario ; la qualification réelle CM/CSS et la TVA des cut-off restent à documenter. Consulter `REGISTRE_LIMITES_RECETTE.md` et les sources officielles du PDF/classeur. Procédures techniques : [EXPLOITATION_HISABPRO.md](../EXPLOITATION_HISABPRO.md).
"""
    (destination/"README.md").write_text(readme,encoding="utf-8")
    limits="# Registre des anomalies et limites de recette\n\nToutes les entrées ci-dessous sont des limites initiales, aucune donnée historique réelle n'est réparée artificiellement.\n\n"
    for c in cases:
        if c["statut"]=="Bloqué":
            limits+=f"## {c['id']} — {c['objectif']}\n\n{c['observations']}\n\nAction : {c['actions']}\n\n"
    limits+="## HP-FAC-012 — Limite d'envoi externe des relances\n\nLa création, l'historique, la modification et l'annulation sont disponibles dans Facturation → Situation financière pour les rôles autorisés ; la recette utilisateur reste Non testé. L'envoi externe automatique n'est pas implémenté : enregistrer une relance journalise une action effectuée hors application, sans preuve automatique de transmission. Ne pas assimiler cette limite à l'absence des parcours de suivi existants.\n\n"
    limits+="## Validation transverse\n\nLes autres cas restent Non testé. La validation PostgreSQL réelle, les parcours navigateur de bout en bout, la revue réglementaire et la sauvegarde/restauration complète doivent être exécutés dans un environnement isolé puis documentés. Ne pas supprimer les anomalies de sources FEC/ETIC lorsque les justificatifs manquent.\n"
    (destination/"REGISTRE_LIMITES_RECETTE.md").write_text(limits,encoding="utf-8")
    proof="# Justificatifs fictifs du scénario\n\nCes documents servent uniquement au laboratoire ; aucune attribution officielle ni facture réelle. Les références et montants ci-dessous permettent au recetteur de créer ou joindre une pièce synthétique marquée FICTIVE.\n\n"
    for e in data["operations"]:
        proof+=f"## {e['reference_recette']} — {e['date']}\n\n{e['description']}\n\n{entry_text(e)}\n\n"
    proof+="## Contrats et qualifications\n\nASS-01 : prime 12 000, couverture 01/12/2025 au 30/11/2026, sans TVA sur cet avis fictif. FNP-01 : réception de service décembre, 3 000 HT, échéance contractuelle 31/01/2026. FAE-01 : variante indépendante bloquée uniquement ; prestation réceptionnée 31/12/2025, 6 000 HT, facture et échéance contractuelle 31/01/2026. Qualification TVA à documenter avant saisie ; aucune FAE dans le principal. REC-LIT01 : provision durable 1 500, conditions fiscales explicitement non satisfaites. REC-DEP01 : perte client estimée 2 000, conditions fiscales explicitement non satisfaites. INT-PPRF : avis intérêts bruts 1 000, retenue documentaire 200, net 800 ; référence à saisir dans les crédits IS. Les valeurs d'engagements, devises, participations et sûretés sont néant uniquement parce que le scénario le stipule, jamais par inférence d'une base incomplète.\n"
    (destination/"justificatifs_fictifs.md").write_text(proof,encoding="utf-8")
    return data,cases


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=OUT)
    args=parser.parse_args()
    data,cases=generate(args.output)
    print(f"Cahier généré : {len(cases)} cas, {len(data['operations'])} écritures ; destination {args.output}.")
