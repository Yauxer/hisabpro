# HisabPro — bilan de stabilisation du 20 octobre 2026

## Résultat de la session

La stabilisation technique FIN-01/02/03 est terminée dans le périmètre testé.
La candidate est disponible pour la recette utilisateur, avec ses limites
explicites. La roadmap globale reste partielle selon la matrice.

Cette livraison ferme les trois points techniques de la
[liste de sortie](FIN_DEVELOPPEMENT_HORS_RH_20261020.md) dans les périmètres
testés. Les fonctionnalités partielles de la roadmap restent décrites par la
matrice. La stabilisation et la recette utilisateur constituent des jalons
distincts ; aucune conformité officielle ni mise en production n’est validée.

## Modifications utilisables

- Dans Cycle commercial, les factures de Vente et d’Achat sont séparées.
  Le chargement parcourt toutes les pages : un achat situé au-delà des
  100 premières factures reste visible et les compteurs utilisent la liste lue.
- Devis, commandes, livraisons, factures et réceptions client distinguent une
  erreur de lecture d’un vrai dossier vide. Actualiser la liste et Réessayer
  permettent la reprise sans F5. Les anciennes réponses d’exercice, cycle ou
  jeton sont écartées. La panne de la dépendance facture est également signalée
  dans Réception client.
- Les commandes se replient sur mobile. Les tables conservent leur défilement
  horizontal ; les données comptables et les règles de numérotation des
  brouillons sont conservées.

Le [complément d’utilisation](../COMMERCIAL_LISTES_673.md) détaille ces gestes.
Les fichiers applicatifs modifiés sont Commercial.jsx et son CSS. Aucun
backend, modèle, schéma, SQL, droit serveur ou calcul comptable/fiscal modifié.
Aucun PostgreSQL réel ni donnée comptable réelle utilisé ou modifié.

## Tests réellement exécutés

| Contrôle | Résultat exécuté |
|---|---|
| Correctif commercial673 et achats complets/partiels | 28 réussites en189,81s |
| Documents après mise à jour des index673 | 9 réussites en1,51s |
| Campagne commune675 sur code figé | 312 réussites en1424,85s ; zéro échec, erreur ou test ignoré ;30avertissements Python |
| Installation vierge102, incluse dans les312 | 93scripts distincts,29rejeux,43tables métier vides ;77tables antérieures conservées ; droits/rejeu contrôlés et cluster nettoyé ; refus de l’argument URL externe |
| Build Vite courant | Code0 en9,48s ; avertissements de taille du bundle et d’import XLSX conservés |

La [preuve technique675](../../Test/PREUVE_CANDIDATE_HORS_RH_675.json) contient
les identifiants des312cas et les382empreintes applicatives. Les9contrôles
documentaires sont également inclus dans la campagne commune.

La campagne commune regroupe les cas par identité de fonction, puis conserve
leurs variantes paramétrées. Elle couvre les limites de capture RAS, annulation,
registre et documents, factures correspondantes entre sociétés, paiements,
ventilation et lettrage, justificatifs, permissions, contextes des listes,
réceptions et droits de consultation. Le parcours annuel relié à un oracle
indépendant inclut stock, facturation, paiements, TVA, immobilisation, clôture
et à-nouveaux. Le dégressif sur cinq exercices, le multi-société et les accès
secondaires disposent de cas séparés.

Les parcours regroupés utilisent le même banc applicatif complet jusqu’à102,
sous LOGIN non propriétaire ; les cas de dépendances absentes et d’installation
disposent de leurs propres bacs isolés. Les témoins préexistants portent sur trois
sociétés fictives, une vente avec achat correspondant et une RAS annulée
avec deux documents. Leurs lignes, liens et métadonnées documentaires, dont les
empreintes enregistrées, sont comparés avant/après. Les anciennes baselines privées sont explicitement
inaccessibles au collecteur livré.

Les campagnes 673 et 675 se recouvrent : leurs réussites ne sont pas
additionnées pour annoncer un nombre de tests distincts supplémentaire.
Les tests d’installation exécutent séparément la chaîne native vierge ;
ils ne valident aucune application de migration sur un dossier réel.
Le CLI conserve son statut explicite de runtime partiel : sa qualification de
schéma, droits et rejeux est distincte des parcours applicatifs exécutés sur
le banc102 de la campagne commune.

## Historique des échecs conservé

Le défaut initial est reproduit par trois échecs avant correction : mélange
des deux cycles et refus de lecture devenu Aucun devis. Le nouveau banc
cherchait ensuite un numéro définitif sur des factures brouillon ; ce repère
a été corrigé vers le vrai tiers unique, sans modifier le produit.

La veille, la campagne après repli mobile comptait 27 réussites et un timeout
avant l’affichage du login. La reprise du 20 octobre passe 28 cas avec des
traces de contexte, sans augmentation des délais ni assouplissement des
assertions. La cause du timeout initial reste indéterminée et sa réussite
ultérieure ne l’efface pas. Une commande mal nommée avait également échoué
à la collecte, sans exécuter de test. Ces événements figurent dans
[le rapport 673](../../Test/rapport_listes_commerciales673.md) et le journal.

La préparation de675 a rencontré un import modèles hors contexte pytest ;
aucun test ni connexion réelle n’a été exécuté par cette commande. L’extraction
de la fonction pure d’empreintes et la collecte pytest ont ensuite préparé
le banc ; ce problème n’a entraîné aucun changement applicatif.

## Intégrité et livraison

Les382sources applicatives sont identiques avant/après la campagne et après
le build. Les témoins de trois sociétés fictives et les métadonnées de leurs
deux documents sont préservés. Les dossiers du banc applicatif et du cluster
sont nettoyés.106fichiers protégés, dont instructions, démarrage, modèles,
schémas et SQL existants, sont inchangés depuis la référence645.

Les63archives antérieures contrôlées conservent leurs SHA-256 et passent les
contrôles CRC et manifeste. Le différentiel675 contient12fichiers ; le cumul
contient79fichiers ajoutés/modifiés depuis645, avec leurs versions finales.
Le contrôle de livraison vérifie leur liste, les octets et les empreintes
contre le dépôt, puis inclut la fin du journal dans les archives finales.

Les archives sont des différentiels, avec l’arborescence exacte. Elles
complètent le dépôt existant. Environnements, caches, uploads et traces
de test, secrets et bases de données sont exclus.

- [Correctif commercial673](../../HisabPro_673_Listes_Commerciales_Fiables.zip).
- [Qualification finale675](../../HisabPro_675_Qualification_Candidate_Hors_RH.zip).
- [Cumul différentiel645–675](../../HisabPro_Session_20261020_Hors_RH_645_675.zip),
  couvrant les travaux du19octobre et leur reprise du20octobre. Utiliser ce
  cumul pour obtenir les dernières versions des fichiers de ces lots.
- [Bilan645–671](RAPPORT_SESSION_20261019_645_671.md), avec liens vers les ZIPs
  antérieurs par étape, conservés.

Le manifeste garde son nom historique ; son contenu décrit les variantes
actuelles et leurs empreintes. Les archives antérieures restent autonomes
avec leur propre manifeste.

## État du produit et limites restantes

La [matrice de70fonctions](MATRICE_COUVERTURE_HISABPRO.md) conserve
16terminé,47partiel,3absent,4bloqué. La checklist de73demandes utilise un
autre découpage :40terminé,31partiel,1absent,1bloqué. Ces nombres ne sont
ni additionnés ni transformés en pourcentage de préparation à la production.

Les limites à garder visibles sont notamment :

- référentiel DGI exhaustif, modèles151/TP et XML/EDI officiellement applicables
  non obtenus dans le dépôt ; les numéros T1… restent internes ;
- pièces et qualifications historiques FEC/ETIC à compléter à partir de
  sources certaines, sans réécrire les définitifs ;
- périmètres encore partiels de la déclaration, du versement et de l’imputation
  RAS, de Liasse seule et des intégrations entre sociétés ;
- réouverture d’un exercice définitivement clôturé soumise à une décision
  métier distincte ; protections conservées ;
- autres limites fonctionnelles et couvertures précisées ligne par ligne
  dans la matrice, sans les déclarer validées par cette campagne sélectionnée.

RH/paie et le point de recette réservé au retour humain restent différés.
Le guide Wordv15 et les cahiers restent disponibles depuis
[l’index de recette](../recette/PAR_OU_COMMENCER_20261019.md) ; les résultats
humains restent à renseigner. Word et le recalcul interactif Excel n’ont pas
été ouverts pendant cette session.

La prochaine étape utilisateur est la recette du périmètre disponible sur un
dossier fictif isolé. L’installation, les secrets/rôles, les migrations déjà
appliquées, la sauvegarde et l’exploitation du dossier cible restent à qualifier
avant une décision de production. Aucun test de laboratoire ne les prévalide.
Les [procédures d’exploitation](../EXPLOITATION_HISABPRO.md) conservent leurs
instructions et ajoutent les commandes des bancs102/675, distinctes d’une
migration d’un dossier existant.
