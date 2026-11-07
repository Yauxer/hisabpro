# Lot526 — Identifier la vraie écriture de stock avant régénération

## Défauts reproduits et correction minimale

La recherche par référence seule, sans exercice ni priorité au lien technique,
pouvait supprimer le brouillon d'un autre exercice ou une pièce manuelle.
Une définitive d'un autre exercice pouvait au contraire empêcher indûment la
génération courante. Un stock renommé dans le Journal pouvait être ignoré,
et un lien incohérent d'inventaire remplacé silencieusement.

La régénération utilise maintenant le lien `ecriture_stock_id` existant en
priorité, en contrôlant société, exercice et origine stock. Sans lien, elle
accepte uniquement une écriture de stock certaine, dans le même exercice,
avec la référence attendue et sans doublon. Sinon elle refuse409 avant toute
suppression. Le verrou/rechargement du parent520 est conservé.

Une origine manuelle ou historiquement indéterminée n'est pas reclassée en
stock pour passer un contrôle. Elle reste à examiner, avec correction
traçable si justifiée. Aucun champ de saisie ajouté ou rendu obligatoire,
aucune migration, aucun montant ou compte comptable modifié.

## Neuf scénarios API/PostgreSQL

- Même référence sur un autre exercice : brouillon conservé avec ses lignes
  et son audit ; définitive également conservée et ne bloquant plus la
  génération courante. La nouvelle pièce est créée et validée sur le bon
  exercice. Aucune clôture ni aucun à-nouveau de l'ancien exercice ne sont
  inventés dans ces scénarios ciblés.
- Deux brouillons non rattachés portant la même référence : refus409,
  tables métier intactes, aucun choix arbitraire.
- Une pièce manuelle unique portant cette référence : refus409 et conservation.
- Vrai stock lié mais renommé, avec collision d'une pièce manuelle : seule la
  vraie source liée est régénérée ; la pièce manuelle et son contenu restent
  présents. Après validation du stock, la clôture refuse normalement le
  brouillon manuel restant. Il n'est pas supprimé pour obtenir un test vert.
- Trois incohérences synthétiques du lien : autre exercice, autre société,
  origine manuelle. Refus409 sans réparation silencieuse ni changement des
  tables métier (hors journal des requêtes).
- Ancien stock sans lien, avec source/référence/exercice uniques : récupération
  déterministe du brouillon, nouvel identifiant lié, audit antérieur conservé,
  validation, clôture−2840 et FEC effectifs.

Les montants sont fictifs : stock8×20=160, CM3000 existante conservée.
Aucune qualification fiscale d'une entreprise réelle n'est déduite.

Avant correction : **8échecs/1réussite,29avertissements,42,22s**, code1.
Le cas positif de récupération d'une source stock unique passait déjà ; il
reste conservé. Les autres scénarios démontrent les problèmes de sélection,
sans revendication de suppression d'une écriture définitive.

Qualification ciblée : **34réussites,29avertissements,132,95s**, code0 : neuf
nouveaux cas, neuf conflits520, six protections de génération510 et dix tests
purs de stock/numérotation. Pas d'addition des passages successifs.

Qualification finale : **410réussites,29avertissements,759.12s**, code0,
aucun échec/erreur/ignoré :401oracles524 et9cas526.
Scénarios du wrapper principal sous rôle LOGIN non propriétaire PostgreSQL18.3,
sources figées vérifiées ; Edge ordinateur/mobile, vente/achat,
factures→règlements→lettrage, PDF/XLSX/impression, fiscalité et clôtures inclus.

Restauration098 :74tables, source préservée, cibles supprimées, trois fonctions
identiques et refus409/reprise conservés. Invariants comptables0 : pièces
déséquilibrées, montants non finis, définitives sans numéro/date.
Trois Python du lot et34du cumulatif compilés ;98SQL/115guides,
main/models/AGENTS, Journal522, mouvements524 et autres sources inchangés.
Frontend inchangé.

Commande : même liste que la consolidation524 avec
`Test/test_consolidation_sources526_isole.py` comme wrapper, avec `-ra` via
`Test/run_unit_tests.py`.


## Installation et limites

Installer `services/stock_service.py` à jour526 sur la version524, puis
redémarrer l'API. Aucune nouvelle migration ni intervention sur les données
réelles. Les origines/lien historiques incohérents restent visibles et à
examiner ; aucune remise en cohérence financière n'est déduite.

Les écritures manuelles concurrentes créant de nouvelles collisions de
référence, les autres générateurs, les accès hors API et les dates d'exercice
modifiées simultanément ne sont pas garantis par ce lot. Recette utilisateur,
production et point6 humain restent en attente.
