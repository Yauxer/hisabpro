"""B11 indépendant : sources décimales conservées, jamais le Journal courant."""
from copy import deepcopy
from decimal import Decimal, localcontext

from services.balance_import_service import montant_import
from services.balance_source_controle_service import cloture_technique

BLOC = 'detail_cpc_documentaire'
NOTE = ('Détail B11 interne en MAD depuis les seules balances normalisées conservées. '
        'Charges = débit moins crédit ; produits = crédit moins débit. Les soldes inverses '
        'restent signés et les comptes soldés sont omis. Les libellés de comptes ne sont pas '
        'conservés à l’import : aucun libellé du plan actuel ne leur est attribué. '
        'Les écarts au CPC figé restent visibles, sans reclassement ni correction. '
        'Ce détail ne prouve ni mouvements bruts ni exhaustivité réglementaire ; '
        'il ne vaut pas liasse prête à déposer.')


def calculer(dossier):
    """Résultats exacts sérialisables, y compris au-delà de la précision Excel."""
    from services.etic_service import CATALOGUE_ETIC
    contenu = dossier['contenu']
    prep = contenu.get('preparation', {})
    periodes = {}
    with localcontext() as ctx:
        ctx.prec = 60
        for periode in ('n', 'n1'):
            source = contenu.get('sources', {}).get(periode)
            etats = prep.get('etats' if periode == 'n' else 'etats_n1') or {}
            cpc = etats.get('cpc') or {}
            base = {'disponible': False, 'motif': '', 'lignes': [], 'charges': None,
                    'produits': None, 'resultat': None, 'cpc_charges': None,
                    'cpc_produits': None, 'cpc_resultat': None,
                    'ecart_charges': None, 'ecart_produits': None, 'ecart_resultat': None}
            if source is None:
                base['motif'] = 'Source détaillée ' + periode.upper().replace('N1', 'N-1') + ' absente ; aucun détail reconstitué.'
            elif not isinstance(source, list) or any(
                not isinstance(r, dict) or not isinstance(r.get('compte'), str)
                or any(r.get(k) is None or r.get(k) == '' for k in ('debit', 'credit'))
                for r in source
            ):
                base['motif'] = 'Source détaillée incomplète ; aucun montant manquant remplacé par zéro.'
            elif cloture_technique(dossier, periode):
                base['motif'] = 'Classes6/7 soldées et résultat119 présent : balance avant clôture technique requise.'
            elif cpc.get('disponible') is False:
                base['motif'] = cpc.get('motif') or 'CPC conservé indisponible ; aucun détail nul fabriqué.'
            elif not cpc:
                base['motif'] = 'CPC conservé absent ; réimporter explicitement la balance.'
            else:
                comptes = {}
                for r in source:
                    compte = r['compte']
                    if not compte.startswith(('6', '7')):
                        continue
                    net = montant_import(r['debit'], compte) - montant_import(r['credit'], compte)
                    comptes[compte] = comptes.get(compte, Decimal(0)) + net
                lignes = [{'compte': c, 'intitule': None,
                           'nature': 'Charge' if c.startswith('6') else 'Produit',
                           'montant': format(v if c.startswith('6') else -v, '.2f')}
                          for c, v in sorted(comptes.items()) if v != 0]
                charges = sum((Decimal(r['montant']) for r in lignes if r['nature'] == 'Charge'), Decimal(0))
                produits = sum((Decimal(r['montant']) for r in lignes if r['nature'] == 'Produit'), Decimal(0))
                # Référence = agrégats du CPC déjà figé, pas un recalcul avec le moteur actuel.
                def reference(cles):
                    valeurs = [cpc.get(k) for k in cles]
                    if any(v is None for v in valeurs):
                        return None
                    nombres = [Decimal(str(v)) for v in valeurs]
                    if not all(v.is_finite() for v in nombres):
                        raise ValueError('Agrégat CPC non fini dans la version conservée.')
                    return sum(nombres, Decimal(0))
                valeurs = {'charges': charges, 'produits': produits, 'resultat': produits - charges}
                refs = {'charges': reference(('II', 'V', 'IX', 'XII')),
                        'produits': reference(('I', 'IV', 'VIII')),
                        'resultat': reference(('resultat_net',))}
                base.update(disponible=True, lignes=lignes)
                for k, v in valeurs.items():
                    base[k] = format(v, '.2f')
                    base['cpc_' + k] = None if refs[k] is None else format(refs[k], 'f')
                    base['ecart_' + k] = None if refs[k] is None else format(v - refs[k], 'f')
            periodes[periode] = base
    return {'code': 'B11', 'titre': next(r['titre'] for r in CATALOGUE_ETIC if r['code'] == 'B11'),
            'methode': 'soldes_classes_6_7_decimal_v1', 'note': NOTE,
            'periodes': periodes, 'pret_a_deposer': False}


def presentation(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if not bloc:
        return {'conserve': False, 'vue': None, 'note': NOTE, 'pret_a_deposer': False}
    return {**deepcopy(bloc), 'conserve': True, 'pret_a_deposer': False}


def conserver(db, user, preparation_id, data):
    """Nouvelle version, verrou société et rejeu avant tout nouveau calcul."""
    from datetime import datetime, timezone
    from fastapi import HTTPException
    from sqlalchemy import func
    import models
    from services.balance_import_service import lire_preparation, empreinte_preparation
    sid = user['societe_id']
    societe = db.query(models.Societe).filter_by(id=sid).with_for_update().first()
    if not societe:
        raise HTTPException(404, 'Société introuvable.')
    row = db.query(models.LiasseBalancePreparation).filter_by(id=preparation_id, societe_id=sid).first()
    if not row:
        raise HTTPException(404, 'Préparation introuvable dans cette société.')
    try:
        dossier = lire_preparation(row)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    if data.empreinte_parent != dossier['empreinte_sha256']:
        raise HTTPException(409, 'Préparation différente de la source attendue.')
    if (societe.devise or 'MAD').strip().upper() != 'MAD':
        raise HTTPException(422, 'Détail exprimé en MAD ; aucune conversion automatique.')
    demande = {'schema_version': 1, 'cle': str(data.cle),
               'parent': {'id': row.id, 'version': row.version, 'empreinte_sha256': row.empreinte_sha256}}
    ancien = db.query(models.LiasseBalancePreparation).filter(
        models.LiasseBalancePreparation.societe_id == sid,
        models.LiasseBalancePreparation.contenu[BLOC]['cle'].as_string() == str(data.cle)).first()
    if ancien:
        try:
            saved = lire_preparation(ancien)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if {k: saved['contenu'][BLOC][k] for k in demande} != demande:
            raise HTTPException(409, 'Clé déjà utilisée pour une autre source B11.')
        return saved
    try:
        vue = calculer(dossier)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    acteur = db.query(models.Utilisateur).filter_by(id=user['id']).one()
    contenu = deepcopy(row.contenu)
    contenu[BLOC] = {**demande, 'vue': vue, 'auteur': {'id': acteur.id, 'nom': acteur.nom},
                    'conserve_le_utc': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    latest = db.query(func.max(models.LiasseBalancePreparation.version)).filter_by(
        societe_id=sid, exercice=row.exercice).scalar() or 0
    nouveau = models.LiasseBalancePreparation(societe_id=sid, exercice=row.exercice,
        exercice_id=row.exercice_id, version=latest + 1, contenu=contenu,
        empreinte_sha256=empreinte_preparation(contenu), created_by=user['id'])
    db.add(nouveau); db.commit(); db.refresh(nouveau)
    return lire_preparation(nouveau)
