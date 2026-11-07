"""Annexes manuelles documentaires, indépendantes de la comptabilité réelle."""
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from services import balance_etic_tables_service as commun
from services.balance_import_service import montant_import
from services.etic_service import CATALOGUE_ETIC

BLOC = 'annexes_etic_documentaires'
STATUTS = commun.STATUTS
IDENTIFIANTS = {'A2':'indication','A3':'nature','B10':'bien','C1':'associe','C2':'nature','C4':'devise'}
NOTE = ('Annexes documentaires selon les colonnes du catalogue HisabPro existant. '
        'Une case vide reste inconnue. Les valeurs financières sont les montants comptabilisés '
        'en MAD, y compris les contre-valeurs documentées de C4 ; aucune conversion de devise '
        'ou qualification fiscale n’est effectuée. Titres et pourcentages ne sont pas des MAD. '
        'Les dates de contrat sont saisies explicitement, jamais déduites des dates comptables. '
        'Documenté ne signifie pas complet ni prêt à déposer. Aucune donnée du Journal '
        'ou de l’ETIC comptable n’est modifiée.')


def catalogue(dossier):
    bloc = dossier['contenu'].get(BLOC)
    if bloc:
        return deepcopy(bloc['catalogue'])
    resultat = []
    for row in CATALOGUE_ETIC:
        if row['code'] not in IDENTIFIANTS:
            continue
        meta = deepcopy({k:row[k] for k in ('code','groupe','titre','colonnes_saisie')})
        meta['champ_identifiant'] = IDENTIFIANTS[row['code']]
        for c in meta['colonnes_saisie']:
            if c['type'] == 'number':
                c['unite'] = ('titres' if c['cle'] == 'titres' else '%' if c['cle'] == 'pourcentage' else 'MAD')
        resultat.append(meta)
    return resultat


def nombre(colonne, valeur, contexte):
    unite = colonne.get('unite', 'MAD')
    if unite == 'MAD':
        return format(montant_import(valeur, contexte), '.2f')
    if isinstance(valeur, bool) or not isinstance(valeur, (str, int, float)):
        raise ValueError(contexte + ' : nombre invalide.')
    try:
        raw = str(valeur).strip().replace('\u00a0','').replace('\u202f','').replace(' ','')
        if len(raw) > 100 or (',' in raw and '.' in raw):
            raise ValueError('Nombre ambigu ou trop long.')
        n = Decimal(raw.replace(',', '.'))
        if not n.is_finite() or n < 0:
            raise ValueError('Nombre fini positif ou nul requis.')
        if unite == 'titres':
            if n > Decimal('999999999999999999') or n != n.to_integral_value():
                raise ValueError('Nombre entier de titres hors limites.')
            return str(int(n))
        if n > 100 or n != n.quantize(Decimal('0.000000000001')):
            raise ValueError('Pourcentage entre 0 et 100, au plus 12 décimales.')
        return format(n, 'f')
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(contexte + ' : ' + str(exc)) from exc


def normaliser(dossier, tables):
    resultat = commun.normaliser(dossier, tables, referentiel=catalogue, convertir_nombre=nombre)
    schemas = {r['code']:r for r in catalogue(dossier)}
    for table in resultat:
        for row in table['lignes']:
            for col in schemas[table['code']]['colonnes_saisie']:
                if col['type'] == 'date' and row[col['cle']]:
                    v = row[col['cle']]
                    try:
                        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
                            raise ValueError('Format invalide')
                        date.fromisoformat(v)
                    except ValueError as exc:
                        raise ValueError(col['label'] + ' : date réelle au format AAAA-MM-JJ requise.') from exc
    return resultat


def presentation(dossier):
    vue = commun.presentation(dossier, nom_bloc=BLOC, referentiel=catalogue, note=NOTE)
    bloc = dossier['contenu'].get(BLOC) or {}
    if 'controle_capital' in bloc:
        vue['controle_capital'] = deepcopy(bloc['controle_capital'])
    return vue


def conserver(db, user, preparation_id, data):
    return commun.conserver(db, user, preparation_id, data, nom_bloc=BLOC,
                            normalisation=normaliser, referentiel=catalogue, enrichir=enrichir)


def enrichir(dossier, demande):
    from services.balance_capital_controle_service import calculer
    return {'controle_capital': calculer(dossier, demande)}
