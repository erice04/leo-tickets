import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "frontend" / "src" / "assets"
SRC = Path(
    r"C:\Users\erlin\.cursor\projects\c-Users-erlin-OneDrive-Desktop-LEO-tickets\assets"
    r"\c__Users_erlin_AppData_Roaming_Cursor_User_workspaceStorage_895bdb42e4eab50bb2bdc1644ff327ba_images_"
    r"square-format-postage-stamp-vector-outline-frame-perforated-edges-border-339419245-"
    r"87c1d34b-c4d8-4836-a488-f6e0523105b7.png"
)


def is_white(arr: np.ndarray) -> np.ndarray:
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return (r > 235) & (g > 235) & (b > 235)


def is_dark_line(arr: np.ndarray) -> np.ndarray:
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return (r < 90) & (g < 90) & (b < 90)


def main() -> None:
    arr = np.array(Image.open(SRC).convert("RGBA"))
    h, w = arr.shape[:2]

    # Drop dreamstime footer band.
    arr = arr[: int(h * 0.88)].copy()
    h, w = arr.shape[:2]

    white = is_white(arr[..., :3])
    arr[white, 3] = 0

    alpha = arr[..., 3] > 10
    ys, xs = np.where(alpha)
    cropped = arr[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    ch, cw = cropped.shape[:2]

    dark = is_dark_line(cropped[..., :3])
    row_counts = dark.sum(axis=1)
    col_counts = dark.sum(axis=0)
    row_threshold = max(30, int(cw * 0.08))
    col_threshold = max(30, int(ch * 0.08))

    top = int(np.argmax(row_counts > row_threshold))
    bottom = ch - 1 - int(np.argmax(row_counts[::-1] > row_threshold))
    left = int(np.argmax(col_counts > col_threshold))
    right = cw - 1 - int(np.argmax(col_counts[::-1] > col_threshold))

    il, ir = left + 4, right - 4
    it, ib = top + 4, bottom - 4

    frame = cropped.copy()
    frame[it : ib + 1, il : ir + 1, 3] = 0

    target_w = 320
    scale = target_w / cw
    target_h = int(ch * scale)
    frame_img = Image.fromarray(frame).resize((target_w, target_h), Image.Resampling.LANCZOS)

    out_frame = ASSETS / "postcard-stamp-custom-frame.png"
    out_meta = ASSETS / "postcard-stamp-custom-insets.json"
    frame_img.save(out_frame, optimize=True)

    meta = {
        "logoTopPct": round(it / ch * 100, 2),
        "logoLeftPct": round(il / cw * 100, 2),
        "logoRightPct": round((cw - ir - 1) / cw * 100, 2),
        "logoBottomPct": round((ch - ib - 1) / ch * 100, 2),
        "borderColor": "#1a1a1a",
    }
    out_meta.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print("saved", out_frame.name, meta)


if __name__ == "__main__":
    main()
