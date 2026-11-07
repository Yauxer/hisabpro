"""Cahier complémentaire677/679/681 : calculs indépendants en centimes."""
from pathlib import Path
from zipfile import ZipFile
import csv,importlib.util,json,math
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart,Reference
from openpyxl.workbook.properties import CalcProperties

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/recette'
NOM='ANNEXE_BALANCES_RAPPROCHEMENTS_20261020'
JSON_NOM='donnees_recette_balances_ras_20261020.json'
TITRE='CAHIER DE RECETTE FONCTIONNELLE ET TECHNIQUE — HISABPRO'
DOMAINES=['Balances','Rapprochements RAS']
CHAMPS=[('id','Identifiant'),('module','Module'),('objectif','Objectif'),('prerequis','Prérequis'),
 ('donnees','Données exactes'),('actions','Actions dans l’interface'),('attendu','Résultat attendu'),
 ('ecritures','Écritures attendues'),('fiscal','Impacts fiscaux'),('controles','Contrôles'),
 ('statut','Statut humain'),('reel','Résultat réel'),('anomalies','Anomalies constatées'),
 ('preuve_attendue','Preuve attendue'),('preuves','Preuves réelles'),('observations','Observations')]


def argent(cents):
    signe='-' if cents<0 else '';q,r=divmod(abs(cents),100)
    return f'{signe}{q}.{r:02d}'


def jeu():
    debits={'2311':100000,'2321':200000,'2331':300000,'2340':400000,'2351':500000,
        '2380':600000,'3111':700000,'3421':800000,'5141':1400000,'6111':100000}
    credits={'28321':30000,'1111':4470000,'7111':600000}
    balance=[{'compte':c,'debit':argent(debits.get(c,0)),'credit':argent(credits.get(c,0))}
        for c in sorted(set(debits)|set(credits))]
    n1=[{'compte':r['compte'],'debit':argent(debits.get(r['compte'],0)//2),
        'credit':argent(credits.get(r['compte'],0)//2)} for r in balance]
    # Pas d'import d'un calcul métier : toutes les attentes sont des calculs entiers.
    brut=sum(debits[c] for c in debits if c[0] not in '67')
    amort=credits['28321'];resultat=credits['7111']-debits['6111']
    capital=10000000;achat_ht=1000000;tva=200000;cash=525000;ras=75000
    avant_total=capital+achat_ht+tva+cash+ras
    banque_avant=capital-cash;banque_apres=banque_avant-ras
    return {'version':1,'publication':'2026-10-20','statut_humain':'À effectuer — aucune réussite préremplie',
        'environnement':'Base de recette isolée uniquement, aucune société réelle.',
        'societes':{'BAL':'RECETTE BALANCES 683 SARL','RAS':'RECETTE RAS 683 SARL'},
        'comptes_recette':{'administrateur':'admin683@example.com','lecteur':'lecture683@example.com',
            'mot_de_passe_fictif':'RecetteHisab683!2026'},
        'exercice':{'annee':2026,'date_debut':'2026-01-01','date_fin':'2026-12-31','statut':'ouvert'},
        'balance_n':balance,'balance_n1':n1,
        'fichiers':{'n':'BALANCE_FICTIVE_N_683.csv','n1':'BALANCE_FICTIVE_N1_683.csv','logo':'LOGO_FICTIF_683.png'},
        'oracle_balances':{'comptes':len(balance),'total_debit':argent(sum(debits.values())),
            'total_credit':argent(sum(credits.values())),'brut':argent(brut),'amortissements':argent(amort),
            'actif_net':argent(brut-amort),'passif':argent(credits['1111']+resultat),'cpc':argent(resultat),
            'n1_actif_net':argent((brut-amort)//2),'n1_cpc':argent(resultat//2),
            'immobilisations_corporelles_brut':argent(sum(debits[c] for c in debits if c.startswith('23'))),
            'immobilisations_corporelles_net':argent(sum(debits[c] for c in debits if c.startswith('23'))-amort)},
        'ras':{'date_operation':'2026-10-19','fournisseur':'FOURNISSEUR FICTIF RR683','article':'SERVICE FICTIF RR683',
            'prix_ht':'10000.00','tva_pct':'20','ttc':'12000.00','capital':'100000.00',
            'references':{'capital':'CAP-RR683','facture':'FOURN-RR683','cash':'VIR-RR683','capture':'RAS-RR683','versement':'VERSEMENT-RR683'},
            'simulation':{'date_paiement':'2026-10-19','payeur':'pm_privee_assujettie','prestataire':'pp_assujettie',
                'prestation_liste_b':True,'exclusion':'aucune_apres_controle','attestation':'presentee',
                'date_attestation':'2026-09-01','reference_attestation':'ATTESTATION-FICTIVE-RR683',
                'montant_paiement_ttc':'6000.00','tva_paiement':'1000.00'},
            'justification_quote_part':'VENTILATION FICTIVE RR683 : 5000 HT + 1000 TVA = 6000 TTC',
            'compte_capture_choisi':'4457','cash':'5250.00','retenue':'750.00'},
        'oracle_ras':{'avant_versement':{'pieces':4,'lignes':9,'debit':argent(avant_total),'credit':argent(avant_total),
                'banque':argent(banque_avant),'fournisseur_crediteur':'6000.00','compte4457_crediteur':'750.00',
                'cpc':'-10000.00','bilan':argent(banque_avant+tva)},
            'apres_versement':{'pieces':5,'lignes':11,'debit':argent(avant_total+ras),'credit':argent(avant_total+ras),
                'banque':argent(banque_apres),'fournisseur_crediteur':'6000.00','compte4457':'0.00',
                'cpc':'-10000.00','bilan':argent(banque_apres+tva)},
            'rapprochement_partiel':{'rapproche':'300.00','capacite_documentaire':'450.00'},
            'rapprochement_complet':{'rapproche':'750.00','capacite_documentaire':'0.00'},
            'retrait_du_second':{'rapproche':'300.00','capacite_documentaire':'450.00'},
            'impact_de_chaque_lien_ou_retrait':{'pieces':0,'lignes':0,'debit':'0.00','credit':'0.00'}},
        'limites':['Qualifications RAS supposées du laboratoire, aucun dossier réel qualifié.',
            'Compte4457 explicitement choisi dans le jeu, pas imposé réglementairement.',
            'Liasse seule complète, ETIC/fiscalité/annexes et formats officiels toujours partiels ou bloqués.',
            'Le rapprochement n’est ni preuve de versement DGI ni crédit imputable ; aucune déclaration automatique déverrouillée.',
            'Installation103 réelle, recette humaine et production non validées. RH/paie différées.']}


def cas():
    ts=[]
    def add(id,module,objectif,donnees,actions,attendu,ecritures='Aucune nouvelle écriture.',prerequis='Cas précédent terminé sur base fictive isolée.',controles='Comparer aux montants de l’oracle et conserver la preuve.'):
        ts.append(dict(id=id,module=module,objectif=objectif,prerequis=prerequis,donnees=donnees,actions=actions,
            attendu=attendu,ecritures=ecritures,fiscal='Aucune validation fiscale automatique ; hypothèses du laboratoire seulement.',
            controles=controles,statut='Non testé',reel='',anomalies='',preuve_attendue='Capture de l’écran et export lorsqu’il est indiqué.',preuves='',observations=''))
    add('BAL683-01','Balances','Créer la société de balances','RECETTE BALANCES 683 SARL ; MAD ; exercice2026 du01/01 au31/12.',
        'Créer une nouvelle société depuis le sélecteur. Vérifier son plan et l’exercice2026 ouvert. Choisir cette société. Les ICE/IF manquants restent signalés ; ne pas inventer de références réelles.',
        'Société distincte, comptes du CSV présents dans son plan, aucune écriture au Journal.',prerequis='Administrateur et base vierge isolée fournis par le technicien. Application et migration103 préparées sur cette seule cible.')
    add('BAL683-02','Balances','Importer N et N-1','BALANCE_FICTIVE_N_683.csv et BALANCE_FICTIVE_N1_683.csv,13comptes chacun.',
        'Comptabilité → Liasse fiscale → Préparer depuis des balances externes → Importer N / N-1. Joindre les deux CSV fournis, puis Contrôler et préparer.',
        'Débit=crédit51000MAD ; actif/passif49700 ; CPC5000 ; N-1 actif24850 et CPC2500. Aucune archive fiscale ni écriture créée.')
    add('BAL683-03','Balances','Conserver et rouvrir la version','Préparation contrôlée du cas02.',
        'Cliquer Conserver une nouvelle version. Relever version1 et son empreinte. Recharger la page, ouvrir Importer N / N-1 puis sélectionner version1 dans Préparations conservées, sans joindre les CSV à nouveau.',
        'Même version, même empreinte et mêmes totaux. Les fichiers sources normalisés ont été conservés.')
    add('BAL683-04','Balances','Vérifier le détail des immobilisations','Corps : brut21000, amortissements300, net20700 ; N-1 net10350.',
        'Dans version1, cliquer Consulter le bilan et les comptes sources. Choisir Actif. Rechercher visuellement les sous-postes231/232/233/234/235/238. Sur mobile, faire défiler horizontalement le tableau pour lire les colonnes de droite.',
        'Bruts1000/2000/3000/4000/5000/6000. Les amortissements et nets non ventilés restent Indisponible. Total général brut50000/amortissements300/net49700 ; N-1 net24850. Ne pas additionner les sous-postes une seconde fois.')
    add('BAL683-05','Balances','Consulter les comptes sources N/N-1','Compte28321 : crédit300 enN,150 enN-1.',
        'Dans Comptes sources normalisés, sélectionner N et rechercher28321. Vérifier une seule ligne. Passer à N-1 et rechercher28321 à nouveau. Rechercher9999999999, puis effacer le filtre.',
        'Crédit300 puis150, aucun compte pour9999999999 ; effacement retrouve13comptes. Aucun intitulé historique inventé depuis le plan courant.')
    add('BAL683-06','Balances','Exporter la version contrôlée','Version1 et empreinte relevée au cas03 ; fichier LOGO_FICTIF_683.png fourni.',
        'Dans les paramètres de la société fictive, importer LOGO_FICTIF_683.png, simple rectangle bleu de test. Revenir à la version1 de préparation. Cliquer Exporter la préparation Excel puis Exporter la préparation PDF. Ouvrir les documents et comparer version/empreinte, bilans, CPC et balances sources.',
        'Exercice2026/version1/même empreinte. PDF et Excel montrent le détail et les comptes. Le motif bleu est présent. Le logo/identité actuels sont hors empreinte ; aucune ancienne version n’est réécrite.')
    add('BAL683-07','Balances','Vérifier N-1 absent et préservation de version1','Réimporter uniquement BALANCE_FICTIVE_N_683.csv.',
        'Actualiser la page puis importer seulement N, contrôler et conserver version2. Consulter le détail et sélectionner N-1. Revenir ensuite à version1 et réexporter son PDF.',
        'Version2 : N-1 indisponible, jamais supposé nul. Version1 conserve sa sourceN-1, son empreinte et ses chiffres ; son export porte toujoursv1.')
    add('RRP683-01','Rapprochements RAS','Préparer les quatre pièces sources du jeu','Nouvelle société RECETTE RAS 683 SARL ; capital100000 ; facture12000TTC ; cash5250 ; capture750 ; date19/10/2026.',
        'Créer la société RAS distincte enMAD, exercice2026 ouvert, TVA encaissement, prorata du laboratoire100%. Saisir auJournalBQ CAP-RR683 : débit5141=100000, crédit1111=100000, puis valider. Créer le fournisseur FOURNISSEUR FICTIF RR683. Créer une facture achat du19/10/2026 référenceFOURN-RR683, service quantité1 prixHT10000 TVA20%, charge déductible100% du laboratoire. Valider la facture, comptabiliser et valider son écriture. Enregistrer un virement5250 référenceVIR-RR683 comptabilisé, puis valider sa pièce. Dans le règlement, utiliser l’assistant TVA117-V-b : payeur personne morale privée assujettie, prestataire personne physique assujettie, listeB oui, aucune exclusion après contrôle dans ce seul jeu, attestation présentée du01/09/2026 référenceATTESTATION-FICTIVE-RR683 ; quote-part6000TTC dont1000TVA ; justification VENTILATION FICTIVE RR683 : 5000 HT + 1000 TVA = 6000 TTC. Choisir4457, référenceRAS-RR683, confirmer et valider l’OD750.',
        '4pièces validées/9lignes ; débit=crédit118000 ; banque94750 ; fournisseur créditeur6000 ; compte4457 créditeur750 ; résultat−10000 ; bilan96750.',
        'Capital : D5141/C1111=100000. Achat : D6111=10000,D34552=2000,C4411=12000. Cash : D4411/C5141=5250. Capture : D4411/C4457=750.',
        prerequis='Société de recette distincte des balances. Qualifications supposées du laboratoire et données JSON complètes ; ne pas utiliser ces faits pour qualifier une opération réelle.')
    add('RRP683-02','Rapprochements RAS','Saisir la pièce de versement à rapprocher','RéférenceVERSEMENT-RR683, date19/10/2026, débit4457=750, crédit5141=750.',
        'Dans Journal, créer la pièceBQ VERSEMENT-RR683 avec les deux lignes indiquées, puis la valider. Consulter ses montants avant toute création de rapprochement.',
        '5pièces validées/11lignes ; débit=crédit118750 ; banque94000 ;4457soldé ; fournisseur6000 ; CPC−10000 ; bilan96000.',
        'Une nouvelle pièce de750 au débit et au crédit. Aucune date de paiement fiscal n’est déduite de sa date comptable.')
    add('RRP683-03','Rapprochements RAS','Rapprocher une première part300','Capture750 ; pièce validéeVERSEMENT-RR683 ; montant300.',
        'Déclaration TVA → Registre des retenues TVA2026 → capture sur achat → Rapprochement comptable d’un versement. Chercher VERSEMENT-RR683, sélectionner la pièce, saisir300, confirmer le rapprochement documentaire puis enregistrer.',
        'Lien actif300, capacité documentaire450 ; acteur et empreinte visibles. Journal inchangé à5pièces/11lignes et118750MAD.')
    add('RRP683-04','Rapprochements RAS','Compléter par450','Même capture et même pièce ; montant450.',
        'Sélectionner à nouveau la pièce disponible, saisir450, confirmer et enregistrer. Actualiser les rapprochements.',
        'Deux liens actifs300+450=750 ; capacité documentaire0. Aucun double paiement ni écriture supplémentaire.')
    add('RRP683-05','Rapprochements RAS','Retirer le lien450','Motif : ERREUR DOCUMENTAIRE FICTIVE RR683.',
        'Sur le lien450, cliquer Retirer le rapprochement, saisir exactement le motif, puis Confirmer le retrait documentaire. Relire la trace après actualisation.',
        'Lien300 actif et lien450 retiré conservés. Montant rapproché300, capacité documentaire450. Le versement comptabilisé reste750 :450n’est pas un reste fiscal à payer.')
    add('RRP683-06','Rapprochements RAS','Refuser un dépassement','Après retrait, capacité450 ; tentative500 sur la même pièce.',
        'Choisir la pièceVERSEMENT-RR683, saisir500, confirmer puis enregistrer. Lire l’alerte et actualiser les rapprochements.',
        'Rejet explicite ; montant rapproché toujours300, capacité450 et deux traces. Aucun changement de pièce, lien ou retrait.')
    add('RRP683-07','Rapprochements RAS','Vérifier le lecteur et le PDF','Compte Lecture lecture683@example.com, mot de passe fictif RecetteHisab683!2026 ; LOGO_FICTIF_683.png.',
        'Dans la société RAS, importer le logo de test dans les paramètres puis créer le compte Lecture indiqué depuis Administration → Utilisateurs. Se déconnecter et se reconnecter avec ce compte. Ouvrir la capture et les rapprochements. Vérifier l’absence de commandes de création/retrait. Télécharger PDF des rapprochements documentaires et l’ouvrir.',
        'Lecture et PDF autorisés ; liens actif300/retiré450 et motif conservés, empreintes et références exactes. Logo actuel si configuré. Le PDF interne ne vaut pas reçu fiscal.')
    add('RRP683-08','Rapprochements RAS','Vérifier le cloisonnement et le sens des soldes','Société BAL du cas01, ne contenant aucune capture RAS de la société RAS.',
        'Revenir au compte administrateur, sélectionner RECETTE BALANCES 683 SARL et ouvrir son registre TVA2026. Vérifier l’absence de captureRR683. Revenir ensuite à la société RAS et retrouver les deux traces.',
        'Aucune capture ni pièce de l’autre société visible. Retour : mêmes liens et écritures. Déclaration/imputation/versement DGI toujours distincts de cette preuve documentaire.')
    return ts


def markdown(d,ts):
    l=['# '+TITRE,'Version 1 du 20 octobre 2026','Complément 677/679/681 — Balances détaillées et rapprochements documentaires RAS',
        'Mode d’emploi et cahier complémentaire. Les15cas humains sont Non testé. Résultat réel, anomalies et preuves restent à renseigner. Aucun résultat humain n’est déduit des tests automatisés.',
        'Développement du périmètre décrit disponible ; tests automatisés consignés séparément ; recette utilisateur à effectuer ; production : non validée.',
        '## Préparer la recette','Un technicien fournit une base de test isolée et fait appliquer explicitement la chaîne103. Ne jamais utiliser une société réelle. Les commandes de laboratoire créent leurs propres cibles et ne migrent pas la base utilisateur.',
        'Le technicien prépare le compte administrateur fictif admin683@example.com, mot de passe RecetteHisab683!2026, dans une société initiale LAB ACCUEIL 683. Ce mot de passe publié est réservé au laboratoire. Le lecteur lecture683@example.com sera créé au casRRP683-07 avec le même mot de passe fictif.',
        'Créer deux sociétés distinctes : RECETTE BALANCES 683 SARL et RECETTE RAS 683 SARL. DeviseMAD, exercice2026du01/01au31/12ouvert. Conserver les alertes ICE/IF lorsqu’ils ne sont pas fournis ; ne pas inventer de justificatifs réels.',
        'Les CSV fournis ont une feuille logique et les colonnescompte,debit,credit ; ils alimentent uniquement une préparation de balances, jamais le Journal. Le classeur de suivi à plusieurs feuilles n’est pas un fichier de balance à importer.',
        '## Données et calculs indépendants','Calculs en entiers/centimes, sans appel aux services de l’application. Les montants du scénario sont exclusivement fictifs.',
        'BalanceN :13comptes ; débit=crédit51000MAD ; actif brut50000, amortissements300, net49700 ; passif49700 ; résultat5000. N-1 : actif net24850, résultat2500.',
        'Immobilisations corporelles : brut21000, amortissements300, net20700, N-1 net10350. Sous-postes231/232/233/234/235/238 : bruts1000/2000/3000/4000/5000/6000. Ne pas inventer la ventilation des amortissements/net entre ces sous-postes.',
        'Jeu RAS : capital100000 ; achat10000HT+2000TVA=12000TTC ; quote-part6000dont1000TVA ; retenue supposée du laboratoire750 ; cash5250. Les qualifications de l’assistant sont des hypothèses documentées du jeu, pas une qualification d’un dossier réel.',
        'Avant pièce de versement :4pièces/9lignes, débit=crédit118000, banque94750, fournisseur6000créditeur,4457créditeur750,CPC−10000,bilan96750.',
        'Après pièce de versement :5pièces/11lignes, débit=crédit118750, banque94000, fournisseur6000créditeur,4457soldé,CPC−10000,bilan96000. Les liens300+450puis le retrait450ne modifient aucun de ces chiffres.',
        'La capacité documentaire450après retrait ne signifie pas reste à payer450 : la pièce de versement750reste comptabilisée. Le retrait ne contrepassera aucune écriture.',
        '## Comment utiliser les avancées','Depuis Liasse fiscale, conserver la préparation puis consulter son bilan et ses comptes sources. Les exports PDF/XLSX portent la version/empreinte ; le logo et l’identité actuels restent hors empreinte.',
        'Les sous-postes du bilan sont pour mémoire et ne se somment pas une deuxième fois. Sans sourceN-1, les comparatifs sont indisponibles, pas nuls. Le tableau du bilan se défile horizontalement sur mobile sans déplacer toute la page.',
        'Depuis Déclaration TVA ou la Liasse, ouvrir le registre des captures achats, choisir Rapprochement comptable d’un versement, sélectionner une pièce déjà validée et saisir le montant explicite. Les comptes choisis dans le jeu ne sont pas imposés réglementairement.',
        'Le PDF des rapprochements est séparé des exports annuels099. Les pièces, acteurs, empreintes et retraits y restent visibles. Ce document n’est ni un reçu fiscal, ni un bordereau DGI, ni une attestation de droit à imputation.',
        '## Ordre de passage et suivi humain','Exécuter BAL683-01à07puis RRP683-01à08. Les véritables numéros de pièces sont attribués par l’application : relever ceux affichés, sans supposer un identifiant technique. Le tableau de bord Excel se recalcule à l’ouverture ; ses statuts humains restent vierges de réussite.']
    for t in ts:
        l += ['## '+t['id']+' — '+t['objectif']]
        l += [label+' : '+(t[k] if t[k] else 'À renseigner par la personne chargée de la recette.') for k,label in CHAMPS if k not in ('id','objectif')]
    l += ['## Limites et prochaine reprise']+d['limites']
    l += ['Les guides généraux antérieurs et leurs statuts humains restent conservés. Modes d’emploi : docs/LIASSE_BALANCES_DETAIL_677.md, docs/LIASSE_BALANCES_CONSULTATION_679.md et docs/RAS_RAPPROCHEMENT_681.md. Les rapports techniques détaillent les commandes réellement exécutées.']
    # Lisibilité : conserver les données structurées exactes ; espacer les groupes
    # nombre/unité et les références seulement dans la prose générée.
    import re
    def lisible(v):
        v=v.replace('prixHT','prix HT').replace('auJournalBQ','au Journal BQ').replace('pièceBQ','pièce BQ').replace('CPC−','CPC −')
        v=re.sub(r'\b([Rr]éférence)(?=[A-Z])',r'\1 ',v)
        v=re.sub(r'(?<=\d)(MAD|HT|TTC|TVA|comptes|pièces|lignes|créditeur|soldé|puis|cas\b|du\b|ouvert|et\b|au\b|à\b|sur\b|dont\b|ne\b|enN)',r' \1',v)
        v=re.sub(r'\b(exercice|capital|débit|crédit|actif|passif|bilan|CPC|brut|net|amortissements|fournisseur|banque|trésorerie|créditeur|version|phase|cas|lien|pièces|lignes|MAD|TVA|TTC|HT|puis|du|au|en|à|compte|OD|BQ|Les|montant|date|Choisir|capacité|déductible|validée)(?=\d)',r'\1 ',v,flags=re.I)
        return v
    return '\n\n'.join(x if x.startswith('## BAL') or x.startswith('## RRP') else lisible(x) for x in l)+'\n'


def classeur(out,d,ts):
    wb=Workbook();s=wb.active;s.title='Synthèse';wb.calculation=CalcProperties(fullCalcOnLoad=True)
    s.append([TITRE]);s.append(['Recette humaine à effectuer — aucune réussite préremplie'])
    s.append(['Domaine','Non testé','Réussi','Échoué','Bloqué','Total','Progression'])
    for i,n in enumerate(DOMAINES,4):
        xs=[t for t in ts if t['module']==n];ws=wb.create_sheet(n);ws.append([label for _,label in CHAMPS])
        for t in xs:ws.append([t[k] for k,_ in CHAMPS])
        dv=DataValidation(type='list',formula1='"Non testé,Réussi,Échoué,Bloqué"');ws.add_data_validation(dv);dv.add(f'K2:K{len(xs)+1}')
        s.append([n]+[f'=COUNTIF(\'{n}\'!K2:K{len(xs)+1},"{st}")' for st in ('Non testé','Réussi','Échoué','Bloqué')]+[f'=SUM(B{i}:E{i})',f'=IF(F{i}=0,0,C{i}/F{i})'])
    s.append(['TOTAL']+[f'=SUM({c}4:{c}5)' for c in 'BCDEF']+['=IF(F6=0,0,C6/F6)'])
    for i in range(4,7):s.cell(i,7).number_format='0%'
    ch=BarChart();ch.title='État de la recette humaine';ch.add_data(Reference(s,min_col=2,max_col=5,min_row=3,max_row=5),titles_from_data=True);ch.set_categories(Reference(s,min_col=1,min_row=4,max_row=5));s.add_chart(ch,'A10')
    ordre=wb.create_sheet('Ordre de passage');ordre.append(['Ordre','Identifiant','Domaine','Objectif','Statut humain'])
    for i,t in enumerate(ts,1):ordre.append([i,t['id'],t['module'],t['objectif'],'Non testé'])
    donnees=wb.create_sheet('Données');donnees.append(['Objet','Données exactes'])
    for k in ('societes','comptes_recette','exercice','fichiers','ras'):donnees.append([k,json.dumps(d[k],ensure_ascii=False)])
    oracle=wb.create_sheet('Oracle');oracle.append(['Domaine','Contrôle / phase','Valeur exacte'])
    for k,v in d['oracle_balances'].items():oracle.append(['Balances',k,str(v)])
    for phase,values in d['oracle_ras'].items():
        for k,v in values.items():oracle.append(['RAS',phase+' · '+k,str(v)])
    a=wb.create_sheet('Anomalies');a.append(['ID anomalie','ID test','Constat','Gravité','Statut','Décision'])
    preuves=wb.create_sheet('Preuves');preuves.append(['ID test','Capture / fichier attendu','Preuve réelle','Observations'])
    for t in ts:preuves.append([t['id'],t['preuve_attendue'],'',''])
    limites=wb.create_sheet('Limites');limites.append(['Limite restante','Action'])
    for x in d['limites']:limites.append([x,'Qualification humaine / sources applicables à obtenir.'])
    for ws in wb:
        ws.freeze_panes='D2' if ws.title in DOMAINES else 'A2';ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='185FA5')
        for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=50 if ws.title in DOMAINES else 38
        if ws.title in DOMAINES:
            for c in ('E','F','G'):ws.column_dimensions[c].width=100
        if ws.title=='Données':ws.column_dimensions['B'].width=100
        for row in ws:
            for c in row:
                c.alignment=Alignment(vertical='top',wrap_text=True)
                if isinstance(c.value,str) and not c.value.startswith(('=COUNTIF','=SUM','=IF')):c.data_type='s'
        for i in range(2,ws.max_row+1):
            ws.row_dimensions[i].height=min(400,max(45,15*max(math.ceil(len(str(c.value or ''))/max(20,ws.column_dimensions[c.column_letter].width)) for c in ws[i])))
    s.merge_cells('A1:G1');s.merge_cells('A2:G2');s.column_dimensions['A'].width=32
    for c in 'BCDEFG':s.column_dimensions[c].width=15
    wb.save(out/(NOM+'.xlsx'))


def generer(out=OUT):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    d=jeu();ts=cas();d['cas']=ts
    (out/JSON_NOM).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
    for cle in ('n','n1'):
        with (out/d['fichiers'][cle]).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['compte','debit','credit'],delimiter=';');w.writeheader();w.writerows(d['balance_'+cle])
    from PIL import Image
    Image.new('RGB',(20,12),'#185FA5').save(out/d['fichiers']['logo'],'PNG')
    md=out/(NOM+'.md');md.write_text(markdown(d,ts),encoding='utf8')
    spec=importlib.util.spec_from_file_location('guide_ooxml683',ROOT/'docs/guide/generer_guide.py')
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    g.SOURCE=md;g.STEM=out/NOM;items=g.blocs();g.docx(items);g.pdf(items)
    classeur(out,d,ts)
    return d


if __name__=='__main__':
    d=generer();print('Cahier complémentaire généré :',len(d['cas']),'cas humains Non testé.')
