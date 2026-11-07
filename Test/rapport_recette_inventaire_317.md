# Annexe de recette inventaire — lot317 — 10 octobre2026

L'annexe complète le cahier annuel existant sans le régénérer. PDF23pages,
Excel6feuilles et1graphique, Markdown, JSON d'oracle et générateur sans accès DB.

19identifiants uniques ;16cas Non testé et3Bloqué en attente de préparation
technique isolée pour les sources historiques inconnues. Résultat réel et
anomalies restent vides. Les colonnes attendues décrivent données, actions,
écritures, impacts sous hypothèses de laboratoire, contrôles et preuves.

Scénario indépendant : capital1000 ; achat10×20HT=200, TVA laboratoire40,
facture240 payée ; comptage8, stock160, perte40. Quatre écritures/neuf lignes,
D=C1640. Solde banque760 ; fournisseur0 ; résultat avant impôt−40 ; bilan960/960.
La perte physique40 n'exige pas une seconde OD : achat200 et variation crédit160
donnent déjà une charge nette40. Aucun IS/CM/CSS inventé.

Générateur réellement exécuté : code0. Vérificateur indépendant réellement
exécuté : code0, lecture de toutes les pages PDF avec pypdf, des six feuilles
avec openpyxl, statuts/IDs/formules/graphique/champs et comptabilité contrôlés.
Compilation du générateur : code0. Les formules Excel ne sont pas exécutées
par openpyxl ; recalcul demandé à l'ouverture. La mise en page visuelle et
le parcours utilisateur complet restent à vérifier humainement.

PDF SHA256 :1505d4aeace5bdee65b2f232016e353f53b7d5cafddd9ff95795e9ec0b89fc90.
Excel SHA256 :032645aaf04e425adf9bab96dc275552535d5ffe50567a340821c2f2878b7378.
Ces empreintes concernent cette génération ; les métadonnées PDF/ZIP peuvent
changer lors d'une régénération sans changement des chiffres.

La génération et sa vérification n'utilisent aucune base. Elles ont lieu
pendant la globale315, sans modifier ses653sources figées. La preuve313
(148tests et4Edge) porte sur ses propres fixtures, et ne valide pas automatiquement
les19cas utilisateur de cette annexe.
