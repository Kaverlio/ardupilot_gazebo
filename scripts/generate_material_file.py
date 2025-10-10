#!/usr/bin/env python3
"""Generate material definitions for ORB-optimized textures."""

def generate_material_file(num_tiles=100):
    """Generate material file content for all tiles."""

    material_content = """// ORB-optimized ground textures
// Each material represents a unique tile with features specifically designed for ORB feature detection

"""

    for i in range(num_tiles):
        material_content += f"""material ORBOptimized/Tile{i:03d}
{{
  technique
  {{
    pass
    {{
      ambient 0.95 0.95 0.95 1.0
      diffuse 1.0 1.0 1.0 1.0
      specular 0.02 0.02 0.02 1.0 5

      texture_unit
      {{
        texture orb_tile_{i:03d}.png
        filtering anisotropic
        anisotropy 16
      }}
    }}
  }}
}}

"""

    return material_content

if __name__ == "__main__":
    content = generate_material_file(100)

    output_file = "/home/wintery/Projects/gazebo/models/orb_optimized_ground/materials/scripts/orb_optimized.material"
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"Generated material definitions for 100 tiles in {output_file}")