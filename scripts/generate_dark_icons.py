"""Generate missing '-dark' icon variants by copying the base icon file.

This script will scan src/web/static/icons for files named
'icon-<name>.svg' and create 'icon-<name>-dark.svg' if it doesn't exist.
"""
from pathlib import Path

ICONS_DIR = Path(__file__).resolve().parents[1] / 'src' / 'web' / 'static' / 'icons'

if __name__ == '__main__':
    created = 0
    for p in ICONS_DIR.glob('icon-*.svg'):
        name = p.stem  # e.g. icon-services or icon-services-light
        # skip variant files
        if name.endswith('-light') or name.endswith('-glow') or name.endswith('-dark'):
            continue
        dark_name = ICONS_DIR / f"{name}-dark.svg"
        if not dark_name.exists():
            print(f"Creating {dark_name.name} from {p.name}")
            dark_name.write_bytes(p.read_bytes())
            created += 1
    print(f"Done. Created {created} dark icons.")
