# Reprise après les compléments B11 et B1

B11 est livré dans703 et B1 dans705. Le dépôt et le dernier événement du journal
restent la source de vérité ; ne pas les réappliquer depuis la note historique701.
RH/paie et point6 humain restent différés.

## Détails certains à examiner ensuite

Le B4 du catalogue existant détaille les soldes des comptes251. Les balances
conservées peuvent fournir ces soldes signés et leur comparatif, sans lire le
Journal ou le plan actuels. Elles ne fournissent ni identité de l’émetteur,
capital, quote-part détenue ou produits reçus. Ces informations doivent rester
à compléter, ou être explicitement sourcées et conservées séparément.
La rubrique financière24/25 du bilan mélange plusieurs postes : ne pas la
présenter comme un agrégat strictement comparable au seul251, ni fabriquer
un écart trompeur avec cette rubrique plus large.

B2/B2bis/B3/B5 exigent une revue des sources de mouvements. N/N-1 permettent
des soldes de clôture, sans déduire acquisitions, cessions, amortissements sortis,
dotations/reprises ou utilisations de provisions. Définir les données explicites
et leur traçabilité avant toute automatisation. Les sources manquantes ne sont
pas reconstituées depuis la comptabilité réelle de la société active.

B12/B13/B14 et C3 nécessitent leurs sources fiscales ou historiques propres.
Ne pas brancher les calculs IS/TVA du Journal courant sur une balance externe.
Tout nouveau taux ou traitement obligatoire nécessite une source officielle.
Les spécifications RAS/EDI restent une question distincte déjà documentée ;
ne pas inventer un schéma officiel pour débloquer le mode indépendant.

## Invariants à conserver

- Sources exactes : contenu.sources.n/n1 en chaînes décimales, pas preparation.soldes flottant.
- B11 indisponible après solde technique119 ; B1 reste disponible si ses sources le sont.
- Montants manquants distincts de0, soldes inverses signés et écarts visibles.
- B1 : brut21, amortissements281 groupés, aucune allocation par compte21 présumée.
- Référence du CPC/bilan déjà figée ; lecture, PDF, Excel et ZIP sans recalcul historique.
- Nouvelle version pour figer un calcul ; empreinte parent, UUID/rejeu, droits et société contrôlés.
- Pièces propres à leur version ; autres compléments conservés, logo actuel hors empreinte.
- La consultation B1/B11 est partagée dans BalancePreparationDetailAutomatique.jsx ; leurs moteurs restent distincts.

## Contrôles de reprise

Lire AGENTS.md, le journal complet et son état, inspecter les processus et les
ZIPs récents avant de relancer une commande. Les scripts de finalisation703/705
terminés ne doivent pas être rejoués : ils écrivent les preuves et les archives.
Les rapports et preuves publics distinguent les campagnes finales des essais
initiaux et de l’échec du helper navigateur705. Les campagnes se recouvrent.

Le ZIP de session703/705 ne contient que les changements de cette exécution.
Le cumulatif645/705 conserve aussi les livraisons antérieures de continuité.
Les deux sont différentiels. Recette utilisateur, ouverture Office et installation
cible restent à vérifier ; aucun test isolé ne prouve une mise en production
ou une conformité réglementaire officielle.
