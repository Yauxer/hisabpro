# HisabPro — remplacement contrôlé des rapprochements

La fiche NEG023 est exécutée dans Edge sur ordinateur et mobile avec API réelle et PostgreSQL natif isolé. Deux écritures fictives BQ de100000MAD et deux lignes de relevé distinctes sont créées. CAP-01 est rapproché depuis le sélecteur de l'écran.

Un défaut réel est reproduit aux deux largeurs : choisir une autre écriture directement sur la ligne déjà rapprochée retournait200 et remplaçait son lien. Le test attendait un refus et les deux exécutions échouées sont conservées. Aucun rapprochement réel de l'utilisateur n'a été modifié pour reproduire ce défaut.

La correction ajoute un contrôle dans la fonction métier partagée de rapprochement, sous le verrou existant. Si une ligne est déjà rapprochée vers une autre écriture, l'API répond409 : Dérapprochez cette ligne de relevé avant de choisir une autre écriture. Aucun calcul comptable, droit ou migration n'est changé. Les propositions automatiques réutilisent cette même fonction ; elles ne contournent pas le garde-fou.

Les tests finaux vérifient le message visible, la conservation exacte de la situation et du journal, puis l'interdiction inverse d'utiliser la même ligne comptable pour une seconde ligne de relevé. Le sélecteur vide permet toujours le dérapprochement explicite. Après cette action, le nouveau rapprochement est autorisé et persiste après rechargement. Aucune nouvelle écriture n'est produite par ces opérations de lien.

Les deux parcours finaux et la campagne native de permissions banque/relevés passent. Les nombres et durées exacts sont joints dans PREUVE_CAHIER849.json. Le backend modifié est compilé ; le frontend est inchangé et aucun nouveau build n'est revendiqué. Les462empreintes de la candidate sont actualisées dans CANDIDAT_FACTURATION_COMPTABILITE_849.json ;une seule diffère de841,la route rapprochement. Les anciennes archives et preuves841 restent conservées.

Le suivi atteint168fiches automatiquement réussies,5partielles,89nonqualifiées individuellement et10bloquées à la source. Les70statuts fonctionnels globaux restent inchangés. Les lots843à849 qualifient10scénarios négatifs supplémentaires ;la correction métier de cette reprise porte uniquement sur le rapprochement. Ce résultat ne vaut ni recette humaine ni validation de production.

Prochaine étape indépendante :stocks et immobilisations,NEG025à028. La recette sur une copie de l'environnement cible et les réserves documentées841 restent à traiter ;RH/paie,formats officiels et justificatifs historiques différés. Aucun PostgreSQL utilisateur utilisé.
