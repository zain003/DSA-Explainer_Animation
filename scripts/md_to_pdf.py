"""Convert docs/REPORT.md -> REPORT.html and print PDF via Edge."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "docs" / "REPORT.md"
HTML = ROOT / "docs" / "REPORT.html"
PDF = ROOT / "docs" / "REPORT.pdf"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

CSS = """
body { font-family: Segoe UI, Arial, sans-serif; font-size: 11pt; line-height: 1.45;
       color: #111; max-width: 800px; margin: 24px auto; padding: 0 16px; }
h1 { font-size: 20pt; } h2 { font-size: 14pt; margin-top: 1.4em; } h3 { font-size: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; }
th, td { border: 1px solid #444; padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #eee; }
code, pre { font-family: Consolas, monospace; font-size: 9.5pt; }
pre { background: #f5f5f5; padding: 10px; white-space: pre-wrap; }
a { color: #0645ad; }
"""


def main() -> None:
    md = MD.read_text(encoding="utf-8")
    body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Project Report: Data Structure Explainer</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>"
    )
    HTML.write_text(html, encoding="utf-8")
    print(f"html_bytes={len(html)} has_zain={'Zain Ali Khan' in html}")

    if not EDGE.exists():
        raise SystemExit(f"Edge not found: {EDGE}")

    uri = HTML.resolve().as_uri()
    cmd = [
        str(EDGE),
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF}",
        uri,
    ]
    subprocess.run(cmd, check=False)
    time.sleep(2)
    print(f"pdf_bytes={PDF.stat().st_size} path={PDF}")


if __name__ == "__main__":
    main()
