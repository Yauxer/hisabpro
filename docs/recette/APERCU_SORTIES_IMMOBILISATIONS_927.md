# Vérifier une cession avant de la comptabiliser

Dans **Immobilisations**, ouvrir **Cession / mise au rebut** sur un bien actif. Choisir la nature, la date et, pour une cession, le prix et le traitement de TVA. Utiliser **Calculer avant comptabilisation** : le formulaire affiche les amortissements selon le plan, la VNC théorique, le résultat, la TVA et le TTC, ainsi que les dotations déjà présentes ou encore à comptabiliser.

Le calcul ne crée ni écriture, ni exercice, ni période, et ne consomme pas les séquences métier. La consultation HTTP peut laisser sa trace d’audit normale. Annuler ferme le formulaire sans enregistrer de sortie. L’exercice et la période doivent déjà exister et être ouverts.

Toute modification du formulaire efface l’aperçu, même si l’on revient ensuite à la première valeur. Recalculer pour obtenir des chiffres actualisés. Si les sources d’amortissement ou les paramètres transmis ont changé entre l’aperçu et l’enregistrement, l’empreinte transmise est refusée : recalculer avant de réessayer. Ce contrôle porte sur les sources et calculs de l’aperçu ; il ne constitue pas un gel universel de tous les paramètres de société.

**Comptabiliser la sortie** conserve le flux existant : contrôles métier, dotations manquantes, sortie d’actif, produit de cession et encaissement si demandé. L’aperçu est facultatif ; les anciens clients API restent compatibles. Il ne remplace ni les contrôles d’enregistrement ni la validation définitive des écritures. Seuls les rôles autorisés peuvent enregistrer ; l’API d’aperçu accepte aussi la consultation seule.

Exemple de recette : bien de24 000MAD, cinq ans linéaires, mis en service le01/01/2025, dotation2025 de4 800MAD déjà enregistrée, cession le01/01/2026 pour20 000MAD HT, TVA hypothétique20%, sans encaissement. La convention interne existante inclut le jour de sortie : dotation2026 de13,33MAD, cumul4 813,33MAD, VNC19 186,67MAD et résultat813,33MAD. Les trois écritures nouvelles sont la dotation, la sortie et le produit de cession ; aucune banque n’est créée dans cet exemple.

**Réserve maintenue :** ces montants ne valident pas une convention fiscale obligatoire ni la qualification/régularisation de TVA. La fiche historique IMM004 reste **Partiel**, car son ancien oracle attendait VNC19 200 et résultat800. Aucun montant historique n’a été modifié pour effacer cet écart. La mise au rebut et les biens non amortissables restent soumis à leur justification propre.

[Recette PDF — six cas](RECETTE_APERCU_SORTIES_927.pdf) · [Excel à remplir](SUIVI_APERCU_SORTIES_927.xlsx) · [Données exactes et écritures attendues](JEU_APERCU_SORTIES_927.json) · [Résultats automatiques](RESULTATS_MVP_927.md). Utiliser exclusivement une copie de recette restaurable.
