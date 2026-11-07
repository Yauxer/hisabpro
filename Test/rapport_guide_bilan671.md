# Guide courant et bilan de session — lot671

Le mode d’emploi est actualisé en version15 du19octobre2026, en Markdown,
Word et PDF de35pages. Les annulations décrivent le formulaire date/motif,
individuel ou collectif. Le parcours des réceptions utilise Préparer depuis
une commande. La lecture/reprise, les documents RAS, les sociétés liées,
les achats correspondants et les reprises de provisions ont leurs compléments
et liens vers les données chiffrées.

Les17résultats humains du guide restent Non testé et À renseigner.
Les12cas de l’annexe RAS conservent leurs résultats vierges.
La checklist conserve73demandes :40terminées,31partielles,1absente,1bloquée.
SEP20-01 est corrigé de absent à partiel sur les preuves633/635/661 ; les
validations des deux pièces restent séparées et la réplication générale
des paiements/avoirs/livraisons n’est pas développée. La matrice de70fonctions
reste distincte :16terminées,47partielles,3absentes,4bloquées.

## Vérifications exécutées

- Génération Word/PDF : code0 ; 35pages, 505blocs documentaires.
- Guide courant et annexe RAS :9tests réussis en1,53s, zéro échec/erreur/ignoré.
- Oracle et parcours annuel connecté :2tests réussis en45,58s ;15cas volontairement non sélectionnés,30avertissements. Zéro échec/erreur/ignoré.
- Intégrité :106fichiers protégés inchangés ;59archives antérieures vérifiées par empreinte, CRC et manifeste. Le différentiel cumulatif comprend70fichiers.

Les contrôles documentaires ouvrent réellement les ZIPs OOXML et XML, extraient
le PDF, contrôlent le suivi humain vierge, les liens des jeux et les comptages.
Les cumuls600/840 du petit parcours de vente sont calculés indépendamment.
Les six contrôles de l’annexe RAS sont rejoués avec les trois nouveaux contrôles
du guide. Ils ne simulent aucune recette utilisateur.

Le scénario annuel est exécuté dans `test_e2e_runtime_session_isole`, sous
LOGIN applicatif non propriétaire sur PostgreSQL091 nonce : oracle indépendant,
facturation, paiements/lettrage, TVA, immobilisation, clôture et à-nouveaux.
Il qualifie ce parcours sur le code courant ; les nouvelles fonctions099–102
restent couvertes par leurs bancs distincts, notamment647/651/661.

Les pages finales34/35 sont rendues et inspectées. L’application Word et le
recalcul interactif Excel n’ont pas été ouverts ici. Les outils ne touchent
aucun PostgreSQL réel. Les anciens ZIPs sont préservés, le cumul ne contient
que les fichiers ajoutés/modifiés depuis645. Les résultats des campagnes
antérieures se recouvrent et ne sont pas additionnés.

Développement global partiel, recette utilisateur à effectuer, production non
validée. RH/paie et point6 humain différés ; modèles fiscaux officiels et
justificatifs historiques encore nécessaires selon le registre.
