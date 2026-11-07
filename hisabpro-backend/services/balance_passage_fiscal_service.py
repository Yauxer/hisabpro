"""B12 autonome : données comptables exactes et hypothèses fiscales sourcées."""
from copy import deepcopy
from decimal import Decimal,InvalidOperation,localcontext
from services import balance_etic_tables_service as commun
from services.balance_cpc_detail_service import calculer as detail_cpc
from services.balance_resultat_courant_service import sources as disponibilites
from services.balance_import_service import montant_import
from services.fiscalite_is_service import calculer_base_fiscale,calculer_is

LIBELLES={'resultat_net_comptable': 'Résultat net comptable', 'impots_comptabilises_67': 'Impôts comptabilisés67', 'resultat_avant_impots': 'Résultat avant impôts reconstitué', 'autres_reintegrations': 'Autres réintégrations hors67', 'reintegrations_depuis_net': 'Total des réintégrations depuis le net', 'deductions': 'Déductions déclarées', 'resultat_fiscal_avant_deficit': 'Résultat fiscal avant déficits', 'deficit_disponible_declare': 'Déficit disponible déclaré', 'deficit_impute_propose': 'Déficit imputé proposé', 'deficit_restant': 'Déficit disponible restant', 'deficit_genere': 'Déficit généré indicatif', 'benefice_fiscal_propose': 'Bénéfice fiscal proposé', 'taux_is_declare': 'Taux IS déclaré (%)', 'is_theorique_taux_declare': 'IS théorique selon taux déclaré'}
BLOC='passage_fiscal_documentaire'
NOTE=('B12 documentaire interne en MAD depuis la seule balance N conservée. '
      'Résultat net comptable et soldes67 distincts ; leur addition reconstitue '
      'le résultat avant impôts, selon le périmètre du moteur existant. '
      'Les autres réintégrations déclarées excluent ce67 déjà repris dans le '
      'passage depuis le net. Déductions, déficit disponible et taux sont '
      'explicitement déclarés et sourcés. Aucun régime, avantage, éligibilité '
      'ou millésime de déficit n’est déduit ; le disponible doit être justifié '
      'par un état fiscal revu. Imputation = proposition arithmétique, pas '
      'confirmation juridique. IS théorique selon le taux déclaré, jamais '
      'taux automatique du secteur ou de la société active. Une case vide '
      'reste inconnue, même pour un tableau déclaré néant. CM, CSS, crédits, '
      'acomptes et solde final restent à compléter dans un contexte distinct ; '
      'cet IS théorique ne représente donc pas une liquidation ou un montant '
      'à payer. Aucun Journal/module fiscal réel lu ou modifié ; aucune '
      'imputation confirmée ni écriture créée. Contrôles de la version '
      'conservée, distincts du brouillon ; pas de liasse prête à déposer.')


def catalogue(dossier):
    bloc=dossier['contenu'].get(BLOC)
    if bloc:return deepcopy(bloc['catalogue'])
    cols=[{'cle':'nature','label':'Désignation de la synthèse fiscale','type':'text'},
        {'cle':'reintegrations','label':'Autres réintégrations hors67','type':'number'},
        {'cle':'deductions','label':'Déductions fiscales déclarées','type':'number'},
        {'cle':'deficit_disponible','label':'Déficit disponible déclaré et justifié','type':'number'},
        {'cle':'taux_is','label':'Taux IS déclaré','type':'number','unite':'%'},
        {'cle':'regime_avantages','label':'Régime et avantages à justifier','type':'text'}]
    return [{'code':'B12-N','groupe':'B','titre':'Passage fiscal documentaire — N','colonnes_saisie':cols}]


def nombre(colonne,valeur,contexte):
    if colonne.get('unite')!='%':return format(montant_import(valeur,contexte),'.2f')
    if isinstance(valeur,bool) or not isinstance(valeur,(str,int,float)):
        raise ValueError(contexte+' : taux numérique requis.')
    try:
        raw=str(valeur).strip().replace('\u00a0','').replace('\u202f','').replace(' ','')
        if len(raw)>100 or (',' in raw and '.' in raw):raise ValueError('Taux ambigu.')
        n=Decimal(raw.replace(',','.'))
        if not n.is_finite() or n<0 or n>100 or n!=n.quantize(Decimal('.001')):
            raise ValueError('Taux fini de0 à100, trois décimales maximum.')
        return format(n.quantize(Decimal('.001')),'.3f')
    except (InvalidOperation,ValueError) as exc:raise ValueError(contexte+' : '+str(exc)) from exc


def normaliser(dossier,tables):
    tables=commun.normaliser(dossier,tables,referentiel=catalogue,convertir_nombre=nombre)
    for t in tables:
        if len(t['lignes'])>1:raise ValueError('Une seule synthèse fiscale sourcée par exercice est autorisée.')
        if not disponibilites(dossier)['n']['disponible'] and (t['lignes'] or t['statut']!='a_completer' or t['justification']):
            raise ValueError('Source N/CPC indisponible ; fournir une balance avant clôture technique.')
        for r in t['lignes']:
            if not r['nature'] or not r['reference_source']:
                raise ValueError('Désignation et référence explicite de source requises, même pour une synthèse partielle.')
    return tables


def calculer_controles(dossier,demande):
    base=detail_cpc(dossier)['periodes']['n'];table=demande['tables'][0]
    row=table['lignes'][0] if table['lignes'] else {}
    keys=('resultat_net_comptable','impots_comptabilises_67','resultat_avant_impots',
          'autres_reintegrations','reintegrations_depuis_net','deductions','resultat_fiscal_avant_deficit',
          'deficit_disponible_declare','deficit_impute_propose','deficit_restant','deficit_genere',
          'benefice_fiscal_propose','taux_is_declare','is_theorique_taux_declare')
    v={k:None for k in keys};alertes=[];lignes=deepcopy(base['lignes'])
    with localcontext() as ctx:
        ctx.prec=60
        net=Decimal(base['resultat']) if base['disponible'] else None
        impot=sum((Decimal(r['montant']) for r in lignes if r['compte'].startswith('67')),Decimal('0.00')) if base['disponible'] else None
        avant=None if net is None else net+impot
        ri,ded,deficit,taux=(None if row.get(k) is None else Decimal(row[k])
                              for k in ('reintegrations','deductions','deficit_disponible','taux_is'))
        v.update(resultat_net_comptable=net,impots_comptabilises_67=impot,resultat_avant_impots=avant,
            autres_reintegrations=ri,reintegrations_depuis_net=None if impot is None or ri is None else impot+ri,
            deductions=ded,deficit_disponible_declare=deficit,taux_is_declare=taux)
        fiscal=None
        if avant is not None and ri is not None and ded is not None:
            fiscal=calculer_base_fiscale(resultat_comptable_avant_is=avant,reintegrations=ri,
                deductions=ded,deficit_reportable_disponible=deficit)
            for cle,champ in [('resultat_fiscal_avant_deficit','resultat_fiscal_avant_deficit'),
                ('deficit_impute_propose','deficit_impute'),('deficit_restant','deficit_reportable_restant'),
                ('deficit_genere','deficit_fiscal_genere'),('benefice_fiscal_propose','benefice_fiscal_imposable')]:
                v[cle]=fiscal[champ]
        exercice=dossier.get('exercice',dossier['contenu'].get('exercice'))
        if fiscal is not None and fiscal['benefice_fiscal_imposable'] is not None and taux is not None:
            if isinstance(exercice,int) and not isinstance(exercice,bool) and exercice>=2023:
                calc=calculer_is(exercice=exercice,resultat_comptable_avant_is=avant,
                    reintegrations=ri,deductions=ded,deficit_reportable_disponible=deficit,taux_force=taux)
                v['is_theorique_taux_declare']=calc['is_theorique']
                if calc['taux_provisoire']:alertes.append('Exercice futur par rapport au référentiel du moteur ; taux déclaré à revoir, aucune conformité déduite.')
            else:alertes.append('Exercice absent ou hors périmètre du moteur IS2023+ ; aucun IS théorique calculé.')
        if table['statut']=='neant_declare' and net not in (None,Decimal(0)):
            alertes.append('Néant déclaré malgré un résultat comptable non nul ; aucune hypothèse fiscale égale à0 déduite.')
        def f(k,x):return None if x is None else format(x,'.3f' if k=='taux_is_declare' else '.2f')
        return {'methode':'base_fiscale_pure_partagee_et_taux_declare_v1','disponible':base['disponible'],
            'motif':base['motif'],'montants':{k:f(k,x) for k,x in v.items()},'lignes':lignes,
            'alertes':alertes,'a_completer':['Qualification et millésimes des déficits','Régime et taux applicables',
                'Cotisation minimale','CSS','Retenues/crédits déjà imputés','Acomptes','Solde final'],
            'liquidation':{k:None for k in ('cm','css','credits','acomptes','solde_final')},'pret_a_deposer':False}


def presentation(dossier):
    bloc=dossier['contenu'].get(BLOC) or {}
    vue=commun.presentation(dossier,nom_bloc=BLOC,referentiel=catalogue,note=bloc.get('note_conservee',NOTE))
    vue['sources']={'n':disponibilites(dossier)['n']}
    vue['controle_passage_fiscal']=deepcopy(bloc.get('controle_passage_fiscal'))
    notes=dossier['contenu'].get('notes_etic_documentaires',{}).get('lignes',[])
    if any(r['code']=='B12' and r['statut']=='non_applicable' for r in notes) and any(t['lignes'] for t in vue['tables']):
        vue['alertes'].append('La note B12 est non applicable alors qu’une synthèse fiscale est déclarée ; revoir les deux compléments.')
    return vue


def conserver(db,user,preparation_id,data):
    return commun.conserver(db,user,preparation_id,data,nom_bloc=BLOC,normalisation=normaliser,
        referentiel=catalogue,enrichir=lambda d,q:{'controle_passage_fiscal':calculer_controles(d,q),'note_conservee':NOTE})
