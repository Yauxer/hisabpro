# Effets : échéance civile locale — lot 471

Un effet échéant aujourd'hui pouvait rester bloqué entre minuit local et minuit
UTC : JavaScript interprétait la chaîne `AAAA-MM-JJ` comme un instant à minuit UTC.
L'action compare maintenant deux dates civiles ISO, avec l'utilitaire local déjà
utilisé par les formulaires. La date de l'infobulle est également affichée sans
conversion de fuseau. Un effet échéant demain reste bloqué.

Le défaut a été reproduit deux fois dans la recette regroupée, puis isolée, après
minuit en Europe/Paris. **9 tests réussis en 119,33 s**, 29 avertissements, exit 0.
Le nouveau test Edge fixe le navigateur à 23 h 30 UTC la veille, en Europe/Paris,
sur 390 px : l'effet du jour est disponible, celui de demain reste indisponible
avec la bonne date affichée. Les huit parcours connexes contrôlent encaissement,
frais, impayé/remplacement, rapprochement, lettrage, FEC et clôture/à-nouveaux.

Commande : `python -X utf8 Test/run_unit_tests.py Test/test_e2e_effets_date_locale_isole.py Test/test_e2e_instruments_runtime_isole.py -ra`.
Build et compilation exécutés avant livraison. API réelle et PostgreSQL jetable
sous LOGIN limité ; aucun effet ni mouvement réel modifié. Aucun escompte
contractuel ou calcul fiscal ajouté. Autres fuseaux et recette humaine à vérifier.
