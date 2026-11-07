"""Arithmétique sociale déclarative ; aucune règle légale ou valeur par défaut."""
from decimal import Decimal,ROUND_HALF_UP

D=Decimal
def argent(v):return format(v.quantize(D('.01'),rounding=ROUND_HALF_UP),'.2f')
def anomalie(code,message):return {'code':code,'message':message}


def assiettes(base,brut,variables):
    """Variables complètes du mois ; plafonds mensuels par rubrique et salarié.

    Chaque variable fournit le contenu de rubrique conservé lors de sa saisie.
    Les unités annuelle/journalière exigent d'autres faits et restent inconnues.
    Les conditions d'éligibilité sont confirmées séparément par le déclarant.
    """
    result={'BRUT':{'montant':brut,'anomalies':[]}}
    for regime in ['CNSS','AMO']:
        erreurs=[];total=base[regime];groupes={}
        if total is None:erreurs.append(anomalie('BASE_INCONNUE','Part de la base salariale soumise à '+regime+' non déclarée.'))
        for v in variables:
            r=v['regles'][regime];m=D(v['montant']);traitement=r['traitement']
            if r['statut_reglementaire']=='OBSOLETE' or traitement=='A_VERIFIER':
                erreurs.append(anomalie('RUBRIQUE_A_QUALIFIER','Traitement '+regime+' de '+v['code']+' inconnu ou obsolète.'));continue
            if traitement=='SOUMIS':
                if total is not None:total+=m
            elif traitement=='EXONERE':pass
            elif traitement=='PLAFOND_MONTANT':
                if r['unite']=='operation':
                    if total is not None:total+=m-min(m,D(r['plafond']))
                elif r['unite']=='mensuel':
                    cle=v['rubrique_id'];g=groupes.setdefault(cle,{'version':v['rubrique_version_id'],'montant':D(0),'plafond':D(r['plafond'])})
                    if g['version']!=v['rubrique_version_id']:erreurs.append(anomalie('RUBRIQUE_CHANGE_DANS_MOIS','Plusieurs versions de '+v['code']+' pour un plafond mensuel ; régularisation à examiner.'))
                    g['montant']+=m
                else:erreurs.append(anomalie('CUMUL_NON_DISPONIBLE','Plafond '+r['unite']+' de '+v['code']+' : cumul ou nombre de jours non disponible.'))
            else:erreurs.append(anomalie('TRAITEMENT_INCONNU','Traitement de rubrique non calculable.'))
        for g in groupes.values():
            if total is not None:total+=g['montant']-min(g['montant'],g['plafond'])
        result[regime]={'montant':None if erreurs else total,'anomalies':erreurs}
    return result


def branche(c,bases):
    r={'assiette_avant_plafond':None,'assiette_retenue':None,'salarial':None,'patronal':None,'anomalies':[]}
    def bloquer(code,message):r['anomalies'].append(anomalie(code,message));return r
    if c['statut_reglementaire']=='OBSOLETE':return bloquer('BRANCHE_OBSOLETE','Règle de branche obsolète ; nouvelle qualification requise.')
    if c['applicabilite']=='A_VERIFIER':return bloquer('APPLICABILITE_INCONNUE','Applicabilité de la branche non qualifiée.')
    if c['applicabilite']=='NON_APPLICABLE':r.update(salarial='0.00',patronal='0.00');return r
    if c['calcul_mode']=='FORFAIT':
        for k in ['salarial','patronal']:
            if c['forfait_'+k] is None:r['anomalies'].append(anomalie('FORFAIT_INCONNU','Forfait '+k+' non déclaré.'))
            else:r[k]=argent(D(c['forfait_'+k]))
        return r
    if c['calcul_mode']!='TAUX':return bloquer('MODE_INCONNU','Mode de calcul à qualifier.')
    base=bases.get(c['assiette'])
    if base is None or base['montant'] is None:
        if base:r['anomalies'].extend(base['anomalies'])
        return bloquer('ASSIETTE_INCONNUE','Assiette de branche non disponible ; aucun brut de substitution.')
    m=base['montant'];r['assiette_avant_plafond']=argent(m)
    if c['plafond_mode']=='A_VERIFIER':return bloquer('PLAFOND_INCONNU','Plafonnement à qualifier.')
    if c['plafond_mode']=='MONTANT':
        if c['unite']!='mensuel':return bloquer('UNITE_NON_CALCULABLE','Plafond '+c['unite']+' : aucun prorata mensuel implicite.')
        m=min(m,D(c['plafond']))
    r['assiette_retenue']=argent(m)
    for k in ['salarial','patronal']:
        if c['taux_'+k] is None:r['anomalies'].append(anomalie('TAUX_INCONNU','Taux '+k+' non déclaré.'))
        else:r[k]=argent(m*D(c['taux_'+k])/D(100))
    return r
