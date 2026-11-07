# Financement indépendant — sources et limites du lot695

Consultation effective le21octobre2026 :

- [Catalogue des normes du ministère](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx)
  ouvert : le lien CGNC tomesI/II est présent. Son
  [PDF lié](https://www.finances.gov.ma/Publication/depp/2010/7004_recettes_priv_annee25_11_210.pdf)
  a expiré lors de la consultation.
- [CGNC hébergé par l’OEC Casablanca](https://oec-casablanca.ma/img/uploads/Code_general_de_la_normalisation_comptable.pdf) :
  passages indexés effectivement obtenus sur le tableau de financement.
  Ils distinguent les flux bruts des emplois/ressources stables et les variations
  nettes des autres masses ; l’autofinancement utilise la CAF et les distributions.
  Ouverture directe502 : pas de PDF intégral téléchargé ni d’empreinte binaire.

Le lot réutilise `calculer_tableau_financement` de `liasse_service.py`, déjà
présent et testé, sans modifier ses règles de classement ou calcul. Il ajoute
la saisie documentaire des flux à partir de sources explicitement déclarées.
Il ne déduit pas des acquisitions, cessions ou remboursements depuis une simple
variation de soldes. Une cellule vide reste inconnue, un zéro est une déclaration
explicite. Les flux N-1 ne sont pas déduits de la balance N-1.

La CAF utilisée doit recouper l’ESG figé de la préparation. Si les classes6/7
ont été soldées et que l’ESG est indisponible, l’autofinancement et les totaux
qui en dépendent restent indisponibles. Un contrôle chiffré ne constitue pas
une validation fiscale ni un dossier prêt à déposer.

La consultation partielle n’est ni une revue normative intégrale, ni une preuve
de conformité officielle. Les documents sectoriels et copies de cabinets trouvés
par le moteur de recherche ne servent pas à introduire une nouvelle règle.
RAS/EDI restent soumis à leurs modèles applicables, indépendamment de ce lot.
