# Calcul social connecté au brut

Le parcours est désormais **03 · Traitement de la paie → résultat du brut → Préparer les cotisations de ce brut → 04 · Charges sociales → Simulations sociales**. Il conserve des calculs pédagogiques par salarié et par branche, avec leurs paramètres et sources. Il ne valide aucune paie définitive et ne produit ni IR, ni net bancaire, ni bulletin, ni paiement, ni écriture.

## Prérequis

Faire installer `hisabpro-backend/117_paie_simulations_sociales.sql` après115/116 **sur une copie isolée et restaurable**. La migration ajoute une table et un index d’intégrité pour rattacher les snapshots à la société du brut. Les migrations précédentes et les données existantes ne sont pas réécrites. Aucune installation n’a été faite sur la base réelle de l’utilisateur.

Personnel doit être actif et protégé. La lecture exige identité et rémunération ; le calcul exige aussi proposer. Les paramètres du régime doivent être approuvés dans le référentiel897. Leur qualification réglementaire reste un contrôle humain distinct ; une approbation technique ne certifie pas les règles.

## Utilisation

1. Préparer les dossiers, contrats, salaires et variables approuvées. Dans **Traitement de la paie**, conserver une simulation du brut pour la sélection et le mois souhaités.
2. Depuis son résultat, cliquer **Préparer les cotisations de ce brut**, puis **Nouvelle simulation sociale**. L’identifiant du brut est prérempli par le lien ; **Charger le brut** permet de relire sa sélection. Un autre identifiant doit être chargé explicitement avant le calcul.
3. Choisir le régime applicable à toute cette sélection **après contrôle de l’éligibilité**. Aucun régime n’est affecté automatiquement aux salariés. Pour des régimes différents, préparer des sélections de brut distinctes.
4. Pour chaque salarié, déclarer les **parts soumises de la base salariale seule** pour CNSS et AMO. Exemple fictif : pour une base9000.10 et un gain800.01, ne pas saisir9800.11 comme part de base. Le logiciel ajoute les gains selon les règles conservées des variables. Un champ vide reste inconnu ; un montant0 est une déclaration explicite à justifier.
5. Renseigner la référence du contrôle et confirmer le régime, les parts renseignées et les conditions des rubriques. Cette confirmation ne remplit aucun champ vide et ne remplace pas une preuve matérielle. En l’absence de confirmation ou de référence, les branches restent bloquées.
6. Saisir le motif, confirmer le **mode pédagogique**, puis **Calculer et conserver**. Les taux en pourcentage et les forfaits proviennent uniquement des versions approuvées du régime choisi. Les arrondis se font au centime, séparément par branche et payeur, avant totalisation.
7. Relire les assiettes avant et après plafond, les parts salariale et patronale et les anomalies. Les **Paramètres et sources conservés** permettent de retrouver les versions utilisées. La liste affiche toutes les simulations, les plus récentes en premier ; **Consulter** rouvre un snapshot sans le recalculer.

## Contrôles et limites

- Le brut est comparé aux sources courantes au moment du calcul : contrat, salaire et variables, y compris celles encore en attente. Une différence bloque le salarié ; créer un nouveau brut après traitement des sources, sans modifier l’ancien.
- Toutes les branches déclarées dans le régime sont prises en compte. Un régime vide ou une branche sans version approuvée couvrant le mois ne devient pas une cotisation nulle. Un changement de version dans le mois est signalé ; aucun taux moyen n’est inventé.
- Les assiettes CNSS et AMO sont séparées. Les exclusions des gains précèdent le plafond de la branche. Les plafonds d’exonération **mensuels** sont cumulés par salarié et rubrique sur les variables du mois ; ils ne sont pas répétés pour chaque variable. Plusieurs versions concurrentes d’une même rubrique mensuelle sont bloquantes.
- Les plafonds à l’opération sont appliqués à l’opération ; les unités annuelles/journalières restent bloquées faute de cumul ou de jours. Aucun plafond annuel divisé par12 implicitement. Les proratas, régularisations annuelles, cas particuliers et autres assiettes contractuelles complexes restent à traiter dans les lots suivants.
- Une assiette inconnue peut laisser visible une autre branche calculable ; le total concerné reste **À compléter**. Aucun salarié ou composant manquant n’est ignoré pour obtenir un total. Une branche explicitement non applicable peut donner0, après contrôle des conditions ; une applicabilité À vérifier reste inconnue.
- Les règles obsolètes sont bloquantes. Les règles À vérifier peuvent servir uniquement à l’arithmétique pédagogique sous hypothèses déclarées ; elles ne sont pas requalifiées automatiquement. Les composants et l’éligibilité restent déclaratifs et nécessitent un contrôle humain.
- Deux clics pendant la même requête ne créent pas deux snapshots. Un nouveau calcul volontaire crée une nouvelle version. Les anciens snapshots conservent leurs montants et empreintes même après un changement de taux futur.
- IR, déductibilité fiscale des cotisations, réduction familiale, frais professionnels, régularisations, net et coût employeur définitif restent distincts. Un brut diminué des cotisations n’est pas présenté comme un net à payer.

Les nouveaux écrans ne modifient pas les simulations historiques de l’ancien espace Paie & GRH.

## Recette complète de cette étape

[PDF six cas](RECETTE_CALCUL_SOCIAL_PAIE_899.pdf), [Excel de suivi](SUIVI_CALCUL_SOCIAL_PAIE_899.xlsx), [données exactes](JEU_CALCUL_SOCIAL_PAIE_899.json). Le jeu P899 est indépendant des variables inconnues ou supplémentaires du cahier893 : tous ses champs et hypothèses sont fournis, avec un oracle chiffré indépendant. Les chiffres ne représentent **aucun taux légal**.

Le résultat fictif initial est354.00MAD salarial et512.00MAD patronal ; après un gain supplémentaire100.00 et un nouveau brut,357.00/516.00. Les résultats réels de recette humaine restent à renseigner : tous les statuts sont **Non testé**. Tests automatisés, installation PostgreSQL cible, recette utilisateur et production sont des validations distinctes.
