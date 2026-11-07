# MODE D’EMPLOI ET RECETTE — FLUX TVA DOCUMENTAIRES

Version 1 du 22 octobre 2026. B14 interne depuis les balances externes.

## Accès et portée

Comptabilité → Liasse fiscale → Préparer depuis des balances externes →
sélectionner une préparation conservée → Documenter les flux TVA B14 depuis
les balances. B14-N est un identifiant interne de préparation, sans assimilation
à une déclaration officielle. Aucun dépôt, liquidation ou paiement n’est créé.

Trois familles :4455 TVA facturée/collectée ;34552 TVA récupérable sur charges ;
34551 TVA récupérable sur immobilisations. Les soldes de la balance sont certains
dans ce périmètre du moteur existant : crédit−débit pour4455 et débit−crédit
pour34551/34552. Les soldes inverses restent signés ; aucun reclassement.

Une balance ne prouve pas les flux de l’année. Le début, les opérations et les
déclarations sont donc saisis explicitement et justifiés. Le solde de fin N-1
reste pour mémoire et ne préremplit jamais le début N. Le journalTV n’est pas
lu et ne vaut pas preuve de dépôt. Une référence saisie ne confirme pas un dépôt.

Fin reconstituée = début déclaré + opérations déclarées − déclarations justifiées.
Écart = fin reconstituée − solde de fin balance N. TVA récupérable totale =
charges + immobilisations ; net documentaire = collectée − récupérable totale.
Ce net ne constitue pas le montant à payer ou le crédit fiscal confirmé.

## Prérequis et jeu chiffré exact

Créer une société fictive isolée en MAD pour2026 avec administrateur, comptable
et lecteur. Vérifier les comptes1111,5141,4455,34552,34551 du plan et ajouter
un logo fictif dans les paramètres. Le lot727 utilise les migrations existantes,
sans nouveau SQL. Redémarrer le backend et reconstruire le frontend.

Importer BALANCE_FICTIVE_TVA727_N.csv et BALANCE_FICTIVE_TVA727_N1.csv fournis
dans docs/recette. N-1 est facultatif et n’intervient jamais comme flux supposé.
Les CSV ne créent aucune écriture dans le Journal.

N :1111 crédit10000 ;5141 débit10300 ;4455 crédit1000 ;34552 débit500 ;
34551 débit200. Débit=crédit=11000MAD ; résultat comptable0. N-1 :1111 crédit10000 ;
5141 débit10150 ;4455 crédit300 ;34552 débit100 ;34551 débit50.
Débit=crédit=10300MAD. Les comptes non mouvementés ont un côté explicitement0.

Choisir B14-N ; déclaration Saisie documentée — à revoir ; justification
Synthèse fictive727, déclarations explicitement justifiées. Ajouter trois lignes :

- Famille4455 : début300 ; opérations2000 ; déclarations1300 ; références des déclarations DECL FICTIVE727 4455 ; référence source NOTE FICTIVE727 4455.
- Famille34552 : début100 ; opérations800 ; déclarations400 ; références des déclarations DECL FICTIVE727 34552 ; référence source NOTE FICTIVE727 34552.
- Famille34551 : début50 ; opérations300 ; déclarations150 ; références des déclarations DECL FICTIVE727 34551 ; référence source NOTE FICTIVE727 34551.

Ces références décrivent un jeu fictif, sans prétendre qu’un dépôt existe.
Oracle indépendant :4455 =300+2000−1300=1000 ;34552 =100+800−400=500 ;
34551 =50+300−150=200. Chaque écart à la balance vaut0. Récupérable totale :
début150, opérations1100, déclarations550, fin700. Net documentaire :début150,
opérations900, déclarations750, fin300. Pour mémoire N-1 :300,100,50,150,150.

## Utilisation pas à pas

1. Importer les deux CSV, contrôler les totaux et conserver une version. Noter l’empreinte source et la version.
2. Ouvrir B14, choisir la déclaration documentée, saisir la justification et les trois lignes ci-dessus. Le quatrième ajout est interdit ; les familles ne peuvent pas être répétées.
3. Cocher la confirmation puis Conserver les tableaux ETIC dans une nouvelle version. La nouvelle version est sélectionnée sans F5. Réouvrir B14.
4. Vérifier les fins1000,500,200,700 et300, les écarts0 et les références conservées. Vérifier les soldes N-1 pour mémoire uniquement.
5. Modifier les opérations4455 de2000 en1999,99 sans conserver : le contrôle figé reste1000. Conserver une nouvelle version : fin999,99, écart−0,01 et alerte visible ; net reconstitué299,99. Le solde de la balance reste1000 et le net source300.
6. Relire l’ancienne version : les fins1000 et300 sont conservées. Aucun ajustement automatique ne réécrit la balance ou les flux.
7. Vider la déclaration4455 puis conserver : fin reconstituée et écart4455 inconnus ; net reconstitué inconnu. Les fins sources restent connues. Une case vide ne vaut pas0.
8. Sans balance N-1, conserver les mêmes flux N explicitement justifiés : N reste calculable, N-1 reste Indisponible. Ne pas inventer une ouverture à partir d’un comparatif absent.
9. Télécharger PDF/Excel/ZIP, contrôler le logo fictif, les sources, références, inconnus et manifeste SHA256. Comparer le Journal : aucune écriture ou déclaration créée.

## Refus, signes et droits

NaN, Infinity, booléen, montant avec plus de deux décimales ou au-delà de
9999999999999,99 en valeur absolue : conservation refusée sans version nouvelle.
Le signe négatif est autorisé pour conserver les soldes/flux inverses justifiés.
Exemple4455 :début−300, opérations2000, déclarations700 →fin1000 ; aucune valeur
absolue ne doit remplacer−300. Justifier cette donnée dans sa source fictive.

Toute ligne exige sa référence de source, même partielle. Toute déclaration
renseignée, y compris0, exige une référence de déclaration ou du néant justifié.
Famille inconnue/doublon, champ supplémentaire, quatrième ligne et omission du
tableau : refus. Une référence commençant par= reste du texte dans Excel.

Lecteur : consultation/exports autorisés, saisie désactivée, conservation
interdite. Autre société : préparation invisible. Empreinte incohérente ou clé
réutilisée pour d’autres flux : conflit. Rejeu identique : même version.
Néant déclaré ne remplit pas les champs vides par0 ; soldes sources non nuls
et note B14 Non applicable contradictoire restent signalés.

## Cahier de recette humain

Les réussites automatisées locales ne remplissent jamais ces statuts humains.
Exécuter dans une société fictive de recette ; conserver captures et exports.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|V727-01|Créer société fictive MAD2026, importer CSV N/N-1, contrôler11000/10300.|Capture de la balance et version source ; soldes4455=1000,34552=500,34551=200.|Non testé|
|V727-02|Saisir trois familles et les flux/références exacts ci-dessus puis conserver.|Capture des fins1000,500,200,700,300 ; écarts0 ; nouvelle version sans F5.|Non testé|
|V727-03|Modifier opérations4455 en1999,99 puis conserver ; vider ensuite sa déclaration.|Brouillon sans effet ; nouvelle fin999,99/écart−0,01 ; après vide, fin/écart et total net inconnus.|Non testé|
|V727-04|Essayer NaN, précision0,001, famille doublon, référence manquante ; tester lecteur et autre société.|Refus sans version créée, brouillon conservé ; droits403 et cloisonnement404.|Non testé|
|V727-05|Télécharger PDF/Excel/ZIP avec logo et référence =SOURCE_FICTIVE727.|Logo visible, sources et inconnus identiques, référence Excel texte, manifeste vérifié.|Non testé|
|V727-06|Relire versions anciennes, tester N-1 absent et signe négatif ; comparer Journal et module TVA.|Historique stable, N-1 inconnu,−300 préservé, aucune écriture/liquidation/déclaration réelle modifiée.|Non testé|

## Limites et suite

Les flux sont déclarés, pas prouvés automatiquement. Le net documentaire ne
valide ni exigibilité, ni déductibilité, ni TVA due, ni dépôt. La préparation
B14 n’est pas un formulaire officiel ni un dossier prêt à déposer. Les sources
extra-comptables C3 et la fiscalité externe complète restent à poursuivre,
ainsi que les justificatifs humains. XML/EDI exige un schéma officiel.
RH/paie, recette utilisateur, installation cible et production restent différés.
