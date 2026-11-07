# Liasse fiscale — résultats du lot 943

**7 tests distincts réussis, aucun échec ni ignoré**, dans une campagne finale de 597,58 secondes XML (code0) : trois parcours Edge/API/PostgreSQL temporaire et quatre tests unitaires d'exports.

- HP-LIA-002 : exports annuels PDF/Excel vérifiés sur ordinateur1440 et mobile390. Identité IF/ICE, logo et caractères littéraux conservés ; bilan337010, immobilisations24000/4800/19200, CPC106409,75, CAF112709,75, B12 et ventilations B6/B7 comparés aux sources. Références02/002 et montants inconnus restent distincts.
- HP-LIA-001 : **Bloqué (source)**. Le cahier annuel reste à20/23 sections ETIC. Le refus409, l'absence d'archive et la conservation des écritures et du snapshot sont vérifiés ; la finalisation annuelle n'est pas déclarée réussie.
- Un dossier fictif capital-seul23/23 vérifie séparément l'archive interne, son empreinte/version et les refus SQL de modification/suppression. Il ne remplace pas le dossier annuel.

L'exécution initiale a échoué à la collecte en raison d'un ancien stub `models`. La reprise avec les fixtures réelles collectées en premier a réussi :5tests,41,04s. La première cible annuelle a échoué sur une hypothèse de test : la ligne de synthèse des immobilisations porte le repèreC, et non le compte23. L'assertion porte désormais sur le libellé et les mêmes montants ; aucun calcul applicatif n'a été modifié. Les rapports d'échecs sont conservés et les répétitions ne sont pas additionnées.

Le suivi porte désormais236Réussi,6Partiel,20Non qualifié par fiche et10Bloqué(source), sur272. Les deux cas humains restent Non testé ;332anciens documents de recette sont conservés octet pour octet.

Produit inchangé :549empreintes identiques au lot941, frontend/backend/migrations non modifiés. Dernier build réel931 :214modules,5,55s ;non relancé ici. Aucune base réelle utilisée. Ni recette humaine, conformité officielle, EDI, dépôt ou préparation de production ne sont validés par ces tests.

[Preuve](../../Test/PREUVE_MVP_943.json) · [Rattachement](../../Test/QUALIFICATION_FICHES_943.json) · [Guide](QUALIFICATION_LIASSE_943.md) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_943.xlsx).
