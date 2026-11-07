"""Liens bancaires explicites de lots natifs, sans réécrire les écritures."""
from datetime import datetime
from decimal import Decimal,InvalidOperation
import re
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy import text
import models

def active(db):
    return db.get_bind().dialect.name=='postgresql' and bool(db.execute(
        text("SELECT to_regclass('rapprochement_ventilations')")).scalar())

def verrou(db,sid):
    if db.get_bind().dialect.name=='postgresql':
        db.execute(text('SELECT pg_advisory_xact_lock(726883,:sid)'),{'sid':sid})

def affectations(db,sid):
    if not active(db):return []
    return db.execute(text('SELECT releve_id,ecriture_ligne_id,operation_id FROM rapprochement_ventilations WHERE societe_id=:sid ORDER BY ecriture_ligne_id'),{'sid':sid}).mappings().all()

def montant(value):
    try:
        n=Decimal(str(value))
        if not n.is_finite() or n<0 or n!=n.quantize(Decimal('0.01')):raise ValueError()
        return n
    except (InvalidOperation,ValueError,TypeError):
        raise HTTPException(409,'Montant bancaire inconnu ou invalide : rapprochement bloqué.')

def natif(db,sid,operation,compte):
    prefix='VT-'+UUID(str(operation)).hex+'-'
    rows=db.query(models.Reglement).filter(models.Reglement.societe_id==sid,
        models.Reglement.numero.startswith(prefix)).order_by(models.Reglement.numero).all()
    if not rows:raise HTTPException(404,'Ventilation introuvable pour cette société.')
    if not 2<=len(rows)<=50 or any(r.numero!=f'{prefix}{i:02d}' for i,r in enumerate(rows,1)):
        raise HTTPException(409,'Le lot natif doit être entier et comporter de2à50règlements.')
    premier=rows[0]
    if premier.tiers_id is None or len({r.facture_id for r in rows})!=len(rows):
        raise HTTPException(409,'Liens tiers/factures du lot incomplets ou ambigus.')
    lignes=[];types=set();eids=set();sens=None
    for r in rows:
        if (r.tiers_id,r.date,r.mode,r.banque,r.reference)!=(premier.tiers_id,premier.date,premier.mode,premier.banque,premier.reference) or r.mode not in {'virement','carte','prelevement','autre'} or r.statut!='complet' or not r.est_comptabilisee:
            raise HTTPException(409,'Une ventilation bancaire immédiate, cohérente et non annulée est requise.')
        f=db.query(models.Facture).filter_by(id=r.facture_id,societe_id=sid).first()
        e=db.query(models.Ecriture).filter_by(id=r.ecriture_id,societe_id=sid).first()
        if f is None or f.tiers_id!=premier.tiers_id or e is None or e.id in eids or not e.est_validee or not e.numero_ecriture or e.source!='reglement' or e.date!=r.date:
            raise HTTPException(409,'Chaque règlement doit conserver une écriture native définitive distincte.')
        eids.add(e.id);types.add(f.type)
        banque=[l for l in e.lignes if l.compte==compte]
        if len(banque)!=1:raise HTTPException(409,'Compte bancaire absent ou ambigu dans une écriture du lot.')
        l=banque[0];d,c=montant(l.debit),montant(l.credit);m=montant(r.montant)
        actuel='credit' if d>0 and c==0 else 'debit' if c>0 and d==0 else None
        if actuel is None or d+c!=m or m<=0 or (sens is not None and sens!=actuel):
            raise HTTPException(409,'Montants ou sens bancaires incohérents dans le lot.')
        sens=actuel;lignes.append((l,e))
    if len(types)!=1 or ('vente' in types)!=(sens=='credit'):
        raise HTTPException(409,'Cycle achat/vente incohérent dans le lot.')
    return {'operation_id':str(UUID(str(operation))),'date':premier.date.isoformat(),
        'reference':premier.reference,'tiers':premier.tiers,'sens':sens,
        'montant':float(sum((montant(r.montant) for r in rows),Decimal(0))),
        'ecriture_ligne_ids':sorted(l.id for l,e in lignes),'nb_reglements':len(rows)},lignes

def candidats(db,sid,compte,debut,fin):
    if not active(db):return []
    numeros=db.query(models.Reglement.numero).filter(models.Reglement.societe_id==sid,
        models.Reglement.date>=debut,models.Reglement.date<=fin,models.Reglement.numero.like('VT-%')).all()
    ids={m[1] for (n,) in numeros if (m:=re.fullmatch(r'VT-([a-f0-9]{32})-\d{2}',n or ''))}
    result=[]
    for ident in sorted(ids):
        try:data,_=natif(db,sid,ident,compte)
        except HTTPException:continue
        result.append(data)
    return result

def deja_pointees(db,sid,ids,releve_id):
    simple=db.query(models.RapprochementLigne.id).filter(models.RapprochementLigne.societe_id==sid,
        models.RapprochementLigne.rapprochee.is_(True),models.RapprochementLigne.ecriture_ligne_id.in_(ids),
        models.RapprochementLigne.id!=releve_id).first()
    groupe=any(a['ecriture_ligne_id'] in ids and a['releve_id']!=releve_id for a in affectations(db,sid))
    if simple or groupe:raise HTTPException(409,'Une ligne comptable du lot est déjà rapprochée avec un autre relevé.')

def depointer(db,sid,releve):
    from routers.rapprochement import _assert_date_modifiable,_ligne_comptable
    for a in affectations(db,sid):
        if a['releve_id']==releve.id:
            _,e=_ligne_comptable(db,sid,a['ecriture_ligne_id']);_assert_date_modifiable(db,sid,e.date)
    if active(db):
        db.execute(text('DELETE FROM rapprochement_ventilations WHERE societe_id=:sid AND releve_id=:rid'),{'sid':sid,'rid':releve.id})

def rapprocher(db,sid,releve,operation,acteur):
    from routers.rapprochement import _assert_date_modifiable
    if not active(db):raise HTTPException(503,'Le rapprochement des ventilations n’est pas activé sur cette installation.')
    data,lignes=natif(db,sid,operation,releve.compte)
    _assert_date_modifiable(db,sid,releve.date)
    for l,e in lignes:_assert_date_modifiable(db,sid,e.date)
    if montant(releve.montant)!=Decimal(str(data['montant'])) or releve.sens!=data['sens']:
        raise HTTPException(409,'Montant total ou sens du relevé incompatible avec la ventilation.')
    existants=[a for a in affectations(db,sid) if a['releve_id']==releve.id]
    if existants:
        if sorted(a['ecriture_ligne_id'] for a in existants)==data['ecriture_ligne_ids'] and all(str(a['operation_id'])==data['operation_id'] for a in existants) and releve.rapprochee:
            return data
        raise HTTPException(409,'Dérapprochez la ventilation actuelle avant de la remplacer.')
    if releve.rapprochee or releve.ecriture_ligne_id:
        raise HTTPException(409,'Dérapprochez la ligne avant de choisir une ventilation.')
    deja_pointees(db,sid,data['ecriture_ligne_ids'],releve.id)
    for lid in data['ecriture_ligne_ids']:
        db.execute(text('INSERT INTO rapprochement_ventilations(releve_id,ecriture_ligne_id,societe_id,operation_id) VALUES(:rid,:lid,:sid,CAST(:operation AS UUID))'),
            {'rid':releve.id,'lid':lid,'sid':sid,'operation':data['operation_id']})
    releve.rapprochee=True;releve.reglement_id=None;releve.ecriture_ligne_id=None
    releve.date_rapprochement=datetime.utcnow();releve.rapproche_par=acteur
    db.flush()
    return data
