# Rapprocher une capture TVA avec une écriture déjà validée

Ce module conserve un **rapprochement comptable documentaire**. Il ne crée
aucun règlement ou mouvement comptable et ne certifie ni le versement fiscal,
ni un dépôt, ni un crédit imputable. Le montant non rapproché indique seulement
la part du montant capturé qui n’a pas encore été liée à une pièce.

## Installation

La migration additive `hisabpro-backend/103_ras_rapprochements_versement.sql`
doit être appliquée explicitement par l’administrateur, après la chaîne102,
avec une sauvegarde et les procédures de déploiement habituelles. Aucun SQL
n’est exécuté automatiquement au démarrage. Sans103, la consultation de ce
panneau indique la migration manquante ; les fonctions099 existantes restent
distinctes. **La base PostgreSQL réelle de l’utilisateur n’a pas été utilisée
ni migrée pendant le développement.**

Pour vérifier la chaîne sur une base jetable, depuis la racine du dépôt :

```powershell
hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/recette_installation_vierge_103.py --rapport .codex-tests/installation103.md
```

Ce programme crée sa propre cible isolée, refuse l’option `--url`, contrôle et
supprime cette cible. Il ne constitue pas une commande de migration de votre base.

## Utilisation

Ce rapprochement est limité aux sociétés dont la devise est explicitement
**MAD**. Une autre devise est refusée ; aucune conversion n’est supposée.
L’interface fonctionne aussi sur un accès HTTP local sans `crypto.randomUUID`,
en utilisant le générateur cryptographique partagé de l’application.

1. Dans **Journal**, saisir et valider la véritable pièce comptable à rapprocher
   si elle n’existe pas encore. Le module ne choisit aucun compte fiscal à votre
   place. Il recherche une pièce validée avec débit du compte choisi dans la
   capture et crédit de trésorerie ; une OD de capture/annulation est exclue.
2. Ouvrir **Déclaration TVA**, puis **Registre des retenues TVA · année**.
   Le même registre est accessible depuis la Liasse fiscale.
3. Sur une capture **opérée sur achat**, ouvrir
   **Rapprochement comptable d’un versement**. L’OD de la capture doit être
   validée et la capture active pour créer un lien.
4. Renseigner tout ou partie de la référence, cliquer **Chercher une pièce
   validée**, puis sélectionner la pièce. Les pages de50pièces disposent de
   commandes précédent/suivant. Le débit disponible est relu lors de l’enregistrement.
5. Renseigner le **Montant à rapprocher MAD**, puis confirmer le rapprochement
   documentaire et l’enregistrer. Un montant partiel est possible. Le serveur
   refuse un dépassement du montant capturé ou du débit disponible, y compris
   pour deux demandes simultanées. Une même clé de demande n’ajoute pas deux liens.
6. Consulter la date comptable, la référence, le montant, l’acteur et l’empreinte
   des faits conservés. **La date comptable n’est pas assimilée à la date effective
   du versement.** Une pièce source contrepassée est signalée sans retrait automatique.
7. En cas d’erreur d’affectation, utiliser **Retirer le rapprochement**, saisir
   le motif et confirmer. L’ancien lien et le retrait restent visibles. Aucune
   écriture n’est supprimée, modifiée ou contrepassée par ce retrait.

Une capture annulée conserve son historique de rapprochements, avec une alerte
et une capacité documentaire indisponible. Il faut revoir les pièces et retirer
les liens devenus incorrects ; aucune compensation fiscale n’est calculée.

## Exemple strictement fictif

Capture opérée75MAD, compte explicitement choisi4457 ; pièce validée débit4457
75MAD / crédit5141 75MAD. Le choix4457 est celui du jeu, pas un compte imposé par
le logiciel ou une prescription réglementaire de ce guide.

- Rapprocher30MAD : montant rapproché30 ; capacité documentaire45.
- Rapprocher ensuite45MAD : montant rapproché75 ; capacité documentaire0.
- Retirer le lien45MAD : montant rapproché30 ; capacité documentaire45.

Dans les trois cas, la pièce validée reste exactement75MAD et le Journal est
inchangé. **La capacité documentaire45 ne signifie pas qu’il reste45MAD à payer.**

## Consultation, documents et droits

Le rôle Lecture peut consulter, actualiser et télécharger le
**PDF des rapprochements documentaires**, sans créer ou retirer un lien.
Les autres sociétés restent inaccessibles. Le PDF reprend les liens actifs et
retirés, les faits, les empreintes et le logo/identité actuels, hors empreinte.
Il s’agit d’un document interne distinct des exports annuels du registre099,
qui ne contiennent pas ces rapprochements. Une incohérence d’empreinte bloque
la lecture plutôt que d’afficher une preuve altérée.

Pour consulter ou joindre le véritable reçu, utiliser les justificatifs de la
pièce du Journal. Le PDF interne n’est pas ce reçu et ne remplace pas le modèle
de l’administration. Les règles de déclaration, imputation et formats DGI
restent à qualifier ; elles ne sont pas activées par la présence d’un rapprochement.

Les recherches officielles du20octobre ont retrouvé un passage indexé de
l’[article112 du CGI2026](https://www.finances.gov.ma/Publication/dgi/2025/CGI-2026-FR.pdf)
concernant le relevé selon modèle administratif ; les spécifications applicables
n’ont pas été obtenues. Les ouvertures directes de la NC735 et de la fiche MEF
ont échoué. Aucun imprimé/XSD ni nouvelle règle fiscale n’a été déduit de ces recherches.

Recette humaine et installation cible restent à effectuer. Les résultats
automatisés sont consignés dans [le rapport681](../Test/rapport_ras_rapprochements681.md).
