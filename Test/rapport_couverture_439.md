# Couverture et exploitation — contrôle439

La matrice, le registre des anomalies, la procédure d’exploitation et le rapport
de session du15octobre sont actualisés pour les lots433–438. Aucun statut humain
de recette n’est modifié. Les nouvelles migrations085/086 restent manuelles.

QA documentaire réelle :70 fonctions (15 terminé/47 partiel/4 absent/4 bloqué),31 nouveaux liens valides,6 ZIPs CRC valides et20 fichiers livrés conformes ;84 anciens SQL et115 fichiers de guides/recettes inchangés ;main/models/schemas inchangés. Syntaxe des commandes PowerShell nouvelles analysée sans exécution :0 erreur.

Les preuves de tests proviennent des XML/code0 réellement produits pour chaque
lot ;aucun nouveau test applicatif n’est déclaré exécuté pour cette seule mise
àjour documentaire. Les suites se recouvrent etne sont pas additionnées.

Premier contrôle :le filtre d’identifiants omettait les dix lignes LIA suffixées
ou alphanumériques etéchouait. La chaîne PowerShell poursuivait alors àtort
après l’échecPython ;son fichier.exit initial0 est nonprobant. La reprise élargit
le filtre aux vrais IDs etarrête immédiatement sur erreur. Le contrôle complet
etla syntaxe des commandes passent ensuite ;preuve commandes_v2.exit seulement.

Vérifications effectuées par les scripts locaux verifier439.py etla méthode
PowerShell Parser.ParseInput, sans lancer les commandes documentées. Les ZIPs
ont aussi été comparés au dépôt en retenant la dernière version de chaque fichier,
àl’exception des journaux/manifestes qui continuent d’évoluer.

La globale430 reste historique. Développement global partiel, recette utilisateur
àeffectuer, production nonvalidée. Aucun PostgreSQL réel ni données réelles.
