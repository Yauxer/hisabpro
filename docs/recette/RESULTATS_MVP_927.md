# Résultats — aperçu des sorties d’immobilisations927

La campagne finale unique a réellement terminé avec **62 tests réussis, aucun échec ni ignoré**, en539,33s, code0. Elle comporte les tests unitaires, les API sur PostgreSQL natif jetable et les parcours Edge. Les30 avertissements de dépendances sont conservés dans les rapports. [Preuve et identifiants](../../Test/PREUVE_MVP_927.json).

Les sept nouveaux cas PostgreSQL vérifient le linéaire et le dégressif, l’égalité des montants aperçu/enregistrement, le refus d’une empreinte périmée après changement de demande ou de dotation, les dotations incohérentes, la mise au rebut d’un bien déclaré non amortissable, les droits et l’isolation de société, les dates et les montants non finis. L’appel du calcul métier et de sa dépendance a aussi réellement fonctionné dans une transaction PostgreSQL READ ONLY. Les photos des écritures, lignes, immobilisations, exercices, périodes et cinq séquences métier sont identiques avant et après aperçu. La trace d’audit HTTP reste distincte.

Les quatre nouveaux parcours Edge couvrent cession et rebut à1440px et390px : lecture du calcul, disparition de l’aperçu après saisie, absence de résurrection en revenant à la valeur initiale, transmission de l’empreinte, enregistrement aux mêmes montants et rafraîchissement du registre. Les captures sont dans le sous-dossier `preuves/927_*_apercu.png`.

La campagne élargie rejoue les anciens clients sans empreinte, les sorties et encaissements différés, les reprises d’ouverture, les mutations concurrentes, les clôtures, les cinq annuités dégressives et les deux parcours annuels complets d’intégrité. Elle ne qualifie pas toute la roadmap. Les campagnes ciblées antérieures ont réellement réussi :13tests unitaires,7nouveaux cas PostgreSQL,puis11cas PostgreSQL/Edge. Ces répétitions ne sont pas ajoutées au total62.

Build frontend final :214modules,4,91s,code0 ; avertissement de taille du bundle conservé. Compilation Python et vérification des empreintes des anciennes migrations effectuées. Aucun SQL ajouté ou modifié. Aucune base ou donnée réelle utilisée. Aucune nouvelle restauration exécutée dans927 ;la restauration84tables de925 reste une preuve antérieure distincte.

Six nouveaux cas humains sont tous **Non testé**. IMM004 reste **Partiel**, et le suivi global ne gagne artificiellement aucune fiche :181Réussi,6Partiel,76Non qualifié individuellement et9Bloqué à la source. Convention de prorata et TVA de cession restent à qualifier ;ces tests n’approuvent ni la recette utilisateur ni la production.

[Guide](APERCU_SORTIES_IMMOBILISATIONS_927.md) · [PDF](RECETTE_APERCU_SORTIES_927.pdf) · [Excel humain](SUIVI_APERCU_SORTIES_927.xlsx) · [Suivi global](SUIVI_AUTOMATISATION_CAHIER_927.xlsx) · [Décision MVP](DECISION_FACTURATION_COMPTABILITE_927.md).
