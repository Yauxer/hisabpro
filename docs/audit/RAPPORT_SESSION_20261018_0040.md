# HisabPro — session du 18 octobre 2026

Reprise depuis le dépôt à00:40UTC, après lecture du journal, vérification des
processus et récupération des résultats de536. Aucune étape livrée n'a été
réappliquée. Le dépôt local ne comporte pas de métadonnées Git ; les versions
sont suivies par empreintes et archives différentielles.

## Avancées utilisables

- Les proformas sont maintenant reconnues dans la liste : leur modification,
  PDF et conversion utilisent le statut réellement stocké.
- Deux demandes simultanées de comptabilisation d'une facture ne créent qu'une
  écriture. Deux validations/conversions sont aussi sérialisées : même numéro,
  un mouvement de stock, protection de la facture définitive conservée.
- La suppression d'un brouillon de facture retrouve sa vraie origine et
  conserve une RAS déjà comptabilisée par une OD distincte.
- Les comptes en consultation seule gardent les détails et téléchargements
  de Factures, Avoirs et Acomptes, sans formulaires de mutation proposés.
- Paie / GRH dispose d'un registre PDF des congés et absences : société/logo,
  filtre, périodes, jours calendaires, motifs, décisions et historique.
- La reprise du registre après sauvegarde/restauration native a été vérifiée.

## Vérification rapide sur l'installation

1. Redémarrer l'API et reconstruire le frontend après copie des fichiers.
2. Ouvrir Paie / GRH → Congés & absences, choisir un statut et utiliser
   Exporter le registre PDF. Vérifier identité, logo, périodes et décisions.
3. Avec un compte Consultation seule, consulter les documents commerciaux et
   télécharger leurs pièces. Les commandes d'écriture doivent être absentes
   ou désactivées. Ces vérifications restent à effectuer par l'utilisateur.

Un [exemple entièrement fictif du registre](exemples/REGISTRE_GRH_FICTIF_20261018.pdf)
est joint ; son aperçu d'une page a été inspecté localement.

## Tests et ZIPs par étape

Les suites se recouvrent. Les résultats sont présentés par périmètre et par
version testée ; ils ne représentent pas un nombre de fonctionnalités.

| Étape | Périmètre | Tests exécutés | ZIP différentiel |
|---|---|---|---|
|536|Sources des factures, références fournisseurs et RAS distincte|171connexes confirmés à la reprise ;17ciblés précédemment consignés|[536](../../HisabPro_536_Journal_Factures_References_RAS.zip)|
|538|Double comptabilisation de facture|4ciblés,344consolidation et247externes|[538](../../HisabPro_538_Factures_Comptabilisation_Concurrente.zip)|
|541|Statut proforma dans les sorties API|2API et18connexes|[541](../../HisabPro_541_Factures_Statut_Proforma.zip)|
|540|Factures en consultation seule|6Edge,352consolidation et247externes ;build9.03s|[540](../../HisabPro_540_Factures_Consultation_Seule.zip)|
|543|Validation et conversion simultanées, stock unique|4ciblés,356consolidation et247externes|[543](../../HisabPro_543_Factures_Validation_Conversion_Concurrentes.zip)|
|545|Avoirs/Acomptes en consultation seule|6Edge et28connexes ;build7.10s|[545](../../HisabPro_545_Avoirs_Acomptes_Consultation_Seule.zip)|
|547|Registre PDF GRH, logo, filtre et rôles|5ciblés et208connexes ;build5.10s|[547](../../HisabPro_547_GRH_Registre_Absences_PDF_Logo.zip)|
|549|Restauration native du registre GRH|1scénario froid098,61.21s,74tables|[549](../../HisabPro_549_Restauration_Registre_GRH.zip)|

Toutes les commandes finales listées ont terminé avec code0. Les échecs avant
correction et ajustements d'oracle sont conservés dans les rapports de chaque
lot et le journal. Les avertissements Pydantic/import et bundles restent
documentés. Les scripts de tests créent leurs propres cibles nonce ; aucun
PostgreSQL réel ni donnée comptable de l'utilisateur n'a été utilisé.

Un délai de revue automatique a interrompu une application de patch545 sans
modifier les fichiers. L'inspection puis l'unique nouvelle tentative ont
permis de poursuivre et de tester le lot normalement.

## État de livraison

| Domaine de validation | État |
|---|---|
|Développement global|Partiel ; matrice70lignes :15terminé,47partiel,4absent,4bloqué|
|Tests automatisés|Réussis dans les périmètres et versions ci-dessus|
|Recette utilisateur|À effectuer ; le point6 reste réservé au retour humain|
|Mise en production|Non validée|

Les98migrations et115guides existants,main.py,models.py etAGENTS.md sont
inchangés. Aucun commit ou push. Le registre GRH n'ajoute ni droit à congé
acquis, ni retenue de salaire, ni taux social, ni déclaration officielle.
La paie complète et les limites fiscales restent explicites dans la matrice.

## Prochaine reprise

Exporter le même registre GRH en Excel avec logo, filtre et historique, en
préservant les textes saisis et les rôles. Commencer par le journal actif,
les processus et les fichiers réellement présents. Les lots530–551 sont livrés.

Le cumulatif différentiel de cette reprise inclut les lots530–551 après529,
leurs rapports, le journal et cet index. Il contient uniquement les fichiers
modifiés/ajoutés, sans environnement, dump, cache ou projet complet.

## Derniers contrôles avant clôture

Deux tests de rendu pur supplémentaires vérifient le registre sans logo, avec
970sauts de ligne ou un texte échappé long :2réussites,1avertissement,0.68s.
Les marqueurs finaux et les occurrences du motif dans l'historique restent
intacts, sans troncature. Aucun fichier produit modifié. [ZIP551](../../HisabPro_551_GRH_PDF_Limites.zip).
