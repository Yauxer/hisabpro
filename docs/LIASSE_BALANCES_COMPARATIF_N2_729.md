# MODE D’EMPLOI ET RECETTE — COMPARATIF C3 N-2 EXPLICITE

Version 1 du 22 octobre 2026. Source N-2 rattachée, sans reprise du Journal.

## Accès et portée

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation de2026 → Rattacher une source N-2 aux indicateurs C3.
Le formulaire propose uniquement des préparations conservées de2024 de la même
société. L’exercice est celui de clôture, N-2 signifie ici2026−2=2024.

La source est choisie explicitement avec sa référence. Sa balance N, ses états
déjà conservés, son exercice, son identifiant, sa version et son empreinte sont
copiés dans un nouveau snapshot. Ni le Journal, ni les salariés ne sont lus.
Les pièces jointes restent attachées à la préparation d’origine ; elles ne sont
pas transférées automatiquement. Consulter leur origine pour les justificatifs.

Le rattachement ne recalcule pas un contrôle C3 déjà conservé. Un message demande
une nouvelle conservation des indicateurs C3 pour inclure N-2. Les versions
précédentes restent immuables, même après création d’une autre préparation source.
Les données extra-comptables restent à documenter ; aucun C3 complet ou dossier
prêt à déposer n’est revendiqué.

## Prérequis et jeu exact

Utiliser une société fictive isolée en MAD, des utilisateurs administrateur,
comptable et lecteur, et un logo fictif. Créer explicitement les exercices
calendaires2024,2025 et2026 dans l’administration si absents. Aucun Journal
ne sera alimenté par les imports. Vérifier les comptes du plan1111,5141,7111,
6132,2111,28111,7581,6701,6171 et1191 avant import.

Le lot729 utilise les migrations existantes sans nouveau SQL. Redémarrer le
backend et reconstruire le frontend après installation. Les quatre CSV fournis
sont des données fictives, jamais à importer dans un dossier comptable réel.

Exercice2024 : importer BALANCE_FICTIVE_COMPARATIF729_N2.csv comme Balance N,
sans N-1. Lignes :1111 crédit10000 ;5141 débit11000 ;7111 crédit2000 ;6132
débit1000. Débit=crédit=12000MAD ; résultat=2000−1000=1000 ; situation nette=
capital10000+résultat1000=11000. Aucun impôt ou non-valeur dans ce jeu.
Conserver ; noter l’identifiant, la version et l’empreinte de cette source2024.

Exercice2026 : importer BALANCE_FICTIVE_COMPARATIF729_N.csv en N et
BALANCE_FICTIVE_COMPARATIF729_N1.csv en N-1. Ce sont les chiffres du jeu723,
recopiés sous des noms propres à729 sans modifier les anciens fichiers.

N :1111 crédit10000 ;2111 débit2000 ;28111 crédit500 ;5141 débit14500 ;
7111 crédit10000 ;6132 débit3000 ;7581 crédit1000 ;6701 débit1600 ;6171 débit400.
Débit=crédit=21500. Net=10000−3000−400+1000−1600=6000 ; situation nette=
10000+6000−2000+500=14500 ; avant impôts7600 ; CA10000 ; rémunérations6171=400.

N-1 :1111 crédit10000 ;2111 débit1000 ;28111 crédit200 ;5141 débit12200 ;
7111 crédit5000 ;6132 débit2000. Débit=crédit=15200 ; net3000 ; situation12200.
Chaque côté non mouvementé des comptes présents vaut explicitement0.

## Utilisation et contrôles

1. En2024, importer puis conserver la préparation N-2 ci-dessus. Elle doit apparaître dans la liste2024 ; noter sa version et son empreinte, sans inventer un identifiant.
2. Revenir à2026, importer N/N-1 puis conserver. Ouvrir Consulter les indicateurs comptables C3 depuis les balances et conserver une version initiale. Sélectionner N-2 : source non fournie, montants inconnus.
3. Ouvrir Rattacher une source N-2 aux indicateurs C3. Choisir la préparation2024 exacte, saisir la référence BALANCE FICTIVE729 N-2 explicitement choisie et cocher la confirmation.
4. Cliquer Rattacher N-2 dans une nouvelle version. La nouvelle version doit être sélectionnée sans F5. Réouvrir le rattachement :4 comptes, débit/crédit12000, exercice2024, version/empreinte/référence visibles.
5. Le message d’actualisation C3 apparaît. Ouvrir C3, choisir N-2 : l’ancien contrôle reste inconnu. Cocher puis Conserver les indicateurs C3 dans une nouvelle version. Réouvrir C3 et choisir N-2.
6. Vérifier situation11000, CA2000, avant impôts1000, impôts0, net1000, rémunérations comptabilisées0. Les références bilan/CPC permettent un écart0 quand elles sont présentes ; effectif et distributions restent inconnus.
7. Comparer N14500/net6000 et N-1 à12200/net3000 : ils n’ont pas changé. Le message demandant d’inclure N-2 disparaît. Relire les anciennes versions : elles restent sans N-2.
8. Modifier la référence en brouillon sans enregistrer : la référence conservée reste inchangée. Relire annule le brouillon. Un autre snapshot2024 ne modifie pas une source déjà rattachée.
9. Télécharger le dossier ZIP : balance_N2.csv, comparatif_n2_documentaire.json, C3 documentaire JSON et PDF/Excel. Vérifier source, références, logo et manifeste SHA256. Aucun Journal ni document joint déplacé.

## Variante après solde119 et scénarios négatifs

En2024, créer une autre préparation avec BALANCE_FICTIVE_COMPARATIF729_TECHNIQUE.csv :
1111 crédit10000 ;5141 débit11000 ;1191 crédit1000. Débit=crédit=11000.
La situation nette reste11000 ; les classes6/7 soldées ne donnent pas le CA
ou le résultat d’activité annuel. Rattacher cette version puis conserver C3 :
activité inconnue, jamais0 fabriqué ; message demandant une balance avant solde.
L’ancienne source normale reste disponible dans son ancienne version.

Sans préparation2024, le formulaire explique l’import préalable. Référence vide
ou constituée d’espaces : conservation impossible. Source d’une autre société :
invisible/refusée. Source2025 pour dossier2026 : refus, même si elle est équilibrée.
Empreinte source ou parent incohérente : conflit ; aucun snapshot nouveau.

Import N-2 déséquilibré, compte doublon, NaN, infini, montant négatif ou surprécis :
refus par les contrôles d’import existants. Un résultat119 mélangé aux classes6/7
est refusé comme à l’import normal. Ne jamais corriger une écriture pour masquer
ces contrôles. Une référence commençant par= reste texte dans Excel.

Lecteur : consultation et exports autorisés, aucun rattachement. Comptable :
rattachement permis dans sa société. Rejeu identique : même version ; même clé
avec référence différente : conflit. Aucun format officiel EDI n’est généré.

## Cahier de recette humain

Les cas ci-dessous restent Non testé jusqu’à exécution par une personne sur une
installation de recette. Les tests locaux ne valident ni recette humaine ni
conformité réglementaire. Conserver captures et exports comme preuves.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|N729-01|Créer exercices fictifs2024/2025/2026 ; importer CSV N2 en2024, N/N1 en2026.|Captures totaux12000/21500/15200, versions et empreintes ; aucune écriture créée.|Non testé|
|N729-02|Conserver C3 sans N2, rattacher source2024 avec référence exacte puis relire C3.|Rattachement4comptes/12000 ; contrôle C3 ancien inchangé, message d’actualisation visible.|Non testé|
|N729-03|Conserver une nouvelle version C3 puis sélectionner N-2.|Situation11000, CA2000, avant impôts/net1000, impôts0 ; N/N1 inchangés ; message disparu.|Non testé|
|N729-04|Essayer source2025, autre société, référence vide et empreinte incohérente ; profil lecteur.|Refus sans version nouvelle ; lecteur sans saisie, cloisonnement et conflits explicites.|Non testé|
|N729-05|Télécharger PDF/Excel/ZIP avec logo et référence =SOURCE_FICTIVE729.|Source N2 et trace figées, CSV12000 équilibré, référence Excel texte, logo et manifeste contrôlés.|Non testé|
|N729-06|Rattacher variante119 puis conserver C3 ; relire sources/versions anciennes et Journal.|Situation11000, activité inconnue ; ancien net1000 conservé ; aucune écriture/pièce déplacée.|Non testé|

## Limites et prochaine étape

C3 N-2 provient désormais d’une source explicitement rattachée. Effectif moyen,
distributions, affectations et données par titre nécessitent encore leurs
justificatifs ; aucun salarié ni bulletin n’est repris automatiquement.
La fiscalité externe complète reste partielle. XML/EDI attend le schéma officiel.
RH/paie, recette humaine, installation cible et production restent différés.
