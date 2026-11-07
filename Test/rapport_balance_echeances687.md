# Lot687 — échéances documentaires des balances conservées

Nouvelle fonction de préparation : sélection explicite des comptes de créances
et dettes, montants d’échéance partiels, analyses complémentaires et justification.
Les champs absents restent inconnus et le reliquat non qualifié est visible.
Une nouvelle version immuable conserve les mêmes sources et états, référence
le parent par son empreinte et n’insère aucune écriture ou facture.

La sélection de comptes reprend les B6/B7 existants, sans nouvelle règle fiscale.
Soldes de sens inverse visibles/non ventilables ; sources historiques absentes
non reconstituées ; aucune utilisation du plan ou de factures courantes.
Table071 et protection existantes réutilisées, aucun SQL/modèle/migration changé.
Création sérialisée par société et cléUUID idempotente. Dépassements, montants
non finis/négatifs/sous-centime, doublons, mauvaises sources et mauvais droits
refusés. Analyses complémentaires plafonnées séparément, pas additionnées.

PDF/XLSX et interface relisent les mêmes compléments ; les deux empreintes,
reliquats/inconnus et justifications sont repris, logo/identité hors empreinte.
L’Excel garde les références comme texte, le PDF les échappe. Trois rôles et
largeurs1440/390, rejets422 avec conservation de saisie et réponses réelles
retardées contrôlées. L’interface sélectionne immédiatement la version créée.

## Tests exécutés

- Première API/SQL :17réussites33,66s, zéro échec/erreur/ignoré.
- Premier Edge :1réussite/3échecs47,83s. Le banc ouvrait le fichier temporaire
  Playwright sans extension avec openpyxl. Téléchargement réel sauvegardé avec
  extension avant ouverture :4réussites50,59s, aucun échec/erreur/ignoré.
- Cible complète :27réussites130,37s,30avertissements, zéro échec/erreur/ignoré :
  19API/unitaires,7Edge et1restauration froide. Les trois nouveaux Edge retiennent
  un vraiGET200 puis changent de version, ferment le panneau ou changent le JWT.
- Restauration82tables : schéma/données/ACL/séquences, versions et compléments,
  PDF/XLSX/logos/rejeu identiques après redémarrage du vrai main:app sous LOGIN
  limité. Source préservée et cibles supprimées. L’ancienne preuve privée452
  est restaurée ; preuve687 distincte.
- Build Vite :5,84s, code0. Avertissements XLSX/bundles préexistants conservés.
- Utilitaire de gel initial : importmodels échoué hors cheminbackend avant
  mutation. Correction de l’utilitaire par extractionAST de la seule fonction
  deSHA ;392sources applicatives figées. Ce n’était pas un test produit.

Première campagne commune :93réussites/3échecs213,17s. Le document avait été
régénéré après chargement de son générateur dans le processus, et le collecteur
triait les tests historiques par nom, exécutant l’immutabilité avant la création
des deux versions. Aucun défaut produit n’a été masqué : ordre de définition
restauré, documents/code figés, puis6cas ciblés réussis15,12s. Un huitième Edge
vérifie la saisie de deux comptes avec filtre sans perdre le premier brouillon.

Commande finale réellement exécutée :

```powershell
$env:DATABASE_URL = 'sqlite+pysqlite:///:memory:'
$env:PYTHON_DOTENV_DISABLED = '1'
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py session687_validee Test/test_session687_consolidee_isole.py -x
```

**97cas distincts réussis215,25s**,30avertissements, zéro échec/erreur/ignoré.
Campagne bornée : compléments/API/Edge/restauration, anciens exports et détails
de balances677/679, préparations071 et rapprochements RAS681. Les347cas de la
candidate précédente ne sont pas présentés comme réexécutés ici. Les campagnes
se recouvrent et ne sont pas additionnées.

392sources applicatives et660scriptsTest figés inchangés ; témoin non vide
(écriture validée et lignes, deux versions, compléments et PDF) préservé.
Application/cluster nettoyés,107fichiers protégés et73archives antérieures
inchangés, contenu des archives vérifié. Compilation10Python réussie.
[Preuve structurée](PREUVE_BALANCES_ECHEANCES_687.json).

## Recette et limites

Word/PDF11pages/Excel5feuilles et7cas humains Non testé ; CSV quatre comptes et
JSON/oracle indépendants. D=C9000, actif/passif9000, CPC0 ; B6solde8000,
ventilé2000+1000=3000/reliquat5000 ; B7solde3000/ventilé3000/reliquat0.
Zéro écriture. Interface mobile et page de calcul du PDF inspectées.
Les documents ne sont pas ouverts dans MicrosoftOffice ; recette humaine
et installation cible restent à effectuer, production non validée.

Aucun PostgreSQL réel. Le module ne constitue pas une ETIC officielle complète,
ne calcule pas de nouvelle échéance, ne crée ni archive fiscale ni liquidation.
Matrice globale inchangée ; RH/paie et point6 humain différés.
[Mode d’emploi](../docs/LIASSE_BALANCES_ECHEANCES_687.md).
