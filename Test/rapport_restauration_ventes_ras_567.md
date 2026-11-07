# Lot 567 — Reprise des ventes et de l'assistant RAS TVA

Test réel : **1 réussi, 29 avertissements, 71,99 s, code 0**.
Commande : `Test/run_unit_tests.py Test/test_restauration_ventes_ras_tva_isole.py`.

Deux clusters PostgreSQL nonce distincts, sauvegarde `pg_dump` puis restauration
`pg_restore`, API complètes sous LOGIN applicatif non propriétaire. Aucun mock
des calculs ou des réponses. Les enveloppes du banc ajoutent uniquement les
migrations existantes092–098 avant le démarrage et les contrôles supplémentaires.
Les anciens fichiers SQL et bancs sont conservés.

Après restauration :

- 74 tables, schéma, données, séquences et ACL restitués à l'identique avant reprise.
- JSON de préparation identique hors heure de consultation ; CSV et empreinte
  identiques. CA150,00 MAD, HT documentaire100,00 MAD, écart50,00 MAD.
- Texte du PDF identique et logo présent ; valeurs Excel identiques et feuille
  Comptabilité complète. Le logo provient de la société fictive restaurée.
- Même résultat de simulation RAS TVA :75,00 MAD, net525,00 MAD. Aucun
  règlement, écriture ou déclaration n'est créé par la simulation.
- Aucun changement des tables métier pendant ces lectures ; source préservée.
  Les pistes FEC/justificatifs et décisions du scénario parent sont aussi
  contrôlées réellement. Cibles et processus créés par le banc nettoyés.

L'ancien rapport technique452 est restauré après capture de la preuve567 pour
ne pas réécrire la preuve historique. Le scénario parent porte sur la banque,
clôture et pièces : aucun scénario RH/paie supplémentaire n'a été développé.

[Exemple PDF avec logo entièrement fictif](../docs/audit/exemples/VENTES_RACCORDEMENT_LOGO_FICTIF_20261018.pdf).

Ces vérifications ne constituent ni une restauration de production, ni une
recette utilisateur, ni la prise en charge complète de la RAS TVA.
