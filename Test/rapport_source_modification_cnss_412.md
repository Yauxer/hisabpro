# Recherche ciblée de la modification CNSS — lot 412

Consultation du 11 octobre 2026, lecture seule. Ce complément porte uniquement sur le texte de modification 2-14-14 non obtenu au [lot 384](rapport_sources_paie_edi_384.md). Les preuves antérieures et leurs limites restent conservées ; aucun calcul, taux, migration ou paramètre de paie n'a été modifié.

## Résultats réellement observés

- Les requêtes ciblées CNSS/SGG/ACAPS n'ont pas fourni le texte promulgué recherché. Les indications privées de numéro et de date de Bulletin officiel ont seulement orienté des tentatives d'ouverture ; elles ne constituent pas une preuve normative retenue.
- Les chemins exploratoires [SGG arabe 6317](https://www.sgg.gov.ma/BO/AR/2014/BO_6317_Ar.pdf) et [SGG français 6318](https://www.sgg.gov.ma/BO/FR/2014/BO_6318_Fr.pdf), ainsi que leurs variantes de chemin, n'ont pas été accessibles par l'outil. Cela ne démontre ni l'absence des textes ni la validité de ces URL supposées. Aucune page de ces bulletins n'a été lue ou qualifiée.
- L'ouverture de la [page de consultation des Bulletins officiels SGG](https://www.sgg.gov.ma/BulletinOfficiel.aspx) a retourné HTTP 503. Il s'agit du résultat de cette consultation, pas d'un constat de panne générale.
- La [fiche CNSS publiée par ACAPS](https://www.acaps.ma/fr/files/fichesynthetiquecnsspdf) a été ouverte à nouveau, trois pages. Son tableau synthétique ne remplace pas le texte de modification ni la qualification des dates d'effet et des parts exactes. Aucune nouvelle preuve réglementaire suffisante obtenue par rapport au lot 384.

## Limite et prochaine action

La qualification de la paie définitive reste bloquée sur le référentiel applicable complet : retrouver le texte officiel de modification, établir ses dates d'effet et sa consolidation, puis qualifier assiettes, parts exactes, plafonds, exceptions et arrondis avant de modifier les calculs. Aucun partage exact n'a été déduit arbitrairement d'un ratio. Ne pas exécuter le script historique donnees_fiscales.sql sur la base réelle.

Le schéma officiel XML/EDI SIMPL-IS reste une dépendance distincte déjà documentée, sans nouvel export de substitution. Les développements indépendants de cette preuve sont livrés dans les lots 404 à 410 ; le point 6 reste en attente de l'utilisateur.

## Contrôle local

UTF-8 strict, références locales et domaines primaires des quatre liens HTTP contrôlés localement. Ce contrôle documentaire ne valide pas les URL distantes non accessibles ni le contenu des textes non obtenus. Aucun PostgreSQL réel, aucune donnée comptable réelle et aucun fichier de configuration sensible consultés.
