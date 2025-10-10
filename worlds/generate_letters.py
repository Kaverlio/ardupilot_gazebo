#!/usr/bin/env python3
import random
import math

def generate_letter_models():
    """Generate letter models distributed across the map"""
    letters_xml = ""

    # Define letters to use
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
               'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

    # Colors palette (RGB values)
    colors = [
        (1, 0, 0),      # Red
        (0, 1, 0),      # Green
        (0, 0, 1),      # Blue
        (1, 1, 0),      # Yellow
        (1, 0, 1),      # Magenta
        (0, 1, 1),      # Cyan
        (1, 0.5, 0),    # Orange
        (0.5, 0, 1),    # Purple
        (0, 0.5, 0),    # Dark Green
        (0.5, 0.5, 0),  # Olive
        (1, 0.3, 0.3),  # Light Red
        (0.3, 1, 0.3),  # Light Green
        (0.3, 0.3, 1),  # Light Blue
        (0.7, 0.7, 0),  # Dark Yellow
        (0, 0.7, 0.7),  # Dark Cyan
    ]

    letter_id = 0

    # 1. Add letters to the center landing pad area (within radius 3)
    for angle in range(0, 360, 30):  # 12 letters around the circle
        rad = math.radians(angle)
        r = 2.0  # radius from center
        x = r * math.cos(rad)
        y = r * math.sin(rad)

        letter = random.choice(letters)
        color = random.choice(colors)
        size = random.uniform(0.2, 0.4)
        rotation = random.uniform(0, 2*math.pi)

        letters_xml += f"""
    <!-- Letter {letter} on landing pad -->
    <model name="letter_pad_{letter_id}">
      <static>true</static>
      <pose>{x:.2f} {y:.2f} 0.02 0 0 {rotation:.2f}</pose>
      <link name="link">
        <visual name="visual">
          <geometry>
            <box>
              <size>{size} {size*0.1} 0.005</size>
            </box>
          </geometry>
          <material>
            <ambient>{color[0]} {color[1]} {color[2]} 1</ambient>
            <diffuse>{color[0]} {color[1]} {color[2]} 1</diffuse>
            <emissive>{color[0]*0.2} {color[1]*0.2} {color[2]*0.2} 1</emissive>
          </material>
        </visual>
      </link>
    </model>"""
        letter_id += 1

    # 2. Create a dense grid of letters across the entire map
    # Cover area from -15 to +15 in both X and Y (30x30 = 900 sq meters)
    # With ~10 letters per sq meter = 9000 letters (too many!)
    # Let's do 2-3 letters per sq meter for performance = ~2700 letters

    grid_spacing = 0.7  # meters between letters
    for x in range(-15, 16):
        for y in range(-15, 16):
            # Skip the center landing pad area
            if math.sqrt(x*x + y*y) < 3.5:
                continue

            # Add 2-3 random letters per square meter
            num_letters = random.randint(2, 3)
            for _ in range(num_letters):
                # Random offset within the grid cell
                offset_x = random.uniform(-0.4, 0.4)
                offset_y = random.uniform(-0.4, 0.4)
                pos_x = x + offset_x
                pos_y = y + offset_y

                letter = random.choice(letters)
                color = random.choice(colors)
                size = random.uniform(0.1, 0.35)
                height = 0.003 + random.uniform(0, 0.01)  # Slight height variation
                rotation = random.uniform(0, 2*math.pi)

                # Create letter as a simple colored box (representing the letter)
                letters_xml += f"""
    <model name="letter_{letter}_{letter_id}">
      <static>true</static>
      <pose>{pos_x:.2f} {pos_y:.2f} {height:.3f} 0 0 {rotation:.3f}</pose>
      <link name="link">
        <visual name="visual">
          <geometry>
            <box>
              <size>{size:.2f} {size*0.15:.2f} 0.002</size>
            </box>
          </geometry>
          <material>
            <ambient>{color[0]:.1f} {color[1]:.1f} {color[2]:.1f} 1</ambient>
            <diffuse>{color[0]:.1f} {color[1]:.1f} {color[2]:.1f} 1</diffuse>
            <specular>0.1 0.1 0.1 1</specular>
          </material>
        </visual>"""

                # Add a second visual element to make it more letter-like
                if letter in ['A', 'H', 'I', 'T', 'L', 'F', 'E']:
                    # Add a perpendicular bar for these letters
                    letters_xml += f"""
        <visual name="visual2">
          <pose>0 0 0.001 0 0 1.57</pose>
          <geometry>
            <box>
              <size>{size*0.8:.2f} {size*0.1:.2f} 0.001</size>
            </box>
          </geometry>
          <material>
            <ambient>{color[0]:.1f} {color[1]:.1f} {color[2]:.1f} 1</ambient>
            <diffuse>{color[0]:.1f} {color[1]:.1f} {color[2]:.1f} 1</diffuse>
          </material>
        </visual>"""
                elif letter in ['O', 'Q', 'C', 'G']:
                    # Make these letters circular
                    letters_xml += f"""
        <visual name="visual2">
          <pose>0 0 0 0 0 0</pose>
          <geometry>
            <cylinder>
              <radius>{size*0.4:.2f}</radius>
              <length>0.002</length>
            </cylinder>
          </geometry>
          <material>
            <ambient>{color[0]:.1f} {color[1]:.1f} {color[2]:.1f} 1</ambient>
            <diffuse>{color[0]:.1f} {color[1]:.1f} {color[2]:.1f} 1</diffuse>
          </material>
        </visual>"""

                letters_xml += """
      </link>
    </model>"""
                letter_id += 1

    return letters_xml

# Generate the letter models
letter_models = generate_letter_models()

# Output just the models (to be inserted into the world file)
print(f"Generated {letter_models.count('model name=')} letter models")
print("\n<!-- LETTER MODELS START -->")
print(letter_models)
print("<!-- LETTER MODELS END -->")

# Save to a file
with open('/home/wintery/Projects/gazebo/worlds/letter_models.xml', 'w') as f:
    f.write(letter_models)

print("\nLetter models saved to letter_models.xml")