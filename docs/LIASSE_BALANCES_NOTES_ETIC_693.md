# Notes de préparation ETIC depuis des balances conservées

Version 693 du 21 octobre 2026 — recette fictive, données réelles interdites.

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
ouvrir **Importer N / N-1**, ou **Consulter les préparations** pour le rôle lecture.
Sélectionner une préparation conservée puis **Documenter les notes de préparation ETIC**.

La liste reprend le catalogue ETIC déjà présent dans HisabPro. Chaque rubrique
possède un texte de travail, une référence ou justification et un état de note :
**À compléter**, **Note renseignée**, **Non applicable — déclaré**. L’absence de
note reste inconnue. Une déclaration non applicable doit être justifiée ; elle
n’est pas une conclusion automatiquement établie depuis les comptes.

Ces notes ne remplacent pas les tableaux structurés, leurs ventilations ou les
contrôles fiscaux. Les compteurs portent sur les notes, jamais sur le degré de
conformité ou sur une liasse prête à déposer. B6/B7 gardent leur formulaire
documentaire d’échéances séparé.

## Utilisation

1. Choisir la rubrique. Saisir un texte et sa source. Pour une note renseignée,
   le texte et la justification sont requis ; pour non applicable, la justification
   est requise. Un texte provisoire peut rester À compléter.
2. Passer à d’autres rubriques : les brouillons restent dans le formulaire ouvert.
   Modifier un champ annule la confirmation précédente. Fermer/recharger le
   formulaire abandonne les brouillons non conservés.
3. Cocher la confirmation puis **Conserver les notes ETIC dans une nouvelle version**.
   Tous les champs de toutes les rubriques du formulaire sont conservés ensemble.
   La nouvelle version apparaît immédiatement, sans F5.
4. Rouvrir les notes pour vérifier texte, état, auteur, date UTC et version source.
   Les titres du catalogue sont figés avec les notes ; leur évolution future ne
   réécrit pas les versions historiques.
5. Utiliser les boutons d’export de la préparation : PDF, Excel et dossierZIP
   reprennent les mêmes notes. Le ZIP contient `notes_etic_documentaires.json`,
   couvert par le manifesteSHA256. PDF/Excel gardent le logo actuel de la société.

Une nouvelle conservation remplace la liste de notes dans la nouvelle version.
Repasser une rubrique À compléter et vider son texte ne modifie aucune ancienne
version. L’API accepte une liste explicite de remplacement ; les rubriques
omises y restent À compléter. Les autres compléments de la préparation,
balances et états déjà figés sont conservés intégralement.

Les **pièces jointes sont propres à leur version**, comme au lot691 : elles ne
sont pas copiées silencieusement vers une nouvelle version. Vérifier et joindre
les pièces pertinentes à la version que l’on souhaite transmettre. Les notes
ne garantissent ni l’existence ni la validité d’une référence citée.

## Recette manuelle sur société fictive uniquement

Prérequis : installation de test autorisée, migrations déjà nécessaires aux
préparations (071) et aux pièces (104, si utilisées), un administrateur,
un comptable et un lecteur. Utiliser la balance fictive
[687](recette/BALANCE_FICTIVE_ECHEANCES687.csv) : capital6000, clients8000,
fournisseurs3000, banque1000 ; débit=crédit9000, résultat0. Aucun de ces comptes
ni montants n’est modifié par les notes. Aucune écriture ou incidence fiscale
n’est attendue pour les cinq cas suivants. Recette humaine **Non testé**.

| ID | Objectif / actions exactes | Résultat et preuve attendus | Statut |
|---|---|---|---|
|NET693-01|Importer/conserver la balance, ouvrir les notes sans saisie.|Toutes les notes À compléter ; aucun zéro ou non applicable présumé. Capture initiale.|Non testé|
|NET693-02|A1 : Note renseignée ; texte `Méthodes fictives à vérifier.` ; source `Annexe fictive NET693`. B9 : Non applicable — déclaré ; justification `Revue fictive des engagements NET693`. Confirmer/conserver.|Version suivante sélectionnée ; les deux rubriques relues, auteur/date/source présents. Ancienne version inchangée. Capture des deux notes.|Non testé|
|NET693-03|Dans une nouvelle saisie, B8 Non applicable — déclaré, justification vide. Confirmer/conserver ; puis saisir `Revue fictive NET693` et réessayer.|Premier envoi refusé et brouillons conservés ; seconde confirmation nécessaire ; conservation réussie. Captures du refus et de la version créée.|Non testé|
|NET693-04|Ouvrir la version avec les notes sous le rôle lecture puis télécharger PDF/Excel/ZIP.|Champs désactivés, aucune action de conservation ; notes identiques dans les trois formats, logo dans PDF/Excel, JSON dans manifeste. Conserver fichiers et capture.|Non testé|
|NET693-05|Revenir sous administrateur. Remettre A1 À compléter et vider texte/source, conserver. Reconsulter l’ancienne version puis la nouvelle et leurs pièces.|Ancienne note intacte ; nouvelle à compléter. Autres notes et échéances inchangées. Pièces propres à chaque version, sans copie implicite. Captures et comparaison des sources/écritures.|Non testé|

## Portée technique

Pas de nouvelle migration, pas de modification du Journal ni des lignes ETIC
comptables. Le contenu est enregistré dans une nouvelle préparation immuable.
Empreinte attendue, UUID de rejeu, verrou société et isolation des droits sont
contrôlés. Les notes sont du texte, jamais des formules Excel ou du HTML exécuté.
Les limites de10 000caractères pour le texte et2000 pour la référence protègent
les exports ; les retours à la ligne sont conservés dans le PDF.

La recette utilisateur et la mise en production restent à valider. Le tableau
de financement et les autres données structurées restent à compléter ; aucun
format DGI/EDI ni règle fiscale nouvelle n’est introduit par cette étape.
