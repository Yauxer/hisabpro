# Prochaine implantation : reprises partielles de provisions

État du19octobre2026, lot611 : **conception seulement**. Aucun écran, schéma,
API ni calcul de reprise n’a été ajouté. Les changements utilisables de la
reprise restent ceux décrits dans le [rapport591–609](RAPPORT_SESSION_20261019_591_609.md).

## Constats précis dans le dépôt

`models.AjustementInventaire` porte le montant, les comptes et les liens vers
l’écriture initiale et sa contrepassation. Il ne possède aucun registre de
reprises partielles. `contrepassation_id` sert déjà aux inverses CCA/PCA/FNP/FAE.
Ne pas détourner ce lien pour représenter plusieurs reprises de provision.

`services/cloture_service.py` distingue désormais les familles par type603.
Les provisions ne reçoivent pas de contrepassation automatique. Le montant
de dotation est déclaré ; le logiciel ne connaît pas la disparition du risque.

`routers/ecritures.py` protège déjà les captures RAS lors de modification,
suppression et contrepassation générique. La même question devra être traitée
pour les futures pièces de reprise : une simple FK ne suffit pas à éviter
un message500 ou une annulation générique désynchronisée du registre.

## Contrat proposé pour le prochain lot

1. Sélection explicite d’un ajustement de provision/dépréciation appartenant
   à la société, avec écriture initiale définitive. Contrôler ses lignes réelles
   par rapport aux faits du dossier. Une ancienne classification incohérente
   reste visible ; aucune réparation implicite par le nouveau formulaire.
2. Saisir une date dans une période ouverte, un montant exact au centime et
   une justification de la reprise. Référence/date justificative restent
   facultatives conformément aux règles existantes. Ne pas inventer de tiers.
3. Afficher séparément dotation source, reprises définitives, montants réservés
   par des brouillons et capacité disponible **dans ce seul registre lié**.
   Ce n’est pas le solde comptable global du compte : des mouvements manuels
   sans lien peuvent exister et ne doivent pas être attribués par heuristique.
4. Produire un aperçu avant création. Le compte de reprise dépend de la nature
   réelle de la dotation : exploiter uniquement un rapprochement déterministe,
   sinon demander un choix explicite sans prétendre qualifier sa fiscalité.
   [Sources disponibles](SOURCES_PROVISIONS_20261019.md) : extraits CGNC seulement ;
   qualifier chaque schéma retenu avant de le coder. Les choix d’exploitation,
   financiers et non courants ne sont pas interchangeables.
5. Créer un brouillon lié et le valider par le Journal ordinaire. Un UUID
   technique d’idempotence doit être généré par l’interface ; pas de champ
   technique à saisir par le comptable. Même clé/mêmes faits : même résultat ;
   même clé/autres faits :409, sans doublon.
6. Annulation contrôlée : conserver dossier et pièce d’origine, avec inverse
   traçable lorsque nécessaire. Une annulation ne libère la réservation qu’en
   cohérence avec son état comptable. L’inverse doit respecter une période
   ouverte, même si l’exercice source est clos. Ne pas utiliser une baisse
   silencieuse du montant initial ni supprimer une pièce définitive.

La règle de capacité doit compter les reprises actives et les réservations de
brouillons, sous verrou de la source ; deux demandes concurrentes ne peuvent
consommer le même reliquat. Les transitions de validation/annulation et les
corrections depuis le Journal doivent suivre un ordre de verrous compatible
avec la clôture098. Tester explicitement les courses, pas seulement les requêtes
séquentielles. Une augmentation de provision doit rester une nouvelle source
distincte, sans fusion déduite de libellés semblables.

## Persistance et compatibilité à préparer

Prévoir un registre dédié, société/source/pièce/acteur/date/montant/faits figés,
liens d’annulation et clé unique d’idempotence. La structure exacte et ses FK
doivent être définies avec les contraintes réellement présentes, sans supposer
une unicité composite existante. Le précédent employes/grh_absences interdit
de compter sur `create_all` pour modifier une table déjà existante.

La prochaine migration candidate serait100, **non créée dans ce lot**. Elle
devra être additive, rejouable et accompagnée des droits SQL minimaux, protections
de dossier et contrôles de société. Préférer une table gérée par migration avec
garde explicite lorsqu’elle manque, selon le modèle099, pour que le démarrage
ne tente pas une création avant ses contraintes préalables. Ne modifier aucun
ancien SQL. Installation vierge/rejeu/restauration doivent être testés sur nonce,
puis la migration réelle reste une étape de déploiement distincte.

## Recette technique à implémenter

- Dotation fictive1000, reprise400 puis200 : capacités600 puis400 ; sources
  inchangées et débits/crédits exacts. Ne pas présenter ces chiffres comme
  une estimation de risque réel.
- Demande supérieure au disponible, zéro, négatif, NaN/infini, booléen, précision
  excessive : refus avant mutation. Source étrangère :404 ; lecteur :403.
- Deux demandes concurrentes de600 sur1000 : une seule acceptée ; même clé
  répétée : un seul dossier/une seule pièce, y compris après timeout client.
- Source en brouillon ou classification historique incompatible : diagnostic
  explicite ; aucune source ou date inventée pour rendre le contrôle vert.
- Annulation d’un brouillon et d’une pièce définitive, tentative de suppression/
  modification/contrepassation depuis Journal, période destination fermée,
  clôture concurrente et source dans exercice antérieur clos.
- API/Edge1440 et390, changements société/exercice, consultation seule, aperçu,
  création, validation, annulation, CPC/bilan/FEC et dump/restore natifs avec ACL.

Ces cas ne sont **pas exécutés** pour cette future fonctionnalité. Le lot611
ne marque aucun périmètre fonctionnel supplémentaire terminé. Prochaine action
exacte : qualifier les schémas de reprise retenus puis écrire le contrat métier
et ses tests, définir migration100 et protections Journal, avant toute UI.
