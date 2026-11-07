# Lot689 — dossier de préparation de balances partageable

Un téléchargement regroupe une seule version contrôlée : donnéesJSON,
PDF/XLSX avec logo actuel, balances normalisées disponibles, complément687
éventuel, identité d’export, notice et manifesteSHA-256. Noms d’entrées fixes,
aucun chemin d’import utilisé. SourcesN-1 absentes non fabriquées ; anciennes
sources détaillées absentes et logo historique incompatible signalés.

Le manifeste contrôle la liste, taille et empreinte de chaque autre fichier.
Il ne s’auto-hache pas et ne constitue pas une signature ou certification.
Le téléchargement est une lecture : aucune écriture, préparation supplémentaire,
archive fiscale définitive ni donnée de dépôt créée. Les autres sociétés restent
inaccessibles et le rôleLecture exporte. Réponse HTTP sans cache ; téléchargement
tardif ignoré après changement de JWT ou démontage/changement de version.

## Tests réellement exécutés

- API :5réussites29,35s, zéro échec/erreur/ignoré. N/N-1, compléments, CRC,
  manifeste de chaque fichier, snapshot et empreinte, CSVexact, PDF/XLSX/logos,
  droitsLecture/cloisonnement, anciennes sources absentes et empreinte altérée.
- Edge :4réussites39,88s, trois rôles et largeurs1440/390, ZIP réellement
  téléchargé, ouvert et contrôlé ; aucune mutation HTTP ou comptable. Un vrai
  ZIP200 retenu puis libéré après changementJWT n’est pas téléchargé.
- Restauration froide :1réussite56,80s,82tables, schéma/données/ACL/séquences
  identiques, source préservée/cibles supprimées. ZIP reconstitué et chaque
  manifeste vérifié ; sources, données, valeursExcel, textesPDF et images
  identiques après redémarrage natif sous LOGIN limité. Pas d’égalité binaire
  PDF/XLSX présumée : leurs dates techniques peuvent varier. Anciennes preuves
  privées452/687 restaurées, nouvelle preuve689 distincte.
- Finale :**46cas distincts réussis137,87s**,30avertissements, zéro échec,
  erreur ou ignoré. Dossier/API/Edge, huit Edge687, exports/détails677/679 et
  cinq Edge/RAS681 connexes. Campagnes recouvrantes non additionnées ; aucune
  réexécution globale des347ou97cas antérieurs revendiquée.
- Build :**4,72s**, code0 ; avertissements préexistants XLSX/bundles conservés.
  **7Python compilés**,393sources applicatives et664scriptsTest figés inchangés.
  Témoin non vide (écriture validée et lignes, deux versions, sources, dossier,
  valeurs/rendus/logos) conservé.107fichiers protégés et75archives antérieures
  inchangés, leurs contenus/manifeste/CRC contrôlés ; cibles/applications nettoyées.

Commande finale avec Python du venv et collecte inoffensive :

```powershell
$env:DATABASE_URL = 'sqlite+pysqlite:///:memory:'
$env:PYTHON_DOTENV_DISABLED = '1'
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py session689_validee Test/test_session689_consolidee_isole.py -x
```

[Preuve structurée](PREUVE_DOSSIER_BALANCES_689.json).

## Mode d’emploi et limites

Word/PDF6pages/Excel4feuilles avec deux cas humains Non testé ; résultats,
anomalies et preuves réelles vierges. OOXML/XML/CRC, PDF, formules/listesExcel
et blancs réellement vérifiés ; pagePDF et interface mobile inspectées.
MicrosoftOffice non ouvert. Le générateur est fourni avec sa sourceMD.

Deux utilitaires documentaires ad hoc ont échoué sur des littéraux accentués
mal encodés dans le pipe PowerShell ; générateur sauvegardé enUTF8, génération
et vérification réexécutées avec succès. Trois ajouts précédents de la matrice
avaient subi le même remplacement d’accents : texte corrigé sans changer les
statuts ni les archives historiques. Aucun défaut produit contourné.

Aucun PostgreSQL réel ni nouveauSQL. La préparation ne remplace pas la liasse
officielle complète, son ETIC, financement ou fiscalité. RAS/EDI restent soumis
aux modèles manquants. RH/paie, recette humaine et qualification de production
restent différées. [Mode d’emploi](../docs/LIASSE_BALANCES_DOSSIER_689.md).
