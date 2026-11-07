# Reprise après les qualifications et bases fiscales — 907/909

Le dépôt et le journal restent la source de vérité. Le lot907 a livré les qualifications séparées ; le lot909 prépare les bases depuis les snapshots brut/social et conserve les preuves. Le moteur de paie complet reste **partiel**.

Complément911 : la [comparaison après arrondi de la base annuelle](ARRONDI_BASE_ANNUELLE_911.md) est ajoutée aux nouveaux contrôles annuels, sans modifier les anciens. Elle ne traite pas les modalités mensuelles, les imputations ou un versement. Reprendre les empreintes et preuves911 lorsqu'elles sont présentes, plutôt que celles909 citées historiquement ci-dessous.

## Reprendre sans refaire les lots

Lire AGENTS, le master Personnel/Paie et le journal intégral ; exécuter `Test/journal_codex.py etat`, inspecter les processus et les ZIPs avant de relancer une commande. Les anciennes interruptions et la note ETIC de 2026 dans AGENTS sont historiques : ne pas les confondre avec l'étape active du journal.

Consulter [PREUVE_PAIE_909](../../Test/PREUVE_PAIE_909.json), [CANDIDAT_PAIE_909](../../Test/CANDIDAT_PAIE_909.json) et le manifeste909. Ne pas additionner les résultats recouvrants des ciblées et de la finale. La campagne907 comportait un ancien montage de restauration échoué, corrigé et rejoué séparément ; la preuve le distingue explicitement.

Créer un nouvel identifiant et un nouveau baseline avant toute prochaine modification. Ne pas réécrire les SQL113–120 ni les snapshots. Aucun PostgreSQL utilisateur, `.env`, clé ou écriture réelle ne doit servir aux tests. Les fixtures natives existantes vérifient leur répertoire et nonce avant DDL, sauvegarde ou restauration.

Reprise ciblée portable, depuis la racine, avec les dépendances du projet déjà installées :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
$env:DATABASE_URL='postgresql://audit_inactif:valeur_fictive@127.0.0.1:1/aucune_base'
.\hisabpro-backend\.venv\Scripts\python.exe -m pytest Test/test_paie909_bases_unitaire.py Test/test_paie909_bases_isole.py -q
```

Cette URL est volontairement inutilisable et ne remplace pas la cible native éphémère créée par les fixtures. Ne pas lancer `main.py` sur l'environnement habituel pour reproduire un test destructif.

## État exact à préserver

- 119 : qualifications de base des frais et de déductibilité salariale, avec preuves et approbateur indépendant habilité ; absence historique inconnue.
- 120 : préparations fiscales immuables, FK sociale et société, reprise idempotente et versions successives ; sources courantes vérifiées au calcul, histoire consultée sans recalcul.
- Le revenu affiché est **avant frais professionnels et autres déductions**. RNI définitif, IR et net sont nuls au sens JSON `null`, jamais un montant zéro présumé.
- Le calcul actuel couvre les bases des mois complets déjà supportés par le brut. Retenues/remboursements non qualifiés, entrées/sorties et changements dans le mois restent bloquants.
- Une déduction partielle ou plafonnée ne devient pas une déduction intégrale par défaut. Le contrôle explicite de l'éligibilité du montant reste nécessaire.

## Prochain travail métier

1. **Frais professionnels.** Le CGI2026 complet a été obtenu depuis leCRI ; articles58/59 lus, SHA et pages dans [le rapport de sources907](SOURCES_FISCALES_907.md). Distinguer le revenu servant au seuil et la base après exclusion des avantages ; vérifier le cadre général59-I-A et les catégoriesB/C. Les paramètres annuels ne justifient pas à eux seuls les modalités mensuelles. Tester indépendamment seuil, plafond, avantages et situations particulières avant de coder.
2. **Autres déductions.** Qualifier les conditions et plafonds réellement applicables aux retraites, prévoyance, assurance-groupe et financement du logement. Ne pas étendre la seule qualification binaire907 à un montant partiellement éligible. Une absence d'information n'est pas une déclaration de zéro.
3. **Cumuls et paiement.** Définir les périodes et sources effectivement retenues ; sélectionner explicitement les préparations d'un salarié et éviter le double comptage de plusieurs versions d'un même mois. Le parcours905 prouve douze mois sociaux réels de test ; il ne constitue pas un cumul fiscal ni une preuve de paiement. La période de variable n'est pas la date de paiement visée par156.
4. **Retenue et arrondis.** Obtenir et lire la doctrine officielle applicable sur mensualisation et régularisations. L'article167 a été lu ; distinguer l'arrondi d'une base et celui d'un versement. Ne pas diviser aveuglément un impôt annuel ou multiplier une prime ponctuelle par douze. Ne pas réutiliser le helper historique de salaire fixe comme moteur intégré.
5. **Famille et suite.** Conserver l'éligibilité confirmée et ses sources, sans inférence depuis l'état civil. Le contrôle annuel901 reste une primitive séparée sur RNI déclaré. Net, bulletins, clôture/validation de paie, paiements, OD et déclarations restent les lots suivants.

Si une règle manque, documenter le point précis et poursuivre les développements indépendants. Une difficulté d'accès à un site ne prouve pas l'absence du texte. Aucun résultat de recette utilisateur, conformité officielle ou disponibilité de production ne doit être affirmé automatiquement.

[Guide909](BASES_FISCALES_CONNECTEES_909.md) · [Index de recette](MODE_EMPLOI_PERSONNEL_PAIE.md).
