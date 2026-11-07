"""Annexe de recette utilisateur, sans taux réglementaire inventé ni connexion DB."""
from pathlib import Path
from xml.sax.saxutils import escape
import json

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'docs/recette'
TITRE = 'CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
SALARIE = {'nom': 'Salma RECETTE FICTIVE', 'poste': 'Gestion administrative',
    'matricule': 'RH-REC-001', 'numero_cnss': '000000001', 'type_contrat': 'CDI',
    'date_embauche': '2026-01-01', 'email': 'salma.recette@example.com',
    'telephone': '', 'salaire_brut': '10000.00', 'situation_familiale': 'celibataire',
    'nb_enfants': 0, 'personnes_charge_ir': 0}


def cas():
    result = []
    def add(domaine, objectif, donnees, actions, attendu, statut='Non testé', prerequis=None):
        result.append({'id': f'RH-{len(result)+1:03}', 'module': domaine, 'objectif': objectif,
            'prerequis': prerequis or 'Société fictive RH RECETTE 2026 ; exercice 2026 ouvert ; administrateur connecté. Aucun dossier réel.',
            'donnees': donnees, 'actions': actions, 'attendu': attendu,
            'ecritures': 'Aucune écriture comptable créée ou modifiée par ce périmètre.',
            'fiscal': 'Aucune déclaration ni liquidation fiscale. Une simulation éventuelle ne valide pas la réglementation.',
            'controles': 'Recharger et comparer le résultat ; vérifier société active, erreurs affichées et absence de mutation comptable.',
            'statut': statut, 'resultat_reel': '', 'anomalies': '',
            'preuves': 'Capture de la page et du résultat ; joindre le CSV si exporté.', 'observations': ''})
    add('Dossiers', 'Créer une fiche complète', json.dumps(SALARIE, ensure_ascii=False),
        'Ouvrir Paie & GRH → Équipe → Ajouter un salarié. Saisir exactement les champs du jeu salarié, laisser date de sortie vide, confirmer zéro personne à charge, puis Enregistrer la fiche.',
        'Fiche active visible immédiatement ; brut 10 000,00 MAD ; champs relus après rechargement. Le numéro CNSS est volontairement fictif, sans attestation.')
    add('Dossiers', 'Modifier sans rafraîchissement manuel', 'Salma ; poste Gestion administrative et facturation ; salaire brut 10500.00.',
        'Équipe → Modifier Salma. Changer poste et brut puis Enregistrer la fiche. Ouvrir de nouveau la fiche.',
        'Nouvelles valeurs visibles immédiatement et après rechargement ; aucun salaire payé ni écriture générée.')
    add('Dossiers', 'Recherche et ordre des ajouts', 'Deuxième fiche : Youssef RECETTE FICTIVE ; matricule RH-REC-002 ; poste Logistique ; CDI ; embauche 2026-01-01 ; brut 8000.00 ; personnes à charge 0.',
        'Créer la seconde fiche. Comparer ordre des deux fiches ; rechercher RH-REC-001, puis effacer la recherche.',
        'Youssef ajouté après Salma apparaît en premier ; recherche ne conserve que Salma ; retour aux deux dossiers.')
    add('Dossiers', 'Archiver et restaurer', 'Youssef RH-REC-002.',
        'Cliquer Archiver Youssef et confirmer. Sélectionner Archivés, ouvrir la fiche puis Réactiver. Revenir au filtre Actifs.',
        'Dossier archivé puis restauré sans suppression ; données conservées et liste mise à jour.')
    add('Dossiers', 'Refuser salaire négatif et dates incohérentes', 'Nouvelle fiche Erreur RECETTE ; brut -1 ; puis brut 8000, embauche 2026-01-01 et sortie 2025-12-31.',
        'Tenter Enregistrer avec brut négatif. Corriger le brut puis tenter avec date de sortie antérieure à embauche. Fermer sans enregistrer.',
        'Enregistrement refusé avec erreur lisible ; aucun dossier invalide persisté.')
    add('Sécurité', 'Consultation sans mutation', 'Utilisateur lecture : lecteur.rh@example.com ; rôle lecture ; mot de passe temporaire RecetteRH2026! à changer.',
        'Créer ce compte depuis Paramètres → Utilisateurs dans la société fictive. Se connecter en lecteur, ouvrir Paie & GRH et Consulter Salma.',
        'Données consultables ; formulaire désactivé ; pas de création, modification, archivage ou décision de congés disponible.')
    add('Préparation', 'Afficher les paramètres manquants sans faux zéro', 'Administrateur ; octobre 2026 ; aucun nouveau taux ajouté à la société.',
        'Ouvrir Préparation mensuelle, choisir 2026 et Octobre. Lire les avertissements et les montants indisponibles.',
        'Si référentiel incomplet : préparation indisponible, motif explicite, montants non calculables affichés par tiret, export désactivé. Si complet : provenance et simulation clairement affichées ; conserver la preuve des paramètres.')
    add('Préparation', 'Personnes à charge explicitement confirmées', 'Salma ; brut restauré à 10000.00 ; situation mariée ; enfants 2 ; personnes à charge À confirmer.',
        'Modifier Salma avec ces valeurs. Ouvrir Préparation mensuelle. Puis confirmer personnes à charge0 dans la fiche et relire.',
        'Le mariage et les deux enfants ne deviennent pas automatiquement trois personnes à charge ; À confirmer bloque le calcul concerné. Confirmation zéro retire ce motif sans masquer les autres blocages.')
    add('Préparation', 'Choisir le mois et garder la sélection', 'Novembre 2026, puis Octobre 2026.',
        'Choisir Novembre, recharger la page et vérifier la sélection ; revenir à Octobre. Comparer les dates de dossier et messages.',
        'Mois réellement envoyé au serveur et conservé ; aucune écriture ni paiement produit.')
    add('Préparation', 'Entrée en cours de mois', 'Youssef ; embauche 2026-10-15 ; octobre 2026.',
        'Modifier la date d’embauche, ouvrir Préparation mensuelle pour Octobre ; ensuite restaurer embauche 2026-01-01.',
        'Entrée partielle signalée ; aucun prorata inventé et aucune simulation de mois entier présentée comme définitive.')
    add('Préparation', 'Paie réglementaire et bulletin', 'Bulletin figé, CNSS, journal SA, primes et retenues sur absences.',
        'Consigner le blocage ; ne pas chercher à valider un bulletin ou déclarer des cotisations depuis cette simulation.',
        'Fonctions absentes du périmètre actuel ; paramètres et règles officielles à vérifier avant développement et recette.',
        'Bloqué', 'Validation des sources CNSS/fiscales et développement du cycle de paie complet requis.')
    add('Congés et absences', 'Créer une demande datée', 'Salma ; Congé ; début 2026-10-12 ; fin 2026-10-14 ; motif REC-RH-CONGE-01.',
        'Paie & GRH → Congés & absences → Nouvelle demande. Sélectionner Salma, Congé et dates, saisir motif puis Enregistrer la demande.',
        'Demande au statut Demandé, trois jours calendaires inclusifs informatifs ; aucune réduction de salaire ni solde légal calculé.')
    add('Congés et absences', 'Refuser un chevauchement actif', 'Salma ; Absence ; début 2026-10-13 ; fin 2026-10-15 ; motif REC-RH-CHEVAUCHEMENT.',
        'Avant de décider la demande précédente, créer cette deuxième demande avec dates chevauchantes.',
        'Création refusée avec erreur lisible ; première demande intacte et aucune seconde demande active créée.')
    add('Congés et absences', 'Approuver et relire la piste d’audit', 'Demande REC-RH-CONGE-01 ; commentaire Accord de recette fictive.',
        'Administrateur : Approuver, saisir commentaire, Confirmer la décision. Ouvrir Historique et recharger.',
        'Statut Approuvé et commentaire persistés ; historique contient création puis décision, acteurs et dates ; aucun impact paie automatique.')
    add('Congés et absences', 'Annuler une demande approuvée', 'Demande REC-RH-CONGE-01.',
        'Administrateur : Annuler et confirmer. Ouvrir Historique. Créer ensuite la demande REC-RH-CHEVAUCHEMENT avec ses dates initiales.',
        'Annulation tracée sans effacer les événements ; dates libérées et deuxième demande maintenant autorisée.')
    add('Congés et absences', 'Refuser avec commentaire et état terminal', 'Demande REC-RH-CHEVAUCHEMENT ; commentaire Refus de recette fictive.',
        'Refuser la demande, saisir commentaire et confirmer. Ouvrir Historique puis vérifier les actions restantes.',
        'Statut Refusé ; commentaire et historique visibles ; pas d’action d’approbation ou annulation sur cet état terminal.')
    add('Congés et absences', 'Permissions de décision', 'Compte rôle comptable : comptable.rh@example.com ; mot de passe RecetteRH2026! ; Youssef ; absence 2026-11-02 au 2026-11-03 ; motif REC-RH-AUTEUR.',
        'Créer le compte en administrateur, se connecter en comptable, créer cette demande puis consulter ses actions. Annuler sa propre demande. Revenir en lecteur pour consulter l’historique.',
        'Comptable peut demander et annuler sa propre demande, sans approuver/refuser ; lecteur consulte sans mutation. Deux jours calendaires informatifs.')
    add('Sécurité', 'Isolation entre sociétés', 'Société B fictive RH AUTRE RECETTE ; dossier Salma seulement dans société A.',
        'Administrateur : créer ou sélectionner la société B, ouvrir Paie & GRH, vérifier dossiers et demandes. Revenir à A.',
        'Aucun dossier ou événement de A visible dans B ; retour A restitue ses propres dossiers. Aucun transfert silencieux.')
    add('Préparation', 'Export CSV d’une simulation complète', 'Mois complet et référentiel annuel officiellement vérifié, documenté puis configuré ; aucun taux de laboratoire à installer dans un dossier réel.',
        'Après levée du blocage de paramètres, ouvrir Préparation mensuelle, comparer les calculs à une feuille indépendante puis Exporter la préparation CSV ; ouvrir et comparer chaque montant.',
        'Export uniquement si toutes les lignes sont calculables ; valeurs identiques au serveur et avertissements de simulation présents. En l’absence de paramètres validés, test bloqué et export désactivé.',
        'Bloqué', 'Référentiel annuel complet vérifié par personne compétente ; oracle indépendant du dossier requis.')
    add('Traçabilité', 'Consulter une année sans preuve documentaire',
        'Société RH RECETTE 2026 ; exercice 2026 ; aucune preuve déjà consignée.',
        'Ouvrir Paie & GRH → Préparation mensuelle → Paramètres et sources. Lire Référentiel documentaire2026 et noter son empreinte actuelle.',
        'Statut Non vérifié, aucune version documentaire, avertissement paie définitive indisponible. Aucun taux installé ni montants changés.')
    add('Traçabilité', 'Consigner une preuve partielle sans date présumée',
        'Titre REC-RH-PREUVE-01 ; URL vide ; article REC-01 ; dates effet et consultation vides ; périmètre Traçabilité de recette uniquement ; limites Document fictif sans valeur réglementaire ; régime Laboratoire ; commentaire Première preuve fictive.',
        'Dans Référentiel documentaire2026, cliquer Consigner une preuve. Saisir les valeurs exactes, conserver les dates vides, puis Enregistrer la preuve. Recharger.',
        'Version1, statut Preuves partielles ; dates documentaires Non renseignées, auteur et date de consignation présents. Même empreinte capturée que RH-020. Simulation et paie définitive restent soumises à leurs blocages ; preuve ne vaut pas validation des taux.')
    add('Traçabilité', 'Ajouter une version et relire la première',
        'Titre REC-RH-PREUVE-02 ; URL https://example.com/recette-rh ; article REC-02 ; effet vide ; consultation2026-10-08 explicitement confirmée dans ce scénario ; périmètre Deuxième preuve fictive ; limites Exemple sans source officielle ; régime Laboratoire ; commentaire Version documentaire2.',
        'Consigner ces valeurs comme nouvelle preuve. Recharger, ouvrir Historique documentaire et comparer la version1 avec la capture RH-021. Ne pas ouvrir le lien fictif pour y chercher un texte officiel.',
        'Version2 courante et version1 conservée intégralement. Titre, commentaire, dates et empreinte de version1 inchangés ; même empreinte actuelle si aucun paramètre changé. Aucune action modifier ou supprimer une version.')
    add('Traçabilité', 'Refuser une preuve invalide sans perdre les versions',
        'Première tentative titre vide ; deuxième titre REC-RH-INVALIDE, URL http://example.com/recette-rh ; autres champs vides.',
        'Cliquer Consigner une preuve, tenter Enregistrer la preuve sans titre. Saisir ensuite le titre et URL HTTP puis retenter. Lire le message, Annuler la consignation et recharger.',
        'Titre obligatoire ; URL non HTTPS refusée avec erreur lisible. Toujours deux versions, aucune troisième preuve enregistrée ; anciennes preuves inchangées.')
    add('Traçabilité', 'Consulter les preuves sans droit administrateur',
        'Compte lecteur.rh@example.com du RH-006 ; société A ; année2026.',
        'Se connecter en lecteur, ouvrir Préparation mensuelle et Référentiel documentaire. Ouvrir Historique documentaire.',
        'Versions1/2 visibles dans la société autorisée ; bouton Consigner une preuve absent. Aucune mutation possible ; paie définitive toujours indisponible.')
    add('Traçabilité', 'Isoler les années et sociétés',
        'Administrateur ; société A avec exercices2025 (2025-01-01/2025-12-31) et2026 ; société B RH AUTRE RECETTE du RH-018, exercice2026 ; aucune preuve B ou A2025.',
        'Si nécessaire créer exercice2025 dans A depuis Exercices. Revenir à Paie & GRH. Ouvrir un formulaire de preuve sans enregistrer ; changer année2026→2025, puis société A→B. Revenir A2026.',
        'Formulaire fermé au changement ; ni succès ni données de2026A dans2025A ou B. Contextes sans preuve : Non vérifié. Retour A2026 restitue ses deux versions ; aucun transfert.',
        prerequis='Deux sociétés fictives et deux exercices ouverts explicitement créés. Ne pas modifier un exercice réel pour préparer ce test.')
    add('Traçabilité', 'Signaler des paramètres périmés en conservant les preuves',
        'Laboratoire isolé : rubrique fictive preuve_recette2090, taux_pat0.02 avant capture, puis0.03 après ; aucun autre taux, salarié ou calcul de paie activable. Valeurs sans portée réglementaire.',
        'Après préparation par opérateur de test, sélectionner exercice2090, ouvrir Référentiel documentaire et conserver capture version1. Après changement fictif confirmé par cet opérateur, Recharger. Lire le statut et les deux empreintes ; consigner une nouvelle preuve fictive REC-RH-PERIME-02 puis recharger.',
        'Statut Périmé avant nouvelle preuve, empreinte actuelle différente de celle capturée ; version1 conservée. Nouvelle version2 Preuves partielles, jamais Validé ou Conforme ; paie définitive indisponible.',
        'Bloqué', 'Opérateur requis pour préparer la rubrique et son changement dans une base de test isolée. Pas de formulaire UI dédié de configuration de ces paramètres retrouvé ; ne pas chercher à changer les taux réels. Les tests développeur couvrent ce scénario via API réelle mais ne prévalident pas cette recette utilisateur.')
    return result


def generer(destination=DEST):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    items = cas()
    texte = ('Annexe Paie / GRH, version du 8 octobre 2026. Toutes les données sont fictives. '
        'Cette annexe complète les 218 cas du cahier annuel. Les résultats utilisateur restent à renseigner. '
        'Le module gère les dossiers, demandes, preuves documentaires versionnées et une simulation conditionnelle ; '
        'bulletins figés, déclarations CNSS et écritures SA ne sont pas développés. '
        'Aucun taux réglementaire ni droit légal de congé n’est inventé.')
    cols = list(items[0])
    wb = Workbook()
    synth = wb.active
    synth.title = 'Synthèse'
    synth.append([TITRE])
    synth.append([texte])
    synth.append(['Domaine', 'Cas', 'Réussis', 'Échoués', 'Bloqués', 'Non testé'])
    for domaine in dict.fromkeys(c['module'] for c in items):
        subset = [c for c in items if c['module'] == domaine]
        ws = wb.create_sheet(domaine)
        ws.append(cols)
        for item in subset:
            ws.append([item[k] for k in cols])
        ws.freeze_panes = 'A2'
        ws.auto_filter.ref = ws.dimensions
        dv = DataValidation(type='list', formula1='"Non testé,Réussi,Échoué,Bloqué"')
        ws.add_data_validation(dv)
        dv.add(f'K2:K{ws.max_row}')
        synth.append([domaine, len(subset), *[f'=COUNTIF(\'{domaine}\'!K2:K{ws.max_row},"{s}")' for s in ['Réussi', 'Échoué', 'Bloqué', 'Non testé']]])
    dataset = wb.create_sheet('Jeu de données')
    dataset.append(['Champ', 'Valeur fictive exacte'])
    for key, value in SALARIE.items():
        dataset.append([key, value])
    for ws in wb:
        for cell in ws[1]:
            cell.font = Font(bold=True, color='FFFFFF')
            cell.fill = PatternFill('solid', fgColor='183D35')
        for row in ws:
            for cell in row:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 32
        if ws.title not in ('Synthèse', 'Jeu de données'):
            for i in range(2, ws.max_row+1):
                ws.row_dimensions[i].height = 160
    wb.save(destination / 'ANNEXE_RECETTE_PAIE_GRH.xlsx')
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(TITRE), styles['Title']), Spacer(1, 15),
        Paragraph('Annexe Paie / GRH', styles['Heading1']), Paragraph(escape(texte), styles['BodyText']),
        Paragraph(f'{len(items)} cas : {sum(c["statut"] == "Non testé" for c in items)} non testés, {sum(c["statut"] == "Bloqué" for c in items)} bloqués. Aucun résultat utilisateur prévalidé.', styles['BodyText'])]
    for item in items:
        story.append(PageBreak())
        story.append(Paragraph(escape(item['id'] + ' — ' + item['objectif']), styles['Heading1']))
        for key in cols:
            if key in ('id', 'objectif'):
                continue
            story.append(Paragraph(escape(key.replace('_', ' ').capitalize()), styles['Heading3']))
            story.append(Paragraph(escape(str(item[key]) or 'À renseigner pendant la recette.'), styles['BodyText']))
    SimpleDocTemplate(str(destination / 'ANNEXE_RECETTE_PAIE_GRH.pdf'), pagesize=A4,
        title=TITRE + ' — Annexe Paie GRH').build(story)
    (destination / 'ANNEXE_RECETTE_PAIE_GRH.md').write_text('# ' + TITRE + '\n\n## Annexe Paie / GRH\n\n' + texte +
        f'\n\nLes fichiers PDF et Excel portent les mêmes {len(items)} cas, avec colonnes résultat réel, anomalies et preuves. '
        'Les données CNSS et noms sont fictifs ; ne jamais les saisir dans un dossier réel. '
        'Les statuts de recette utilisateur ne reprennent pas automatiquement les succès des tests développeur.\n', encoding='utf-8')
    print(f'Annexe générée : {len(items)} cas, PDF et Excel')
    return items


if __name__ == '__main__':
    generer()
