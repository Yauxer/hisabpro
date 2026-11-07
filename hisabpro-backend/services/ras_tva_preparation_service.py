"""Préparation descriptive mensuelle, dérivée des captures099 sans mutation."""
from datetime import date
from decimal import Decimal
import hashlib
import json
from services.ras_tva_registre_service import construire as registre
from services.ras_tva_documents_service import NOTE_DOCUMENTS

NOTE = ('Préparation interne des retenues opérées sur achats pour les paiements du mois précédent. '
    'Captures TVA guidées uniquement ; les retenues libres et historiques ne sont pas qualifiées ici. '
    'État courant des OD et annulations, y compris les annulations postérieures au mois sélectionné. '
    'Les annulations doivent être rapprochées des bordereaux éventuellement déjà déposés ; elles ne constituent pas une déduction automatique. '
    'Aucun versement n’est suivi ici : les montants actifs ne sont ni un reste à payer ni un paiement justifié. '
    'Ce document ne vaut pas bordereau officiel et ne détermine aucun crédit imputable.')

GROUPES = [('saisies', 'Captures du mois de paiement'), ('actives', 'Captures actives'),
    ('validees', 'Actives · OD validées'), ('annulees', 'Captures annulées · à rapprocher')]


def mois_paiement(annee, mois):
    date(annee, mois, 1)  # Validation y compris pour les appels internes.
    if mois == 1:
        return f'{annee - 1:04d}-12'
    return f'{annee:04d}-{mois - 1:02d}'


def selectionner(source, annee, mois):
    """Pas de solde fiscal : seulement les captures et leur état courant."""
    periode = f'{annee:04d}-{mois:02d}'
    precedent = mois_paiement(annee, mois)
    lignes = []
    for r in source['lignes']:
        if r['nature'] != 'achat' or not r['date_paiement'].startswith(precedent + '-'):
            continue
        r = {**r, 'diagnostics': list(r['diagnostics'])}
        if r['mois_reversement_prevu'] != periode:
            r['diagnostics'].append('Mois prévu du dossier différent du mois suivant le paiement : à vérifier')
        lignes.append(r)
    resultat = {k: source[k] for k in ('societe_id', 'societe', 'disponible', 'migration_requise')}
    resultat.update(annee=annee, periode=periode, mois_paiement=precedent, note=NOTE,note_documents=NOTE_DOCUMENTS,
        lignes=lignes, totaux=None,
        presentation={'titre': 'Préparation mensuelle des retenues TVA opérées',
            'periode': f'Mois de versement prévu : {periode} · Paiements : {precedent}',
            'natures': [('achat', 'Opérées sur achats')], 'groupes': GROUPES})
    if source['disponible']:
        groupes = {'saisies': lignes, 'actives': [r for r in lignes if not r['annulation_id']],
            'validees': [r for r in lignes if not r['annulation_id'] and r['od_validee']],
            'annulees': [r for r in lignes if r['annulation_id']]}
        totaux = {}
        for cle, rows in groupes.items():
            connus = [Decimal(r['retenue_tva']) for r in rows if r['retenue_tva'] is not None]
            somme = format(sum(connus, Decimal(0)), '.2f')
            totaux[cle] = {'montant': somme if len(connus) == len(rows) else None,
                'partie_certaine': somme, 'nombre': len(rows)}
        resultat['totaux'] = {'achat': totaux}
    resultat['empreinte_sha256'] = hashlib.sha256(json.dumps(resultat, sort_keys=True,
        ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    return resultat


def construire(db, sid, annee, mois):
    precedent = mois_paiement(annee, mois)
    # Même connexion et même snapshot RO/RR que le registre. Janvier consulte
    # les paiements de décembre N-1, sans dépendre de l'exercice comptable actif.
    return selectionner(registre(db, sid, int(precedent[:4])), annee, mois)
