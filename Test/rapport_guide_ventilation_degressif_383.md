# Mode d'emploi version 12 — lot 383

Fiches 05 et 11 actualisées sans réécrire les autres parcours : annulation collective native, règlements de factures d'un exercice précédent, et dégressif cinq ans avec oracle indépendant. Les trois variantes utilisent des dossiers fictifs distincts. Les limites « instrument bancaire unique », « rapprochement à une ligne » et « historiques ambigus » restent explicites.

La fiche d'annulation contrôle deux factures 120/240, deux paiements 120/120, quatre originaux/dix lignes équilibrés à 600 MAD puis deux contrepassations : six pièces/quatorze lignes équilibrées à 840 MAD. Les originaux sont conservés.

## Contrôles documentaires exécutés

- `docs/guide/generer_guide.py` : code 0, **439 blocs**.
- DOCX : **9 entrées**, CRC, tous XML/relations internes parsés et résolus ; contenu des nouvelles variantes présent.
- PDF : **30 pages**, texte présent sur chacune, nouvelles variantes retrouvées, tous les blocs textuels dans les limites physiques des pages.
- Deux rendus PDF inspectés visuellement, pages 10 et 20 : texte lisible et tableau du dégressif visible sans troncature.
- **18 fiches**, tableau de **17 statuts Non testé** conservé. Aucun résultat humain prérempli.

Le premier choix de page de rendu dégressif sélectionnait la page d'introduction ; sa correction de critère a produit un `StopIteration` dans le script de contrôle temporaire. Le critère a ensuite été corrigé et le contrôle final repasse avec code 0. Aucun défaut du Word/PDF ni changement métier.

Le DOCX n'a pas été ouvert dans Microsoft Word ici. La recette humaine, la qualification réglementaire et la mise en production restent non validées. Le point 6 est laissé en attente à la demande de l'utilisateur. Générer le guide n'exécute aucun test métier et ne touche à aucune base.
