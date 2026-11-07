# -*- coding: utf-8 -*-
"""Présentation détaillée du bilan à partir des agrégats déjà calculés.

Les sous-postes sont affichés POUR MÉMOIRE et ne sont jamais additionnés aux
rubriques mères. L'absence de N-1 vaut ``None`` (pas un montant nul fictif).
"""
from __future__ import annotations

import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

SPEC = json.loads(Path(__file__).with_name('bilan_rubriques.json').read_text(encoding='utf-8'))
C = Decimal('0.01')


def money(v):
    return Decimal(str(v or 0)).quantize(C, rounding=ROUND_HALF_UP)


def brut_detail(soldes, prefixes):
    return money(sum((money(v.get('debit')) - money(v.get('credit'))
                      for compte, v in (soldes or {}).items()
                      if compte.startswith(tuple(prefixes))), Decimal('0')))


def lignes_bilan_detaille(bilan, soldes, bilan_n1, soldes_n1, cote, n1_disponible):
    """Retourne les lignes structurées consommées par le PDF, sans changer la liasse."""
    if cote not in ('actif', 'passif'):
        raise ValueError('Côté du bilan inconnu')
    sections = [s for s in SPEC if s['side'] == cote]
    racine = bilan[cote]
    precedent = (bilan_n1 or {}).get(cote, {})
    lignes = []
    for section in sections:
        groupes = racine.get(section['key'], [])
        groupes_n1 = precedent.get(section['key'], [])
        if len(groupes) != len(section['groups']) or len(groupes_n1) != len(section['groups']):
            raise ValueError(f"Rubriques du bilan incompatibles : {section['key']}")
        lignes.append({'type': 'titre', 'label': section['label'], 'valeurs': []})
        for index, spec in enumerate(section['groups']):
            parent = groupes[index]
            parent_n1 = groupes_n1[index]
            if cote == 'actif':
                vals = [parent['brut'], parent['amort_prov'], parent['net'],
                        parent_n1['net'] if n1_disponible else None]
            else:
                vals = [parent['montant'], parent_n1['montant'] if n1_disponible else None]
            lignes.append({'type': 'rubrique', 'numero': spec['code'],
                           'label': spec['label'], 'valeurs': vals, 'niveau': 0})
            details = spec['details'] if cote == 'actif' else []
            sommes_n = Decimal('0'); sommes_n1 = Decimal('0')
            for detail in details:
                d = brut_detail(soldes, detail['prefixes'])
                d1 = brut_detail(soldes_n1, detail['prefixes']) if n1_disponible else None
                sommes_n += d
                if d1 is not None: sommes_n1 += d1
                # Les amortissements et dépréciations ne sont pas imputés
                # arbitrairement aux sous-postes sans ventilation fiable.
                net = d if abs(money(parent['amort_prov'])) < C else None
                net_n1 = (d1 if abs(money(parent_n1['amort_prov'])) < C else None)
                lignes.append({'type': 'detail', 'numero': detail['code'],
                               'label': detail['label'],
                               'valeurs': [float(d), None, float(net) if net is not None else None,
                                           float(net_n1) if net_n1 is not None else None],
                               'niveau': 1})
            reste = money(parent.get('brut')) - sommes_n
            reste_n1 = money(parent_n1.get('brut')) - sommes_n1 if n1_disponible else None
            if details and (abs(reste) >= C or (reste_n1 is not None and abs(reste_n1) >= C)):
                lignes.append({'type': 'detail', 'numero': '…', 'label': 'Autres comptes de la rubrique',
                               'valeurs': [float(reste), None,
                                           float(reste) if abs(money(parent['amort_prov'])) < C else None,
                                           (float(reste_n1) if reste_n1 is not None and abs(money(parent_n1['amort_prov'])) < C else None)],
                               'niveau': 1})
        if cote == 'actif':
            def tot(key): return float(sum((money(r[key]) for r in groupes), Decimal('0')))
            def tot_n1(): return float(sum((money(r['net']) for r in groupes_n1), Decimal('0')))
            vals = [tot('brut'), tot('amort_prov'), tot('net'), tot_n1() if n1_disponible else None]
        else:
            section_montant = sum((money(r['montant']) for r in groupes), Decimal('0'))
            if section['key'] == 'financement_permanent':
                section_montant += sum((money(r['montant']) for r in racine['capitaux_propres']), Decimal('0'))
            section_n1 = None
            if n1_disponible:
                section_n1 = sum((money(r['montant']) for r in groupes_n1), Decimal('0'))
                if section['key'] == 'financement_permanent':
                    section_n1 += sum((money(r['montant']) for r in precedent['capitaux_propres']), Decimal('0'))
            vals = [float(section_montant), float(section_n1) if section_n1 is not None else None]
        lignes.append({'type': 'total', 'label': section['total'], 'valeurs': vals})
    if cote == 'actif':
        t = racine['total']; t1 = precedent.get('total', {})
        vals = [t['brut'], t['amort_prov'], t['net'], t1.get('net') if n1_disponible else None]
    else:
        vals = [racine['total'], precedent.get('total') if n1_disponible else None]
    lignes.append({'type': 'total', 'label': f'TOTAL GÉNÉRAL {cote.upper()}', 'valeurs': vals})
    return lignes
