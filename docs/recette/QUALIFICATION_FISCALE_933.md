# Tester la préparation fiscale depuis des balances externes

Le cahier existe déjà et contient les données champ par champ et les quatorze cas :[Word](CAHIER_RECETTE_FISCALE_755.docx),[PDF](CAHIER_RECETTE_FISCALE_755.pdf) et [Excel humain à remplir](CAHIER_RECETTE_FISCALE_755.xlsx). Ils sont conservés ;aucun résultat humain n’a été prévalidé ou remplacé.

Pour ce scénario uniquement,utiliser [la balance N](BALANCE_FICTIVE_FISCALE755_N.csv),[N-1](BALANCE_FICTIVE_FISCALE755_N1.csv),[le logo fictif](LOGO_FICTIF755.png),[les justificatifs fictifs](JUSTIFICATIFS_FICTIFS755.pdf) et [les données et calculs](DONNEES_FISCALES755.json). Travailler sur une copie isolée. Ne pas mélanger les chiffres de ce jeu avec les jeux des composants749–753 ou avec le Journal de votre société habituelle.

Dans **Liasse fiscale → Préparer depuis des balances externes**,importer les deux fichiers,contrôler puis conserver. Suivre les six étapes du cahier :B12,CM,CSS,crédits,acomptes,revue annuelle. Les versions successives restent conservées. Les exports ZIP,PDF et Excel portent les données de la version sélectionnée et le logo de la société du laboratoire.

Le résultat de recette de ce jeu est un **solde proposé de3 650MAD**,selon ses hypothèses :IS théorique24 000,crédits disponibles350,acomptes justifiés20 000,CSS0 séparée. La date de contrôle15/03/2027 est une donnée fictive à saisir ;ne pas changer l’horloge du poste. Ce parcours ne crée pas les écritures des CSV dans le Journal et ne confirme ni liquidation,paiement,dépôt EDI ou archive fiscale définitive.

Le [suivi automatique933](SUIVI_AUTOMATISATION_CAHIER_933.xlsx) rattache maintenant chaque ficheF755 à ses tests. La colonne de méthode distingue les parcours navigateur des contrôles API. Les variantes négatives des fiches11–13 sont contrôlées par API sur ce même jeu ;leurs gestes de formulaire restent à effectuer dans la recette humaine. Les vrais fichiers CSV erronés et la consultation seule sont aussi vérifiés dans Edge. Le sélecteur de tableau reste utilisable pour consulter,alors que les champs métier du lecteur sont désactivés.

Pour le partenaire,commencer par le cahier Word/PDF et renseigner le classeur humain755. Le suivi automatique apporte les preuves techniques ;il ne remplit pas la colonne Résultat réel ou les captures humaines à votre place. Les réserves de cession,justificatifs historiques et configuration de la cible restent ouvertes.

[Résultats exécutés](RESULTATS_MVP_933.md) · [Correspondance des quatorze fiches](../../Test/QUALIFICATION_FICHES_933.json) · [Décision actuelle](DECISION_FACTURATION_COMPTABILITE_933.md).
