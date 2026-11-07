# Reprise RAS — 9 et 10 octobre 2026

Le dépôt est la source de vérité. Le journal conserve l'interruption du quota
de la session du 9 octobre et la reprise du10octobre à00:58UTC, interrompue
par quota avant sa limite prévue02:58UTC. Une nouvelle exécution commence
à08:14UTC, avec limite10:14UTC, puis est interrompue par quota. La reprise
actuelle commence à09:36UTC, avec limite11:36UTC. Elle finalise le paquet
en cours avant toute nouvelle fonctionnalité.
Les services utilisateur ont été préservés. Aucun test ni script de migration
n'a été lancé contre le PostgreSQL réel et aucune donnée comptable réelle
n'a été modifiée.

## Changements déjà livrés et vérifiés

- **291/292** : une RAS estimée sur la facture ne constitue pas un paiement.
  Facture de laboratoire de 1 200 MAD, estimation 100 ; un paiement de
  1 100 laisse 100 à régler, sans OD automatique de retenue. Les historiques
  effectivement marqués comme comptabilisés sont conservés et distingués.
- **295/296/297** : les soldes historiques indéterminables restent visibles
  dans le recouvrement, le dashboard et la balance âgée. Les totaux concernés
  indiquent « À vérifier » ; les exports CSV, Excel et PDF conservent le
  diagnostic sans remplacer un montant inconnu par zéro.
- **304** : quatre parcours Edge vente/achat, bureau/mobile, ont réellement
  enregistré les deux paiements 1 100 puis 100, validé leurs écritures puis
  lettré les trois lignes du tiers. Oracle : trois écritures, sept lignes,
  débit = crédit = 2 400 MAD, collectif soldé, banque +1 200/−1 200.
- **294** : les sources officielles obtenues et les accès incomplets sont
  documentés. Aucun taux, prorata universel ou régime IR/IS/TVA nouveau n'a
  été déduit d'une lecture partielle.
- **298** : deux cas utilisateur de l'annexe RAS estimation sont fournis en
  PDF et Excel avec calculs indépendants et suivi vierge. Ils restent
  **Non testé** ; les preuves automatisées sont distinctes de la recette humaine.

## Capture explicite et activation

Les lots293/303 ajoutent un flux déclaratif de retenue effectivement opérée
sur un règlement immédiat comptabilisé, par virement ou espèces. Montant,
date, référence de pièce et compte destination doivent être choisis
explicitement. L'OD est un brouillon à contrôler et à valider ; cette saisie
ne vaut ni attestation authentifiée ni crédit IS automatiquement qualifié.

La migration083 est additive et **manuelle**, hors `Base.metadata` et hors
bootstrap. Une installation sans083 conserve les fonctionnalités précédentes
et affiche l'indisponibilité de la capture. La copie du ZIP et le démarrage
ne doivent pas activer ces nouvelles tables.

Les cinq Edge finaux303 passent : vente/achat, bureau/mobile, puis un cas sans
migration ni POST/DDL. Validation, cinq lignes lettrées puis délettrées et
annulation sont exécutées réellement. Les contrôles backend293 et la
sauvegarde/restauration305 passent sur des PostgreSQL nonce. Une vraie connexion
LOGIN insère une trace cohérente ; les ACL historiques et les nouveaux triggers
sont vérifiés et distingués. La présence d'un fichier de test n'est jamais une
preuve de réussite.

L'annexe306 fournit deux parcours utilisateur avec capture, validation et
annulation : PDF neuf pages et Excel trois onglets, deux cas **Non testé**.
Le parcours automatisé307 couvre un chèque client remis puis rejeté, le virement
de remplacement, la validation et le lettrage sur ordinateur et mobile. Oracle :
cinq écritures, onze lignes, débit = crédit = 6 000 MAD ; banque 1 200,
comptes d'attente et collectif soldés. Aucun frais ou escompte n'est présumé.

## Documents et preuves

- [Guide de mise à jour et activation isolée](MISE_A_JOUR_RAS_20261009.md).
- [Rapport backend capture293](../Test/rapport_ras_capture_reglement.md).
- [Rapport navigateur capture303](../Test/rapport_e2e_ras_capture_isole.md).
- [Preuve navigateur paiements sans capture304](../Test/rapport_e2e_ras_solde_lettrage.md).
- [Sources officielles RAS et limites294](../Test/rapport_sources_ras_20261009.md).
- [Annexe estimation PDF298](recette/ANNEXE_RECETTE_RAS_ESTIMATION_20261009.pdf).
- [Suivi Excel estimation298](recette/ANNEXE_RECETTE_RAS_ESTIMATION_20261009.xlsx).
- [Annexe capture PDF306](recette/ANNEXE_RECETTE_RAS_CAPTURE_20261010.pdf).
- [Suivi Excel capture306](recette/ANNEXE_RECETTE_RAS_CAPTURE_20261010.xlsx).
- [Sauvegarde/restauration isolée305](../Test/rapport_sauvegarde_ras_reglements_isole.md).
- [Chèque impayé, règlement et lettrage307](../Test/rapport_e2e_cheque_impaye_isole.md).
- [Annulation historique sûre308](../Test/rapport_ras_historique_annulation.md).
- [Avoirs, société et verrou PostgreSQL309](../Test/rapport_avoirs_ras_societe.md).
- [Articles historiques et documents310](../Test/rapport_articles_historique_nombres_lecture.md).
- [Consolidation finale311](../Test/rapport_non_regression_globale_20261010_finale.md).
- [Correction de mesure et retests312](../Test/rapport_e2e_articles_diagnostic_stock_mesure.md).
- [Nouvelle non-régression globale300](../Test/rapport_non_regression_globale_20261010_RAS.md).
- [Matrice de couverture](audit/MATRICE_COUVERTURE_HISABPRO.md).
- [Registre des anomalies](audit/REGISTRE_ANOMALIES_HISABPRO.md).
- [Journal actif](../CODEX_PROGRESS.md).

## Limites et prochaine étape

La globale286, 2 582 réussites, porte sur la version précédente ; elle ne
prévalide pas les changements RAS de cette reprise. La nouvelle consolidation
doit compter les cas réellement exécutés sur des sources figées et conserver
tout échec. Les suites ciblées qui se recouvrent ne sont pas additionnées.

La globale300 a terminé pendant l'interruption de quota :2627réussis,
12échecs, 0erreur, 0ignoré,32avertissements ; code1 en2386,05secondes.
Les645empreintes restent identiques. Les traces récupérées à08:14UTC montrent
un identifiant de société non défini dans le calcul du crédit d'avoir ; les
préparations de clôture échouent avant la clôture elle-même. Cette exécution
reste une preuve d'échec. La correction309 et ses retests sont distincts,
sans transformer rétrospectivement ce résultat en succès.

Le lot309 reproduit l'erreur de société, puis corrige également le verrou de
l'utilisation d'un avoir : PostgreSQL doit verrouiller la table des avoirs,
sans verrouiller le côté nullable de sa jointure de lignes. Trente-trois tests
API/connexes passent après les deux corrections. Les huit Edge récupérés
passent après la première correction, avant la seconde ; la prochaine globale
doit couvrir l'ensemble de la version finale. Refus404 inter-société,
remboursement fictif100 sur crédit500 et disponible400 sont exercés.

La reprise à09:36UTC finalise310 après une nouvelle interruption de quota :
les valeurs historiques d'article inconnues sont visibles sans remplacement
par0/20 ; une description seule ne réécrit aucun prix/frais/seuil/TVA.
Les documents requièrent les valeurs explicites et restent des brouillons
sans écriture ni mouvement dans cette recette. Principal3tests dont2Edge,
5connexes et build139modules passent. Le résultat final d'une ancienne session
inaccessible n'est pas utilisé comme preuve. La nouvelle globale311 termine
sur649sources figées : **2 734 réussis, 4 échecs, 0 erreur, 0 ignoré,
32 avertissements ; code1 en3 150,16s**. Les empreintes restent identiques.
Deux échecs sont causés par le compteur de test qui assimilait le diagnostic
POST du stock à une mutation. Le lot312 distingue cette lecture exacte,
force son actualisation réelle et conserve les contrôles des refus et des
documents inchangés. Deux délais navigateur navigation/login ont une cause
non établie et restent visibles. Les relances sont documentées séparément ;
aucune réussite globale n'est déclarée par addition de ces commandes.
La relance finale des trois modules312 donne13réussites140,11s, code0,
25avertissements, dont les quatre cas échoués311. Le contrôle de relecture
utilise l'exercice du document ; les montants du devis et de la commande
restent100HT/20TVA/120TTC après le refus d'édition. Les deux délais restent
sous surveillance, malgré leurs reprises réussies.

L'étape suivante, après cette livraison, est la qualification des nombres
historiques dans l'inventaire et ses contrôles de clôture. Les routes d'inventaire
ne passent pas par ArticleOut ; leurs coûts inconnus ne sont pas prévalidés
par310. Aucun changement inventaire n'est inclus dans cette reprise.

Restent notamment la qualification réglementaire complète des RAS, les
attestations et déclarations, les références sociales complètes pour la paie,
le référentiel DGI et le schéma XML/EDI applicable, ainsi que les justificatifs
historiques FEC/ETIC. Les informations absentes ne sont pas inventées.

**Développement global : partiel. Tests automatisés : uniquement les périmètres
réellement exécutés. Recette utilisateur : à effectuer. Mise en production :
non validée.** Le bilan détaillé, la numérotation interne T1…T25 et les autres
lots déjà livrés ne sont pas réappliqués.
