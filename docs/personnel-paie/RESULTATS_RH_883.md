# Personnel / RH883 — résultats exécutés et fin de session

28 octobre2026. Le périmètre livré comprend la date d’entrée connue,les trois régimes déclarés du contrat,leur approbation/lecture à date et leurs masques. Aucune règle d’affiliation,taux,exonération ou calcul de cotisation n’a été introduite.

## Résultats

| Campagne | Résultat réel | Durée pytest |
|---|---:|---:|
| `personnel883_nonreg` |362réussis ;0échec/erreur/ignoré|714,31s|
| `personnel883_qualification_finale` |28réussis ;0échec/erreur/ignoré|129,45s|
| `npm run build` |Code0 ;201modules|Vite4,66s|
| Compilation Python |5fichiers ajoutés/modifiés :OK|Exécutée|

Les28cas de qualification comprennent **11nouveaux cas883** (9API/SQL et2Edge) et17APIworkflow877 rejoués sur le dernier code. Ces17identifiants remplacent leurs résultats antérieurs dans le décompte final :**373cas distincts**,et non390. Répartition :**152unitaires/source,205API-SQL-bootstrapPostgreSQL natif isolé,16Edge/API/PostgreSQL isolé**.

Les362non-régressions ont débuté avant deux corrections complémentaires :filtrage du contrat applicable pour reprendre les régimes et refus de détacher une rémunération future approuvée. Les28qualifications ont tourné après ces corrections ;elles couvrent les deux contrôles et toutes lesAPIworkflow877 sur ce code. Les scénarios antérieurs sans régime ne changent pas de valeurs avec le filtrage. Le frontend est inchangé depuis le build final. Les empreintes et la chronologie sont consignées dans la preuveJSON ;les campagnes ne sont pas présentées comme un lancement simultané sur un seul instantané.

Les avertissements antérieurs Pydantic/SQLAlchemy et Vite(xlsx/chunk) restent visibles. Aucune réussite n’est déduite d’une commande interrompue ou d’un test ignoré.

## Correctifs et garanties contrôlées

-110 appliquée deux fois :anciennes valeurs conservées,colonnes nouvelles nulles sur les anciennes versions ;autres tables inchangées. Migrations antérieures immuables.
-Date d’entrée appliquée seulement après décision ;distincte du début du contrat ;timestamps/nombres refusés comme dates.
-Régimes facultatifs,texte borné ;proposition et décision nécessitent la capacité sensible ;masques des valeurs,motifs et références dans liste,fiche,demandes et historique.
-Versions datées,omissions connues conservées dans le contrat applicable,effacement explicite à confirmer,ancienne version protégée par trigger et permissions runtime.
-Isolation société,absence de mouvement comptable et interdiction de modifier une version approuvée réellement testées.
-CDD expiré :le premier test a reproduit une reprise hors période et un403 indu ;filtre début/fin corrigé,puis test réussi.
-Salaire futur :le premier test a reproduit une nouvelle proposition201 qui aurait détaché une rémunération approuvée ;garde409 partagée entre proposition et approbation,puis montant9876,54 conservé. Aucun salaire ni date validés réécrits.
-UI1440/390 :création avec date connue,contrat et trois régimes,soumission/approbation indépendante,révocation et masques,sans débordement horizontal global. Capture mobile inspectée.

Les campagnes intermédiaires7/9/10cas et les deux échecs reproduits restent conservés ;elles ne sont pas additionnées au total373.

## Recette et livraisons

-[CahierPDF consolidé :20pages,43cas](CAHIER_RECETTE_PERSONNEL_HISABPRO_883.pdf).
-[ClasseurExcel :9feuilles,43statuts humains Non testé](SUIVI_RECETTE_PERSONNEL_883.xlsx),avec résultats réels,anomalies,preuves et tableau de bord recalculé à l’ouverture.
-[Jeu fictif et calculs indépendants](JEU_DONNEES_PERSONNEL_883.json),[cas structurés](CAS_RECETTE_PERSONNEL_883.json).
-[Preuve373identifiants et campagnes](../../Test/PREUVE_PERSONNEL_PAIE_883.json),[480empreintes produit](../../Test/CANDIDAT_PERSONNEL_PAIE_883.json),[XMLJUnit](../../Test/preuves_personnel883/).
-[Usage,installation,cohérence et limitesD05](REGIMES_ET_LIMITES_RH_883.md).

Le calcul indépendant des trois bases connues reste23000,10MAD,puis23876,54MAD après hausse. P004/P005 sont des dossiers supplémentaires sans salaire attesté ;ils ne valent pas zéro et ne permettent pas d’affirmer une masse salariale globale complète. Les libellés de régimes,CNSS et comptes de recette sont fictifs et non déclarables.

**Base PostgreSQL utilisateur jamais contactée ;migrations105–110 non installées sur la cible pendant la session.** Tous les essais destructifs restent sur PostgreSQL natif éphémère vérifié par nonce. La recette humaine,l’installation cible,l’exploitation et la conformité réglementaire ne sont pas validées automatiquement.

## Prochaine reprise

Les étapes879,881 et883 sont livrées et qualifiées dans leur périmètre ;ne pas les réappliquer. Le Lot1 intégral reste **partiel** uniquement pour la collecte sécurisée RIB/pièces et le cadrageD05(clés,rotation,sauvegarde/restauration,conservation). Ce blocage et une proposition technique concrète figurent dans le guide ;aucune clé ni durée n’a été inventée.

Après arrêt de ce cadrage,implémenter la collecte chiffrée,son approbation indépendante et sa restauration isolée,puis clore la recette du Lot1 avant le Lot2. La paie complète demeure un ensemble de lots séparés. Aucun nouveau «go» n’est nécessaire pour les étapes techniques déjà autorisées ;les approbations métier de l’application sont conservées.
