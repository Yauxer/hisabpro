"""Bases fiscales reliées aux snapshots brut/social, sans retenue mensuelle."""
from calendar import monthrange
from datetime import date
from decimal import Decimal
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from services import personnel_workflow_service as w,paie_campagnes_service as brut,paie_social_calcul_service as social
from services.paie_catalogue_schemas import Contenu as Rubrique
from services.paie_social_schemas import Contenu as Branche
from services.paie_bases_fiscales_schemas import Declaration as DeclarationFiscale
from services.paie_social_calcul_schemas import Declaration as DeclarationSociale
from services.paie_bases_fiscales_moteur import calculer
from services.paie_social_moteur import argent,anomalie


def autoriser(db,user,action=None):
    ctx=social.autoriser(db,user,action)
    if not db.scalar(text("SELECT to_regclass('public.paie_preparations_fiscales') IS NOT NULL AND to_regprocedure('public.hisabpro_paie_qualification_ir119()') IS NOT NULL")):
        raise HTTPException(503,'Installer les migrations 119 et 120 des qualifications et bases fiscales.')
    return ctx


def normaliser_branches(lignes):
    return [{**x,'contenu':Branche.model_validate(x['contenu']).model_dump(mode='json') if x['contenu'] else None} for x in lignes]


def preparer_salarie(db,user,ctx,e,gross,declaration,branches_courantes,branches_sources,debut,fin,branches_changees):
    erreurs=[]
    actuel=social.calcul_salarie(db,user,ctx,gross,DeclarationSociale.model_validate(e['declaration']),branches_courantes,debut,fin)
    if brut.empreinte(actuel)!=brut.empreinte(e) or branches_changees:
        erreurs.append(anomalie('SOURCE_SOCIALE_CHANGEE','Sources courantes différentes du calcul social ; préparer de nouveaux snapshots brut/social sans modifier l’historique.'))
    if e['anomalies'] or e['salarial'] is None:erreurs.append(anomalie('SOCIAL_INCOMPLET','Calcul social source incomplet.'))
    variables=[]
    for v in gross['variables']:
        row=db.execute(text("SELECT * FROM paie_variables WHERE id=:i AND societe_id=:s AND employe_id=:e AND statut='APPROUVE'"),{'i':v['id'],'s':user['societe_id'],'e':e['employe_id']}).mappings().first()
        if not row:erreurs.append(anomalie('VARIABLE_FISCALE_ABSENTE','Variable source approuvée introuvable.'));continue
        try:c=Rubrique.model_validate(row['instantane']['rubrique'])
        except (ValidationError,KeyError):erreurs.append(anomalie('REGLE_FISCALE_INVALIDE','Qualification fiscale source non interprétable.'));continue
        variables.append({'id':row['id'],'code':v['code'],'montant':format(row['montant'],'.2f'),'rubrique_id':row['rubrique_id'],
          'rubrique_version_id':row['rubrique_version_id'],'regle_ir':c.regles.IR.model_dump(mode='json'),
          'frais_professionnels':None if c.frais_professionnels is None else c.frais_professionnels.model_dump(mode='json')})
    regles={b['branche_id']:b for b in branches_sources}
    branches=[{'branche_id':b['branche_id'],'version_id':b['version_id'],'code':b['code'],'salarial':b['salarial'],
      'deductibilite_ir':regles[b['branche_id']]['contenu'].get('deductibilite_ir') if regles[b['branche_id']]['contenu'] else None} for b in e['branches']]
    r=calculer(gross['base'],declaration,variables,branches)
    if erreurs:
        for k in ['brut_imposable','base_frais_professionnels','cotisations_salariales_deductibles','cotisations_salariales_non_deductibles','revenu_avant_frais_autres_deductions']:r[k]=None
        r['anomalies']=erreurs+r['anomalies']
    return {'employe_id':e['employe_id'],'nom':e['nom'],'matricule':e['matricule'],'brut':e['brut'],
      'declaration':declaration.model_dump(mode='json'),'variables_sources':variables,**r}


def sortie(row,user,ctx,reutilise=False):return brut.sortie(row,user,ctx,reutilise)


@w.transaction
def simuler(db,user,data):
    ctx=autoriser(db,user,'proposer');sid=user['societe_id'];demande=brut.empreinte(data.model_dump(mode='json',exclude={'cle_idempotence'}))
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:bases-fiscales:{sid}:{data.social_id}'})
    ancien=db.execute(text('SELECT * FROM paie_preparations_fiscales WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Clé de reprise déjà utilisée pour une autre préparation fiscale.')
        return sortie(ancien,user,ctx,True)
    source=social.lire(db,user,data.social_id);c=source['contenu'];gross=brut.lire(db,user,c['brut_id'])
    debut=date.fromisoformat(c['periode']);fin=debut.replace(day=monthrange(debut.year,debut.month)[1])
    if debut.year!=2026:raise HTTPException(400,'Cadre fiscal préparé pour 2026 uniquement ; autres millésimes à qualifier.')
    declarations={d.employe_id:d for d in data.declarations}
    if set(declarations)!={e['employe_id'] for e in c['employes']}:raise HTTPException(400,'Déclarer exactement tous les salariés du snapshot social.')
    courantes=social.charger_branches(db,sid,c['regime'],debut,fin)
    try:changees=brut.empreinte(normaliser_branches(courantes))!=brut.empreinte(normaliser_branches(c['branches_sources']))
    except ValidationError:changees=True
    if gross['empreinte']!=c['brut_empreinte']:raise HTTPException(409,'Lien entre les snapshots brut et social incohérent.')
    employes={e['employe_id']:e for e in gross['contenu']['employes']}
    if set(employes)!=set(declarations):raise HTTPException(409,'Sélection brute et sociale incohérente.')
    lignes=[preparer_salarie(db,user,ctx,e,employes[e['employe_id']],declarations[e['employe_id']],courantes,c['branches_sources'],debut,fin,changees) for e in c['employes']]
    def total(k):return argent(sum((Decimal(e[k]) for e in lignes),Decimal(0))) if all(e[k] is not None for e in lignes) else None
    contenu={'mode':'PREPARATION_BASES_FISCALES_NON_VALIDEE','statut_reglementaire':'NON_VALIDE_JURIDIQUEMENT','paie_definitive_autorisee':False,
      'periode':c['periode'],'social_id':source['id'],'social_empreinte':source['empreinte'],'brut_id':gross['id'],'brut_empreinte':gross['empreinte'],
      'branches_sources':c['branches_sources'],'employes':lignes,'complet_pour_bases':all(not e['anomalies'] for e in lignes),
      'totaux':{**{k:total(k) for k in ['brut_imposable','base_frais_professionnels','cotisations_salariales_deductibles','cotisations_salariales_non_deductibles','revenu_avant_frais_autres_deductions']},
        'frais_professionnels':None,'revenu_net_imposable':None,'ir':None,'net_a_payer':None},
      'avertissement':'Préparation des bases avant frais professionnels et autres déductions. Les montants intermédiaires ne sont pas un RNI définitif. Aucun taux de frais, retenue mensuelle, arrondi fiscal, net, bulletin, paiement ou écriture. Sources contrôlées au calcul ; historique conservé sans recalcul à la consultation.'}
    numero=db.scalar(text('SELECT coalesce(max(numero),0)+1 FROM paie_preparations_fiscales WHERE social_id=:i'),{'i':source['id']})
    ident=db.scalar(text('INSERT INTO paie_preparations_fiscales(societe_id,social_id,numero,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:i,:n,:k,:d,CAST(:c AS jsonb),:h,:u,:m) RETURNING id'),
      {'s':sid,'i':source['id'],'n':numero,'k':str(data.cle_idempotence),'d':demande,'c':brut.canonique(contenu),'h':brut.empreinte(contenu),'u':user['id'],'m':data.motif})
    return sortie(db.execute(text('SELECT * FROM paie_preparations_fiscales WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid}).mappings().one(),user,ctx)


def lire(db,user,ident):
    ctx=autoriser(db,user);r=db.execute(text('SELECT * FROM paie_preparations_fiscales WHERE id=:i AND societe_id=:s'),{'i':ident,'s':user['societe_id']}).mappings().first()
    if not r:raise HTTPException(404,'Préparation fiscale introuvable dans cette société.')
    return sortie(r,user,ctx)


def lister(db,user,decalage,limite):
    autoriser(db,user);p={'s':user['societe_id'],'o':decalage,'l':limite}
    return {'total':db.scalar(text('SELECT count(*) FROM paie_preparations_fiscales WHERE societe_id=:s'),p),
      'elements':[dict(r) for r in db.execute(text("SELECT id,social_id,numero,cree_at,contenu->>'periode' AS periode,contenu->>'complet_pour_bases' AS complet,contenu#>>'{totaux,brut_imposable}' AS brut_imposable FROM paie_preparations_fiscales WHERE societe_id=:s ORDER BY id DESC OFFSET :o LIMIT :l"),p).mappings()]}


def options(db,user,ident):
    autoriser(db,user);source=social.lire(db,user,ident)
    return {'social':source,'brut':brut.lire(db,user,source['contenu']['brut_id'])}


def verifier_sources_salarie(db,user,ctx,source,employe_id):
    """Vérifie une préparation conservée sans la modifier ni en créer une autre."""
    c=source['contenu'];e=next((e for e in c['employes'] if e['employe_id']==employe_id),None)
    if e is None:raise HTTPException(404,'Salarié absent de cette préparation fiscale.')
    s=social.lire(db,user,c['social_id']);g=brut.lire(db,user,c['brut_id'])
    if (s['empreinte'],g['empreinte'])!=(c['social_empreinte'],c['brut_empreinte']):raise HTTPException(409,'Liens des sources fiscales incohérents.')
    debut=date.fromisoformat(c['periode']);fin=debut.replace(day=monthrange(debut.year,debut.month)[1])
    branches=social.charger_branches(db,user['societe_id'],s['contenu']['regime'],debut,fin)
    try:changees=brut.empreinte(normaliser_branches(branches))!=brut.empreinte(normaliser_branches(s['contenu']['branches_sources']))
    except ValidationError:changees=True
    es=next((x for x in s['contenu']['employes'] if x['employe_id']==employe_id),None)
    eg=next((x for x in g['contenu']['employes'] if x['employe_id']==employe_id),None)
    if es is None or eg is None:raise HTTPException(409,'Sélection des sources fiscales incohérente.')
    actuel=preparer_salarie(db,user,ctx,es,eg,DeclarationFiscale.model_validate(e['declaration']),branches,s['contenu']['branches_sources'],debut,fin,changees)
    if brut.empreinte(actuel)!=brut.empreinte(e):raise HTTPException(409,'Sources de la préparation fiscale modifiées ; recalculer le brut, le social et les bases avant le cumul.')
    return e
