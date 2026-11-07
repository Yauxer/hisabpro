# HisabPro — relances et suivi fournisseurs

Les parcours utilisent de nouvelles sociétés fictives sur PostgreSQL natif isolé et Edge, aux largeurs 1440 et 390. Deux factures fournisseurs de 240 MAD, références 02 et 002, et une vente impayée de 14400 MAD sont créées, comptabilisées et validées par API. Les tests des interfaces portent sur les métadonnées de suivi ; ce lot ne rejoue pas les 50 opérations annuelles.

La relance interne de la vente est créée au 22/12/2025, niveau 1 et canal email, avec promesse au 31/01/2026. La promesse devient 15/02/2026, le commentaire est modifié, puis la relance est annulée. Chaque étape est rechargée et contrôlée dans l'interface et l'API. La relance annulée reste dans l'historique. Aucun email externe n'est envoyé et les écritures définitives restent identiques.

Le cas fournisseurs d'origine demande T4 2025. Ses deux factures arrivent à échéance le 31/12/2025 : elles ne sont pas encore en retard à la fin de cette période, donc le rapport ne les affiche pas. Les dates ne sont pas modifiées pour obtenir un test vert. Un contrôle complémentaire T1 2026 conserve les références 02 et 002 distinctes et complète la date de livraison/service au 02/12/2025, sans litige ni exclusion. Les compléments persistent après rechargement. Le CSV téléchargé contient les deux lignes, dates et références exactes ; son nom est incorrect (export.bin), anomalie conservée pour correction ultérieure. Le cas HP-FAC-017 reste partiel. Les montants indicatifs d'amende et l'assujettissement ne sont pas validés par ce test.

Les premiers essais échoués sont conservés : sélecteurs de libellés du test trop stricts, attente incorrecte de lignes en T4 2025, puis nom de fichier export.bin. Le dernier parcours vérifie séparément le contenu du fichier et consigne explicitement le nom incorrect ; il ne prouve pas la résolution de cette anomalie. Aucun code produit ni migration n'est modifié dans ce lot.

Suivi : 131 fiches réussies, 6 partielles, 125 non qualifiées individuellement, 10 bloquées par les sources. Les 70 statuts fonctionnels restent inchangés. Aucun PostgreSQL réel utilisateur n'est utilisé. La recette utilisateur et la conformité réglementaire ne sont pas validées automatiquement.

Utilisation : Situation → Échéances & impayés → Relancer, puis onglet Relances pour modifier ou annuler. Délais de paiement → choisir exercice et trimestre → Compléter chaque facture → recharger → Exporter CSV. Vérifier les dates et l'applicabilité avant tout usage déclaratif.

Prochaine étape : corriger le nom du CSV des délais, diagnostiquer les navigations/polices du laboratoire et terminer le contrôle avant IS sur mobile. Reprendre ensuite les fiches non qualifiées, sans répéter les lots déjà couverts. RH/paie et point 6 restent différés.
