# Activation des ventilations bancaires sur une copie de recette — lot392

Ce document concerne uniquement un environnement de test isolé. Le point6, préparation de mise en production et recette partenaire, reste en attente du retour utilisateur. Aucune migration n’a été exécutée sur le PostgreSQL réel.

## Fichiers et ordre

Appliquer le différentiel sur la copie de recette, puis faire appliquer `hisabpro-backend/084_rapprochement_ventilations.sql` par le rôle migrateur habituel. Préconditions :047,048 et083 déjà appliquées selon la procédure de cette installation. Ne pas rejouer les anciennes migrations pour activer cette fonction.084 crée une table d’affectations, ses contraintes et gardes ; elle étend le garde047 des liens simples sans changer ses autres contrôles. Models/main ne sont pas modifiés : `create_all` ne crée pas cette table et ne remplace pas la migration.

Avant DDL, le technicien vérifie l’hôte, le port, le nom de la base de recette et son isolation effective. Cette session a employé uniquement des clusters loopback à port aléatoire différent de5432, avec marqueur nonce et données fictives.

084 ne modifie aucun montant, relevé historique, règlement, écriture ou société. Aucun backfill des références libres. Le script est transactionnel et rejouable ; les affectations déjà créées sont conservées. Les permissions nouvelles restent limitées à la table d’affectations et aux lectures/mises à jour nécessaires au pointage. Aucun rôle n’est créé par la migration.

## Vérification de recette

Redémarrer le backend de recette et recharger le frontend de recette. La lecture authentifiée de `/api/rapprochement/5141/situation?date_debut=2026-01-01&date_fin=2026-12-31` expose `ventilations_activees:true`. Sans084, les anciens rapprochements simples continuent de fonctionner ; les propositions de ventilation restent absentes et la route dédiée refuse avec503. Ne pas contourner ce refus.

Créer deux facturesTTC120/240, un virement natif240 affecté120/120, valider les écritures et saisir une seule ligne bancaire240. Le choix Ventilation doit pointer deux lignes et persister après rechargement. Dérapprocher restitue les deux lignes disponibles sans effacer le relevé ni modifier les écritures.

## Preuves et limites

Les tests portent sur API authentifiée, Edge bureau/mobile, SQL réel nonce, rôleLOGIN non propriétaire, concurrence, refus inter-sociétés, périodes clôturées, lien simple, total exact et rejeu084. Voir le rapport392 et la variante annuelle393. Ces preuves ne valent ni recette utilisateur ni validation du PostgreSQL réel. Les chèques/effets groupés et les historiques sans lot natif restent distincts.
