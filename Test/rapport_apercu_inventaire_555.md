# Lot 555 — Aperçu et consultation des ajustements d'inventaire

Un aperçu permet de vérifier le journal OD, la date de clôture paramétrée,
les deux comptes et leurs intitulés, les débits/crédits et la date de
contrepassation avant de créer un brouillon. Il utilise le constructeur métier
existant. Aucun ajustement, écriture ou exercice n'est préparé par cet aperçu.
Une modification du formulaire invalide immédiatement l'ancien résultat ;
une réponse HTTP retardée ne peut pas réactiver un ancien montant.

Les quatre cut-off préparent leur inverse en brouillon au lendemain de la
clôture réelle. Les provisions ne sont pas inversées automatiquement.
L'écran et la confirmation des dotations n'imposent plus le 1er janvier ou le
31 décembre pour un exercice décalé. Les dates des ajustements déjà créés sont
tirées de leurs écritures, sans recalcul ni modification de ces écritures.

Les comptes Consultation seule conservent les informations d'inventaire mais
n'ont ni formulaire de création ni suppression proposés ; les boutons de
dotations/clôture sont désactivés. Les refus API existants restent actifs.
Les erreurs 422 utilisent le formateur partagé pour indiquer le champ fautif.
Le formulaire et les actions s'adaptent à un écran de 390 px.

## Tests réellement exécutés

- Avant ajout : 8 échecs, 2 désélectionnés, 42,91 s. Sept routes d'aperçu
  absentes (404) ; le test lecteur échouait sur un sélecteur de texte ambigu
  avant son assertion de permission. Le défaut du bouton lecteur était visible
  dans le code ; ne pas confondre cette inspection avec une reproduction UI.
- Première correction : 7 réussis, 3 échecs de sélecteurs stricts de test,
  47,66 s. Le justificatif apparaissait aussi dans la liste des brouillons.
- Deuxième : 8 réussis, 2 échecs d'oracle de format d'affichage, 48,60 s.
  `fr-MA` utilise un point de milliers ; l'oracle a été corrigé sans changer
  les montants métier ou le formateur existant.
- Suite étendue : **11 réussis, 29 avertissements, 50,85 s** : sept modèles,
  rôles admin/comptable/lecture, création après aperçu, réponse réelle retardée
  après modification, refus sans création d'exercice pour une cible inconnue
  ou une saisie invalide. PostgreSQL nonce098 et Edge, aucun mock métier.
- Tests purs connexes : **43 réussis, 1 avertissement, 1,26 s**.
- Build Vite final : **réussi** ; avertissements de taille du bundle conservés.

Capture mobile examinée : champs et dates lisibles. L'espacement entre débit
et crédit a été augmenté après cette inspection. Les tests connexes de clôture
et de chargements retardés sont consignés dans le journal après leur achèvement.

## Utilisation et limites

Comptabilité → Clôture → choisir l'exercice → Ajouter un ajustement → renseigner
type, montant et justification → Vérifier l'écriture → relire les lignes →
Créer l'écriture. Valider les brouillons dans le Journal après contrôle.
Toute modification de montant ou de compte impose une nouvelle vérification.
Le contrôle des périodes et du calendrier suivant est refait à l'enregistrement.

Pas de nouveau taux, de règle fiscale ou de calcul automatique des provisions.
Les justificatifs restent à fournir par le comptable. Aucun PostgreSQL réel,
aucune migration ; recette utilisateur et production non validées.

Extension finale : **34 réussis, 29 avertissements, 153,58 s, code 0**.
Elle inclut les 20 cas natifs553, le cycle de clôture connecté existant et
les deux chargements retardés390/1365. Build final **5,74 s**, code0.
Deux fichiers Python compilés. Capture390 finale relue après espacement.
