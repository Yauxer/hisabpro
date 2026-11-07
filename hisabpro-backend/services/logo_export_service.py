"""Logo intégré des documents ; jamais de lecture réseau ni de chemin historique."""
import base64
from io import BytesIO
from services.logo_societe_service import normaliser_logo


def image_logo(societe):
    valeur = societe.get('logo_url') if isinstance(societe, dict) else getattr(societe, 'logo_url', None)
    try:
        valeur = normaliser_logo(valeur)
        return BytesIO(base64.b64decode(valeur.split(',', 1)[1], validate=True)) if valeur else None
    except (ValueError, TypeError, AttributeError):
        # Les anciens logos incompatibles ne doivent pas empêcher un export.
        return None


def logo_pdf(societe):
    from reportlab.lib.units import mm
    from reportlab.platypus import Image
    image = image_logo(societe)
    return Image(image, width=27*mm, height=14*mm, kind='proportional') if image else None


def ajouter_logo_pdf(story, societe):
    from reportlab.lib.units import mm
    from reportlab.platypus import Spacer
    logo = logo_pdf(societe)
    if logo:
        logo.hAlign = 'LEFT'
        story[:0] = [logo, Spacer(1, 3*mm)]


def ajouter_logo_xlsx(workbook, societe):
    """Image hors des cellules de données : une feuille d'identité dédiée."""
    from openpyxl.drawing.image import Image
    image = image_logo(societe)
    if image:
        sheet = workbook.create_sheet('Logo société', 0)
        sheet['A1'] = 'Logo de la société'
        sheet['A2'] = str(societe.get('raison_sociale') or '') if isinstance(societe, dict) else str(getattr(societe, 'raison_sociale', '') or '')
        sheet['A2'].data_type = 's'
        logo = Image(image)
        ratio = min(240 / logo.width, 120 / logo.height)
        logo.width *= ratio
        logo.height *= ratio
        sheet.add_image(logo, 'A4')
        sheet.column_dimensions['A'].width = 45
