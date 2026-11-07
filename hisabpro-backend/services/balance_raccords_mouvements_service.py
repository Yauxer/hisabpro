"""Raccords explicites des clôtures de mouvements aux seules sources N figées."""
from copy import deepcopy
from decimal import Decimal,localcontext
from services import balance_etic_tables_service as commun
from services.balance_import_service import montant_import,empreinte_preparation

BLOC='raccords_mouvements_documentaires'
MV='mouvements_documentaires'
# Périmètres techniques des _section_b2/_section_b2bis/_section_b5 existantes.
PREFIXES={'B2':('21','22','23'),'B2bis':('281','282','283'),'B5':('15','29','39','45','59')}
NOTE=('Rattachements documentaires explicites aux comptes de la balance N conservée. '
      'Périmètres techniques HisabPro : B2 comptes21/22/23, B2bis281/282/283, B5 comptes15/29/39/45/59. '
      'Solde débiteur pour B2, créditeur pour B2bis/B5 ; signes inverses préservés. '
      'Comparaison : somme des clôtures déclarées rattachées moins solde du même compte. '
      'Un choix vide reste non rattaché ; une valeur inconnue ou un compte sans ligne ne devient pas0. '
      'Aucune attribution automatique, lecture du Journal courant ou correction d’écart. '
      'Les contrôles sont figés avec leurs mouvements/sources, distincts du brouillon. '
      'Un contrôle ancien doit être refait après changement de mouvements ou de sources. '
      'Un écart nul ne prouve pas la complétude du registre ou une conformité fiscale. Pas prêt à déposer.')


def empreintes(dossier):
    c=dossier['contenu']
    return {'empreinte_mouvements':empreinte_preparation(c[MV]) if c.get(MV) else None,
            'empreinte_source_n':empreinte_preparation({'n':c.get('sources',{}).get('n')})}


def sources(dossier):
    rows=dossier['contenu'].get('sources',{}).get('n')
    disponible=isinstance(rows,list) and all(isinstance(r,dict) and isinstance(r.get('compte'),str)
       and all(r.get(k) is not None and r.get(k)!='' for k in ('debit','credit')) for r in rows)
    return {'disponible':disponible,'comptes':{code:sorted({r['compte'] for r in rows if r['compte'].startswith(prefixes)}) if disponible else []
       for code,prefixes in PREFIXES.items()}}


def catalogue(dossier):
    bloc=dossier['contenu'].get(MV)
    if not bloc:raise ValueError('Conserver d’abord les mouvements documentaires B2/B2bis/B5.')
    schemas={t['code']:t for t in bloc['catalogue']}
    return [{'code':t['code'],'titre':schemas[t['code']]['titre'],'lignes':[
        {'ligne':i,'nature':r['nature'],'fin':r['fin'],'reference_source':r['reference_source']}
        for i,r in enumerate(t['lignes'],1)]} for t in bloc['tables']]


def normaliser(dossier,tables):
    originaux={t['code']:t for t in catalogue(dossier)};src=sources(dossier);vus=set();resultat=[]
    for t in tables:
        if t.code not in originaux or t.code in vus:raise ValueError('Tableau de rattachement inconnu ou en doublon.')
        vus.add(t.code);rows=[];indices=set()
        for r in t.lignes:
            if r.ligne in indices:raise ValueError('Chaque ligne de mouvement doit apparaître exactement une fois.')
            indices.add(r.ligne);compte=r.compte.strip()
            if compte and compte not in src['comptes'][t.code]:raise ValueError('Compte présent dans la source N et dans le périmètre du tableau requis.')
            rows.append({'ligne':r.ligne,'compte':compte})
        if indices!=set(range(1,len(originaux[t.code]['lignes'])+1)):
            raise ValueError('Toutes les lignes du tableau courant sont requises, sans indice inconnu ni omission.')
        resultat.append({'code':t.code,'lignes':sorted(rows,key=lambda r:r['ligne'])})
    if vus!=set(originaux):raise ValueError('Les trois tableaux de rattachement sont requis.')
    return sorted(resultat,key=lambda t:list(PREFIXES).index(t['code']))


def calculer_controles(dossier,demande):
    src=sources(dossier);orig={t['code']:t for t in demande['catalogue']};tableaux={}
    with localcontext() as ctx:
        ctx.prec=60
        for table in demande['tables']:
            code=table['code'];soldes={}
            if src['disponible']:
                for r in dossier['contenu']['sources']['n']:
                    compte=r['compte']
                    if compte in src['comptes'][code]:
                        n=montant_import(r['debit'],compte)-montant_import(r['credit'],compte)
                        soldes[compte]=soldes.get(compte,Decimal(0))+(n if code=='B2' else -n)
            valeurs={r['ligne']:r for r in orig[code]['lignes']};comptes=[]
            for compte,solde in sorted(soldes.items()):
                lignes=[valeurs[r['ligne']] for r in table['lignes'] if r['compte']==compte]
                somme=sum((Decimal(r['fin']) for r in lignes),Decimal(0)) if lignes and all(r['fin'] is not None for r in lignes) else None
                comptes.append({'compte':compte,'solde_source':format(solde,'.2f'),
                    'somme_clotures_declarees':None if somme is None else format(somme,'.2f'),
                    'ecart':None if somme is None else format(somme-solde,'.2f'),'lignes':len(lignes)})
            tableaux[code]={'comptes':comptes,'non_rattachees':[r['ligne'] for r in table['lignes'] if not r['compte']]}
    return {'methode':'clotures_declarees_rattachees_moins_solde_source_n_v1','source_disponible':src['disponible'],
        'tableaux':tableaux,'pret_a_deposer':False}


def presentation(dossier):
    bloc=dossier['contenu'].get(BLOC);actuel=bool(bloc and all(bloc.get(k)==v for k,v in empreintes(dossier).items()))
    courant=catalogue(dossier) if dossier['contenu'].get(MV) else []
    choix={t['code']:{r['ligne']:r['compte'] for r in t['lignes']} for t in bloc['tables']} if actuel else {}
    for t in courant:
        for r in t['lignes']:r['compte']=choix.get(t['code'],{}).get(r['ligne'],'')
    return {'conserve':bool(bloc),'actuel':actuel,'snapshot':deepcopy(bloc),'courant':courant,'sources':sources(dossier),
            'note':bloc.get('note_conservee',NOTE) if bloc else NOTE,'pret_a_deposer':False}


def conserver(db,user,preparation_id,data):
    return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,referentiel=catalogue,
        enrichir=lambda d,q:{'controle_raccords':calculer_controles(d,q),'note_conservee':NOTE,**empreintes(d)})
