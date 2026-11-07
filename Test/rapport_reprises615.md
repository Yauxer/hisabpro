# Lot615 — reprises partielles de provisions

## Changements utilisables

Clôture comporte désormais un panneau de reprises lié aux dotations existantes,
y compris celles d’un exercice antérieur clôturé. Une source doit être validée,
ses deux lignes réelles doivent recouper son dossier et la nature doit être
qualifiée. Une source orpheline, déjà contrepassée, incohérente ou portant un
montant historique inexploitable reste signalée sans bloquer les autres sources.

L’aperçu est une lecture RO/RR, sans préparation de calendrier ou écriture.
Il présente comptes/libellés, débits/crédits exacts, date réelle de destination,
capacité et empreinte des faits. Les références justificatives ne deviennent
pas obligatoires pour créer/valider ; un FEC sans justificatif reste refusé
par le contrôle documentaire existant.

Le brouillon conserve source/faits/acteur/clé UUID technique dans un registre
immuable. Les réservations consomment la capacité ; deux demandes concurrentes
ne peuvent pas utiliser deux fois le même montant. Une même clé avec mêmes
faits est rejouable sans doublon ; mêmes clé/autres faits :409.

L’annulation conserve la pièce initiale et produit un inverse en brouillon.
La capacité n’est libérée qu’après validation des deux pièces, à la date de
l’inverse. Le calcul réserve aussi les reprises futures : une annulation de
juin ne finance pas une reprise de mars. Cette règle est contrôlée dans le
service et dans le dernier rempart SQL, sous verrou de la source.

Les commandes génériques modifier/supprimer/contrepasser du Journal refusent
les sources liées, reprises et inverses. La validation ordinaire reste possible,
avec garde contre la validation d’un inverse avant son original. Le lot du
Journal peut valider les deux dans l’ordre chronologique.

## Persistance et compatibilité

Migration100 additive, explicite, rejouable, deux tables dédiées, FK sur les
clés réellement existantes ; aucune contrainte composite supposée, aucun modèle
ajouté au bootstrap. Sans100 :503 explicite dans le seul panneau, démarrage et
Journal préexistants conservés. Droits applicatifs SELECT/INSERT sur registres,
UPDATE/DELETE/TRUNCATE interdits ; triggers de cohérence/immutabilité et protection
des pièces. Aucune ancienne migration ou donnée comptable réelle modifiée.

[Mode d’emploi et installation séparée](../docs/REPRISES_PROVISIONS_615.md).
[Sources CGNC et périmètre qualifié](../docs/audit/SOURCES_PROVISIONS_20261019.md).

## Tests réellement exécutés

Consolidation finale :139réussis en228.306s ; compatibilité UUID/Edge/lecture :5réussis en56.739s (quatre parcours déjà couverts dans la consolidation, ne pas additionner comme cas uniques) ; restauration native100 :1réussie en50.520s,77tables. Aucun échec/ignoré dans ces commandes finales. Build Vite réussi et Python compilé. Compatibilité avec absence de crypto.randomUUID testée sans remplacer les API métier.

Commandes finales :

```powershell
$env:PYTHON_DOTENV_DISABLED='1'
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_reprises_provisions.py Test/test_consolidation_reprises615_isole.py Test/test_lecture_reprises615_isole.py -q
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_restauration_reprises615_isole.py -q
npm run build
```

Preuves de mise au point conservées : premier passage43cas/2échecs de fixture
(exercice créé deux fois), puis43réussis ; deux essais Edge échoués d’abord
sur un libellé non accessible, puis sur un scénario sans référence de pièce,
suivis de2réussis après correction. Consolidation130cas/1échec source orpheline,
et reproduction chronologique1échec (200 au lieu409). Ces échecs sont consignés,
pas présentés comme des réussites. Les63cibles suivantes ont réussi.

## Limites

Registre lié uniquement, jamais solde global imputé par heuristique. Les reprises
manuelles historiques, sources ambiguës et choix non qualifiés nécessitent
une analyse distincte. Aucune détermination de risque, règle de déductibilité
fiscale ou reprise automatique au calendrier. Sources officielles indexées
effectivement consultées, pas de revue intégrale du PDF revendiquée.

Les tests utilisent exclusivement PostgreSQL natif jetable et des sociétés
fictives ; SQLite ne remplace pas les protections PostgreSQL. Installation100
sur la base utilisateur, recette visuelle humaine, Excel interactif et mise en
production non exécutés. RH/paie et recette humaine globale restent différées.
