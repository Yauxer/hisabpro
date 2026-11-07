# Calcul documentaire facultatif CCA / PCA — lot595

Dans Clôture, le calcul utilise le montant déjà comptabilisé, la base déclarée
et la période explicitement saisis. La convention choisie est celle des jours
calendaires inclusifs, avec arrondi au centime à demi au supérieur. Le calendrier
réel de l'exercice, y compris décalé, fournit la date de coupure. Une source Python
Decimal unique alimente l'écran, le PDF et le libellé proposé.

Le calcul et le PDF ne créent aucune écriture. Une reprise explicite remplit le
formulaire existant après relecture et comparaison de l'empreinte. L'aperçu,
la création du brouillon, la contrepassation et la validation dans le Journal
conservent les règles existantes. Une saisie modifiée invalide le résultat ;
un calendrier ou une identité modifiés exigent un nouveau calcul avant export
ou reprise. Les consultations seules calculent et exportent sans préparer
d'écriture. Aucun schéma, migration ou démarrage automatique modifié.

## Calcul indépendant et interactions

12 000 MAD du01/10/2025 au31/03/2026 :182jours, dont90après31/12/2025.
Part reportée5934,07 ; complément6065,93. L'arrondi est effectué une seule fois
sur la part reportée, puis le complément est calculé par différence exacte.
Années bissextiles, périodes entièrement passées/futures, dates extrêmes,
demi-centime et grandes valeurs sont couverts ; les entrées non finies,
ambiguës, booléennes ou incompatibles avec le centime sont refusées.

Dans Edge réel, deux écritures initiales fictives sont validées : capital20 000
et charge ou produit12 000. Le calcul et son PDF ne les modifient pas. La reprise
conduit aux lignes5934,07 du modèle CCA ou PCA, puis une contrepassation en
brouillon au01/01/2026. Après validation de l'ajustement, CPC−6065,93 pour CCA
ou+6065,93 pour PCA, bilan équilibré et sources définitives intégralement inchangées.
Les comptes de la recette sont des choix explicites des modèles existants,
pas une affectation obligatoire nouvelle.

## Tests réellement exécutés

- Calculs purs et API :32 réussis,27,95s.
- Première UI :4 échecs de sélection/attente. Noms accessibles des listes rendus
  explicites et attente du calendrier2025 ajoutée ; séparateur de milliers du
  test aligné sur l'utilitaire déjà présent. Aucun calcul financier contourné.
- Cible admin CCA :1 réussie39,17s ; quatre parcours finaux :4 réussis38,71s.
- Bancs intermédiaires :103 réussis229,45s puis181,17s. Ils ne sont pas additionnés.
- **Banc de livraison :103 réussis182,63s, aucun ignoré/échec, code0**, JUnit
  `consolidation595_livree.xml`. Anciens ajustements, périodes, aperçu, rôles,
  téléchargements GET du registre et POST du nouveau PDF inclus.
- **Restauration finale native :1 réussie108,33s**,75tables, schéma/données/ACL/
  séquences identiques, source préservée et cibles supprimées. Calcul JSON,
  empreinte, texte PDF, logo et ajustement validé/contrepassation brouillon
  identiques avant et après restauration. Anciennes preuves conservées.
- Build Vite final :4,93s, code0 ; avertissement de taille du bundle existant.
  Python compilés et guide PDF1page inspecté, texte et limites de page vérifiés.

## Limites

Aucun PostgreSQL utilisateur ni donnée réelle touché. La méthode est facultative,
pas une méthode comptable ou fiscale imposée. La TVA, la déductibilité, les
provisions et leurs reprises ne sont pas calculées par cet outil. Le PDF est
à conserver avec les pièces réelles ; ses données ne sont pas archivées
automatiquement dans la liasse. L'empreinte identifie les données, pas une
signature ou le hash du PDF. Recette humaine et production non validées.

Guide : `docs/guides/UTILISATION_CALCUL_CCA_PCA_20261018.pdf`.
Suite : compléter la recette documentaire des lots593/595, puis poursuivre
les parcours annuels et les provisions spécialisées selon les sources vérifiées.
RH/paie et retour utilisateur réservé restent différés.
