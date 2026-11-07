# Frais professionnels et déductibilité IR — lot 907

Ce lot complète le paramétrage fiscal. Il ne calcule aucun frais professionnel ni aucune retenue mensuelle. Une cotisation calculée par le moteur social n'est pas considérée automatiquement comme une déduction fiscale.

## Installation et accès

Sur une **copie isolée et sauvegardée**, le technicien applique `hisabpro-backend/119_paie_qualifications_fiscales.sql` après les migrations 113 à 118. La migration ajoute des gardes aux versions existantes, sans modifier leurs contenus. Elle peut être rejouée. Aucun taux ou régime n'est préchargé.

Le module Personnel doit être actif et protégé. Le préparateur doit disposer des habilitations identité, rémunération et proposition. Le décideur doit être une autre personne, habilitée à approuver. Pour approuver une qualification déclarée validée, il doit également disposer de `personnel.valider_regles_paie` et confirmer son contrôle des preuves. Cette capacité n'est jamais attribuée automatiquement.

## Catalogue — frais professionnels

Ouvrir **02 · Éléments de paie → Catalogue → Créer une rubrique**, ou consulter une rubrique puis proposer une nouvelle version. Les trois traitements IR, CNSS et AMO restent indépendants.

Dans **Frais professionnels**, activer « Définir la qualification ». Choisir « À vérifier », « Incluse » ou « Exclue » pour la fraction imposable de cette rubrique dans la base des frais professionnels. Renseigner les conditions applicables. Il s'agit d'une qualification de base, pas d'un pourcentage de déduction.

Une qualification déclarée validée exige une référence de justificatif, le texte, son article, une URL officielle HTTPS, l'empreinte SHA-256 déclarée de la preuve et sa date de consultation. Le serveur ne télécharge pas cette URL et ne garantit pas que la preuve déclarée correspond au document : le décideur doit le vérifier.

## Charges sociales — déductibilité IR

Ouvrir **04 · Charges sociales → Référentiel → Créer une branche**, ou proposer une nouvelle version d'une branche existante. Dans **Déductibilité IR**, activer la qualification et choisir « À vérifier », « Déductible » ou « Non déductible » pour la **part salariale**. Les paramètres de calcul social et cette qualification fiscale sont distincts.

Même si le calcul social reste « À vérifier », la validation de cette qualification fiscale seule exige les preuves et l'habilitation dédiée. Une convention contractuelle ne suffit pas à dispenser de la justification fiscale officielle.

## Historique et vérification

Les anciennes versions sans ce renseignement affichent « À vérifier — qualification non renseignée ». Elles ne sont pas réécrites. Une nouvelle qualification s'applique avec les dates de sa nouvelle version ; les snapshots déjà calculés sont conservés. Décocher la qualification d'une nouvelle proposition signifie « non renseignée », jamais « non déductible » ni « zéro ».

Les garde-fous existent dans l'API et dans PostgreSQL. Les parcours automatiques utilisent uniquement des sociétés fictives, une cible PostgreSQL native éphémère et Edge. La recette humaine et la production restent à valider séparément.

Suite : relier ces qualifications aux sources du brut et du social pour établir les bases fiscales ; qualifier ensuite les frais, les cumuls, la retenue mensuelle et les arrondis avant le net et les bulletins.
