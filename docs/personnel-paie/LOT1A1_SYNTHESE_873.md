# HISABPRO — PERSONNEL & PAIE

## Lot 1A.1 — droits d'accès et consultation protégée

Livraison du 27 octobre 2026. Première sous-étape backend du Lot 1A, après l'audit du Lot 0. Le dossier salarié versionné et le circuit d'approbation restent les prochaines sous-étapes.

## Ce qui est ajouté

Un administrateur peut attribuer et révoquer, pour sa société, des droits explicites de lecture de l'identité, des rémunérations, des identifiants sensibles et des preuves de référentiel. Les délégations sont datées, motivées et conservées dans l'historique. Les rôles globaux existants ne changent pas : aucun droit comptable général n'est ajouté.

Après activation volontaire de la protection, les anciens accès au Personnel vérifient ces droits côté serveur. Le salaire, les informations familiales et le numéro CNSS sont masqués selon l'habilitation. Les simulations, registres et PDF sont également contrôlés. L'administrateur n'obtient pas une lecture financière implicite.

L'interface affiche « Masqué » et propose seulement la consultation dans ce mode. Lors d'un rafraîchissement après révocation, les détails déjà ouverts sont vidés. L'API applique les nouvelles autorisations sans attendre une reconnexion.

## Installation et activation sont distinctes

La nouvelle migration 105 ajoute les structures et protections, sans modifier les dossiers salariés ni la comptabilité et sans attribuer de droits par défaut. Son installation seule conserve le fonctionnement historique. Les anciennes limites d'accès restent donc présentes tant qu'une société n'a pas explicitement activé la protection.

L'activation place actuellement le Personnel de cette société en consultation protégée : les anciennes créations, modifications, archives et opérations de registres sont bloquées. Le nouveau circuit contrôlé remplacera ces mutations dans les sous-étapes suivantes. Ce basculement doit être préparé et essayé sur une copie avant tout usage cible.

La migration n'est pas exécutée automatiquement au démarrage. Aucune installation ni activation n'a été faite sur la base de l'utilisateur. Le guide joint décrit les prérequis, les API d'administration, l'attribution des droits et les contrôles à effectuer.

## Traçabilité et isolation

Les sociétés conservent des habilitations indépendantes. Une invitation supprimée puis recréée ne récupère pas les anciennes délégations. Un compte référencé dans l'historique Personnel est conservé et peut être désactivé ; une suppression physique est refusée proprement.

Les contrôles sont revalidés en base et les opérations d'administration sont sérialisées. Deux demandes concurrentes ne créent pas une double délégation. L'activation attend une opération historique déjà engagée. Les protections SQL empêchent la suppression des traces et les réponses personnelles ne sont pas mises en cache HTTP.

## Tests réellement exécutés

187 cas distincts sont qualifiés après résolution des échecs : 81 tests unitaires ou contrôles de sources, 95 cas API/SQL/démarrage sur PostgreSQL natif isolé et 11 parcours Edge avec API/PostgreSQL réellement connectés. Les JUnit conservent aussi les essais initiaux échoués et les corrections correspondantes.

La validation comprend la migration rejouée avec des habilitations et une activation déjà enregistrées, les droits SQL du compte applicatif non propriétaire, le masquage et la révocation, les accès invités, les anciennes routes et les parcours historiques sans activation. Les détails locaux conservés après révocation ont été reproduits puis corrigés sur ordinateur et mobile.

Build Vite réussi en 10,07 secondes ; dix fichiers Python ajoutés ou modifiés sont compilés. Les avertissements existants de bundle et d'import xlsx restent signalés. Les contrôles de clôture restent inchangés : seule la classification de leur aperçu en lecture a été corrigée dans le scanner de tests, puis vérifiée sur PostgreSQL.

## Limites et suite

Ce lot ne livre pas encore le versionnement des salaires et contrats, les approbations de dossiers, un profil « Personnel seul », les bulletins définitifs, les paiements ou les déclarations. Les neuf rubriques de sidebar restent prévues avec les écrans du Lot 1B.

Les données réelles n'ont pas été modifiées. L'installation sur une copie de l'environnement cible, les délégations et la politique de basculement restent à valider. Il n'existe pas de retour silencieux aux anciens droits après activation ; une rétrogradation vers un ancien code ignorant ces contrôles est à exclure.

Prochaine étape : Lot 1A.2, structures et historique des dossiers, contrats et rémunérations exactes à date d'effet ; puis Lot 1A.3 pour les propositions et approbations. Aucun taux ni calcul légal nouveau n'a été introduit dans cette livraison.
