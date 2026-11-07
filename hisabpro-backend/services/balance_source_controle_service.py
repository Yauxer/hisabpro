"""Gardes des sources externes, communes aux projections B11/B13/C3."""
from decimal import Decimal, localcontext
from services.balance_import_service import montant_import

def cloture_technique(dossier, periode):
    """Même garde119 que l'import, y compris pour un ancien CPC sans drapeau."""
    rows = dossier['contenu'].get('sources', {}).get(periode)
    if not isinstance(rows, list) or any(not isinstance(r, dict) or not isinstance(r.get('compte'), str)
        or any(r.get(k) is None or r.get(k) == '' for k in ('debit', 'credit')) for r in rows):
        return False
    with localcontext() as ctx:
        ctx.prec = 60
        technique = sum((montant_import(r['credit'], r['compte']) - montant_import(r['debit'], r['compte'])
                         for r in rows if r['compte'].startswith('119')), Decimal(0))
        activite = any(montant_import(r['debit'], r['compte']) != montant_import(r['credit'], r['compte'])
                       for r in rows if r['compte'].startswith(('6', '7')))
    return bool(technique) and not activite


