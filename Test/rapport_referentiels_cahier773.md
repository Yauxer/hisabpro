# Référentiels du cahier773

Les nouvelles fiches de tiers apparaissent maintenant en tête de la page, y compris après rechargement. Le tri est appliqué après le chargement complet et avant les filtres existants. L’ordre de l’API et des sélecteurs reste inchangé. Aucun backend ni migration modifié.

Parcours Edge/API/PostgreSQL éphémère exécuté avec les données exactes du cahier, sur1440/390 :7tiers créés puis réouverts,comptes3421/4411/4481 et auxiliaires générés vérifiés ;3articles créés puis réouverts,prix/TVA/achat/vente vérifiés,M-01 stock zéro,services non stockables en forfait sans mouvement. Aucune écriture comptable créée par les référentiels. La société et ses paramètres sont des préconditions API ;leurs formulaires étaient couverts769.

Résultats :première campagne1échec prouvant le tri alphabétique,conservé ;après correction2réussites ;après ajout du contrôle après reload,campagne6réussites en118,29s (2référentiels,2délais,2activité),aucun échec/erreur/ignoré final. Les2référentiels ont été revalidés en60,71s après ajout du contexte unique de cluster aux preuves. Recouvrements non additionnés. Build Vite0 en5,13s avec avertissement bundle ;2Python compilés.

Cas :HP-ADM-006 à012 et014/015 réussis automatiquement dans ce périmètre. HP-ADM-013 reste partiel :création M-01 et ses champs UI réussis,mais les comptes de stock3111/6114 ne sont pas des champs de l’article et restent à vérifier dans le vrai parcours d’inventaire. Les272fiches humaines conservent leurs statuts.

Preuves :PREUVE_REFERENTIELS_CAHIER773.json,preuves_referentiels773 etcaptures docs/recette/PREUVE_REFERENTIELS_773_BUREAU.png / MOBILE.png. Aucun PostgreSQL réel utilisé ;aucune recette humaine/production validée. Incident Lettrage769 toujours ouvert ;RH/paie etpoint6 différés.

Suite :premier cycle commercial du cahier avec dates2025 explicitement saisies,écritures/stocks générés par les vrais formulaires.
