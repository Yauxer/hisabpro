"""Vue courante en lecture cohérente, sans nouvelle règle de règlement."""
from decimal import Decimal,DecimalException
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import joinedload
import models
from services.tva_service import money
from services.societes_liees_service import liaison,verifier_acces
from services.factures_liees_service import disponible,suivi,valeur

TAILLE=10


def finances(db,fid,sid):
    from routers.factures import _verifier_montants_representables,_situation_paiement_facture
    f=db.query(models.Facture).options(joinedload(models.Facture.lignes)).filter_by(id=fid,societe_id=sid).first()
    if not f:raise HTTPException(404,'Pièce de correspondance introuvable.')
    cles=('total_ttc','solde_restant','total_encaisse','total_reglement_en_cours','total_avoirs','total_acomptes','montant_ras','credit_tiers')
    try:
        _verifier_montants_representables(f)
        s=_situation_paiement_facture(db,sid,f)
        valeurs={}
        for k in cles:
            if s[k] is None:raise ValueError('Montant inconnu')
            v=Decimal(str(s[k]))
            if not v.is_finite():raise ValueError('Montant non fini')
            arrondi=money(v)
            # Tolérer seulement le bruit binaire des sommes de centimes,
            # jamais arrondir silencieusement un vrai montant sous-centime.
            if abs(v-arrondi)>Decimal('0.00000001'):raise ValueError('Montant non exprimé au centime')
            valeurs[k]=format(arrondi,'.2f')
        reste=Decimal(valeurs['solde_restant']);ttc=Decimal(valeurs['total_ttc'])
        etat='Annulée — montants à rapprocher' if valeur(f.statut)=='annulee' else ('Solde couvert' if reste==0 else ('Partiellement couverte' if reste<ttc else 'À régler'))
        return {**valeurs,'etat_solde':etat,'diagnostic':None}
    except (HTTPException,ValueError,TypeError,DecimalException,OverflowError) as exc:
        if isinstance(exc,HTTPException) and exc.status_code not in (409,422):raise
        return {**dict.fromkeys(cles),'etat_solde':'À vérifier','diagnostic':'Situation financière indéterminée : vérifiez la facture et ses documents liés. Aucun montant nul n’est présumé.'}


def construire(db,user,lid,page):
    disponible(db);l=liaison(db,lid,user['societe_id'])
    verifier_acces(db,user['id'],(l['vendeur_id'],l['acheteur_id']))
    params={'id':lid,'taille':TAILLE,'offset':(page-1)*TAILLE}
    total=db.scalar(text('SELECT count(*) FROM factures_correspondantes WHERE liaison_id=:id'),params)
    rows=db.execute(text('SELECT * FROM factures_correspondantes WHERE liaison_id=:id ORDER BY id DESC LIMIT :taille OFFSET :offset'),params).mappings().all()
    items=[]
    for row in rows:
        s=suivi(db,row,user)
        s['vente']['statut']=valeur(db.get(models.Facture,row['facture_vente_id']).statut)
        s['achat']['statut']=valeur(db.get(models.Facture,row['facture_achat_id']).statut)
        s['vente']['finances']=finances(db,row['facture_vente_id'],l['vendeur_id'])
        s['achat']['finances']=finances(db,row['facture_achat_id'],l['acheteur_id'])
        items.append(s)
    return {'liaison_id':lid,'active':not bool(l['retired_at']),'page':page,'taille':TAILLE,'total':total,'items':items,
        'note':'Lecture courante des factures liées uniquement. Le solde tient compte des règlements et imputations existants ; un solde couvert ne prouve pas un encaissement. Les deux sociétés restent indépendantes.'}
