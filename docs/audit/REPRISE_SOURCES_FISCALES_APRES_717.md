# Reprise après les compléments707–715 : sources fiscales et historiques autonomes

Lire le journal actif, vérifier les ZIPs/proofs et processus avant toute reprise.
707/709/711/713/715 sont des compléments distincts des préparations depuis
balances. Ne pas les réappliquer. RH/paie et point6 humain restent différés.
Le cahier717 consolide leur utilisation sans valider une recette utilisateur.

## Zone à traiter et dépendances vérifiées dans le dépôt

La recherche dans services/balance_*.py ne retrouve pas de moteur structuré
B12/B13/B14/C3 indépendant ; les notes693 peuvent documenter les rubriques,
mais ne remplacent pas leurs données et contrôles. balance_import_service
conserve explicitement les limites Retraitements/liquidation/annexes et EDI.
Ne pas assimiler cette absence du mode indépendant à une absence du module
fiscal comptable normal, qui dispose déjà de ses moteurs et snapshots.

etic_service._automatiques construit actuellement B12 en appelant
routers.fiscalite.situation_is sur la comptabilité du sid/exercice courant.
Il distingue résultat net comptable, réintégrations dont IS comptabilisé,
déductions, résultat fiscal avant déficits, déficits imputés et bénéfice taxable.
Ce raccord au Journal courant ne doit pas être réutilisé tel quel pour une
balance externe. Prévoir un contexte documentaire explicite et ses propres
sources avant toute liquidation autonome, sans dupliquer les règles fiscales.

B13 utilise les soldes71/73 moins61/63 et les impôts67. Le code existant précise
que l’affectation des impôts entre courant/non courant peut nécessiter une
donnée extra-comptable. Les montants comptables certains peuvent être repris
des sources exactes ; ne pas qualifier une ventilation inconnue par défaut.

_section_b14 reconstitue ouverture/opérations/déclarations/clôture à partir
des mouvements AN,TV et autres journaux des comptes4455/34551/34552. Les seules
balances N/N-1 ne fournissent pas ces flux ou les déclarations effectivement
déposées. Conserver les données explicites et leurs références ; ne pas appeler
le Journal TVA de la société active pour compléter une balance indépendante.

_calcul_c3_depuis_soldes fournit les indicateurs comptables ; _section_c3 lit
trois exercices du Journal et compte les employés actifs pour l’effectif courant.
Dans une préparation N/N-1, N-2 et l’effectif restent inconnus sans source
explicite. La formule de situation nette existante ajoute le résultat au solde
11/13 car sa source exclut la clôture technique : ne pas l’appliquer aveuglément
à une balance externe déjà soldée119. Réutiliser la garde119 du détail B11
et vérifier chaque périmètre, sans double compter un résultat technique.

## Ordre proposé pour la prochaine intervention fonctionnelle

1. Examiner les données certaines de B13/C3 dans les seuls snapshots/sources
   exactes N/N-1 ; laisser N-2, effectif et autres informations non fournies
   indisponibles. Définir la saisie historique explicitement sourcée avant de
   rendre C3 complet, sans réintroduire RH/paie dans ce périmètre.
2. Définir les retraitements et déficits/crédits/acompte propres au dossier
   externe pour B12, avec sources/auteur/version et snapshot cohérent. Vérifier
   les textes officiels applicables avant toute règle nouvelle ou modification.
3. Structurer les flux et déclarations TVA explicitement sourcés pour B14 ;
   ne pas confondre mouvements comptables et déclarations réellement déposées.
4. Reprendre ensuite les contrôles de complétude du mode indépendant, sans
   activer Prêt à déposer tant que ses sources et spécifications manquent.

## Invariants et preuves à conserver

Calculs Decimal depuis contenu.sources.n/n1, inconnus distincts de0, signes
inverses et écarts visibles ; aucun flux inventé depuis une variation de solde.
Nouvelle version, SHAparent, UUID/rejeu avant calcul, droits/société/MAD,
provenance figée et contrôles historiques sans recalcul au GET/exports.
Ne pas modifier les écritures validées ou réparer arbitrairement les anciennes
anomalies FEC/ETIC. Aucune connexion à la base réelle pour ces développements.
Tests natifs nonce et Edge, exports/logo/manifeste et restauration froide,
guide humain Word/PDF/Excel et ZIP différentiel vérifié par étape.
Les spécifications RAS/EDI déjà bloquées sont un sujet séparé : ne pas inventer
un schéma officiel. Recette humaine et production restent nonvalidées.
