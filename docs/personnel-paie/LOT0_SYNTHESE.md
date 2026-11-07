# HISABPRO — PERSONNEL & PAIE

## Lot 0 — audit et proposition d'architecture

27 octobre 2026. Référence : cahier des charges master version 1.0. Ce dossier prépare les lots suivants ; aucun nouveau moteur, formulaire, barème, bulletin définitif ou paiement n'est livré.

## Navigation prévue

Un groupe « Personnel & Paie » dans la sidebar donnera accès aux neuf rubriques : Personnel ; Éléments de paie ; Traitement de la paie ; Charges sociales ; Fiscalité salariale ; Avances & prêts ; Paiements ; Comptabilisation ; États & reporting. Les rubriques seront visibles dans le groupe déplié, avec un état « À venir » sans faux lien tant qu'elles ne sont pas livrées. Clôture et régularisations restent rattachées aux deux dernières rubriques concernées.

Le style et la navigation mobile/clavier actuels sont à conserver. Le code de module `paie_grh` et l'URL historique `/cnss` restent à prendre en compte lors du basculement. La sidebar n'a pas été modifiée dans Lot 0.

## Ce qui existe réellement

Dossiers salariés avec archivage logique, simulation mensuelle indicative, absences avec décisions et historique, registre d'affectation des avances 3431, preuves de référentiel et exports limités. Le journal `SA`, les exercices/verrouillages, le grand livre, la banque et le rapprochement existent déjà et doivent être réutilisés.

Le futur traitement complet des paies exige encore les rubriques et règles versionnées, campagnes approuvées, bulletins figés, dettes, paiements et déclarations, écritures liées de façon unique, états et travaux de clôture Personnel. L'inventaire contient 19 tables ORM utiles, 14 routes Personnel et 49 sources avec empreintes ; il distingue le code présent du schéma réellement installé chez l'utilisateur.

## Écarts confirmés sur données fictives isolées

Deux salariés peuvent actuellement partager le même matricule dans une société. Une création devient active sans circuit d'approbation. Le salaire est modifié directement, sans version à date d'effet. Un compte en lecture peut récupérer le salaire et le numéro CNSS sans masquage depuis l'API existante. Ces écarts au nouveau master devront être traités avant activation du nouveau module.

Autre dépendance confirmée : l'API de règlement commerciale refuse un règlement sans facture. Elle ne peut pas être réutilisée telle quelle pour un salaire ; aucune fausse facture ni faux tiers client ne doit être créé pour contourner cette limite.

## Architecture proposée

Conserver les identifiants de `employes`, ajouter des extensions et versions de contrats/rémunérations, puis des demandes d'approbation et événements traçables. Les montants nouveaux seront décimaux exacts ; les dates ou valeurs historiques non attestées resteront explicitement non qualifiées. Les futures campagnes et bulletins figeront leurs sources et règles.

Les fonctions Personnel/Paie s'appuieront sur l'authentification et les sociétés existantes, avec des capacités explicites et projections API. Les écritures et leur validation resteront dans la comptabilité commune. Les paiements salariaux nécessiteront un adaptateur de trésorerie hors facture et des liens réconciliables avec la banque, sans doubler les services existants.

## Choix à examiner avant les lots concernés

1. Habilitations : pilote proposé pour des utilisateurs déjà légitimement admin/comptable avec capacités Personnel explicites. Un profil « Personnel seul » devra être réellement confiné hors des autres modules avant usage ; lui donner un rôle comptable général est exclu.
2. Approbations : deuxième acteur pour les opérations sensibles, y compris pour un admin et sa propre paie. Le cas d'une entreprise à utilisateur unique nécessite une décision explicite.
3. Journal : conserver `SA` est proposé. `PAI` n'existe pas dans le contrat actuel et requerrait une évolution dédiée.
4. Comptabilisation : proposition d'OD centralisée et détail salarial confidentiel réconciliable ; granularité à examiner avant Lot 4.
5. Données sensibles : gestion des clés, chiffrement, rotation et conservation à arrêter avant stockage de coordonnées bancaires de salariés.
6. Règles et formats : textes officiels consolidés, cas de référence, arrondis, conventions et formats déclaratifs/bancaires à vérifier avant leurs calculs et exports. Aucun taux ou compte n'est nouvellement affirmé comme obligatoire ici.

## Tests réellement exécutés

Cinq campagnes totalisent 241 cas réussis, zéro échec, erreur ou cas ignoré : 105 tests unitaires/validation de schéma ; 127 cas API, SQL et démarrage sur PostgreSQL natif éphémère ; 9 parcours Edge avec API/PostgreSQL réellement connectés. Les durées et résultats détaillés sont dans LOT0_TESTS_ET_REPRISE.md et ses JUnit joints.

Les cas couvrent notamment dossiers, simulation, paramètres non finis, droits/sociétés, absences, preuves de référentiel, registre d'avances, concurrence et reprise de l'ancien schéma qui provoquait InvalidForeignKey. Les trois nouveaux tests de caractérisation constatent des écarts actuels ; leur réussite ne valide pas le nouveau master.

Build Vite réussi en 11,51 secondes, avec les avertissements existants de bundle et d'import xlsx. Les deux nouveaux scripts Python sont compilés et l'inventaire est régénéré à l'identique. Les 463 empreintes du candidat comptabilité/facturation restent identiques. Aucun PostgreSQL utilisateur, donnée réelle, fichier backend produit ou migration n'a été modifié.

## Livrables et prochaine sous-étape

Le dossier contient l'audit, l'inventaire reproductible, la conception avec schéma de flux, la matrice RBAC, le plan de migrations/recette et le plan exécutable Lot 1A. Les preuves JUnit et caractérisations sont jointes au ZIP différentiel.

Prochaine étape : examiner l'architecture et le choix d'habilitations, puis lancer Lot 1A, fondations backend Personnel et historique. Les écrans/sidebar seront traités en Lot 1B avec des rubriques réellement livrées. La recette utilisateur, la validation des règles de paie et l'état du futur environnement de production restent à effectuer.

Le Lot 0 est un travail d'audit et de conception ; il ne constitue pas une certification, une recette utilisateur validée ni une autorisation de mise en production.
