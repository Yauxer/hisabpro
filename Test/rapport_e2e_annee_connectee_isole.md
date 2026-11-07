# Recette annuelle connectée réduite — 8 octobre 2026

## Périmètre et oracle

Une seule société fictive SARL et un même exercice 2025, suivis de l'ouverture 2026. Les opérations passent par les routes métier normales sur une instance FastAPI reliée à PostgreSQL éphémère protégé par nonce. Les parcours navigateur utilisent Microsoft Edge. Aucun mock métier, aucune base réelle et aucune modification directe de lignes comptables ne sont utilisés.

L'oracle indépendant `docs/recette/oracle_annee_connectee_2025.json` est écrit avant le premier test. Empreinte SHA-256 initiale : `33f1fe632ecf6e3db6f03e6fedb85b407da76c8f3a49addc390f50250ad0ac5a`. Son calcul de journal utilise uniquement Decimal, sans importer de moteur comptable/fiscal HisabPro. Le dossier complet de 218 cas utilisateur existant n'est pas remplacé par ce parcours réduit.

Capital bancaire 20 000 MAD ; achat de 10 unités à 100 HT, TVA 200 et TTC 1 200 ; vente de 4 unités à 200 HT, TVA 160 et TTC 960. Paiements client 360 en mars puis 600 en juin ; fournisseur 600 en mars puis 600 en juin. Les deux comptes auxiliaires sont soldés et lettrés sur trois lignes chacun. Stock final physique 6 unités × CMUP 100 = 600 MAD.

Immobilisation informatique acquise et mise en service au 1er janvier 2025 : 1 200 HT + 240 TVA = 1 440 TTC, non payée, durée linéaire 3 ans, dotation annuelle 400 et VNC fin 2025 de 800. La dette reste au 4481, les 240 restent au débit du 34551 ; la déclaration TVA ne déduit pas ces 240 et doit signaler l'acquisition non payée.

Résultat avant impôt : 800 − 1 000 + 600 − 400 = 0 MAD. Banque : 20 000 + 960 − 1 200 = 19 760 MAD. Dix écritures définitives / 23 lignes avant impôt, débit = crédit = 26 760 MAD.

## Qualification explicite du profil de laboratoire

La constitution et l'exploitation fictives sont posées au 1er janvier 2020, sans concession de service public. L'année de début est configurée à 2020 ; les dates précises figurent dans l'oracle et la justification fiscale, car la société ne possède pas de champs dédiés permettant leur qualification automatique. Les paramètres enregistrés par API sont droit commun, sans exonération CM ni exonération du minimum, sans exclusion ni taux réduit.

L'oracle d'intégration utilise les paramètres déjà livrés : base 800 × 0,25 % = 2 MAD ; minimum 3 000 ; IS théorique zéro ; impôt attendu 3 000. Résultat net −3 000, report au débit de 1199 de 3 000 et dette 4453 de 3 000. Les à-nouveaux attendus sont équilibrés à 25 000 MAD. Ce scénario contrôle la cohérence du profil explicite de laboratoire ; il ne qualifie pas un dossier réel et ne revendique aucune validation du CGI.

TVA d'encaissement : mars collectée 60, récupérable 100, due zéro et crédit final 40 ; juin collectée 100 et récupérable 100, due zéro, crédit antérieur/final 40 ; annuelle collectée 160, récupérable 200 et crédit 40. Le chiffre juin zéro du premier plan désignait le solde propre de juin ; l'oracle a distingué le crédit reporté pendant l'analyse, avant tout test. Le report est une simulation calculée des périodes précédentes, pas une déclaration déposée ou figée.

## Commande et état d'exécution

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
./hisabpro-backend/.venv/Scripts/python.exe -X utf8 Test/run_unit_tests.py Test/test_e2e_annee_connectee_isole.py -x
```

- Premier run : oracle pur réussi, parcours arrêté avant les opérations navigateur, 1 réussi / 1 échoué en 37,54 s. Le sélecteur du test cherchait le label « Exercice actif » sur le sélecteur global du Layout, qui ne le porte pas. Le label existe dans GestionExercices sur d'autres pages ; ce résultat ne constitue pas une régression de ces tests existants. Le test utilise désormais le sélecteur global contenant l'option de l'année demandée, sans modifier l'application.
- Deuxième run : oracle pur réussi, validation des deux factures, quatre paiements, huit écritures et lettrage client effectués. Arrêt au choix du tiers fournisseur, 1 réussi / 1 échoué en 41,65 s. Le chargement de Lettrage.jsx ne protège pas les réponses de requêtes concurrentes ; une liste client tardive peut remplacer la liste fournisseur après un changement rapide de compte. Cette anomalie a été signalée à l'agent principal avant toute correction de source. Aucune donnée ni oracle n'a été ajusté pour la masquer.

## Résultat final exécuté

Après correction séparée de la concurrence du lettrage et livraison vérifiée du ZIP 222, la même commande annuelle est **réussie : 2 tests, 23,95 s, exit 0**. L'oracle est resté identique à son empreinte initiale ; son SHA-256 a été vérifié après exécution. `py_compile` du fichier de test : exit 0.

Le parcours navigateur valide réellement les deux factures, les quatre paiements et les écritures, puis lettre les trois lignes client et les trois lignes fournisseur. Le stock final, la banque, les soldes par compte et les totaux sont contrôlés contre l'oracle indépendant. Les simulations TVA de mars, juin et annuelle conservent le crédit 40 et signalent l'immobilisation non payée sans déduire sa TVA 240. La dotation 400 et l'écriture de stock 600 sont générées et validées. Le contrôle de clôture est équilibré, sans brouillon ni dotation manquante ; l'impôt du profil de laboratoire est 3 000.

La clôture verrouille l'exercice et ses périodes, refuse une nouvelle écriture et une seconde clôture, solde les comptes de gestion, puis génère les à-nouveaux 2026 équilibrés à 25 000 avec perte 3 000 et dette fiscale 3 000. Les lignes préexistantes sont inchangées. La navigation et le rechargement affichent les à-nouveaux. Les deux aperçus FEC sont exportables et les exports texte 2025/2026 sont réellement produits.

Cinq téléchargements navigateur sont ouverts et contrôlés : balance générale 2025 XLSX/PDF, balance résultat 2025 XLSX, balance des à-nouveaux 2026 XLSX/PDF. Les classeurs sont lus avec openpyxl, les PDF avec leur parseur réel ; banque 19 760, résultat avant clôture zéro, perte reportée 3 000 et totaux des à-nouveaux 25 000 sont vérifiés. Aucune erreur JavaScript ni réponse serveur 500 n'a été observée.

## Limites

Cette recette intégrée reste un scénario réduit, avec un profil fiscal de laboratoire explicitement paramétré. Elle ne couvre pas une année utilisateur complète ni tous les 218 cas du cahier existant. Aucun PostgreSQL réel n'a été utilisé. Les dates fictives de constitution/exploitation n'ont pas de qualification automatique dans le modèle société. Le report TVA est une simulation et ne prouve ni dépôt ni gel d'une déclaration. IR, CNSS, RAS, déclarations officielles et validation réglementaire sont hors de ce lot. La recette utilisateur, les données historiques réelles et la readiness de production restent à valider séparément.
