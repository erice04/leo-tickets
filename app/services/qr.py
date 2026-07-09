import base64
import io
from pathlib import Path

import qrcode
from PIL import Image

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "leo-logo.png"
BOX_SIZE = 10
# Fraction of data modules cleared for the logo (high EC allows ~30% coverage).
LOGO_MODULE_FRACTION = 0.28
QR_BORDER = 2


def get_cipher():
    letters = "abcdefghijklmnopqrstuvwxyz0123456789@.-"
    shuffled_letters = list("dbu2tn1g8mjepzi3wr74xay5h.l-@6v9sofk0qc")
    return {letters[i]: shuffled_letters[i] for i in range(len(letters))}


def qr_encode(plaintext: str) -> str:
    cipher = get_cipher()
    return "".join(cipher.get(char.lower(), char) for char in plaintext)


def qr_decode(encoded_text: str) -> str:
    cipher = get_cipher()
    inverse_cipher = {v: k for k, v in cipher.items()}
    return "".join(inverse_cipher.get(char, char) for char in encoded_text)


def _load_logo(logo_bytes: bytes | None = None) -> Image.Image | None:
    if logo_bytes:
        return Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
    if LOGO_PATH.is_file():
        return Image.open(LOGO_PATH).convert("RGBA")
    return None


def _prepare_logo(logo: Image.Image) -> Image.Image:
    """Trim transparent margins so the artwork centers correctly."""
    alpha = logo.split()[-1]
    bbox = alpha.getbbox()
    if bbox:
        logo = logo.crop(bbox)
    return logo


def _symmetric_clear_modules(data_modules: int, requested: int) -> int:
    """Pick a clear size with equal margin on all sides of the data matrix."""
    clear = max(3, min(requested, data_modules))
    if (data_modules - clear) % 2 != 0:
        if clear + 1 <= data_modules:
            clear += 1
        else:
            clear -= 1
    return clear


def _clear_center_modules(modules: list[list[bool]], clear_modules: int) -> int:
    """Blank center QR modules before render so no black dots remain at the edges."""
    n = len(modules)
    clear_modules = max(3, min(clear_modules, n))
    start = (n - clear_modules) // 2
    end = start + clear_modules
    for row in range(start, end):
        for col in range(start, end):
            modules[row][col] = False
    return clear_modules


def _cleared_zone_center(
    *,
    clear_modules: int,
    data_modules: int,
    box_size: int,
    border: int,
) -> tuple[int, int]:
    start = (data_modules - clear_modules) // 2
    left = (border + start) * box_size
    top = (border + start) * box_size
    zone_px = clear_modules * box_size
    return left + zone_px // 2, top + zone_px // 2


def _embed_logo(
    qr_img: Image.Image,
    logo: Image.Image,
    *,
    clear_modules: int,
    data_modules: int,
    box_size: int = BOX_SIZE,
    border: int = QR_BORDER,
) -> Image.Image:
    qr_img = qr_img.convert("RGB")
    logo = _prepare_logo(logo)
    zone_px = clear_modules * box_size
    logo_max = int(zone_px * 0.82)
    logo.thumbnail((logo_max, logo_max), Image.Resampling.LANCZOS)

    cx, cy = _cleared_zone_center(
        clear_modules=clear_modules,
        data_modules=data_modules,
        box_size=box_size,
        border=border,
    )
    qr_img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
    return qr_img


def generate_qr(
    data: str,
    logo_bytes: bytes | None = None,
    *,
    embed_logo: bool = True,
) -> str:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=BOX_SIZE,
        border=QR_BORDER,
    )
    qr.add_data(data)
    qr.make(fit=True)

    logo = _load_logo(logo_bytes) if embed_logo else None
    clear_modules = 0
    data_modules = len(qr.modules)
    if logo is not None:
        requested = max(7, min(data_modules - 6, int(data_modules * LOGO_MODULE_FRACTION)))
        clear_modules = _symmetric_clear_modules(data_modules, requested)
        clear_modules = _clear_center_modules(qr.modules, clear_modules)

    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    if logo is not None:
        img = _embed_logo(
            img,
            logo,
            clear_modules=clear_modules,
            data_modules=data_modules,
            box_size=BOX_SIZE,
            border=QR_BORDER,
        )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
