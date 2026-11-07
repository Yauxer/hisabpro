# Banque du cahier : correctif et recette771

Le nom d’une banque personnalisée disparaissait après la première frappe : le même état contenait le choix « Autre » et le nom réel. La sélection du mode libre est maintenant distincte ; le nom est contrôlé et réaffiché à la réouverture. Aucun champ, contrat API, migration ou donnée historique modifié. Les boutons de modification/suppression ont désormais un nom accessible.

Utilisation : Paramètres → Comptes bancaires → Ajouter un compte → Banque « Autre » → saisir Banque Recette ; RIB fictif000000000000000000000001, MAD, compte5141. Créer puis modifier ou rouvrir le compte : le nom et les zéros du RIB sont conservés. Un nom vide bloque l’enregistrement.

Tests réellement exécutés sur Edge et PostgreSQL éphémère : reproduction avant correctif1échec conservé ; après correctif2réussites sur1440/390 ; connexes société/administration3réussites. Build Vite0 en12,00s avec avertissement de poids du bundle ;compilation Python OK. Le test société769 avait aussi été rejoué avant correction :1réussite,non additionnée aux5tests distincts après correction.

HP-ADM-005 : Réussi automatique pour ce parcours bancaire. Les classeurs de recette humaine restent inchangés. Aucun PostgreSQL réel ni donnée comptable réelle utilisé. Le libellé bancaire et le RIB sont fictifs ; aucune attribution officielle attestée.

Preuves : PREUVE_BANQUE_CAHIER771.json,preuves_banque771/*.xml et captures docs/recette/PREUVE_BANQUE_771_BUREAU.png / MOBILE.png. L’échec initial n’est pas remplacé. L’incident Lettrage769 reste ouvert et indépendant.

Prochaine étape : tiers et articles exacts du cahier puis cycle commercial connecté via leurs formulaires ;RH/paie etpoint6 restent différés.
