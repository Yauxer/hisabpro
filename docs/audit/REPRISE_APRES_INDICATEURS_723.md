# Reprise après les projections indépendantes B13 et C3

Vérifier journal, processus, derniers ZIPs et preuves avant de poursuivre.
Ne pas réappliquer721/723. RH/paie et point6 humain restent différés.

## Présent dans le code

B13 : synthèses fiscales documentaires sourcées, courant exact, compte67
distinct de l’impôt théorique déclaré, inconnus et versions conservés.
C3 : moteur comptable partagé en Decimal exact, N/N-1 et comparatifs aux états
figés ; N-2/extra-comptable indisponibles, aucun Journal/RH repris.
Garde119 commune B11/B13/C3 ; anciennes versions figées non réparées
automatiquement. Le nouveau calcul B11 refuse le faux0 historique sans drapeau
CPC, et C3 ne compte pas deux fois le résultat déjà soldé en119.

Les guides721/723 sont deux jeux fictifs distincts. Leur recette humaine reste
à effectuer. Les derniers tests exécutés et leurs limites sont dans les rapports.

## Prochaines interventions fonctionnelles

1. B12 : définir le contexte fiscal propre aux balances externes. Ne pas appeler
   `routers.fiscalite.situation_is`, qui interroge le Journal/modules de la société.
   Réutiliser les moteurs purs, dont `fiscalite_is_service.calculer_is`, après
   vérification des textes officiels applicables à toute règle nouvelle/modifiée.
   Distinguer résultat net comptable, impôt déjà comptabilisé, réintégrations,
   déductions, déficits par millésime, bénéfice taxable, IS/CM/CSS, crédits,
   acomptes et solde. Les paramètres/données absents ne deviennent pas les
   valeurs par défaut d’une liquidation. Aucun automatisme fiscal fondé sur
   de simples probabilités ou sur des pièces manquantes.
2. B14 : structurer des flux et références de déclarations explicitement sourcés.
   Une variation des soldes4455/34551/34552 ne prouve pas les flux, et le
   journalTV ne prouve pas un dépôt. Conserver ouvertures, opérations,
   déclarations et clôtures séparées ; écarts visibles, inconnus préservés.
3. Complétude : C3 nécessite encore N-2 et des données extra-comptables
   explicitement documentées. Les notes/pièces existantes peuvent les conserver,
   mais ne les injectent pas automatiquement dans les indicateurs. Ne pas
   afficher un C3 réglementaire complet ou Prêt à déposer tant qu’elles manquent.

Conserver les règles communes : nouvelle version, SHAparent, UUID/rejeu avant
calcul financier, auteur/UTC/source/méthode figés, droits/société/MAD, nombres
exacts et exports/logo/manifeste. Tester PostgreSQL natif nonce et navigateur,
restauration et cohabitation avec les autres compléments, sans base réelle.

RAS/EDI officiel, justificatifs historiques FEC/ETIC manquants, recette
utilisateur, installation cible et production sont des sujets distincts.
Ne pas inventer un schéma de dépôt ou réparer une écriture validée pour
faire disparaître une anomalie. Conserver les statuts de couverture honnêtes.
