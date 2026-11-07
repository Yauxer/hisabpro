# Consolidation de la reprise21:29UTC — lot346

## Version et commande

Après livraison343 (conversion BL/BR) et344 (validation définitive), les
**684sources/SQL/tests/configurations/assets publics** sont figés avant
la nouvelle consolidation. Les fichiers de preuve du préfixe
`.codex-tests/global_HisabPro_20261010_2129_final` sont neufs ; aucune preuve
antérieure n’est écrasée. Node vérifié :v24.17.0.

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 .codex-tests/globale_2129.py figer
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 .codex-tests/globale_2129.py run
```

Le wrapper exécute `Test/run_unit_tests.py Test -vv --tb=short` avec JUnitXML,
dotenv désactivé et contrôle des SHA avant/après. Il conserve le véritable
code de sortie, le log et le XML. Lancement10octobre2026 à21:53:38UTC.

Le runner utilise SQLite mémoire pour les tests purs ; les API/migrations/
parcours connectés disposent de PostgreSQL éphémères vérifiés par URL,
répertoire et nonce. Le banc07b3 non isolé est explicitement exclu et n’est
pas présenté comme réussi. Aucun PostgreSQL utilisateur ou donnée réelle.

## Résultat final relu

Fin le 10 octobre à 23:00:23 UTC : **3 105 réussis, 7 échoués,
0 erreur, 0 ignoré**, 32 avertissements, 4 000,94 secondes, code **1**.
JUnit : 3 112 cas, durée 4 000,866 secondes. Contrôle SHA effectué après
achèvement : **684/684 fichiers identiques**, aucun changement pendant
l'exécution. La consolidation n'est pas validée.

Les sept échecs restent ouverts :

- Devis notes, Edge 1365 : connexion interrompue par un délai de navigation
  vers le dashboard ; écran « Failed to fetch ». Cause non établie.
- Capture RAS, achat/vente et 1365/390 : quatre annulations attendues 200
  répondent 422, « La date d’annulation ne peut pas précéder la capture RAS
  associée ». Le refus métier est conservé ; il faut comparer les dates
  réellement soumises avant toute correction.
- Effets, remise/rejet : deux dates attendues futures ne déclenchent pas
  HTTPException. Le test paramètre `date.today() + timedelta(days=1)` lors
  de l'import. La suite a traversé minuit en Europe/Paris : ce paramètre
  peut être devenu la date courante lors de l'exécution. Cette hypothèse
  doit être vérifiée sur une relance ciblée ; elle ne transforme pas les
  deux échecs en réussites.

Le budget de reprise allait jusqu'à 23:29 UTC. À la consultation finale
du 11 octobre après 00:42 UTC, il est dépassé : aucun nouveau développement
ou retest n'est lancé. Les preuves originales sont conservées. Prochaine
reprise : diagnostiquer ces sept cas sur environnement isolé, corriger la
cause minimale si reproduite, puis consolider à nouveau. Ensuite qualifier
la lecture API/UI des anciens documents à montants invalides.

Les69tests343 et91tests344 sont des sélections antérieures distinctes,
non additionnées à cette consolidation. La globale336,3009réussis, reste
la preuve de sa version avant341/343/344. Les anciennes globales échouées
et les erreurs de préparation des tests343 restent consignées.

La recette utilisateur, l’ouverture Office, le déploiement et les règles
fiscales/sociales encore bloquées restent des validations séparées.
