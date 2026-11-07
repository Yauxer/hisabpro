# Comptes de provision par type — lot603

Cause : les trois modèles acceptaient indifféremment les comptes15/39/45.
Un modèle Stock pouvait donc créer une dépréciation client3942, et inversement.
Correction minimale : contrepartie stock391, client3942, risques/charges15ou45,
avec subdivisions conservées. L’interface reçoit ces préfixes depuis
`/api/cloture/types-ajustements`, issus du même dictionnaire métier que le
contrôle du serveur. Elle ne duplique plus une liste globale indifférenciée.
Noms accessibles explicites ajoutés aux champs Type et Comptes du formulaire.

Pas de migration, de modèle ou de SQL historique changé. Les anciennes pièces
restent inchangées ; le correctif ne tente pas de réparer une classification
historique. Montant, risque, choix de dotation, fiscalité et reprise ne sont
pas déduits de ce seul contrôle de saisie. CPT-09 reste partiel.

Source : [qualification CGNC](../docs/audit/SOURCES_PROVISIONS_20261019.md),
passages indexés OEC sur les familles. PDF complet502 et catalogue MEF timeout
signalés ; aucune revue intégrale ou certification revendiquée.

## Exécutions ciblées

- Avant correction :19cas,10échecs attendus reproduisant les croisements,
 9acceptations des familles/subdivisions valides.
- Après correction :42tests purs réussis0,511s, puis11API réussis44,388s.
- Edge final :2réussis43,118s,1440/390px, trois familles par parcours,
  refus réellement reçu du serveur sans mutation, puis aperçu/création et
  validation ordinaires au Journal. Première exécution :2échecs d’accès au
  champ Type ; libellés accessibles corrigés avant relance.
- Les5anciens tests directs du service de clôture ont également été exécutés.

La consolidation finale et le build sont consignés ci-dessous après lecture
de leurs preuves. Aucun PostgreSQL utilisateur interrogé ou modifié.


## Qualification finale

70tests natifs réussis256,618s,74purs réussis2,165s,5anciens tests de clôture
réussis0,279s ; aucun échec/ignoré dans ces exécutions finales. Build réussi
5,14s, Python compilé, guidePDF1page inspecté et bornes contrôlées.
Les commandes ciblées précédentes ne sont pas additionnées à ces totaux.
Suite : CCA/PCA, clôture et AN sur calendrier décalé réel ; puis poursuite
des reprises spécialisées avec traçabilité explicite. RH/paie différées.
