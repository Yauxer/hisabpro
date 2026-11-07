# MODE D’EMPLOI ET RECETTE — COTISATION MINIMALE SUR BALANCE EXTERNE

Version 1 du 22 octobre 2026. Complément 741 du mode Liasse seule.

## Fonctionnement

Dans Comptabilité → Liasse fiscale → Import Balance / Liasse seule, ouvrir une
préparation conservée puis Calculer la cotisation minimale — 2026. La base
comptable provient exclusivement de la balance N importée. Les comptes de
produits retenus ou hors base apparaissent dans le contrôle  ; aucun compte du
Journal actif n’est repris. Ce formulaire est distinct du contexte fiscal
CM/CSS/crédits/acomptes déjà disponible.

Ajouter une ligne, choisir Saisie documentée — à revoir et justifier les
paramètres. Choisir explicitement IS hors forfait non-résident, puis saisir
la base exclue et la base éligible au taux réduit. Choisir oui ou non pour
l’exonération totale et l’exonération du minimum. Le responsable doit vérifier
les conditions et justificatifs  ; le logiciel ne déduit aucune exonération
ou vente éligible du secteur, de la date de création ou du nom d’un compte.

Une sélection vide reste À qualifier. Un montant vide reste inconnu. Même
une déclaration Néant ne signifie ni zéro ni exonération. Les contrôles du
brouillon ne remplacent pas les valeurs conservées avant une nouvelle
conservation. Cocher la confirmation puis Conserver le calcul CM dans une
nouvelle version. La liste et le résultat se mettent à jour sans F5.

Le calcul partage le moteur CM déjà utilisé dans le module fiscal. Les bases
standard/réduite, les parts proportionnelles, le minimum et la CM proposée sont
distincts. Le maximum avec l’IS théorique B12 est proposé seulement si cet IS
est connu. Si B12 change, une alerte conserve l’ancien contrôle pour mémoire ;
relire les pièces et conserver explicitement une nouvelle qualification CM.

Le calcul est couvert pour 2026 uniquement, en MAD, avant clôture technique.
CSS, crédits, acomptes et solde final restent à traiter séparément. Aucun paiement,
écriture ou liquidation n’est confirmé. Le dossier n’est pas déclaré prêt à
déposer. Voir les sources vérifiées dans SOURCES_CM_20261022_741.md.

## Jeu de données exact et résultats indépendants

Utiliser une société fictive CM recette 741, MAD, exercice 2026. Dans un dossier
isolé, importer BALANCE_FICTIVE_CM741_N.csv sans N-1. Il contient :1111 crédit 10000,
5141 débit 16400,7111 crédit 10000,6132 débit 3000,7581 crédit 1000,6701 débit 1600.
Débit=crédit=21000 MAD. Résultat net 6400  ; avant impôts 8000.

Pour B12 :autres réintégrations 500, déductions 200, déficit déclaré 1000, taux
explicitement déclaré 20%. Justifier chaque hypothèse avec la note fictive
NOTE-B12-741. Bénéfice proposé=8000+500−200−1000=7300  ; IS théorique 1460.
Ces données et ce taux sont fictifs, sans qualification d’une société réelle.

Pour CM :Désignation CM fictive 2026  ; Périmètre IS hors forfait non-résident ;
base exclue 0, base réduite 0, exonération totale non, exonération du minimum non.
Référence NOTE-CM741  ; justification Qualifications fictives vérifiées pour
la recette, aucune exonération déclarée. La base du moteur vaut 10000  ; 7581 est
hors de ses familles CM. Part proportionnelle=10000 ×0,25%=25  ; minimum 3000 ;
CM proposée 3000  ; maximum IS/CM3000. Aucun solde final calculé.

Sur une nouvelle version, exonération totale oui, sourcée par NOTE-EXO741 :
CM proposée 0, maximum IS/CM1460. Cette variante teste la saisie explicite  ; elle
ne prouve pas qu’une société réelle bénéficie d’une exonération. Remettre non
et choisir exonération du minimum oui, sourcée par NOTE-MIN741 :CM25, maximum
IS/CM1460. Aucune condition d’exonération n’est inventée par le test.

Pour le calcul à deux taux, importer BALANCE_FICTIVE_CM741_GRANDE_N.csv dans
une préparation distincte, sans B12. Même jeu sauf 7111 crédit 2000000 et 5141 débit
2006400  ; débit=crédit=2011000. BaseCM2000000  ; base exclue 200000  ; base réduite
500000  ; deux exonérations non. Base standard 1300000  ; part standard 3250,
part réduite 750, CM4000. IS/maximum indisponibles puisqueB12 absent.

## Recette humaine à effectuer

Les résultats des tests automatisés ne remplissent pas les statuts ci-dessous.
Prérequis :bac isolé, société et fichiers fictifs décrits ci-dessus, administrateur
ou comptable  ; profil Lecture pour le refus de mutation. Aucun impact fiscal
réel ni écriture attendue. Conserver les captures, versions et exports obtenus.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|CM741-01|Importer le petit CSV dans CM recette 741  ; conserver  ; compléter B12 avec 500/200/1000/20 et NOTE-B12-741.|Balance 21000/21000, net 6400, avant impôts 8000, B12 bénéfice 7300/IS1460  ; captures et version.|Non testé|
|CM741-02|Ajouter la qualification CM normale décrite ci-dessus  ; régime explicite,0/0, non/non, NOTE-CM741  ; conserver.|Base 10000, part 25, minimum 3000, CM3000, maximum 3000  ; 7581 hors base  ; aucun solde final  ; capture.|Non testé|
|CM741-03|Dans une nouvelle conservation, vider la base réduite ou laisser une exonération À qualifier  ; puis essayer Néant justifié sans ligne.|CM et maximum indisponibles, aucun zéro/non fabriqué  ; anciennes versions inchangées  ; captures.|Non testé|
|CM741-04|Reprendre les paramètres complets 0/0, choisir exonération totale oui et minimum non  ; NOTE-EXO741  ; conserver.|CM0, IS théorique 1460, maximum 1460  ; aucun paiement ou liquidation  ; capture.|Non testé|
|CM741-05|Exonération totale non, minimum oui  ; 0/0, NOTE-MIN741  ; conserver.|CM25, maximum 1460  ; qualification exclusivement fictive  ; capture.|Non testé|
|CM741-06|Importer le grand CSV distinct sans B12  ; base exclue 200000, réduite 500000, non/non  ; NOTE-GRAND741  ; conserver.|Base 2000000, standard 1300000, parts 3250+750, CM4000  ; IS/maximum indisponibles  ; captures et exports.|Non testé|
|CM741-07|Essayer NaN,−1,0.001 puis une base réduite supérieure au disponible  ; ouvrir ensuite le dossier en Lecture.|Refus 422 sans nouvelle version ni modification des pièces  ; brouillon corrigeable  ; Lecture sans bouton de conservation, POST403 côté serveur  ; traces/captures.|Non testé|
|CM741-08|Dans le petit dossier exonéré totalement, changer le taux déclaré B12 de 20 à 10  ; ouvrir CM, puis conserver explicitement  ; exporterZIP/PDF/Excel et relire ancienne version.|Alerte B12, puisIS/max 730 après conservation  ; ancien 1460 préservé  ; export de la version conservée avec logo, source juridique et manifeste  ; aucune valeur du brouillon exportée.|Non testé|

## Utilisation des exports et limites

Télécharger PDF, Excel ou le dossier ZIP de la version conservée. Excel comporte
Origine CM, Calcul CM, Sources CM, Qualification CM et Alertes CM. Le ZIP inclut
cotisation_minimale_documentaire.json etson manifesteSHA256. Les paramètres,
sources, taux du moteur et résultats conservés doivent se recouper. Une référence
commençant par = reste du texte dans Excel, aucune formule injectée. Le logo de
la société utilise le mécanisme existant des exports.

Ces tests ne valident ni l’éligibilité fiscale d’un dossier réel, ni la recette
utilisateur, Office, l’installation cible ou la production. Aucun PostgreSQL réel
utilisé. RH/paie etpoint 6 restent différés. Le schéma EDI officiel reste requis.
