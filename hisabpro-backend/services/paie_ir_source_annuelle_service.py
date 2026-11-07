"""IR annuel sur un RNI constitué ; origine et précision conservées."""
from copy import deepcopy
from decimal import Decimal,ROUND_CEILING,InvalidOperation
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text
from services import personnel_workflow_service as w,paie_ir_annuel_service as annuel,paie_frais_annuels_service as frais,paie_campagnes_service as brut
from services.paie_ir_annuel_schemas import Simulation
from services.paie_ir_annuel_moteur import calculer,REFERENTIEL


def arrondir_source(valeur):
    if not isinstance(valeur,(str,Decimal)):raise ValueError('RNI source décimal exact requis.')
    try:
        montant=Decimal(valeur)
        if not montant.is_finite() or montant<0 or montant.quantize(Decimal('.0001'))!=montant:raise ValueError('RNI source incohérent.')
        unite=Decimal(REFERENTIEL['arrondi_base_annuelle']['unite'])
        return format((montant/unite).to_integral_value(rounding=ROUND_CEILING)*unite,'.2f')
    except InvalidOperation as e:raise ValueError('RNI source hors précision autorisée.') from e


@w.transaction
def simuler(db,user,data):
    ctx=frais.autoriser(db,user,'proposer');sid=user['societe_id']
    if not db.scalar(text("SELECT to_regclass('public.paie_ir_sources_annuelles') IS NOT NULL")):raise HTTPException(503,'Installer la migration 122 de liaison IR annuel.')
    demande=brut.empreinte({'origine':'FRAIS_ANNUELS','donnees':data.model_dump(mode='json',exclude={'cle_idempotence'})})
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'),{'c':f'hisabpro:paie:ir:annuel:{sid}'})
    ancien=db.execute(text('SELECT * FROM paie_controles_ir_annuels WHERE societe_id=:s AND cle_idempotence=:k'),{'s':sid,'k':str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['demande_sha256']!=demande:raise HTTPException(409,'Clé de reprise déjà utilisée pour une autre demande.')
        return annuel.sortie(db,ancien,user,ctx,True)
    source=frais.lire(db,user,data.frais_annuels_id);c=source['contenu']
    if not c['complet_pour_rni_arithmetique'] or c['rni_annuel_arithmetique_avant_arrondis'] is None:raise HTTPException(409,'Compléter le contrôle des frais et les autres déductions avant de contrôler l’IR.')
    frais.verifier_sources_courantes(db,user,ctx,source)
    try:
        base=arrondir_source(c['rni_annuel_arithmetique_avant_arrondis'])
        d=Simulation.model_validate({'annee':c['annee'],'revenu_net_imposable_annuel':base,'personnes_charge':data.personnes_charge,
            'cadre_general_confirme':data.cadre_general_confirme and data.source_annuelle_confirmee,'eligibilite_famille_confirmee':data.eligibilite_famille_confirmee,
            'reference_rni':f'Frais annuels #{source["id"]}, empreinte {source["empreinte"]}','reference_famille':data.reference_famille,
            'mode_pedagogique_confirme':True,'cle_idempotence':data.cle_idempotence,'motif':data.motif})
    except (ValueError,ValidationError) as e:raise HTTPException(409,'RNI source hors du périmètre du contrôleur annuel ; aucune réduction de précision implicite.') from e
    contenu=calculer(d)
    contenu['source_frais_annuels']={'id':source['id'],'empreinte':source['empreinte'],'employe_id':c['employe_id'],'nom':c['nom'],'matricule':c['matricule'],'annee':c['annee'],
        'rni_avant_arrondis':c['rni_annuel_arithmetique_avant_arrondis'],'base_annuelle_utilisee':base,'regle_arrondi':deepcopy(REFERENTIEL['arrondi_base_annuelle']),
        'source_annuelle_confirmee':data.source_annuelle_confirmee,'reference_controle_annuel':c['declaration']['reference_controle_annuel']}
    contenu['avertissement']='Contrôle annuel sur RNI issu des frais annuels, arrondi à la dizaine supérieure avant le barème. Le RNI source et la base utilisée sont conservés séparément. Aucune retenue mensuelle, imputation, somme à déclarer ou verser, net ou paie définitive.'
    ident=db.scalar(text('INSERT INTO paie_controles_ir_annuels(societe_id,annee,cle_idempotence,demande_sha256,contenu,empreinte,auteur_id,motif) VALUES(:s,:a,:k,:d,CAST(:c AS jsonb),:h,:u,:m) RETURNING id'),
        {'s':sid,'a':c['annee'],'k':str(data.cle_idempotence),'d':demande,'c':brut.canonique(contenu),'h':brut.empreinte(contenu),'u':user['id'],'m':data.motif})
    db.execute(text('INSERT INTO paie_ir_sources_annuelles(ir_id,societe_id,frais_annuels_id,auteur_id) VALUES(:i,:s,:f,:u)'),{'i':ident,'s':sid,'f':source['id'],'u':user['id']})
    return annuel.sortie(db,db.execute(text('SELECT * FROM paie_controles_ir_annuels WHERE id=:i AND societe_id=:s'),{'i':ident,'s':sid}).mappings().one(),user,ctx)
