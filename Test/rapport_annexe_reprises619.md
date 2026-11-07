# Lot619 — cahier de recette complémentaire des reprises615/617

Livrables WordOOXML, PDF25pages, Excel et JSON de données fictives.20cas
humains tous **Non testé** ; résultat réel/anomalies/preuves laissés vides.
Deux limites non exécutables **Bloqué** sont séparées du tableau de bord humain.
Préparation depuis société vierge, plan/calendriers/logo, dotation, reprises,
annulation, exports, FEC, lecteur, sociétés et scénarios négatifs détaillés.

L’Excel contient synthèse avec formules/progression/graphique, six domaines,
données à plat, oracle, Journal attendu10lignes, balance et limites. Colonnes
de résultat réel/anomalies/preuves et listes de statuts. Le recalcul interactif
dans Excel et la mise en page Word du partenaire ne sont pas prétendus testés.
Le Word réutilise le générateur OOXML existant du guide ; aucun paquet installé.

## Oracle indépendant et parcours réel

Calcul en centimes entiers, sans import des services métier. Capital20000,
dotation1000, reprises400+200, inverse400. Résultat avant impôt−800, provision800,
reprises actives200, disponible800 ; banque20000, actif=passif20000.
Journal final5pièces/10lignes, débit=crédit22000. Exercice2025 non clôturé,
aucune TVA, liquidation IS ou déductibilité estimée dans cette annexe.

Les données fixes sont reprises dans un vrai parcours Edge1440/390 et
PostgreSQL100 natif jetable : préparation société/capital/dotation par API,
reprises/validation/inverse via interface, états réels, FEC exporté et sommé,
suivi PDF réellement téléchargé ; capital et source définitive inchangés.
Cela ne vaut pas exécution humaine de RP-01 à TECH-RP01.

## Validation documentaire

6cas réussis en34.984s (4documentaires+2Edge) puis4contrôles documentaires sur les fichiers livrés en1.085s après précision des libellés5141/6195 ; aucun échec/ignoré final. Python compilé. PDF rendu et inspecté visuellement
(couverture et ficheRP-03),25pages. Les fichiers WordZIP/XML, champs/cas du PDF,
formules/validations Excel, jeu JSON et génération rejouable sont contrôlés.

Mise au point conservée : un test documentaire a d’abord échoué sur un titre
PDF réparti sur plusieurs lignes, normalisation d’espaces corrigée ; puis deux
parcours ont atteint les soldes/états attendus avant d’échouer dans le parseur
du test FEC (colonnes réelles Montant_Debit/Montant_Credit). Le parseur a été
corrigé, sans modification du produit, des comptes ou des montants attendus.

## Limites

Complément du cahier général, limité aux reprises liées et exports615/617.
Ce n’est pas la livraison finale de toute la roadmap. Les références/numéros
INV/ANN-REPRISE sont générés et doivent être relevés par le testeur. Les
justificatifs manquants et mouvements manuels ne sont pas inventés. Base réelle,
recette humaine, Excel interactif et mise en production non validés. RH/paie
restent différées.
