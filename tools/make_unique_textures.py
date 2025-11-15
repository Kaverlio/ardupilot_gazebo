#!/usr/bin/env python3
"""Augment existing ground_plane textures with many non-overlapping, fully filled,
high-contrast geometric figures, letters and digits."""

from __future__ import annotations

import argparse
import math
import random
from pathlib import Path
from typing import Tuple, List

from PIL import Image, ImageDraw, ImageFont

# Тепер додаємо складні фігури, літери й цифри
SHAPES = (
    "rectangle",
    "ellipse",
    "square",
    "circle",
    "rhombus",
    "triangle",
    "diamond",
    "pentagon",
    "trapezium",
    "star",
    "plus",
    "arrow",
    "letter",
    "digit",
)

# Базова палітра кольорів (яскраві + темні)
PALETTE = (
    (20, 20, 20),       # майже чорний
    (240, 240, 240),   # майже білий
    (230, 50, 50),     # червоний
    (40, 120, 255),    # синій
    (255, 160, 0),     # помаранчевий
    (0, 190, 160),     # бірюзовий
    (180, 0, 220),     # фіолетовий
)


def luminance(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def get_average_color(img: Image.Image, box: Tuple[int, int, int, int]) -> Tuple[int, int, int]:
    region = img.crop(box)
    region_small = region.resize((1, 1))
    return region_small.getpixel((0, 0))


def pick_contrasting_color_for_bg(
    bg: Tuple[int, int, int],
    rng: random.Random,
    min_diff: float = 80.0,
) -> Tuple[int, int, int]:
    """Обирає колір з палітри, який максимально відрізняється по яскравості від фону."""
    bg_l = luminance(bg)

    # спочатку пробуємо знайти колір, який перевищує поріг
    candidates = []
    for c in PALETTE:
        diff = abs(luminance(c) - bg_l)
        if diff >= min_diff:
            candidates.append((diff, c))

    if candidates:
        # випадковий з тих, що проходять поріг
        return rng.choice(candidates)[1]

    # якщо жоден не проходить поріг — беремо той, який максимально відрізняється
    best = max(PALETTE, key=lambda c: abs(luminance(c) - bg_l))
    return best


def clamped_box(cx: int, cy: int, w: int, h: int, width: int, height: int) -> Tuple[int, int, int, int]:
    half_w = w // 2
    half_h = h // 2
    left = max(0, min(width - w, cx - half_w))
    top = max(0, min(height - h, cy - half_h))
    return left, top, left + w, top + h


def regular_polygon(
    cx: int,
    cy: int,
    radius: float,
    sides: int,
    rotation: float,
) -> Tuple[Tuple[float, float], ...]:
    points = []
    for i in range(sides):
        angle = rotation + 2 * math.pi * i / sides
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        points.append((x, y))
    return tuple(points)


def bbox_from_points(points: Tuple[Tuple[float, float], ...]) -> Tuple[int, int, int, int]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))


def boxes_intersect(a: Tuple[int, int, int, int], b: Tuple[int, int, int, int], margin: int = 2) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ax1 -= margin
    ay1 -= margin
    ax2 += margin
    ay2 += margin
    bx1 -= margin
    by1 -= margin
    bx2 += margin
    by2 += margin
    return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    # Пробуємо DejaVuSans, якщо ні – падаємо на стандартний шрифт
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size=size)
    except Exception:
        return ImageFont.load_default()


def draw_shape_on_image(
    img: Image.Image,
    shape: str,
    rng: random.Random,
    placed_boxes: List[Tuple[int, int, int, int]],
    min_size: int = 40,
    max_size: int = 60,
    max_attempts: int = 120,
) -> bool:
    """Малює одну фігуру на зображенні без перекриття інших. Повертає True, якщо вдалося розмістити."""
    width, height = img.size
    draw = ImageDraw.Draw(img)

    for _ in range(max_attempts):
        cx = rng.randint(min_size, width - min_size)
        cy = rng.randint(min_size, height - min_size)

        # Розміри фігури
        size = rng.randint(min_size, max_size)

        # Попередньо будуватимемо полігон або box, щоби мати bbox
        pts = None
        box = None

        if shape == "rectangle":
            w = size
            h = rng.randint(min_size, max_size)
            box = clamped_box(cx, cy, w, h, width, height)
            bbox = box

        elif shape == "ellipse" or shape == "circle":
            if shape == "circle":
                w = h = size
            else:
                w = size
                h = rng.randint(min_size, max_size)
            box = clamped_box(cx, cy, w, h, width, height)
            bbox = box

        elif shape == "square":
            side = size
            box = clamped_box(cx, cy, side, side, width, height)
            bbox = box

        elif shape in ("triangle", "pentagon"):
            sides = 3 if shape == "triangle" else 5
            radius = size / 2
            pts = regular_polygon(cx, cy, radius, sides, rng.random() * math.pi)
            bbox = bbox_from_points(pts)

        elif shape in ("rhombus", "diamond"):
            w = size
            h = rng.randint(min_size, max_size)
            pts = (
                (cx, cy - h / 2),
                (cx + w / 2, cy),
                (cx, cy + h / 2),
                (cx - w / 2, cy),
            )
            bbox = bbox_from_points(pts)

        elif shape == "trapezium":
            top_w = size
            bottom_w = top_w + rng.randint(0, max_size // 2)
            h = rng.randint(min_size, max_size)
            pts = (
                (cx - bottom_w / 2, cy + h / 2),
                (cx + bottom_w / 2, cy + h / 2),
                (cx + top_w / 2, cy - h / 2),
                (cx - top_w / 2, cy - h / 2),
            )
            bbox = bbox_from_points(pts)

        elif shape == "star":
            outer = size / 2
            inner = outer * 0.5
            num_points = 5
            pts_list = []
            for i in range(num_points * 2):
                ang = math.pi / 2 + i * math.pi / num_points
                r = outer if i % 2 == 0 else inner
                x = cx + r * math.cos(ang)
                y = cy - r * math.sin(ang)
                pts_list.append((x, y))
            pts = tuple(pts_list)
            bbox = bbox_from_points(pts)

        elif shape == "plus":
            arm = size / 2
            thickness = max(min_size / 4, size / 5)
            t = thickness
            pts = (
                (cx - t / 2, cy - arm),
                (cx + t / 2, cy - arm),
                (cx + t / 2, cy - t / 2),
                (cx + arm, cy - t / 2),
                (cx + arm, cy + t / 2),
                (cx + t / 2, cy + t / 2),
                (cx + t / 2, cy + arm),
                (cx - t / 2, cy + arm),
                (cx - t / 2, cy + t / 2),
                (cx - arm, cy + t / 2),
                (cx - arm, cy - t / 2),
                (cx - t / 2, cy - t / 2),
            )
            bbox = bbox_from_points(pts)

        elif shape == "arrow":
            # Простенька стрілка вправо
            w = size
            h = rng.randint(min_size, max_size)
            left = cx - w / 2
            right = cx + w / 2
            top = cy - h / 2
            bottom = cy + h / 2
            mid_y = cy
            pts = (
                (left, top + h * 0.25),
                (cx, top + h * 0.25),
                (cx, top),
                (right, mid_y),
                (cx, bottom),
                (cx, bottom - h * 0.25),
                (left, bottom - h * 0.25),
            )
            bbox = bbox_from_points(pts)

        elif shape in ("letter", "digit"):
            # квадратна область під символ
            side = size
            box = clamped_box(cx, cy, side, side, width, height)
            bbox = box

        else:
            # невідомий тип – скіпаємо
            continue

        # Перевірка на межі зображення
        x1, y1, x2, y2 = bbox
        if x2 <= 0 or y2 <= 0 or x1 >= width or y1 >= height:
            continue

        # Перевірка на перекриття з уже розміщеними фігурами
        if any(boxes_intersect(bbox, b) for b in placed_boxes):
            continue

        # Підбираємо контрастний колір відносно середнього фону цієї області
        bg = get_average_color(img, bbox)
        color = pick_contrasting_color_for_bg(bg, rng)

        # Тепер реально малюємо фігуру — ВСЕ СУЦІЛЬНО ЗАЛИТО
        if shape in ("rectangle", "square"):
            draw.rectangle(box, fill=color)
        elif shape in ("ellipse", "circle"):
            draw.ellipse(box, fill=color)
        elif shape in ("triangle", "pentagon", "rhombus", "diamond", "trapezium", "star", "plus", "arrow"):
            draw.polygon(pts, fill=color)
        elif shape in ("letter", "digit"):
            x1, y1, x2, y2 = box
            w_box = x2 - x1
            h_box = y2 - y1

            tile = Image.new("RGBA", (w_box, h_box), (0, 0, 0, 0))
            tdraw = ImageDraw.Draw(tile)

            if shape == "letter":
                char = chr(rng.randint(ord("A"), ord("Z")))
            else:
                char = str(rng.randint(0, 9))

            font_size = int(min(w_box, h_box) * 0.8)
            font = load_font(max(font_size, 10))

            # Центрований текст
            tw, th = tdraw.textsize(char, font=font)
            tx = (w_box - tw) // 2
            ty = (h_box - th) // 2

            tdraw.text((tx, ty), char, font=font, fill=color)

            img.paste(tile.convert("RGB"), (x1, y1), tile)

        placed_boxes.append(bbox)
        return True

    # Не вдалося розмістити цю фігуру без перекриття
    return False


def augment_image(
    img_path: Path,
    rng: random.Random,
    min_shapes: int,
    max_shapes: int,
) -> Image.Image:
    img = Image.open(img_path).convert("RGB")

    # Кількість фігур: в 4 рази більше, ніж було (було 4–9 → тепер десь 16–36)
    num_shapes = rng.randint(min_shapes, max_shapes)

    placed_boxes: List[Tuple[int, int, int, int]] = []

    for _ in range(num_shapes):
        shape = rng.choice(SHAPES)
        draw_shape_on_image(img, shape, rng, placed_boxes)

    return img


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seed", type=int, default=2024, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--min-shapes",
        type=int,
        default=20,  # було 4 → тепер у 4 рази більше за замовчуванням
        help="Minimum number of shapes per texture",
    )
    parser.add_argument(
        "--max-shapes",
        type=int,
        default=40,
        help="Maximum number of shapes per texture",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    textures_dir = repo_root / "models" / "ground_plane_unique" / "materials" / "textures"
    out_dir = textures_dir / "textures_augmented"
    out_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)

    png_files = sorted(textures_dir.glob("*.png"))
    if not png_files:
        print(f"No PNG files found in {textures_dir}")
        return

    for img_path in png_files:
        print(f"Augmenting {img_path.name}...")
        out_img = augment_image(img_path, rng, args.min_shapes, args.max_shapes)
        out_path = out_dir / img_path.name
        out_img.save(out_path, "PNG")


if __name__ == "__main__":
    main()