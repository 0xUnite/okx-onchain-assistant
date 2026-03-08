#!/usr/bin/env python3
"""Render terminal-style PNG screenshots from captured CLI outputs."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "submission_assets" / "raw_outputs"
OUT_DIR = ROOT / "submission_assets" / "screenshots"

FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
]

SCREENSHOTS = [
    (
        "01_precheck.txt",
        "01_precheck.png",
        "$ python3 ai_assistant/main.py precheck ETH USDC 1 ethereum 0x742d35Cc6634C0532925a3b844Bc9e7595f",
    ),
    (
        "02_simulate.txt",
        "02_simulate.png",
        "$ python3 ai_assistant/main.py simulate ETH USDC 1 ethereum 0x742d35Cc6634C0532925a3b844Bc9e7595f",
    ),
    (
        "03_private.txt",
        "03_private.png",
        "$ python3 ai_assistant/main.py private ethereum 5000 0.8",
    ),
    (
        "04_revoke_dryrun.txt",
        "04_revoke_dryrun.png",
        "$ python3 ai_assistant/main.py revoke 0x742d35Cc6634C0532925a3b844Bc9e7595f ethereum",
    ),
    (
        "05_painkiller_demo.txt",
        "05_painkiller_demo.png",
        "$ python3 painkiller_demo.py --wallet 0x742d35Cc6634C0532925a3b844Bc9e7595f --chain ethereum",
    ),
]


def load_font(size: int = 22) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def render(content: str, out_path: Path, title: str, font: ImageFont.FreeTypeFont) -> None:
    lines = content.replace("\t", "    ").splitlines() or [""]

    pad_x = 28
    pad_y = 24
    top_bar_h = 44
    line_h = int(font.size * 1.45)

    max_line = max(lines, key=len)
    text_w = int(font.getlength(max_line))
    width = max(1200, min(2100, text_w + pad_x * 2))
    height = top_bar_h + pad_y * 2 + line_h * len(lines)

    img = Image.new("RGB", (width, height), "#0d1117")
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.rectangle((0, 0, width, top_bar_h), fill="#161b22")
    draw.ellipse((14, 14, 26, 26), fill="#ff5f57")
    draw.ellipse((34, 14, 46, 26), fill="#febc2e")
    draw.ellipse((54, 14, 66, 26), fill="#28c840")
    draw.text((86, 12), title, fill="#8b949e", font=font)

    y = top_bar_h + pad_y
    for line in lines:
        draw.text((pad_x, y), line, fill="#e6edf3", font=font)
        y += line_h

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def main() -> None:
    font = load_font()
    for raw_name, out_name, command in SCREENSHOTS:
        raw_path = RAW_DIR / raw_name
        if not raw_path.exists():
            continue
        output = raw_path.read_text(encoding="utf-8", errors="replace").strip("\n")
        text = f"{command}\n\n{output}"
        render(text, OUT_DIR / out_name, "OKX Onchain Assistant - Real Run", font)
        print(f"generated: {OUT_DIR / out_name}")


if __name__ == "__main__":
    main()
