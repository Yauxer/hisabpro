# Reprendre une lecture d’immobilisations après un échec

Si le registre ne peut pas être chargé, l’écran affiche une alerte et **—** dans les indicateurs. Il n’annonce plus une absence de biens ou des totaux à zéro. La création et la génération annuelle restent désactivées pendant cette indisponibilité. Rétablir la connexion ou résoudre le refus d’accès, puis utiliser **Réessayer le registre**, sans F5. Les valeurs et commandes habituelles reviennent après la lecture réussie.

Pour un plan d’amortissement indisponible, une alerte remplace le tableau et propose **Réessayer le plan**. Cette reprise relit les annuités ;elle ne génère pas de dotation. Les droits restent ceux du rôle :un lecteur ne reçoit pas les boutons Générer après reprise.

Une liste réellement vide, reçue avec succès, affiche toujours **Aucune immobilisation** et des zéros. Une coupure ou un refus n’est pas assimilé à ce résultat. Les données sources et calculs ne changent pas ;la trace d’audit HTTP reste distincte de la comptabilité.

Les tests automatisés provoquent explicitement des coupures de transport de deux GET dans Edge, puis retirent le blocage pour vérifier la reprise sur l’API et PostgreSQL natif jetable. Aucun JSON financier ou montant n’est remplacé. Ces simulations ne prouvent pas la disponibilité du réseau ou de la base de votre future cible.

Si une modification est enregistrée mais que le rafraîchissement échoue ensuite, utiliser **Réessayer le registre** pour relire les données. Ne pas renvoyer le formulaire pour compenser un simple échec de lecture.

Le formulaire permet aussi de renommer un bien dont les dotations existent déjà :il n’envoie plus les paramètres inchangés du plan qui provoquaient un refus. Les montants décimaux de l’API peuvent être représentés en chaînes ;leur comparaison tient compte de cette représentation. Un véritable changement de durée reste transmis et refusé par le verrou du serveur après dotation. Aucun verrou comptable n’est supprimé.

Sur mobile,les quatre indicateurs passent sur deux colonnes et les commandes se replient pour rester visibles.

[Quatre cas humains PDF](RECETTE_LECTURE_IMMOBILISATIONS_931.pdf) · [Excel à remplir](SUIVI_LECTURE_IMMOBILISATIONS_931.xlsx) · [Données et étapes exactes](JEU_LECTURE_IMMOBILISATIONS_931.json). Utiliser exclusivement une copie de recette. Les anciens cas humains restent inchangés. Aucune nouvelle règle fiscale ni migration ;les réserves sur la cession restent ouvertes.
