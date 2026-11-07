# MODE D’EMPLOI ET RECETTE — RÉSULTAT COURANT DOCUMENTAIRE

Version 1 du 21 octobre 2026. B13 autonome interne, sans calcul de taux fiscal.

## Accès et portée

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation conservée → Documenter le résultat courant B13
depuis les balances. Les formulaires B13-N et B13-N1 sont des identifiants
internes, distincts d’un modèle officiel DGI ou EDI.

Une synthèse sourcée au plus par période. La balance fournit le résultat
courant71/73 moins61/63 ; le compte67 est séparé, pour mémoire uniquement.
Réintégrations, déductions et impôt théorique courant sont des déclarations
explicites. Aucune reprise du Journal courant ni de sa liquidation IS.

Les deux calculs affichés sont documentaires : courant + réintégrations −
déductions ; courant − impôt théorique déclaré. Aucun taux n’est appliqué.
Le résultat courant après impôt déclaré ne part pas de la base retraitée.
Régime et avantages restent à documenter ; ne pas reprendre un taux fictif
de ce guide pour une société réelle.

## Prérequis et jeu chiffré exact

Créer une société fictive séparée en MAD avec exercice2026, administrateur,
comptable et lecteur. Compléter le plan existant ; vérifier les comptes1111,
5141,7111,6132,7581 et6701. Ajouter un logo fictif dans les paramètres.
Le module de préparations et ses migrations existantes sont requis ;721
n’ajoute aucune migration. Redémarrer le backend et reconstruire le frontend.

Importer les CSV BALANCE_FICTIVE_COURANT721_N.csv et
BALANCE_FICTIVE_COURANT721_N1.csv fournis dans docs/recette. Chaque cellule
non mouvementée des lignes présentes vaut explicitement0.

N :1111 crédit10000 ;5141 débit16400 ;7111 crédit10000 ;6132 débit3000 ;
7581 crédit1000 ;6701 débit1600. Débit=crédit=21000MAD.
Résultat courant10000−3000=7000 ; résultat non courant1000 ; résultat avant
impôts8000 ; impôts comptabilisés1600 ; net6400. Banque16400=capital10000+net6400.

N-1 :1111 crédit10000 ;5141 débit13000 ;7111 crédit5000 ;6132 débit2000.
Débit=crédit=15000MAD ; courant=net=3000. Aucun impôt comptabilisé dans ce jeu.

Synthèse N : déclaration Saisie documentée — à revoir ; justification Synthèse
fictive721, sans taux fiscal calculé ; désignation Synthèse courante fictive N ;
réintégrations500 ; déductions200 ; impôt théorique1200 ; régime/avantages À
vérifier sur justificatifs, aucun avantage déduit ; référence NOTE FICTIVE721 N,
postes courants seulement. Base documentaire7000+500−200=7300 ; courant après
impôt déclaré7000−1200=5800. Les1600 du compte67 ne préremplissent pas1200.

Synthèse N-1 : même statut ; justification Synthèse fictive N-1 ; désignation
Synthèse courante N-1 ; réintégrations0 ; déductions0 ; impôt théorique0 ;
référence NOTE FICTIVE721 N-1, zéros déclarés. Base et courant après impôt3000.
Ces zéros sont saisis explicitement ; régime/avantages reste vide, à documenter.

## Utilisation et vérifications

1. Importer les deux CSV, contrôler puis conserver ; noter version et empreinte.
2. Ouvrir le formulaire B13 et saisir la synthèse N ci-dessus. Le bouton Ajouter une ligne devient indisponible après la première ligne de cette période.
3. Passer à B13-N1 et saisir la synthèse N-1. Revenir à N ; les saisies du brouillon doivent être conservées.
4. Cocher la confirmation puis Conserver les tableaux ETIC dans une nouvelle version. La nouvelle version doit être sélectionnée sans F5.
5. Réouvrir B13 ; vérifier7000,7300,1600 pour mémoire,1200 déclaré et5800. Comparer le résultat courant au CPC VII figé ; écart attendu0.
6. Modifier l’impôt déclaré en1199,99 sans enregistrer : le contrôle conservé reste5800. Après conservation d’une nouvelle version, il devient5800,01 ; l’ancienne version reste5800.
7. Télécharger le dossier ZIP. Contrôler PDF, Excel, résultat courant documentaire JSON et manifeste SHA256. Le logo actuel apparaît sur PDF/Excel, hors empreinte historique du contenu.
8. Vérifier le Journal : aucune écriture, aucun règlement ni aucune liquidation générés. Les autres compléments et les anciennes versions restent inchangés ; les pièces restent attachées à leur version d’origine.

## Inconnus, erreurs et limites

Laisser l’impôt théorique vide : courant après impôt indisponible, sans reprise
automatique de67. Laisser une réintégration ou déduction vide : base
documentaire indisponible. Zéro explicite et inconnue sont distincts.
N-1 absent : formulaire de cette période indisponible, aucune donnée fabriquée.
Une balance soldée en119 ne fournit pas un CPC nul ; la préparation demande
la balance avant clôture technique. Néant n’impose pas des hypothèses fiscales0.

NaN, infini, montant négatif dans les cases déclarées et précision supérieure
à deux décimales sont refusés. La désignation et la référence identifient toute
synthèse, même partielle. Les contrôles restent ceux de la version conservée ;
la déclaration documentée ne garantit pas une validation fiscale. Une note B13
non applicable avec une synthèse déclarée déclenche une alerte à revoir.
Le lecteur consulte et exporte, sans enregistrer. Une préparation d’une autre
société ne doit pas être accessible. Après rejet, corriger le brouillon sans F5.

## Cas de recette humaine à effectuer

|ID|Actions et données exactes|Résultat et preuve attendus|Statut|
|---|---|---|---|
|B721-01|Importer les deux CSV fictifs, conserver, saisir les deux synthèses exactes, confirmer et conserver.|Nouvelle version sans F5 ; courant N7000, base7300, compte67 à1600 séparé, impôt déclaré1200, après5800. N-1 courant/base/après3000. Captures et empreintes.|Non testé|
|B721-02|Dans une nouvelle version, vider déductions et impôt N en gardant réintégrations500 ; conserver. Puis saisir explicitement0 dans les trois cases et conserver.|Avec les vides : base et après indisponibles ; avec les trois0 : base et après7000. Aucune reprise de1600. Captures des deux versions.|Non testé|
|B721-03|Modifier impôt1200 en1199,99 dans le brouillon puis enregistrer une nouvelle version ; relire la version précédente.|Avant enregistrement5800 conservé ; ensuite5800,01 ; ancienne version5800. Télécharger les deux dossiers et comparer les sources conservées.|Non testé|
|B721-04|Saisir NaN puis corriger ; essayer une seconde ligne et une synthèse sans référence. Refaire dans une société fictive sans N-1 et consulter comme lecteur.|Rejets sans version supplémentaire ni perte du brouillon ; une ligne maximum ; N-1 indisponible ; lecteur sans bouton de conservation. Captures et relevé des versions.|Non testé|
|B721-05|Télécharger ZIP/PDF/Excel avec logo fictif. Dans une société distincte, importer une balance soldée1191 crédit6400,1111 crédit10000,5141 débit16400 ; conserver B13 sans hypothèse.|Manifestes, champs numériques et logo corrects. Sur balance soldée, courant indisponible et mention de clôture technique, jamais0 fabriqué. Captures et fichiers.|Non testé|
|B721-06|Noter le nombre et les montants des écritures avant/après B13. Comparer les autres compléments, anciennes versions et pièces. Déclarer la noteB13 non applicable tout en gardant la synthèse.|Journal et autres données inchangés ; aucun IS ou paiement créé ; contradiction visible sans correction automatique. Preuves avant/après, recette fiscale humaine à effectuer.|Non testé|

## Statuts du livrable

Fonction documentaire développée ; résultats automatisés dans le rapport721.
La recette utilisateur de ces six cas reste à effectuer. L’installation sur
PostgreSQL réel, Office Desktop, la conformité réglementaire et la production
ne sont pas validées automatiquement. B12, B14 et C3 demeurent des travaux
distincts. RH/paie et le point6 différé restent hors de ce lot.
