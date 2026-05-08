"""Generate Projectizer.app icon as both .icns (macOS) and .ico (Windows).

Run from the project root:
    .venv/bin/python scripts/generate-icon.py
or via run.sh's bundled venv:
    Projectizer.app/Contents/Resources/.venv/bin/python scripts/generate-icon.py

Outputs:
  Projectizer.app/Contents/Resources/icon.icns   (referenced by Info.plist)
  icon.ico                                        (for Windows shortcuts)
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Pillow not installed. Run inside the venv: pip install Pillow")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_RES = PROJECT_ROOT / "Projectizer.app" / "Contents" / "Resources"

SIZE = 1024
RADIUS = int(SIZE * 0.22)            # macOS Big Sur+ corner radius (~22.4%)
ACCENT = (108, 92, 231, 255)         # #6c5ce7
ACCENT_LIGHT = (138, 122, 240, 255)  # #8a7af0


def find_bold_font(size: int) -> ImageFont.FreeTypeFont:
    """Pick a heavy/bold sans-serif from common system locations."""
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def make_master_png() -> Image.Image:
    """Create the 1024x1024 master icon with rounded rect + bold 'P'."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded-rect base in brand purple.
    draw.rounded_rectangle((0, 0, SIZE - 1, SIZE - 1), radius=RADIUS, fill=ACCENT)

    # Bold letter "P" centered, optically nudged.
    font = find_bold_font(int(SIZE * 0.62))
    text = "P"
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (SIZE - text_w) // 2 - bbox[0]
    y = (SIZE - text_h) // 2 - bbox[1] - int(SIZE * 0.02)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return img


def write_icns(master: Image.Image, out_path: Path) -> None:
    """Build .icns via macOS iconutil from a temporary .iconset directory."""
    if not shutil.which("iconutil"):
        print("iconutil not found (macOS only); skipping .icns generation", file=sys.stderr)
        return

    iconset = out_path.with_suffix(".iconset")
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir(parents=True)

    # Apple's required filenames for iconutil
    sizes = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]
    for size, name in sizes:
        master.resize((size, size), Image.LANCZOS).save(iconset / name, "PNG")

    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(out_path)], check=True)
    shutil.rmtree(iconset)
    print(f"Wrote {out_path}")


def write_ico(master: Image.Image, out_path: Path) -> None:
    """Multi-resolution .ico for Windows."""
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    master.save(out_path, format="ICO", sizes=sizes)
    print(f"Wrote {out_path}")


def main() -> None:
    APP_RES.mkdir(parents=True, exist_ok=True)
    master = make_master_png()

    # Save the master PNG too — handy for previews / re-generation.
    master_png = PROJECT_ROOT / "icon.png"
    master.save(master_png, "PNG")
    print(f"Wrote {master_png}")

    write_icns(master, APP_RES / "icon.icns")
    write_ico(master, PROJECT_ROOT / "icon.ico")


if __name__ == "__main__":
    main()
