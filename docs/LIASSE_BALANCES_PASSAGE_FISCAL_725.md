# MODE D’EMPLOI ET RECETTE — PASSAGE FISCAL DOCUMENTAIRE

Version 1 du 22 octobre 2026. B12 interne sur balance externe N, taux déclaré.

## Accès et portée

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation conservée → Préparer le passage fiscal B12 depuis
la balance. B12-N est un identifiant interne, sans assimilation à un formulaire
DGI officiel. La préparation reste distincte du Journal et de la fiscalité de
la société active. Aucune écriture ou liquidation n’est créée.

Le résultat net et les impôts comptabilisés67 restent séparés. Leur addition
reconstitue le résultat avant impôts dans le périmètre du moteur existant.
Les autres réintégrations excluent ces67 déjà repris. Déductions, déficit
éligible disponible et taux sont explicitement déclarés. Une case vide reste
inconnue. Ni un secteur, ni un régime, ni un avantage ne sont devinés.

Le déficit saisi doit provenir d’un état fiscal justifié dont les millésimes,
la nature, l’éligibilité et les imputations antérieures ont été revus. La
proposition arithmétique affichée ne confirme pas cette qualification juridique.
Le taux fictif20 du scénario sert uniquement à vérifier le calcul.

## Prérequis et données exactes

Utiliser uniquement une société fictive séparée en MAD, exercice2026, avec
administrateur, comptable et lecteur. Ajouter un logo fictif aux paramètres.
Le lot725 utilise les migrations existantes ; aucune migration nouvelle.
Redémarrer le backend et reconstruire le frontend après installation.

Importer BALANCE_FICTIVE_PASSAGE725_N.csv dans docs/recette. N-1 est facultatif
et n’intervient pas dans ce passage fiscal N. Vérifier les comptes existants
1111,5141,7111,6132,7581,6701 avant import.

Balance N :1111 crédit10000 ;5141 débit16400 ;7111 crédit10000 ;6132 débit3000 ;
7581 crédit1000 ;6701 débit1600. Débit=crédit=21000MAD. Net=10000−3000+1000−1600
=6400MAD. Résultat avant impôts=6400+1600=8000MAD.

Saisir une synthèse B12-N : déclaration Saisie documentée — à revoir ;
justification Synthèse fictive725, hypothèses explicitement justifiées ;
désignation Passage fiscal fictif N ; autres réintégrations hors67=500 ;
déductions=200 ; déficit disponible déclaré et justifié=1000 ; taux IS déclaré=20 ;
régime et avantages=Régime à revoir, aucun avantage déduit ; référence source=
NOTE FICTIVE725, déficit éligible explicitement déclaré.

Calcul indépendant : total des réintégrations depuis le net=1600+500=2100 ;
résultat fiscal avant déficits=6400+2100−200=8300 ; déficit proposé=min(1000,8300)
=1000 ; disponible restant=0 ; bénéfice proposé=7300 ; IS théorique selon taux
déclaré=7300×20/100=1460MAD. Il ne faut pas ajouter de nouveau1600 à8300.

Variante taux19,999 :7300×19,999/100=1459,927, arrondi au centime1459,93MAD.
L’arrondi indépendant est calculé au centime, moitié supérieure. CM, CSS,
crédits, acomptes et solde final restent Indisponibles dans ce lot ;1460 n’est
pas le montant à payer. Ces éléments nécessitent un contexte fiscal distinct.

## Utilisation et vérifications pas à pas

1. Importer le CSV N, contrôler les totaux et conserver. Noter la version et l’empreinte source.
2. Ouvrir B12, choisir la déclaration documentée et saisir la justification exacte ci-dessus.
3. Ajouter une ligne et saisir tous les champs. Une seule synthèse est autorisée. Le bouton Ajouter une ligne devient indisponible.
4. Cocher la confirmation puis Conserver les tableaux ETIC dans une nouvelle version. La nouvelle version est sélectionnée sans F5 ; réouvrir B12.
5. Contrôler6400,1600,8000,500,2100,200,8300,1000,0,7300 et1460. Vérifier le taux20,000%. Le solde final reste indisponible.
6. Modifier le taux en19,999 sans conserver : le contrôle figé reste1460. Après conservation, il devient1459,93. Relire l’ancienne version :1460 doit rester inchangé.
7. Vider le déficit puis conserver une nouvelle version : résultat avant déficits8300 connu, imputation/bénéfice/IS indisponibles. Remettre1000 et vider le taux : bénéfice7300 connu, IS indisponible.
8. Télécharger le dossier ZIP : passage_fiscal_documentaire.json, préparation PDF/Excel, manifeste SHA256. Vérifier le logo, les sources67, les hypothèses et les valeurs inconnues.
9. Comparer le Journal avant/après : aucune écriture générée ou modifiée. Les anciennes versions et les autres compléments documentaires restent conservés.

## Scénarios négatifs et droits

NaN, Infinity, taux supérieur100, taux négatif, plus de trois décimales,
montant négatif, montant avec plus de deux décimales, nature ou référence
vide : conservation refusée sans création de version. Le brouillon doit
rester disponible pour correction. Une référence commençant par le signe=
est exportée comme texte Excel et ne doit pas devenir une formule.

Lecteur : consultation et exports autorisés, saisie désactivée, conservation
interdite. Autre société : préparation invisible. Empreinte source incohérente :
conflit explicite. Double clic/rejeu strictement identique : même version,
pas de duplication. Clé réutilisée avec un taux différent : conflit.

Une balance dont les classes6/7 sont soldées vers119 n’est pas une source de
résultat fiscal annuel exploitable : fournir la balance avant clôture
technique. Un tableau sans hypothèse peut rester À compléter, sans inventer0.
Une note B12 Non applicable avec synthèse déclarée affiche une contradiction.
Un tableau déclaré néant ne transforme jamais les champs inconnus en zéros.

## Cahier de recette humain

Chaque ligne reste Non testé jusqu’à exécution par une personne sur son
installation de recette. Les tests automatisés locaux sont décrits dans le
rapport725 et ne valent ni recette humaine, ni validation réglementaire.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|F725-01|Créer la société fictive MAD2026 et importer le CSV N équilibré21000.|Capture des totaux, du net6400 et de la version source ; aucun Journal créé.|Non testé|
|F725-02|Saisir RI500, déductions200, déficit1000, taux20, désignation et référence exactes puis conserver.|Capture8300,7300,1460 et version nouvelle ;67=1600 distinct, solde final indisponible.|Non testé|
|F725-03|Taux19,999 en brouillon puis nouvelle version ; vider déficit, puis vider taux dans deux versions distinctes.|Brouillon1460 inchangé ; nouvelle version1459,93 ; inconnus préservés selon les étapes7.|Non testé|
|F725-04|Essayer NaN, Infinity, taux100,001, montant négatif et référence vide ; lecteur et autre société.|Refus sans version créée ; brouillon conservé ; droits403 et cloisonnement404.|Non testé|
|F725-05|Télécharger PDF/Excel/ZIP avec logo fictif ; référence =SOURCE_FICTIVE725.|Logo visible, JSON figé, hypothèses et inconnus identiques, référence Excel texte, manifeste vérifié.|Non testé|
|F725-06|Relire les anciennes versions et les autres compléments, comparer Journal et solde après conservation.|Aucune écriture ou liquidation modifiée ; anciennes valeurs stables ; preuve avant/après.|Non testé|

## Limites et suite

Ce lot ne gère pas encore le rapprochement B14 et ne confirme aucune imputation
fiscale réelle. Le taux et le déficit doivent être justifiés hors de ce jeu
fictif. Les sources officielles complètes du millésime restent à vérifier pour
toute nouvelle règle juridique : aucune n’a été introduite dans ce lot.
La numérotation est interne. Le dossier n’est pas prêt à déposer ; XML/EDI
reste conditionné au schéma officiel. RH/paie et recette humaine restent différés.
