# IR annuel depuis un RNI constitué — lot915

Dans **Personnel & Paie → 05 · Fiscalité salariale**, un contrôle annuel peut maintenant reprendre le RNI d’un contrôle des frais annuels complet. Le montant ne se ressaisit pas. Cette étape relie les douze préparations mensuelles au contrôle annuel ; elle ne constitue pas encore un moteur de retenue mensuelle ou une paie définitive.

Sur une **copie isolée**, installer la migration additive `122_paie_ir_sources_annuelles.sql` après121, selon la [procédure119–122](INSTALLATION_COPIE_PAIE_119_122.md). Le démarrage habituel ne remplace pas cette installation. Les migrations antérieures restent intactes. Aucune migration n’a été exécutée sur la base habituelle de l’utilisateur.

1. Constituer les douze mois du [jeu913](JEU_FRAIS_ANNUELS_PAIE_913.json) et suivre le [guide des cumuls](CUMULS_FRAIS_ANNUELS_913.md). Choisir une seule version de préparation fiscale par mois. Les règles synthétiques de ce jeu servent exclusivement aux tests et ne sont pas des règles autorisées pour une paie réelle.
2. Dans le résultat du contrôle annuel complet, cliquer **Contrôler l’IR de ce RNI**. Le formulaire reprend l’identifiant réel du contrôle. Cliquer **Charger le RNI annuel** et vérifier salarié, année, montant exact et empreinte.
3. Confirmer séparément le contrôle annuel source et l’application du barème général. Ces confirmations exigent un examen des revenus, déductions et éventuels cas particuliers ; elles ne doivent pas être cochées automatiquement.
4. Pour le jeu fictif, choisir **2** personnes à charge, saisir **FAMILLE-FICTIVE915** et le motif **Contrôle IR sourcé FICTIF915**. Confirmer l’éligibilité familiale et le périmètre arithmétique. En exploitation, une famille inconnue reste inconnue, y compris lorsqu’aucune personne n’est déclarée.
5. Cliquer **Calculer et conserver l’IR annuel sourcé**. Comparer les valeurs ci-dessous. Le lien **Consulter le contrôle des frais annuels source** permet de revenir aux douze préparations et à leurs références.

| Valeur du jeu fictif | Attendu MAD |
|---|---:|
| RNI constitué avant arrondis | 83881.0200 |
| Base annuelle à la dizaine supérieure | 83890.00 |
| Tranches :2000+4000+1167 | 7167.0000 |
| Réduction familiale :2×600 | 1200.0000 |
| IR annuel arithmétique après réduction | 5967.0000 |

Le calcul réutilise le barème annuel et l’éligibilité familiale déjà présents. La base est arrondie **avant** le passage dans le modèle monétaire à deux décimales ; le RNI source à quatre décimales reste conservé séparément. Il n’y a ni troncature du RNI ni conversion d’un mois en année. L’ancienne saisie manuelle annuelle et les snapshots historiques restent disponibles avec leurs résultats d’origine.

L’arrondi de base provient du CGI2026, article167, page imprimée317, relu dans [le document DGI publié par le CRI Casablanca-Settat](https://casainvest.ma/sites/default/files/2026-02/Code%20impo%CC%82ts%202026.pdf). Empreinte SHA256 du document consulté : `fe03c94471aefd23a9be9de11da5bff0593b45a72c2f90939eeaae7298b413e1`. Barème et famille : articles73-I et74, sources conservées dans le contrôle annuel. Aucune nouvelle doctrine de mensualisation n’est déduite de ces règles annuelles.

Une source partielle ou dont les variables, règles ou préparations actuelles ne correspondent plus est refusée pour un nouveau calcul. Les anciens contrôles restent consultables ; une reprise avec la même clé et la même demande restitue le même snapshot. La base impose des liens de société et interdit modification, suppression et réaffectation du lien annuel. Une erreur de migration rend le nouveau parcours indisponible sans effacer les contrôles manuels antérieurs.

Les autres déductions du RNI restent déclarées et justifiées dans le contrôle913 : ce raccordement ne valide pas automatiquement leurs conditions juridiques. Aucune échéance ou date de paiement n’est déduite de la période comptable.

La retenue mensuelle, les imputations, le versement, le net, les bulletins et les écritures de paie restent à développer. Le résultat annuel n’est ni une somme à verser ni une certification. La recette utilisateur et la mise en production restent à valider.

[Cahier PDF](RECETTE_IR_SOURCE_PAIE_915.pdf) · [Suivi Excel](SUIVI_IR_SOURCE_PAIE_915.xlsx) · [Données exactes](JEU_IR_SOURCE_PAIE_915.json).
