# Personnel / RH — interfaces et recette du pilote (879)

Livraison du 28 octobre 2026. Ce document remplace l’état **intermédiaire non qualifié** de879 pour les sources et tests décrits ici ; les anciens documents restent des preuves historiques.

## Ce qui est utilisable

- Sidebar **Personnel & Paie** : neuf rubriques visibles ; **01 Personnel** disponible, huit rubriques honnêtement marquées **À venir**. L’espace historique `/cnss` reste accessible selon les droits.
- Salariés : liste, recherche, filtres, pagination, création au brouillon et reprise explicite d’une fiche ancienne non ambiguë.
- Dossier : identité, coordonnées facultatives, numéro CNSS et données fiscales personnelles sous droits ; consultation à date du contrat, de la rémunération et du statut de sortie.
- Contrats et salaires : propositions, soumission, approbation par un autre compte habilité, montants exacts et dates d’effet ; les versions approuvées restent conservées.
- Demandes et historique : auteur, décideur, motif, référence, révision, rejet conservé ; conflits visibles et absence de transfert silencieux de préparation.
- Habilitations : attribution/révocation par administrateur, activation volontaire de la protection, masques après actualisation et purge lors d’un changement de société.
- Ordinateur et mobile : parcours navigateur réel aux largeurs1440 et390px, formulaires défilables, navigation clavier et reprise après erreur réseau.

La création ou modification administrative d’un salarié ne génère **aucune écriture comptable**, dette, déclaration ou paie calculée. Les totaux du jeu de recette sont des sommes indépendantes de bases contractuelles.

## Démarrer sur une copie de test

1. Faire préparer par l’administrateur technique une copie isolée restaurable. Ne pas utiliser les données réelles pour essayer les scénarios négatifs.
2. Installer les migrations **105 → 106 → 107 → 108** avec le rôle migrateur prévu par le projet, dans cet ordre, sans réécrire les migrations déjà appliquées. Le code runtime garde ses droits limités. Les prérequis antérieurs restent ceux des guides873/875/877.
3. Choisir la société de recette et vérifier que le module GRH est activé dans ses modules. Préparer deux comptes **déjà légitimement admin/comptable**, distincts, appartenant à cette société. Conserver un administrateur pour les habilitations. Ne pas attribuer un rôle comptable à une personne qui doit uniquement gérer le personnel.
4. Ouvrir **Personnel & Paie → 01 Personnel → Habilitations**. Accorder au préparateur les droits identité, rémunérations, identifiants sensibles, proposer, soumettre et historique ; au validateur les lectures utiles, approuver et historique. Chaque attribution demande un motif.
5. Activer volontairement la protection après lecture de ses effets. Les anciennes mutations Personnel/absences/avances deviennent bloquées ; l’espace historique n’est pas un contournement.
6. Dans **Salariés → Créer un salarié**, utiliser les données P001/P002/P003 du cahier. Le salaire n’est pas un champ de création. Choisir explicitement le compte du bénéficiaire ou confirmer son absence de compte, avec une référence de contrôle.
7. Ouvrir la demande, la soumettre avec le préparateur ; le second compte la contrôle et l’approuve. Proposer ensuite contrat, puis rémunération. Utiliser **Consulter les conditions au** pour comparer le présent et une hausse future.
8. Suivre les29 cas du PDF dans l’ordre. Renseigner le résultat réel dans Excel ; tous les statuts humains sont initialement **Non testé**.

L’activation est un choix de la société : aucune activation, attribution de droit ou migration n’a été effectuée sur la base utilisateur pendant cette session. Si un prérequis historique manque sur la copie, noter le cas bloqué ; ne pas inventer une reprise.

## Documents à ouvrir

- [Cahier PDF —17pages,29cas](CAHIER_RECETTE_PERSONNEL_HISABPRO_879.pdf).
- [Classeur Excel —synthèse, cinq domaines et données de saisie](SUIVI_RECETTE_PERSONNEL_879.xlsx).
- [Jeu de données exact et calculs indépendants](JEU_DONNEES_PERSONNEL_879.json).
- [Cas de recette structurés](CAS_RECETTE_PERSONNEL_879.json).
- [Résultats réellement exécutés](LOT1BC_RESULTATS_879.md).

Le classeur distingue la couverture automatisée de chaque cas du résultat humain à renseigner. Les formules et le graphique se recalculent à l’ouverture dans Excel ; aucun résultat humain n’a été prérempli comme réussi.

## Limites et suite

**Pilote Personnel1A/1B/1C : livré et qualifié sur le périmètre ci-dessus.** Le Lot1 complet du master reste **partiel** pour un déploiement général : profil exclusivement Personnel avec confinement hors des autres modules, coordonnées bancaires chiffrées et gestion des clés, pièces sécurisées et régimes sociaux doivent être complétés ou explicitement cadrés avant leur usage. Les références de pièces enregistrées ne prouvent pas leur contrôle humain.

Les liens bénéficiaire et matricule ne sont pas librement rectifiables dans ce pilote. Les cas historiques ambigus restent visibles et nécessitent un examen ; aucune réparation arbitraire n’est effectuée. Un compte utilisateur désactivé ne peut plus faire approuver sa préparation ; après108, un autre responsable peut la rejeter sans changer son auteur.

Le calcul de paie, les bulletins, variables, cotisations, IR, prêts, virements et déclarations du nouveau circuit relèvent des lots suivants. Les fonctions historiques ne constituent pas une qualification de ces lots. Avant le Lot2, traiter les limites du Lot1 ; le choix de conservation des clés de chiffrement doit être arrêté avant toute collecte de RIB. Les taux et règles réglementaires nécessiteront leurs sources officielles.

**Tests automatisés validés : oui, dans l’environnement isolé décrit. Recette utilisateur : à effectuer. PostgreSQL cible et exploitation : à valider. Prêt pour production : non validé.**
