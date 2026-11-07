# Préparation ventes — exports internes Excel/PDF423

Deux exports serveur etboutons dans la préparation418. Les sources sont relues dans la société etles bornes réelles de l'exercice ;l'empreinte de l'aperçu est obligatoire. Sources modifiées :409,invitation à actualiser,aucun export silencieusement différent. L'identité de la société est incluse dans la préparation etsonCSV. Les archives etanciens formats de liasse restent inchangés.

XLSX Synthèse/Sources :identités ettextes littéraux,aucune formule introduite,montants inconnus À vérifier,totaux connus séparés. Centimes exacts :si quinze chiffres significatifs ou une conversion flottante ne suffisent pas,le montant reste un texte exact. PDF interne paysage avec tableaux répétés,sources etempreinte. Aucun modèle DGI ni XML fabriqué,aucune nouvelle règle fiscale.

La réponse d'export tardive est ignorée après changement d'exercice/société/token ou démontage. L'actualisation est désactivée pendant un téléchargement. Les téléchargements utilisent Content-Disposition exposé explicitement au CORS sur cette seule nouvelle route.

## Tests réellement exécutés

exports423_racine:27réussis,169.602s ;exports423_connexes_final:19réussis,114.187s ;suites recouvrantes non additionnées ;compilation0/build141modules11.05s.

Copie de travail :20API/rendus réussis88.70s ;premierEdge2échecs4réussites81.71s,nom export.bin malgré corps valide. Cause :Content-Disposition inaccessible au JavaScript cross-origin. Après correction :6Edge réussis79.002s. PDF multipages :1réussite2.364s avec120sources uniques,totaux exacts ettexte entièrement dans les pages.

Racine :27API/rendus/Edge puis19connexes,avec deux exports Lecture explicitement testés. Authentification absente,empreinte étrangère,formatXML etempreinte malformée refusés ;sources inchangées. NaN historique reste inconnu. Les exports existants,bilan détaillé,numérotation interne,archive finalisée/navigation liasse restent vérifiés. Les assertions monétaires ne sont pas assouplies.

Une première commande connexe a utilisé deux noms de fichier inexistants :aucun cas exécuté,runner code1,erreur d'invocation conservée. Relance avec noms vérifiés etnouvelXML réussie. Les suites recouvrantes ne sont pas additionnées.

## Limites etsuite

09Ereste partiel :préparation interne disponible,format fiscal officiel etrapprochement au CAcomptable non qualifiés. Aucun PostgreSQL réel,modèle,main,migration ou données réelles modifiés. Recette humaine à effectuer,point6 en attente. Globale419interrompue et411échouée conservées ;nouvelle preuve426sur sources finales à exécuter.726sources anciennes contrôlées avant intégration ;seuls7fichiers source de ce lot changés/ajoutés.
