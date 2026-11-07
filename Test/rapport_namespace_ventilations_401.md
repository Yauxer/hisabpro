# Numéro technique des ventilations —401

Cause : le POST public d'un règlement isolé acceptait un numéro VT suivi du UUIDhex32 et de l'indice01. Ce même espace de numéros est utilisé pour reconnaître les lots natifs; une saisie manuelle pouvait donc imiter ou polluer ce lien technique. Reproduit sur vente et achat :réponse201 avant correction,contre422 attendu.

Correction minimale : garde du seul point d'entrée POST public, avant toute écriture ou verrou de facture. Le format technique exact est réservé au flux par-tiers; numéro commercialVT-2026-RECETTE-001 accepté. Helper interne et génération atomique native inchangés. Le PATCH ne permet déjà pas de modifier le numéro. Aucune migration,aucune réécriture d'historiques ou réparation arbitraire.

89tests racine réussis,202.546s,zéroéchec/erreur/ignoré;compilation0. Avant correction:2échecs et1réussite,créations201du format technique reproduites.

Suite :nouvelle garde,création native par-tiers,annulation collective,pointageAPI/SQL/Edge,annulation après pointage etRAS. Tous exécutés réellement sur PostgreSQLnonce/Edge. Les autres709empreintes de397 restent identiques;nouveaux tests399/400/401 ajoutés. La connexe397 précède cette garde; la preuve401 couvre son périmètre, pas une nouvelle globale de tous modules. Globale391 en échec conservée.

Limite :les anciennes références historiques ne sont pas automatiquement requalifiées;un numéro technique ne prouve pas la réalité d'un virement. Recette humaine à effectuer,aucune base réelle,point6 en attente.
