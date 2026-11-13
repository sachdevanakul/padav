"""Polyomino helpers + SVG drawing for PIA visual items. Everything is computed, so answer keys are correct by construction."""
from __future__ import annotations

import random
from typing import Iterable

Cells = frozenset  # frozenset[tuple[int, int]]
INK, PAPER, GRID, MUTED = "#1f2937", "#ffffff", "#9ca3af", "#6b7280"


def norm(cells: Iterable[tuple[int, int]]) -> Cells:
    cells = list(cells)
    mx, my = min(x for x, _ in cells), min(y for _, y in cells)
    return frozenset((x - mx, y - my) for x, y in cells)


def rot(cells: Cells, k: int = 1) -> Cells:
    for _ in range(k % 4):
        cells = norm((-y, x) for x, y in cells)
    return cells


def flip(cells: Cells) -> Cells:
    return norm((-x, y) for x, y in cells)


def rotations(cells: Cells) -> set[Cells]:
    return {rot(cells, k) for k in range(4)}


def congruent(a: Cells, b: Cells) -> bool:
    return norm(b) in rotations(a) | rotations(flip(a))


def chiral(cells: Cells) -> bool:
    return flip(cells) not in rotations(cells)


def connected(cells: Cells) -> bool:
    todo, seen = [next(iter(cells))], set()
    while todo:
        x, y = todo.pop()
        if (x, y) in seen:
            continue
        seen.add((x, y))
        todo += [c for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)) if c in cells]
    return seen == set(cells)


def free_polyominoes(n: int) -> list[Cells]:
    """All free polyominoes with n cells (one per congruence class)."""
    shapes = {frozenset({(0, 0)})}
    for _ in range(n - 1):
        grown = set()
        for s in shapes:
            for x, y in s:
                for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if c not in s:
                        grown.add(norm(s | {c}))
        shapes = grown
    out: list[Cells] = []
    for s in sorted(shapes, key=sorted):
        if not any(congruent(s, t) for t in out):
            out.append(s)
    return out


def near_misses(shape: Cells) -> list[Cells]:
    """Connected shapes of the same size made by moving one cell; not congruent to the original."""
    out: list[Cells] = []
    for cell in shape:
        rest = shape - {cell}
        for x, y in rest:
            for c in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if c in rest or c == cell:
                    continue
                cand = norm(rest | {c})
                if connected(cand) and not congruent(cand, shape) and not any(congruent(cand, o) for o in out):
                    out.append(cand)
    return out


def shuffled_options(correct, distractors, rng: random.Random):
    options = [correct, *distractors]
    rng.shuffle(options)
    return options, "abcd"[options.index(correct)]


# ---- drawing ----------------------------------------------------------------------------------------------------
def svg_wrap(width: int, height: int, body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
            f'font-family="Arial, Helvetica, sans-serif" role="img"><title>{title}</title>'
            f'<rect width="{width}" height="{height}" fill="{PAPER}"/>{body}</svg>')


def poly(cells: Cells, x0: float, y0: float, s: float, fill: str = INK) -> str:
    return "".join(f'<rect x="{x0 + x * s:.1f}" y="{y0 + y * s:.1f}" width="{s:.1f}" height="{s:.1f}" fill="{fill}" stroke="{PAPER}" stroke-width="2"/>' for x, y in sorted(cells))


def extent(cells: Cells) -> tuple[int, int]:
    return max(x for x, _ in cells) + 1, max(y for _, y in cells) + 1


def label(text: str, x: float, y: float, size: int = 16, anchor: str = "middle", fill: str = INK) -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="700" text-anchor="{anchor}" fill="{fill}">{text}</text>'


def option_row(options: list[Cells], top: float, width: int, s: float) -> str:
    slot = width / 4
    out = []
    for i, shape in enumerate(options):
        w, h = extent(shape)
        cx = slot * i + slot / 2
        out.append(f'<rect x="{slot * i + 10:.1f}" y="{top:.1f}" width="{slot - 20:.1f}" height="{6 * s + 40:.1f}" rx="10" fill="none" stroke="{GRID}"/>')
        out.append(poly(shape, cx - w * s / 2, top + 20 + (6 * s - h * s) / 2, s))
        out.append(label("ABCD"[i], cx, top + 6 * s + 34, 15))
    return "".join(out)


def shape_question_svg(target: Cells, options: list[Cells], title: str, caption: str) -> str:
    width, s = 720, 22
    w, h = extent(target)
    body = label(caption, width / 2, 28, 15, fill=MUTED) + poly(target, width / 2 - w * s / 2, 48 + (6 * s - h * s) / 2, s)
    body += option_row(options, 48 + 6 * s + 24, width, s)
    return svg_wrap(width, int(48 + 6 * s + 24 + 6 * s + 50), body, title)


def fit_question_svg(board_w: int, board_h: int, hole: Cells, hole_at: tuple[int, int], options: list[Cells], title: str, caption: str) -> str:
    width, s = 720, 26
    hx, hy = hole_at
    hole_abs = {(x + hx, y + hy) for x, y in hole}
    filled = {(x, y) for x in range(board_w) for y in range(board_h)} - hole_abs
    bx = width / 2 - board_w * s / 2
    body = label(caption, width / 2, 28, 15, fill=MUTED) + poly(frozenset(filled), bx, 48, s, "#4b5563")
    body += "".join(f'<rect x="{bx + x * s:.1f}" y="{48 + y * s:.1f}" width="{s}" height="{s}" fill="{PAPER}" stroke="{INK}" stroke-dasharray="4 3"/>' for x, y in hole_abs)
    top = 48 + board_h * s + 24
    slot, ps = width / 4, 22
    for i, shape in enumerate(options):
        w, h = extent(shape)
        cx = slot * i + slot / 2
        body += f'<rect x="{slot * i + 10:.1f}" y="{top:.1f}" width="{slot - 20:.1f}" height="{6 * ps + 40:.1f}" rx="10" fill="none" stroke="{GRID}"/>'
        body += poly(shape, cx - w * ps / 2, top + 20 + (6 * ps - h * ps) / 2, ps) + label("ABCD"[i], cx, top + 6 * ps + 34, 15)
    return svg_wrap(width, int(top + 6 * ps + 50), body, title)


# ---- matrix (3x3) figures --------------------------------------------------------------------------------------
def shape_svg(kind: str, cx: float, cy: float, r: float, rotation: int = 0, fill: str = INK) -> str:
    if kind == "circle":
        return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"/>'
    if kind == "square":
        return f'<rect x="{cx - r:.1f}" y="{cy - r:.1f}" width="{2 * r:.1f}" height="{2 * r:.1f}" fill="{fill}"/>'
    if kind == "triangle":
        pts = f"{cx:.1f},{cy - r:.1f} {cx + r:.1f},{cy + r:.1f} {cx - r:.1f},{cy + r:.1f}"
        return f'<polygon points="{pts}" fill="{fill}"/>'
    if kind == "diamond":
        pts = f"{cx:.1f},{cy - r:.1f} {cx + r:.1f},{cy:.1f} {cx:.1f},{cy + r:.1f} {cx - r:.1f},{cy:.1f}"
        return f'<polygon points="{pts}" fill="{fill}"/>'
    if kind == "arrow":  # asymmetric so every rotation is distinguishable
        pts = f"{cx:.1f},{cy - r:.1f} {cx + r * .8:.1f},{cy + r * .2:.1f} {cx + r * .25:.1f},{cy + r * .2:.1f} {cx + r * .25:.1f},{cy + r:.1f} {cx - r * .25:.1f},{cy + r:.1f} {cx - r * .25:.1f},{cy + r * .2:.1f} {cx - r * .8:.1f},{cy + r * .2:.1f}"
        return f'<polygon points="{pts}" fill="{fill}" transform="rotate({rotation} {cx:.1f} {cy:.1f})"/>'
    raise ValueError(kind)


def count_svg(kind: str, n: int, x: float, y: float, size: float) -> str:
    """n copies of a shape laid out inside a size x size cell."""
    r = size * 0.12
    layouts = {1: [(.5, .5)], 2: [(.3, .5), (.7, .5)], 3: [(.5, .27), (.28, .72), (.72, .72)], 4: [(.3, .3), (.7, .3), (.3, .7), (.7, .7)]}
    return "".join(shape_svg(kind, x + px * size, y + py * size, r) for px, py in layouts[n])


def bits_svg(bits: frozenset, x: float, y: float, size: float) -> str:
    c = size / 3
    return "".join(f'<rect x="{x + (i % 3) * c + 4:.1f}" y="{y + (i // 3) * c + 4:.1f}" width="{c - 8:.1f}" height="{c - 8:.1f}" fill="{INK}"/>' for i in sorted(bits))


def matrix_svg(cell_draw, option_draw, title: str, caption: str) -> str:
    """cell_draw(row, col, x, y, size) -> svg for the 8 given cells; option_draw(i, x, y, size) -> svg."""
    width, size = 560, 120
    left = (width - 3 * size) / 2
    body = label(caption, width / 2, 26, 14, fill=MUTED)
    for r in range(3):
        for c in range(3):
            x, y = left + c * size, 40 + r * size
            body += f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="{GRID}"/>'
            if (r, c) == (2, 2):
                body += label("?", x + size / 2, y + size / 2 + 14, 42, fill=MUTED)
            else:
                body += cell_draw(r, c, x, y, size)
    top, osz = 40 + 3 * size + 24, 100
    slot = width / 4
    for i in range(4):
        x = slot * i + (slot - osz) / 2
        body += f'<rect x="{x}" y="{top}" width="{osz}" height="{osz}" fill="none" stroke="{GRID}"/>' + option_draw(i, x, top, osz)
        body += label("ABCD"[i], x + osz / 2, top + osz + 24, 15)
    return svg_wrap(width, int(top + osz + 40), body, title)
