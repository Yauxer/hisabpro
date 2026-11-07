"""Réponses de validation JSON même pour une entrée numérique NaN/Infinity."""
import math

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse


def _valeurs_json(value):
    # Les nombres non finis d'une requête ne sont jamais des nombres JSON
    # valides. Les conserver dans le détail Pydantic ferait échouer la réponse
    # 422 elle-même ; leur représentation textuelle conserve le diagnostic.
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    if isinstance(value, dict):
        return {key: _valeurs_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_valeurs_json(item) for item in value]
    return value


async def erreur_validation_json(request, exc):
    erreurs=exc.errors()
    if request.url.path.startswith('/api/employes/personnel'):
        # Une validation ne doit jamais réémettre un RIB ou un corps Personnel.
        erreurs=[{k:e[k] for k in ('loc','msg','type') if k in e} for e in erreurs]
        for e in erreurs:
            if e.get('type')=='union_tag_invalid':e['msg']='Type de proposition Personnel non reconnu.'
            if e.get('type')=='extra_forbidden' and e.get('loc'):e['loc']=(*e['loc'][:-1],'champ_inattendu')
    return JSONResponse(status_code=422,
                        content={"detail": _valeurs_json(jsonable_encoder(erreurs))})
