"""Raccordement arithmétique, sans qualification individuelle des pièces.

Même périmètre CA711/712 et exclusion des clôtures techniques que la source
des états de synthèse. Les mouvements et écarts ne modifient aucune écriture.
"""
from decimal import Decimal, localcontext
from sqlalchemy import or_
import models
from services.etats_synthese_service import _est_cloture_technique


NOTE = ('Comptes711/712, écritures validées de l’exercice, hors clôtures techniques. '
        'Écart = CA comptable moins HT documentaire signé. Un écart nul ne prouve '
        'pas le rattachement de chaque facture ou avoir. Les origines sont les '
        'marqueurs techniques du Journal, pas une qualification fiscale.')


def construire(db, sid, ex, ht_documentaire):
    e, l = models.Ecriture, models.LigneEcriture
    compte_ca = or_(l.compte.like('711%'), l.compte.like('712%'))
    rows = db.query(e.id.label('ecriture_id'), l.id.label('ligne_id'), e.date, e.exercice,
        e.journal, e.reference, e.source, l.compte, l.debit, l.credit).join(l, l.ecriture_id == e.id).filter(
        e.societe_id == sid, e.exercice == ex.annee, e.est_validee.is_(True),
        ~_est_cloture_technique(), compte_ca).order_by(e.date, e.id, l.id).all()
    brouillons = db.query(e.id).join(l, l.ecriture_id == e.id).filter(
        e.societe_id == sid, e.exercice == ex.annee, e.est_validee.is_(False),
        compte_ca).distinct().count()
    mouvements, comptes, origines, hors_periode = [], {}, {}, set()
    with localcontext() as ctx:
        ctx.prec = 100
        total = Decimal('0.00')
        for r in rows:
            debit, credit = Decimal(str(r.debit)), Decimal(str(r.credit))
            if not debit.is_finite() or not credit.is_finite():
                # Le Journal validé est normalement protégé par ses contraintes.
                # Ne jamais transformer un historique non exploitable en zéro.
                return {'note': NOTE, 'ca_net': None, 'ecart_ca_moins_ht': None,
                    'comptes': [], 'origines': [], 'mouvements': [], 'brouillons_exclus': brouillons,
                    'nb_hors_periode': None, 'avertissements': ['Montants comptables non finis : raccordement indéterminable.']}
            net = credit - debit
            total += net
            origine = r.source or 'non_renseignee'
            compte = comptes.setdefault(r.compte, {'compte': r.compte, 'debit': Decimal(0), 'credit': Decimal(0)})
            compte['debit'] += debit; compte['credit'] += credit
            groupe = origines.setdefault(origine, {'source': origine, 'ca_net': Decimal(0), 'nb_lignes': 0})
            groupe['ca_net'] += net; groupe['nb_lignes'] += 1
            if not (ex.date_debut <= r.date <= ex.date_fin):
                hors_periode.add(r.ecriture_id)
            mouvements.append({'ecriture_id': r.ecriture_id, 'ligne_id': r.ligne_id,
                'date': r.date.isoformat(), 'journal': getattr(r.journal, 'value', r.journal),
                'reference': r.reference, 'source': origine, 'compte': r.compte,
                'debit': format(debit, '.2f'), 'credit': format(credit, '.2f'), 'ca_net': format(net, '.2f')})
        avertissements = []
        if hors_periode:
            avertissements.append('Des dates du Journal sortent des bornes de cet exercice : à vérifier.')
        if ht_documentaire is None:
            avertissements.append('Montants documentaires incomplets : aucun écart complet calculable.')
        return {'note': NOTE, 'ca_net': format(total, '.2f'),
            'ecart_ca_moins_ht': format(total - Decimal(ht_documentaire), '.2f') if ht_documentaire is not None else None,
            'comptes': [{**c, 'debit': format(c['debit'], '.2f'), 'credit': format(c['credit'], '.2f'),
                         'ca_net': format(c['credit'] - c['debit'], '.2f')} for _, c in sorted(comptes.items())],
            'origines': [{**g, 'ca_net': format(g['ca_net'], '.2f')} for _, g in sorted(origines.items())],
            'mouvements': mouvements, 'brouillons_exclus': brouillons,
            'nb_hors_periode': len(hors_periode), 'avertissements': avertissements}
