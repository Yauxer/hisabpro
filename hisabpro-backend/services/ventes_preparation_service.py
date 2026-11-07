"""Préparation documentaire interne : aucune déclaration ou codification DGI."""
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from decimal import Decimal, DecimalException, localcontext

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import joinedload
import models
from services.tva_service import ventilation_facture, ventilation_avoir, total_ventilation

NOTE = ('Préparation interne issue des factures et avoirs de vente. '
        'HT commercial avant escompte ; TVA et TTC selon les calculs des pièces. '
        'Ce relevé ne représente ni le chiffre d’affaires comptable, ni une déclaration DGI. '
        'Les écritures manuelles et ventes absentes de la facturation ne sont pas incluses dans le relevé documentaire ; elles peuvent contribuer au raccordement comptable séparé. '
        'Les identités proviennent des snapshots des pièces, jamais de la fiche tiers actuelle. '
        'Cette préparation courante est extérieure aux archives de liasse existantes.')


def _valeur(v):
    return getattr(v, 'value', v)


def _montant(v):
    if v is None or isinstance(v, bool):
        raise ValueError('Montant inconnu')
    d = Decimal(str(v))
    if not d.is_finite() or d < 0:
        raise ValueError('Montant inexploitable')
    with localcontext() as ctx:
        ctx.prec = max(28, len(d.as_tuple().digits) + max(0, d.adjusted()) + 4)
        return d.quantize(Decimal('0.01'))


def _sommes(rows):
    with localcontext() as ctx:
        ctx.prec = max([28] + [len(str(r[k])) + 10 for r in rows for k in ('ht', 'tva', 'ttc')])
        return {k: format(sum((Decimal(r[k]) for r in rows), Decimal(0)), '.2f') for k in ('ht', 'tva', 'ttc')}


def preparer_lecture(db):
    """Initialiser avant l'authentification, sur la même et unique connexion."""
    if db.get_bind().dialect.name == 'postgresql':
        if not db.in_transaction():
            db.connection(execution_options={'isolation_level': 'REPEATABLE READ'})
            db.execute(text('SET TRANSACTION READ ONLY'))
        elif (db.connection().get_isolation_level() != 'REPEATABLE READ'
              or db.scalar(text('SHOW transaction_read_only')) != 'on'):
            raise HTTPException(409, 'La préparation requiert une nouvelle lecture cohérente. Actualisez la préparation.')
    return db


def construire(db, sid, exercice):
    preparer_lecture(db)
    return _construire(db, sid, exercice)


def _construire(db, sid, exercice):
    # Une lecture ne crée ni exercice ni périodes et ne finalise aucun dossier.
    ex = db.query(models.ExerciceComptable).filter_by(societe_id=sid, annee=exercice).first()
    if ex is None:
        raise HTTPException(404, 'Exercice introuvable pour cette société.')
    societe=db.query(models.Societe).filter_by(id=sid).one()
    from routers.factures import _calc_totaux, _total_avoir_qualifie
    documents = []
    exclusions = {'brouillons': 0, 'proformas': 0, 'annules': 0}
    for modele, nature in ((models.Facture, 'facture'), (models.Avoir, 'avoir')):
        rows = db.query(modele).options(joinedload(modele.lignes)).filter(
            modele.societe_id == sid, modele.type == 'vente',
            modele.date >= ex.date_debut, modele.date <= ex.date_fin,
        ).order_by(modele.date, modele.id).all()
        for piece in rows:
            if _valeur(piece.statut) in {'annule', 'annulee'}:
                exclusions['annules'] += 1
                continue
            if nature == 'facture' and piece.est_proforma:
                exclusions['proformas'] += 1
                continue
            if nature == 'facture' and not piece.est_validee:
                exclusions['brouillons'] += 1
                continue
            diagnostics = []
            if piece.exercice != exercice:
                diagnostics.append('Référence d’exercice incohérente avec la période : à vérifier.')
            if not piece.tiers_ice_snapshot:
                diagnostics.append('ICE figé non renseigné dans cette pièce.')
            if not piece.est_comptabilisee:
                diagnostics.append('Pièce non comptabilisée.')
            row = {'nature': nature, 'id': piece.id, 'numero': piece.numero,
                   'date': piece.date.isoformat(), 'tiers': piece.tiers,
                   'ice': piece.tiers_ice_snapshot, 'identifiant_fiscal': piece.tiers_if_snapshot,
                   'facture_id': piece.id if nature == 'facture' else piece.facture_id,
                   'comptabilisee': bool(piece.est_comptabilisee), 'diagnostics': diagnostics}
            try:
                if not piece.lignes or piece.exercice != exercice:
                    raise ValueError('Source incomplète')
                if nature == 'facture':
                    _calc_totaux(piece)  # Garder les contrôles historiques existants.
                    ventilation = ventilation_facture
                else:
                    _total_avoir_qualifie(piece)
                    if any(l.montant_ht_force is not None and l.montant_ht_force < 0 for l in piece.lignes):
                        raise ValueError('Base d’avoir historique négative')
                    ventilation = ventilation_avoir
                    parent = db.query(models.Facture).filter_by(id=piece.facture_id, societe_id=sid).first()
                    if parent is None or _valeur(parent.type) != 'vente':
                        raise ValueError('Facture source absente ou incohérente')
                # Même moteur et mêmes arrondis que les pièces, sans détour
                # par float qui peut perdre un centime sur un grand montant.
                avant = total_ventilation(ventilation(piece, appliquer_escompte=False))
                apres = total_ventilation(ventilation(piece, appliquer_escompte=True))
                ht, tva, ttc = avant['base'], apres['tva'], apres['ttc']
                signe = 1 if nature == 'facture' else -1
                row.update({k: format(signe * _montant(v), '.2f') for k, v in zip(('ht', 'tva', 'ttc'), (ht, tva, ttc))})
            except (HTTPException, DecimalException, ValueError, TypeError, OverflowError) as exc:
                if isinstance(exc, HTTPException) and exc.status_code != 422:
                    raise
                row.update(ht=None, tva=None, ttc=None)
                diagnostics.append('Montants sources à vérifier ; aucune valeur remplacée par zéro.')
            documents.append(row)
    documents.sort(key=lambda r: (r['date'], r['nature'], r['id']))
    connus = [r for r in documents if r['ht'] is not None]
    data = {'exercice': exercice, 'societe_id': sid,
            'societe':{k:getattr(societe,k,None) for k in ('raison_sociale','ice','identifiant_fiscal')},
            'date_debut': ex.date_debut.isoformat(),
            'date_fin': ex.date_fin.isoformat(), 'note': NOTE,
            'documents': documents, 'exclusions': exclusions,
            'nb_montants_inconnus': len(documents)-len(connus),
            'totaux_partie_connue': _sommes(connus),
            'totaux': _sommes(connus) if len(connus) == len(documents) else None}
    from services.ventes_raccordement_service import construire as raccordement
    data['comptabilite'] = raccordement(db, sid, ex, data['totaux']['ht'] if data['totaux'] is not None else None)
    data['empreinte_sha256'] = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    data['constate_le'] = datetime.now(timezone.utc).isoformat()
    data['csv'] = exporter_csv(data)
    return data


def exporter_csv(data):
    out = io.StringIO(newline='')
    w = csv.writer(out, delimiter=';')
    # Échapper les cellules texte pouvant être interprétées comme formules.
    def texte(v):
        v = '' if v is None else str(v)
        return "'"+v if v.lstrip().startswith(('=', '+', '-', '@')) else v
    w.writerow(['Préparation interne des ventes', data['exercice']])
    w.writerow(['Société',texte(data['societe']['raison_sociale'])])
    w.writerow(['ICE société',texte(data['societe']['ice']),'IF société',texte(data['societe']['identifiant_fiscal'])])
    w.writerow([data['note']])
    w.writerow(['Période', data['date_debut'], data['date_fin']])
    w.writerow(['Empreinte', data['empreinte_sha256']])
    w.writerow(['Nature', 'ID source', 'Numéro', 'Date', 'Client figé', 'ICE figé', 'IF figé',
                'HT commercial signé', 'TVA signée', 'TTC signé', 'Comptabilisée', 'Diagnostics'])
    for r in data['documents']:
        w.writerow([texte(r[k]) for k in ('nature', 'id', 'numero', 'date', 'tiers', 'ice', 'identifiant_fiscal')]
                   + [r[k] if r[k] is not None else 'À vérifier' for k in ('ht', 'tva', 'ttc')]
                   + ['Oui' if r['comptabilisee'] else 'Non', texte(' '.join(r['diagnostics']))])
    for label, valeurs in [('Total complet', data['totaux']), ('Partie connue uniquement', data['totaux_partie_connue'])]:
        w.writerow([label] + ['']*6 + [valeurs[k] if valeurs is not None else 'À vérifier' for k in ('ht', 'tva', 'ttc')])
    w.writerow(['Exclusions'] + [f'{k} : {v}' for k, v in data['exclusions'].items()])
    compta = data.get('comptabilite')
    if compta:
        w.writerow(['Raccordement comptable', compta['note']])
        w.writerow(['CA comptes711/712', compta['ca_net'] if compta['ca_net'] is not None else 'À vérifier'])
        w.writerow(['Écart CA moins HT documentaire', compta['ecart_ca_moins_ht'] if compta['ecart_ca_moins_ht'] is not None else 'À vérifier'])
        w.writerow(['Écriture', 'Ligne', 'Date', 'Journal', 'Référence', 'Origine technique', 'Compte', 'Débit', 'Crédit', 'CA net'])
        for m in compta['mouvements']:
            w.writerow([texte(m[k]) for k in ('ecriture_id', 'ligne_id', 'date', 'journal', 'reference', 'source', 'compte')]
                + [m[k] for k in ('debit', 'credit', 'ca_net')])
        for alerte in compta['avertissements']: w.writerow(['À vérifier', texte(alerte)])
    return out.getvalue()
