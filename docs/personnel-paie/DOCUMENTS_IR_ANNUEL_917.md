# Télécharger le contrôle annuel et ses sources

Dans **Personnel & Paie → 05 · Fiscalité salariale → Contrôle annuel IR**, ouvrir un résultat relié à son RNI annuel constitué. Deux boutons sont disponibles : **Télécharger le contrôle IR en PDF** et **Télécharger le contrôle IR en Excel**. Aucun montant ne se ressaisit. Ce complément917 nécessite le code915 et sa migration122 ; il n’ajoute aucune migration ou règle fiscale.

Le document reprend le RNI exact, la base annuelle arrondie, les tranches, la réduction familiale, le résultat, les frais annuels et les douze sources mensuelles avec leurs identifiants et empreintes. L’export relit les snapshots et leurs liens ; il ne recalcule aucune préparation ou paie. Une source devenue périmée pour un nouveau calcul ne fait pas disparaître le document historique d’un contrôle déjà conservé.

L’identité et le **logo actuels de la société** apparaissent dans les documents, distinctement des informations du salarié conservées dans le snapshot. Les logosPNG/JPEG intégrés passent par le service commun des exports. Sans logo, le document reste disponible. Aucune image n’est téléchargée depuis une URL ou un chemin fourni par un utilisateur.

Le classeur comporte **Identite, IR annuel, Frais annuels, Tranches, Sources mensuelles, Regles et anomalies**, ainsi qu’une feuille **Logo société** lorsqu’un logo existe. Les montants sont conservés **comme texte exact**, afin de garder les décimales d’origine. Les noms et références sont aussi du texte : une référence commençant par `=` ne devient pas une formule Excel. Le classeur ne recalcule pas un impôt et n’est pas un bulletin.

Pour le [jeu915](JEU_IR_SOURCE_PAIE_915.json), comparer : RNI**83881.0200**, base**83890.00**, IR avant famille**7167.0000**, réduction**1200.0000**, IR annuel arithmétique**5967.0000**. Les douze périodes vont de2026-01-01 à2026-12-01. Une famille inconnue conserve **À compléter** pour le résultat final ; aucune valeur manquante ne devient zéro.

Les accès exigent les habilitations de lecture d’identité et de rémunération, dans la société concernée. Le profilPersonnel seul dispose uniquement des chemins d’export PDF/Excel prévus. Les réponses sont privées et sans cache. Chaque téléchargement réussi ajoute un événement **CONTROLE_IR_EXPORTE** dans l’historique du dossier, avec l’identifiant du contrôle, sa source, son format et son empreinte ; le motif de l’événement ne recopie pas les montants. Le contrôle, les préparations et les écritures comptables ne sont pas modifiés.

Après révocation des droits, cliquer **Actualiser** : les résultats et boutons disparaissent. Un ancien fichier téléchargé sur le poste reste un document confidentiel à conserver selon les règles internes ; l’application ne peut pas révoquer un fichier déjà remis à un utilisateur autorisé.

Les contrôles annuels manuels sans rattachement au RNI constitué gardent leur consultation existante. Ce nouveau document exige le parcours sourcé : il n’invente ni salarié ni provenance pour une ancienne saisie manuelle.

La retenue mensuelle, les imputations, le versement, le net, les bulletins et les écritures de paie restent non déterminés par ces exports. La recette utilisateur, les polices/rendus sur votre poste, la restauration d’exploitation et la production restent à valider. Aucune conformité officielle n’est déclarée.

[CahierPDF](RECETTE_DOC_IR_PAIE_917.pdf) · [SuiviExcel](SUIVI_DOC_IR_PAIE_917.xlsx) · [Données](JEU_DOC_IR_PAIE_917.json) · [Installation sur copie](INSTALLATION_COPIE_PAIE_119_122.md).
