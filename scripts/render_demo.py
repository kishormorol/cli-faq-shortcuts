"""Render a 24-second illustrative demo. Optional build deps: Pillow, imageio-ffmpeg.

Usage: python scripts/render_demo.py --output-dir docs/media
The extractor itself remains dependency-free. No real history is read.
"""
import argparse
import os
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, FPS, SECONDS = 1280, 720, 12, 24
BG, PANEL, TEXT, MUTED, GREEN = "#0b1220", "#111f33", "#f0f5fa", "#a6b7ca", "#70e3b0"


def font(size, bold=False, mono=False):
    base = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    choices = [base / ("consola.ttf" if mono else "segoeuib.ttf" if bold else "segoeui.ttf"),
               Path("/usr/share/fonts/truetype/dejavu") / (
                   "DejaVuSansMono.ttf" if mono else "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")]
    for path in choices:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


FONTS = {"title": font(46, bold=True), "body": font(26), "mono": font(26, mono=True),
         "small": font(19), "label": font(20, bold=True), "big": font(60, bold=True)}


def render(t):
    frame = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(frame)
    def text(x, y, value, style="body", fill=TEXT):
        d.text((x, y), value, font=FONTS[style], fill=fill)
    scene = min(int(t // 6), 3)
    elapsed = t % 6
    text(64, 34, "CLI FAQ SHORTCUTS", "label", GREEN)
    text(965, 34, "24-second walkthrough", "small", MUTED)
    titles = ["Stop retyping the same request.", "Find the asks you keep repeating.",
              "Pick a shortcut. Keep your workflow.", "Next time, just type /sent."]
    text(64, 94, titles[scene], "title")
    labels = ["01 / REPEAT", "02 / DISCOVER", "03 / CHOOSE", "04 / REUSE"]
    d.rounded_rectangle((64, 185, 1216, 559), radius=20, fill=PANEL, outline="#29415c", width=2)
    text(94, 205, labels[scene], "label", MUTED)
    d.line((94, 245, 1186, 245), fill="#29415c", width=1)
    if scene == 0:
        asks = [("MON", "Did the newsletter actually go out?"),
                ("TUE", "Did everyone get the newsletter?"),
                ("FRI", "Check delivery and show me the bounces.")]
        for i, (day, ask) in enumerate(asks):
            if elapsed >= i * 0.65:
                text(96, 276 + i * 72, day, "label", GREEN)
                text(186, 270 + i * 72, ask, "mono")
        text(96, 502, "Different words. The same recurring task.", "small", MUTED)
    elif scene == 1:
        command = "> /faq-shortcuts"
        text(96, 265, command[:max(2, int(elapsed * 24))], "mono", GREEN)
        if elapsed >= 1:
            text(96, 318, "Read project history. Group requests by intent.")
        if elapsed >= 2:
            text(96, 375, "/sent", "mono", GREEN)
            text(345, 375, "Newsletter delivery checks", "mono")
            text(1060, 375, "8 asks", "small", MUTED)
        if elapsed >= 2.7:
            text(96, 431, "/signups", "mono", GREEN)
            text(345, 431, "Weekly signup counts", "mono")
            text(1060, 431, "6 asks", "small", MUTED)
        text(96, 502, "The agent proposes shortcuts. You choose which ones to create.", "small", MUTED)
    elif scene == 2:
        text(96, 265, "> Create /sent", "mono", GREEN)
        if elapsed >= 0.8:
            text(96, 326, ".claude/skills/sent/SKILL.md", "mono")
        if elapsed >= 1.6:
            text(96, 383, "Uses your project's existing status script.")
        if elapsed >= 2.4:
            text(96, 429, "Report only. Never resend from this shortcut.", fill=GREEN)
        text(96, 502, "A small, reviewable skill file you can keep with your project.", "small", MUTED)
    else:
        text(96, 263, "> /sent", "mono", GREEN)
        if elapsed >= 0.8:
            for i, (value, label) in enumerate([("100", "SENT"), ("98", "DELIVERED"), ("2", "BOUNCED")]):
                x = 96 + i * 330
                text(x, 329, value, "big", GREEN if i != 2 else "#ffc88a")
                text(x, 410, label, "label", MUTED)
        if elapsed >= 1.7:
            text(96, 460, "Delivery report ready. No messages resent.")
        text(96, 508, "Illustrative output from a synthetic project, not a live recording.", "small", MUTED)
    text(64, 587, "Claude Code  /  Codex  /  Cursor", "body", GREEN)
    text(64, 638, "github.com/kishormorol/cli-faq-shortcuts", "small")
    text(889, 638, "Synthetic examples throughout", "small", MUTED)
    for i in range(4):
        x = 964 + i * 65
        d.rounded_rectangle((x, 596, x + 48, 602), radius=3, fill=GREEN if i <= scene else "#29415c")
    d.rectangle((0, 710, int(WIDTH * t / SECONDS), 719), fill=GREEN)
    return frame


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, default=Path("docs/media"))
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    video = args.output_dir / "faq-shortcuts-demo.mp4"
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "rawvideo",
           "-vcodec", "rawvideo", "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS),
           "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
           "-movflags", "+faststart", str(video)]
    frames = []
    with subprocess.Popen(cmd, stdin=subprocess.PIPE) as process:
        for i in range(FPS * SECONDS):
            frame = render(i / FPS)
            process.stdin.write(frame.tobytes())
            if i % 3 == 0:
                frames.append(frame.resize((960, 540)).quantize(colors=96))
        process.stdin.close()
        if process.wait() != 0:
            raise SystemExit("Video encoding failed")
    frames[0].save(args.output_dir / "faq-shortcuts-demo.gif", save_all=True,
                   append_images=frames[1:], duration=250, loop=0, optimize=True)
    render(23).save(args.output_dir / "faq-shortcuts-demo.png")
    sheet = Image.new("RGB", (1280, 720))
    for i in range(4):
        sheet.paste(render(i * 6 + 4).resize((640, 360)), ((i % 2) * 640, (i // 2) * 360))
    sheet.save(args.output_dir / "contact-sheet.png")
    print(f"Rendered {SECONDS}s / {WIDTH}x{HEIGHT} / {FPS}fps to {args.output_dir}")


if __name__ == "__main__":
    main()
