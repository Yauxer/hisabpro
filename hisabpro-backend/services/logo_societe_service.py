"""Validation des nouveaux logos intégrés ; aucune lecture fichier ou réseau."""
import base64
import binascii
from io import BytesIO
import re

from PIL import Image, UnidentifiedImageError

MAX_LOGO_BYTES = 512 * 1024
MAX_LOGO_PIXELS = 4_000_000


def normaliser_logo(value):
    if value is None:
        return None
    value = value.strip()
    if not value:
        return ""
    if len(value) > MAX_LOGO_BYTES * 4 // 3 + 40:
        raise ValueError("Le logo doit peser au maximum 512 Ko.")
    match = re.fullmatch(r"data:image/(png|jpeg);base64,([A-Za-z0-9+/]+={0,2})", value)
    if not match:
        raise ValueError("Choisissez un logo PNG ou JPEG intégré ; les URL et chemins locaux ne sont pas acceptés.")
    try:
        raw = base64.b64decode(match[2], validate=True)
        if len(raw) > MAX_LOGO_BYTES:
            raise ValueError("Le logo doit peser au maximum 512 Ko.")
        with Image.open(BytesIO(raw)) as image:
            if image.format != {"png": "PNG", "jpeg": "JPEG"}[match[1]]:
                raise ValueError("Le contenu du logo ne correspond pas au format PNG/JPEG annoncé.")
            if image.width * image.height > MAX_LOGO_PIXELS:
                raise ValueError("Le logo doit contenir au maximum 4 millions de pixels.")
            image.verify()
        # JPEG.verify ne décode pas tous les pixels ; refuser aussi un flux
        # tronqué qui échouerait seulement lors de l'édition du PDF.
        with Image.open(BytesIO(raw)) as image:
            image.load()
    except (binascii.Error, UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("Le logo PNG/JPEG est illisible ou invalide.") from error
    return value
