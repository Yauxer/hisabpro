# Vérification des livrables réellement archivés — 9 octobre 2026

Le premier cumulatif de reprise a été relu intégralement : 60 chemins distincts,
CRC valides, contenus identiques aux fichiers du dépôt et 22 différentiels sources.
Aucun cache, environnement, secret ou dump inclus. Les services de l'utilisateur
sont restés actifs ; les sessions de tests sont terminées.

Les deux PDF et deux Excel ont ensuite été ouverts **depuis les octets du ZIP** :

| Annexe | Pages PDF | Feuilles Excel | Cas utilisateur |
|---|---:|---:|---:|
| Corrections 277 | 18 | 7 | 8 Non testé |
| Achats partiels 284 | 6 | 3 | 2 Non testé |

Les colonnes des cas « Résultat réel », « Anomalies » et « Observations » sont
vides. Les preuves attendues restent renseignées, sans preuve utilisateur fabriquée.

Le premier contrôle complémentaire a terminé avec code 1 : il interdisait les
mots « Réussi/Échoué/Bloqué » dans toutes les cellules, y compris les libellés
normaux du tableau de synthèse. Cela n'était pas un échec fonctionnel ni une
prévalidation des cas. Le contrôle a été corrigé pour lire la colonne « Statut »
des feuilles de cas, puis réellement réexécuté : **code 0**, dix cas Non testé,
pages/feuilles exactes et fichiers archivés conformes au dépôt.

Cette vérification documentaire ne remplace pas la recette utilisateur. La
globale applicative finale reste 2 582 réussites, 32 avertissements existants,
code retour 0 et 625 empreintes conservées. Aucun code applicatif ou test métier
n'a changé après cette exécution.

Le cumulatif vérifié inclut ce rapport et la note de reprise actualisée. Le
premier cumulatif reste conservé ; il n'est pas écrasé. La nouvelle archive est
contrôlée et listée séparément avant livraison.
