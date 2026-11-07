# Personnel & Paie — Lot 1A.1 : socle des habilitations

Date : 27/10/2026. Suite du Lot 0 (871). **Sous-étape de sécurité livrée ; le Lot 1A complet et le moteur de paie ne sont pas terminés.** Aucun nouveau rôle global ni nouvelle rubrique de sidebar. Le code du journal `SA`, les modèles comptables et les taux restent inchangés.

## 1. Deux états de déploiement distincts

**Installer la migration 105 n'active pas la protection.** Sans activation explicite d'une société, les routes et droits historiques restent compatibles. Cela inclut les limites constatées au Lot 0 : les anciens salaires et numéros CNSS sont accessibles selon les anciens rôles. Les nouvelles habilitations ne doivent pas être présentées comme déjà protectrices dans cet état.

Une activation explicite par un administrateur de la société bascule son Personnel en mode **protégé**. Alors :

- Aucun droit de lecture Personnel n'est accordé implicitement, y compris à l'administrateur. Les habilitations nécessaires doivent être attribuées explicitement.
- Les anciens GET de dossiers, simulations, absences, preuves et avances vérifient les capacités. Les valeurs non autorisées ne quittent pas l'API.
- Les anciennes créations, éditions, archives, décisions d'absence, affectations d'avances et consignations de référentiel sont refusées avec 409. Ce mode est une consultation protégée ; le nouveau circuit de modifications/approbations sera ajouté aux sous-étapes suivantes.
- Les autres sociétés restent dans leur propre état. Les rôles globaux admin/comptable/lecture ne changent pas et aucun droit comptable général n'est ajouté.

Ce choix reprend le pilote de D01 : habilitations explicites des comptes existants, sans prétendre fournir un profil « Personnel seul » confiné hors des autres modules. Une personne ayant déjà le rôle comptable garde ses droits comptables existants ; les capacités ci-dessous ne remplacent pas ce rôle.

## 2. Capacités de lecture disponibles

| Capacité | Effet en mode protégé |
|---|---|
| `personnel.lire_identite` | Liste et fiche historiques de la société, avec les masques ci-dessous. |
| `personnel.lire_remuneration` | Salaire et paramètres familiaux/IR ; avec identité, accès à la simulation et au registre d'avances. |
| `personnel.lire_identifiants_sensibles` | Numéro CNSS ; avec identité, accès au registre d'absences et à son PDF, susceptibles de contenir des motifs personnels. |
| `personnel.audit_lire` | Consultation des preuves de référentiel ; aucune consignation historique en mode protégé. |

Sans lecture de rémunération, `salaire_brut`, `situation_familiale`, `nb_enfants` et `personnes_charge_ir` sont retournés à null. Sans lecture des identifiants sensibles, `numero_cnss` est null. L'interface distingue **Masqué** de **À compléter**. Les nouvelles capacités financières/de validation des lots suivants ne sont pas acceptées comme simples valeurs libres.

La gestion des habilitations reste réservée à un administrateur authentifié dont l'accès société est revalidé en base. Elle ne confère pas une auto-approbation de paie : aucune approbation de paie n'est disponible dans cette livraison.

## 3. API de gestion

Préfixe : `/api/employes/securite`, inclus dans le routeur existant ; aucune nouvelle inscription d'utilisateur ou identité parallèle.

| Méthode et chemin | Autorisation | Résultat |
|---|---|---|
| GET `/acces` | Compte authentifié | Mode de sa société, capacités de ce compte, installation et état des anciennes modifications. |
| GET `/habilitations` | Admin société | Habilitations courantes et révoquées de sa société, avec auteurs/dates/motifs. |
| POST `/habilitations` | Admin société | Accord explicite à un membre actif principal ou invité. Doublon actif refusé409 ; compte étranger404. |
| POST `/habilitations/{id}/revoquer` | Admin société | Révocation tracée ; seconde révocation409 ; objet étranger404. |
| POST `/activation` | Admin société | Activation explicite unique ; seconde activation409. |

Exemple de corps d'accord, sur une copie de test et après avoir vérifié l'identifiant du compte choisi (123 est fictif) :

```json
{"utilisateur_id":123,"capacite":"personnel.lire_identite","motif":"Accès de consultation validé"}
```

Exemple de corps de révocation :

```json
{"motif":"Retrait de la délégation"}
```

L'activation exige le corps explicite suivant ; elle ne doit pas être envoyée à une société utilisée en écriture avant d'avoir évalué le passage en consultation protégée :

```json
{"confirmation":"PROTEGER_PERSONNEL","motif":"Basculement contrôlé des accès Personnel"}
```

Les motifs sont bornés et non vides. Champs supplémentaires, booléens comme identifiants, capacités inconnues et confirmation incorrecte sont refusés. La société et l'auteur viennent de l'authentification, jamais d'un champ du corps.

## 4. Préparation sur une copie de l'environnement cible

1. Sauvegarder et vérifier les prérequis du projet, les migrations antérieures et le rôle applicatif. Préserver les scripts déjà exécutés, notamment080/081/082/095. Aucune de ces migrations n'est modifiée par la livraison.
2. Appliquer `105_personnel_habilitations.sql` avec le rôle migrateur/propriétaire. Elle ajoute deux tables de sécurité, leurs contraintes/index et fonctions de contrôle ; ne modifie aucune ligne de salarié, écriture, taux ou historique existant. Les droits sont provisionnés pour le rôle applicatif `hisabpro` ; toute autre configuration doit être examinée avant usage.
3. Déployer les fichiers backend et le frontend reconstruits. La migration n'est pas exécutée automatiquement au démarrage. Sans105, GET `/acces` annonce le mode historique ; les opérations d'administration demandent l'installation avec503.
4. Vérifier GET `/acces`, préparer les délégations utiles par compte et contrôler les capacités de lecture. L'administrateur qui souhaite consulter les données doit aussi recevoir ses capacités explicitement.
5. Activer seulement la société de test choisie, puis recharger ses écrans. Vérifier masques, refus des anciennes mutations, révocation et cloisonnement entre sociétés.
6. Conserver l'état de protection et l'historique. Il n'existe pas de retour HTTP implicite en mode historique ni de suppression des événements de délégation.

Aucune de ces opérations n'a été appliquée à la base utilisateur pendant le développement. L'installation et la politique de délégations de l'environnement cible restent à valider.

## 5. Intégrité et concurrence

Les attributions et révocations sont sérialisées par société, avec revalidation de l'administrateur après le verrou commun de gestion des utilisateurs. La protection utilise un verrou partagé sur les consultations/anciennes mutations et exclusif sur activation/délégation/révocation. Une ancienne opération commencée avant le basculement termine avant l'activation ; aucune mutation historique nouvelle ne passe après celle-ci.

Les habilitations ont une unicité active par société/utilisateur/capacité. Leur historique ne peut être supprimé ou tronqué ; seule une révocation tracée est autorisée. Les lignes d'activation sont immuables. Les tests incluent le rôle SQL applicatif LOGIN non propriétaire et le rôle propriétaire pour contrôler les protections.

Une habilitation invitée mémorise l'identité de son invitation. Supprimer puis recréer l'invitation ne réactive pas l'ancienne habilitation : il faut révoquer l'ancienne délégation puis en attribuer une nouvelle. Un compte référencé dans l'historique Personnel ne peut plus être supprimé physiquement par l'API :409 propose sa désactivation, qui conserve la trace.

Les réponses de dossiers et registres sont privées sans stockage HTTP (`Cache-Control: no-store`). L'API applique immédiatement la révocation sur les requêtes suivantes, avec le même JWT. L'écran vide ses détails locaux lors du rafraîchissement des droits, notamment via **Actualiser**. Il ne s'agit pas d'un effacement à distance d'informations déjà vues : les sessions ouvertes doivent être rafraîchies après un changement de politique.

Le code protégé ne doit pas être rétrogradé vers une version ancienne qui ignorerait ces contrôles après activation. En cas de retrait, fermer les accès concernés et conserver schéma/historique ; pas de rollback par suppression des tables ou retour silencieux aux anciens droits.

## 6. Tests, constats et limites

Les campagnes et JUnit sont joints à `Test/PREUVE_PERSONNEL_PAIE_873.json`. Sont exécutés sur bases fictives PostgreSQL natives isolées : masques et chemins historiques, rôles, sociétés/invitations, révocation, suppression contrôlée du compte, double délégation concurrente, activation sérialisée, intégrité SQL, installation sans105/partielle et rejeu105 avec historique peuplé et droits inchangés.

Deux parcours Edge1440/390 vérifient consultation masquée, absence de boutons d'écriture, délégation puis révocation sans reconnexion, purge du détail déjà ouvert et conservation des données/écritures. Les parcours historiques restent testés sans activation. Le build et la compilation sont exécutés. SQLite ne remplace pas les validations PostgreSQL.

Les échecs initiaux sont conservés : cycle de vie d'un clientHTTP de test, libelléCNSS incorrect dans le test, puis véritable détail local conservé après révocation et corrigé. Un scanner statique ancien classait le POST de lecture `/cloture/ajustements/apercu` comme mutation ; sa classification est corrigée avec contrôle d'authentification/absence d'appels mutateurs et tests PostgreSQL de l'aperçu sans création. Aucun fichier produit de clôture n'est modifié.

La migration105, le socle d'accès et les adaptations de compatibilité sont livrés. Ne sont pas livrés ici : unicité métier du matricule, rémunérations/contrats versionnés, approbation de dossiers, profil Personnel seul, stockage sécurisé du RIB, bulletins/calculs définitifs, paiements, déclarations et neuf nouveaux écrans.

## 7. Reprise — Lot 1A.2

Ajouter les extensions de dossiers, rémunérations/contrats exacts et datés, demandes et événements, puis les API contrôlées de1A.3. Préserver `employes.id` et les historiques sans inventer de date ou salaire attesté. Étendre les capacités par une **nouvelle** migration, sans réécrire105 après déploiement. Le mode protégé restera fermé aux anciennes écritures et les nouveaux changements passeront par le circuit approuvé. La sidebar et les premiers écrans restent au Lot1B.
