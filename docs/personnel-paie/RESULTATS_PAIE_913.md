# Résultats — cumuls et frais annuels913

**176 cas distincts réussis** dans la finale, sans échec, erreur ou test ignoré : {'unitaires_source': 134, 'API_SQL_restauration_PostgreSQL_natif_isole': 36, 'navigateur_Edge_API_PG_isole': 6}. Les campagnes recouvrantes ne sont pas additionnées. Le premier montage TRUNCATE a été corrigé pour atteindre le trigger plutôt que le refusFK antérieur ; la chronologie reste dans [la preuve](../../Test/PREUVE_PAIE_913.json).

Douze mois effectivement préparés sur PostgreSQL natif : cumuls111601.32/base108001.20/déductible720.00, frais27000.3000 etRNI83881.0200 avant arrondis. Le seuil utilise le brut imposable, la base des frais exclut les avantages concernés. Autres déductions inconnues, cadre non confirmé, année partielle et sources périmées ne deviennent pas des zéros ou une annualisation. Choix d'une seule version par mois, idempotence concurrente, FK de société, profil Personnel fermé et invariants d'immutabilité vérifiés.

Edge1440/390 : douze choix réels par salarié, bouton limité aux versions uniques, calcul exact, mois retiré etanomalie explicite, ancien résultat conservé, liens de source, onglets etrévocation, absence de données dans le stockage navigateur etcomptabilité inchangée. Restauration native98tables, douze liens source etRNI relus sousrôlelimité, schéma/données/séquences/ACL identiques, prédicat d'index altéré détecté, source intacte etseconde cible nonce supprimée.

Build : {'code': 0, 'modules': 211, 'secondes_vite': 5.89, 'avertissements': 'xlsx/chunks existants'}. Compilation : 13 fichiersPython ; candidat534empreintes. Migration121 additive rejouée deuxfois puis avecdonnées, aucun SQL antérieur modifié.129cas humains dans onze ensemblesPDF/Excel, tous Non testé. Le nouveau classeur comprend Synthese, IRAnnuel, Donnees etPeriodes, avec les douze références exactes.

[Guide](CUMULS_FRAIS_ANNUELS_913.md), [recettePDF](RECETTE_FRAIS_ANNUELS_PAIE_913.pdf), [suiviExcel](SUIVI_FRAIS_ANNUELS_PAIE_913.xlsx). La règle annuelle59-I-A a été relue dans le documentDGI2026 duCRI ; les catégories particulières et la mensualisation restent à traiter. Ce contrôle ne prouve pas un paiement ou une conformité officielle.

Suite : contrôleIR annuel relié auRNI constitué, puis qualification de la retenue mensuelle et des cas complexes avant net/bulletins. Aucune base habituelle, clé ou donnée comptable réelle utilisée.
