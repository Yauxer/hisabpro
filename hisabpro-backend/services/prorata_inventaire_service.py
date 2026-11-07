"""Calcul documentaire facultatif ; aucune règle de déductibilité déduite."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

NOTE = ('Répartition documentaire facultative en jours calendaires inclusifs, choisie par l’utilisateur. '
    'Le montant déjà comptabilisé, sa base et la période sont déclarés ; aucun rapprochement automatique avec une facture. '
    'Ce calcul ne détermine ni TVA ni déductibilité fiscale. Vérifiez que cette convention décrit votre contrat. '
    'La part non reportée est un complément arithmétique, pas une qualification du résultat comptable. '
    'Aucune écriture créée ou validée ici. Conservez cette feuille avec les pièces réelles ; elle n’est pas archivée automatiquement.')


class ProrataIn(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: Literal['cca','pca']
    reference: str = Field(min_length=1,max_length=80)
    montant: Decimal
    base: Literal['ht','ttc','autre']
    date_debut: date
    date_fin: date
    convention: Literal['jours_calendaires_inclusifs']

    @field_validator('reference')
    @classmethod
    def reference_explicite(cls,v):
        if not v.strip():raise ValueError('Référence documentaire requise pour cette feuille de calcul.')
        return v.strip()

    @field_validator('montant',mode='before')
    @classmethod
    def montant_explicite(cls,v):
        if isinstance(v,bool):raise ValueError('Montant numérique requis.')
        return v

    @field_validator('montant')
    @classmethod
    def montant_au_centime(cls,v):
        if not v.is_finite() or v <= 0 or v >= Decimal('1e16'):
            raise ValueError('Montant positif fini inférieur à 10 000 000 000 000 000 MAD requis.')
        if v != v.quantize(Decimal('.01')):raise ValueError('Le montant déjà comptabilisé doit être saisi au centime.')
        return v

    @field_validator('date_debut','date_fin',mode='before')
    @classmethod
    def date_explicite(cls,v):
        if not isinstance(v,(str,date)):raise ValueError('Date explicite au format AAAA-MM-JJ requise.')
        return v


def calculer(faits:ProrataIn,fin_exercice:date):
    if faits.date_fin < faits.date_debut:
        raise ValueError('La fin de la période doit suivre son début.')
    total=(faits.date_fin-faits.date_debut).days+1
    futurs=0 if fin_exercice >= faits.date_fin else total if fin_exercice < faits.date_debut else (faits.date_fin-fin_exercice).days
    with localcontext() as ctx:
        ctx.prec=50
        reporte=(faits.montant*Decimal(futurs)/Decimal(total)).quantize(Decimal('.01'),rounding=ROUND_HALF_UP)
        non_reporte=faits.montant-reporte
    montant=format(faits.montant,'.2f');report=format(reporte,'.2f')
    base={'ht':'HT','ttc':'TTC','autre':'base déclarée autre'}[faits.base]
    libelle=(f'{faits.type.upper()} — {faits.reference} — {montant} MAD {base} ; '
        f'{faits.date_debut} au {faits.date_fin} ; après {fin_exercice} : {futurs}/{total} jours ; {report} MAD')
    return {'faits':{**faits.model_dump(mode='json'),'montant':montant},
        'date_fin_exercice':fin_exercice.isoformat(),'jours_total':total,'jours_apres_cloture':futurs,
        'montant_reporte':report,'montant_non_reporte':format(non_reporte,'.2f'),
        'arrondi':'Au centime, demi au supérieur', 'libelle_propose':libelle,'note':NOTE}
