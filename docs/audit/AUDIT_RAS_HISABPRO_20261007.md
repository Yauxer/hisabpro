# Audit RAS HisabPro — 7/8 octobre 2026

État : **RAS sur HT partielle ; RAS TVA absente**. Cet audit ne constitue pas
une validation réglementaire et n'autorise aucune réparation de données réelles.
Le dépôt courant et les expériences isolées sont les seules preuves de code.

## Fonctionnalités réellement présentes

| Domaine | État observé | Limite |
|---|---|---|
| Taux RAS de facture | Saisie de ras_taux, assiette = totalité du HT calculé | Qualification juridique du payeur, bénéficiaire et prestation non déterminée |
| Net théorique | Calcul total TTC moins RAS HT dans liste, PDF, recouvrement | Une retenue estimée n'est pas distinguée d'une retenue effectivement opérée/justifiée |
| Comptabilisation | Au premier règlement comptabilisé, OD pour la totalité de la RAS de facture | Aucun prorata par paiement ou preuve fiscale distincte |
| Vente | Débit 3453 / crédit compte client, auxiliaire rattaché | Nature du crédit d'impôt non qualifiée automatiquement |
| Achat | Débit compte fournisseur / crédit 4457, auxiliaire rattaché | Versement au Trésor et déclaration de retenue non orchestrés |
| Annulation | Contrepassation RAS lorsque le dernier règlement actif est annulé | Rejet de chèque/effet, paiement partiel et plusieurs règlements à tester ensemble |
| Crédits IS | Saisie documentée des crédits et montants déjà imputés sur acomptes | Aucun pont automatique démontré avec chaque OD RAS de facture |
| Acomptes commerciaux | Réception/versement, TVA, imputation, annulation, échéances | Aucun champ ni cycle de retenue à la source sur acompte |
| TVA article 117 | Limitation explicitement renvoyée par /api/tva | Pas de montant RAS TVA, d'attestation ni de déclaration dédiés |

Fichiers : routers/factures.py (_montant_ras et _situation_paiement_facture),
routers/commercial.py (création et annulation de règlement), acomptes.py,
services/recouvrement_service.py, routers/fiscalite.py et routers/tva.py.

## Références officielles et portée de vérification

La publication officielle du ministère rappelle l'extension de la RAS IS/TVA
à certains payeurs : banques/assurances et entreprises dont le CA HT du dernier
exercice clos atteint 500 millions MAD dès juillet 2026, puis seuils 350 millions
en 2027 et 200 millions en 2028. Elle décrit également la retenue IS de 5 % sur
les rémunérations concernées hors TVA et une échéance de reversement après le
paiement, la mise à disposition ou l'inscription en compte.
[Al Maliya, numéro spécial LF 2026, dispositions fiscales](https://www.finances.gov.ma/Maliya%20tawassol/SLF2026-Fr.pdf).

La doctrine DGI 2024 décrit la RAS TVA des articles 117-IV/V : qualification du
fournisseur et des opérations, attestation de régularité, listes réglementaires
et exclusions. Elle indique notamment un versement au cours du mois suivant
chaque paiement et des seuils d'exclusion par opération et fournisseur/mois.
Ces conditions ne peuvent pas être déduites d'un simple taux appliqué au HT.
[Note circulaire DGI 735, LF 2024](https://www.finances.gov.ma/Publication/dgi/2024/Note-Circulaire735LF2024.pdf).

Le texte consolidé actuel doit cadrer les articles 15 bis, 19, 73, 117, 151, 157
et les dispositions transitoires de l'article 247 selon le cas étudié.
[CGI 2026, ministère des Finances](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf).
L'information officielle sur l'attestation constitue une autre référence utile.
[Communication MEF/DGI sur la RAS TVA](https://www.finances.gov.ma/fr/pages/detail-actualite.aspx?fiche=6947).

Les extraits indexés des publications primaires ont été consultés. Les ouvertures
directes des PDF ont rencontré des timeouts pendant cette session ; l'intégralité
du CGI consolidé, de la note 737 et du BO applicable n'a pas été récupérée dans ce
lot. Aucun barème, obligation ou format déclaratif nouveau n'a été codé à partir
de sources secondaires. Les détails réglementaires doivent être vérifiés sur les
textes complets avant une automatisation de la qualification ou de la RAS TVA.

## Anomalies techniques reproduites

### RAS-01 — pourcentage invalide persistant

Expérience réelle FastAPI/PostgreSQL temporaire avant correction : cinq POST de
factures fictives avec NaN, Infinity, true, -1 et 150 ont chacun renvoyé **201**
et persisté une facture. true était converti en 1 %. Le POST ne renvoyait pas
500 ; le schéma de sortie ne publiait pas ras_taux.

Le lot RAS-TAUX-FINIS-20261007 ajoute une validation avant coercition : valeur
finie, non booléenne, bornes mathématiques 0–100 ; PATCH null préserve le taux.
Aucun taux légal n'est prescrit. Les anciennes valeurs ne sont pas réécrites.
Preuves : Test/test_ras_taux_finis.py et Test/rapport_ras_taux_finis.md.

### RAS-02 — information supprimée à la lecture

Expérience réelle API isolée après création d'une facture à 10 % : le stockage
contenait ras_taux=10, mais GET /api/factures omettait ras_taux, montant_ras et
net_a_payer. FactureOut ne déclare pas ces champs ; le response_model les élimine.
Le formulaire d'édition initialise facture.ras_taux || 0 : une modification peut
alors transmettre zéro et effacer un taux existant. Le lot séparé
RAS-LECTURE-CONSERVATION-20261008 corrige cette sortie et vérifie une édition
réelle Edge conservant 10 %. Les anciens taux non finis/hors limites restent
inchangés en base, avec diagnostic et montants RAS indéterminables nulls.
Preuves : Test/test_ras_lecture_conservation.py et son rapport associé.

### RAS-03 — estimation assimilée à un paiement

Calcul exécuté : facture TTC 1 200, HT 1 000, RAS 10 %, aucun règlement ⇒ RAS 100,
reste 1 100 et statut partiellement_reglee. Le service compte la retenue estimée
dans total_impute même si aucune OD RAS ni preuve de retenue n'existe.
Ce comportement est établi ; la règle de qualification fiscale reste à décider
sur texte applicable et justificatifs. Aucun débit/crédit historique n'est modifié.

## Risques métier à traiter dans un lot qualifié

1. Distinguer RAS HT (IS/IR selon bénéficiaire/régime) et RAS sur le montant de TVA.
2. Déterminer les conditions du payeur à la date fiscale pertinente et le CA du
   dernier exercice clos, sans assimiler automatiquement toutes les sociétés.
3. Qualifier les lignes concernées et les exclusions ; une facture mixte ou des
   frais accessoires ne prouvent pas que la totalité du HT relève d'une retenue.
4. Identifier l'événement générateur réel : paiement, mise à disposition ou
   inscription en compte selon le texte applicable. Le premier règlement ne
   démontre pas à lui seul que toute la retenue de facture doit être constatée.
5. Gérer paiements partiels, acomptes et chèques/effets non encaissés ou rejetés,
   avec une trace distincte du montant retenu et de son justificatif.
6. Relier retenues effectivement subies, crédits fiscaux, versements au Trésor,
   déclarations et annexes annuelles sans double imputation.
7. Vérifier les comptes et la nature d'impôt selon le dossier ; les deux comptes
   génériques actuels ne prouvent pas une couverture universelle de toutes les RAS.

## Tests et ce qu'ils prouvent

- Avant correction numérique : 65 tests existants RAS/recouvrement/ETIC/acomptes
  réellement réussis en 24,52 s. Certains ETIC utilisent un banc ORM SQLite ;
  ils ne sont pas présentés comme validation PostgreSQL de ces contrôles.
- Après correction numérique : 42 ciblés réussis en 33,82 s, dont 11 API réelles
  sur PostgreSQL éphémère ; les valeurs invalides sont refusées sans mutation.
- Connexes après correction : 165 réussis en 67,63 s (les 65 précédents plus 100
  tests de documents numériques). Ces suites se recouvrent ; leurs nombres ne
  doivent pas être additionnés comme une couverture indépendante.
- Le cycle connecté acompte 400 → facture 1 200 → imputation 400 → règlement 800
  et lettrage est couvert par la recette E2E existante. Cette preuve ne contient
  aucune RAS ; elle ne valide donc pas la combinaison acompte + RAS.
- Les tests ETIC de recoupement RAS contrôlent montant, sens, compte, tiers et
  ambiguïtés d'une écriture donnée. Ils ne valident pas l'assujettissement fiscal.
- RAS HT partielle avec chèque/effet, rejet, annulation multiple, avoir et RAS TVA :
  scénario connecté et oracle qualifié manquants.

Aucune base réelle ni donnée comptable réelle n'a été utilisée. Aucun dépôt DGI,
reversement, réparation de facture définitive ou contrôle réglementaire validé
automatiquement. Priorité suivante : présenter le diagnostic historique dans les
formulaires et concevoir le flux de retenue effectivement opérée avec justificatifs et règles
applicables vérifiées, en gardant la RAS TVA explicitement incomplète jusque-là.
