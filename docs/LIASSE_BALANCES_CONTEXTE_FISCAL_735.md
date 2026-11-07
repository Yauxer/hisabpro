# MODE D’EMPLOI ET RECETTE — CONTEXTE FISCAL EXTERNE

Version 1 du 22 octobre 2026. Complément documentaire, sans nouvelle règle fiscale.

## Accès et portée

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation → Documenter CM, CSS, crédits et acomptes.
Les quatre rubriques CF-CM, CF-CSS, CF-CREDITS et CF-ACOMPTES sont internes.
Elles ne constituent pas des codes ou formulaires officiels de la DGI.

Ce complément conserve les montants et leurs justificatifs sans lire le Journal
ni le module fiscal actif. Il ne calcule aucun taux, exonération, impôt dû,
ordre d’imputation ou solde final. La CSS reste séparée. Un montant saisi n’est
pas un paiement confirmé ni la reconnaissance de son éligibilité fiscale.
Les totaux portent sur les seules lignes saisies, dont l’exhaustivité reste
à vérifier. Aucune écriture comptable n’est générée.

## Prérequis et données exactes

Utiliser une société fictive MAD, exercice 2026, un administrateur ou comptable,
un lecteur pour les contrôles de droits et un logo fictif intégré. Ne pas
effectuer cette recette sur une société réelle. Redémarrer le backend et
reconstruire le frontend ; aucune migration nouvelle pour ce complément.

Importer BALANCE_FICTIVE_CONTEXTE735_N.csv en N puis conserver la préparation.
Les six comptes sont : 1111 crédit 10000 ; 5141 débit 16400 ; 7111 crédit
10000 ; 6132 débit 3000 ; 7581 crédit 1000 ; 6701 débit 1600. Débit = crédit
= 21000 MAD. Résultat net 6400 ; impôts comptabilisés 1600 ; avant impôts 8000.
N-1 peut rester absent : il ne sera pas inventé.

Dans le complément B12, saisir désignation Passage fiscal fictif N ; autres
réintégrations hors67 500 ; déductions 200 ; déficit disponible explicitement
justifié 1000 ; taux déclaré 20 ; régime Régime à revoir, aucun avantage déduit ;
référence NOTE FICTIVE725, déficit éligible explicitement déclaré. Déclaration
Saisie documentée — à revoir et justification Hypothèses fictives735 à revoir.
Conserver : base avant déficit 8300 ; bénéfice proposé 7300 ; IS théorique 1460.
Le taux et le déficit sont des hypothèses de laboratoire, pas une qualification
juridique pour une société réelle.

Dans le contexte fiscal, choisir pour chaque rubrique Saisie documentée — à
revoir et justification Déclaration fictive735, à revoir. Ajouter les lignes
suivantes. Les montants sont tous en MAD, positifs ou nuls, deux décimales maximum.

| Rubrique | Désignation et référence | Montants exacts |
|---|---|---|
| CF-CM | CM fictive sans qualification automatique ; NOTE-CM735 | CM déclarée 3000 |
| CF-CSS | CSS fictive explicitement nulle ; NOTE-CSS735 | CSS déclarée 0 |
| CF-CREDITS | Crédit A fictif ; CERT-A735 | Total 300 ; déjà imputé 100 |
| CF-CREDITS | Crédit B fictif ; CERT-B735 | Total 200 ; déjà imputé 50 |
| CF-CREDITS | Crédit C fictif ; CERT-C735 | Total 100 ; déjà imputé 0 |
| CF-ACOMPTES | Acompte fictif ; QUITTANCE735 | Effectivement versé 1000 ; crédit antérieur imputé 100 ; crédits/ retenues déjà imputés 150 |

Ces justificatifs sont fictifs. Les montants CM/CSS sont déclarés, jamais
calculés depuis la balance. Une référence libre sert à identifier une preuve ;
elle ne valide pas à elle seule le droit fiscal. Joindre les pièces de recette
à la version appropriée si nécessaire, avec le module de justificatifs existant.

## Utilisation et résultats attendus

1. Choisir CF-CM, ajouter la ligne et saisir les données exactes. Une seule ligne est admise. Passer à CF-CSS et saisir explicitement 0 avec sa référence.
2. Choisir CF-CREDITS et ajouter les trois certificats. Total et part déjà imputée restent deux montants distincts. Limite technique : 50 lignes ; un couple désignation/référence identique est refusé dans la rubrique.
3. Choisir CF-ACOMPTES et ajouter la quittance. Saisir 1000 comme versement effectif ; 100 et 150 dans leurs colonnes d’imputation respectives. Ne pas inscrire 1250 comme versement bancaire. Limite technique : 20 lignes.
4. Cocher la confirmation, puis Conserver le contexte fiscal dans une nouvelle version. Réouvrir : les quatre rubriques et leurs sources sont conservées ensemble. L’ancienne version reste lisible ; aucune touche F5 n’est nécessaire.
5. Vérifier les contrôles conservés : CM 3000 ; CSS 0 ; crédits totaux 600 ; déjà imputés côté crédits 150 ; crédits moins part déjà imputée 450 ; acomptes versés 1000 ; crédits antérieurs imputés 100 ; déjà imputés côté acomptes 150 ; écart d’imputation 0. L’IS B12 pour mémoire est 1460.
6. Vérifier séparément les oracles : 300+200+100=600 ; 100+50+0=150 ; 600−150=450 ; 150−150=0. Les deux valeurs 150 documentent les mêmes imputations, elles ne deviennent pas deux nouveaux crédits. Aucun total de paiement ou solde fiscal n’est déduit de ces sommes.
7. Modifier CM en 9999 sans conserver : le contrôle reste 3000. Relire les tableaux conservés pour abandonner ce brouillon. Vider CM puis conserver : CM devient Indisponible, pas 0. Ressaisir explicitement 3000 et conserver pour rétablir le jeu de départ.
8. Modifier les crédits déjà imputés côté acomptes en 149,99 et conserver : écart −0,01, alerte visible, sources intactes. Restaurer explicitement 150 par une nouvelle version. Aucun écart n’est corrigé automatiquement.
9. Modifier le taux B12 en 10 et conserver B12 : IS théorique B12 courant 730, mais le contexte garde son ancien 1460 pour mémoire. Un message indique le changement de B12. Relire les justificatifs et conserver le contexte pour actualiser sa référence à 730. Les anciennes versions et valeurs restent inchangées.
10. Télécharger le dossier de préparation ZIP. Comparer contexte_fiscal_documentaire.json, les feuilles Excel CF-CM/CF-CSS/CF-CREDITS/CF-ACOMPTES, Totaux contexte fiscal et Origine contexte fiscal avec le PDF. Vérifier montants, inconnus, sources, logo et manifeste SHA-256.

## Cas négatifs et droits

Une case vide reste inconnue. Une liste vide, même déclarée Néant avec une
justification, ne remplit pas les montants par 0. Un total est indisponible si
au moins une ligne de son champ est inconnue. Les autres totaux certains
restent visibles. La différence crédits moins part déjà imputée ne confirme
pas leur disponibilité juridique pour une liquidation.

Tester NaN, Infinity, −1 et 0,001 : refus sans nouvelle version, brouillon
corrigeable. Le montant déjà imputé 301 pour un crédit total 300 est refusé.
Une désignation ou référence vide est refusée, même pour une ligne partielle.
Une référence commençant par = reste du texte dans Excel. Un doublon exact,
une seconde ligne CM/CSS ou un dépassement des limites est refusé côté serveur.

Le lecteur peut consulter les données et exporter ; il ne peut pas conserver.
Une autre société ne voit pas la préparation. Une empreinte parent incohérente
ou une clé de conservation réutilisée pour d’autres données provoque un conflit.
Une réponse tardive ne doit pas remplacer une autre version sélectionnée.

## Cahier de recette humain

Ces statuts sont distincts des tests automatisés. Les colonnes Résultat réel,
Anomalies et Preuves réelles du classeur restent vierges avant recette humaine.
Prérequis communs : société fictive et jeu ci-dessus. Écritures attendues pour
chaque cas : aucune. Impact fiscal : documentaire uniquement ; aucun impôt,
paiement ou dépôt confirmé. Les sources applicables restent à qualifier.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|CF735-01|Importer le CSV N et conserver B12 avec RI500, déductions200, déficit1000, taux20.|D=C21000, net6400, avant8000, bénéfice7300, IS théorique1460 ; capture préparation/B12.|Non testé|
|CF735-02|Saisir CF-CM3000 et CF-CSS0 avec les désignations et références ci-dessus.|CM3000, CSS0 distincts, aucun impôt dû ou solde ; capture contrôles.|Non testé|
|CF735-03|Saisir les trois crédits 300/100,200/50,100/0, puis l’acompte1000/100/150 ; conserver.|Crédits600, déjà imputés150, restants450, écart0 ; références présentes, aucune écriture.|Non testé|
|CF735-04|CM9999 en brouillon puis Relire ; vider CM et conserver ; rétablir3000 explicitement.|Contrôle3000 avant conservation ; vide=Indisponible ; anciennes versions intactes.|Non testé|
|CF735-05|Déjà imputés côté acomptes149,99 puis150, avec conservation à chaque fois.|Écart−0,01 et alerte, puis écart0 ; aucune correction automatique des justificatifs.|Non testé|
|CF735-06|Passer B12 au taux10 puis conserver le contexte après revue des justificatifs.|Contexte garde1460 avec alerte avant actualisation ; ensuite730 ; anciennes versions inchangées.|Non testé|
|CF735-07|Tester NaN,0,001, crédit300/déjà imputé301, doublon, référence vide, lecteur et autre société.|Refus sans mutation ; brouillon conservé ; lecteur sans commande de conservation ; autre société sans accès.|Non testé|
|CF735-08|Exporter PDF/Excel/ZIP avec logo et référence =CERT-FICTIF735 ; comparer au contrôle et au Journal.|Valeurs/sources identiques, inconnus préservés, logo présent, référence Excel texte, SHA vérifiés, Journal intact.|Non testé|

## Limites et prochaine étape

Le contexte fiscal devient utilisable pour rassembler les justificatifs. La
liquidation externe complète demeure partielle : obtenir les textes officiels
applicables et qualifier CM, CSS, crédits et acomptes avant d’étendre les calculs.
L’ouverture du CGI 2026 officiel a échoué pendant cette étape ; un extrait de
recherche ou un texte ancien ne prouve pas le régime complet applicable.
EDI attend également son schéma officiel. Recette utilisateur et installation
cible à effectuer ; production non validée. RH/paie et point6 humain différés.
