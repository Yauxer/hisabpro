# Justificatifs des préparations de balances — mode d’emploi et recette

Version 1 du 21 octobre 2026

Le panneau permet de joindre à une version conservée les documents qui expliquent
les montants renseignés : état des créances, échéancier reçu, analyse signée ou
autre source disponible. L’ajout conserve l’auteur, la date d’ajout, la référence,
la taille et l’empreinte du fichier, sans modifier les balances ou le Journal.
Le contenu doit être contrôlé par le comptable ; sa présence ne certifie aucune
qualification fiscale ni complétude de l’ETIC.

## Installation et préparation du laboratoire

Le technicien applique explicitement la migration additive104 après la chaîne103,
sur une cible autorisée et sauvegardée. Aucune migration réelle n’a été exécutée
pendant le développement. Le démarrage de l’application n’applique pas104.
Sans cette migration, le panneau explique son indisponibilité ; les préparations
et leurs exports restent disponibles, le ZIP signalant ce module indisponible.

Pour contrôler le schéma sur une cible jetable créée par le programme, depuis
la racine du dépôt :

hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/recette_installation_vierge_104.py --rapport .codex-tests/installation104.md

Cette commande refuse une URL externe et ne migre pas la base utilisateur.
Elle qualifie le schéma et un runtime partiel ; les tests applicatifs sont
distincts. La recette humaine se déroule sur une base dédiée, jamais une société
comptable réelle. RH/paie, point6 humain et production restent différés.

Réutiliser le laboratoire du cahier687 : RECETTE ECHEANCES 687 SARL, MAD,
exercice 2026 ouvert, version 3 avec bilan 9000 et CPC 0. Créance 3421 de 8000,
ventilée2000  à plus d’un an et 1000 échues, reliquat5000 non qualifié. Dette 4411
de 3000 ventilée1000 dans chaque catégorie, reliquat0. Aucune écriture au Journal.
Les fichiers fictifs sont fournis : ETAT_CREANCES_FICTIF691.pdf et
FICHIER_REFUSE_FICTIF691.txt. Les données et le SHA du PDF figurent dans
DONNEES_JUSTIFICATIFS691.json ; aucun document réel n’est fabriqué ou remplacé.

## Utiliser les justificatifs

Dans Comptabilité → Liasse fiscale → Préparer depuis des balances externes,
sélectionner la version conservée puis ouvrir Justificatifs complémentaires
de cette version. Choisir le fichier, renseigner éventuellement une référence
documentaire, puis Joindre et conserver le justificatif. Sans référence saisie,
le nom original sert de référence. Aucun champ de date comptable n’est ajouté.

Le fichier peut être PDF, PNG/JPEG, Excel ou Word, dans la limite indiquée dans
le panneau : maximum 10 Mo par fichier,50 Mo cumulés par version. Une configuration
plus restrictive est affichée par l’application. L’interface se rafraîchit après
l’ajout et conserve les noms originaux pour la lecture ; le nom physique stocké
est attribué par l’application pour éviter un écrasement.

L’auteur et la date sont ceux de l’ajout, sans assimilation à la date fiscale
de la pièce. L’empreinte affichée est celle conservée à l’ajout. Le téléchargement
individuel et le ZIP relisent les octets et contrôlent leur taille et empreinte.
Un fichier absent ou modifié bloque sa délivrance : restaurer la bonne sauvegarde
ou faire examiner le stockage ; aucune preuve de remplacement n’est inventée.

Les ajouts restent dans l’historique et ne proposent pas de suppression. Une
nouvelle version de balances ne recopie pas automatiquement les pièces d’une
ancienne ; terminer la ventilation, sélectionner la version à transmettre puis
y joindre les sources pertinentes. L’ancienne version garde ses pièces.
Le rôle Lecture consulte et télécharge, sans ajouter de fichier.

## Deux empreintes et un dossier ZIP

L’empreinte historique de la préparation couvre ses données conservées. Les
pièces ajoutées ensuite sont des compléments séparés, hors de cette empreinte.
Leurs métadonnées et leurs fichiers figurent dans le ZIP de préparation :
justificatifs.json et le dossier justificatifs/. Le manifeste SHA-256 du ZIP
contrôle chaque fichier réellement livré, y compris ces pièces.

Le contenu original des justificatifs est conservé octet pour octet. Le PDF
et l’Excel générés de préparation portent le logo actuel de la société ; les
documents sources joints ne sont pas réécrits pour ajouter un logo ou une mention.
Ce paquet reste une préparation interne, sans archive fiscale définitive,
preuve de dépôt DGI, crédit fiscal ou EDI officiel.

## PJD691-01 — joindre la source fictive, à effectuer

Statut humain : Non testé. Prérequis : laboratoire et version 3 décrits ci-dessus,
administrateur connecté et migration 104 préparée par le technicien.
Données : ETAT_CREANCES_FICTIF691.pdf ; laisser la référence documentaire vide.

1. Relever l’empreinte de la version 3 avant l’ajout et vérifier le Journal vide.
2. Ouvrir Justificatifs complémentaires de cette version ; choisir le PDF fourni.
3. Cliquer Joindre et conserver le justificatif. Attendre le message de conservation.
4. Vérifier son nom original, la référence égale à ce nom, la date d’ajout,
   l’auteur connecté, la taille et le SHA. Comparer ce SHA au JSON de données fourni.
5. Sans F5, vérifier que le document apparaît. Réouvrir ensuite la version et
   retrouver la même trace. Vérifier la même empreinte de préparation et le Journal.

Résultat attendu : un document, une trace, aucune nouvelle version ni écriture,
bilan 9000/CPC 0 et reliquats inchangés. Aucun impact fiscal nouveau.
Contrôles : comparer les deux empreintes dans leurs périmètres respectifs.
Preuve attendue : capture avant/après et référence du fichier. Résultat réel,
anomalies, preuve réelle et observations : à renseigner par la personne chargée
de la recette.

## PJD691-02 — télécharger le document et le paquet, à effectuer

Statut humain : Non testé. Prérequis : cas 01 terminé.
Données : même version 3 et même PDF.
Utiliser Télécharger le justificatif puis Télécharger le dossier de préparation ZIP.
Extraire le ZIP dans un dossier de recette séparé et ouvrir le PDF joint.
Comparer ses octets ou son SHA au fichier d’origine, puis vérifier sa référence,
son auteur, sa taille et son SHA dans justificatifs.json. Le nom du fichier dans
le ZIP est le nom physique attribué par l’application. Vérifier le manifeste
contre ce fichier et l’empreinte de préparation contre l’écran.

Résultat attendu : pièce identique, métadonnées cohérentes et manifeste valide,
sans prétendre à une certification de contenu. Aucune écriture ou opération
fiscale attendue. Contrôles : taille/SHA, bilan 9000/CPC 0 et Journal vide.
Preuves attendues : fichier téléchargé, ZIP et contrôle SHA ; résultats réels,
anomalies et observations à renseigner.

## PJD691-03 — vérifier Lecture et les sociétés, à effectuer

Statut humain : Non testé. Prérequis : cas 01 terminé ; compteLecture fictif
lecture 691@example.com, mot de passe de laboratoire Recette691!2026 créé par
l’administrateur depuis Administration → Utilisateurs dans la société de recette.
Se connecter en Lecture, ouvrir la même version puis le panneau. Vérifier la
pièce, ses données et son téléchargement ; aucun champ d’envoi ni bouton d’ajout
ne doit être proposé. Sur écran390 px, vérifier la lecture verticale, y compris
les noms et empreintes. Revenir en administrateur, sélectionner une autre société
fictive puis ses préparations : la version et la pièce de la première ne doivent
pas apparaître. Revenir à la société d’origine et retrouver la trace.

Résultat attendu : consultation/export autorisés, ajout et mélange de sociétés
impossibles. Aucune écriture ou conséquence fiscale attendue. Contrôles : rôle,
contexte, empreintes et traces ; preuves/captures et résultats réels à renseigner.

## PJD691-04 — refuser un format, à effectuer

Statut humain : Non testé. Prérequis : administrateur revenu dans le laboratoire,
version 3 avec sa pièce valide. Données : FICHIER_REFUSE_FICTIF691.txt fourni.
Dans le sélecteur système, choisir Tous les fichiers si nécessaire puis ce TXT.
Tenter de le joindre et lire le refus de format. Vérifier qu’aucune nouvelle
trace n’est créée et que le PDF initial reste disponible. Sélectionner à nouveau
le PDF valide si une reprise de saisie doit être vérifiée ; toute nouvelle
validation constitue un nouvel ajout, ne pas l’envoyer inutilement.

Résultat attendu : refus explicite, état et fichiers valides conservés.
Écritures et impacts fiscaux attendus : aucun. Contrôles : liste inchangée,
message lisible, Journal vide ; capture/résultats réels/anomalies à renseigner.

## PJD691-05 — vérifier l’attachement à une version, à effectuer

Statut humain : Non testé. Prérequis : administrateur, version 3 documentée.
Depuis cette version, compléter la justification de la ventilation sans changer
ses montants puis conserver une nouvelle version. Ouvrir ses justificatifs :
aucun fichier n’y est présumé. Revenir à la version 3 et retrouver sa pièce.
Choisir explicitement la nouvelle version et y joindre le PDF si cette source
reste pertinente pour sa ventilation. Vérifier les empreintes propres à chaque
préparation et à chaque fichier.

Résultat attendu : deux versions distinctes, pièces associées explicitement,
ancienne version préservée ; mêmes états chiffrés et zéro écriture créée.
Pas de qualification fiscale nouvelle. Contrôles : sélectionner/relever les
versions effectivement attribuées, sans supposer leurs identifiants techniques.
Conserver captures et ZIP des versions ; résultats réels et observations à remplir.

## Limites et reprise

La preuve d’intégrité d’un fichier n’est pas une preuve de sa validité comptable
ou fiscale. Les autres analyses ETIC, financement, liquidations et modèles DGI
restent à compléter selon la matrice. Les dossiers historiques incomplets restent
visibles. Les données réelles ne sont pas réparées, les écritures définitives
ne sont pas modifiées. Les résultats automatisés sont consignés séparément
dans le rapport691 ; ces cinq cas humains restent à effectuer.
