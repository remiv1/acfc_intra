"""Module des fonctions pour la création de visuels."""

from io import BytesIO
import base64
import qrcode

def generate_qrcode(data: str, *, size: int = 3, border: int = 1,
                    color: str = "black", back_color: str = "white") -> str:
    """Génère un QR code à partir des données fournies."""
    # Créer le QR code
    qr = qrcode.QRCode(version=1,
        error_correction=qrcode.ERROR_CORRECT_L,
        box_size=size,border=border)
    qr.add_data(data)
    qr.make(fit=True)

    # Générer l'image QR code en base64
    img = qr.make_image(fill_color=color, back_color=back_color)
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    qr_code_base64: str = base64.b64encode(buffer.getvalue()).decode()
    return qr_code_base64
