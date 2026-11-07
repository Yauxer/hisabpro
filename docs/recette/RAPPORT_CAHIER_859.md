# HisabPro — erreur réseau et rafraîchissement des règlements

Les fiches SEC009 et SEC005 sont exécutées dans Edge aux largeurs1440/390 avec API réelle et PostgreSQL natif éphémère. Le transport GET de la liste du Journal est interrompu depuis le navigateur :aucune réponse métier n'est remplacée par des données fabriquées et les autres API restent réellement connectées.

Un défaut UX est reproduit :le Journal affiche Failed to fetch. Les données sont protégées et le bouton Réessayer existe,mais le message reste technique et en anglais. Le client partagé JSON/téléchargement utilise maintenant une seule fonction qui traduit les TypeError de fetch en Connexion au serveur indisponible. Vérifiez votre connexion puis réessayez. La cause technique reste attachée à l'erreur. Les refus HTTP du serveur et les annulations ne sont pas convertis en pannes réseau ;aucun droit ni calcul comptable n'est changé.

SEC009 :pendant la coupure,le message français est visible,aucune commande de création d'écriture n'est proposée et aucun enregistrement financier n'est envoyé. Le témoin comptable reste identique. Après rétablissement,le bouton Réessayer provoque une vraie réponse200 et affiche le témoin initial sans mutation.

SEC005 :un règlement partiel120MAD est enregistré sur la facture fournisseur240MAD de la copie. La liste affiche Part. payée et le solde serveur est120MAD. La navigation interne vers le Journal affiche PAY-859 et une seule nouvelle pièce,débit4411/crédit5141 pour120MAD. L'origine temporelle du document est inchangée :aucuneF5 ou navigation complète n'a été utilisée. Un seul POST de règlement a été émis et les écritures initiales restent conservées.

La première passe après correction a validé la reprise et le paiement mais le test cherchait un attribut data-label absent du tableau. Le sélecteur a été corrigé vers le texte réellement affiché,Part. payée. Les échecs initiaux et leurs traces sont conservés ;ce problème de sélecteur ne justifie aucun autre correctif produit.

Validation finale :deux parcours connectés,12tests de transport sous Node et5connexes du cache/droits réussis. Les testsNode exécutent le vrai clientJavaScript avec transport synthétique pour les deux voies JSON/PDF :succès,panne,annulation et statuts401/403/422. Le401 conserve l'effacement de session et sa reconnexion ;403/422gardent leurs messages métier et l'annulation conserve AbortError. Ces12tests ne sont pas présentés comme des appels réels PostgreSQL. BuildVite réussi en6,34s,avec les avertissements existants concernant le bundle et xlsx.

Une seule source du produit est modifiée,src/services/api.js. Les462empreintes sont mises à jour dans CANDIDAT_FACTURATION_COMPTABILITE_859.json ;backend et migrations restent identiques. Le contrôle concerne l'échec de fetch avant réponse HTTP,pas toutes les ruptures possibles pendant la lecture d'un corps ou tous les fetch directs de l'application.

Le suivi atteint177fiches automatiquement réussies,5partielles,80nonqualifiées individuellement et10bloquées à la source. Les70statuts globaux restent inchangés. Prochaine étape :changement de société avec formulaire non enregistré et vérification des droits/contextes rechargés. Aucune donnée réelle ni PostgreSQL utilisateur touché ;réserves841,recettehumaine et production restent à traiter,RH/paie/EDI différés.
