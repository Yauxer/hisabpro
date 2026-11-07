# RAS TVA — précision du contrôle de tauxHT577

Le raccordement571 refuse les combinaisons RASHT/TVA non couvertes. Son contrôle
utilisait toutefois un arrondi monétaire au centime pour vérifier le tauxHT :
des pourcentages positifs inférieurs à0,005 pouvaient devenir artificiellement0.

La correction réutilise le validateur partagé des taux et compare la valeur
Decimal sans arrondi monétaire. Elle ne change aucun taux fiscal ni les données
existantes. Un taux source invalide reste signalé ; le taux0 reste admissible.

Reproduction sur vraies factures et API d'aperçu, cluster PostgreSQL nonce099 :
**3 échecs,2 réussis,32,82s**, pour1e-8,0,0001 et0,001 admis à tort.
Après correction :**78 réussis,29 avertissements,108,62s, code0**, comprenant
les5 cas de précision,29 casAPI571/573 et44 simulations559. Aucun échec ni
test ignoré final. L'aperçu ne crée aucune donnée métier.

Backend uniquement ; pas de build frontend nécessaire pour ce lot. Aucun
PostgreSQL réel, ancienne migration ou écriture validée modifié. La qualification
de l'installation cible et le traitement déclaratif complet restent à effectuer.
Prochaine étape : registre descriptif des captures, sans crédit fiscal présumé.
