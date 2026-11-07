# Sûretés et engagements documentaires dans Liasse seule

Version 697 du 21 octobre 2026 — société fictive et base de test uniquement.

Dans **Comptabilité → Liasse fiscale → Préparer depuis des balances externes**,
sélectionner une préparation conservée puis **Documenter les tableaux ETIC B8 et B9**.
Ces tableaux reprennent les colonnes du catalogue HisabPro déjà présent. Ils ne
constituent pas une nouvelle définition du modèle réglementaire et ne donnent
aucun statut officiel à la préparation.

## Préparer le dossier de test

Utiliser une société fictive en MAD, un exercice 2026 et un compte administrateur
ou comptable. Importer les fichiers de recette existants
**BALANCE_FICTIVE_FINANCEMENT695_N.csv** et **BALANCE_FICTIVE_FINANCEMENT695_N1.csv**
du répertoire docs/recette, puis conserver une version. Débit = crédit N :
17 000 MAD ; N-1 : 6 000 MAD. Les engagements ci-dessous sont exclusivement des
hypothèses de recette documentaire : ne pas les enregistrer dans le Journal.
Les données exactes figurent aussi dans **DONNEES_TABLEAUX_ETIC697.json**.

## Comprendre les déclarations

**À compléter** permet de conserver un brouillon partiel sans présumer sa source.
**Saisie documentée — à revoir** exige une justification du tableau et, pour
chaque ligne, une nature et une référence de source permettant de l’identifier.
Les autres informations peuvent rester inconnues : ce statut ne signifie pas
que la rubrique est complète ou réglementairement validée.
**Néant — déclaré et justifié** exige une justification et aucune ligne.
Une liste vide avec À compléter ne signifie jamais qu’il n’existe aucun engagement.

Chaque montant est en MAD, positif ou nul, fini, avec deux décimales maximum et
une borne technique de 9 999 999 999 999,99 MAD. Les virgules décimales sont acceptées.
Le vide reste inconnu ; saisir 0 est une déclaration explicite. Aucune conversion
de devise ni totalisation de sûretés et engagements de sens différents n’est présumée.
Les bornes sont des contraintes de saisie, pas des seuils fiscaux.

## Saisir B8 puis B9

Choisir **B8**, sélectionner **Saisie documentée — à revoir**, saisir la justification
**Contrat fictif697 — sûreté déclarée** puis **Ajouter une ligne au tableau**.
Renseigner Nature : **Hypothèque fictive697** ; Objet : **Immeuble fictif** ;
Tiers : **Banque fictive697** ; Montant couvert : **12345,67** ; laisser Valeur nette
comptable vide ; Date / lieu d’inscription : **À confirmer** ; Référence de source :
**Annexe A fictive697**. La valeur nette ne doit pas être déduite arbitrairement
de la balance ou remplacée par zéro.

Choisir **B9**. Les saisies B8 restent dans le brouillon. Sélectionner
**Saisie documentée — à revoir**, justification **Relevé fictif697 des engagements**.
Ajouter une ligne : Reçu / donné **Donné** ; Nature **Caution fictive697** ;
Montant exercice **2000** ; Montant N-1 **0** ; Observation **Recette uniquement** ;
Référence de source **Annexe B fictive697**. Ce N-1 est déclaré d’après la source
fictive, pas calculé depuis la balance. B8 et B9 ne s’additionnent pas.

Confirmer les données puis **Conserver les tableaux ETIC dans une nouvelle version**.
Les deux tableaux sont conservés ensemble ; la nouvelle version est sélectionnée.
La précédente reste consultable sans modification. Auteur, date UTC, catalogue,
valeurs et empreinte de source sont conservés. Notes, échéances et financement
existants sont préservés. Les pièces jointes restent propres à leur version ;
elles ne sont pas copiées automatiquement dans la nouvelle version.

Si une note B8/B9 est déclarée non applicable alors que son tableau contient des
lignes, une alerte demande de revoir les deux compléments. Rien n’est effacé ou
reclassé automatiquement. Modifier les notes reste une opération distincte.

## Vérifier ou corriger

Le rôle lecture consulte les tableaux et exporte la préparation ; il ne peut
pas modifier les champs ou conserver une version. Un refus serveur conserve le
brouillon pour correction. Une modification de saisie retire la confirmation.
**Retirer la ligne du brouillon** ne touche pas une ancienne version : seul un
nouvel enregistrement conserve le retrait. **Relire les tableaux conservés**
réinitialise le brouillon à la version sélectionnée ; ne pas l’utiliser avant
d’avoir conservé une saisie que l’on souhaite garder.

PDF et Excel présentent les mêmes valeurs, les sources et les inconnus avec
l’identité et le logo actuels. Le dossier ZIP ajoute tables_etic_documentaires.json
et son SHA-256 au manifeste. Une formule saisie dans un texte reste du texte
Excel ; les montants sont numériques lorsqu’ils sont représentables exactement.
Les exports ne créent pas d’écriture, de liquidation ni d’archive fiscale définitive.

## Cahier de vérification humaine

Tous les cas ci-dessous restent **Non testé** pour la recette utilisateur.
Les résultats des bancs automatisés sont documentés séparément dans Test.
Capturer la version et l’empreinte visibles pour chaque preuve.

| ID | Actions et données exactes | Résultat, contrôle et preuve attendus | Statut humain |
|---|---|---|---|
|ET697-01|Dans une préparation fictive conservée, ouvrir B8/B9 avant saisie.|Deux tableaux À compléter sans ligne. Aucune absence d’engagement présumée. Capture de la version et des deux déclarations.|Non testé|
|ET697-02|Saisir les deux lignes chiffrées du mode d’emploi, changer B8/B9 puis conserver avec confirmation.|B8 12 345,67 MAD et valeur nette inconnue ; B9 2 000 MAD et N-1 explicitement nul. Brouillons préservés, nouvelle version sélectionnée, ancienne intacte. Captures et JSON ZIP.|Non testé|
|ET697-03|Dans une nouvelle saisie, remplacer montant couvert par NaN, confirmer et tenter de conserver ; corriger en 0 puis conserver.|Refus explicite, aucune version créée sur refus, brouillon conservé. Après correction et confirmation, zéro conservé exactement. Captures de l’erreur et du succès.|Non testé|
|ET697-04|Après le cas02, choisir Néant pour B9 en laissant la ligne ; tenter de conserver. Retirer la ligne explicitement et conserver avec justification Revue fictive697, aucun engagement.|Première demande refusée. Nouvelle version B9 Néant justifiée et sans ligne ; version précédente toujours avec caution. Captures comparées.|Non testé|
|ET697-05|Avec un lecteur de la société fictive, ouvrir une version documentée puis exporter le ZIP. Avec un compte d’une autre société sans invitation, demander cette préparation.|Lecteur : champs désactivés, aucun bouton de conservation, export autorisé. Autre société : données non accessibles. Captures des droits.|Non testé|
|ET697-06|Configurer un logo de test, télécharger PDF/Excel/ZIP de la même version. Si note B8 non applicable et ligne B8 présente, consulter l’alerte.|Logo et version cohérents ; références et inconnus conservés ; JSON et manifeste présents ; alerte visible sans effacement automatique. Conserver les exports et vérifier les empreintes.|Non testé|

Aucune écriture comptable ni aucun impact fiscal n’est attendu pour ces six cas.
La revue des contrats réels et de leur qualification appartient au responsable
du dossier. Les autres tableaux structurés, compléments fiscaux et spécifications
RAS/EDI officiels restent à traiter séparément. RH/paie et point6 restent différés.
