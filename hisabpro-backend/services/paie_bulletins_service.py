"""Bulletins de paie figés, avances/prêts, comptabilisation, paiements et états (lot 968).

Chaque bulletin assemble des snapshots déjà conservés : brut simulé, cotisations
calculées avec les taux déclarés dans le référentiel social, contrôle IR mensuel.
L'IR retenu et les retenues d'avances sont déclarés et contrôlés ; aucun taux
légal n'est supposé ici. Les écritures produites restent des brouillons à
valider dans le Journal.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from uuid import UUID
from typing import Literal
from fastapi import HTTPException
from pydantic import Field, field_validator
from sqlalchemy import text
import models
from services import (paie_campagnes_service as brut, paie_social_calcul_service as social,
                      paie_ir_mensuel_service as mensuel, personnel_workflow_service as w)
from services.paie_catalogue_schemas import Base
from services.personnel_dossiers_service import montant_exact
from services.tresorerie_service import verifier_sortie as verifier_sortie_caisse

D = Decimal
ZERO = D('0.00')
COMPTES = {'brut': '6171', 'patronal': '6174', 'organismes': '4441', 'ir': '44525',
           'avances': '3431', 'net': '4432'}
# Salarié actif : dossier Personnel protégé « ACTIF », sinon fiche historique active.
ACTIF = "(d.statut='ACTIF' OR (d.employe_id IS NULL AND e.actif))"
TRESORERIE = {'virement': ('BQ', '5141'), 'cheque': ('BQ', '5141'), 'especes': ('CA', '5161')}
AVERTISSEMENT = ('Bulletin établi à partir des taux, plafonds et déductions déclarés dans HisabPro. '
                 'Vérifier les paramètres légaux en vigueur (CNSS, AMO, IR) avant remise au salarié.')


def argent(v):
    return D(v).quantize(D('0.01'), rounding=ROUND_HALF_UP)


def texte(v):
    return format(argent(v), '.2f')


# ── Schémas ─────────────────────────────────────────────────────────────────

class Retenue(Base):
    avance_id: int = Field(strict=True, gt=0)
    montant: Decimal

    @field_validator('montant', mode='before')
    @classmethod
    def m(cls, v):
        return montant_exact(v)


class Creation(Base):
    controle_id: int = Field(strict=True, gt=0)
    ir_retenu: Decimal
    reference_ecart_ir: str | None = Field(default=None, min_length=1, max_length=300)
    retenues_avances: list[Retenue] = Field(default_factory=list, max_length=20)
    cle_idempotence: UUID
    motif: str = Field(min_length=1, max_length=500)

    @field_validator('ir_retenu', mode='before')
    @classmethod
    def ir(cls, v):
        return montant_exact(v)


class Annulation(Base):
    motif: str = Field(min_length=1, max_length=500)


class Comptabilisation(Base):
    periode: date
    date_ecriture: date


class Paiement(Base):
    bulletin_ids: list[int] = Field(min_length=1, max_length=200)
    date_paiement: date
    mode: Literal['virement', 'cheque', 'especes']
    reference: str | None = Field(default=None, min_length=1, max_length=100)


class Avance(Base):
    employe_id: int = Field(strict=True, gt=0)
    nature: Literal['AVANCE', 'PRET']
    date_octroi: date
    montant: Decimal
    retenue_mensuelle: Decimal | None = None
    mode_versement: Literal['virement', 'cheque', 'especes']
    motif: str = Field(min_length=1, max_length=500)

    @field_validator('montant', 'retenue_mensuelle', mode='before')
    @classmethod
    def m(cls, v):
        return None if v is None else montant_exact(v)


# ── Accès ───────────────────────────────────────────────────────────────────

def autoriser(db, user, action=None):
    ctx = mensuel.autoriser(db, user, action)
    if not db.scalar(text("SELECT to_regclass('public.paie_bulletins') IS NOT NULL AND to_regclass('public.paie_avances') IS NOT NULL")):
        raise HTTPException(503, 'Installer la migration 131 des bulletins et avances de paie.')
    return ctx


def exiger_comptable(user):
    if user['role'] not in {'admin', 'comptable'}:
        raise HTTPException(403, 'La comptabilisation et le paiement de la paie sont réservés aux profils admin et comptable.')


def verrou(db, sid):
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:c,0))'), {'c': f'hisabpro:paie:bulletins:{sid}'})


# ── Avances et prêts ────────────────────────────────────────────────────────

def soldes_avances(db, sid, employe_id=None, exclure_bulletin=None):
    """Solde restant de chaque avance active : montant - retenues des bulletins valides."""
    rows = db.execute(text('''
        SELECT a.*, p.nom AS nom_employe,
               coalesce((SELECT sum((r->>'montant')::numeric) FROM paie_bulletins b
                          CROSS JOIN LATERAL jsonb_array_elements(b.contenu->'retenues_avances') r
                          WHERE b.societe_id=a.societe_id AND b.statut='VALIDE' AND r->>'avance_id'=a.id::text
                            AND (CAST(:x AS bigint) IS NULL OR b.id<>CAST(:x AS bigint))),0) AS rembourse,
               e.est_validee AS ecriture_validee
        FROM paie_avances a JOIN employes p ON p.id=a.employe_id AND p.societe_id=a.societe_id
        LEFT JOIN ecritures e ON e.id=a.ecriture_id
        WHERE a.societe_id=:s AND (CAST(:e AS integer) IS NULL OR a.employe_id=CAST(:e AS integer))
        ORDER BY a.date_octroi DESC, a.id DESC'''), {'s': sid, 'e': employe_id, 'x': exclure_bulletin}).mappings().all()
    sortie = []
    for r in rows:
        d = dict(r)
        d['rembourse'] = argent(d['rembourse'])
        d['solde'] = argent(d['montant'] - d['rembourse']) if d['statut'] == 'ACTIVE' else ZERO
        sortie.append(d)
    return sortie


def salaries(db, user):
    autoriser(db, user)
    return [dict(x) for x in db.execute(text('SELECT e.id,e.nom,coalesce(e.matricule,d.matricule_cle) AS matricule FROM employes e '
                                             'LEFT JOIN personnel_dossiers d ON d.employe_id=e.id AND d.societe_id=e.societe_id '
                                             'WHERE e.societe_id=:s AND ' + ACTIF + ' ORDER BY e.nom,e.id'),
                                        {'s': user['societe_id']}).mappings()]


def lister_avances(db, user):
    autoriser(db, user)
    return {'elements': soldes_avances(db, user['societe_id'])}


@w.transaction
def creer_avance(db, user, data):
    autoriser(db, user, 'proposer')
    sid = user['societe_id']
    if data.retenue_mensuelle is not None and data.retenue_mensuelle > data.montant:
        raise HTTPException(400, 'La retenue mensuelle ne peut pas dépasser le montant accordé.')
    if not db.scalar(text('SELECT EXISTS(SELECT 1 FROM employes e LEFT JOIN personnel_dossiers d ON d.employe_id=e.id AND d.societe_id=e.societe_id '
                          'WHERE e.id=:e AND e.societe_id=:s AND ' + ACTIF + ')'), {'e': data.employe_id, 's': sid}):
        raise HTTPException(404, 'Salarié actif introuvable dans cette société.')
    ident = db.scalar(text('''INSERT INTO paie_avances(societe_id,employe_id,nature,date_octroi,montant,retenue_mensuelle,mode_versement,motif,auteur_id)
        VALUES(:s,:e,:n,:d,:m,:r,:v,:mo,:u) RETURNING id'''),
        {'s': sid, 'e': data.employe_id, 'n': data.nature, 'd': data.date_octroi, 'm': data.montant,
         'r': data.retenue_mensuelle, 'v': data.mode_versement, 'mo': data.motif, 'u': user['id']})
    return {'id': ident}


@w.transaction
def annuler_avance(db, user, ident, data):
    autoriser(db, user, 'proposer')
    sid = user['societe_id']
    a = db.execute(text('SELECT * FROM paie_avances WHERE id=:i AND societe_id=:s FOR UPDATE'), {'i': ident, 's': sid}).mappings().first()
    if not a:
        raise HTTPException(404, 'Avance introuvable dans cette société.')
    if a['statut'] != 'ACTIVE':
        raise HTTPException(409, 'Cette avance est déjà annulée.')
    if a['ecriture_id']:
        raise HTTPException(409, "Supprimer d'abord le brouillon de versement dans le Journal (ou contrepasser l'écriture validée).")
    db.execute(text("UPDATE paie_avances SET statut='ANNULEE',annule_par=:u,annule_at=:t,motif_annulation=:m WHERE id=:i AND societe_id=:s"),
               {'u': user['id'], 't': datetime.now(), 'm': data.motif, 'i': ident, 's': sid})
    return {'id': ident, 'statut': 'ANNULEE'}


@w.transaction
def comptabiliser_avance(db, user, ident):
    exiger_comptable(user)
    autoriser(db, user)
    sid = user['societe_id']
    a = db.execute(text('SELECT a.*,p.nom FROM paie_avances a JOIN employes p ON p.id=a.employe_id AND p.societe_id=a.societe_id '
                        'WHERE a.id=:i AND a.societe_id=:s FOR UPDATE OF a'), {'i': ident, 's': sid}).mappings().first()
    if not a:
        raise HTTPException(404, 'Avance introuvable dans cette société.')
    if a['statut'] != 'ACTIVE':
        raise HTTPException(409, 'Avance annulée : rien à comptabiliser.')
    if a['ecriture_id']:
        raise HTTPException(409, 'Le versement de cette avance est déjà comptabilisé.')
    journal, tresorerie = TRESORERIE[a['mode_versement']]
    verifier_sortie_caisse(db, sid, tresorerie, a['montant'], a['date_octroi'])  # lot 977
    libelle = f"{'Prêt' if a['nature'] == 'PRET' else 'Avance'} au personnel — {a['nom']}"
    e = ecrire(db, user, a['date_octroi'], journal, libelle, f'AV-{a["id"]}',
               [(COMPTES['avances'], libelle, a['montant'], ZERO), (tresorerie, libelle, ZERO, a['montant'])])
    db.execute(text('UPDATE paie_avances SET ecriture_id=:e WHERE id=:i AND societe_id=:s'), {'e': e, 'i': ident, 's': sid})
    return {'id': ident, 'ecriture_id': e}


# ── Calcul du bulletin ──────────────────────────────────────────────────────

def ir_arrondi(controle):
    f = (controle.get('fractions_exactes') or {}).get('ir_apres_reduction')
    if not f:
        return None
    valeur = Fraction(int(f['numerateur']), int(f['denominateur']))
    return argent(D(valeur.numerator) / D(valeur.denominator))


def assembler(db, user, controle_id, exclure_bulletin=None):
    """Lit et vérifie les snapshots sources (empreintes) ; renvoie les éléments du bulletin."""
    ctrl = mensuel.lire(db, user, controle_id)
    c = ctrl['contenu']
    if c.get('anomalies') or c.get('ir_mensuel_arithmetique') is None:
        raise HTTPException(409, "Contrôle IR incomplet : traiter ses anomalies avant d'établir le bulletin.")
    src = c['source_preparation']
    soc = social.lire(db, user, src['social_id'])
    gross = brut.lire(db, user, src['brut_id'])
    if soc['empreinte'] != src['social_empreinte'] or gross['empreinte'] != src['brut_empreinte']:
        raise HTTPException(409, 'Provenance du contrôle IR incohérente avec les simulations sources.')
    eid = ctrl['employe_id']
    ligne_brut = next((e for e in gross['contenu']['employes'] if e['employe_id'] == eid), None)
    ligne_soc = next((e for e in soc['contenu']['employes'] if e['employe_id'] == eid), None)
    if not ligne_brut or not ligne_soc or ligne_brut['brut'] is None:
        raise HTTPException(409, 'Salarié absent ou incomplet dans les simulations sources.')
    if ligne_soc['anomalies'] or ligne_soc['salarial'] is None or ligne_soc['patronal'] is None:
        raise HTTPException(409, 'Cotisations sociales incomplètes : compléter la simulation sociale.')
    gains = [{'libelle': 'Salaire de base', 'montant': texte(ligne_brut['base'])}]
    gains += [{'libelle': v['code'], 'montant': texte(v['montant'])} for v in ligne_brut['variables'] if v['nature'] == 'GAIN']
    cotisations = [{'code': b['code'], 'assiette': b['assiette_retenue'], 'salarial': b['salarial'], 'patronal': b['patronal']}
                   for b in ligne_soc['branches']]
    return {
        'controle': ctrl, 'employe_id': eid, 'nom': c['nom'], 'matricule': c['matricule'], 'periode': c['periode'],
        'gains': gains, 'brut': texte(ligne_brut['brut']), 'cotisations': cotisations,
        'cotisations_salariales': texte(ligne_soc['salarial']), 'cotisations_patronales': texte(ligne_soc['patronal']),
        'brut_imposable': c['bases_sources']['brut_imposable'],
        'frais_professionnels': c['declaration'].get('frais_professionnels_declares'),
        'rni': c['rni_arithmetique'], 'ir_arithmetique': c['ir_mensuel_arithmetique'], 'ir_propose': texte(ir_arrondi(c)),
        'avances': [{'id': a['id'], 'nature': a['nature'], 'solde': texte(a['solde']),
                     'retenue_mensuelle': None if a['retenue_mensuelle'] is None else texte(a['retenue_mensuelle'])}
                    for a in soldes_avances(db, user['societe_id'], eid, exclure_bulletin) if a['statut'] == 'ACTIVE' and a['solde'] > 0],
        'sources': {'controle': {'id': ctrl['id'], 'empreinte': ctrl['empreinte']},
                    'social': {'id': soc['id'], 'empreinte': soc['empreinte']},
                    'brut': {'id': gross['id'], 'empreinte': gross['empreinte']}},
    }


def apercu(db, user, controle_id):
    autoriser(db, user)
    a = assembler(db, user, controle_id)
    a.pop('controle')
    a['deja_etabli'] = db.scalar(text("SELECT id FROM paie_bulletins WHERE societe_id=:s AND employe_id=:e AND periode=:p AND statut='VALIDE'"),
                                 {'s': user['societe_id'], 'e': a['employe_id'], 'p': a['periode']})
    return a


def sortie(row):
    r = dict(row)
    if brut.empreinte(r['contenu']) != r['empreinte']:
        raise HTTPException(409, 'Empreinte du bulletin incohérente : ne pas utiliser ce bulletin.')
    r.pop('cle_idempotence', None)
    return r


@w.transaction
def creer(db, user, data):
    autoriser(db, user, 'proposer')
    sid = user['societe_id']
    verrou(db, sid)
    ancien = db.execute(text('SELECT * FROM paie_bulletins WHERE societe_id=:s AND cle_idempotence=:k'),
                        {'s': sid, 'k': str(data.cle_idempotence)}).mappings().first()
    if ancien:
        if ancien['controle_id'] != data.controle_id:
            raise HTTPException(409, 'Clé de reprise utilisée pour un autre bulletin.')
        return {**sortie(ancien), 'reutilise': True}
    a = assembler(db, user, data.controle_id)
    if db.scalar(text("SELECT EXISTS(SELECT 1 FROM paie_bulletins WHERE societe_id=:s AND employe_id=:e AND periode=:p AND statut='VALIDE')"),
                 {'s': sid, 'e': a['employe_id'], 'p': a['periode']}):
        raise HTTPException(409, 'Un bulletin valide existe déjà pour ce salarié et ce mois : annuler-le avant de le refaire.')
    propose = D(a['ir_propose'])
    if data.ir_retenu != propose and not data.reference_ecart_ir:
        raise HTTPException(400, f"IR retenu différent du calcul ({a['ir_propose']} MAD) : indiquer la référence justifiant l'écart.")
    disponibles = {x['id']: D(x['solde']) for x in a['avances']}
    retenues = []
    for r in data.retenues_avances:
        if r.montant <= 0:
            continue
        if r.avance_id not in disponibles:
            raise HTTPException(409, f'Avance #{r.avance_id} introuvable, soldée ou d’un autre salarié.')
        if r.montant > disponibles[r.avance_id]:
            raise HTTPException(409, f'Retenue sur l’avance #{r.avance_id} supérieure à son solde ({texte(disponibles[r.avance_id])} MAD).')
        disponibles[r.avance_id] -= r.montant
        retenues.append({'avance_id': r.avance_id, 'montant': texte(r.montant)})
    total_avances = sum((D(r['montant']) for r in retenues), ZERO)
    net = D(a['brut']) - D(a['cotisations_salariales']) - data.ir_retenu - total_avances
    if net < 0:
        raise HTTPException(409, 'Net à payer négatif : réduire les retenues déclarées.')
    contenu = {
        'mode': 'BULLETIN_968', 'avertissement': AVERTISSEMENT,
        'employe_id': a['employe_id'], 'nom': a['nom'], 'matricule': a['matricule'], 'periode': a['periode'],
        'gains': a['gains'], 'brut': a['brut'], 'cotisations': a['cotisations'],
        'cotisations_salariales': a['cotisations_salariales'], 'cotisations_patronales': a['cotisations_patronales'],
        'brut_imposable': a['brut_imposable'], 'frais_professionnels': a['frais_professionnels'], 'rni': a['rni'],
        'ir_arithmetique': a['ir_arithmetique'], 'ir_propose': a['ir_propose'], 'ir_retenu': texte(data.ir_retenu),
        'reference_ecart_ir': data.reference_ecart_ir if data.ir_retenu != propose else None,
        'retenues_avances': retenues, 'total_avances': texte(total_avances),
        'net_a_payer': texte(net), 'cout_employeur': texte(D(a['brut']) + D(a['cotisations_patronales'])),
        'sources': a['sources'],
    }
    ident = db.scalar(text('''INSERT INTO paie_bulletins(societe_id,employe_id,periode,controle_id,cle_idempotence,contenu,empreinte,net_a_payer,auteur_id,motif)
        VALUES(:s,:e,:p,:c,:k,CAST(:j AS jsonb),:h,:n,:u,:m) RETURNING id'''),
        {'s': sid, 'e': a['employe_id'], 'p': a['periode'], 'c': data.controle_id, 'k': str(data.cle_idempotence),
         'j': brut.canonique(contenu), 'h': brut.empreinte(contenu), 'n': net, 'u': user['id'], 'm': data.motif})
    row = db.execute(text('SELECT * FROM paie_bulletins WHERE id=:i'), {'i': ident}).mappings().one()
    return {**sortie(row), 'reutilise': False}


ETAT_SQL = '''SELECT b.id,b.employe_id,b.periode,b.statut,b.net_a_payer,b.cree_at,b.ecriture_id,b.paiement_ecriture_id,b.paiement_date,b.paiement_mode,
    b.motif_annulation,b.contenu->>'nom' AS nom,b.contenu->>'matricule' AS matricule,b.contenu->>'brut' AS brut,
    b.contenu->>'cotisations_salariales' AS cotisations_salariales,b.contenu->>'cotisations_patronales' AS cotisations_patronales,
    b.contenu->>'ir_retenu' AS ir_retenu,b.contenu->>'total_avances' AS total_avances,b.contenu->>'cout_employeur' AS cout_employeur,
    e.est_validee AS ecriture_validee,e.numero_ecriture,pe.est_validee AS paiement_valide
    FROM paie_bulletins b LEFT JOIN ecritures e ON e.id=b.ecriture_id LEFT JOIN ecritures pe ON pe.id=b.paiement_ecriture_id
    WHERE b.societe_id=:s'''


def lister(db, user, periode=None, annee=None):
    autoriser(db, user)
    sql = ETAT_SQL + ' AND (CAST(:p AS date) IS NULL OR b.periode=CAST(:p AS date)) AND (CAST(:a AS integer) IS NULL OR extract(year FROM b.periode)=CAST(:a AS integer)) ORDER BY b.periode DESC,b.contenu->>\'nom\',b.id DESC'
    return {'elements': [dict(x) for x in db.execute(text(sql), {'s': user['societe_id'], 'p': periode, 'a': annee}).mappings()]}


def lire(db, user, ident):
    autoriser(db, user)
    r = db.execute(text('SELECT b.*,s.raison_sociale,s.identifiant_fiscal,s.ice,s.cnss_numero AS cnss_societe,s.adresse,s.ville FROM paie_bulletins b JOIN societes s ON s.id=b.societe_id '
                        'WHERE b.id=:i AND b.societe_id=:s'), {'i': ident, 's': user['societe_id']}).mappings().first()
    if not r:
        raise HTTPException(404, 'Bulletin introuvable dans cette société.')
    out = sortie({k: v for k, v in r.items() if k not in {'raison_sociale', 'identifiant_fiscal', 'ice', 'cnss_societe', 'adresse', 'ville'}})
    out['societe'] = {k: r[k] for k in ('raison_sociale', 'identifiant_fiscal', 'ice', 'cnss_societe', 'adresse', 'ville')}
    emp = db.execute(text('SELECT * FROM employes WHERE id=:e AND societe_id=:s'), {'e': r['employe_id'], 's': user['societe_id']}).mappings().first()
    out['salarie'] = {k: (emp or {}).get(k) for k in ('poste', 'numero_cnss', 'date_embauche')}
    return out


@w.transaction
def annuler(db, user, ident, data):
    autoriser(db, user, 'proposer')
    sid = user['societe_id']
    verrou(db, sid)
    b = db.execute(text('SELECT * FROM paie_bulletins WHERE id=:i AND societe_id=:s FOR UPDATE'), {'i': ident, 's': sid}).mappings().first()
    if not b:
        raise HTTPException(404, 'Bulletin introuvable dans cette société.')
    if b['statut'] != 'VALIDE':
        raise HTTPException(409, 'Ce bulletin est déjà annulé.')
    if b['paiement_ecriture_id'] or b['paiement_date']:
        raise HTTPException(409, 'Bulletin payé : supprimer le brouillon de paiement ou contrepasser le paiement avant annulation.')
    if b['ecriture_id']:
        raise HTTPException(409, "Bulletin comptabilisé : supprimer le brouillon de paie du mois dans le Journal (ou le contrepasser) avant annulation.")
    db.execute(text("UPDATE paie_bulletins SET statut='ANNULE',annule_par=:u,annule_at=:t,motif_annulation=:m WHERE id=:i AND societe_id=:s"),
               {'u': user['id'], 't': datetime.now(), 'm': data.motif, 'i': ident, 's': sid})
    return {'id': ident, 'statut': 'ANNULE'}


# ── Écritures ───────────────────────────────────────────────────────────────

def ecrire(db, user, jour, journal, libelle, reference, lignes):
    """Brouillon équilibré ; mêmes contrôles que la saisie manuelle du Journal."""
    from routers.ecritures import _verifier_periode_ouverte, _verifier_comptes_plan, _set_audit_context
    from services.auxiliaire_service import rattacher_ligne_auxiliaire

    class L:
        def __init__(self, compte, debit, credit):
            self.compte, self.debit, self.credit = compte, debit, credit
    lignes = [l for l in lignes if l[2] > 0 or l[3] > 0]
    if sum(l[2] for l in lignes) != sum(l[3] for l in lignes):
        raise HTTPException(409, 'Écriture de paie déséquilibrée : vérifier les bulletins.')
    exercice = _verifier_periode_ouverte(db, user['societe_id'], jour, 'créer')
    _verifier_comptes_plan(db, user['societe_id'], [L(c, d, k) for c, _, d, k in lignes])
    _set_audit_context(db, user, 'creation_paie')
    e = models.Ecriture(societe_id=user['societe_id'], est_validee=False, date=jour, date_piece=jour, journal=journal,
                        libelle=libelle, reference=reference, exercice=exercice.annee if exercice else jour.year, source='paie')
    db.add(e)
    db.flush()
    for compte, lib, debit, credit in lignes:
        ligne = models.LigneEcriture(ecriture_id=e.id, compte=compte, libelle=lib[:255], debit=debit, credit=credit)
        rattacher_ligne_auxiliaire(db, user['societe_id'], ligne, tiers_id=None)
        db.add(ligne)
    db.flush()
    return e.id


@w.transaction
def comptabiliser(db, user, data):
    exiger_comptable(user)
    autoriser(db, user)
    sid = user['societe_id']
    verrou(db, sid)
    periode = data.periode.replace(day=1)
    rows = db.execute(text("SELECT * FROM paie_bulletins WHERE societe_id=:s AND periode=:p AND statut='VALIDE' AND ecriture_id IS NULL ORDER BY id FOR UPDATE"),
                      {'s': sid, 'p': periode}).mappings().all()
    if not rows:
        raise HTTPException(409, 'Aucun bulletin valide à comptabiliser pour ce mois.')
    total = {k: ZERO for k in ('brut', 'salarial', 'patronal', 'ir', 'avances', 'net')}
    for r in rows:
        c = sortie(r)['contenu']
        total['brut'] += D(c['brut']); total['salarial'] += D(c['cotisations_salariales'])
        total['patronal'] += D(c['cotisations_patronales']); total['ir'] += D(c['ir_retenu'])
        total['avances'] += D(c['total_avances']); total['net'] += D(c['net_a_payer'])
    mois = periode.strftime('%m/%Y')
    lignes = [
        (COMPTES['brut'], f'Rémunérations brutes {mois}', total['brut'], ZERO),
        (COMPTES['patronal'], f'Charges sociales patronales {mois}', total['patronal'], ZERO),
        (COMPTES['organismes'], f'Cotisations salariales et patronales {mois}', ZERO, total['salarial'] + total['patronal']),
        (COMPTES['ir'], f'IR retenu à la source {mois}', ZERO, total['ir']),
        (COMPTES['avances'], f'Retenues sur avances et prêts {mois}', ZERO, total['avances']),
        (COMPTES['net'], f'Rémunérations nettes dues {mois}', ZERO, total['net']),
    ]
    e = ecrire(db, user, data.date_ecriture, 'SA', f'Paie {mois} — {len(rows)} bulletin(s)', f'PAIE-{periode:%Y-%m}', lignes)
    db.execute(text('UPDATE paie_bulletins SET ecriture_id=:e WHERE id = ANY(:ids) AND societe_id=:s'),
               {'e': e, 'ids': [r['id'] for r in rows], 's': sid})
    return {'ecriture_id': e, 'bulletins': len(rows), 'totaux': {k: texte(v) for k, v in total.items()}}


@w.transaction
def payer(db, user, data):
    exiger_comptable(user)
    autoriser(db, user)
    sid = user['societe_id']
    verrou(db, sid)
    ids = sorted(set(data.bulletin_ids))
    rows = db.execute(text('SELECT * FROM paie_bulletins WHERE societe_id=:s AND id = ANY(:ids) FOR UPDATE'), {'s': sid, 'ids': ids}).mappings().all()
    if len(rows) != len(ids):
        raise HTTPException(404, 'Bulletin introuvable dans cette société.')
    for r in rows:
        if r['statut'] != 'VALIDE':
            raise HTTPException(409, f'Bulletin #{r["id"]} annulé : aucun paiement.')
        if r['paiement_date']:
            raise HTTPException(409, f'Bulletin #{r["id"]} déjà payé.')
        if not r['ecriture_id']:
            raise HTTPException(409, f'Bulletin #{r["id"]} non comptabilisé : comptabiliser la paie du mois avant le paiement.')
    total = sum((argent(r['net_a_payer']) for r in rows), ZERO)
    if total <= 0:
        raise HTTPException(409, 'Net total nul : aucun paiement à enregistrer.')
    journal, tresorerie = TRESORERIE[data.mode]
    verifier_sortie_caisse(db, sid, tresorerie, total, data.date_paiement)  # lot 977
    noms = ', '.join(sorted({r['contenu']['nom'] for r in rows}))
    libelle = f'Paiement salaires — {noms}' if len(rows) <= 3 else f'Paiement salaires — {len(rows)} salariés'
    e = ecrire(db, user, data.date_paiement, journal, libelle, data.reference or f'PAIE-REG-{data.date_paiement:%Y%m%d}',
               [(COMPTES['net'], libelle, total, ZERO), (tresorerie, libelle, ZERO, total)])
    db.execute(text('UPDATE paie_bulletins SET paiement_ecriture_id=:e,paiement_date=:d,paiement_mode=:m WHERE id = ANY(:ids) AND societe_id=:s'),
               {'e': e, 'd': data.date_paiement, 'm': data.mode, 'ids': ids, 's': sid})
    return {'ecriture_id': e, 'bulletins': len(rows), 'total': texte(total)}


# ── États ───────────────────────────────────────────────────────────────────

def etats(db, user, annee):
    autoriser(db, user)
    rows = [dict(x) for x in db.execute(text(ETAT_SQL + " AND b.statut='VALIDE' AND extract(year FROM b.periode)=:a ORDER BY b.periode,b.contenu->>'nom'"),
                                       {'s': user['societe_id'], 'a': annee}).mappings()]
    champs = ('brut', 'cotisations_salariales', 'cotisations_patronales', 'ir_retenu', 'total_avances', 'net_a_payer', 'cout_employeur')
    mois = {}
    for r in rows:
        m = mois.setdefault(r['periode'].isoformat()[:7], {'periode': r['periode'].isoformat()[:7], 'bulletins': 0, **{k: ZERO for k in champs},
                                                          'comptabilises': 0, 'payes': 0})
        m['bulletins'] += 1
        m['comptabilises'] += bool(r['ecriture_id'])
        m['payes'] += bool(r['paiement_date'])
        for k in champs:
            m[k] += D(str(r[k]))
    lignes = sorted(mois.values(), key=lambda x: x['periode'])
    for m in lignes:
        m['organismes_sociaux'] = m['cotisations_salariales'] + m['cotisations_patronales']
        for k in (*champs, 'organismes_sociaux'):
            m[k] = texte(m[k])
    totaux = {k: texte(sum((D(m[k]) for m in lignes), ZERO)) for k in (*champs, 'organismes_sociaux')}
    return {'annee': annee, 'mois': lignes, 'totaux': totaux, 'bulletins': rows,
            'note': 'Récapitulatif interne. Les déclarations CNSS (Damancom) et IR (SIMPL) se déposent sur les portails officiels.'}
