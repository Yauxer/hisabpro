# Année, clôture et lettrage sous LOGIN applicatif — lot 444

Deux causes distinctes ont été reproduites sur le schéma complet sous un vrai
LOGIN SQL non propriétaire, puis corrigées par migrations additives manuelles.

- 088 : SELECT/INSERT sur clotures_exercice et USAGE/SELECT de sa séquence ;
  SELECT seul sur bareme_ir,taux_cotisations,deductions_ir. Ni édition de taux,
  ni qualification sociale nouvelle, ni UPDATE/DELETE de trace de clôture.
- 089, après049/053 : le déclencheur lettrage identifie le tiers par tiers_id,
  puis auxiliaire figé, puis libellé comme repli historique. Les à-nouveaux et
  règlements du même tiers peuvent avoir des libellés différents. Deux tiers
  distincts ne deviennent pas identiques parce que leur libellé est le même.

SHA088 : `fda06dcc9a681bbf9a4e899a2c623f362122c96f9ee95c869a9505e85a65f112`.
SHA089 : `5ffb8e0b1cdf262ec58d5787e00c3ad52d5cd1d03b1b5bf50488730bc99afbb2`.

089 remplace uniquement la fonction existante ; aucun déclencheur désactivé,
aucune écriture/ligne/groupe historique modifié. Comparaison textuelle des quatre
blocs de gardes049 réussie : société, validation, clôture, historique/délettrage,
portée du code et conclusion de contrôle restent identiques. Le contrôle différé
d'équilibre et les définitions/états des déclencheurs restent inchangés sur PG.
La normalisation SQL historique du repli est conservée ; pas de prétention à
une normalisation Unicode universelle commune à tous les anciens auxiliaires.

## Tests réellement exécutés

16 ciblés réussis en70.72s, puis 43 connexes réussis en 208.474s XML,
zéro échec/erreur/ignoré ;compilation des deux fichiers Python code0.
Les deux cas supplémentaires lecture/RBAC et rôle088absent sont inclus dans
la suite connexe. Les suites se recouvrent :ne pas additionner leurs nombres.
Avertissements de dépréciation existants maintenus.

- Année2025→2026, même société :facturation vente/achat, ventilations240,
  lettrage partiel, TVA lue selon l'oracle existant et relevé de trois opérations
  pour cinq lignes bancaires. Solde1000,flux1480 ;clôture/résultat laboratoire−3000,
  à-nouveaux4180, puis soldes120 de chaque sens sur anciennes factures.
  Lettrage des AN/paiements, deux lignes bancaires2026/flux240 et solde1000.
  Lecture seule2025, exports FEC deux exercices et balance Excel4060/4060 vérifiés.
- Dégressif60000 sur5ans, réseau normal et latence250ms :24000/14400/8640/6480/6480,
  acquisition72000 et cinq dotations définitives,6pièces débit=crédit=132000,
  VNC0, acquisition originale préservée et absence de doublon. Éligibilité fiscale
  réelle du bien non validée par ce scénario technique.
- Dix testsSQL089 :deux cycles client/fournisseur avec libellés distincts et
  délettrage tracé ;sept refus atomiques (tiers,compte,exercice différents,
  déséquilibre,brouillon,exerciceclos,autresociété), puis rejeu sans mutation des
  tables/ACL et conservation de l'historique. Écritures définitives identiques.
- 088 :quatre ACL fermées, droits hors périmètre et UPDATE des séquences inchangés ;
  refus d'UPDATE/DELETE/TRUNCATE, rejeu sans mutation. Les vraies traces de la
  clôture restent immuables même pour le propriétaire. Lecture de provenance
  paie200, lecteur authentifié403 sur clôture ;rôle absent, aucun objet créé.
- Anciens parcours de lettrage/clôture/année et cinq Edge runtime442 réexécutés.

Commande connexe :Test/run_unit_tests.py avec test_lettrage_identite_auxiliaire_postgres.py,
test_e2e_runtime_annuel_isole.py,test_lettrage_final.py,test_lettrage_codes_trois_lettres.py,
test_e2e_lettrage_concurrence_isole.py,test_e2e_cloture_isole.py,
test_e2e_annee_connectee_isole.py,test_e2e_runtime_consolide_isole.py.

## Échecs intermédiaires conservés

Baseline087 :1échec65.45s (attente réponseEdge ;log réel SQL42501sur clôtures
et lectures de référentiels). Après088 :1échec38.75s, clôture réussie puis
SQL23514au lettrage AN/paiement de même tiers mais libellés distincts.
Après089 :année seule réussie39.92s,logAPIvide.
Premier banc SQL :4réussites/1échec23.49s,route exercices absente du FastAPIminimal ;
route réelle ajoutée au fixture,aucune règle contournée. Ciblés16 réussis ensuite.
Premiers connexes :16réussites/1échec65.62s ;email@example.invalid de la nouvelle
fixture refusé422parEmailStr. Test corrigé vers@example.com ;aucun email envoyé.
La validation d'email et l'application ne sont pas assouplies.
Tous XML/logs/exit et logs API nonce sont conservés dans le bac de session.

## Limites et suite

Les anciens bancs annuels utilisaient un manifeste partiel :leur réussite
historique ne validait pas la coexistence049/053du schéma consolidé.
Les nouveaux parcours la testent ;ce défaut n'est pas propre au LOGIN runtime.
Les oracles chiffrés antérieurs sont inchangés, sans nouvelle règle fiscale.
PostgreSQL jetable et données fictives uniquement ;aucune base réelle.
088/089 restent manuelles,horsbootstrap ;installation087/restore084 ne sont pas
annoncées couvrir089. L'édition des taux sociaux globaux n'est pas provisionnée
par ces seuls droits de lecture ;le référentiel qualifié par société reste à terminer.
Recette humaine, production et conformité officielle non validées. Point6enattente.
Prochaine étape :consolider installation089 puis restauration des droits et
gardes sur cible vide isolée, avant couverture et cumulatif.
