"""
Compte les lignes de code du projet PHARE et génère un rapport .md.
Couvre : app desktop Python + PWA (JS / HTML / CSS).
"""
from pathlib import Path

ROOT       = Path(__file__).parent
OUTPUT_MD  = ROOT / "comptage_lignes.md"

# ── Fichiers desktop Python ────────────────────────────────────────────────
PYTHON_FILES = [
    "main.py", "ui_main.py", "ui_popup.py",
    "database.py", "renfort_engine.py", "import_handler.py",
    "config.py", "version.py",
]

# ── Fichiers PWA ───────────────────────────────────────────────────────────
PWA_EXTS = {".js", ".html", ".css", ".json"}
PWA_DIR  = ROOT / "pwa"
PWA_EXCLUDE = {"manifest.json"}   # manifeste purement déclaratif


def compter(path: Path) -> int:
    with open(path, encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f)


# ── Desktop ────────────────────────────────────────────────────────────────
desktop = []
for name in PYTHON_FILES:
    p = ROOT / name
    if p.exists():
        desktop.append((name, compter(p)))

# ── PWA ───────────────────────────────────────────────────────────────────
pwa = []
for p in sorted(PWA_DIR.rglob("*")):
    if p.is_file() and p.suffix in PWA_EXTS and p.name not in PWA_EXCLUDE:
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        pwa.append((rel, compter(p)))

# ── Totaux ────────────────────────────────────────────────────────────────
total_desktop = sum(n for _, n in desktop)
total_pwa     = sum(n for _, n in pwa)
total         = total_desktop + total_pwa

# ── Rapport MD ────────────────────────────────────────────────────────────
with open(OUTPUT_MD, "w", encoding="utf-8") as md:
    from version import VERSION, BUILD
    md.write(f"# Comptage des lignes — PHARE v{VERSION}\n\n")
    md.write(f"*Build {BUILD} — {len(desktop) + len(pwa)} fichiers*\n\n")
    md.write(f"**Total projet : {total:,} lignes**\n\n")

    md.write("## Application desktop (Python)\n\n")
    md.write("| Fichier | Lignes |\n|---------|-------:|\n")
    for name, n in desktop:
        md.write(f"| `{name}` | {n:,} |\n")
    md.write(f"| **Sous-total** | **{total_desktop:,}** |\n\n")

    md.write("## PWA mobile (JS / HTML / CSS)\n\n")
    md.write("| Fichier | Lignes |\n|---------|-------:|\n")
    for name, n in pwa:
        md.write(f"| `{name}` | {n:,} |\n")
    md.write(f"| **Sous-total** | **{total_pwa:,}** |\n\n")

    md.write(f"---\n**TOTAL : {total:,} lignes**\n")

print(f"OK — {len(desktop) + len(pwa)} fichiers, {total:,} lignes.")
print(f"Rapport : {OUTPUT_MD}")
