# Installer les qualifications fiscales et la chaîne annuelle sur une copie

Complément de la [procédure116–118](INSTALLATION_COPIE_PAIE_116_118.md), pour les lots907,909,913 et915. Les migrations119–122 ont été exécutées dans les bases éphémères des tests, jamais dans la base habituelle de l’utilisateur.

Préparer une copie isolée et restaurable, avec configuration backend/frontend distincte. Faire identifier explicitement sa connexion par le responsable technique ; ne pas charger automatiquement la connexion habituelle. Sauvegarder séparément les éléments du coffre RH nécessaires à une restauration. Ne pas remplacer une clé existante par une nouvelle clé.

Extraire le ZIP cumulatif913–915 depuis la racine du dépôt si les lots907–911 y sont déjà présents. Pour une base de code antérieure au lot871, le cumul historique871–915 suppose lui aussi les prérequis de ce point de départ ; il ne remplace pas une installation complète du produit. Ne pas déduire les migrations installées du seul nom d’un ZIP ou de l’existence d’une table.

Le responsable technique applique dans cet ordre les SQL manquants, avec un rôle de gestion du schéma, arrêt à la première erreur et outil explicitement relié à la copie :

| SQL | Apport | Vérification fonctionnelle |
|---|---|---|
| `119_paie_qualifications_fiscales.sql` | Gardes des qualifications IR/frais et déductibilité | Anciennes règles non qualifiées restent « à vérifier » ; validation exige les preuves et le droit expert |
| `120_paie_preparations_fiscales.sql` | Préparations fiscales liées aux simulations brutes/sociales | Onglet Bases fiscales, données connues séparées des inconnues |
| `121_paie_frais_annuels.sql` | Cumuls annuels et liens vers les mois choisis | Choix explicite d’une version par mois, détails et empreintes conservés |
| `122_paie_ir_sources_annuelles.sql` | Lien du contrôle IR vers les frais annuels | Bouton Contrôler l’IR de ce RNI, RNI exact et base arrondie distincts |

Les fichiers se trouvent dans `hisabpro-backend`. Les migrations antérieures ne sont ni remplacées ni réécrites. Un prérequis manquant se corrige en installant ce prérequis sur la copie, jamais en supprimant une contrainte ou une table. Le rôle applicatif `hisabpro` reçoit les seuls droits prévus lorsqu’il existe ; pour un autre nom de rôle, faire vérifier les droits équivalents sans contourner le problème par une application superutilisateur.

Dans l’outil SQL connecté **à la copie identifiée**, ces lectures aident à contrôler les nouveaux objets :

```sql
SELECT current_database(), current_user;
SELECT to_regclass('public.paie_preparations_fiscales'),
       to_regclass('public.paie_controles_frais_annuels'),
       to_regclass('public.paie_controle_frais_sources'),
       to_regclass('public.paie_ir_sources_annuelles');
SELECT conrelid::regclass AS objet, conname,
       pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid IN ('public.paie_controle_frais_sources'::regclass,
                  'public.paie_ir_sources_annuelles'::regclass)
ORDER BY 1, 2;
SELECT tgrelid::regclass AS objet, tgname, tgenabled,
       pg_get_triggerdef(oid) AS definition
FROM pg_trigger
WHERE NOT tgisinternal
  AND tgrelid IN ('public.paie_controles_frais_annuels'::regclass,
                 'public.paie_controle_frais_sources'::regclass,
                 'public.paie_ir_sources_annuelles'::regclass)
ORDER BY 1, 2;
```

Ces lectures ne remplacent pas la recette : il faut notamment les FK de société, le lien IR→source, les gardes contre modification/suppression/troncature et les privilèges sous le vrai rôle applicatif **de la copie**. Aucun test destructif ne doit être tenté sur une base d’exploitation. La réexécution idempotente des migrations et les refus des écritures interdites ont été testés ici sur les cibles nonce isolées.

Redémarrer le backend de la copie et reconstruire son frontend. Activer Personnel en mode protégé et déléguer explicitement les habilitations nécessaires à des acteurs de recette séparés. La validation des règles fiscales conserve son habilitation expert indépendante. Une503 précisant une migration requise est un diagnostic d’installation ; elle n’appelle pas une correction de données comptables.

Suivre [le guide915](IR_ANNUEL_SOURCE_915.md), puis renseigner le [classeur](SUIVI_IR_SOURCE_PAIE_915.xlsx). Une sauvegarde de la copie doit pouvoir être restaurée dans une seconde cible distincte avec schéma, données, séquences, ACL, liens et empreintes identiques. La restauration native99tables a été exécutée automatiquement dans cette session ; elle ne constitue pas une validation de la sauvegarde d’exploitation.

État à distinguer : développements de préparation annuelle livrés ; tests automatisés décrits dans les rapports ; recette utilisateur à effectuer ; production non validée. La retenue mensuelle, le net, les bulletins et la comptabilisation de paie restent hors du résultat de ces contrôles annuels.
