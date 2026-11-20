# -*- coding: utf-8 -*-
"""
confetti_generator.py
Copyright (c) 2026 Vincenzo Iannone — MIT License

Generative art with controlled quadrilateral angles (80°-100°)
and configurable radius bounds proportional to vertex distance.

Ogni "coriandolo" è un quadrilatero quasi rettangolare a cui viene
sottratta l'unione dei cerchi centrati sui suoi vertici.

Uso rapido:
    python confetti_generator.py                       # mostra a schermo
    python confetti_generator.py -o opera.png          # salva su file
    python confetti_generator.py --palette vaporwave --seed 42 -o opera.png
    python confetti_generator.py --list-palettes
"""

import argparse
import random

import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
PALETTES = {
    "bauhaus":     ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51'],  # Bauhaus Contemporaneo
    "bauhaus-classic": ['#E63946', '#F1FAEE', '#A8DADC', '#457B9D', '#1D3557'],  # Bauhaus Classico
    "industrial":  ['#2B2B2B', '#7F8C8D', '#BDC3C7', '#E5E7E9', '#000000'],  # Minimalismo Industriale
    "vaporwave":   ['#5E48E8', '#00CFFA', '#FF00A6', '#4900FF', '#BC13FE'],  # Vaporwave Notturno
    "arid":        ['#BC6C25', '#DDA15E', '#FEFAE0', '#606C38', '#283618'],  # Arido Organico
}

BACKGROUND = '#F5F5F0'  # Carta avorio


def create_confetti(offset_x, offset_y, scale=1.0, r_min=0.55, r_max=0.80):
    """
    Genera un singolo coriandolo complesso in una posizione specifica.

    Parameters
    ----------
    offset_x, offset_y : float
        Centro del coriandolo nella canvas.
    scale : float
        Scala generale della forma.
    r_min : float
        Bound inferiore del raggio, proporzionale alla distanza dal centro (0.0–1.0).
    r_max : float
        Bound superiore del raggio, proporzionale alla distanza dal centro (0.0–1.0).

    Note sui valori consigliati
    ---------------------------
    r_min >= 0.4, r_max <= 0.95
    Con bounds stretti (es. 0.55–0.80) le forme sono più regolari e meno casuali.
    Esempi:
        r_min=0.40, r_max=0.95  →  comportamento originale, forme molto variabili
        r_min=0.55, r_max=0.80  →  default consigliato, bilanciato
        r_min=0.60, r_max=0.70  →  forme quasi costanti, molto geometriche
        r_min=0.70, r_max=0.90  →  cerchi grandi → forme sottili/filiformi
        r_min=0.40, r_max=0.55  →  cerchi piccoli → forme piene e compatte
    """
    d = scale * 5

    # ------------------------------------------------------------------
    # 1. Costruzione del quadrilatero con angoli vincolati tra 80° e 100°
    # ------------------------------------------------------------------
    # Partiamo da un rettangolo e perturbiamo i vertici in due componenti:
    #   - Radiale  (lungo la diagonale dal centro): non altera gli angoli
    #   - Tangenziale (perpendicolare alla diagonale): altera gli angoli,
    #     limitata a tan(10°) ≈ 0.176 × distanza per restare entro ±10° da 90°

    w = random.uniform(d * 0.5, d)
    h = random.uniform(d * 0.5, d)
    theta = random.uniform(0, 2 * np.pi)  # rotazione globale casuale

    base_corners = np.array([
        [ w / 2,  h / 2],
        [-w / 2,  h / 2],
        [-w / 2, -h / 2],
        [ w / 2, -h / 2]
    ])

    perturbed = []
    for corner in base_corners:
        direction = corner / np.linalg.norm(corner)          # versore radiale
        tangent   = np.array([-direction[1], direction[0]])  # versore tangenziale

        dist = np.linalg.norm(corner)
        max_radial     = d * 0.15
        max_tangential = dist * np.tan(np.radians(10)) * 0.5  # garantisce ±10° max

        radial_perturb     = random.uniform(-max_radial, max_radial)
        tangential_perturb = random.uniform(-max_tangential, max_tangential)

        new_corner = corner + direction * radial_perturb + tangent * tangential_perturb
        perturbed.append(new_corner)

    # Rotazione globale del quadrilatero
    rot = np.array([[np.cos(theta), -np.sin(theta)],
                    [np.sin(theta),  np.cos(theta)]])
    rotated = [rot @ p for p in perturbed]

    # Traslazione al centro (offset_x, offset_y)
    centers = [(offset_x + p[0], offset_y + p[1]) for p in rotated]

    # ------------------------------------------------------------------
    # 2. Generazione dei cerchi con raggio proporzionale e bounds stretti
    # ------------------------------------------------------------------
    # Clamp di sicurezza: hi sempre > lo di almeno 0.05
    lo = max(0.0, min(r_min, 0.99))
    hi = max(lo + 0.05, min(r_max, 1.0))

    circles = []
    for cx, cy in centers:
        dist = np.sqrt((cx - offset_x) ** 2 + (cy - offset_y) ** 2)
        r = random.uniform(dist * lo, dist * hi)
        circles.append(Point(cx, cy).buffer(r))

    # ------------------------------------------------------------------
    # 3. Forma finale = quadrilatero − unione dei cerchi
    # ------------------------------------------------------------------
    quad        = Polygon(centers)
    all_circles = unary_union(circles)
    return quad.difference(all_circles)


def render_artwork(num_elements=300, r_min=0.55, r_max=0.80,
                   palette="bauhaus", seed=None, output=None, dpi=200):
    """
    Genera l'opera generativa e la mostra a schermo o la salva su file.

    Parameters
    ----------
    num_elements : int
        Numero di coriandoli da disegnare.
    r_min, r_max : float
        Bounds del raggio (passati a create_confetti).
    palette : str
        Nome di una palette in PALETTES.
    seed : int or None
        Seme del generatore casuale: stesso seed → stessa immagine.
    output : str or None
        Percorso del file da salvare (png, svg, pdf...). Se None, mostra a schermo.
    dpi : int
        Risoluzione per i formati raster.
    """
    if seed is not None:
        random.seed(seed)

    colors = PALETTES[palette]

    fig, ax = plt.subplots(figsize=(12, 12), facecolor=BACKGROUND)
    ax.set_aspect('equal')

    for _ in range(num_elements):
        ox    = random.uniform(-50, 50)
        oy    = random.uniform(-50, 50)
        scale = random.uniform(0.5, 2.0)

        shape = create_confetti(ox, oy, scale, r_min=r_min, r_max=r_max)

        if not shape.is_empty:
            color = random.choice(colors)
            alpha = random.uniform(0.6, 0.9)

            # Gestione MultiPolygon (se il coriandolo si spezza in più parti)
            geoms = [shape] if isinstance(shape, Polygon) else shape.geoms
            for poly in geoms:
                x, y = poly.exterior.xy
                ax.fill(x, y, color=color, alpha=alpha, ec='white', lw=0.5)

    ax.axis('off')
    plt.tight_layout()

    if output:
        fig.savefig(output, dpi=dpi, facecolor=BACKGROUND)
        plt.close(fig)
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Generative 'confetti': quadrilaterals minus circles on their vertices.")
    parser.add_argument("-n", "--num", type=int, default=300,
                        help="number of confetti (default: 300)")
    parser.add_argument("--r-min", type=float, default=0.55,
                        help="lower radius bound, fraction of vertex distance (default: 0.55)")
    parser.add_argument("--r-max", type=float, default=0.80,
                        help="upper radius bound, fraction of vertex distance (default: 0.80)")
    parser.add_argument("-p", "--palette", choices=PALETTES.keys(), default="bauhaus",
                        help="color palette (default: bauhaus)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="random seed for reproducible output")
    parser.add_argument("-o", "--output", default=None,
                        help="save to file (png, svg, pdf...) instead of showing")
    parser.add_argument("--dpi", type=int, default=200, help="output resolution (default: 200)")
    parser.add_argument("--list-palettes", action="store_true", help="list palettes and exit")
    args = parser.parse_args()

    if args.list_palettes:
        for name, cols in PALETTES.items():
            print(f"{name:16s} {' '.join(cols)}")
        return

    render_artwork(args.num, r_min=args.r_min, r_max=args.r_max,
                   palette=args.palette, seed=args.seed,
                   output=args.output, dpi=args.dpi)


if __name__ == "__main__":
    main()
