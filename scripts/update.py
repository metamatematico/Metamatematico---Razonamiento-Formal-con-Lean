"""
update.py — Actualizador de METAMATEMÁTICO
==========================================
Comprueba si hay nuevas versiones en GitHub y aplica la actualización.

Uso:
    python scripts/update.py            # comprueba y pregunta
    python scripts/update.py --yes      # actualiza sin preguntar
    python scripts/update.py --check    # solo comprueba, no actualiza
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd: list[str], **kw) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", **kw)
    return r.returncode, (r.stdout + r.stderr).strip()


def git(*args) -> tuple[int, str]:
    return run(["git"] + list(args))


def main():
    parser = argparse.ArgumentParser(description="Actualizador de METAMATEMÁTICO")
    parser.add_argument("--yes",   action="store_true", help="Actualizar sin confirmar")
    parser.add_argument("--check", action="store_true", help="Solo verificar, no actualizar")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║    METAMATEMÁTICO — Actualizador         ║")
    print("╚══════════════════════════════════════════╝\n")

    # Versión actual
    _, sha   = git("rev-parse", "--short", "HEAD")
    _, msg   = git("log", "--oneline", "-1")
    print(f"Versión actual : {sha}  —  {msg}\n")

    # Fetch
    print("Consultando GitHub…", end=" ", flush=True)
    code, out = git("fetch", "origin", "main")
    if code != 0:
        print(f"✗\nError al consultar: {out}")
        sys.exit(1)
    print("ok")

    # ¿Hay commits nuevos?
    _, ahead_behind = git("rev-list", "--left-right", "--count", "HEAD...origin/main")
    try:
        behind = int(ahead_behind.split()[-1])
    except Exception:
        behind = 0

    if behind == 0:
        print("✔ El sistema está al día. No hay actualizaciones disponibles.")
        return

    # Mostrar qué hay de nuevo
    _, new_commits = git("log", "HEAD..origin/main", "--oneline")
    print(f"\n⬆  {behind} actualización(es) disponible(s):\n")
    for line in new_commits.splitlines():
        print(f"   {line}")

    if args.check:
        print("\n(modo --check: no se aplican cambios)")
        return

    # Confirmar
    if not args.yes:
        resp = input("\n¿Aplicar la actualización? [s/N] ").strip().lower()
        if resp not in ("s", "si", "sí", "y", "yes"):
            print("Cancelado.")
            return

    # git pull
    print("\nDescargando…")
    code, out = git("pull", "origin", "main")
    if code != 0:
        print(f"✗ Error en git pull:\n{out}")
        sys.exit(1)
    print(out)

    # pip install
    req = ROOT / "requirements.txt"
    if req.exists():
        print("\nActualizando dependencias Python…")
        code, out = run(
            [sys.executable, "-m", "pip", "install", "-r", str(req), "-q"],
            timeout=180,
        )
        if out:
            print(out[:600])

    # Nueva versión
    _, new_sha = git("rev-parse", "--short", "HEAD")
    _, new_msg = git("log", "--oneline", "-1")

    print(f"\n✔ Actualización completada.")
    print(f"  Nueva versión: {new_sha}  —  {new_msg}")
    print("\n▶ Reinicia la aplicación para aplicar los cambios:")
    print("  PYTHONIOENCODING=utf-8 streamlit run app.py\n")


if __name__ == "__main__":
    main()
