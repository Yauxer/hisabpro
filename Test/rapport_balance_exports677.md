# Lot 677 — Préparations de balances : détail et provenance des exports

Le PDF net seul et l’Excel d’aperçu ne suffisaient pas à consulter les
immobilisations ni à identifier la version conservée exportée. Le dossier
conserve désormais ses agrégats, mais les présente avec le détail partagé du
bilan : brut, amortissements/provisions, net, comparatif et sous-postes pour
mémoire. Une nouvelle route de lecture XLSX exporte le snapshot vérifié, sa
provenance et ses balances sources normalisées. L’interface l’utilise pour les
versions conservées ; l’Excel d’aperçu reste distinct.

Aucun schéma, migration ou calcul comptable/fiscal modifié. Les agrégats
historiques ne sont pas recalculés depuis le plan courant. Les versions sans
source gardent leurs agrégats sans détails inventés. N-1 absent et CPC/ESG
indisponibles restent explicites. Les exports comportent le logo/identité
actuels, indiqués hors empreinte du contenu. Les textes restent du texte Excel.

## Oracle indépendant

Balance N fictive : débit = crédit = 51 000 MAD ; immobilisations corporelles
21 000 brut, amortissements 300, net 20 700 ; actif total brut 50 000,
amortissements 300, net 49 700 ; CPC 5 000. N-1 vaut la moitié : actif net
24 850 et CPC 2 500. Les sous-postes corporels 231/232/233/234/235/238 valent
respectivement 1 000/2 000/3 000/4 000/5 000/6 000 brut. Aucun amortissement
n’est ventilé arbitrairement entre ces sous-postes.

Les parcours natifs créent aussi une écriture de capital fictif de 333 MAD,
validée par l’API ordinaire, indépendante des balances importées. Les photos
des tables métier et ACL sont identiques avant/après consultation et exports.
Une version 2 distincte est conservée ; le rechargement et les téléchargements
de version 1 gardent ses chiffres et son empreinte.

## Exécutions

- Baseline : 35 réussites, 2,94 s, zéro échec/ignoré. La première commande Python
  système a échoué en collecte (3 dépendances absentes, 8,69 s) ; reprise via
  l’environnement virtuel et URL SQLite mémoire explicite.
- Première suite ciblée : 42 réussites/3 échecs en 6,61 s, puis 43/2 en 6,06 s.
  Les erreurs concernaient le banc : cellule vide relue `None`, source de test
  non normalisée et intitulé exact du CPC. Montants attendus inchangés.
- Nouveaux parcours natifs : **4 réussites en 47,00 s**. Edge 1440/390,
  administrateur/lecteur, avec/sans N-1, ancien snapshot, refus 401/404,
  refus de création 403 pour Lecture, documents PDF/XLSX réellement ouverts.
  PostgreSQL jetable marqué, LOGIN applicatif non propriétaire, chaîne 091.
- Ancien banc de composant : **10 réussites en 21,61 s** après ajout du
  `ModulesProvider` et de son identité fictive. Ce banc utilise des réponses
  synthétiques ; il est distinct des parcours natifs précédents.
- Build Vite : **réussi en 6,38 s**, code 0. Avertissements existants concernant
  les bundles et l’import XLSX conservés.

Campagne commune finale : **62 réussites en 104,66 s**, 30 avertissements,
zéro échec/erreur/ignoré, code 0, sur les sept modules concernés. Les groupes
précédents se recouvrent et ne sont pas additionnés. Compilation Python réussie
pour les trois fichiers backend et les trois fichiers de tests modifiés.

La première campagne commune, chargée avant la correction des bancs, a donné
51 réussites, 1 échec et 10 erreurs en 387,75 s : dix setups sans contexte
société et une clé `est_principale` inexistante dans le banc lecteur. Les
contrats réels et les délais n’ont pas été assouplis ; la campagne finale utilise
le provider et le vrai sélecteur multi-société. Ces échecs sont conservés.

## Contrôles et limites

Capture Lecture 390 et page PDF actif détaillé rendue inspectées : textes,
colonnes et commandes lisibles. 106 fichiers protégés inchangés (AGENTS,
main/modèles/schémas et 102 migrations). Aucun PostgreSQL réel utilisé.

SQLite sert ici aux contrats purs/API unitaires ; concurrence, immutabilité
SQL et téléchargements connectés disposent de bancs PostgreSQL distincts.
L’installation cible et la recette humaine ne sont pas validées. Le mode
Liasse seule complet reste partiel : ETIC, fiscalité, annexes et EDI ne sont
pas déduits d’une balance. RH/paie et retour humain restent différés.

Mode d’emploi : [préparations détaillées](../docs/LIASSE_BALANCES_DETAIL_677.md).
