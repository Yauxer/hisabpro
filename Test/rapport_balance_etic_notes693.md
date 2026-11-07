# Lot693 — notes documentaires de préparation ETIC

Les préparations indépendantes permettent de conserver des notes par rubrique
du catalogue ETIC existant : À compléter, Note renseignée ou Non applicable
déclaré et justifié. Textes, sources, auteur, date UTC, catalogue et parent sont
figés dans une nouvelle version. Les autres compléments et balances sont
préservés ; aucune écriture ou donnée ETIC comptable n’est modifiée.

Interface multirubrique, droits lecture/admin/comptable, contrôles de contexte
et sélection automatique de la version conservée. PDF/Excel/ZIP reprennent
les notes ; sourceJSON couverte par manifeste, texte échappé et formules Excel
non exécutées. Les retours à la ligne du PDF sont conservés.

## Résultats réellement exécutés

- Reprise691 :10réussites35,47s.
- API/SQL693 ciblés :14réussites34,24s.
- Edge initial :5réussites/1échec77,93s, libellé du bouton de fermeture erroné
  dans le banc. Correction du test puis7réussites50,37s.
- Restauration ciblée :1réussite55,64s,83tables/cinq fichiers.
- Campagne commune initiale :111réussites et1erreur de teardown281,72s.
  La comparaison des exports régénérés incluait leurs métadonnées temporelles.
  Banc corrigé : comparaison des textes/cellules/images, CSV/JSON/pièces exacts
  et notice hors seule date de génération ; chaque octet reste contrôlé par le
  manifeste de son export. Aucun changement applicatif pour cette correction.
- **Campagne finale :111réussites278,64s**, zéro échec/erreur/ignoré,
  30avertissements préexistants. API/PostgreSQL natif et Edge réels, y compris
  POST tardif après changement de version, trois rôles et largeurs1440/390.
- Build Vite :**5,59s**, code0. **10Python compilés**.

Les campagnes recouvrantes ne sont pas additionnées. La finale couvre les
balances conservées, le détail du bilan, échéances687, dossiers689,
justificatifs691, notes693 et restauration froide sur bases nonce exclusivement.
1 065empreintes de sources et scripts figées et vérifiées. Témoin indépendant :
capital333validé, versions, notes, sourcePDF, logo et exports inchangés.
Schéma/données/ACL/séquences et octets des cinq fichiers conservés après
restauration, source préservée et cibles supprimées.108fichiers SQL/bootstrap
préservés ; aucune nouvelle migration. ZIP691 et cumul antérieurs intacts.

Commandes finales : Python du venv avec dotenv désactivé et URLSQLite de
collecte inoffensive ; fixtures exclusivement PostgreSQL isolé :

```powershell
hisabpro-backend\.venv\Scripts\python.exe -X utf8 -u .codex-tests/lancer_session.py notes693_commune_final Test/test_session693_balances_isole.py -x -vv
npm run build
```

## Documents et limites

[Mode d’emploi](../docs/LIASSE_BALANCES_NOTES_ETIC_693.md), Word/PDF4pages,
Excel5feuilles et cinq cas humains Non testé. OOXML/XML/CRC, tous les identifiants
PDF, statuts/formules/listes et cellules de résultats vierges contrôlés. Première
génération arrêtée faute dateVersion et codes PDF trop étroits détectés puis
corrigés ; version finale contrôlée et page de recette inspectée. MicrosoftOffice
non ouvert. Capture mobile Edge inspectée, sans débordement horizontal.

Les pièces jointes restent propres à leur version et ne sont pas copiées vers
les nouvelles versions. Une note ne prouve pas l’existence ou la valeur d’un
justificatif cité. Les tableaux chiffrés ETIC, le financement et les compléments
fiscaux ne sont pas réputés complets. RH/paie et point6 humain restent différés.
Aucun PostgreSQL réel, aucune recette humaine ou production déclarée validée.

[Preuve structurée](PREUVE_NOTES_ETIC_693.json).
