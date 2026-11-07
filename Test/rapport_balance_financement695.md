# Lot695 — financement documentaire indépendant

Les préparations depuis balances permettent désormais de saisir et justifier
les16flux N/N-1, puis conserver une nouvelle version avec ses calculs figés.
Les masses sont issues du moteur existant, jamais les flux bruts supposés
depuis leurs variations. Les cellules vides restent inconnues ; chaque zéro est
une déclaration explicite justifiée. La CAF doit recouper l’ESG figé.

La partie emplois/ressources reste indisponible tant que les flux et la CAF
nécessaires ne sont pas connus. Sans balance N-1, pas de rapprochement N ;
sans N-2, aucun rapprochement N-1 présumé. Les totaux N-1 utilisent les seules
rubriques mères, sans doubler les sous-postes. Les écarts restent visibles et
ne sont pas automatiquement compensés. L’indicateur `ecart_nul` est strictement
mathématique, distinct du seuil historique1MAD du moteur partagé.

Auteur/date/source et libellés figés ; autres compléments inchangés, pièces
propres à leur version. Droits lecture/admin/comptable, isolation société,
rejeu UUID, concurrence et abandon de réponses hors contexte. PDF/Excel/ZIP
avec logo et JSON financier couvert par manifeste. Textes échappés, aucune
formule issue d’une saisie exécutée. Aucune migration ni écriture créée ; moteur
comptable existant et SQL historiques inchangés.

## Résultats exécutés

- API initiale :17réussites62,43s.
- Edge initial :1échec46,80s. Les agrégats numériques étaient passés au formateur
  de chaînes exactes : CAF et totaux affichaient À vérifier. Conversion de type
  corrigée dans le panneau et assertions alignées sur le format existant
  `11.000,00 MAD`.
- Candidate suivante :26réussites210,27s,18API,7Edge et restauration froide.
- Ajouts finaux : totaux N-1, écart strict, cas50centimes, POST réel tardif,
  saisieN-1 dans Edge et garde-fou de précision : au-delà de la borne technique,
  détails exacts conservés et aucun total approximatif présenté.
- **Campagne du périmètre finale :138réussites536,37s**, zéro échec/erreur/ignoré,
  30avertissements préexistants. Inclut balances, échéances, notesETIC, pièces,
  dossiers, trois rôles Edge et restauration froide83tables/cinq fichiers.
- **Moteur comptable partagé :24réussites0,88s** (patches051/052).
- **Build final :6,07s**, code0. Build initial6,48s conservé dans les preuves.

Campagnes recouvrantes non additionnées. L’oracle indépendant vérifie CAF2000,
ressources11000, emplois4000, variationsFR7000/BFG3000/trésorerie4000 et écarts0.
Distribution supplémentaire1000 : ressources10000 et écart−1000 visibles.
Les tests vérifient aussi les non-finis, nombres négatifs, précision, sources
absentes, CAF inconnue après clôture technique, métadonnées et valeurs Excel,
PDF/logos et octets réels du ZIP, schéma/données/ACL/séquences après restauration.

## Campagne annuelle complémentaire

**347réussites1810,38s** (30min10s), zéro échec/erreur/ignoré et30avertissements,
code0. `financement695_annuel`, socle connecté681, est exécuté sur les mêmes
sources figées que la campagne138. Les témoins des factures intersociétés,
RAS, retraits, justificatifs et PDF sont intacts. La recette annuelle connectée
stock/paiements/lettrage/TVA/immobilisations/clôture/à-nouveaux passe, ainsi que
le scénario dégressif et les bancs d’installation/restauration103.

**1 071empreintes** de sources et scripts vérifiées, **10Python compilés**,
**108SQL/bootstrap préservés**, moteur partagé inchangé. Restauration104 du
périmètre :83tables/cinq fichiers, données/schéma/ACL/séquences et octets/rendus/
logos/sources identiques ; cibles supprimées et source préservée. Clusters et
applications des deux campagnes nettoyés. Processus PostgreSQL6028 et Node20040
de l’utilisateur préservés, sans connexion à sa base.

Commandes réellement exécutées (Python du venv, dotenv désactivé et URLSQLite
de collecte inoffensive ; fixturesPostgreSQL nonce, jamais la base utilisateur) :

```powershell
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py financement695_commune Test/test_session695_balances_financement_isole.py -x -vv
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py financement695_moteur Test/test_patch051_compta_audit_critique.py Test/test_patch052_conformite_normative.py -x
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py financement695_annuel Test/test_session681_consolidee_isole.py -x -vv
npm run build
```

Les trois campagnes sont rapportées séparément, sans total de cas uniques
inventé. Les durées console ci-dessus et duréesJUnit sont distinguées dans la
[preuve structurée](PREUVE_FINANCEMENT_695.json). Les preuves privées historiques
remplacées par les tests sont sauvegardées puis restaurées après capture de
la preuve propre695. Les ZIP693 et cumul antérieurs restent intacts.

## Recette utilisateur et limites

[Mode d’emploi](../docs/LIASSE_BALANCES_FINANCEMENT_695.md) Word/PDF6pages,
Excel6feuilles, six cas humains Non testé. Deux balancesCSV,16fluxCSV et
JSON/oracle exacts sont fournis. OOXML/XML/CRC, identifiantsPDF, feuilles,
statuts/formules/listes et blancs de résultats contrôlés ; page de recette
inspectée. MicrosoftOffice non ouvert. Sources normatives consultées et limites
d’accès consignées [ici](../docs/audit/SOURCES_FINANCEMENT_20261021_695.md).

Aucun PostgreSQL réel ou donnée comptable réelle modifié. Les saisies restent
des déclarations documentaires à vérifier contre leurs pièces. ETIC structurée,
fiscalité/annexes et formats officiels restent partiels ou bloqués ; RH/paie et
point6 humain différés. Recette utilisateur et production non validées.
