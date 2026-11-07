"""C3 depuis les seules balances conservées, sans interrogation du Journal/RH."""
from copy import deepcopy
from decimal import Decimal,localcontext
from types import SimpleNamespace
from services import balance_etic_tables_service as commun
from services.balance_import_service import montant_import
from services.balance_source_controle_service import cloture_technique
from services.etic_service import _calcul_c3_depuis_soldes

BLOC='indicateurs_comptables_documentaires'
CHAMPS=('situation_nette','chiffre_affaires_ht','resultat_avant_impots','impots_resultats','resultat_net','salaires_bruts')
NOTE=('C3 comptable interne en MAD, calcul partagé avec le moteur ETIC existant, '
      'sortie décimale exacte. Sources détaillées N/N-1 uniquement, jamais le '
      'Journal ou les salariés de la société courante. Situation nette : comptes11/13 '
      '+ résultat − non-valeurs21 + amortissements281, selon le moteur existant. '
      'Après solde technique119, situation nette calculable sans ajouter un second '
      'résultat ; activité indisponible, jamais zéro fabriqué. Rémunérations6171 '
      'désigne le solde comptabilisé, sans validation des bulletins ou de la paie. '
      'N-2, effectif moyen, distributions et données par titre restent à documenter '
      'sur sources explicites ; aucun historique ou libellé de compte déduit. '
      'Les écarts aux états figés restent visibles. Ce complément ne constitue '
      'ni C3 réglementaire complet, ni liasse prête à déposer.')


def calculer(dossier):
    from services.etic_service import CATALOGUE_ETIC
    c=dossier['contenu'];periodes={}
    n2=c.get('comparatif_n2_documentaire') or {}
    provenance={'cle':n2['cle'],'source_preparation':deepcopy(n2['source_preparation']),'reference_source':n2['reference_source']} if n2 else None
    f=lambda v:None if v is None else format(v,'.2f')
    with localcontext() as ctx:
        ctx.prec=60
        for p in ('n','n1','n2'):
            rows=c.get('sources',{}).get(p) if p!='n2' else n2.get('sources_n2')
            etats=(n2.get('etats_n2') if p=='n2' else c.get('preparation',{}).get('etats' if p=='n' else 'etats_n1')) or {}
            cpc=etats.get('cpc') or {}
            v={'disponible':False,'motif':'','lignes':[],'avertissements':[],
               **{k:None for k in CHAMPS},**{'reference_'+k:None for k in CHAMPS},
               **{'ecart_'+k:None for k in CHAMPS},'effectif_moyen':None,
               'benefices_distribues':None,'resultat_par_titre':None,'distribution_par_titre':None}
            if rows is None:
                v['motif']='Source N-2 non fournie ; aucun historique du Journal repris.' if p=='n2' else 'Source détaillée absente ; aucun montant reconstitué.'
            elif not isinstance(rows,list) or any(not isinstance(r,dict) or not isinstance(r.get('compte'),str)
                    or any(r.get(k) is None or r.get(k)=='' for k in ('debit','credit')) for r in rows):
                v['motif']='Source détaillée incomplète ; aucun montant manquant remplacé par zéro.'
            else:
                soldes={}
                for r in rows:
                    compte=r['compte'];s=soldes.setdefault(compte,{'debit':Decimal(0),'credit':Decimal(0)})
                    for k in ('debit','credit'):s[k]+=montant_import(r[k],compte)
                valeurs=_calcul_c3_depuis_soldes(soldes,decimal_exact=True)
                technique=cloture_technique({'contenu':{'sources':{'n2':rows}}} if p=='n2' else dossier,p)
                activite=bool(cpc) and cpc.get('disponible') is not False and not technique
                if not activite:
                    for k in CHAMPS:
                        if k!='situation_nette':valeurs[k]=None
                    if not technique:valeurs['situation_nette']=None
                    v['avertissements'].append('Activité indisponible après solde119 ou sans CPC exploitable ; fournir la balance avant clôture technique.')
                v.update(disponible=True,**valeurs)
                for compte,s in sorted(soldes.items()):
                    if not compte.startswith(('11','13','21','281','6','7')):continue
                    crediteur=compte.startswith(('11','13','281','7'))
                    net=s['credit']-s['debit'] if crediteur else s['debit']-s['credit']
                    if net:
                        nature=('Capitaux propres/assimilés' if compte.startswith(('11','13')) else
                            'Non-valeur brute' if compte.startswith('21') else 'Amortissement groupé' if compte.startswith('281') else
                            'Charge' if compte.startswith('6') else 'Produit')
                        v['lignes'].append({'compte':compte,'nature':nature,'intitule':None,'montant':f(net)})
                def ref(valeur):
                    if valeur is None:return None
                    n=Decimal(str(valeur))
                    if not n.is_finite():raise ValueError('Référence des états conservés non finie.')
                    return n
                refs={k:ref(cpc.get(code)) if activite else None for k,code in (
                    ('resultat_avant_impots','XI'),('impots_resultats','XII'),('resultat_net','resultat_net'))}
                bilan=etats.get('bilan') or {};passif=bilan.get('passif',{});actif=bilan.get('actif',{})
                cp=passif.get('capitaux_propres')
                assim=next((r for r in passif.get('financement_permanent',[]) if r.get('code')=='131/135'),{})
                nv=next((r for r in actif.get('immobilise',[]) if r.get('code')=='21'),{})
                cp_vals=[ref(r.get('montant')) for r in cp] if cp else []
                a,n=ref(assim.get('montant')),ref(nv.get('net'))
                refs['situation_nette']=(sum(cp_vals,Decimal(0))+a-n
                    if cp_vals and all(x is not None for x in cp_vals) and a is not None and n is not None else None)
                for k,n in refs.items():
                    v['reference_'+k]=f(n)
                    v['ecart_'+k]=None if n is None or v[k] is None else f(Decimal(v[k])-n)
                    if v['ecart_'+k] is not None and Decimal(v['ecart_'+k])!=0:
                        v['avertissements'].append('Écart '+k+' avec les états figés ; à justifier sans correction automatique.')
            periodes[p]=v
    vue={'code':'C3','titre':next(r['titre'] for r in CATALOGUE_ETIC if r['code']=='C3'),
        'methode':'moteur_c3_partage_decimal_et_source_n2_v2' if n2 else 'moteur_c3_partage_decimal_et_garde119_v1',
        'note':NOTE if not n2 else NOTE.replace('N-2, effectif moyen, distributions et données par titre restent à documenter', 'N-2 rattaché explicitement et figé ; effectif moyen, distributions et données par titre restent à documenter'),
        'provenance_n2':provenance,'periodes':periodes,
        'informations_a_completer':([] if n2 else ['Source N-2'])+['Effectif moyen','Bénéfices distribués',
            'Résultat et distribution par titre','Affectations justifiées'],'pret_a_deposer':False}
    from services.balance_c3_extra_service import integrer
    return integrer(vue,dossier)


def presentation(dossier):
    bloc=dossier['contenu'].get(BLOC)
    return ({**deepcopy(bloc),'conserve':True,'pret_a_deposer':False} if bloc else
            {'conserve':False,'vue':None,'note':NOTE,'pret_a_deposer':False})


def conserver(db,user,preparation_id,data):
    demande=SimpleNamespace(empreinte_parent=data.empreinte_parent,cle=data.cle,tables=[])
    return commun.conserver(db,user,preparation_id,demande,nom_bloc=BLOC,
        normalisation=lambda d,t:[],referentiel=lambda d:[],enrichir=lambda d,q:{'vue':calculer(d)})
