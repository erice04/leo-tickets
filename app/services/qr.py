import base64
import io

import qrcode


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


def generate_qr(data: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
