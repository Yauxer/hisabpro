# HisabPro — huit scénarios négatifs de saisie

Le formulaire d'inscription utilisait un minimum de six caractères alors que le serveur en impose déjà huit. Cette différence est reproduite dans le navigateur, puis corrigée par le seul changement minLength=8. La politique du serveur reste identique et aucune migration n'est ajoutée.

Les huit cas NEG001 à NEG008 sont exécutés sur ordinateur et mobile dans deux sociétés fictives isolées. Une seconde fenêtre sans session tente une inscription avec l'email déjà utilisé du laboratoire : refus400 et une seule société avec son utilisateur. L'email est unique au laboratoire, selon la convention de recette773. Le mot de passe court, cinq caractères, est invalide dans le navigateur et également refusé400 par le serveur, sans société orpheline.

Dans Paramètres, un ICE de14chiffres est refusé avec un message explicite et l'identité stockée reste strictement identique. Les bornes01/07/2025–30/06/2026 sont refusées en création, car2026 existe déjà dans ce laboratoire. Pour contrôler effectivement le chevauchement avec2025, le test propose en complément les mêmes bornes en modification de2026 : refus409 explicite de chevauchement. Aucune période n'est changée ni supprimée. Un exercice01/01/2027–31/01/2028 est refusé pour durée excessive et le calendrier reste identique.

Au Journal, D5141=100 et C1111=99 affichent un écart de1 et ne peuvent pas être enregistrés. L'API refuse aussi422 avant création d'une écriture. Dans Factures, le prix unitaire−10 pour une quantité1 est refusé après action finale d'enregistrement, avec message de ligne et formulaire conservé. L'API refuse422. Le taux101% n'est pas proposé dans la sélection du formulaire ; envoyé directement à l'API, il est refusé422 sans création ni correction automatique du taux.

Après les huit cas, aucune facture ni écriture n'est présente. Les nombres globaux de sociétés et utilisateurs sont identiques, ainsi que l'identité de la société et ses exercices. Seuls le tiers et l'article fictifs nécessaires aux essais sont préparés volontairement. Les refus n'engendrent aucun numéro comptable définitif.

Les essais initiaux sont conservés : différence du minimum de mot de passe reproduite ; méthodePUT incorrecte dans un contrôle de test remplacée par le PATCH existant ; action finale d'enregistrement ajoutée au test de prix négatif, le choix du mode brouillon ne soumettant pas le formulaire. Aucun de ces ajustements de test ne contourne un contrôle métier. Les deux parcours finaux réussissent. Build Vite réussi en6,31s avec avertissements existants de taille de bundle et d'import xlsx statique/dynamique.

Le suivi passe à144fiches réussies,5partielles,113nonqualifiées individuellement et10bloquées par les sources. Les70statuts fonctionnels restent inchangés. Aucun PostgreSQL utilisateur ni donnée comptable réelle n'a été utilisé ; la recette humaine et la conformité réglementaire ne sont pas validées automatiquement.

Prochaine étape : accès lecture, révocation des accès invités et changement personnel de mot de passe avec révocation des anciens jetons ; puis autres scénarios négatifs. RH/paie et point6 restent différés.
