# Résultats du lot 955 — cotisation minimale sur deux copies

**Deux tests Edge/API/PostgreSQL natif isolé réussis**, aucun échec ni ignoré. Finale `cm955_final` : 92,69 secondes XML, code 0 (92,98 secondes affichées par pytest).

Chaque test, sur écran de 1440 ou 390 pixels, utilise deux sociétés fictives distinctes avec les mêmes 48 écritures avant IS du cahier. Le test enregistre et recharge le formulaire CM : exonération explicitement justifiée dans la copie A, contrôle non exonéré dans la copie B.

| Contrôle | Copie A | Copie B |
|---|---:|---:|
| Base CM | 170 500,00 | 170 500,00 |
| Calcul avant minimum et exonération | 426,25 | 426,25 |
| CM exigible selon les hypothèses | 0,00 | 3 000,00 |
| IS théorique | 23 420,25 | 23 420,25 |
| Solde IS après crédit de 200 | 23 220,25 | 23 220,25 |

Les écritures et le calcul IS sont conservés. Une demande d'exonération sans justification est refusée avec le code 422 avant mutation. Les quatre sociétés de laboratoire sont indépendantes ; aucun dossier réel n'est utilisé.

La fiche **HP-FIS-024 passe de Partiel à Réussi dans le périmètre automatisé**. Le suivi comporte **250 réussis, 10 partiels et 12 bloqués**, sur 272 fiches. Aucun statut humain n'est rempli. Les 343 anciens documents sont préservés.

Le produit reste strictement identique au candidat 953, 550 empreintes. Aucun backend, frontend, migration ou taux fiscal n'est modifié dans ce lot ; le build 953 réussi reste applicable et n'a pas été relancé. Ces copies comptables servent au calcul de CM : elles ne constituent pas une restauration du dossier annuel commercial et des immobilisations. L'exonération d'une société réelle nécessite ses justificatifs et une qualification humaine.

[Guide](CM_COPIES_955.md) · [Preuves](../../Test/PREUVE_MVP_955.json) · [Correspondances](../../Test/QUALIFICATION_FICHES_955.json) · [Suivi](SUIVI_AUTOMATISATION_CAHIER_955.xlsx).
