# Petites améliorations UX — liste Factures767

14 tests Edge/API surPostgreSQL éphémère réussis en144.1s,aucun échec/erreur/ignoré.4nouveaux parcours UX,2régressions dates100/101factures,8lectures historiques etvrai exercice vide. Campagnes précédentes4puis14 également réussies,recouvrements non additionnés. Build final7,92s code0 ;compilation2tests Python OK.

Demande utilisateur du24octobre :repérer et corriger les améliorations simples évidentes. Intervention limitée àla liste Factures,avec le style existant. Aucune règle de validation/paiement/retard,aucun calcul comptable/fiscal ni API modifié.

- Réinitialiser les filtres remet ensemble recherche,type,statut et deuxdates àleur valeur initiale,sans changer l’exercice ;retour du focus vers la recherche.
- Effacer la recherche dispose dun nom accessible etne modifie pas les autres critères. Le champ reste un champtexte avec rôle searchbox pour éviter une seconde croix native. Les boutons type/statut exposent aria-pressed,le focus clavier reste visible etle compteur est annoncé.
- Le vide distingue exercice sans facture etcritères sans résultat. Il propose Afficher toutes les factures de cet exercice,ou Créer une première facture uniquement si le rôle autorise l’écriture. Les erreurs de lecture restent dans leur branche distincte.
- L’état vide sort du grand tableau :il ne dépend plus de ses11colonnes ou de son défilement horizontal. Sa carte suit sa hauteur naturelle pour ne pas couper le bouton surmobile. Le tableau rempli etses colonnes sont conservés.

Les4nouveauxparcours sont :filtres combinés1440/390,exercice vide admin1440 etlecture390. Saisie des5critères,activation au clavier,effacement partiel puisglobal,focus,retour des3factures,aucune requête de mutation parles filtres etphotographie comptable identique. Le rôlelecture ne reçoit pas laction de création. Louverture puisla fermeture du formulaire admin ne crée pas de facture. Vérifications géométriques :bouton contenu dansle viewport etcarte sans contenu caché ;captures réellement inspectées.

Les8régressions de lecture couvrent notammentNaN/Inf/quantitéNULL etvrai vide ;les états indéterminés ne deviennent pas des zéros. Ces jeux historiques sont préparés uniquement dansles clusters nonce des fixtures. Les2cas100/101factures vérifient pagination,périodes,avoirs,indicateurs etexportCSV. La seule adaptation de cet ancien test déplace la recherche du message vide de l’intérieur du tableau vers la page,conformément àson nouvel emplacement ;l’assertion etles oracles financiers sont conservés.

Le premier contrôle4cas/build11,33s puis14cas/build7,93s étaient verts. La revue visuelle a ensuite justifié les corrections de largeur/hauteur du vide ;campagne14 etbuild7,92s rejoués après ces modifications. Aucun test échoué ou ignoré masqué. Pas de certification d’accessibilité ni de recette humaine globale prétendue. L’ergonomie de tous les écrans n’est pas validée par ce lot. Backend/migrations et117protections inchangés ;aucune base réelle.

[Mode d’emploi](../docs/UX_FACTURES_FILTRES_767.md), [reprise](../docs/audit/REPRISE_APRES_UX_FACTURES_767.md).
