# Lot551 — derniers contrôles du rendu PDF GRH

**2 tests de rendu pur réussis,1avertissement,0.68s**,code0 :
`Test/run_unit_tests.py Test/test_grh_registre_pdf_limites.py -ra`.

Les motifs restent sous la limite existante de1000caractères :970sauts de
ligne suivis d'un marqueur final, ou50répétitions d'un texte contenant `<`, `>`
et `&`. Le motif est aussi présent dans son événement historique.

Le PDF est généré sans logo, accepte le passage sur plusieurs pages et conserve
les deux marqueurs finaux ainsi que les100occurrences du texte échappé.
Un contrôle exploratoire préalable a produit28pages avec les marqueurs intacts.
Ces tests sont distincts des validations PostgreSQL et Edge547/549.

Aucun fichier produit, règle métier, donnée réelle ou migration modifié.
Les suites déjà qualifiées ne sont pas déclarées relancées. Les sources du
registre et la preuve de restauration restent inchangées.
