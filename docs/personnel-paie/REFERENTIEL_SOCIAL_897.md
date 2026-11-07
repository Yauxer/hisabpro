# Charges sociales — référentiel versionné

Le menu **Personnel & Paie → 04 · Charges sociales** permet de préparer les branches sociales par société et par régime. Ce lot conserve les paramètres et leur historique ; il ne calcule pas encore les cotisations d’une campagne. Il ne crée ni bulletin, ni paiement, ni écriture comptable.

## Installation et accès

Faire installer la migration additive `hisabpro-backend/116_paie_referentiel_social.sql` **sur une copie isolée et restaurable**, après le socle Personnel et les migrations113 à115. Les migrations précédentes restent inchangées. Aucun script n’a été exécuté sur la base réelle de l’utilisateur. La migration est rejouable, sans taux préchargé ni habilitation attribuée automatiquement.

Activer Personnel et son mode protégé. La lecture exige les habilitations identité et rémunération. La proposition exige `personnel.proposer`, la décision `personnel.approuver`. La qualification d’une règle déclarée validée exige en plus `personnel.valider_regles_paie` et une confirmation explicite du contrôle. Le profil Personnel seul reste isolé de la facturation/comptabilité.

## Utilisation

1. **Créer une branche** : définir un code de régime et un code de branche stables, un organisme et les conditions d’applicabilité. Aucun régime n’est affecté automatiquement à un salarié.
2. Indiquer l’applicabilité : **À vérifier** reste une inconnue ; **Non applicable** exige une justification et ne porte aucun taux ou forfait. Ne pas l’utiliser pour faire disparaître une anomalie.
3. Choisir un calcul par taux ou forfait. Les taux sont exprimés en **pourcentage** : saisir `1.234567` pour1,234567 %, jamais une fraction implicite. Les parts salariale et patronale sont indépendantes ; saisir explicitement `0` si une part nulle est justifiée. Un champ vide reste inconnu.
4. Pour un taux, déclarer l’assiette CNSS, AMO ou brut et le plafond éventuel avec son unité. Un plafond annuel ou journalier n’est pas automatiquement transformé en plafond mensuel. Les forfaits ne combinent pas assiette et plafond.
5. Renseigner les **composants couverts** avec des codes stables, séparés par des virgules. Par exemple, une branche regroupant deux garanties déclare leurs deux codes. Une autre branche du même régime ne pourra pas couvrir la même garantie sur une période commune. Les codes sont déclaratifs : le logiciel ne peut pas reconnaître deux synonymes arbitraires saisis par un utilisateur.
6. Déclarer les dates d’effet et la source. La qualification initiale reste **À vérifier**. Une qualification **Validée après contrôle humain** exige référence, texte/convention, empreinte SHA-256 et date de consultation. Une source réglementaire exige aussi article et URL HTTPS officielle. Une convention contractuelle n’est pas assimilée à un texte de loi. L’empreinte est déclarée ; aucun téléchargement ou contrôle matériel de la preuve n’est effectué par le serveur.
7. Enregistrer puis **Consulter** la branche. La proposition apparaît immédiatement et conserve son auteur. Un autre décideur habilité peut l’approuver ou la rejeter avec motif et référence. Le préparateur ne peut pas approuver sa propre proposition. Une approbation conserve la version sans certifier la conformité.
8. **Proposer une nouvelle version** pour tout changement. La date est volontairement laissée vide. Après une première approbation, la suivante doit commencer dans le futur et après la dernière version approuvée. Les anciens contenus restent inchangés. Le filtre de date montre la version réellement applicable ; une version expirée ne réactive pas une version antérieure.

Les contrôles de composition comparent les intervalles entiers et tiennent compte des changements de version. Une proposition conflictuelle peut être conservée pour examen, mais son approbation est bloquée. Les autres sociétés et régimes sont des périmètres distincts ; cela ne constitue pas une preuve d’éligibilité d’un salarié.

## Recette

Le [cahier PDF](RECETTE_SOCIAL_PAIE_897.pdf), le [classeur Excel](SUIVI_SOCIAL_PAIE_897.xlsx) et le [jeu exact](JEU_SOCIAL_PAIE_897.json) fournissent six cas consécutifs. Les données sont entièrement fictives ; tous les statuts humains restent **Non testé**. Les preuves automatisées sont consignées séparément dans `Test/PREUVE_PAIE_897.json`.

## Sources et limites

Le28/10/2026, les documents officiels [ACAPS AMO](https://www.acaps.ma/fr/grand-public/sante/couverture-medicale-de-base-amo) et [décret2-01-2723 publié par l’ACAPS](https://www.acaps.ma/sites/default/files/publication_documents/decret_ndeg_2-01-2723.pdf) ont été ouverts à nouveau. Ils décrivent des branches et populations distinctes ; le décret disponible cite des modifications historiques. Ils ne suffisent pas, seuls, à qualifier tous les taux et dates d’effet pour chaque salarié en2026. Aucun taux issu de ces lectures n’est automatiquement activé.

Le [plan3B](PREPARATION_COTISATIONS_3B_895.md) conserve les autres références et leurs limites. La suite est le calcul social séparé, sur sources explicites et snapshot du brut, puis l’IR et les bulletins. La recette utilisateur, les règles réglementaires applicables et le déploiement en production restent à valider humainement.
