# RAS TVA — raccordement déclaratif571

La simulation559 peut désormais être rapprochée d'un règlement immédiat déjà
comptabilisé. Le serveur refait le calcul avant de préparer la capture083 et
son OD, avec un dossier immuable de qualification déclarée. Aucun compte n'est
choisi automatiquement, aucune attestation ni qualification fiscale certifiée.

## Périmètre

- Article117-V-b/listeB du CGI2026 seulement, simulation positive complète.
- Paiement par virement ou espèces, facture définitive comptabilisée et tiers
  réel ; date de simulation égale à la date du paiement.
- Net calculé égal au montant réel du règlement. Les quotes-parts TTC/TVA
  cumulées ne dépassent pas les montants de la facture. La ventilation de TVA
  reste explicitement justifiée, sans allocation automatique entre taux.
- Les autres règlements actifs doivent déjà posséder leur dossier RAS TVA.
  Avoirs/acomptes affectés, autre paiement non qualifié, RAS HT ou historique
  sont refusés dans ce premier périmètre ; ils ne sont pas reclassés.
- Référence de ventilation, faits, source, calcul et empreinte sont conservés.
  L'aperçu est relu sous verrous au POST. Une demande identique est idempotente.
- L'OD reste à contrôler et valider dans le Journal. Une annulation conserve
  le dossier et utilise la contrepassation existante du règlement.

**Limite déclarative explicite :** le moteur TVA courant utilise les seuls
flux de trésorerie et ne traite pas encore l'imputation/reversement des nouvelles
retenues TVA. Il refuse donc de produire un solde automatique pour une période
ou son report concerné par ces captures. Les autres sociétés et les périodes
antérieures continuent à fonctionner. Aucun crédit ou reversement présumé.
Ce lot ne constitue pas une déclaration fiscale complète.

## Installation et API

Migration additive `099_ras_tva_details.sql`, après la chaîne existante jusqu'à098
et notamment083. Application manuelle par l'administrateur, après sauvegarde
et contrôle de l'installation cible ; aucune migration au démarrage. Ni
`models.py` ni `main.py` modifiés. L'absence de099 est signalée sans DDL implicite.

- `GET /api/reglements/{rid}/ras-tva` : disponibilité et dossier conservé.
- `POST /api/reglements/{rid}/ras-tva/apercu` : objet `simulation`559 et
  `justification_quote_part` ; lecture seule, renvoie une empreinte.
- `POST /api/reglements/{rid}/ras-tva` : mêmes données, empreinte de l'aperçu,
  référenceRAS, compte destination explicitement choisi, `pieces_verifiees:true`.

La route générique `/ras` reste disponible. Une ancienne capture libre ne reçoit
pas rétroactivement une qualification TVA.099 ajoute uniquement une table de
détails liée à083, des contrôles de liens, des droitsSELECT/INSERT au LOGIN et
des protections contre UPDATE/DELETE/TRUNCATE, y compris pour le propriétaire.

## Tests exécutés

Exclusivement données fictives sur clusters PostgreSQL nonce, API réelles sous
LOGIN limité, sans mock de calcul ou de réponse et sans PostgreSQL utilisateur.

- Avant modification :58 réussis,26 avertissements,31,25s.
- Ciblage final avant garde déclarative :26 réussis,29 avertissements,67,49s.
- Compatibilité simulation/capture083 et absence099 :59 réussis,29 avertissements,
  49,57s. Aucune migration implicite sur le banc ancien.
- Livraison finale avec garde TVA et tests du moteur :**76 réussis,
  29 avertissements,72,74s**, code0 ;27 cas natifs571,44 simulations et5 calculsTVA.

Les cas natifs couvrent75/100%, achat/vente, deux paiements partiels jusqu'au
solde, validation des OD et auxiliaires, idempotence/concurrence, droits et
multi-société, aperçu périmé, période fermée via API, annulation et conservation,
ACL et JSON incohérent. Une faute SQL réelle après création de l'OD vérifie le
rollback de l'OD, de la capture et du dossier, puis la réussite du même rejeu.
La migration est rejouée sans changer les données des tables antérieures.

Échecs intermédiaires consignés dans CODEX_PROGRESS : références fournisseurs
manquantes et normalisation Pydantic dans le jeu de test ; mauvais libellé de
statut de période remplacé par la vraie API. Une commande utilisait un nom de
fichierTVA inexistant : code4, aucun test exécuté ; chemin corrigé. Les chiffres
ci-dessus se recouvrent et ne s'additionnent pas comme des tests uniques.

## Sources et suite

CGI2026 TGR, article117 pagesPDF202–203, consulté de nouveau le18octobre2026.
[Note des sources](../docs/audit/SOURCES_RAS_TVA_20261018.md). Les tentatives de
lecture de la NC735 sur MEF ont expiré et sa copieAMDIE a répondu403 ; aucune
règle déclarative n'est inventée sur cette base.

Suite : interface guidée573 puis qualification de la chaîne099/restauration.
Le reversement, l'imputation et les modèles déclaratifs restent à développer
sur sources officielles applicables. RH/paie et recette humaine différées.
