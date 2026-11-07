# B13 indépendant — sources consultées et portée du lot721

Consultations effectives du21octobre2026 :

- [Catalogue MEF des normes CNC](https://www.finances.gov.ma/fr/Nos-metiers/Pages/cnc-normes.aspx) : le moteur de recherche retourne la référence CGNC tomesI/II ; ouverture directe en timeout.
- [CGNC hébergé par l’OEC Casablanca](https://oec-casablanca.ma/app/webroot/img/uploads/Code_general_de_la_normalisation_comptable.pdf) et variante sans app/webroot : ouvertures502, pas de document intégral téléchargé ni d’empreinte binaire.
- [Plan comptable sectoriel immobilier du MEF](https://www.finances.gov.ma/Publication/depp/2022/Plan%20comptable%20du%20secteur%20Immobilier.pdf) : extrait B13 indexé distinguant résultat comptable courant, retraitements courants et impôt théorique ; ouverture intégrale en timeout. Ce texte sectoriel n’est pas transposé comme norme générale.

Cette consultation ne permet pas de revendiquer une revue normative intégrale
du CGNC ou du millésime fiscal applicable. Aucun nouveau taux, avantage,
obligation fiscale ou modèle DGI/EDI n’est codé dans721.

Le périmètre comptable71/73 moins61/63 reprend exclusivement
`etic_service._automatiques` déjà présent. Le détail exact et la garde du CPC
indisponible réutilisent `balance_cpc_detail_service.calculer`. La garde119
explicite reprend celle de `balance_import_service.normaliser_balance` pour
les anciens snapshots dont le CPC n’a pas encore son drapeau d’indisponibilité.
Les écarts avec le CPC VII figé restent visibles ; aucun moteur existant ni
ancien snapshot n’est corrigé pour obtenir un rapprochement nul.

Les nouveaux formulaires sont **documentaires internes**, sans nouvelle règle
de liquidation. Le total67 comptabilisé est affiché pour mémoire. Il n’est pas
assimilé à un impôt théorique sur le courant, et ne préremplit aucune case.
L’utilisateur fournit lui-même les réintégrations, déductions, l’impôt théorique
et la référence de sa synthèse. Aucun taux ni régime n’est calculé. Une seule
synthèse par période évite une addition de synthèses qui se recouvriraient.

Deux équations arithmétiques documentaires, sans bornage fiscal ou liquidation :
base = courant + réintégrations déclarées − déductions déclarées ;
courant après impôt déclaré = courant − impôt théorique déclaré.
La seconde part bien du résultat comptable courant, pas de la base retraitée.
Les résultats signés sont conservés ; aucune perte n’est transformée en zéro.
Un montant manquant laisse indisponible tout résultat qui en dépend.
Une déclaration néant n’invente pas de zéros fiscaux.

Les données de recette sont fictives et arithmétiques. Les montants déclarés
ne prouvent aucun calcul fiscal réglementaire. B12, la liquidation IS, les
avantages applicables et les sources officielles complètes restent distincts.
