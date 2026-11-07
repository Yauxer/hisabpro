"""Mouvements B2/B2bis/B5 déclarés : contrôle arithmétique sans flux inférés."""
from copy import deepcopy
from decimal import Decimal,localcontext
from services import balance_etic_tables_service as commun
from services.balance_emetteurs_service import nombre

BLOC='mouvements_documentaires'
CODES=('B2','B2bis','B5')
NOTE=('Mouvements documentaires internes de l’exercice N, déclarés depuis des sources explicites. '
      'Ouverture, augmentations/dotations, diminutions/sorties/reprises et clôture ne sont jamais déduites '
      'des seules balances N/N-1 ou du Journal courant. Contrôle indicatif : ouverture plus augmentations '
      'moins diminutions, puis écart clôture déclarée moins clôture reconstituée. '
      'Ouverture et clôture peuvent être signées ; augmentations et diminutions non négatives, en MAD. '
      'Une case vide reste inconnue. Les contrôles sont figés et distincts du brouillon. '
      'Aucun raccord par compte au bilan ou au registre, aucune exhaustivité ni qualification fiscale '
      'ne sont prouvés ; aucune écriture créée. Les cessions B3 restent un complément séparé. Pas prêt à déposer.')


def catalogue(dossier):
    bloc=dossier['contenu'].get(BLOC)
    if bloc:return deepcopy(bloc['catalogue'])
    from services.etic_service import CATALOGUE_ETIC
    resultat=[]
    for code in CODES:
        augmentation='Acquisitions et augmentations déclarées' if code=='B2' else 'Dotations déclarées'
        diminution={'B2':'Sorties et diminutions déclarées','B2bis':'Amortissements sortis déclarés','B5':'Reprises et utilisations déclarées'}[code]
        resultat.append({'code':code,'groupe':'B','titre':next(r['titre'] for r in CATALOGUE_ETIC if r['code']==code),
          'champ_identifiant':'nature','colonnes_saisie':[
            {'cle':'nature','label':'Nature déclarée','type':'text'},
            *[{'cle':k,'label':label,'type':'number','unite':'MAD','signe':signe} for k,label,signe in (
               ('debut','Ouverture déclarée',True),('augmentations',augmentation,False),
               ('diminutions',diminution,False),('fin','Clôture déclarée',True))]]})
    return resultat


def normaliser(dossier,tables):
    return commun.normaliser(dossier,tables,referentiel=catalogue,convertir_nombre=nombre)


def calculer_controles(dossier,demande):
    tableaux={}
    with localcontext() as ctx:
        ctx.prec=60
        for table in demande['tables']:
            lignes=[]
            for i,r in enumerate(table['lignes'],1):
                theorique=None if any(r[k] is None for k in ('debut','augmentations','diminutions')) else Decimal(r['debut'])+Decimal(r['augmentations'])-Decimal(r['diminutions'])
                fin=None if r['fin'] is None else Decimal(r['fin'])
                lignes.append({'ligne':i,'fin_reconstituee':None if theorique is None else format(theorique,'.2f'),
                  'fin_declaree':None if fin is None else format(fin,'.2f'),
                  'ecart_fin':None if theorique is None or fin is None else format(fin-theorique,'.2f')})
            totaux={}
            for k in ('fin_reconstituee','fin_declaree','ecart_fin'):
                n=sum((Decimal(r[k]) for r in lignes),Decimal(0)) if lignes and all(r[k] is not None for r in lignes) else None
                totaux[k]=None if n is None else format(n,'.2f')
            tableaux[table['code']]={'lignes':lignes,'totaux':totaux}
    return {'methode':'ouverture_plus_augmentations_moins_diminutions_declarees_v1','tableaux':tableaux,'pret_a_deposer':False}


def presentation(dossier):
    bloc=dossier['contenu'].get(BLOC) or {}
    vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
    vue['controle_mouvements']=deepcopy(bloc.get('controle_mouvements'))
    return vue


def conserver(db,user,preparation_id,data):
    return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,
        referentiel=catalogue,enrichir=lambda d,q:{'controle_mouvements':calculer_controles(d,q),'note_conservee':NOTE})
