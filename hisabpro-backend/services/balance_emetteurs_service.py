"""Déclarations B4 sourcées, sans déduire un émetteur depuis le compte général."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
from services import balance_etic_tables_service as commun
from services.balance_etic_annexes_service import nombre as nombre_annexe
from services.balance_import_service import montant_import

BLOC = 'declarations_emetteurs'
PERIODES = {'B4-N': 'n', 'B4-N1': 'n1'}
NOTE = ('Déclarations documentaires B4 en MAD, séparées du détail brut issu des balances. '
        'B4-N et B4-N1 sont des identifiants internes de formulaire. '
        'La valeur brute rattachée au251 et les produits reçus peuvent être signés. '
        'Capital non négatif ; quote-part de0 à100, au plus12 décimales. '
        'Une case vide reste inconnue. Les informations sur les émetteurs ne sont jamais '
        'déduites du compte, du capital ou du Journal courant. Les pourcentages de '
        'sociétés différentes ne sont pas additionnés. Les contre-valeurs MAD éventuelles '
        'doivent être justifiées, sans conversion automatique. Documenté ne signifie '
        'ni complet ni prêt à déposer. Les contrôles concernent la version conservée, '
        'pas le brouillon ; aucun écart n’est corrigé automatiquement.')


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    colonnes = [
        {'cle':'compte','label':'Compte251 source','type':'text'},
        {'cle':'emetteur','label':'Émetteur','type':'text'},
        {'cle':'identifiant','label':'Identifiant facultatif','type':'text'},
        {'cle':'valeur_brute','label':'Valeur brute rattachée au251','type':'number','unite':'MAD','signe':True},
        {'cle':'capital_emetteur','label':'Capital de l’émetteur','type':'number','unite':'MAD'},
        {'cle':'quote_part','label':'Quote-part détenue','type':'number','unite':'%'},
        {'cle':'produits_recus','label':'Produits reçus déclarés','type':'number','unite':'MAD','signe':True},
    ]
    return [{'code':code,'groupe':'B','titre':'Émetteurs — '+('N' if p=='n' else 'N-1'),
             'champ_identifiant':'emetteur','colonnes_saisie':deepcopy(colonnes)} for code,p in PERIODES.items()]


def sources(dossier):
    """Métadonnées de saisie seulement ; aucun contrôle financier recalculé au GET."""
    resultat = {}
    for p in ('n','n1'):
        lignes = dossier['contenu'].get('sources', {}).get(p)
        disponible = isinstance(lignes,list) and all(isinstance(r,dict) and isinstance(r.get('compte'),str)
            and all(r.get(k) is not None and r.get(k)!='' for k in ('debit','credit')) for r in lignes)
        resultat[p] = {'disponible':disponible, 'comptes':sorted({r['compte'] for r in lignes if r['compte'].startswith('251')}) if disponible else []}
    return resultat


def nombre(c, valeur, contexte):
    if not c.get('signe'):
        return nombre_annexe(c,valeur,contexte)
    if isinstance(valeur,bool) or not isinstance(valeur,(str,int,float)):
        raise ValueError(contexte+' : nombre signé invalide.')
    try:
        raw=str(valeur).strip().replace('\u00a0','').replace('\u202f','').replace(' ','')
        if len(raw)>100 or (',' in raw and '.' in raw):
            raise ValueError('Nombre ambigu ou trop long.')
        n=Decimal(raw.replace(',','.'))
        if not n.is_finite() or abs(n)>Decimal('9999999999999.99') or n!=n.quantize(Decimal('.01')):
            raise ValueError('Montant fini signé, borné et limité à deux décimales requis.')
        return format(n.quantize(Decimal('.01')),'.2f')
    except (InvalidOperation,ValueError) as exc:
        raise ValueError(contexte+' : '+str(exc)) from exc


def normaliser(dossier,tables):
    lignes=commun.normaliser(dossier,tables,referentiel=catalogue,convertir_nombre=nombre)
    disponibles=sources(dossier)
    for table in lignes:
        src=disponibles[PERIODES[table['code']]]
        if not src['disponible'] and (table['lignes'] or table['statut']!='a_completer' or table['justification']):
            raise ValueError('Source détaillée de cette période absente ou incomplète : aucune déclaration rattachée ne peut être conservée.')
        for r in table['lignes']:
            if any(v is not None and v!='' for v in r.values()) and r['compte'] not in src['comptes']:
                raise ValueError('Compte251 présent dans la balance de cette période requis pour rattacher la ligne.')
    return lignes


def calculer_controles(dossier,demande):
    resultat={}
    with localcontext() as ctx:
        ctx.prec=60
        for table in demande['tables']:
            p=PERIODES[table['code']];src=sources(dossier)[p];soldes={}
            if src['disponible']:
                for r in dossier['contenu']['sources'][p]:
                    if r['compte'].startswith('251'):
                        compte=r['compte'];soldes[compte]=soldes.get(compte,Decimal(0))+montant_import(r['debit'],compte)-montant_import(r['credit'],compte)
            comptes=[]
            for compte,solde in sorted(soldes.items()):
                rows=[r for r in table['lignes'] if r['compte']==compte]
                somme=sum((Decimal(r['valeur_brute']) for r in rows),Decimal(0)) if rows and all(r['valeur_brute'] is not None for r in rows) else None
                comptes.append({'compte':compte,'solde_brut_source':format(solde,'.2f'),
                    'somme_brute_declaree':None if somme is None else format(somme,'.2f'),
                    'ecart_brut':None if somme is None else format(somme-solde,'.2f'), 'lignes':len(rows)})
            alertes=[]
            if table['statut']=='neant_declare' and any(n!=0 for n in soldes.values()):
                alertes.append('Néant déclaré malgré un solde251 non nul ; revoir la déclaration et sa source.')
            resultat[p]={'disponible':src['disponible'],'comptes':comptes,'alertes':alertes}
    return {'methode':'comparaison_brut_declare_par_compte251_v1','periodes':resultat,'pret_a_deposer':False}


def presentation(dossier):
    bloc=dossier['contenu'].get(BLOC) or {}
    vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
    vue['sources']=sources(dossier)
    vue['controle_emetteurs']=deepcopy(bloc.get('controle_emetteurs'))
    notes=dossier['contenu'].get('notes_etic_documentaires',{}).get('lignes',[])
    if any(r['code']=='B4' and r['statut']=='non_applicable' for r in notes) and any(any(v is not None and v!='' for v in r.values()) for t in vue['tables'] for r in t['lignes']):
        vue['alertes'].append('La note B4 est non applicable alors que des émetteurs sont déclarés ; revoir les deux compléments.')
    return vue


def conserver(db,user,preparation_id,data):
    return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,
        referentiel=catalogue,enrichir=lambda d,q:{'controle_emetteurs':calculer_controles(d,q),'note_conservee':NOTE})
