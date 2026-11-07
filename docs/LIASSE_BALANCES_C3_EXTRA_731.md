# MODE D’EMPLOI ET RECETTE — DÉCLARATIONS EXTRA-COMPTABLES C3

Version 1 du 22 octobre 2026. Sources déclarées N/N-1/N-2, sans module RH/paie.

## Accès et portée

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation → Documenter les données extra-comptables C3.
Une synthèse sourcée par période C3-N, C3-N1 et C3-N2 ; identifiants internes.

L’effectif moyen est déclaré en personnes, les bénéfices distribués en MAD et
les valeurs par titre en MAD/titre. La précision technique admise est de deux
décimales maximum, sans arrondi silencieux. Un effectif fractionnaire est admis,
sans plafond de100 assimilé à un pourcentage. Les montants non finis sont refusés.

Aucun effectif n’est déduit des salariés ou du6171 ; aucun montant par titre
n’est déduit du net, du capital ou d’un paiement. Les décisions, le nombre et
la nature des titres doivent être justifiés par leurs sources. Les valeurs par
titre sont saisies explicitement ; l’application ne vérifie pas une qualification
juridique ou sociale à partir d’un texte libre.

Une case vide reste inconnue, même si un bénéfice distribué est explicitement0.
Le résultat par titre peut être négatif ; effectif, bénéfices distribués et
distribution par titre sont positifs ou nuls. Aucun Journal, salarié, bulletin,
liquidation fiscale ou paiement n’est créé. RH/paie reste hors de cette étape.

## Prérequis et données exactes

Utiliser uniquement une société fictive MAD avec exercices2024/2025/2026,
administrateur, comptable, lecteur et logo fictif. Redémarrer le backend et
reconstruire le frontend ; aucune migration nouvelle. Préparer la source N-2
comme décrit dans le guide729, fourni dans le cumulatif de session.

Quatre CSV propres à731 sont fournis. En2024, importer
BALANCE_FICTIVE_EXTRA731_N2.csv comme N puis conserver. En2026, importer
BALANCE_FICTIVE_EXTRA731_N.csv et BALANCE_FICTIVE_EXTRA731_N1.csv en N/N-1.
Rattacher explicitement la préparation2024 et conserver les indicateurs C3.

N :capital1111 crédit10000 ; non-valeur2111 débit2000 ; amortissement28111
crédit500 ; banque5141 débit14500 ; ventes7111 crédit10000 ; charges6132
débit3000 ; produit7581 crédit1000 ; impôts6701 débit1600 ; rémunération6171
débit400. Débit=crédit=21500 ; net6000 ; situation14500.

N-1 :1111 crédit10000 ;2111 débit1000 ;28111 crédit200 ;5141 débit12200 ;
7111 crédit5000 ;6132 débit2000. Débit=crédit=15200 ; net3000 ; situation12200.
N-2 :1111 crédit10000 ;5141 débit11000 ;7111 crédit2000 ;6132 débit1000.
Débit=crédit=12000 ; net1000 ; situation11000.

Ces données et les effectifs ci-dessous sont des hypothèses de test documentaire,
pas un scénario de paie ni une validation sociale. Aucun rapprochement avec un
bulletin n’est supposé. La quantité fictive100 titres sert à l’oracle indépendant,
mais ne devient pas un champ obligatoire ni un nombre inféré du capital.

Saisir pour chaque tableau : déclaration Saisie documentée — à revoir ;
justification Déclarations fictives731, sources à revoir ; désignation
Synthèse fictive731 suivie du code C3-N, C3-N1 ou C3-N2 ; décisions/affectations
PV FICTIF731 suivi du code, cent titres ; décision et qualification à vérifier ;
référence NOTE EXTRA FICTIVE731 suivie du code.

Montants exacts : C3-N effectif3,50 ; bénéfices distribués2000 ; résultat par
titre60 ; distribution par titre20. C3-N1 effectif3 ; bénéfices1000 ; résultat
par titre30 ; distribution par titre10. C3-N2 effectif2 ; bénéfices0 ; résultat
par titre10 ; distribution par titre0.

Oracle indépendant :6000/100=60 et2000/100=20 ;3000/100=30 et1000/100=10 ;
1000/100=10 et0/100=0. Ces divisions vérifient le jeu fictif ; les valeurs
par titre restent déclarées dans l’application, jamais déduites automatiquement.

## Utilisation et vérifications

1. Préparer N/N-1/N-2 et conserver C3 avant toute déclaration : comptabilité connue, quatre champs extra-comptables indisponibles.
2. Ouvrir Documenter les données extra-comptables C3. Choisir C3-N, ajouter une ligne et saisir les valeurs, désignation, décisions et référence exactes ci-dessus.
3. Passer à C3-N1 puis C3-N2 et remplir leurs synthèses. Revenir à N : le brouillon doit rester intact ; une deuxième ligne de la même période est interdite.
4. Cocher la confirmation puis Conserver les tableaux ETIC dans une nouvelle version. Réouvrir : les déclarations conservées montrent3,50 personnes,2000MAD,60MAD/titre et20MAD/titre pour N. Un message demande d’actualiser C3.
5. Ouvrir les indicateurs C3 : l’ancien contrôle conserve ses inconnus. Cocher puis Conserver les indicateurs C3 dans une nouvelle version. Réouvrir et choisir N/N-1/N-2 : les valeurs déclarées apparaissent avec leurs unités et références ; les nets6000/3000/1000 restent inchangés.
6. Modifier l’effectif N en141,25 sans conserver : le contrôle reste3,50. Conserver les déclarations : seul le complément change, C3 reste3,50. Conserver C3 : il devient141,25 personnes. Revenir explicitement à3,50 par les deux conservations pour la suite du scénario ; les anciennes versions restent lisibles.
7. Effacer la distribution par titre N-2, laisser bénéfices distribués0 puis conserver le complément et C3 : distribution par titre indisponible, jamais0 déduit. Ressaisir0 explicitement puis conserver les deux versions pour rétablir le jeu de départ.
8. Télécharger PDF/Excel/ZIP : extra_c3_documentaire.json, C3 documentaire JSON, sources et manifeste SHA256. Vérifier personnes/MAD/MAD par titre, références, logo et inconnus. Comparer le Journal et les salariés : aucune modification.

## Variante négative et absence de balance

Importer en2024 une nouvelle préparation avec BALANCE_FICTIVE_EXTRA731_PERTE.csv :
1111 crédit10000 ;5141 débit8999 ;6132 débit1001. Débit=crédit=10000 ;
net−1001 et situation8999. Rattacher cette source à2026. Dans les déclarations
C3-N2, saisir résultat par titre−10,01 et référence PERTE FICTIVE731 N2 :100 titres,
net−1001. Conserver le complément puis C3 : net−1001, situation8999 et résultat
par titre déclaré−10,01. Les valeurs N/N-1 et les anciennes versions ne changent pas.

Sans balance comparative, des déclarations sourcées de cette période peuvent
être conservées : elles restent explicitement déclaratives ; la situation,
le résultat comptable et les autres montants sans balance restent inconnus.
Une déclaration d’effectif ne fabrique jamais une comptabilité historique.

NaN, Infinity, booléen, montant surprécis, effectif/distribution négatifs,
référence ou désignation vide : refus sans nouvelle version. Le brouillon reste
corrigeable. Référence commençant par= : texte Excel, aucune formule exécutée.
Lecteur : consultation/exports seulement. Autre société : préparation invisible.
Empreinte incohérente ou clé réutilisée pour d’autres valeurs : conflit.
Néant déclaré ne remplit pas les cases vides par0 ; contradictions avec une
note C3 Non applicable restent visibles.

## Cahier de recette humain

Les réussites automatisées ne renseignent pas ces statuts humains. Exécuter
sur une société fictive de recette et conserver captures/exports comme preuves.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|X731-01|Importer N/N1/N2, rattacher2024 et conserver C3 sans déclarations.|Nets6000/3000/1000 et situations14500/12200/11000 ; extra-comptable indisponible.|Non testé|
|X731-02|Saisir les trois synthèses exactes et conserver complément puis C3.|Unités personnes/MAD/MAD par titre, valeurs3,50/2000/60/20 en N ; nets inchangés, références visibles.|Non testé|
|X731-03|Effectif141,25 en brouillon puis complément et C3 ; revenir3,50 avec les deux conservations.|Aucun plafond100 ; ancien contrôle inchangé avant actualisation, anciennes versions préservées.|Non testé|
|X731-04|Vider distribution par titre N2 alors que bénéfices0 ; tester NaN, précision0,001 et lecteur.|Inconnu non remplacé par0 ; refus sans mutation et brouillon conservé ; lecteur sans conservation.|Non testé|
|X731-05|Télécharger PDF/Excel/ZIP avec logo et référence =SOURCE_FICTIVE731.|Unités exactes, inconnus et références identiques, texte Excel sûr, manifeste et logo vérifiés.|Non testé|
|X731-06|Importer variante PERTE2024, rattacher, déclarer−10,01 et conserver C3 ; comparer données avant/après.|Net−1001/situation8999/valeur par titre−10,01 ; aucune écriture ou donnée RH modifiée.|Non testé|

## Limites et suite

Les déclarations ne confirment ni décision de distribution, ni nature des titres,
ni effectif légal ou conformité sociale. Même sans reliquat technique, C3 reste
à revoir sur justificatifs et n’est pas déclaré réglementairement complet.
La fiscalité externe complète et les schémas officiels EDI restent à poursuivre.
RH/paie, recette humaine, installation cible et production restent différés.
