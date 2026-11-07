# RAS — lecture et conservation, 8 octobre 2026

## Correction minimale

`FactureOut` expose désormais `ras_taux`, `montant_ras`, `net_a_payer` et
`ras_anomalie`. POST et GET utilisent le même calcul existant : HT 1 000,
TVA 200, TTC 1 200, taux 10 % donnent RAS 100 et net 1 100. Aucun taux fiscal,
assujettissement, assiette ou traitement comptable n'a été ajouté ou changé.

Le contrat de lecture perdait auparavant ces trois valeurs lors du filtrage
Pydantic. L'éditeur recevait donc un taux absent et pouvait sauvegarder zéro.
Une édition réelle dans Edge conserve maintenant 10 % après PATCH et GET.

Pour un taux historique NaN, infini ou hors 0–100, la liste et le détail des
règlements restent accessibles avec diagnostic. Les valeurs dépendant de la RAS
sont nulles ; les montants HT/TVA/TTC et les encaissements déterminables restent
lisibles. Aucun solde ni retenue n'est inventé. Les calculs financiers dépendants
et le PDF refusent ce taux par HTTP 409. Aucune ancienne valeur n'est réparée.

## Exécution réelle

Commande finale :

```text
python -X utf8 Test/run_unit_tests.py Test/test_ras_lecture_conservation.py Test/test_ras_taux_finis.py Test/test_fact7_recouvrement.py Test/test_fact8_echeanciers_acomptes.py Test/test_factG_acomptes_avoirs.py Test/test_patch127_etic_ras_recoupement.py
```

Résultat : **89 réussis, 67,12 s**, dont les 7 nouveaux tests sur API connectée
au PostgreSQL éphémère et un scénario Edge avec connexion réelle et sauvegarde.
Le nouveau lot vérifie POST/GET/PATCH à 10 %, cinq anciennes valeurs invalides,
GET liste et règlements sans HTTP 500, PDF proforma refusé par HTTP 409,
stockage/lignes inchangés et aucune écriture créée. Les processus et dossiers
temporaires sont vérifiés arrêtés/nettoyés par la fixture.

Compilation `py_compile` de schemas.py, routers/factures.py et du test : OK.

Essais intermédiaires, non présentés comme réussis :

- 7 échecs en 27,75 s puis 7 en 27,41 s : helper de test réouvrait un client
  HTTP déjà actif ; corrigé avec `contextlib.closing`.
- 1 réussi / 6 échoués en 63,34 s : contrôle PDF brouillon précédant le contrôle
  RAS et sélecteur de bouton trop strict ; fixture et sélecteur corrigés.
- 2 réussis / 5 échoués en 34,22 s : fixture essayait de valider une pièce sans
  numéro définitif ; le vrai garde PostgreSQL a refusé. La fixture utilise une
  proforma synthétique pour tester le PDF sans contourner le garde.

Les données, migrations et déclencheurs réels n'ont jamais été modifiés.

## Limites

La RAS estimée encore comptée comme paiement avant règlement, sa consommation
entière au premier règlement et la RAS TVA restent les limites décrites dans
`docs/audit/AUDIT_RAS_HISABPRO_20261007.md`. Aucune conformité fiscale complète
n'est déclarée. Le diagnostic historique doit encore être présenté explicitement
dans les formulaires afin d'éviter une substitution visuelle par zéro ; ce travail
frontend est coordonné séparément. PostgreSQL réel de l'utilisateur non utilisé.
