"""Préparation des bases fiscales : aucun taux légal ni frais forfaitaire inventé."""
from decimal import Decimal as D
from services.paie_social_moteur import argent,anomalie


def qualification(q,traitements):
    return q is not None and q.get('statut_reglementaire')=='VALIDE' and q.get('traitement') in traitements


def variables_fiscales(variables):
    groupes={};lignes=[]
    for v in variables:groupes.setdefault(v['rubrique_id'],[]).append(v)
    for valeurs in groupes.values():
        v=valeurs[0];r=v['regle_ir'];q=v['frais_professionnels'];erreurs=[]
        if any(x['rubrique_version_id']!=v['rubrique_version_id'] for x in valeurs):
            erreurs.append(anomalie('VERSIONS_FISCALES_MULTIPLES','Plusieurs versions de '+v['code']+' dans le mois ; régularisation à examiner.'))
        imposable=None
        if not qualification(r,{'SOUMIS','EXONERE','PLAFOND_MONTANT'}):
            erreurs.append(anomalie('IR_RUBRIQUE_NON_QUALIFIE','Traitement IR de '+v['code']+' non qualifié.'))
        elif not erreurs:
            montants=[D(x['montant']) for x in valeurs]
            if r['traitement']=='SOUMIS':imposable=sum(montants,D(0))
            elif r['traitement']=='EXONERE':imposable=D(0)
            elif r['unite']=='operation':imposable=sum((max(D(0),m-D(r['plafond'])) for m in montants),D(0))
            elif r['unite']=='mensuel':imposable=max(D(0),sum(montants,D(0))-D(r['plafond']))
            else:erreurs.append(anomalie('CUMUL_FISCAL_MANQUANT','Plafond '+r['unite']+' de '+v['code']+' : faits de cumul ou de jours non disponibles.'))
        frais=None
        if not qualification(q,{'INCLUS','EXCLUS'}):erreurs.append(anomalie('BASE_FRAIS_NON_QUALIFIEE','Qualification des frais professionnels de '+v['code']+' manquante ou obsolète.'))
        elif imposable is not None:frais=imposable if q['traitement']=='INCLUS' else D(0)
        lignes.append({'code':v['code'],'rubrique_id':v['rubrique_id'],'rubrique_version_id':v['rubrique_version_id'],'variable_ids':[x['id'] for x in valeurs],
          'imposable':None if imposable is None else argent(imposable),'base_frais':None if frais is None else argent(frais),'anomalies':erreurs})
    return lignes


def calculer(base_brut,declaration,variables,branches):
    erreurs=[];rbg=declaration.base_imposable;frais=declaration.base_frais
    if not declaration.conditions_confirmees or not declaration.reference_controle:
        erreurs.append(anomalie('CONDITIONS_FISCALES_NON_CONFIRMEES','Confirmer les parts de base, les conditions fiscales et leur référence de contrôle.'))
    if rbg is None:erreurs.append(anomalie('BASE_IR_INCONNUE','Part imposable de la base salariale non déclarée.'))
    if frais is None:erreurs.append(anomalie('BASE_FRAIS_INCONNUE','Part de base salariale éligible aux frais professionnels non déclarée.'))
    if base_brut is None or rbg is not None and rbg>D(base_brut) or frais is not None and rbg is not None and frais>rbg:
        erreurs.append(anomalie('BASE_FISCALE_INCOHERENTE','Base imposable supérieure à la base salariale ou base des frais supérieure à la base imposable.'))
    bases_coherentes=base_brut is not None and rbg is not None and rbg<=D(base_brut) and (frais is None or frais<=rbg)
    conditions=declaration.conditions_confirmees and bool(declaration.reference_controle)
    lignes=variables_fiscales(variables)
    def somme(k):return sum((D(x[k]) for x in lignes),D(0)) if all(x[k] is not None for x in lignes) else None
    vr=somme('imposable');vf=somme('base_frais')
    rbg=rbg+vr if rbg is not None and vr is not None and bases_coherentes and conditions else None
    frais=frais+vf if frais is not None and vf is not None and bases_coherentes and conditions else None
    retenues=[]
    for b in branches:
        q=b['deductibilite_ir'];montant=b['salarial'];err=[];ded=None;non=None
        if not conditions:err.append(anomalie('CONDITIONS_COTISATION_NON_CONFIRMEES','Conditions fiscales et référence de contrôle des cotisations à confirmer.'))
        if montant is None:err.append(anomalie('COTISATION_INCONNUE','Part salariale de '+b['code']+' indisponible.'))
        if not qualification(q,{'DEDUCTIBLE','NON_DEDUCTIBLE'}):err.append(anomalie('DEDUCTIBILITE_NON_QUALIFIEE','Déductibilité IR de '+b['code']+' non qualifiée.'))
        elif q['traitement']=='DEDUCTIBLE' and not declaration.deductibilite_integrale_confirmee:
            err.append(anomalie('DEDUCTION_INTEGRALE_NON_CONFIRMEE','Confirmer que la part salariale de '+b['code']+' est intégralement déductible pour ce salarié ; plafonds partiels et conditions spécifiques non traités automatiquement.'))
        if not err:
            ded=D(montant) if q['traitement']=='DEDUCTIBLE' else D(0)
            non=D(montant) if q['traitement']=='NON_DEDUCTIBLE' else D(0)
        retenues.append({**b,'deductible':None if ded is None else argent(ded),'non_deductible':None if non is None else argent(non),'anomalies':err})
    if not retenues:erreurs.append(anomalie('COTISATIONS_ABSENTES','Aucune ligne sociale source ; aucun zéro déductible présumé.'))
    def cotisations(k):return sum((D(x[k]) for x in retenues),D(0)) if retenues and all(x[k] is not None for x in retenues) else None
    ded=cotisations('deductible');non=cotisations('non_deductible');avant=None
    if rbg is not None and ded is not None:
        if ded>rbg:erreurs.append(anomalie('DEDUCTION_SUPERIEURE_REVENU','Cotisations déductibles supérieures au revenu imposable ; aucun revenu négatif corrigé artificiellement.'))
        else:avant=rbg-ded
    for x in lignes+retenues:erreurs.extend(x['anomalies'])
    m=lambda x:None if x is None else argent(x)
    return {'brut_imposable':m(rbg),'base_frais_professionnels':m(frais),'cotisations_salariales_deductibles':m(ded),
      'cotisations_salariales_non_deductibles':m(non),'revenu_avant_frais_autres_deductions':m(avant),
      'variables':lignes,'cotisations':retenues,'anomalies':erreurs,'frais_professionnels':None,'revenu_net_imposable':None,'ir':None,'net_a_payer':None}
