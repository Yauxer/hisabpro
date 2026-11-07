# MODE D’EMPLOI ET RECETTE — CSS SUR RÉFÉRENCE FISCALE SOURCÉE

Version 1 du 22 octobre 2026. Complément 743 du mode Liasse seule.

## Utilisation

Dans Comptabilité → Liasse fiscale → Import Balance / Liasse seule, ouvrir une
préparation fictive 2026 conservée. Le guide CM741 et son petit CSV fournissent
un dossier de départ ; le résultat comptable de ce dossier n’est pas la base
CSS reprise automatiquement. Ouvrir Calculer la CSS — 2026.

Ajouter une ligne et choisir Saisie documentée — à revoir. Renseigner une
désignation, le périmètre Société relevant de l’IS, l’exercice fiscal de
référence, le bénéfice net fiscal servant à l’IS du dernier exercice clos.
Confirmer oui seulement si la source correspond effectivement à ce dernier
exercice clos. Choisir explicitement oui ou non pour l’exonération permanente
d’IS, avec justification et référence de pièces. Une exonération temporaire
ne suffit pas à choisir oui. Le responsable doit vérifier les conditions.

Une sélection ou un montant vide reste inconnu. Néant n’est pas un bénéfice
égal à zéro et ne permet pas de fabriquer une CSS nulle. Cocher la confirmation
puis Conserver le calcul CSS dans une nouvelle version. La version et le
contrôle se rafraîchissent sans F5. Modifier un brouillon n’altère pas les
chiffres conservés ou exportés avant une nouvelle conservation explicite.

Le taux proportionnel s’applique au bénéfice entier. Le calcul partage le
moteur CSS existant et conserve sa source juridique. La CSS reste distincte
de l’IS/CM, des retenues, crédits et acomptes. Aucun paiement ou liquidation
n’est confirmé. La date de clôture source n’étant pas qualifiée dans ce
formulaire, l’échéance reste à déterminer séparément ; aucun 31 mars automatique.

## Données fictives exactes

Utiliser uniquement une société fictive CM recette 741, MAD, exercice 2026, et
la préparation du petit CSV du guide 741. Le contexte fiscal 735 peut conserver
une CSS explicitement déclarée 0 pour tester le diagnostic ; ne jamais modifier
une déclaration réelle pour ce scénario.

Le fichier NOTE_FICTIVE_CSS743_2025.md fournit une source de recette interne,
explicitement fictive : résultat comptable avant IS2025=2000000, réintégrations 0,
déductions 0, déficit imputé 0 ; bénéfice net fiscal servant à l’IS=2000000.
Aucun taux IS2025 n’est calculé ou inventé. Il ne s’agit pas d’une déclaration
DGI ou d’un justificatif d’une société réelle.

Saisir : désignation CSS fictive 2026 ; périmètre Société relevant de l’IS ; 
exercice de référence 2025 ; bénéfice 2000000 ; source du dernier exercice clos
confirmée oui ; exonération permanente non. Référence NOTE-CSS2025-743 ; 
justification Source fiscale fictive 2025 vérifiée, aucune exonération permanente
déclarée. CSS proposée=2000000 ×1,5%=30000. Si le contexte déclarait 0, écart=30000.
L’IS théorique B12 N1460 et le net comptable 6400 du petit dossier ne sont pas
utilisés pour ce calcul. Ces données ne qualifient aucun dossier réel.

Variante de seuil :999999.99 → CSS0 ; 1000000 →15000 ; 5000000 →125000 ; 
10000000 →350000 ; 40000000 →2000000. Les calculs sont indépendants et fictifs.
L’exonération permanente oui, explicitement justifiée dans le seul bac, donne
CSS0 ; ce scénario ne prouve pas l’éligibilité d’une société réelle.

## Recette humaine à effectuer

Prérequis communs : bac isolé, préparation 2026 et sources fictives ci-dessus,
administrateur ou comptable. Le profil Lecture sert aux refus de mutation.
Aucune écriture ni paiement attendu ; aucun effet fiscal réel confirmé.
Les statuts humains restent Non testé malgré les tests automatisés.

| ID | Actions et données exactes | Résultat et preuve attendus | Statut humain |
|---|---|---|---|
|CSS743-01|Ouvrir le petit dossier fictif 741 ; compléter la CSS avec 2025/2000000/oui/non, régime Société IS et NOTE-CSS2025-743 ; conserver.|CSS30000 au taux 1,500%, année 2026/référence 2025 ; B12 N et Journal inchangés ; capture et version.|Non testé|
|CSS743-02|Dans des versions successives, saisir 999999.99 puis 1000000,5000000,10000000,40000000 ; conserver à chaque fois, source fictive adaptée.|CSS0,15000,125000,350000,2000000 ; taux proportionnels sur tout le bénéfice, pas progressifs ; captures et anciennes versions.|Non testé|
|CSS743-03|Vider le bénéfice, l’exercice, une qualification ; puis choisir source du dernier clos non ; conserver séparément. Essayer Néant justifié sans ligne.|CSS indisponible, aucun zéro/non ou exercice 2025 inventé ; aucune reprise du net 6400 ou de B12 ; captures.|Non testé|
|CSS743-04|Reprendre 2025/2000000/source oui ; exonération permanente oui, justification NOTE-EXO-PERM743 fictive ; conserver.|CSS0, base déclarée conservée et taux théorique visible ; aucune validation juridique automatique ; capture.|Non testé|
|CSS743-05|Contexte fiscal CF-CSS déclaré 0 ; calcul CSS30000. Modifier explicitement CF-CSS à 30000 avec source fictive, conserver ; rouvrir CSS puis conserver après revue.|Écart initial 30000 ; alerte de contexte changé sans réécrire l’ancien contrôle ; nouvelle comparaison 0 après conservation CSS ; captures et versions.|Non testé|
|CSS743-06|Saisir NaN,−1,0.001 ou année de référence 2027 dans le dossier 2026 ; essayer de conserver puis corriger.|Refus 422, brouillon préservé et corrigeable, aucune nouvelle version ni écriture ; capture et trace du refus.|Non testé|
|CSS743-07|Ouvrir le dossier comme utilisateur Lecture ; consulter et télécharger ; responsable vérifie le refus serveur d’un POST direct sur le seul bac.|Aucun bouton de conservation, champs désactivés, lecture/export autorisés selon droits, POST403 ; captures et preuve technique, aucune mutation.|Non testé|
|CSS743-08|Modifier un bénéfice dans le brouillon sans conserver ; télécharger PDF/Excel/ZIP, relire une ancienne version puis la version courante.|Valeurs de la seule version conservée, source2025 et juridique, logo, taux en%, montantsMAD et manifesteSHA256 ; aucune valeur du brouillon exportée ; fichiers et captures.|Non testé|

## Exports et limites

Excel ajoute Origine CSS, Calcul CSS, Qualification CSS et Alertes CSS. Le taux
est en %, les montants en MAD. Le dossier ZIP inclut css_documentaire.json et son
manifesteSHA256. Un écart positif signifie que la proposition dépasse la CSS
déclarée dans le contexte conservé. Relire les sources ; aucune déclaration
n’est corrigée automatiquement. Un changement de contexte impose une nouvelle
conservation CSS pour actualiser explicitement la comparaison.

Les qualifications fiscales, la date de clôture/échéance, les justificatifs
réels, Office, la recette utilisateur et la production restent à vérifier.
Le calcul ne constitue pas une déclaration ou un prêt à déposer. Aucune base
réelle utilisée. RH/paie et point 6 humain restent différés.
