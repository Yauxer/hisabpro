"""Fondation1A.2 :diagnostic sans mutation et contrats de valeurs exactes.

Pas de création/approbation applicative dans cette sous-étape.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy import text

TABLES = ('personnel_dossiers', 'personnel_demandes', 'personnel_contrats_versions',
          'personnel_remunerations_versions', 'personnel_evenements')
ESPACES_MATRICULE = ' \t\n\r\f\v'


def normaliser_matricule(valeur):
    if valeur is None:
        return None
    if not isinstance(valeur, str):
        raise ValueError('Le matricule est une référence textuelle.')
    return valeur.strip(ESPACES_MATRICULE) or None


def montant_exact(valeur):
    if isinstance(valeur, bool) or not isinstance(valeur, (str, int, Decimal)):
        raise ValueError('Utiliser un montant décimal exact en texte, sans flottant.')
    try:
        montant = Decimal(valeur)
    except InvalidOperation as exc:
        raise ValueError('Montant décimal invalide.') from exc
    if not montant.is_finite() or montant < 0 or montant >= Decimal('10000000000000000'):
        raise ValueError('Montant fini positif ou nul, limité à16 chiffres entiers.')
    if montant.as_tuple().exponent < -2:
        raise ValueError('Deux décimales maximum ;aucun arrondi implicite.')
    return montant.quantize(Decimal('0.01'))


class RemunerationVersion(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    montant: Decimal
    date_effet: date
    periodicite: Literal['mensuelle', 'journaliere', 'horaire']
    devise: Literal['MAD'] = 'MAD'
    reference_justificatif: str = Field(min_length=1, max_length=200)

    @field_validator('montant', mode='before')
    @classmethod
    def valider_montant(cls, valeur):
        return montant_exact(valeur)

    @field_validator('date_effet', mode='before')
    @classmethod
    def valider_date(cls, valeur):
        # Refuser les timestamps/nombres interprétés comme dates par coercition.
        if type(valeur) is date:
            return valeur
        if not isinstance(valeur, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', valeur):
            raise ValueError('Date d’effet requise au format AAAA-MM-JJ.')
        return valeur

    @field_serializer('montant')
    def serialiser_montant(self, valeur):
        return format(valeur, '.2f')


def preflight_dossiers(db, sid, *, limite=50):
    """Une seule lecture des racines ;jamais conversion/backfill d'un salaire.

    Les listes sont plafonnées, les totaux complets. Les informations de schéma
    ne contiennent aucune donnée d'une autre société.
    """
    if db.bind.dialect.name != 'postgresql':
        raise HTTPException(503, 'Ce diagnostic nécessite PostgreSQL.')
    colonnes = db.execute(text("SELECT column_name,data_type FROM information_schema.columns "
                              "WHERE table_schema='public' AND table_name='employes' ")).all()
    types = dict(colonnes)
    requis = {'id', 'societe_id', 'matricule', 'salaire_brut', 'date_embauche', 'date_sortie', 'actif'}
    if not requis <= set(types):
        raise HTTPException(503, 'Schéma employes incomplet :diagnostic indisponible.')
    tables = {t: bool(db.scalar(text('SELECT to_regclass(:t) IS NOT NULL'), {'t': 'public.'+t})) for t in TABLES}
    attendu = {'personnel_dossiers': {'employe_id', 'societe_id', 'matricule_cle', 'origine', 'statut', 'revision', 'cree_par'},
               'personnel_demandes': {'id', 'societe_id', 'employe_id', 'nature', 'revision_attendue', 'prepare_par', 'statut'},
               'personnel_contrats_versions': {'id', 'societe_id', 'employe_id', 'demande_id', 'date_effet', 'approuvee_at'},
               'personnel_remunerations_versions': {'id', 'societe_id', 'employe_id', 'demande_id', 'montant', 'date_effet', 'approuvee_at'},
               'personnel_evenements': {'id', 'societe_id', 'employe_id', 'auteur_id', 'revision', 'motif'}}
    catalogue = db.execute(text("SELECT table_name,column_name,data_type,numeric_precision,numeric_scale "
                                "FROM information_schema.columns WHERE table_schema='public' "
                                "AND table_name=ANY(:tables)"), {'tables': list(TABLES)}).mappings().all()
    manquantes = {t: sorted(noms-{r['column_name'] for r in catalogue if r['table_name']==t})
                  for t,noms in attendu.items() if tables[t]}
    montant = next((r for r in catalogue if r['table_name']=='personnel_remunerations_versions' and r['column_name']=='montant'), None)
    montant_ok = montant is not None and (montant['data_type'],montant['numeric_precision'],montant['numeric_scale'])==('numeric',18,2)
    cle_composee = bool(db.scalar(text("SELECT EXISTS(SELECT 1 FROM pg_constraint c "
        "WHERE c.conrelid='public.employes'::regclass AND c.contype IN ('p','u') AND "
        "(SELECT array_agg(a.attname::text ORDER BY k.ord) FROM unnest(c.conkey) WITH ORDINALITY k(num,ord) "
        "JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.num)=ARRAY['id','societe_id'])")))
    coherent = all(tables.values()) and not any(manquantes.values()) and montant_ok and cle_composee
    rows = db.execute(text("SELECT id,matricule,date_embauche IS NULL AS entree_inconnue,"
                           "(date_embauche IS NOT NULL AND NOT isfinite(date_embauche)) OR "
                           "(date_sortie IS NOT NULL AND NOT isfinite(date_sortie)) OR "
                           "(date_embauche IS NOT NULL AND date_sortie<date_embauche) AS dates_incoherentes,"
                           "salaire_brut IS NULL OR salaire_brut::text IN ('NaN','Infinity','-Infinity') "
                           "OR salaire_brut<0 AS salaire_invalide "
                           "FROM public.employes WHERE societe_id=:s ORDER BY id"), {'s': sid}).mappings().all()
    groupes = {}
    manquants, entrees, dates, salaires = [], [], [], []
    for r in rows:
        cle = normaliser_matricule(r['matricule'])
        if cle is None:
            manquants.append(r['id'])
        else:
            groupes.setdefault(cle, []).append(r['id'])
        if r['entree_inconnue']:
            entrees.append(r['id'])
        if r['dates_incoherentes']:
            dates.append(r['id'])
        if r['salaire_invalide']:
            salaires.append(r['id'])
    collisions = [{'matricule_cle': k, 'employe_ids': v[:limite], 'nombre': len(v)}
                  for k,v in sorted(groupes.items()) if len(v)>1]
    def detail(ids):
        return {'nombre': len(ids), 'employe_ids': ids[:limite], 'tronque': len(ids)>limite}
    return {'societe_id': sid, 'lecture_seule': True, 'nombre_employes': len(rows),
            'schema_versions': 'installe' if coherent else 'incoherent' if all(tables.values()) else 'partiel' if any(tables.values()) else 'absent',
            'tables': tables, 'type_salaire_historique': types['salaire_brut'],
            'controles_schema': {'colonnes_attendues_manquantes': manquantes,
                                 'montant_numeric_18_2': montant_ok, 'cle_employe_societe_presente': cle_composee},
            'matricules_manquants': detail(manquants),
            'collisions_matricules': {'nombre': len(collisions), 'groupes': collisions[:limite],
                                      'tronque': len(collisions)>limite},
            'dates_entree_inconnues': detail(entrees), 'dates_incoherentes': detail(dates),
            'salaires_invalides': detail(salaires),
            'reprise_sans_ambiguite_matricule': not manquants and not collisions,
            'historique_atteste': False, 'activation_paie_autorisee': False,
            'avertissements': ['Le salaire historique flottant ne constitue pas une rémunération exacte attestée.',
                               'Aucune date d’effet ni approbation n’est déduite de actif ou created_at.',
                               'Les anomalies ne sont ni réparées ni reclassées par ce diagnostic.']}
