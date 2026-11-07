# Lot503 — Reprise d'immobilisations à l'ouverture réelle

Défaut reproduit sur PostgreSQL temporaire : l'assistant cherchait le cumul
théorique à la fin de l'exercice N−1. Sans exercice N−1, il proposait zéro.
Avec un exercice N−1 non contigu, il proposait un cumul arrêté trop tôt.
Cela sous-évaluait les amortissements repris et empêchait le rapprochement.

L'extension jusqu'à la clôture a révélé deux défauts liés : le rapprochement
du livre d'inventaire additionnait les annuités civiles jusqu'à décembre au lieu
de s'arrêter à la date réelle de clôture ; puis la clôture acceptait un exercice
suivant déjà créé dont les dates laissaient un trou de six mois.

La correction réutilise le calcul partagé de la période courante : cumul
d'ouverture = cumul de clôture − dotation de la période. Les méthodes, taux,
proratas et règles fiscales restent inchangés. La présence d'un exercice
antérieur dans le logiciel n'est plus nécessaire au calcul de cette suggestion.
Le rapprochement utilise désormais `situation_a_date` à la date de fin fournie.
La clôture refuse409 si l'exercice suivant ne débute pas le lendemain de cette
fin, avec un message demandant de vérifier les paramètres. Elle ne déplace
aucune date ni pièce existante. La recette corrige explicitement les dates d'un
exercice suivant vide par l'API administrateur, puis relance la clôture.

La reprise reste une décision explicite : choix « reprise antérieure », compte
de contrepartie fourni par l'administrateur, puis contrôle et validation du
brouillon dans le Journal. Le plan théorique ne prouve pas les amortissements
réellement pratiqués avant la migration ; les justificatifs restent nécessaires.
Aucune donnée réelle ni écriture définitive n'est réparée automatiquement.

## Oracles indépendants du code corrigé

Bien fictif10000MAD, linéaire5ans, mise en service au01/01/N−2.

| Exercice N | N−1 présent | Amortissement à l'ouverture | Dotation N | Cumul clôture |
|---|---|---:|---:|---:|
| Janvier–décembre | absent |4000|2000|6000|
| Janvier–décembre | complet |4000|2000|6000|
| Juillet N−1–juin N | absent |3000|2000|5000|
| Avril–décembre | absent |4500|1500|6000|
| Janvier–décembre | arrêté à mars N−1 |4000|2000|6000|

La lecture du diagnostic ne crée aucune pièce. La reprise comptabilise le brut
10000 au débit2355, le cumul d'ouverture au crédit28355 et le solde au crédit4481,
compte explicitement choisi pour ce laboratoire. Aucune TVA ni charge N dans
cette pièce d'ouverture. La dotation N est distincte et validée séparément.

La recette vérifie aussi le refus d'une seconde reprise, le rapprochement à zéro,
les sources définitives intactes, la clôture, le FEC et les soldes/dates des
à-nouveaux. La CM3000 existante du laboratoire n'est pas neutralisée ; elle ne
constitue pas une qualification de la situation fiscale d'une entreprise réelle.

## Exécutions

- Reprise de session :5tests501 réussis,29avertissements,34,30s.
- Avant correction :4échecs/1réussite,29avertissements,34,41s.
- Après correction, cinq cas avant extension clôture :5réussites,
  29avertissements,32,38s.
- Extension avant correction du rapprochement :24réussites/1échec,
  29avertissements,34,17s ;5000 comptabilisés comparés à6000 attendus à tort.
- Première commande corrigée : non exécutée, code4, nom de fichier de test
  inexistant. Relancée avec le fichier réel `test_patch05_livre_inventaire.py`.
- Après correction du rapprochement :27réussites/1échec,
  29avertissements,35,50s ;à-nouveaux au01/01 au lieu du01/07.
- Module étendu :28réussites,29avertissements,34.34s, code0. Aucun échec/erreur/ignoré. Quatre fichiers Python compilés.

Commande module : `Test/run_unit_tests.py Test/test_reprise_ouverture_immobilisations_isole.py Test/test_patch05c_reconciliation_historique.py Test/test_patch05d1_reconciliation_amortissements.py Test/test_patch03_immobilisations.py Test/test_immobilisations_fin_plan.py Test/test_patch05_livre_inventaire.py -ra`.

## Installation et limites

Installer ensemble les deux services et le routeur livrés, puis redémarrer l'API. Aucune nouvelle
migration. Ne pas rejouer une reprise déjà validée dans une base existante :
une éventuelle correction historique exige une analyse et une piste d'audit.

Tests HTTP et PostgreSQL isolé ; interface inchangée. Recette visuelle de
l'assistant et validation des justificatifs à effectuer chez l'utilisateur.
Les historiques partiellement comptabilisés sont le prochain lot distinct.
