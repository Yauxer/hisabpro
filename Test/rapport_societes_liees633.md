# Lot633 — sociétés liées et tiers explicites

Deux tables additives101 : relations vendeur/acheteur avec client/fournisseur
et retraits motivés. Registres append-only, contrôle SQL des sociétés et types
de tiers, sérialisation d'une paire et refus des doublons actifs. Aucune facture
ni écriture créée. Aucun main/modèle ORM/bootstrap ou ancien SQL modifié.

API `/api/societes/liaisons` : création administrateur dans les deux sociétés,
droits relus après verrou, sélection des tiers existants, ICE incompatibles
refusés, idempotence des clés, liste filtrée selon les accès effectifs et retrait
unilatéral motivé sans fuite d'identité devenue inaccessible. UI dédiée dans
Paramètres, contexte société/jeton protégé et consultation seule sans formulaire.

Commandes exécutées avec PYTHON_DOTENV_DISABLED=1 :

```powershell
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_multi_societes_runtime_isole.py -q -x
.\hisabpro-backend\.venv\Scripts\python.exe -X utf8 Test/run_unit_tests.py Test/test_societes_liees633_isole.py -q -x
npm run build
```

Baseline multi-societes7passes104.423s ; suite63312passes41.222s, 0echec/erreur/ignore ; build final OK ; Python compile. API/LOGIN nonce/Edge1440 et390 et lecteur, registres et ACL preserves au rejeu non vide.
Premiers essais : erreur du banc observer sans api_url, puis nom accessible des
select incluant les options ; signature et aria-label corrigés avant relance.
Ces échecs restent conservés, pas présentés comme des réussites. Le build7,10s
initial a réussi ; build final après aria-label contrôlé séparément.

PostgreSQL natif jetable uniquement, LOGIN limité et Edge réel, jamais SQLite.
101 rejouée avant puis après des données non vides, schéma/données/ACL préservés.
Migration utilisateur, recette humaine et production non validées. Association
déclarée seulement, pas preuve d'un groupe fiscal. Pont de facturation635 à
développer après livraison633. RH/paie et point6 humains restent différés.
