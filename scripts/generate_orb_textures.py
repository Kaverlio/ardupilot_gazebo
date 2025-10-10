#!/usr/bin/env python3
"""
Generate unique textures optimized for ORB (Oriented FAST and Rotated BRIEF) feature detection.
Each texture is completely unique with rich corner features, high contrast, and non-repeating patterns.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import random
import string
import os
from pathlib import Path

class ORBTextureGenerator:
    def __init__(self, size=512, seed=42):
        self.size = size
        random.seed(seed)
        np.random.seed(seed)

    def generate_texture(self, tile_id):
        """Generate a unique texture optimized for ORB feature detection."""
        # Create base image with textured background
        img = Image.new('RGB', (self.size, self.size), color=(180, 180, 180))
        draw = ImageDraw.Draw(img)

        # Add noise background for texture
        pixels = img.load()
        noise_intensity = 40
        for i in range(self.size):
            for j in range(self.size):
                noise = random.randint(-noise_intensity, noise_intensity)
                base_color = pixels[i, j]
                pixels[i, j] = tuple(min(255, max(0, c + noise)) for c in base_color)

        # Add unique QR-like pattern (high corner density)
        self._add_qr_pattern(draw, tile_id)

        # Add geometric shapes with high contrast
        self._add_geometric_features(draw, tile_id)

        # Add unique alphanumeric markers
        self._add_text_markers(draw, img, tile_id)

        # Add gradient circles for multi-scale features
        self._add_circles_and_arcs(draw, tile_id)

        # Add checkerboard patterns at various scales
        self._add_checkerboards(draw, tile_id)

        # Add unique line patterns
        self._add_line_patterns(draw, tile_id)

        return img

    def _add_qr_pattern(self, draw, tile_id):
        """Add QR-code-like patterns for corner detection."""
        random.seed(tile_id * 1000)

        # Create a unique QR-like pattern in one corner
        qr_size = 120
        qr_x = random.randint(20, self.size - qr_size - 20)
        qr_y = random.randint(20, self.size - qr_size - 20)
        cell_size = 8

        for i in range(qr_size // cell_size):
            for j in range(qr_size // cell_size):
                if random.random() > 0.5:
                    x = qr_x + i * cell_size
                    y = qr_y + j * cell_size
                    draw.rectangle([x, y, x + cell_size, y + cell_size],
                                 fill=(0, 0, 0) if random.random() > 0.5 else (255, 255, 255))

    def _add_geometric_features(self, draw, tile_id):
        """Add geometric shapes with sharp corners."""
        random.seed(tile_id * 2000)

        # Add triangles
        for _ in range(3):
            points = []
            center_x = random.randint(50, self.size - 50)
            center_y = random.randint(50, self.size - 50)
            radius = random.randint(20, 40)
            for angle in [0, 120, 240]:
                x = center_x + radius * np.cos(np.radians(angle + tile_id * 30))
                y = center_y + radius * np.sin(np.radians(angle + tile_id * 30))
                points.append((x, y))
            color = (random.randint(0, 100), random.randint(0, 100), random.randint(0, 100))
            draw.polygon(points, fill=color, outline=(255, 255, 255), width=2)

        # Add rotated squares
        for _ in range(4):
            size = random.randint(30, 60)
            x = random.randint(size, self.size - size)
            y = random.randint(size, self.size - size)
            angle = tile_id * 15 + random.randint(0, 90)

            # Calculate rotated square corners
            corners = []
            for dx, dy in [(-size/2, -size/2), (size/2, -size/2),
                          (size/2, size/2), (-size/2, size/2)]:
                rot_x = dx * np.cos(np.radians(angle)) - dy * np.sin(np.radians(angle))
                rot_y = dx * np.sin(np.radians(angle)) + dy * np.cos(np.radians(angle))
                corners.append((x + rot_x, y + rot_y))

            fill_color = (random.choice([0, 255]), random.choice([0, 255]), random.choice([0, 255]))
            draw.polygon(corners, fill=fill_color, outline=(128, 128, 128), width=3)

    def _add_text_markers(self, draw, img, tile_id):
        """Add unique text markers for distinctive features."""
        random.seed(tile_id * 3000)

        # Generate unique ID string
        unique_id = f"T{tile_id:03d}"

        # Try to use a monospace font, fallback to default if not available
        try:
            from PIL import ImageFont
            # This will use default font
            font_size = 24
            # Using default font since we don't have specific font files
            font = None
        except:
            font = None

        # Add tile ID at multiple locations
        for i in range(3):
            x = random.randint(30, self.size - 100)
            y = random.randint(30, self.size - 50)
            text = f"{unique_id}-{i}"

            # Draw white background for text
            bbox = [x-5, y-5, x+80, y+30]
            draw.rectangle(bbox, fill=(255, 255, 255), outline=(0, 0, 0), width=2)

            # Draw text
            draw.text((x, y), text, fill=(0, 0, 0), font=font)

        # Add random alphanumeric patterns
        for _ in range(5):
            char = random.choice(string.ascii_uppercase + string.digits)
            x = random.randint(20, self.size - 40)
            y = random.randint(20, self.size - 40)
            size = random.randint(16, 32)
            draw.text((x, y), char, fill=(random.randint(0, 50), random.randint(0, 50), random.randint(0, 50)))

    def _add_circles_and_arcs(self, draw, tile_id):
        """Add circles and arcs for curved features."""
        random.seed(tile_id * 4000)

        # Add concentric circles (like target patterns)
        for _ in range(2):
            center_x = random.randint(60, self.size - 60)
            center_y = random.randint(60, self.size - 60)
            max_radius = 50

            for r in range(10, max_radius, 10):
                color = (0, 0, 0) if (r // 10) % 2 == 0 else (255, 255, 255)
                draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r],
                           outline=color, width=3)

        # Add partial arcs
        for _ in range(4):
            x = random.randint(30, self.size - 30)
            y = random.randint(30, self.size - 30)
            radius = random.randint(20, 40)
            start_angle = random.randint(0, 360)
            end_angle = start_angle + random.randint(45, 180)

            draw.arc([x - radius, y - radius, x + radius, y + radius],
                    start_angle, end_angle, fill=(random.randint(0, 100), 0, random.randint(150, 255)), width=4)

    def _add_checkerboards(self, draw, tile_id):
        """Add checkerboard patterns at different scales."""
        random.seed(tile_id * 5000)

        # Add small checkerboard regions
        for _ in range(2):
            x_start = random.randint(0, self.size - 80)
            y_start = random.randint(0, self.size - 80)
            checker_size = random.choice([8, 12, 16])
            grid_size = random.randint(4, 6)

            for i in range(grid_size):
                for j in range(grid_size):
                    x = x_start + i * checker_size
                    y = y_start + j * checker_size
                    if (i + j) % 2 == 0:
                        draw.rectangle([x, y, x + checker_size, y + checker_size],
                                     fill=(255, 255, 255), outline=(128, 128, 128))
                    else:
                        draw.rectangle([x, y, x + checker_size, y + checker_size],
                                     fill=(0, 0, 0), outline=(128, 128, 128))

    def _add_line_patterns(self, draw, tile_id):
        """Add unique line patterns and grids."""
        random.seed(tile_id * 6000)

        # Add crosshatch pattern in a region
        x_region = random.randint(50, self.size - 150)
        y_region = random.randint(50, self.size - 150)
        region_size = 80
        line_spacing = 12

        # Horizontal lines
        for i in range(0, region_size, line_spacing):
            draw.line([(x_region, y_region + i), (x_region + region_size, y_region + i)],
                     fill=(100, 100, 200), width=2)

        # Vertical lines
        for i in range(0, region_size, line_spacing):
            draw.line([(x_region + i, y_region), (x_region + i, y_region + region_size)],
                     fill=(200, 100, 100), width=2)

        # Add random star patterns (good for corner detection)
        for _ in range(3):
            center_x = random.randint(40, self.size - 40)
            center_y = random.randint(40, self.size - 40)
            num_rays = random.randint(5, 8)
            ray_length = random.randint(20, 35)

            for i in range(num_rays):
                angle = (360 / num_rays) * i + tile_id * 10
                end_x = center_x + ray_length * np.cos(np.radians(angle))
                end_y = center_y + ray_length * np.sin(np.radians(angle))
                draw.line([(center_x, center_y), (end_x, end_y)],
                         fill=(0, 0, 0), width=3)

            # Add center marker
            draw.ellipse([center_x - 5, center_y - 5, center_x + 5, center_y + 5],
                        fill=(255, 0, 0), outline=(0, 0, 0))

def generate_all_textures(num_tiles=100, output_dir='/home/wintery/Projects/gazebo/models/orb_optimized_ground/materials/textures'):
    """Generate all unique texture tiles."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    generator = ORBTextureGenerator(size=512)

    print(f"Generating {num_tiles} unique ORB-optimized textures...")

    for i in range(num_tiles):
        texture = generator.generate_texture(i)
        filename = f"orb_tile_{i:03d}.png"
        filepath = os.path.join(output_dir, filename)
        texture.save(filepath)

        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{num_tiles} textures...")

    print(f"Successfully generated {num_tiles} unique textures in {output_dir}")

if __name__ == "__main__":
    # Generate 100 completely unique tiles for a 10x10 grid
    generate_all_textures(num_tiles=100)