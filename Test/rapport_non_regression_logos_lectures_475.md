# Non-régression après les états de lecture 474

**140 réussis, zéro échec/erreur/ignoré, 29 avertissements, 394,09 s, code 0.**
Cette commande a réellement été exécutée après modification de l'accueil et du
Grand livre. Elle réunit les 136 cas de 469 et les quatre nouveaux parcours 474,
sans additionner à nouveau leurs suites ciblées recouvrantes.

```powershell
python -X utf8 Test/run_unit_tests.py Test/test_consolidation_logos_modeles_20261016.py Test/test_lecture_ecritures_invalides_isole.py Test/test_e2e_lectures_comptables_isole.py -ra
```

Les sources Python, SQL, JavaScript/JSX, styles, assets et configurations sont
empreintées avant et après par le banc local de session. Aucun fichier source
testé n'a changé pendant la commande. Les trois laboratoires sont distincts :
regroupement positif sous runtime 093, négatifs de lecture 470, scénarios 474.
Les brouillons NaN fictifs des négatifs ne sont pas inclus dans les contrôles
du jeu positif. API réelle, PostgreSQL nonce et Edge, aucun PostgreSQL utilisateur.

Le contrôle positif de 469 est de nouveau passé : zéro pièce déséquilibrée,
zéro montant non fini, zéro écriture définitive sans numéro/date ; ACL et les
134 empreintes internes inchangées. Il contient 58 sociétés fictives,
99 écritures, 249 lignes, deux clôtures, 26 lettrages, 64 modèles et 150 lignes de
modèle. La restauration native 092/093 est incluse dans les 140 cas. Les pannes
volontaires prévues par certains tests restent des scénarios explicitement
vérifiés, pas une affirmation d'absence de toute réponse 500.

Build 474 réussi en 7,39 s, compilation des tests modifiés réussie. Les
avertissements sont ceux de Pydantic/multipart et de taille du bundle. Les
limites de 472, notamment concurrence de clôture et écritures SQL directes des
paramètres TVA, ne sont pas déclarées levées par cette campagne. Le lot suivant
qualifie distinctement le verrou d'une ligne d'exercice existante. Les résultats
de cette campagne restent attachés aux sources avant ce prochain changement.

Migrations réelles, Excel du partenaire, impression système, autres navigateurs,
recette utilisateur et mise en production restent à vérifier. Point 6 en attente.
