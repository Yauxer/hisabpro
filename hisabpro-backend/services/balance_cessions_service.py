"""B3 documentaire : données déclarées et différence prix−VNA, sans résultat fiscal."""
from copy import deepcopy
from datetime import date
from decimal import Decimal,localcontext
import re
from services import balance_etic_tables_service as commun
from services.balance_etic_annexes_service import nombre

BLOC='cessions_documentaires'
NOTE=('B3 documentaire interne de l’exercice N, selon les données du tableau de cessions HisabPro existant. '
      'Valeur d’entrée, VNA et prix sont déclarés en MAD depuis des sources explicites ; ils ne sont jamais déduits des balances. '
      'Différence indicative = prix déclaré moins VNA déclarée, sans calcul de résultat fiscal. '
      'Dates et types facultatifs, aucune date reconstituée. Une donnée vide reste inconnue. '
      'Les contrôles concernent la version conservée, pas le brouillon. Aucun rapprochement des mouvements B2/B2bis '
      'ni exhaustivité du registre n’est prouvé ; aucune écriture ou liquidation fiscale créée. Pas de liasse prête à déposer.')


def catalogue(dossier):
    bloc=dossier['contenu'].get(BLOC)
    if bloc:return deepcopy(bloc['catalogue'])
    from services.etic_service import CATALOGUE_ETIC
    return [{'code':'B3','groupe':'B','titre':next(r['titre'] for r in CATALOGUE_ETIC if r['code']=='B3'),
      'champ_identifiant':'designation','colonnes_saisie':[
      {'cle':'designation','label':'Désignation du bien','type':'text'},
      {'cle':'date_sortie','label':'Date de sortie déclarée','type':'date'},
      {'cle':'type_sortie','label':'Type de sortie déclaré','type':'text'},
      *[{'cle':k,'label':v,'type':'number','unite':'MAD'} for k,v in (
        ('valeur_entree','Valeur d’entrée déclarée'),('vna','VNA déclarée'),('prix_cession','Prix de cession déclaré'))]]}]


def normaliser(dossier,tables):
    resultat=commun.normaliser(dossier,tables,referentiel=catalogue,convertir_nombre=nombre)
    for table in resultat:
        for r in table['lignes']:
            if r['type_sortie'] not in ('','cession','retrait','autre'):
                raise ValueError('Type de sortie : cession, retrait, autre ou vide requis.')
            if r['date_sortie']:
                try:
                    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',r['date_sortie']):raise ValueError('Format invalide')
                    date.fromisoformat(r['date_sortie'])
                except ValueError as exc:raise ValueError('Date de sortie déclarée invalide : format AAAA-MM-JJ requis.') from exc
    return resultat


def calculer_controles(dossier,demande):
    lignes=[];alertes=[]
    debut=date.fromisoformat(dossier['contenu']['periode']['debut']);fin=date.fromisoformat(dossier['contenu']['periode']['fin'])
    with localcontext() as ctx:
        ctx.prec=60
        for i,r in enumerate(demande['tables'][0]['lignes'],1):
            vna=None if r['vna'] is None else Decimal(r['vna'])
            prix=None if r['prix_cession'] is None else Decimal(r['prix_cession'])
            ecart=None if vna is None or prix is None else format(prix-vna,'.2f')
            lignes.append({'ligne':i,'difference_prix_vna':ecart})
            if r['valeur_entree'] is not None and vna is not None and vna>Decimal(r['valeur_entree']):
                alertes.append(f'Ligne {i} : VNA supérieure à la valeur d’entrée déclarée ; vérifier les sources sans ajustement automatique.')
            if r['date_sortie'] and not debut<=date.fromisoformat(r['date_sortie'])<=fin:
                alertes.append(f'Ligne {i} : date de sortie déclarée hors période conservée ; vérifier la déclaration.')
        total=sum((Decimal(r['difference_prix_vna']) for r in lignes),Decimal(0)) if lignes and all(r['difference_prix_vna'] is not None for r in lignes) else None
    return {'methode':'difference_prix_vna_declaree_decimal_v1','lignes':lignes,
            'total_difference_prix_vna':None if total is None else format(total,'.2f'),'alertes':alertes,'pret_a_deposer':False}


def presentation(dossier):
    bloc=dossier['contenu'].get(BLOC) or {}
    vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
    vue['controle_cessions']=deepcopy(bloc.get('controle_cessions'))
    return vue


def conserver(db,user,preparation_id,data):
    return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,
        referentiel=catalogue,enrichir=lambda d,q:{'controle_cessions':calculer_controles(d,q),'note_conservee':NOTE})
