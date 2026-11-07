# Lot547 — registre PDF des congés et absences

## Fonction ajoutée

Dans **Paie / GRH → Congés & absences**, le bouton **Exporter le registre PDF**
reprend le filtre de statut de l'écran. L'export est disponible pour un compte
en consultation seule, comme la liste existante.

Le PDF contient l'identité et le logo facultatif de la société, les références
internes des demandes, salariés, périodes, jours calendaires et statuts, puis
les motifs, commentaires de décision et événements de l'historique. Les champs
absents restent identifiés comme non renseignés. Les textes sont échappés et
conservés intégralement, y compris sur plusieurs pages. Le pied de page porte
le numéro de page et la nature interne du document.

Le registre ne calcule aucun droit acquis, report de congé, retenue sur salaire,
taux social ou bulletin. Il ne constitue pas une déclaration officielle.
Aucune migration, donnée comptable, règle de décision ou permission modifiée.

## Construction et cohérence

`GET /api/employes/conges/export/pdf` accepte le paramètre facultatif `statut`
parmi demande/approuve/refuse/annule. Une sélection vide produit un registre
vide explicite ; un statut inconnu est refusé422. Le contexte société provient
du compte authentifié. Aucun identifiant de société fourni par le navigateur
n'est utilisé pour choisir les données.

La liste et l'export partagent leur requête de base. Pour le PDF, demandes,
salariés et événements sont lus ensemble par un seul SELECT ; la projection
`sortie` existante reçoit ces événements au lieu de les relire séparément.
Le rendu réutilise `logo_export_service`, sans réseau ou chemin d'image externe.
La lecture ne crée ni décision, ni archive, ni écriture.

## Tests réellement exécutés

- Avant développement :1échec/4désélectionnés,29avertissements,24.86s,code1 ;
  endpoint absent404, confirmé par inspection du routeur.
- Première qualification :4réussites/1échec,29avertissements,37.16s,code1.
  Le test de notes longues attendait25mentions ; les données contiennent
  également le motif dans l'événement de création, donc50mentions à exporter.
  L'oracle est précisé à partir des champs JSON effectivement enregistrés,
  sans supprimer ou masquer cet événement.
- Qualification finale : **5 réussites,29avertissements,32.53s**,code0.
- Connexes : **208 réussites,29avertissements,201.98s**,code0.
  `Test/run_unit_tests.py Test/test_grh_absences_service.py
  Test/test_grh_absences_postgres.py Test/test_paie_grh_service.py
  Test/test_paie_grh_postgres.py Test/test_parametres_paie_finis.py
  Test/test_paie_referentiel_service.py Test/test_paie_referentiel_postgres.py
  Test/test_e2e_grh_absences_isole.py Test/test_e2e_paie_grh_isole.py
  Test/test_e2e_paie_referentiel_isole.py -ra`.
  Les tests de services purs, anciens bacs PostgreSQL et E2E sont distingués
  des cinq nouveaux cas sur le serveur LOGIN098. Aucun échec/erreur/ignoré.
- `npm run build` : réussi,**5.10s**,code0 ; avertissements de bundles connus
  conservés. Trois Python compilés ;98SQL,115guides,models/main/AGENTS intacts.
  La qualification financière543 reste historique dans son périmètre ; elle
  n'est pas déclarée relancée pour cet export GRH indépendant.

Commande ciblée : `Test/run_unit_tests.py
Test/test_grh_registre_pdf_isole.py -ra`, avec `PYTHON_DOTENV_DISABLED=1`.

Les cas couvrent administrateur et lecteur, demandes approuvées/refusées/en
attente, filtre et sélection vide, logo réellement intégré au PDF, caractères
`<`, `>` et `&`, notes longues et deux sociétés distinctes. Le téléchargement
réel dans Edge390/1440px est effectué depuis le filtre Approuvée. Les tables
métier restent identiques ; l'accès sans session est refusé401. Sources figées
pendant les cinq cas, empreintes consignées.

## Installation et limites

Copier le routeur et le service PDF, redémarrer l'API ; copier `CNSS.jsx` et
reconstruire le frontend avec `npm run build` pour une version compilée.
Aucun SQL à exécuter. Le logo doit être une image intégrée compatible avec
le paramétrage existant ; les anciennes URL ne sont pas téléchargées.

Tests exclusivement sur PostgreSQL nonce et données fictives. La recette
utilisateur, les bulletins définitifs, déclarations sociales et conformité
réglementaire ne sont pas validés par cet export. Le point6 humain et les
115guides de recette existants restent en attente/inchangés.
