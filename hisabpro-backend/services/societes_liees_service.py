"""Relations explicitement déclarées, accès effectifs dans chaque société."""
from fastapi import HTTPException
from sqlalchemy import text
import models


def schema_disponible(db):
    if not db.scalar(text("SELECT to_regclass('public.societes_liees') IS NOT NULL AND to_regclass('public.societes_liees_retraits') IS NOT NULL")):
        raise HTTPException(503, 'Les sociétés liées nécessitent la migration explicite101.')


def role_societe(db, uid, sid):
    u=db.query(models.Utilisateur).filter_by(id=uid).populate_existing().first()
    if not u or not u.actif:return None
    if u.societe_id==sid:return u.role if u.role in {'admin','comptable','lecture'} else None
    l=db.query(models.UtilisateurSociete).filter_by(utilisateur_id=uid,societe_id=sid,actif=True).populate_existing().first()
    return l.role if l and l.role in {'admin','comptable','lecture'} else None


def verifier_acces(db, uid, sids, roles=('admin','comptable','lecture')):
    if any(role_societe(db,uid,s) not in roles for s in sids):
        raise HTTPException(403, 'Droits insuffisants dans les deux sociétés.')


def liaison(db, lid, courant):
    schema_disponible(db)
    l=db.execute(text('SELECT l.*,r.motif AS motif_retrait,r.created_at AS retired_at FROM societes_liees l LEFT JOIN societes_liees_retraits r ON r.liaison_id=l.id WHERE l.id=:id AND (l.vendeur_id=:sid OR l.acheteur_id=:sid)'),{'id':lid,'sid':courant}).mappings().first()
    if not l:raise HTTPException(404,'Liaison introuvable.')
    return dict(l)


def verifier_tiers(db, vendeur, acheteur, client, fournisseur):
    v=db.get(models.Societe,vendeur);a=db.get(models.Societe,acheteur)
    c=db.query(models.Tiers).filter_by(id=client,societe_id=vendeur,actif=True).first()
    f=db.query(models.Tiers).filter_by(id=fournisseur,societe_id=acheteur,actif=True).first()
    if not c or c.type not in {'client','les_deux'} or not f or f.type not in {'fournisseur','les_deux'}:
        raise HTTPException(422,'Choisissez un client actif du vendeur et un fournisseur actif de l’acheteur.')
    for tiers,societe in ((c,a),(f,v)):
        if tiers.ice and societe.ice and tiers.ice.strip()!=societe.ice.strip():
            raise HTTPException(422,'L’ICE du tiers ne correspond pas à celui de la société associée.')
    return c,f


def sortie(db,l):
    d=dict(l)
    for champ in ('vendeur_id','acheteur_id'):
        s=db.get(models.Societe,l[champ]);d[champ.replace('_id','')]=s.raison_sociale
    d['client']=db.get(models.Tiers,l['client_id']).nom
    d['fournisseur']=db.get(models.Tiers,l['fournisseur_id']).nom
    d['active']=not bool(d.get('retired_at'))
    d['cle']=str(d['cle'])
    return d
