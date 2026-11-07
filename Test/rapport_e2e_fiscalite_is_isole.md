# Recette IS connectée : retraitements, imputation et photographie annuelle

Lot `FIS-IS-E2E-20261007`. Deux nouveaux fichiers de test/rapport uniquement ; aucun code produit, migration historique, règle comptable ou fiscale modifié. Les chiffres et références ci-dessous constituent des données fictives de laboratoire, sans portée réglementaire ni preuve de conformité officielle.

## Exécution réelle

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_e2e_fiscalite_is_isole.py -q
```

Résultat final : **1 réussi en 18,56 s**, code de sortie 0, aucun échec, aucun ignoré. 26 avertissements existants de dépréciation SQLAlchemy/Starlette/Pydantic.

Edge headless réel utilise le frontend React et FastAPI réellement démarrés sur loopback, puis PostgreSQL éphémère marqué. Aucun appel métier intercepté, aucune réponse ou authentification remplacée. Les seuls appels externes décoratifs interceptés sont les CDN polices/icônes indisponibles. Le helper vérifie à la sortie l'arrêt des processus et thread web ainsi que la suppression des dossiers E2E/cluster. Aucun PostgreSQL réel ni donnée utilisateur touché.

Le socle de l'application de recette et les migrations de comptabilité sont ceux du helper E2E existant ; sont ajoutées, dans ce cluster seulement, 021, 021b, 022, 023, 024, 025 et 066. Aucune réparation historique 065/067/068/070 n'est exécutée. Cette recette utilise le rôle propriétaire du laboratoire pour le backend ; elle ne prouve pas les permissions fiscales exhaustives d'un compte applicatif non propriétaire.

## Jeu de données et calcul indépendant

Société fictive créée et administrateur authentifié par les vrais endpoints. Exercice 2025 préparé par les routes existantes. Hypothèse explicite : taux IS **forcé à 20 % dans le formulaire existant**, justification « Hypothese synthetique du laboratoire, sans portee reglementaire ». Ce choix teste l'option du produit ; il n'affirme pas qu'un régime légal particulier autorise ce taux pour une société réelle.

Écritures initiales créées et validées par API :

| Référence | Débit MAD | Crédit MAD |
|---|---|---|
| PRODUIT-IS-FICTIF | 5141 Banque 19 700 ; 3453 Retenue 300 | 7111 Produit 20 000 |
| ACOMPTE-IS-FICTIF | 3453 Acompte 1 000 | 5141 Banque 1 000 |

La banque est donc de 18 700 MAD et l'actif fiscal de 1 300 MAD avant liquidation. La saisie fiscale des retenues/acomptes reprend ces sources comptables fictives explicites ; elle ne crée pas artificiellement une deuxième écriture de paiement.

Dans Edge, sélection de 2025 via Clôture → Exercice actif, puis Fiscalité IS :

1. Enregistrement du taux hypothétique 20 % et référence annuelle d'acomptes forcée 4 000 MAD avec justification fictive explicite.
2. Ajout d'une réintégration manuelle 1 000 MAD et d'une déduction manuelle 500 MAD, catégorie existante « autre ». Leur déductibilité réelle n'est pas affirmée : elles sont des entrées explicitement décidées dans ce scénario fictif.
3. Ajout du crédit PPRF 300 MAD, dont 100 déjà imputés sur acomptes, date 01/12/2025, référence `PPRF-FICTIF-300`.
4. Enregistrement de l'acompte 1 : 1 000 MAD versés au 01/12/2025, référence `ACOMPTE-FICTIF-1000`.

Oracle `Decimal` indépendant, comparé aux réponses réelles et au snapshot :

| Élément | Calcul | MAD |
|---|---|---:|
| Résultat comptable avant IS | Produit initial | 20 000 |
| Bénéfice fiscal imposable | 20 000 + 1 000 − 500 | 20 500 |
| IS théorique selon l'hypothèse | 20 500 × 20 % | 4 100 |
| Crédit disponible à liquidation | 300 − 100 déjà imputés | 200 |
| Acomptes/crédits déjà imputés | 1 000 versés + 100 | 1 100 |
| Solde | 4 100 − 200 − 1 100 | 2 800 |

La retenue n'est donc pas comptée deux fois. L'oracle n'utilise pas le service de calcul du produit.

## Contrôles négatifs puis poursuite normale

Une charge IS **fictive incorrecte** de 2 000 MAD est créée et validée via le journal (6701 débit / 4453 crédit). La situation indique réellement une comptabilisation incohérente par rapport aux 4 100 attendus :

- La clôture normale est refusée 409 pour incohérence de comptabilisation.
- La confirmation fiscale est refusée 409 parce que l'exercice n'est pas clôturé.

Le garde de confirmation sur une incohérence d'un exercice *déjà clôturé* n'est pas artificiellement atteint : le flux normal de clôture empêche cette situation et fige ensuite les paramètres influant sur l'impôt. Aucune clôture factice n'est injectée et aucun contrôle contourné.

L'erreur fictive est corrigée via la route de **contrepassation auditée**, au 02/12/2025. L'original reste définitif avec son débit de 2 000 intact, vérifié en PostgreSQL. La contrepassation est une nouvelle écriture distincte. La clôture normale peut ensuite comptabiliser automatiquement l'IS cohérent de 4 100 MAD sur 6701/4453 ; la réponse fiscale est vérifiée cohérente avec cette charge.

Après rechargement de l'écran, **Confirmer la liquidation** produit réellement un POST200. La photographie confirme l'impôt 4 100, crédits disponibles 200, acomptes/crédits imputés 1 100 et solde 2 800. Le montant de solde est vérifié dans le DOM, avec normalisation des séparateurs de milliers du format affiché `2.800,00 MAD`.

Après un second rechargement, la photographie reste visible et le bouton de confirmation disparaît. Le détail complet du snapshot est identique entre API et PostgreSQL ; la référence d'acompte est conservée. Nouvelle confirmation et ajout de crédit après confirmation refusés 409. UPDATE SQL direct du snapshot refusé par le trigger. Aucune erreur JavaScript ni réponse API500 observée.

## Autres commandes exécutées

```powershell
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m pytest Test/test_patch08_5_acomptes_liquidation.py Test/test_patch08_6_css_credits.py Test/test_patch089_retenues_deja_imputees_synthese.py Test/test_patch092_liquidation_reference_acomptes.py -q
& '.\hisabpro-backend\.venv\Scripts\python.exe' -m py_compile Test/test_e2e_fiscalite_is_isole.py
```

Résultats : **29 réussis en 0,23 s** ; compilation finale code de sortie 0.

Exécutions antérieures du nouveau test, explicitement distinguées :

- Premier essai : 1 échec en 36,19 s, sélecteur « Exercice actif » recherché sur Fiscalité IS où il n'existe pas. Navigation corrigée vers le sélecteur existant de Clôture ; contrats `date_correction` et `id` de contrepassation vérifiés avant la relance.
- Deuxième essai : 1 réussi en 18,93 s. Deux appels Query.get propres au test remplacés ensuite par Session.get et contrôle du montant DOM renforcé.
- Troisième essai : 1 échec en 18,80 s, contrôle DOM attendant l'absence de séparateur de milliers alors que l'écran affiche `2.800,00`. Normalisation du format observé corrigée dans le test uniquement.
- Dernier essai après ces corrections : résultat final 1 réussi en 18,56 s cité ci-dessus.

## Limites

Ce scénario réduit ne valide pas la réglementation, le dépôt DGI, XML/EDI, déficits millésimés, CSS complète, tous les régimes IS, ni l'intégralité des exports fiscaux. Il ne vaut ni recette utilisateur ni validation visuelle humaine. Les données historiques et justificatifs manquants ne sont pas réparés. Aucune nouvelle règle fiscale n'a été codée ou présentée comme obligatoire et aucune préparation complète à la production n'est affirmée.
