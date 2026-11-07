# Catalogue d'écritures : avances au personnel —464

Cinq nouveaux modèles facultatifs dans Journal → Nouvelle écriture → Choisir
un modèle → Paie : versement par banque/espèces, récupération sur rémunération
déjà due, remboursement par banque/espèces. Catalogue de 59 à 64 dans le laboratoire.
Les comptes, sens et limites figurent dans la
[revue des sources](../docs/audit/SOURCES_MODELES_PERSONNEL_20261015.md).

Les écritures naissent uniquement après saisie/enregistrement par l'utilisateur.
Aucun salarié, montant, droit à retenue ni bulletin n'est inventé. L'avance n'est
pas automatiquement intégrée au calcul du bulletin ; ce module reste distinct.
Ne pas ressaisir une opération déjà comptabilisée par un autre flux.

Si plusieurs modèles correspondent au même compte, l'interface demande de
choisir l'opération ; elle ne prend plus arbitrairement le premier résultat.
Les réponses tardives d'une ancienne recherche de compte sont ignorées.

Le cycle complet a découvert un défaut antérieur : le journalSAexistant en
base et dans l'interface manquait dans l'énumération des saisies API. Ajout deSA
au seul schéma API ; CLreste réservé au moteur de clôture.

## Exécution et livraison

- Première suite :42 réussis 60,50 s. Le cycle ajouté ensuite a réellement
  reproduit le refus 422 SA(19 réussis/1 échec 131,86 s).
- Après correctifSA :20 réussis et 1 échec 115,38 s, dû à un oracle incluant à tort
  le journalCLréservé. Seul cet oracle a été corrigé ; CLn'a pas été autorisé.
- Suite finale : **21 réussis 110,58 s**,29 avertissements, exit 0 :
  `python -X utf8 Test/run_unit_tests.py Test/test_modeles_avances_runtime_isole.py Test/test_e2e_modeles_detection_isole.py Test/test_e2e_modeles_journal_lettrage_isole.py Test/test_patch063_tiers_libelles_modeles.py -ra`.
- PostgreSQL jetable 092 et vrai serveur sous LOGIN limité. Rejeu 092 deux fois,
  anciennes tables/droits préservés et séquences inchangées ; modèle nouveau
  personnalisé/désactivé non écrasé au rejeu. Cinq schémas API complets, sansTVA.
- Edge 1440/390 : choix explicite 3431, versement puis remboursement 1000,
  écritures définitives équilibrées et 3431/5141 soldés.
- Cycle API des cinq modèles : soldes d'ouverture fictifs 13000 banque,
  10000 capital et 3000 rémunération déjà due. Alimentation caisse 1000 ; avances
  1200 banque+800 caisse ; récupération 1500 ; remboursements 200 banque+300 caisse ;
  règlement du reliquat de rémunération 1500. **8 écritures/17 lignes, débit=crédit
  19500**,3431=4432=0, banque 9500,caisse 500,capital 10000. Aucun compte 6/7,
  aucun calcul de paie/fiscalité prétendu. FEC 18 colonnes exporté,17 lignes.
- BuildVite 5,48 s, exit 0 ; compilation ciblée avant livraison.

La migration additive 092 est fournie mais n'a jamais été appliquée à une base
utilisateur. Installation à contrôler par l'administrateur après 091 et sauvegarde,
sous propriétaire des tables ; ancien schémaSQLinchangé. Les nouveaux modèles
apparaissent après cette migration ; la correctionSAest livrée dans schemas.py.
La qualification réglementaire exhaustive et la recette humaine restent ouvertes.

Prochaine étape : correction du changement de taux d'un modèle de vente, dont
la reproduction Edge a montré une confusion entre leHTet leTTCprincipal.
