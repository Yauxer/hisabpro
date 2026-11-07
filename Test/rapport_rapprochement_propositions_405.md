# Propositions exactes de rapprochement —405

GET en lecture seule puis confirmation explicite d’une sélection. Date,sens,compte,montant exact au centime et référence entière(trim uniquement,casse conservée). L’unicité est vérifiée sur tous les candidats,y compris les correspondances ambiguës ;aucun choix arbitraire. Règlements simples et ventilations natives immédiates ;sans084,liens simples conservés,groupes non activés.

POST authentifié avec permissions d’écriture :sélection1..500 d’entiers stricts,empreinte de la situation recalculée,verrou société et transaction unique. Toute obsolescence,doublon,autre compte/société,clôture ou contrainteSQL entraîne refus sans pointage partiel. Les pointages simples existants hors de la période du relevé restent exclus. Aucune écriture comptable créée ou modifiée.

UI bureau/mobile :sélection ajustable,rechargement,ambiguïtés et sans correspondance affichés. Réponses tardives après changement de compte ignorées. Une course initiale a été reproduite avec societe/moi retenue :bouton actif avant contexte prêt. Correction minimale :attendre société/exercice/situation,conserver gardes de contexte/token. Cinq Edge passent après cette correction. Sept payloads invalides supplémentaires refusés422 sans mutation.

Premiers essais conservés :oracle rollback comptait à tort les liens d’autres sociétés,remplacé par photographie SQL complète avant/après ;sélecteur monétaire corrigé pour virgule française ;banc de réponse retenue libéré avant unroute. Suite copie97réussites puis sept cas stricts et variantes supplémentaires. Les suites se recoupent et ne s’additionnent pas.

Limites :aucun rapprochement approximatif,référence extraite arbitrairement,montant absorbé ou instrument chèque/effet groupé créé. Les références d’un relevé réel ne sont pas supposées identiques à celles du Journal ;les cas non exacts restent manuels.

Historique inexploitable :GET listant les relevés avecNaN a réellement retourné500 ;après sécurisation de la lecture,deux Edge ont reproduit l’affichage trompeur+0,00. Lecture qualifiée et UI corrigées :montantnull,diagnostic,À vérifier,totaux concernés inconnus,pas de statut équilibré ni pointage de la ligne invalide. Aucun montant source réparé. Les correspondances certaines du même dossier restent confirmables. MontantsNaN/Inf/−Inf/0/−10 testés,ainsi que reprise d’ouverture inconnue et bureau/mobile ;photo SQL de la source invalide etcomptabilité conservées.

185tests racine réussis,456.818s,zéroéchec/erreur/ignoré ;721empreintes stables ;compilation etbuild code0.

Aucun PostgreSQL réel ni donnée comptable réelle ;sources et tests finaux sur PGnonce/Edge. Aucun SQL nouveau,main/modèles/migrations conservés. Recette humaine etpoint6 en attente.
