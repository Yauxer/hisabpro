# Formulaire bancaire : date et hauteur des cartes — lot357

La globale354 est terminée avant ce changement :3126réussis,686sources
inchangées. Elle ne constitue pas une validation globale du lot357.

## Analyse et correction minimale

Le formulaire Saisie manuelle utilisait une date UTC. Surtout, l'effet
de contexte remplaçait systématiquement la date par le premier jour de
l'exercice, y compris après une saisie utilisateur. Le lot357 réutilise
`dateLocaleISO`, conserve la date saisie lorsqu'elle reste dans le même
exercice, et propose le jour local borné à l'exercice lors d'un changement
ou d'un contexte incompatible. La vraie date bancaire reste à saisir.
Les filtres de période et les règles backend restent inchangés.

Les clics ordinaires à390px ont ensuite révélé une compression verticale
des cartes : le résumé interceptait le bouton Ajouter. La correction
limitée au double tableau ne protégeait pas la carte des soldes après
import. La règle finale `flex-shrink:0` vise les enfants directs du
conteneur défilant et conserve leur hauteur naturelle.

Aucune écriture validée, migration ou donnée réelle n'est modifiée.

## Preuves conservées et résultats

Toutes les commandes utilisent le Python du venv backend, `-X utf8`,
`PYTHON_DOTENV_DISABLED=1` et `Test/run_unit_tests.py`, avec un préfixe
neuf pour chaque log, JUnit et code retour dans `.codex-tests` :

| Preuve | Résultat réel | Interprétation |
|---|---|---|
| banque357_avant |4échoués,25avertissements,56,29s,code1 | Date affichée01/01 àla place du jour local |
| banque357_final |37réussis,4échoués,25avertissements,110,39s,code1 | Changer uniquement UTC est insuffisant |
| banque357_contexte_avant |1réussi,3échoués,4désélectionnés,25avertissements,52,08s,code1 | Saisie03/17 remplacée et proposition exercice passé àfaire évoluer |
| banque357_corrigee |43réussis,2échoués,25avertissements,141,57s,code1 | Deux clics mobiles interceptés |
| banque357_livraison |44réussis,1échoué,25avertissements,131,87s,code1 | Carte des soldes comprimée après import |
| banque357_finale_v3 |45réussis,0échec/erreur/ignoré,25avertissements,112,18s,code0 |13cas Edge connectés et32cas connexes ; correction finale validée dans cet environnement |

Commande finale :

```text
Test/run_unit_tests.py Test/test_e2e_rapprochement_date_locale_isole.py
Test/test_e2e_rapprochement_dates_contexte_isole.py
Test/test_e2e_rapprochement_isole.py Test/test_rapprochement_bancaire_final.py
Test/test_rapprochement_integrite_archives.py
Test/test_patch083_soldes_rapprochement.py -vv --tb=short
--junitxml=.codex-tests/banque357_finale_v3.xml
```

Les huit nouveaux cas utilisent Edge et l'API réelle sur PostgreSQL
éphémère gardé par URL/répertoire/nonce :00h30Europe/Paris et23h30NewYork,
largeurs1365/390 ; deux saisies conservées àl'arrivée tardive de la vraie
réponse d'exercices ; deux changements vers exercices passé/futur.
Les horloges JavaScript seules sont fixées pour les quatre cas UTC.
Aucune réponse API n'est inventée. Pour les deux cas de contexte tardif,
seule la livraison d'une réponse réellement obtenue est retardée.

Les ajouts contrôlent le POST201, la date et40MAD persistés, l'apparition
sansF5, et la photographie inchangée des écritures/lignes déjà validées.
Les tests connexes couvrent import CSV, soldes, pointage, rechargement,
doublons, filtres et isolation entre sociétés, ainsi que l'intégrité
des archives. Les clics ne sont ni forcés ni remplacés par des appels API.

Le build final réel est réussi :`npm run build`,6,80s,code0. Les
avertissements de bundle et import statique/dynamique restent visibles.
Compilation Python du nouveau test :code0. Sources finales687, seules
trois différences depuis354 :composant, CSS et nouveau test. Le contrôle
final retrouve les687empreintes identiques au snapshot357v3.

## Limites et reprise

Les tests de fonctions pures restent distincts des preuves PostgreSQL.
PostgreSQL réel et recette humaine ne sont pas exécutés. La suite354
précède357 ; les suites ciblées ne s'additionnent pas aux3126tests.
Code/JUnit final et SHA réellement relus. Prochaine action :livrer357 puis guide358,
couverture355 et cumulatif356. La lecture des factures historiques aux
montants inconnus reste le chantier suivant.
