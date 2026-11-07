# Fiscalité salariale — contrôle annuel IR

**Personnel & Paie → 05 · Fiscalité salariale** permet de conserver un contrôle arithmétique annuel du barème général2026 sur un revenu net imposable déclaré. Le résultat n’est ni une retenue mensuelle, ni un montant à déclarer, ni un net à payer.

## Installation et accès

Faire installer la migration additive `hisabpro-backend/118_paie_controles_ir_annuels.sql` après le socle paie, **sur une copie isolée et restaurable**. L’installation réelle chez l’utilisateur n’a pas été effectuée. Les barèmes et taux historiques ne sont ni remplacés, ni corrigés silencieusement ; les snapshots du brut et du social restent inchangés.

Personnel doit être actif et protégé. Identité et rémunération sont nécessaires à la lecture ; proposer est requis pour conserver un calcul. Le profil Personnel seul reste isolé des factures, écritures et autres modules financiers. Ce contrôle pédagogique ne nécessite aucune approbation définitive de paie et ne remplace pas celle des étapes futures.

## Utilisation

1. Ouvrir **Consulter le barème et ses sources** pour voir le millésime disponible, les tranches et références. L’année2026 est la seule traitée par ce nouveau contrôle ; aucun repli d’une autre année n’est effectué.
2. Cliquer **Nouveau contrôle annuel IR**. Saisir le **revenu net imposable annuel déjà établi**, après les déductions justifiées. Ne pas saisir un brut mensuel ni une somme annualisée sans source. Le logiciel ne calcule pas encore cette assiette depuis les campagnes.
3. Renseigner la référence du contrôle du RNI et confirmer que le barème général est applicable. Les taux spécifiques ou exonérations particulières ne sont pas traités dans cette étape.
4. Choisir le nombre de personnes fiscalement éligibles **retenues pour la réduction**, de0 à6, avec une référence et confirmation du contrôle. Ce champ ne décrit pas tous les membres du foyer ; ne pas le déduire automatiquement du nombre d’enfants. Laisser **Inconnu** si la vérification manque. Une déclaration de0 doit elle aussi être contrôlée.
5. Saisir le motif, confirmer le mode arithmétique, puis **Calculer et conserver le contrôle**. Les informations manquantes génèrent un résultat incomplet explicite, sans remplacer une inconnue par0.
6. Relire le détail progressif par tranche, la réduction théorique et celle réellement appliquée. Le résultat exact comporte **quatre décimales** : il précède les arrondis de liquidation, qui ne sont pas qualifiés ici. Montant à déclarer, retenue mensuelle et net restent **Non déterminé / Non calculés**.
7. Réouvrir un ancien contrôle depuis la liste. Il conserve son revenu déclaré, ses références, sources, acteur et empreinte, sans recalcul à la consultation. Un nouveau contrôle volontaire crée un autre snapshot ; la reprise de la même requête est idempotente.

Exemple entièrement fictif : RNI200000.00, deux personnes éligibles confirmées → impôt progressif avant réduction46600.0000, réduction théorique1200.00, résultat arithmétique45400.0000. Pour RNI41000.00 et six personnes retenues, l’impôt avant réduction est100.0000 ; la réduction appliquée est limitée à100.0000 et ne crée pas un crédit fictif. Ces exemples ne sont pas des montants de déclaration à utiliser tels quels.

## Recette et suite

[PDF six cas](RECETTE_IR_ANNUEL_PAIE_901.pdf), [Excel](SUIVI_IR_ANNUEL_PAIE_901.xlsx), [jeu exact](JEU_IR_ANNUEL_PAIE_901.json), [sources et limites](SOURCES_IR_ANNUEL_901.md). Tous les statuts humains sont **Non testé**. Aucun PostgreSQL réel n’a été contacté.

Le module fiscal complet reste **partiel** : assiette automatique reliée au brut/social, frais professionnels et déductibilité, retenues mensuelles, régularisations, net, bulletins et validation définitive restent à poursuivre selon le master. Le contrôle annuel901 ne les présente pas comme développés ni testables.
