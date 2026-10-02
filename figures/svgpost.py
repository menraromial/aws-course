"""Prépare un SVG produit par pdftocairo pour être inséré dans une page.

- chaque couleur de la palette devient une variable CSS, pour que le schéma
  suive le thème clair ou sombre du site ; une couleur hors palette fait
  échouer le script ;
- les identifiants reçoivent le nom de la figure en préfixe ;
- les coordonnées sont arrondies à deux décimales (sauf dans les matrices
  de transformation, où l'arrondi décalerait les pointes de flèches) ;
- largeur et hauteur fixes retirées : la figure suit la colonne de texte.
Démarche reprise du cours « Conteneurs et Kubernetes ».

Usage : python3 svgpost.py entree.svg sortie.svg
"""
import re
import sys
from pathlib import Path

from palette import lire_palette

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB = re.compile(r"rgb\(\s*([\d.]+)%\s*,\s*([\d.]+)%\s*,\s*([\d.]+)%\s*\)")
COULEUR_ATTR = re.compile(r'(fill|stroke)=[\'"](#[0-9a-fA-F]{3,6}|rgb\([^)]*\))[\'"]')


def normaliser(h):
    h = h.upper()
    return "".join(c * 2 for c in h) if len(h) == 3 else h


def vers_hex(couleur):
    m = RGB.fullmatch(couleur.strip())
    if m:
        return "".join(f"{round(float(v) * 2.55):02X}" for v in m.groups())
    return normaliser(couleur.lstrip("#"))


def plus_proche(h, table, fichier):
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    for ref, var in table.items():
        rr, gg, bb = (int(ref[i:i + 2], 16) for i in (0, 2, 4))
        if max(abs(r - rr), abs(g - gg), abs(b - bb)) <= 2:
            return var
    sys.exit(f"{fichier} : couleur #{h} absente de palette.tsv")


def main(entree, sortie):
    svg = Path(entree).read_text()
    nom = Path(sortie).stem
    table = {c: v for _, c, v, _ in lire_palette()}
    table["000000"] = "--fig-ink"   # noir par défaut de TikZ et des icônes
    table["232F3E"] = "--fig-ink"   # bleu nuit des icônes de ressources AWS

    def attr(m):
        prop, var = m.group(1), plus_proche(vers_hex(m.group(2)), table, entree)
        return f'style="{prop}:var({var})"'

    svg = COULEUR_ATTR.sub(attr, svg)
    svg = RGB.sub(lambda m: f"var({plus_proche(vers_hex(m.group(0)), table, entree)})", svg)
    svg = HEX.sub(lambda m: f"var({plus_proche(normaliser(m.group(1)), table, entree)})", svg)
    svg = re.sub(r'style="([^"]*)"((?:\s+[\w:-]+=[\'"][^\'"]*[\'"])*)\s+style="([^"]*)"',
                 r'style="\1;\3"\2', svg)

    ids = set(re.findall(r'\bid=[\'"]([^\'"]+)[\'"]', svg))
    for i in sorted(ids, key=len, reverse=True):
        neuf = f"{nom}-{i}"
        svg = re.sub(rf'\bid=([\'"]){re.escape(i)}\1', f'id="{neuf}"', svg)
        svg = re.sub(rf'#{re.escape(i)}\b', f"#{neuf}", svg)

    morceaux = re.split(r'(transform="[^"]*")', svg)
    svg = "".join(m if m.startswith('transform="') else re.sub(r"(\d+\.\d{2})\d+", r"\1", m)
                  for m in morceaux)
    svg = re.sub(r'<svg([^>]*?)\s+width=[\'"][^\'"]*[\'"]', r"<svg\1", svg, count=1)
    svg = re.sub(r'<svg([^>]*?)\s+height=[\'"][^\'"]*[\'"]', r"<svg\1", svg, count=1)
    Path(sortie).write_text(svg)


if __name__ == "__main__":
    main(*sys.argv[1:3])
