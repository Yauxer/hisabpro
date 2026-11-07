# HisabPro — précision du cas de cession HP-IMM-004

La cession a été testée dans Edge, sur ordinateur et mobile (1440 et 390 pixels), avec PostgreSQL natif temporaire protégé par nonce. Les sociétés de test sont indépendantes du scénario principal et des données réelles.

Données à saisir : reprendre une société fictive avec IMMO-01 acquis 24 000 HT et payé 28 800 le 01/01/2025, amortissement 2025 de 4 800 validé. Dans Clôture, sélectionner 2026, puis Immobilisations → Cession / mise au rebut. Date de sortie 01/01/2026 ; prix 20 000 HT ; TVA 20 % ; cession encaissée immédiatement ; date d’encaissement 01/01/2026 ; compte 5141. Les deux dates sont à renseigner : elles ont chacune leur champ.

Une divergence du cahier a été constatée : il annonçait VNC 19 200 et gain 800 au01/01/2026. Le moteur existant applique une convention30/360 avec bornes inclusives. Le jour de sortie ajoute donc24000÷5÷360=13,33 de dotation 2026. Le cumul atteint4813,33 ; la VNC19186,67 ; le gain comptable813,33. Ce calcul indépendant explique le résultat réel. La convention de calcul du produit n’a pas été changée et n’est pas présentée ici comme une obligation réglementaire.

Quatre écritures sont générées au01/01/2026 : AM, dotation 13,33 en61935/28355 ; OD, sortie D28355=4813,33 etD6513=19186,67 contreC2355=24000 ; VT, D3481=24000 contreC7513=20000 etC4455=4000 ; BQ, D5141=24000 contreC3481=24000. Les quatre sont ensuite validées dans le Journal. Il ne faut pas ajouter un second règlement pour cette cession encaissée immédiatement.

Les écritures définitives et le bilan 2025 sont restés identiques. Le doublon de sortie est refusé. Le registre affiche Cédé après rechargement. Deux tests finaux ont réussi, aucun ignoré ; les deux premiers échecs du script, liés à sa navigation vers le sélecteur d’exercice, sont conservés dans les preuves.

La fiche HP-IMM-004 reste PARTIELLE : le parcours technique et l’intégrité sont testés, mais l’oracle initial est divergent et la qualification/régularisation de TVA sur immobilisation reste à documenter. Cette précision complète les anciens cahiers, qui sont conservés sans écrasement ni modification de leurs réponses humaines. Aucun résultat réglementaire ou de recette utilisateur n’est validé automatiquement.

Suivi :35 fiches réussies,1 partielle,226 nonqualifiées individuellement et10 bloquées dans la source, sur 272. Prochaine étape : raccorder chronologiquement les services et effets au scénario annuel, dans une nouvelle société fictive. RH/paie et point 6 restent différés ;incident Lettrage 769 ouvert.
