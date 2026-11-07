# Appliquer la session de lecture qualifiée — 11 octobre2026

Base de reprise : dépôt et cumulatif `HisabPro_Session_20261011_0811_Cumulatif_Verifie.zip`
déjà vérifiés avant intervention. Ne pas réappliquer les anciens correctifs
si leurs fichiers sont présents. Cette session ajoute uniquement ses différentiels.

## Préparation et application

1. Préparer une copie de recette isolée et sa sauvegarde habituelle. Conserver
   vos fichiers locaux avant remplacement ; comparer toute modification locale
   non livrée. Les fichiers de configuration personnelle restent à préserver.
2. Extraire le ZIP cumulatif de cette session à la racine HisabPro en respectant
   les chemins `hisabpro-backend/...`, `src/...`, `Test/...` et `docs/...`.
   Le cumulatif contient les dernières versions de ses différentiels ; il évite
   de copier plusieurs versions d'un même fichier.
3. Aucun script SQL ni migration n'est ajouté par cette session. N'exécuter
   aucun SQL de réparation et ne remplacer aucune donnée historique.
4. Redémarrer le backend sur l'installation isolée et reconstruire le frontend
   avec la procédure habituelle. Appliquer ensemble les fichiers backend et UI :
   la lecture ajoute des montants nullable et les diagnostics correspondants.
5. Ouvrir le guideWord/PDF version10 et effectuer les vérifications ci-dessous.

## Vérifications ordinaires

- Dans Factures, retrouver les pièces connues, leurs lignes et les montants.
- Un prix explicitement nul reste zéro. Une liste réellement vide reste à zéro.
- Exécuter sur données fictives la création, validation, règlement partiel puis
  complet et le lettrage, côté Vente et Achat. Vérifier les écritures et soldes
  à chaque phase avec le cahier de recette et ses données attendues.
- Vérifier les affichages du cycle commercial et les alertes du tableau de bord.
- Une erreur technique de chargement conserve l'alerte et le bouton Réessayer.

## Vérification négative de lecture historique

Cette variante exige un jeu fictif fourni par le banc isolé363. Ne pas injecter
de NaN, d'infini ou de valeur manquante dans une base existante pour la reproduire.
Si ce jeu est absent, classer ce cas Bloqué et poursuivre la recette normale.

La pièce saine HT100/TVA20/TTC120 doit rester visible avec la pièce défaillante.
La seconde affiche « Montants à vérifier » et un détail en lecture seule.
Les valeurs inconnues ne doivent pas apparaître à zéro ; ses identifiants,
description et sources persistées restent conservés. Les opérations dépendantes
des montants et le CSV contenant cette pièce sont indisponibles. Les calculs
financiers concernés doivent répondre par un refus explicite, sans solde fictif.

Réessayer relit les données et ne répare aucune facture. La remise à une valeur
connue effectuée par les tests vise uniquement leur brouillon fictif. Toute
réparation d'une vraie pièce exige un justificatif et un traitement distinct,
avec conservation de la piste d'audit et des restrictions de validation.

## Preuves et reprise

- `Test/rapport_lecture_factures_historiques_363.md` : correction et suites ciblées.
- `Test/rapport_guide_lecture_364.md` : contrôles Word/PDF et visuels.
- `CODEX_PROGRESS.md` : commandes, succès, échecs initiaux et étapes actives.
- Matrice et registre dans `docs/audit` : périmètres encore partiels ou bloqués.

La consolidation365 garde son résultat distinct et ne doit pas être présumée
réussie à partir des suites ciblées. Recette humaine, ouverture dans Office,
validation d'un dossier réel et préparation de production restent à effectuer.


## Règlements et navigation livrés dans cette session

Les fichiers368 ajoutent une projection de lecture des règlements distincte
des règles de saisie. Les sources défaillantes restent visibles, les totaux
inconnus restent à vérifier et leurs opérations sont indisponibles.
Aucun SQL de réparation n'est fourni. Le cas nul reste explicitement0,00
avec diagnostic, car un règlement nul est interdit à la saisie.

Les fichiers370 ajoutent le menu repliable sur écran de767px ou moins.
Vérifier son ouverture, une navigation, sa croix, Échap et un clic extérieur.
Le bandeau société/exercice reste disponible. Les tableaux larges conservent
le défilement nécessaire dans leur propre page ; vérifier les appareils ciblés.

Preuves distinctes :3653170réussis avant368/370 ;36824ciblés et125connexes
réussis ;37040connexes puis18finaux après filtre. Les résultats se recoupent
et ne s'additionnent pas. Consulter leurs rapports et les échecs initiaux
dans CODEX_PROGRESS.md. Le ZIP cumulatif conserve les dernières versions.
