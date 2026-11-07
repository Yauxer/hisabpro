# Export Excel d'une archive fiscale

La feuille Synthese affichait le statut finalisé et l'identité, mais perdait la version et l'empreinte déjà disponibles dans l'API, le PDF et l'interface.

Correction minimale dans `LiasseFiscale.jsx` : ajouter Version archive et Empreinte SHA-256 uniquement lorsqu'une archive existe. Ces valeurs proviennent de l'archive figée, sans recalcul depuis les données courantes.

Le test Edge connecté existant a été renforcé : téléchargement réel du XLSX, ouverture avec openpyxl et comparaison exacte de la version 1 et des 64 caractères de l'empreinte renvoyée par la finalisation. Il conserve les contrôles du PDF, du snapshot PostgreSQL, du changement d'identité après archivage et des refus de mutation.

- Avant correction : 1 échec en 19,57 s, absence de la version dans Excel.
- Après correction : E2E archive et connexes liasse/exports : **17 réussis en 21,65 s**, aucun échec ni test ignoré.
- Build Vite : **131 modules, 5,04 s**, code de sortie 0 ; avertissements existants de taille du bundle et d'import XLSX.

Les tests utilisent uniquement PostgreSQL éphémère, FastAPI réel et Edge. Aucune connexion ni donnée réelle. L'empreinte identifie le snapshot archivé ; elle n'est pas une signature du fichier Excel et ne constitue pas un dépôt fiscal.
