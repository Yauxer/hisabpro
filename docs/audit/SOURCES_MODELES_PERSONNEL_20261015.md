# Modèles d'avances au personnel — vérification du 15 octobre 2026

Périmètre : cinq aides à la saisie au Journal, avances à moins d'un an, montants
et pièces renseignés par l'utilisateur. Aucun taux, aucun droit automatique à
une retenue, aucune règle de calcul de bulletin ni échéance supposée.

## Sources consultées avant codage

- [CGNC hébergé par l'OEC Casablanca](https://oec-casablanca.ma/app/webroot/img/uploads/Code_general_de_la_normalisation_comptable.pdf) : passage 343 Personnel débiteur obtenu dans l'index du document. Il confirme le débit 3431 par trésorerie et son apurement par classe 4 ou 5. L'ouverture intégrale a échoué 502 ; aucune empreinte du binaire calculée.
- [MEF/CNC — plan comptable du secteur immobilier, page imprimée168](https://www.finances.gov.ma/Publication/depp/2022/Plan%20comptable%20du%20secteur%20Immobilier.pdf) : passage 343 obtenu par recherche indexée officielle ; versement par trésorerie, récupération par 4432 ou trésorerie lors du remboursement.
- [MEF/CNC — plan comptable agricole, page imprimée99](https://www.finances.gov.ma/Publication/depp/2017/Plan%20Comptable%20Agricole%20-vf-dec2015.pdf) : même mécanisme obtenu dans l'index officiel.
- Le [catalogue ministériel des normes](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx) identifie les tomesCGNC ; son ouverture directe reste en timeout.
- [plancomptable.ma —3431](https://www.plancomptable.ma/3431-avances-et-acomptes-au-personnel/) a servi à repérer un exemple pédagogique, jamais de source d'obligation.

Les plans sectoriels corroborent le mécanisme, sans rendre leurs dispositions
sectorielles applicables à toutes les sociétés. Ces consultations ciblées ne
constituent ni une revue intégrale duCGNC ni une validation réglementaire.

## Aides proposées

| Opération choisie explicitement | Journal suggéré | Débit | Crédit |
|---|---|---|---|
| Versement bancaire d'avance | BQ |3431|5141|
| Versement en espèces d'avance | CA |3431|5161|
| Récupération sur rémunération déjà due | SA |4432|3431|
| Remboursement par banque | BQ |5141|3431|
| Remboursement en espèces | CA |5161|3431|

Les deux lignes portent le même montant saisi. La récupération suppose une
rémunération déjà constatée et une décision justifiée ; le modèle ne vérifie pas
un solde individuel salarié et ne modifie aucun bulletin. Ne pas saisir une
seconde écriture si le module source a déjà enregistré l'opération.

## Installation et conservation

La migration additive 092 est livrée, pas exécutée sur une base utilisateur.
Elle doit suivre 091 sous le rôle propriétaire des tables. Le rôle applicatif
conserve uniquement son accès habituel en lecture au catalogue. Les cinq
nouveaux codes sont insérés s'ils sont absents ; leurs lignes sont créées dans
la même transaction. Tout code préexistant, même personnalisé ou désactivé,
reste strictement inchangé. Le rejeu ne crée aucun doublon.
