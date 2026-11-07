# Devis — alerte indicative de stock, 8 octobre 2026

Décision utilisateur : autoriser le devis à approvisionner avec une alerte ;
les services restent disponibles. Aucun blocage, réservation ou promesse future.

## Analyse du dépôt

`Article.stock_actuel` est la photographie de stock physique par société,
maintenue par le service de mouvements. Aucun entrepôt ni réservation n'est
modélisé. Le GET articles fournit déjà stock et caractère stockable, mais le
formulaire conserve la photographie du choix de l'article. Son alerte actuelle
ne cumule pas plusieurs lignes du même article et n'existe pas dans l'édition.
Un stock NULL ou non fini ne peut être assimilé à zéro ; `D(None)` du moteur de
mouvement réalise précisément cette conversion et ne doit pas être utilisé
sans ce contrôle pour ce diagnostic.

Le POST `/api/devis/diagnostic-stock` est une lecture authentifiée, ouverte
au rôle lecture, sans mutation. Une seule requête filtrée société/articles actifs,
cumul Decimal par article, services explicitement non stockables exclus des
alertes. Articles étrangers/inactifs/absents : diagnostic inconnu sans révéler
nom/stock. Quantités négatives, booléens et non finis refusés422. Quantité0
autorisée dans une ligne en préparation. Stocks historiques invalides : NULL et
diagnostic, aucune réparation. Cumul non représentable par un float JSON :
chaîne Decimal canonique avec diagnostic, jamais Infinity ni faux zéro.

## Correction et tests exécutés

Tests seuls préparés pendant le gel ; service et routeur modifiés exclusivement
après le signal de levée de l'agent principal. Aucun changement du frontend,
de la création de devis, du moteur de mouvements ni de la lecture brute articles.
Les quantités sont cumulées en Decimal avec précision adaptée aux exposants,
au nombre de lignes et au stock soustrait. Oracle indépendant entier Python
pour vérifier l'écart exact `2*10**308-5`, sans arrondi masquant les5unités.

Première exécution ciblée :22réussis,25avertissements,17,27s. Après renforcement
de l'oracle d'écart extrême, commande finale réellement exécutée :

```text
PYTHON_DOTENV_DISABLED=1 python -X utf8 Test/run_unit_tests.py Test/test_devis_stock_diagnostic.py Test/test_articles_archivage_stock.py Test/test_stock_integrite_mouvements.py Test/test_fact2_cycle_commercial.py --tb=short
```

**76réussis,25avertissements,16,71s**, aucun ignoré :22nouveaux cas et54connexes.
JWT/API et PostgreSQL éphémère réels. Couverture : disponibilité0/5/6, regroupement
de lignes, services, saisie libre, historiquesNULL/NaN/±Infinity/négatifs, autres
sociétés/articles inactifs/introuvables, inputsbool/nonfinis/négatifs422, rôle
lecture et refus401sans authentification, une seule requête et somme0.1+0.2 exacte.
Les instantanés prouvent aucune mutation d'articles/mouvements/devis/écritures.
Un mouvement réel fait passer le stock5→0 : nouvelle lecture0, alerte, puis
création d'un devis en rupture HTTP201sans réservation ni mouvement supplémentaire.
Compilation routeur/service/test : code0.

## Limites et prochaine étape

Les contrôles UI seront un lot distinct après livraison des bons de réception.
Stock physique actuel, sans réservation, délai d'approvisionnement ni engagement
de disponibilité future. Quantités hors représentation float exposées en texte
Decimal, à afficher sans conversion aveugle versInfinity. Les historiques
invalides sont diagnostiqués, sans réparation ni blocage du devis. Le GET brut
articles demeure hors périmètre ; sa lecture d'un historique non fini ne doit
pas être présentée comme validée par ce diagnostic distinct. PostgreSQL réel,
processus utilisateur et données comptables réelles jamais utilisés.
