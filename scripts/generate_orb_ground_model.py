#!/usr/bin/env python3
"""Generate ground model SDF with 100 unique ORB-optimized tiles in a 10x10 grid."""

def generate_model_sdf():
    """Generate the model.sdf file content with 100 unique tiles."""

    sdf_content = """<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="orb_optimized_ground">
    <static>true</static>
    <link name="ground_link">
      <pose>0 0 0 0 0 0</pose>
      <collision name="collision">
        <geometry>
          <plane>
            <normal>0 0 1</normal>
            <size>100 100</size>
          </plane>
        </geometry>
        <surface>
          <friction>
            <ode>
              <mu>1.0</mu>
              <mu2>1.0</mu2>
            </ode>
          </friction>
        </surface>
      </collision>
"""

    # Generate visual elements for 100 unique tiles in a 10x10 grid
    tile_size = 10.0  # Each tile covers 10x10 meters
    grid_size = 10    # 10x10 grid

    tile_id = 0
    for row in range(grid_size):
        for col in range(grid_size):
            # Calculate position (centered around origin)
            x_pos = -45.0 + col * tile_size
            y_pos = -45.0 + row * tile_size

            # No rotation needed - each texture is already unique
            rotation = 0

            sdf_content += f"""      <visual name="tile_{row:02d}_{col:02d}">
        <pose>{x_pos:.3f} {y_pos:.3f} 0.001 0 0 {rotation:.5f}</pose>
        <cast_shadows>false</cast_shadows>
        <geometry>
          <plane>
            <normal>0 0 1</normal>
            <size>{tile_size} {tile_size}</size>
          </plane>
        </geometry>
        <material>
          <script>
            <uri>file:///home/wintery/Projects/gazebo/models/orb_optimized_ground/materials/scripts</uri>
            <uri>file:///home/wintery/Projects/gazebo/models/orb_optimized_ground/materials/textures</uri>
            <name>ORBOptimized/Tile{tile_id:03d}</name>
          </script>
        </material>
      </visual>
"""
            tile_id += 1

    sdf_content += """    </link>
  </model>
</sdf>
"""

    return sdf_content

def generate_model_config():
    """Generate the model.config file content."""

    config_content = """<?xml version="1.0"?>
<model>
  <name>orb_optimized_ground</name>
  <version>1.0</version>
  <sdf version="1.6">model.sdf</sdf>

  <author>
    <name>ORB Texture Generator</name>
    <email>noreply@example.com</email>
  </author>

  <description>
    Ground plane with 100 unique textures specifically optimized for ORB feature detection.
    Each tile contains unique patterns including QR-like structures, geometric shapes,
    text markers, checkerboards, and high-contrast features ideal for visual SLAM.
  </description>
</model>"""

    return config_content

if __name__ == "__main__":
    # Generate model.sdf
    sdf_content = generate_model_sdf()
    sdf_file = "/home/wintery/Projects/gazebo/models/orb_optimized_ground/model.sdf"
    with open(sdf_file, 'w') as f:
        f.write(sdf_content)
    print(f"Generated model.sdf with 100 unique tiles in {sdf_file}")

    # Generate model.config
    config_content = generate_model_config()
    config_file = "/home/wintery/Projects/gazebo/models/orb_optimized_ground/model.config"
    with open(config_file, 'w') as f:
        f.write(config_content)
    print(f"Generated model.config in {config_file}")