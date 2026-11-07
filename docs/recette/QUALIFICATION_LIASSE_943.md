# Vérifier les exports et la finalisation de la liasse

Suivre le [cahier complet](CAHIER_RECETTE_HISABPRO.pdf), le [classeur humain](CAHIER_RECETTE_HISABPRO.xlsx) et les [données exactes](jeu_donnees_recette.json), sur une copie isolée. Les cas concernés sont **HP-LIA-001 et HP-LIA-002**, dans « Liasse exports ». Leurs résultats humains restent à renseigner.

Dans **Comptabilité → Liasse fiscale**, sélectionner 2025 et consulter la synthèse. Vérifier l'identité IF/ICE, le bilan, le CPC, les contrôles et les notes ETIC. Les repères T1–T25 sont une **numérotation interne HisabPro**, incluant bilan et CPC ; ils ne constituent pas une nomenclature officielle DGI.

Télécharger **Excel**, puis **PDF**. Comparer au minimum :

- Bilan : actif et passif 337 010 MAD ; immobilisations corporelles 24 000 brut, 4 800 amortissements, 19 200 net ; stock 6 600 ; clients 14 400 brut, provision 2 000, net 12 400.
- CPC : résultat net 106 409,75 ; ESG : CAF 112 709,75 ; B12 : bénéfice fiscal 133 830, réintégrations incluant IS comptabilisé 27 420,25.
- B6/B7 : mêmes ventilations que l'écran, zéros conservés et montants inconnus « À compléter ». Les références `02` et `002` désignent deux pièces distinctes.
- Identité, logo et notes : mêmes informations dans les deux documents, y compris les caractères `<`, `>` et `&` ; avertissements et contrôles bloquants visibles.
- Financement : la non-applicabilité du comparatif dans ce premier exercice est explicite ; aucun exercice antérieur n'est fabriqué.

Le scénario annuel ETIC805 conserve volontairement **20 sections complètes sur 23**. B6 contient encore deux montants sans échéance qualifiée (34552 : 80 ; 3491 : 11 000). B13 nécessite une méthode d'affectation de l'impôt documentée. B14 n'est pas confirmé dans ce parcours ; son rapprochement séparé807 ne remplit pas cette confirmation à la place de l'utilisateur.

**HP-LIA-001 reste donc bloqué par les sources**, même si le refus technique de finalisation est correctement testé. Le bouton Finaliser doit être indisponible et la requête de finalisation refusée409. Ne pas confirmer arbitrairement les sections, inventer des échéances, modifier des écritures définitives ou substituer un autre jeu pour obtenir une archive.

Un autre test, capital-seul, vérifie séparément une archive interne23/23 : empreinte, version, relecture et refus SQL de modification/suppression. Cette preuve vérifie le mécanisme d'archive ; elle ne finalise pas le dossier annuel du cahier et ne vaut ni dépôt, ni validation réglementaire.

[Résultats automatisés](RESULTATS_MVP_943.md) · [Rattachement par fiche](../../Test/QUALIFICATION_FICHES_943.json) · [Suivi actualisé](SUIVI_AUTOMATISATION_CAHIER_943.xlsx).
