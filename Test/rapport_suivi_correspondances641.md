# Lot641 — suivi regroupé des correspondances

Paramètres → Sociétés liées → Factures de la liaison : liste paginée10pièces,
les plus récentes en premier, avec les exercices et états de validation/
comptabilisation propres aux deux sociétés. TTC, reste, encaissements/paiements,
portefeuille en cours, avoirs, acomptes, RAS imputée et crédit tiers proviennent
du calcul de situation existant. Aucun paiement ou écriture répliqué.

Lecture READ ONLY / REPEATABLE READ initialisée avant l'authentification, même
Session et unique connexion. Les droits sont contrôlés dans les deux sociétés.
Historique retiré conservé ; tiers étranger refusé sans fuite. Montants inconnus,
non finis ou sous-centimes non assimilés àzéro. Arrondi commun money réutilisé ;
le bruit binaire minime des sommes de centimes est toléré, pas un vrai sous-centime.

« Solde couvert » ne prouve pas un encaissement : chèque600 en portefeuille,
reste0 mais encaissé0 et en cours600. Une annulation est signalée et son reste
calculé n'est pas présenté comme une dette active. Les brouillons restent
identifiés. Lecture courante, distincte d'une archive fiscale.

Actualisation sansF5, contexte société/jeton et réponses tardives protégés.
Le retrait effectué dans la même page invalide l'ancien suivi. Calendrier
acheteur explicitement rappelé dans le détail ; le sélecteur global reçoit le
nom accessible distinct « Exercice comptable », sans conflit avec GestionExercices.
Troisième parcours mobile : vente2026 et achat2027 daté2026, exercice sélectionné
réellement avant validation/comptabilisation dans le Journal de l'acheteur.

29regroupes passes152.412s ;15precision/suivi/oracle/docs passes68.734s ;4Edge calendrier finaux passes45.709s dont achat2027date2026 ;restore80tables1passe63.934s, vue regroupee identique. BuildVite5.22s, Python compile. Zero echec/erreur/ignore final ; suites recouvrantes non additionnees.
Les suites se recouvrent et ne sont pas additionnées comme des cas uniques.
La vue regroupée est également confrontée à l'oracle639 (600réglés et0restant
dans chaque société) et à la restauration native80tables, suivis identiques
après retrait. Ancienne preuve635 conservée séparément et restaurée.

Mise au point : le premier cas inconnu utilisait un frais facultatifNULL,
légitimement traité àzéro par le moteur existant. Le prixNULL tenté ensuite a
été refusé par NOTNULL, sans suppression de contrainte. Le cas effectif utilise
un prixInfinity dans un brouillon fictif ; la pièce d'origine n'est pas modifiée
et le lecteur affiche une situation indéterminée. Un essai calendrier a ciblé
le mauvais libellé du banc avant correction du nom accessible global.

Le test sous-centime a révélé que l'API individuelle actuelle admettait0,005MAD
sans comptabiliser, contrairement àla ventilation par tiers déjà stricte. Ce
cas est signalé sans arrondi silencieux par le suivi ; correction àla source
prévue dans le lot642, sans réécriture des données historiques.

Commandes exécutées avec PYTHON_DOTENV_DISABLED=1 :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_suivi_correspondances641_isole.py Test/test_societes_liees633_isole.py Test/test_e2e_factures_liees635_isole.py Test/test_oracle_societes639_isole.py Test/test_annexe_societes639.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_suivi_correspondances641_isole.py Test/test_annexe_societes639.py Test/test_oracle_societes639_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_factures_liees635_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_restauration_factures_liees635_isole.py -q -x
npm run build
```

Guide et casGRP-015 du cahier20cas actualisés sans remplir de résultat humain.
Aucun nouveau SQL ni ancienne migration modifiée. Installation101/102,
recette utilisateur et production non validées ; RH/paie et point6 différés.
