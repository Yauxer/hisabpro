"""Repérage interne HisabPro ; aucun changement aux codes ou aux archives ETIC."""
import json
from pathlib import Path

NUMEROTATION_INTERNE = json.loads(
    Path(__file__).with_name("liasse_numerotation_interne.json").read_text(encoding="utf-8")
)
NOTE_NUMEROTATION = "T1 à T25 : numérotation interne HisabPro, distincte de la codification DGI. Codes ETIC d'origine conservés."


def numero_tableau(code):
    """Code inconnu/ancien conservé, sans inventer de nouveau numéro."""
    return NUMEROTATION_INTERNE.get(code, code or "")


def reference_etic(code):
    numero = numero_tableau(code)
    return f"{numero} / {code}" if numero != code else (code or "")
