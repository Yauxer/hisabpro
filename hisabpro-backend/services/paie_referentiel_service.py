"""Provenance versionnée : aucune activation de taux, aucun accès réseau."""
from datetime import date
import hashlib
import json
import math
from urllib.parse import urlsplit

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, text

import models


class SourcePaie(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    titre: str = Field(min_length=1, max_length=200)
    url: str | None = Field(default=None, max_length=1000)
    article: str | None = Field(default=None, max_length=200)
    date_effet: date | None = None
    date_consultation: date | None = None
    perimetre: str | None = Field(default=None, max_length=500)
    limite: str | None = Field(default=None, max_length=1000)

    @field_validator('url')
    @classmethod
    def url_https(cls, value):
        if not value:
            return None
        parsed = urlsplit(value)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or any(c.isspace() for c in value):
            raise ValueError('URL HTTPS sans identifiants requise ; aucun téléchargement effectué')
        return value

    @field_validator('date_effet', 'date_consultation', mode='before')
    @classmethod
    def date_facultative(cls, value):
        return None if value == '' else value


class ConsignationPaie(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    empreinte_attendue: str = Field(pattern=r'^[a-f0-9]{64}$')
    sources: list[SourcePaie] = Field(default_factory=list, max_length=20)
    regime: str | None = Field(default=None, max_length=200)
    commentaire: str | None = Field(default=None, max_length=2000)


# Trois listes dans une seule instruction : même snapshot MVCC PostgreSQL,
# y compris si une autre transaction modifie ensuite un paramètre global.
CAPTURE_SQL = text("""
 SELECT json_build_object(
  'bareme_ir', COALESCE((SELECT json_agg(row_to_json(b) ORDER BY b.tranche_min,b.id) FROM public.bareme_ir b WHERE b.annee=:annee),'[]'::json),
  'taux_cotisations', COALESCE((SELECT json_agg(row_to_json(t) ORDER BY t.code,t.id) FROM public.taux_cotisations t WHERE t.annee=:annee),'[]'::json),
  'deductions_ir', COALESCE((SELECT json_agg(row_to_json(d) ORDER BY d.code,d.id) FROM public.deductions_ir d WHERE d.annee=:annee),'[]'::json)
 )
""")


def empreinte_parametres(societe_id, annee, parametres):
    contenu = {'societe_id': societe_id, 'annee': annee, 'parametres': parametres}
    return hashlib.sha256(json.dumps(contenu, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')).hexdigest()


def diagnostics_parametres(parametres):
    erreurs = []
    champs = {
        'bareme_ir': ('tranche_min', 'tranche_max', 'taux', 'deduction'),
        'taux_cotisations': ('taux_sal', 'taux_pat', 'plafond'),
        'deductions_ir': ('montant_an', 'max_beneficiaires'),
    }
    for table, noms in champs.items():
        for ligne in parametres[table]:
            for nom in noms:
                valeur = ligne.get(nom)
                if valeur is None and nom in ('tranche_max', 'plafond', 'max_beneficiaires'):
                    continue
                label = f'{table} #{ligne.get("id")} {nom}'
                try:
                    if isinstance(valeur, bool):
                        raise ValueError()
                    n = float(valeur)
                    if not math.isfinite(n):
                        erreurs.append(f'{label} : {valeur}, valeur non finie')
                    elif nom in ('taux', 'taux_sal', 'taux_pat') and not 0 <= n <= 1:
                        erreurs.append(f'{label} : ratio hors bornes [0, 1]')
                    elif nom == 'plafond' and n <= 0:
                        erreurs.append(f'{label} : plafond non strictement positif')
                    elif nom not in ('taux', 'taux_sal', 'taux_pat') and n < 0:
                        erreurs.append(f'{label} : valeur négative')
                except (ValueError, TypeError, OverflowError):
                    erreurs.append(f'{label} : valeur non numérique')
    return erreurs


def capturer_parametres(db, annee):
    # row_to_json représente les NaN/Infinity SQL en chaînes JSON, sans 0 inventé.
    parametres = db.execute(CAPTURE_SQL, {'annee': annee}).scalar_one()
    return parametres, diagnostics_parametres(parametres)


def sortie_version(version):
    return {nom: getattr(version, nom) for nom in ('id', 'version', 'empreinte', 'parametres', 'sources', 'regime', 'commentaire', 'created_by', 'created_at')} | {'statut': version.qualification}


def lire_referentiel(db, user, annee):
    parametres, diagnostics = capturer_parametres(db, annee)
    empreinte = empreinte_parametres(user['societe_id'], annee, parametres)
    versions = db.query(models.PaieReferentielVersion).filter_by(societe_id=user['societe_id'], annee=annee).order_by(models.PaieReferentielVersion.version.desc()).all()
    courante = versions[0] if versions else None
    statut = 'non_verifie' if courante is None else ('perime' if courante.empreinte != empreinte else courante.qualification)
    return {'annee': annee, 'statut': statut, 'empreinte_actuelle': empreinte,
            'version_courante': sortie_version(courante) if courante else None,
            'historique': [sortie_version(v) for v in versions], 'parametres_actuels': parametres,
            'diagnostics': diagnostics, 'peut_consigner': user['role'] == 'admin',
            'paie_definitive_autorisee': False,
            'limites': ['Consignation de preuves partielles ; aucune conformité réglementaire validée.',
                       'La consignation ne modifie aucun taux et ne débloque pas une paie définitive.']}


def consigner_referentiel(db, user, annee, data):
    # Pas de droit UPDATE société ni LOCK TABLE requis : verrou transactionnel
    # dédié à cette société/année ; la contrainte UNIQUE reste le dernier garde-fou.
    cle = f'hisabpro:paie:referentiel:{user["societe_id"]}:{annee}'
    db.execute(text('SELECT pg_advisory_xact_lock(hashtextextended(:cle,0))'), {'cle': cle})
    parametres, diagnostics = capturer_parametres(db, annee)
    if diagnostics:
        raise HTTPException(409, detail={'message': 'Paramètres invalides : consignation impossible sans correction contrôlée.', 'diagnostics': diagnostics})
    empreinte = empreinte_parametres(user['societe_id'], annee, parametres)
    if empreinte != data.empreinte_attendue:
        raise HTTPException(409, detail='Le référentiel, la société ou l’année a changé. Rechargez avant de consigner.')
    dernier = db.query(func.max(models.PaieReferentielVersion.version)).filter(
        models.PaieReferentielVersion.societe_id == user['societe_id'], models.PaieReferentielVersion.annee == annee).scalar() or 0
    sources = [source.model_dump(mode='json') for source in data.sources]
    version = models.PaieReferentielVersion(societe_id=user['societe_id'], annee=annee, version=dernier + 1,
        empreinte=empreinte, parametres=parametres, sources=sources, regime=data.regime, commentaire=data.commentaire,
        qualification='preuves_partielles' if sources else 'non_verifie', created_by=user['id'])
    db.add(version)
    db.commit()
    return lire_referentiel(db, user, annee)
