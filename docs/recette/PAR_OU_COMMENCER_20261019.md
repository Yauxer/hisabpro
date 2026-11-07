# HisabPro — ouvrir le bon dossier de recette

Point final du20octobre675 :[bilan de stabilisation et ZIPs](../audit/RAPPORT_STABILISATION_HORS_RH_20261020.md).
Les trois points techniques sont clôturés avec312tests communs réussis et
installation102 isolée contrôlée. La recette du périmètre disponible reste
à effectuer lors de la reprise du retour humain ; le guide et les cahiers
ci-dessous gardent leurs résultats vierges.

Complément du20octobre673 : [listes du cycle commercial](../COMMERCIAL_LISTES_673.md),
[preuves28tests](../../Test/rapport_listes_commerciales673.md) et
[liste bornée de sortie](../audit/FIN_DEVELOPPEMENT_HORS_RH_20261020.md).
Le guide Wordv15 reste disponible ci-dessous ; ce complément ajoute la reprise
des cinq listes et la séparation des factures Achat/Vente au-delà100pièces.
La recette humaine reste à effectuer.


Dernier point : **guide d’utilisation version15 et bilan645–671**,
[Word35pages](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.docx),
[PDF](../guide/GUIDE_UTILISATION_VERIFICATION_HISABPRO.pdf) et
[bilan avec ZIPs par étape](../audit/RAPPORT_SESSION_20261019_645_671.md).
Le guide inclut les annulations avec date/motif, erreurs de lecture, droits,
réceptions depuis commandes, documents RAS et parcours entre sociétés.
Les17résultats humains restent à renseigner ; les annexes et jeux ci-dessous
restent distincts. RH/paie et point6 humain différés.


Point du 19 octobre 2026, lots645–671, après633–643 et615–625. Les parcours ci-dessous utilisent des
sociétés fictives distinctes. La recette humaine reste en attente du retour
utilisateur ; aucun fichier de suivi n’a été prérempli en réussite.

## Présentation au partenaire

Dernier complément : **documents des OD RAS — version2, révision653**,
[Word](ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.docx),
[PDF de16pages](ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.pdf),
[Excel de suivi](ANNEXE_RECETTE_DOCUMENTS_RAS_20261019.xlsx),
[jeu chiffré révisé](donnees_recette_documents_ras_20261019.json) et
[PDF fictif à joindre](DOCUMENT_FICTIF_649.pdf).
12cas humains Non testé : capital100000, achat12000TTC, virement5250 et
capture750, documents puis annulation. Avant :4pièces/9lignes D=C118000,
banque94750 et bilan96750 ; après :6pièces/13lignes D=C124000,
banque100000, bilan102000 et résultat−10000. Les ajouts documentaires créent0écriture.
Le cas principal est relevé pour ne pas supposer un cumul mensuel absent du
petit scénario initial649 ; aucune qualification fiscale réelle n'est déduite.
[Mode d'emploi647](../RAS_DOCUMENTS_647.md), [preuve647](../../Test/rapport_ras_documents647.md),
[correction et nouveaux tests653](../../Test/rapport_coherence_scenario653.md).
Documents complémentaires uniquement, sans preuve fiscale, versement ou
crédit présumé. Garder les autres cahiers : ce complément ne les remplace pas.



Pour le dernier développement, ouvrir le [Word des sociétés liées](ANNEXE_RECETTE_SOCIETES_LIEES_20261019.docx),
son [PDF](ANNEXE_RECETTE_SOCIETES_LIEES_20261019.pdf) et son
[Excel de suivi](ANNEXE_RECETTE_SOCIETES_LIEES_20261019.xlsx).
20cas humains Non testé : deux sociétés fictives, capitaux10000 chacune,
vente/achat500HT+100TVA, règlements600 et lettrages séparés. Banques finales
A10600/B9400 ; résultats avant impôt+500/−500 ; bilans10600/9500. Dans chaque
Journal : trois pièces/sept lignes, débit=crédit11200. Les calculs attendus
sont indépendants. [Données](donnees_recette_societes_liees_20261019.json),
[mode d’emploi](../FACTURES_CORRESPONDANTES_635.md),
[preuve639](../../Test/rapport_annexe_societes639.md).
Ne pas mélanger ces sociétés avec celles des reprises de provisions.

Dans Paramètres → Sociétés liées, **Factures de la liaison** regroupe désormais
les deux dossiers avec les états documentaires, TTC, restes, paiements encaissés
et règlements en cours. Actualisation sansF5 ; un solde couvert ne prouve pas
un encaissement. Le [rapport641](../../Test/rapport_suivi_correspondances641.md)
décrit les contrôles et la restauration. Choisir l'exercice acheteur indiqué
par le suivi avant de chercher sa facture après changement de société.

Pour le complément précédent, ouvrir le [Word des reprises de provisions](ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.docx)
ou son [PDF de25pages](ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.pdf), puis
ouvrir le [classeur de suivi](ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.xlsx).
Il comporte20cas détaillés, les données à saisir, les écritures attendues,
les contrôles et les colonnes résultat réel/anomalies/preuves. La synthèse
Excel se recalcule à l’ouverture ; cette ouverture interactive reste à effectuer.

Parcours principal : société de recette vierge, capital20000, dotation1000,
reprises400+200, annulation de400 par inverse. Résultat comptable avant impôt
−800, provision800, disponible800 ;5pièces/10lignes, débit=crédit22000MAD,
actif=passif20000MAD. Les calculs attendus sont indépendants du code métier.
Le scénario laisse2025ouvert et n’ajoute aucun impôt ou TVA.

## Choisir le périmètre

| Document | Usage et base à préparer | Résultats humains |
|---|---|---|
|[Sociétés liées Word](ANNEXE_RECETTE_SOCIETES_LIEES_20261019.docx) / [PDF](ANNEXE_RECETTE_SOCIETES_LIEES_20261019.pdf) / [Excel](ANNEXE_RECETTE_SOCIETES_LIEES_20261019.xlsx)|Lots633/635 ; deux sociétés principales et variantes isolées ; [données](donnees_recette_societes_liees_20261019.json)|20cas Non testé ; deux limites non exécutables séparées|
|[Cahier général PDF](CAHIER_RECETTE_HISABPRO.pdf) / [Excel](CAHIER_RECETTE_HISABPRO.xlsx)|Socle du7octobre,218cas du parcours complet ; consulter aussi les compléments récents ci-dessous|À renseigner ; limites conditionnelles conservées|
|[Annexe reprises Word](ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.docx) / [PDF](ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.pdf) / [Excel](ANNEXE_RECETTE_REPRISES_PROVISIONS_20261019.xlsx)|Lots615/617, trois sociétés fictives dédiées et oracle2025 ; [données JSON](donnees_recette_reprises_20261019.json)|20cas Non testé ; deux limites non exécutables séparées|
|[Annexe RAS/CCA/PCA PDF](ANNEXE_RECETTE_RAS_TVA_CCA_PCA_20261019.pdf) / [Excel](ANNEXE_RECETTE_RAS_TVA_CCA_PCA_20261019.xlsx)|Lots593–607 ; six sociétés fictives, régimes/périodes indiqués ; [données JSON](donnees_recette_593_595_20261019.json)|30cas Non testé ; limites séparées|
|[Annexe inventaire PDF](ANNEXE_RECETTE_INVENTAIRE_20261010.pdf) / [Excel](ANNEXE_RECETTE_INVENTAIRE_20261010.xlsx)|Comptage de stock et régularisation dans une société distincte|16Non testé et3Bloqué, suivant les prérequis documentés|
|[Annexe commerciale PDF](ANNEXE_RECETTE_COMMERCIALE.pdf) / [Excel](ANNEXE_RECETTE_COMMERCIALE.xlsx)|Parcours commercial et contrôles associés, avec le jeu du document|À renseigner|
|[Bilan détaillé PDF](ANNEXE_RECETTE_BILAN_DETAILLE.pdf) / [Excel](ANNEXE_RECETTE_BILAN_DETAILLE.xlsx)|Présentation des rubriques du bilan et contrôles des immobilisations|À renseigner|

Les cas des différentes annexes se recouvrent parfois : ne pas additionner
leurs nombres pour annoncer une couverture unique. Utiliser les sociétés et
montants propres à chaque document, sans mélanger les jeux dans un dossier.
Les documents RH/paie sont conservés dans le dépôt, hors priorité actuelle.

## Utiliser les reprises dans l’application

Le [mode d’emploi615/617/625](../REPRISES_PROVISIONS_615.md) détaille les
commandes de **Clôture → Reprises partielles de provisions** : sélectionner
une dotation validée, vérifier l’aperçu et les justificatifs, créer un brouillon,
valider au Journal, puis annuler au besoin par un inverse traçable.

Le suivi et ses PDF/Excel affichent les originaux, inverses, montants réservés,
références déclarées, identité et logo de la société. Les colonnesN/O de l’Excel
indiquent l’exercice de reprise et celui de l’inverse. Exemple décalé : une
reprise du01/07/2025 peut relever de2026 et son inverse du01/07/2026 de2027,
selon les calendriers préparés. Le [parcours625](../../Test/rapport_reprises_decalees625.md)
documente les deux clôtures et la confirmation de déficit du laboratoire.

Le disponible porte sur le registre lié. Les mouvements manuels sans lien
fiable restent à analyser. Une annulation future ne finance pas une reprise
antérieure ; un inverse en brouillon ne libère pas la réservation. La référence
justificative n’est pas rendue obligatoire pour la validation générale ; le
contrôle FEC conserve ses propres anomalies documentaires.

## Préparer l’environnement avec le technicien

1. Conserver les fichiers et données existants. Les livraisons sont des ZIPs
   différentiels avec arborescence du dépôt ; utiliser le cumul le plus récent
   pour cette session, sur le dépôt courant.
2. Faire préparer une base vierge **isolée** pour les cas du cahier. La
   migration additive100 est livrée séparément et reste à déployer par
   l’administrateur sur une installation utilisateur. Elle n’est pas exécutée
   automatiquement au démarrage. Sans100, seul le panneau affiche une
   indisponibilité explicite.
3. Le [banc d’installation100](../../Test/recette_installation_vierge_100.py)
   crée exclusivement son propre cluster jetable et refuse toute URL externe.
   Il ne migre pas la base active. Le [rapport réel](../../Test/rapport_installation_vierge_100.md)
   décrit91SQL distincts,27rejeux,77tables et les contrôles de droits.
4. Suivre les [procédures d’exploitation](../EXPLOITATION_HISABPRO.md) pour les
   sauvegardes/restaurations et la préparation d’un déploiement. La qualification
   de laboratoire ne remplace pas l’installation cible et sa vérification.

Ne pas réappliquer un ancien ZIP après un cumul plus récent. Aucune ancienne
migration de réparation historique ne doit être lancée par simple analogie avec
les tests. Aucun PostgreSQL utilisateur n’a été utilisé dans ces lots.

## Ce qui est prouvé et ce qui reste à décider

| Décision | État |
|---|---|
|Développement des reprises liées615/617/625|Livré : aperçu, réservations datées, idempotence, annulation, protections et exports|
|Tests automatisés du périmètre|Exécutés sur PostgreSQL natif jetable et Edge ; résultats ci-dessous|
|Recette utilisateur|À effectuer ; tous les nouveaux cas restent Non testé|
|Prêt pour mise en production|Non validé : installation cible, données/justificatifs et qualification réglementaire à traiter|
|Développement global HisabPro|Partiel ; voir la matrice et le plan hors RH|

Preuves utiles : [reprises615](../../Test/rapport_reprises615.md),
[exports617](../../Test/rapport_exports_reprises617.md),
[oracle et cahier619](../../Test/rapport_annexe_reprises619.md),
[35cas intermodules sous100](../../Test/rapport_intermodules621.md),
[calendriers/restauration625](../../Test/rapport_reprises_decalees625.md).
Les nombres de suites ne s’additionnent pas comme des cas uniques.

La [matrice actuelle](../audit/MATRICE_COUVERTURE_HISABPRO.md), le
[plan hors RH](../audit/PLAN_FINALISATION_HORS_RH_20261018.md) et le
[registre des limites](../audit/REGISTRE_ANOMALIES_HISABPRO.md) gardent les
travaux restants : déclaration/imputation/reversement RAS, annexes151 et taxe
professionnelle, référentiels/EDI officiels, comptabilité de groupe et préparation
de production. Le pont documentaire633/635 est désormais livré : liaisons,
achat correspondant et écritures par les commandes ordinaires. Les règlements,
avoirs et livraisons restent propres à chaque société ; pas de consolidation
fiscale. Les historiques FEC/ETIC nécessitant des pièces restent visibles.
La déductibilité fiscale n’est pas déduite d’un montant de provision et HisabPro
n’est pas présenté comme officiellement certifié.

Installation actuelle : [CLI102](../../Test/recette_installation_vierge_102.py)
et [rapport réel](../../Test/rapport_installation_vierge_102.md),93SQL distincts,
29rejeux,80tables. Le programme crée exclusivement son propre cluster jetable,
refuse toute URL externe et ne migre pas la base active. Les migrations101/102
restent à déployer explicitement par l’administrateur sur l’installation cible.


Bilan actuel : [session633–643](../audit/RAPPORT_SESSION_20261019_633_643.md).
Le [correctif642](../../Test/rapport_reglements_centimes642.md) refuse les vrais
sous-centimes à la création/modification des règlements, sans corriger
silencieusement un historique. Les20cas de recette humaine restent Non testé.


Le [bilan645-657](../audit/RAPPORT_SESSION_20261019_645_657.md) rassemble les tests et livraisons courants. Pour RDO-008, suivre le [nouveau formulaire date/motif](../ANNULATION_REGLEMENT_655.md). Aucun cas humain pre-valide.


Complement659 : la [date et le motif](../ANNULATION_REGLEMENT_655.md) sont egalement disponibles pour toute une ventilation. [Tests67cas](../../Test/rapport_annulation_ventilation659.md).


[Bilan courant645-661](../audit/RAPPORT_SESSION_20261019_645_661.md) : annulations datees individuelles/collectives,255cas consolides reussis,aucune recette humaine pre-validee.


Complément663 : une panne de lecture des règlements est signalée, avec [Réessayer et Actualiser](../ANNULATION_REGLEMENT_655.md), sans faux vide. [Preuve663](../../Test/rapport_reglements_lecture663.md).


Complément665 : [consultation seule des règlements](../../Test/rapport_reglements_consultation665.md), sans commandes financières ; Actualiser et RAS restent consultables.


Complément667 : [lecture des réceptions fournisseurs](../../Test/rapport_receptions_lecture667.md) avec reprise et protection des réponses tardives. Aucun changement aux mouvements de stock.


Complément669 : [préparer une réception depuis une commande](../../Test/rapport_entree_reception669.md), navigation sans création cachée et bascule Vente/Achat lisible sur mobile.
