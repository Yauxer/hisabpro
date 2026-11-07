# Frais bancaires au centime —404

Six défauts API reproduits avant correction : booléens, fractions de centime et frais positifs ignorés sur remise/paiement. Première preuve16cas :6échecs/10réussites. Validation Pydantic avant conversion : refus des booléens, non finis, négatifs, fractions de centime et pertes de représentation. Calculs banque/charges en Decimal. Frais sur remettre/payer refusés au lieu d’être ignorés. Un montant historique non représentable au centime est refusé sans réparation.

Effets affiche une erreur API structurée lisible, accessible comme alerte ;l’avis distingue brut et net. Deux Edge bureau/mobile :10,005 refusé422,message centime,statut et photographies inchangés. Cas valides0/null/0,01/10,01 :net banque+charge=120.

Preuves copie :38tests connexes réussis ;premier testUI a échoué sur sa lecture sans paramètre exercice,après refus422/message/photos déjà vérifiés. Oracle corrigé avec paramètre et contrôle200 ;nouvelle suite réelle réussie. Historiques et écritures définitives inchangés ;pas de TVA bancaire ou escompte inventés.

185tests racine réussis,456.818s,zéroéchec/erreur/ignoré ;721empreintes stables ;compilation etbuild code0.

Aucun PostgreSQL réel ni donnée comptable réelle ;sources et tests finaux sur PGnonce/Edge. Aucun SQL nouveau,main/modèles/migrations conservés. Recette humaine etpoint6 en attente.
