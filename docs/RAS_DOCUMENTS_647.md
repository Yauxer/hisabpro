# Documents liés aux captures RAS TVA

Dans **Déclaration TVA**, ouvrir **Registre des retenues TVA** ou
**Préparation mensuelle des retenues opérées**. Le registre est aussi disponible
depuis la liasse fiscale. Sélectionner l'année civile ou le mois de versement
prévu, puis la capture concernée. Le mois prévu ne prouve pas un versement.

## Consulter une pièce

1. Déplier **Documents liés aux OD** sur la capture.
2. Vérifier la section **Capture · OD #…**. S'il existe une annulation,
   une section distincte **Contrepassation · OD #…** apparaît.
3. Les références complémentaires du Journal affichent leur date, leur
   éventuel nom de fichier et leur marquage prioritaire FEC. Une référence
   peut exister sans fichier ; cela reste explicite.
4. Dans **Pièces jointes**, cliquer sur l'icône **Télécharger** du bon fichier.
   Le fichier original est restitué, sans ajout de logo ni transformation.
5. L'icône **Actualiser les pièces jointes** relit la liste. Un refus ou une
   erreur réseau est affiché, sans être présenté comme une liste vide.

Le rôle **Consultation seule** peut consulter et télécharger, sans formulaire
d'ajout. Les droits de société sont vérifiés par l'API. Une pièce d'une autre
société n'est pas rendue accessible par son identifiant.

## Ajouter un document

Avec un rôle administrateur ou comptable, cliquer sur **Joindre un fichier**
dans la section de la bonne OD. Sélectionner un PDF, une image ou un document
autorisé par le stockage existant. Attendre la fin de l'envoi : le fichier,
son complément documentaire et les données du panneau courant sont relus
automatiquement, sans F5. Deux fichiers de même nom ne s'écrasent pas.

L'écran RAS propose la consultation et l'ajout. La gestion documentaire complète
reste disponible dans **Journal → Justificatifs**. Une pièce d'une écriture
définitive est conservée par le flux ordinaire ; l'ajout d'un complément ne
réécrit ni les lignes comptables, ni la référence d'origine, ni le dossier099.
Les règles existantes des brouillons restent distinctes de cette conservation.

Pour une référence sans fichier, utiliser le formulaire de références du
Journal. Le registre reprend ce complément à sa prochaine actualisation.
Une référence déclarée d'attestation dans le dossier RAS et un fichier joint
à l'OD restent deux informations distinctes ; le logiciel ne les assimile pas.

## Exporter

- **Excel** : les feuilles existantes sont conservées. Si des compléments
  existent, une feuille **Documents liés** sépare capture et contrepassation,
  avec ID OD, référence, date, source, nom déclaré et date d'ajout. Les
  références commençant par `=` restent du texte. Le logo société est conservé.
- **PDF** : une section documentaire suit les captures et peut occuper plusieurs
  pages. Le logo société est conservé. Les dates inconnues et références sans
  fichier restent identifiées.
- **CSV** : une section **Documents liés** est ajoutée après les captures,
  avec les mêmes références et protection des textes ressemblant à des formules.

Les montants et totaux RAS ne sont pas modifiés par un ajout documentaire.
Un ajout ou une suppression autorisée dans le Journal modifie l'empreinte du
registre. Si une autre personne intervient entre l'affichage et le téléchargement,
l'ancien export est refusé : cliquer sur **Actualiser le registre** ou
**Actualiser la préparation**, puis télécharger de nouveau.

L'export décrit les références et noms enregistrés dans la base. Il n'embarque
pas les fichiers, et son empreinte de données ne signe pas leur contenu.
Le téléchargement individuel vérifie la disponibilité du fichier. Un fichier
absent ou refusé n'est pas téléchargé comme un faux PDF.

## Périmètre

Il s'agit de documents complémentaires des OD existantes. Leur présence ne
constitue pas une attestation fiscale contrôlée, une preuve de versement, un
crédit imputable ou un bordereau officiel. Le module ne choisit pas leur
qualification à la place du comptable. Aucun nouveau champ obligatoire,
traitement de versement, taux, schéma officiel ou crédit automatique n'est ajouté.

Aucune nouvelle migration pour ce raccordement. Le registre et la capture
nécessitent leur chaîne existante, notamment083/099 ; la mise à jour de la base
réelle reste une opération distincte. Les migrations101/102 concernent les
sociétés liées, pas cet ajout documentaire.

Les [tests et limites du lot647](../Test/rapport_ras_documents647.md) distinguent
l'automatisation isolée de la recette humaine et du déploiement cible. Les
limites de déclaration, imputation et reversement du
[plan hors RH](audit/PLAN_FINALISATION_HORS_RH_20261018.md) restent ouvertes.
