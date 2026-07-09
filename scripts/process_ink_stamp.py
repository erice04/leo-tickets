from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "frontend" / "src" / "assets"
SRC = Path(
    r"C:\Users\erlin\.cursor\projects\c-Users-erlin-OneDrive-Desktop-LEO-tickets\assets"
    r"\c__Users_erlin_AppData_Roaming_Cursor_User_workspaceStorage_895bdb42e4eab50bb2bdc1644ff327ba_images_"
    r"ChatGPT_Image_Jul_8__2026__10_26_05_PM-2625533f-4271-4ee1-8500-3ce00dc06f0a.png"
)


def is_background(r: int, g: int, b: int) -> bool:
    if abs(r - g) < 15 and abs(g - b) < 15 and r > 205:
        return True
    return r > 250 and g > 250 and b > 250


def flood_background(arr: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    bg = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    r, g, b = arr[..., 0].astype(int), arr[..., 1].astype(int), arr[..., 2].astype(int)

    def seed(y: int, x: int) -> None:
        if not bg[y, x] and is_background(r[y, x], g[y, x], b[y, x]):
            bg[y, x] = True
            q.append((y, x))

    for x in range(w):
        seed(0, x)
        seed(h - 1, x)
    for y in range(h):
        seed(y, 0)
        seed(y, w - 1)

    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx]:
                if is_background(r[ny, nx], g[ny, nx], b[ny, nx]):
                    bg[ny, nx] = True
                    q.append((ny, nx))
    return bg


def main() -> None:
    arr = np.array(Image.open(SRC).convert("RGBA"))
    bg = flood_background(arr)
    arr = arr.copy()
    arr[bg, 3] = 0

    alpha = arr[..., 3] > 10
    ys, xs = np.where(alpha)
    cropped = arr[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]

    target_w = 320
    ch, cw = cropped.shape[:2]
    scale = target_w / cw
    target_h = int(ch * scale)
    out_img = Image.fromarray(cropped).resize((target_w, target_h), Image.Resampling.LANCZOS)

    out_path = ASSETS / "postcard-stamp-ink-full.png"
    out_img.save(out_path, optimize=True)
    print("saved", out_path.name, out_img.size)


if __name__ == "__main__":
    main()
