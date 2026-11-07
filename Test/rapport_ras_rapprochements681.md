# Lot681 — Rapprochement documentaire des captures TVA opérées

Nouvelle fonction distincte de la déclaration fiscale : l’utilisateur relie
explicitement un montant de capture active à une pièce comptable déjà validée
portant le débit du compte choisi dans la capture et un crédit de trésorerie.
Les écritures et les paiements restent inchangés. Le retrait est une trace
immuable motivée ; il ne contrepassera pas la pièce.

La migration103 est additive, manuelle et rejouable : deux tables immuables,
six triggers, droits SELECT/INSERT seulement, séquences sans SETVAL et fonctions
de contrôle fermées à PUBLIC. Acteur/société, liens, faits exacts, montants et
capacités sont vérifiés aussi au niveau SQL, avec sérialisation par société.
Les sources sont figées dans une empreinte et relues pour les diagnostics.

L’interface du registre achats propose les pièces par référence, leur débit
disponible, un montant explicite et une confirmation. Consultation seule,
actualisation, trace des retraits et PDF interne avec logo sont disponibles.
Les déclarations TVA et exports099 ne sont pas modifiés pour présumer un versement.

## Oracle et limites

Vecteur fictif : capture75MAD et pièce75MAD, puis liens30+45. Total rapproché75,
capacité documentaire0. Retrait du lien45 : total30, capacité45 ; pièce et Journal
restent75. Deux demandes50 sur une capacité75 ne réussissent pas simultanément.
Le compte4457 est explicitement choisi dans ce jeu. Ce vecteur arithmétique ne
qualifie pas l’éligibilité fiscale du service ou d’un dossier réel.

Aucun montant non rapproché n’est présenté comme dette fiscale ou somme à verser.
Les sources et retraits restent conservés après annulation de capture. L’imputation,
la preuve fiscale de paiement et les modèles officiels restent à qualifier.

## Tests réellement exécutés

- Première API/SQL :20réussites78,10s.
- Garde des faits SQL :1échec attendu39,49s avant durcissement,20non sélectionnés ;
  un INSERT direct acceptait une référence inventée avec une empreinte cohérente.
  Après contrôle SQL du snapshot exact :2réussites39,21s,19non sélectionnés.
- Premiers Edge :3réussites53,87s, administrateur1440/comptable390/lecture390.
- Ciblés finaux :**29réussites219,14s**, zéro échec/erreur/ignoré,30avertissements.
  API et SQL natifs : montants non finis/négatifs/sous-centime, sources inadéquates,
  concurrence capture/pièce, refus SQL direct de dépassement et de faits inventés,
  idempotence/retraits, annulation source, cloisonnement/lecteur, PDF et recherche
  littérale. Trois Edge avec téléchargements PDF/logo réellement ouverts.
- Installation103 :**2réussites42,18s** après un import de banc incorrect
  (1échec1,41s avant création de cluster).94SQL distincts,30rejeux,124applications,
  45tables métier vides,80tables antérieures préservées et6nouveaux triggers actifs.
  CLI de schéma/runtime partiel, distinct des parcours applicatifs natifs103.
- Restauration froide incluse dans les29cas :82tables, schéma/données/ACL/séquences
  identiques ; traces actives/retirées, options, PDF/logos et idempotence identiques
  après redémarrage du vrai main:app sous LOGIN non propriétaire. Source préservée
  et cibles supprimées. Les preuves privées antérieures sont restaurées.
- Build Vite :**6,22s**, code0, avertissements XLSX/bundles préexistants.
  Python compilé pour les fichiers backend/tests modifiés.

## Qualification finale, vérifiée à la reprise du21octobre

La première campagne de412cas a donné387réussites et25erreurs de préparation
en2001,54s : quatre fixtures n’étaient pas exposées par le collecteur. Ce
résultat n’était pas une qualification réussie. Le collecteur a été corrigé.
Les deux régressions complémentaires ont d’abord échoué : navigateur sans
`crypto.randomUUID` (55,42s) et société enEUR acceptée à tort (45,73s).
Correction minimale : générateur cryptographique partagé, création de la clé
dans le bloc d’erreur, gardeMAD dans le service et le contrôleSQL103 non livré.
Puis **5cas ciblés réussis en94,74s**, zéro échec/erreur/ignoré.

Commande finale réellement exécutée avec le Python du venv :

```powershell
$env:DATABASE_URL = 'sqlite+pysqlite:///:memory:'
$env:PYTHON_DOTENV_DISABLED = '1'
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py session681_final Test/test_session681_consolidee_isole.py
```

**347cas distincts réussis en1942,84s**,30avertissements, aucun échec, erreur
ou ignoré. Cette campagne bornée reprend la candidate675, les nouveaux bancs
RAS/API/Edge/installation/restauration103 et cinq E2E de balances677/679.
Les72tests de balances déjà qualifiés679 ne sont pas présentés comme tous
réexécutés ici. Les campagnes recouvrantes ne sont pas additionnées.

Les390sources applicatives figées sont identiques avant/après ; témoins de
quatre sociétés, deux fichiers et rapprochements actifs/retirés/PDF inchangés.
LOGIN applicatif non propriétaire, lecture des baselines privées interdite,
application/cluster jetables supprimés. Installation103 :94SQL distincts,
30rejeux,124applications,45tables métier vides,80tables antérieures préservées,
six triggers actifs. Restauration :82tables, schéma/données/ACL/séquences,
PDF/logos/retraits/options/idempotence identiques après redémarrage.
Build final **11,72s, code0** sur ces mêmes sources. Les106fichiers protégés
et69archives antérieures sont inchangés.
[Preuve structurée](PREUVE_SESSION_HORS_RH_681.json).

## Cahier complémentaire fourni dans ce lot

Le complément683 est un document de recette des fonctions677/679/681,
pas une nouvelle fonctionnalité ni une recette humaine effectuée. Word,
PDF21pages, Excel9feuilles et15cas **Non testé**, résultats/anomalies/preuves
vierges ; deux CSV13comptes, donnéesJSON et logo purement fictif sont fournis.
Le guide généralv15 reste conservé.

Commande `lancer_session.py annexe683 Test/test_annexe_balances_ras683.py` :
**4réussites en29,20s**, zéro échec/erreur/ignoré. Les calculs indépendants en
centimes sont confrontés aux vraies API103 : capital100000, achat12000TTC,
cash5250, capture750, versement750, liens300+450/retrait450. Avant/après :
4pièces/9lignes/118000 puis5pièces/11lignes/118750 ; banque94750→94000,
bilan96750→96000, CPC−10000 ; les rapprochements ne changent aucune écriture.
Word contrôlé en OOXML, PDF lisible et première page inspectée ; ouverture
dans Microsoft Word/Excel non effectuée. Capture Edge comptable390 inspectée.
L’utilitaire de rendu PDF a produit l’aperçu puis échoué sur un import de
journal inutile hors cheminPython ; aucune génération ou test n’en dépend.

[Word](../docs/recette/ANNEXE_BALANCES_RAPPROCHEMENTS_20261020.docx),
[PDF](../docs/recette/ANNEXE_BALANCES_RAPPROCHEMENTS_20261020.pdf),
[Excel](../docs/recette/ANNEXE_BALANCES_RAPPROCHEMENTS_20261020.xlsx).

Aucun PostgreSQL réel ni donnée comptable réelle utilisé. Les102anciens SQL,
AGENTS, main/modèles/schémas restent inchangés (106fichiers protégés). RH/paie,
recette humaine et qualification de la production restent différées.

[Mode d’emploi](../docs/RAS_RAPPROCHEMENT_681.md).
