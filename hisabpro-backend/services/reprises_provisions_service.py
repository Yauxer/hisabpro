"""Reprises explicites, liées à une dotation ; aucun solde global imputé par défaut."""
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import HTTPException
from sqlalchemy import text
import models
from services.cloture_service import construire_ajustement
from services.exercices_service import trouver_exercice_pour_date
from services.plan_comptable import libelle_compte

TYPES = ('provision_risque', 'depreciation_client', 'depreciation_stock')
NOTE = ('Capacité du registre lié uniquement : les mouvements manuels sans lien ne sont pas imputés. '
        'Vérifiez le compte et les justificatifs avant création. Aucune déductibilité fiscale ni disparition du risque n’est présumée.')


def montant_exact(v):
    try:
        if isinstance(v, bool) or v is None:
            raise ValueError
        d = Decimal(str(v))
        if not d.is_finite() or not 0 < d < Decimal('10000000000000000') or d != d.quantize(Decimal('.01')):
            raise ValueError
        return d.quantize(Decimal('.01'))
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError('Montant positif fini attendu, sur 16 chiffres et 2 décimales au maximum.') from None


class RepriseIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: date
    montant: Decimal
    justification: str = Field(min_length=1, max_length=500)
    reference: str | None = Field(default=None, max_length=100)
    date_piece: date | None = None

    @field_validator('montant', mode='before')
    @classmethod
    def montant_valide(cls, v):
        return montant_exact(v)

    @field_validator('justification')
    @classmethod
    def justification_valide(cls, v):
        if not v.strip():
            raise ValueError('Justification obligatoire.')
        return v.strip()


class CreationIn(RepriseIn):
    cle: UUID
    empreinte: str = Field(pattern=r'^[a-f0-9]{64}$')
    mouvements_verifies: bool = Field(strict=True)


class AnnulationIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    date: date
    motif: str = Field(min_length=1, max_length=500)

    @field_validator('motif')
    @classmethod
    def motif_valide(cls, v):
        if not v.strip():
            raise ValueError('Motif obligatoire.')
        return v.strip()


def compte_reprise(type_, activite):
    """CGNC OEC, rubriques 15/39/45. Nature inconnue : aucun choix automatique."""
    if type_ == 'provision_risque':
        for prefixe, produit in [('6195', '7195'), ('6393', '7393'), ('6595', '7595')]:
            if activite.startswith(prefixe):
                return produit
    if type_ == 'depreciation_client':
        if activite == '6196' or activite.startswith('61964'):
            return '7196'
        if activite.startswith('6596'):
            return '7596'
    if type_ == 'depreciation_stock' and (activite == '6196' or activite.startswith('61961')):
        return '7196'
    raise ValueError('Nature de dotation non qualifiée pour ce type : aucune reprise automatique proposée.')


def disponible(db):
    if not hasattr(db, 'get_bind') or db.get_bind().dialect.name != 'postgresql':
        return False
    return bool(db.scalar(text("SELECT to_regclass('public.reprises_provisions') IS NOT NULL AND to_regclass('public.reprises_provisions_annulations') IS NOT NULL")))


def exiger_registre(db):
    if not disponible(db):
        raise HTTPException(503, 'Reprises indisponibles : migration additive 100 à installer séparément.')


def proteger_ecriture(db, sid, eid):
    if disponible(db) and db.scalar(text('''SELECT EXISTS(
        SELECT 1 FROM reprises_provisions r JOIN ajustements_inventaire a ON a.id=r.ajustement_id
        WHERE r.societe_id=:s AND (r.ecriture_id=:e OR a.ecriture_id=:e)
        UNION ALL SELECT 1 FROM reprises_provisions_annulations WHERE societe_id=:s AND ecriture_id=:e)'''), {'s':sid,'e':eid}):
        raise HTTPException(409, 'Pièce liée à une reprise de provision : utilisez le suivi des reprises dans Clôture.')


def verifier_validation(db, sid, eid):
    if disponible(db) and db.scalar(text('''SELECT EXISTS(
        SELECT 1 FROM reprises_provisions_annulations n
        JOIN reprises_provisions r ON r.id=n.reprise_id
        JOIN ecritures original ON original.id=r.ecriture_id
        WHERE n.societe_id=:s AND n.ecriture_id=:e AND NOT original.est_validee)'''), {'s':sid,'e':eid}):
        raise HTTPException(409, 'Validez la reprise d’origine avant son inverse, ou sélectionnez les deux dans le lot.')


def source(db, sid, aid, verrou=False):
    a = db.query(models.AjustementInventaire).filter_by(id=aid, societe_id=sid).first()
    if not a or a.type not in TYPES:
        raise HTTPException(404, 'Dotation de provision introuvable.')
    q = db.query(models.Ecriture).filter_by(id=a.ecriture_id, societe_id=sid).populate_existing()
    e = (q.with_for_update() if verrou else q).first()
    if not e:
        raise HTTPException(409, 'Pièce source absente : vérification historique nécessaire.')
    return a, e


def qualifier(db, sid, a, e):
    if not e.est_validee or not e.numero_ecriture:
        raise ValueError('La dotation source doit être validée dans le Journal.')
    if db.query(models.Ecriture.id).filter_by(societe_id=sid, contrepassation_de_id=e.id).first():
        raise ValueError('La dotation source possède une contrepassation : vérification historique nécessaire.')
    attendues, _, _ = construire_ajustement(a.type, a.montant, a.compte_activite, a.compte_contrepartie)
    forme = lambda ls: sorted((l['compte'], Decimal(str(l['debit'])), Decimal(str(l['credit']))) for l in ls)
    reelles = [{'compte':l.compte,'debit':l.debit,'credit':l.credit} for l in e.lignes]
    if e.exercice != a.exercice or forme(attendues) != forme(reelles):
        raise ValueError('La pièce réelle ne recoupe pas la dotation : aucune réparation implicite.')
    return compte_reprise(a.type, a.compte_activite)


def registre(db, sid, aid):
    rows = db.execute(text('''SELECT r.id,r.ecriture_id,r.montant,r.faits,r.cle,
        e.est_validee,e.numero_ecriture,e.date,e.exercice,
        n.id AS annulation_id,n.ecriture_id AS inverse_id,n.motif,
        i.est_validee AS inverse_validee,i.numero_ecriture AS inverse_numero,i.date AS inverse_date,i.exercice AS inverse_exercice
        FROM reprises_provisions r JOIN ecritures e ON e.id=r.ecriture_id AND e.societe_id=r.societe_id
        LEFT JOIN reprises_provisions_annulations n ON n.reprise_id=r.id AND n.societe_id=r.societe_id
        LEFT JOIN ecritures i ON i.id=n.ecriture_id AND i.societe_id=n.societe_id
        WHERE r.societe_id=:s AND r.ajustement_id=:a ORDER BY r.id DESC'''), {'s':sid,'a':aid}).mappings().all()
    return [dict(r) for r in rows]


def capacite(initial, rows):
    initial = montant_exact(initial)
    valide = brouillon = Decimal('0.00')
    for r in rows:
        # Une annulation en brouillon ne libère jamais la capacité.
        if r['annulation_id'] and r['est_validee'] and r['inverse_validee']:
            continue
        if r['est_validee']:
            valide += montant_exact(r['montant'])
        else:
            brouillon += montant_exact(r['montant'])
    return {'dotation':format(initial,'.2f'), 'reprises_validees':format(valide,'.2f'),
            'reservations_brouillons':format(brouillon,'.2f'), 'disponible':format(initial-valide-brouillon,'.2f')}


def capacite_a_date(initial, rows, jour):
    """Marge minimale à partir du jour demandé, réservations futures comprises."""
    mouvements = {}
    for r in rows:
        m = montant_exact(r['montant'])
        mouvements[r['date']] = mouvements.get(r['date'],Decimal(0)) + m
        if r['annulation_id'] and r['est_validee'] and r['inverse_validee']:
            d = r['inverse_date']
            mouvements[d] = mouvements.get(d,Decimal(0)) - m
    consomme = sum((m for d,m in mouvements.items() if d<=jour),Decimal(0))
    maximum = consomme
    for d in sorted(d for d in mouvements if d>jour):
        consomme += mouvements[d]
        maximum = max(maximum,consomme)
    return montant_exact(initial) - maximum


def lecture_source(db, sid, aid):
    a = db.query(models.AjustementInventaire).filter_by(id=aid, societe_id=sid).first()
    if not a or a.type not in TYPES:
        raise HTTPException(404, 'Dotation de provision introuvable.')
    e = db.query(models.Ecriture).filter_by(id=a.ecriture_id, societe_id=sid).first()
    try:
        if e is None:
            raise ValueError('Pièce source absente : vérification historique nécessaire.')
        produit = qualifier(db,sid,a,e); diagnostic = None
    except (ValueError, InvalidOperation) as exc:
        produit = None; diagnostic = str(exc)
    rows = registre(db,sid,aid)
    try:
        cap = capacite(a.montant,rows)
    except ValueError:
        cap = dict.fromkeys(('dotation','reprises_validees','reservations_brouillons','disponible'))
        diagnostic = 'Montant historique inexploitable : capacité à vérifier, aucune reprise proposée.'
        produit = None
    return {'id':a.id,'type':a.type,'libelle':a.libelle,'exercice':a.exercice,'ecriture_id':e.id if e else a.ecriture_id,
        'date':e.date.isoformat() if e else None,'numero':e.numero_ecriture if e else None,'compte_provision':a.compte_contrepartie,
        'compte_dotation':a.compte_activite,'compte_reprise':produit,'diagnostic':diagnostic,
        **cap, 'reprises':[{**r,'montant':format(r['montant'],'.2f')} for r in rows], 'note':NOTE}


def periode(db, sid, jour):
    ex = trouver_exercice_pour_date(db,sid,jour,creer_si_absent=False)
    if not ex:
        raise HTTPException(404,'Aucun calendrier préparé pour cette date de reprise.')
    p = db.query(models.PeriodeComptable).filter(models.PeriodeComptable.exercice_id==ex.id,
        models.PeriodeComptable.date_debut<=jour,models.PeriodeComptable.date_fin>=jour).first()
    if ex.statut=='cloture' or db.query(models.ClotureExercice.id).filter_by(societe_id=sid,exercice=ex.annee).first() or not p or p.statut!='ouverte':
        raise HTTPException(423,'La date de reprise doit appartenir à une période comptable ouverte.')
    return ex


def faits(data):
    return RepriseIn.model_validate(data.model_dump(include=set(RepriseIn.model_fields))).model_dump(mode='json')


def preparer(db,sid,aid,data,verrou=False):
    exiger_registre(db)
    a,e = source(db,sid,aid,verrou)
    try:
        produit = qualifier(db,sid,a,e)
    except (ValueError, InvalidOperation) as exc:
        raise HTTPException(409,str(exc)) from exc
    if data.date < e.date:
        raise HTTPException(422,'La reprise ne peut pas précéder la dotation source.')
    ex = periode(db,sid,data.date)
    rows = registre(db,sid,aid)
    cap = capacite(a.montant,rows)
    disponible_date = capacite_a_date(a.montant,rows,data.date)
    cap['disponible_pour_date'] = format(disponible_date,'.2f')
    if data.montant > disponible_date:
        raise HTTPException(409,'Montant supérieur à la capacité à cette date, compte tenu des reprises déjà réservées et des annulations validées.')
    doc = {'source_id':aid,'source_ecriture_id':e.id,'societe_id':sid,'exercice':ex.annee,
        'compte_provision':a.compte_contrepartie,'compte_reprise':produit,'capacite':cap,'faits':faits(data),
        'note':NOTE,'version':'CGNC-reprises-615',
        'lignes':[{'compte':a.compte_contrepartie,'debit':format(data.montant,'.2f'),'credit':'0.00'},
                  {'compte':produit,'debit':'0.00','credit':format(data.montant,'.2f')}]}
    for ligne in doc['lignes']:
        ligne['libelle_compte'] = libelle_compte(ligne['compte'],db,sid)
    doc['empreinte'] = hashlib.sha256(json.dumps(doc,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    return doc
