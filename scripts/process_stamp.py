import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "frontend" / "src" / "assets"
SRC_DIR = Path(
    r"C:\Users\erlin\.cursor\projects\c-Users-erlin-OneDrive-Desktop-LEO-tickets\assets"
)

STAMPS = {
    "vertical": SRC_DIR
    / "c__Users_erlin_AppData_Roaming_Cursor_User_workspaceStorage_895bdb42e4eab50bb2bdc1644ff327ba_images_"
    "ChatGPT_Image_Jul_8__2026__08_27_11_PM__1_-0310c82a-4f99-46a6-9364-3ae7a34d6ea9.png",
    "horizontal": SRC_DIR
    / "c__Users_erlin_AppData_Roaming_Cursor_User_workspaceStorage_895bdb42e4eab50bb2bdc1644ff327ba_images_"
    "ChatGPT_Image_Jul_8__2026__08_27_12_PM__2_-1ccb06f0-1070-4976-b061-5e22b02149b4.png",
}


def is_bg_rgb(arr: np.ndarray) -> np.ndarray:
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return (np.abs(r.astype(int) - g.astype(int)) < 10) & (
        np.abs(g.astype(int) - b.astype(int)) < 10
    ) & (r > 170)


def is_green_rgb(arr: np.ndarray) -> np.ndarray:
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    return (g > r + 15) & (g > b + 5) & (g > 70) & (r < 130) & (b < 130)


def find_border(cropped: np.ndarray) -> tuple[int, int, int, int]:
    ch, cw = cropped.shape[:2]
    green = is_green_rgb(cropped)

    margin_x = max(8, int(cw * 0.07))
    min_row_green = max(50, int(cw * 0.08))
    min_col_green = max(50, int(ch * 0.08))

    def row_span(row: np.ndarray) -> int:
        xs = np.where(row)[0]
        if len(xs) < min_row_green // 2:
            return 0
        return int(xs.max() - xs.min())

    def col_span(col: np.ndarray) -> int:
        ys = np.where(col)[0]
        if len(ys) < min_col_green // 2:
            return 0
        return int(ys.max() - ys.min())

    center_w = cw - 2 * margin_x
    min_span = int(center_w * 0.55)

    top = next(
        y
        for y in range(ch)
        if green[y, margin_x : cw - margin_x].sum() >= min_row_green
        and row_span(green[y, margin_x : cw - margin_x]) >= min_span
    )
    bottom = next(
        y
        for y in range(ch - 1, -1, -1)
        if green[y, margin_x : cw - margin_x].sum() >= min_row_green
        and row_span(green[y, margin_x : cw - margin_x]) >= min_span
    )

    band_top = top + max(4, int((bottom - top) * 0.04))
    band_bottom = bottom - max(4, int((bottom - top) * 0.04))
    band_h = band_bottom - band_top
    min_col_span = int(band_h * 0.55)

    left = next(
        x
        for x in range(cw)
        if green[band_top:band_bottom, x].sum() >= min_col_green
        and col_span(green[band_top:band_bottom, x]) >= min_col_span
    )
    right = next(
        x
        for x in range(cw - 1, -1, -1)
        if green[band_top:band_bottom, x].sum() >= min_col_green
        and col_span(green[band_top:band_bottom, x]) >= min_col_span
    )
    return left, top, right, bottom


def find_illustration_top(cropped: np.ndarray, left: int, top: int, right: int, bottom: int) -> int:
    """First row below the header text band, aligned to the inner green border."""
    margin = max(6, int((right - left) * 0.08))
    scan_left = left + margin
    scan_right = right - margin
    scan_end = top + int((bottom - top) * 0.22)

    for y in range(top + 3, scan_end):
        row = cropped[y, scan_left : scan_right + 1, :3].astype(np.int16)
        r, g, b = row[:, 0], row[:, 1], row[:, 2]
        red_text = (r > 130) & (g < 100) & (b < 100)
        dark_green_text = (g > r + 10) & (g > b + 5) & (r < 90) & (b < 90)
        cream = (r > 200) & (g > 175) & (b > 120)
        if red_text.mean() > 0.04 or dark_green_text.mean() > 0.04 or cream.mean() > 0.45:
            continue
        return max(y - 1, top + 2)

    return top + int((bottom - top) * 0.12)


def sample_border_color(cropped: np.ndarray, left: int, top: int, right: int, bottom: int) -> str:
    green = is_green_rgb(cropped)
    samples: list[np.ndarray] = []
    for y in range(top, min(top + 4, bottom)):
        for x in range(left, right + 1):
            if green[y, x]:
                samples.append(cropped[y, x, :3])
    for y in range(max(top, bottom - 3), bottom + 1):
        for x in range(left, right + 1):
            if green[y, x]:
                samples.append(cropped[y, x, :3])
    for x in range(left, min(left + 4, right)):
        for y in range(top, bottom + 1):
            if green[y, x]:
                samples.append(cropped[y, x, :3])
    for x in range(max(left, right - 3), right + 1):
        for y in range(top, bottom + 1):
            if green[y, x]:
                samples.append(cropped[y, x, :3])

    if not samples:
        return "#385129"

    avg = np.mean(samples, axis=0).astype(np.uint8)
    return "#{:02x}{:02x}{:02x}".format(int(avg[0]), int(avg[1]), int(avg[2]))


def pad_crop(arr: np.ndarray, padding: int = 3) -> np.ndarray:
    alpha = arr[..., 3] > 8
    if not alpha.any():
        return arr
    ys, xs = np.where(alpha)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    cropped = arr[y0 : y1 + 1, x0 : x1 + 1]
    ch, cw = cropped.shape[:2]
    out = np.zeros((ch + padding * 2, cw + padding * 2, 4), dtype=np.uint8)
    out[padding : padding + ch, padding : padding + cw] = cropped
    return out


def process_stamp(name: str, src: Path, target_w: int = 320) -> None:
    arr = np.array(Image.open(src).convert("RGBA"))
    out = arr.copy()
    bg = is_bg_rgb(out[..., :3])
    out[bg, 3] = 0

    cropped = pad_crop(out, padding=3)
    ch, cw = cropped.shape[:2]

    left, top, right, bottom = find_border(cropped)
    illustration_top = find_illustration_top(cropped, left, top, right, bottom)
    border_color = sample_border_color(cropped, left, top, right, bottom)

    frame = cropped.copy()
    frame[illustration_top : bottom + 1, left : right + 1, 3] = 0

    scale = target_w / cw
    target_h = int(ch * scale)
    frame_img = Image.fromarray(frame).resize((target_w, target_h), Image.Resampling.LANCZOS)
    full_img = Image.fromarray(cropped).resize((target_w, target_h), Image.Resampling.LANCZOS)

    frame_path = ASSETS / f"postcard-stamp-{name}-frame.png"
    full_path = ASSETS / f"postcard-stamp-{name}-full.png"
    meta_path = ASSETS / f"postcard-stamp-{name}-insets.json"
    frame_img.save(frame_path, optimize=True)
    full_img.save(full_path, optimize=True)

    meta = {
        "logoTopPct": round(illustration_top / ch * 100, 2),
        "logoLeftPct": round(left / cw * 100, 2),
        "logoRightPct": round((cw - right - 1) / cw * 100, 2),
        "logoBottomPct": round((ch - bottom - 1) / ch * 100, 2),
        "borderColor": border_color,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print("saved", name, frame_path.name, full_path.name, meta)


def main() -> None:
    for name, src in STAMPS.items():
        if not src.exists():
            raise FileNotFoundError(src)
        process_stamp(name, src)


if __name__ == "__main__":
    main()
