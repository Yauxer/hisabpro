"""Captures explicites, SQL isolé du metadata et du bootstrap de développement."""
from decimal import Decimal
import math
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
import models


def disponible(db):
    # SQLite sert uniquement aux anciens calculs unitaires ; aucun DDL implicite.
    if not hasattr(db, 'get_bind'):
        return False  # doubles de calcul unitaires sans connexion SQL
    if db.get_bind().dialect.name != 'postgresql':
        return False
    if 'ras_capture_disponible' not in db.info:
        db.info['ras_capture_disponible'] = bool(db.execute(text("SELECT to_regclass('public.ras_reglement_captures') IS NOT NULL AND to_regclass('public.ras_reglement_annulations') IS NOT NULL")).scalar())
    return db.info['ras_capture_disponible']


def captures_facture(db, sid, fid):
    if not disponible(db):
        return []
    return [dict(r) for r in db.execute(text('''SELECT c.*, a.id AS annulation_id,
        a.ecriture_id AS ecriture_annulation_id, e.est_validee AS ecriture_est_validee,
        e.numero_ecriture, ae.est_validee AS annulation_est_validee,
        ae.numero_ecriture AS numero_ecriture_annulation FROM public.ras_reglement_captures c
        LEFT JOIN public.ras_reglement_annulations a ON a.capture_id=c.id
        JOIN public.ecritures e ON e.id=c.ecriture_id AND e.societe_id=c.societe_id
        LEFT JOIN public.ecritures ae ON ae.id=a.ecriture_id AND ae.societe_id=c.societe_id
        WHERE c.societe_id=:sid AND c.facture_id=:fid ORDER BY c.id'''), {'sid': sid, 'fid': fid}).mappings()]


def montant_actif(db, sid, fid):
    total = sum((Decimal(str(c['montant'])) for c in captures_facture(db, sid, fid) if c['annulation_id'] is None), Decimal(0))
    if not total.is_finite():
        return None
    montant = float(total)
    return montant if math.isfinite(montant) else None


def proteger_ecriture_capture(db, sid, eid):
    if disponible(db) and db.execute(text('''SELECT EXISTS(
        SELECT 1 FROM public.ras_reglement_captures WHERE societe_id=:sid AND ecriture_id=:eid
        UNION ALL SELECT 1 FROM public.ras_reglement_annulations WHERE societe_id=:sid AND ecriture_id=:eid)'''),
        {'sid':sid,'eid':eid}).scalar():
        raise HTTPException(409, 'Écriture liée à une capture RAS : utilisez l’annulation du règlement associé')


def annuler_capture(db, sid, reglement, jour, acteur, motif, exercice):
    if not disponible(db):
        return
    # L'appelant détient déjà le verrou du règlement, également pris à la
    # création d'une capture. Le registre est immuable : le lire ne doit pas
    # exiger un droit UPDATE que le rôle applicatif ne possède pas.
    row = db.execute(text('''SELECT c.* FROM public.ras_reglement_captures c
        LEFT JOIN public.ras_reglement_annulations a ON a.capture_id=c.id
        WHERE c.societe_id=:sid AND c.reglement_id=:rid AND a.id IS NULL'''),
        {'sid': sid, 'rid': reglement.id}).mappings().first()
    if row is None:
        return
    if jour < row['date_operation']:
        raise HTTPException(422,'La date d’annulation ne peut pas précéder la capture RAS associée')
    original = db.query(models.Ecriture).options(joinedload(models.Ecriture.lignes)).filter_by(id=row['ecriture_id'], societe_id=sid).first()
    if original is None or db.query(models.Ecriture.id).filter_by(societe_id=sid, contrepassation_de_id=original.id).first():
        raise HTTPException(409, 'Écriture de capture RAS absente ou déjà contrepassée : annulation indéterminable')
    inverse = models.Ecriture(societe_id=sid, journal='OD', date=jour, date_piece=jour,
        exercice=exercice, reference=('ANN-RAS-' + str(row['id']))[:100],
        libelle=f"Annulation capture RAS {row['id']}", source='ras_reglement',
        contrepassation_de_id=original.id, motif_correction=motif,
        lignes=[models.LigneEcriture(compte=l.compte, libelle=l.libelle, debit=l.credit, credit=l.debit,
            tiers_id=l.tiers_id, nature_auxiliaire=l.nature_auxiliaire,
            compte_auxiliaire_snapshot=l.compte_auxiliaire_snapshot,
            libelle_auxiliaire_snapshot=l.libelle_auxiliaire_snapshot) for l in original.lignes])
    db.add(inverse); db.flush()
    db.execute(text('''INSERT INTO public.ras_reglement_annulations
        (capture_id,societe_id,ecriture_id,date_operation,motif,created_by)
        VALUES(:cid,:sid,:eid,:jour,:motif,:acteur)'''),
        {'cid': row['id'], 'sid': sid, 'eid': inverse.id, 'jour': jour, 'motif': motif, 'acteur': acteur})
