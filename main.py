import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches
import math
import time
from matplotlib.collections import PatchCollection
import random

def load_asteroids(filename):
    """Load asteroid data from a file, auto-generating IDs if they don't exist"""
    asteroids = []
    with open("asteroid.txt", 'r') as file:
        # Check if first line is a header by looking for non-numeric values
        first_line = file.readline().strip()
        parts = first_line.split()
        
        has_header = False
        has_ids = False
        
        # Check if first line is a header
        if any(not part.replace('.', '', 1).replace('-', '', 1).isdigit() for part in parts):
            has_header = True
        else:
            # Not a header, rewind to start of file
            file.seek(0)
        
        # Check if data includes IDs by counting columns in the first data line
        if has_header:
            first_data_line = file.readline().strip().split()
            # If we have 6 or more columns and first column is likely an ID
            has_ids = len(first_data_line) >= 6 and first_data_line[0].isdigit()
            file.seek(0)
            if has_header:
                next(file)  # Skip header again
        else:
            # Check first actual data line
            first_data_line = parts
            has_ids = len(first_data_line) >= 6 and first_data_line[0].isdigit()
        
        # Process the data
        asteroid_id = 1  # Start auto-generated IDs at 1
        for line in file:
            parts = line.strip().split()
            if len(parts) < 5:  # Need at least 5 columns for x, y, radius, vx, vy
                continue
                
            if has_ids:
                # Data already has IDs
                asteroid = {
                    'id': int(parts[0]),
                    'x': float(parts[1]),
                    'y': float(parts[2]),
                    'radius': float(parts[3]),
                    'vx': float(parts[4]),
                    'vy': float(parts[5])
                }
            else:
                # Auto-generate IDs
                asteroid = {
                    'id': asteroid_id,
                    'x': float(parts[0]),
                    'y': float(parts[1]),
                    'radius': float(parts[2]),
                    'vx': float(parts[3]),
                    'vy': float(parts[4])
                }
                asteroid_id += 1
            
            asteroids.append(asteroid)
    
    # Convert to dictionary with ID as key
    asteroids_by_id = {a['id']: a for a in asteroids}
    return asteroids_by_id

def check_collision(a1, a2):
    """Check if two asteroids are currently colliding"""
    dist = math.sqrt((a1['x'] - a2['x'])**2 + (a1['y'] - a2['y'])**2)
    return dist < (a1['radius'] + a2['radius'])

def calculate_positions(asteroids_by_id, t):
    """Calculate positions of all asteroids at time t"""
    current_positions = {}
    for asteroid_id, asteroid in asteroids_by_id.items():
        current = asteroid.copy()
        current['x'] = current['x'] + current['vx'] * t
        current['y'] = current['y'] + current['vy'] * t
        current_positions[asteroid_id] = current
    return current_positions

def simulate_collisions(asteroids_by_id, duration=10.0, time_step=0.1):
    """
    Simulate asteroid movement and detect all collisions at each time step
    Returns a list of collisions formatted as [time, id1, id2]
    """
    collisions_list = []
    asteroid_ids = sorted(asteroids_by_id.keys())
    
    # Simulate for the specified duration using fixed time steps
    for t in np.arange(0, duration + time_step, time_step):
        t = round(t, 1)  # Round to one decimal place
        
        # Calculate positions at this time step
        current_positions = calculate_positions(asteroids_by_id, t)
        
        # Check for collisions between all pairs at this timestamp
        for i, id1 in enumerate(asteroid_ids):
            for j, id2 in enumerate(asteroid_ids[i+1:], i+1):
                a1 = current_positions[id1]
                a2 = current_positions[id2]
                
                # Always report smaller ID first for consistency
                if id1 > id2:
                    id1, id2 = id2, id1
                    a1, a2 = a2, a1
                
                # Check if they're colliding
                if check_collision(a1, a2):
                    collisions_list.append([t, id1, id2])
    
    return collisions_list

def generate_asteroid_shape(radius, irregularity=0.4):
    """Generate an irregular polygon representing an asteroid"""
    num_points = random.randint(6, 12)  # Random number of points for the asteroid
    angles = np.linspace(0, 2*np.pi, num_points, endpoint=False)
    
    # Add some randomness to the angles to make it more irregular
    angles += np.random.uniform(-0.2, 0.2, num_points)
    
    # Generate radii with variation
    radii = np.random.uniform(radius * (1-irregularity), radius * (1+irregularity), num_points)
    
    # Convert to cartesian coordinates
    x = radii * np.cos(angles)
    y = radii * np.sin(angles)
    
    return np.column_stack([x, y])

def animate_asteroids(asteroids_by_id, collisions, duration=10.0, time_step=0.1):
    """Create an animation of the asteroid simulation with collision highlights"""
    # Find the bounds of the animation
    all_positions = []
    for t in np.arange(0, duration + time_step, time_step):
        positions = calculate_positions(asteroids_by_id, t)
        all_x = [a['x'] for a in positions.values()]
        all_y = [a['y'] for a in positions.values()]
        all_positions.append((all_x, all_y))
    
    # Calculate bounds with some padding
    flat_x = [x for pos in all_positions for x in pos[0]]
    flat_y = [y for pos in all_positions for y in pos[1]]
    max_radius = max(a['radius'] for a in asteroids_by_id.values())
    
    x_min, x_max = min(flat_x) - max_radius * 2, max(flat_x) + max_radius * 2
    y_min, y_max = min(flat_y) - max_radius * 2, max(flat_y) + max_radius * 2
    
    # Create a dictionary to lookup collisions by time
    collisions_by_time = {}
    for collision in collisions:
        t = collision[0]
        if t not in collisions_by_time:
            collisions_by_time[t] = []
        collisions_by_time[t].append((collision[1], collision[2]))
    
    # Set up the figure and axis with enhanced space theme
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('black')
    ax.set_facecolor('#050520')  # Deep space blue
    
    # Add stars to the background with more variation
    num_stars = 300
    star_x = np.random.uniform(x_min, x_max, num_stars)
    star_y = np.random.uniform(y_min, y_max, num_stars)
    star_sizes = np.random.uniform(0.1, 1.2, num_stars)
    star_colors = ['white', '#88CCFF', '#FFCC88']  # Different star colors
    star_color_indices = np.random.choice(range(len(star_colors)), num_stars)
    star_colors_mapped = [star_colors[i] for i in star_color_indices]
    
    # Add a distant nebula effect
    nebula_x = np.random.uniform(x_min, x_max, 50)
    nebula_y = np.random.uniform(y_min, y_max, 50)
    nebula_sizes = np.random.uniform(50, 200, 50)
    nebula_colors = ['#FF335577', '#5533FF77', '#33FF5577']  # Semi-transparent nebula colors
    nebula_color_indices = np.random.choice(range(len(nebula_colors)), 50)
    nebula_colors_mapped = [nebula_colors[i] for i in nebula_color_indices]
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    
    # No grid
    ax.grid(False)
    
    # Title and time display
    title = ax.set_title('Asteroid Belt Collision Simulation - Time: 0.0s', 
                         fontsize=16, color='white', fontweight='bold')
    
    # Legend for regular and colliding asteroids
    regular_asteroid = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#888888', 
                             markersize=10, label='Asteroid')
    collision_asteroid = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                               markersize=10, label='Collision')
    ax.legend(handles=[regular_asteroid, collision_asteroid], loc='upper right')
    
    # Pre-generate asteroid shapes for consistent rendering
    asteroid_shapes = {}
    for asteroid_id, asteroid in asteroids_by_id.items():
        asteroid_shapes[asteroid_id] = generate_asteroid_shape(asteroid['radius'])
    
    # Initialize the animation
    def init():
        return []
    
    # Animation update function
    def update(frame):
        t = round(frame * time_step, 1)
        
        # Clear previous frame
        ax.clear()
        ax.set_facecolor('#050520')
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal')
        ax.grid(False)
        
        # Add distant nebula effect
        ax.scatter(nebula_x, nebula_y, s=nebula_sizes, c=nebula_colors_mapped, alpha=0.2)
        
        # Add stars
        ax.scatter(star_x, star_y, s=star_sizes, c=star_colors_mapped, alpha=0.8)
        
        # Update title with current time
        ax.set_title(f'Asteroid Belt Collision Simulation - Time: {t:.1f}s', 
                     fontsize=16, color='white', fontweight='bold')
        
        # Reestablish legend
        ax.legend(handles=[regular_asteroid, collision_asteroid], loc='upper right')
        
        # Get current positions and check for collisions at this time
        positions = calculate_positions(asteroids_by_id, t)
        active_collisions = collisions_by_time.get(t, [])
        colliding_ids = set()
        for id1, id2 in active_collisions:
            colliding_ids.add(id1)
            colliding_ids.add(id2)
        
        # Draw all asteroids with irregular shapes
        for asteroid_id, asteroid in positions.items():
            # Get the pre-generated shape
            vertices = asteroid_shapes[asteroid_id]
            
            # Translate to current position
            translated_vertices = vertices + [asteroid['x'], asteroid['y']]
            
            if asteroid_id in colliding_ids:
                # Collision effects
                # Add explosion-like glow
                glow = plt.Circle(
                    (asteroid['x'], asteroid['y']), 
                    asteroid['radius'] * 2.5,
                    color='orange',
                    alpha=0.2
                )
                ax.add_patch(glow)
                
                # Add smaller brighter glow
                inner_glow = plt.Circle(
                    (asteroid['x'], asteroid['y']), 
                    asteroid['radius'] * 1.5,
                    color='yellow',
                    alpha=0.3
                )
                ax.add_patch(inner_glow)
                
                # The asteroid itself (red/orange during collision)
                asteroid_patch = plt.Polygon(
                    translated_vertices,
                    closed=True,
                    fc='#FF5500',
                    ec='#FFAA00',
                    alpha=0.9
                )
            else:
                # Normal asteroid with textured appearance
                # Choose a random gray-brown color for the asteroid
                asteroid_color = random.choice(['#8B7355', '#A8A8A8', '#8B795E', '#696969'])
                asteroid_patch = plt.Polygon(
                    translated_vertices,
                    closed=True,
                    fc=asteroid_color,
                    ec='#444444',
                    alpha=0.9
                )
            
            ax.add_patch(asteroid_patch)
            
            # Add ID label with better visibility
            text_shadow = ax.text(
                asteroid['x'], asteroid['y'], str(asteroid_id),
                ha='center', va='center', color='black', fontweight='bold',
                fontsize=10, zorder=10
            )
            
            ax.text(
                asteroid['x'], asteroid['y'], str(asteroid_id),
                ha='center', va='center', color='white', fontweight='bold',
                fontsize=10, zorder=11
            )
        
        # Add annotation for collisions
        if active_collisions:
            collision_text = "⚠ COLLISION DETECTED ⚠\n"
            for id1, id2 in active_collisions:
                collision_text += f"Asteroids {id1} and {id2}\n"
            ax.text(
                0.02, 0.98, 
                collision_text.strip(), 
                transform=ax.transAxes,
                verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='firebrick', alpha=0.8),
                fontsize=12, fontweight='bold', color='white'
            )
        
        return ax.get_children()
    
    # Create animation
    frames = int(duration / time_step) + 1
    anim = FuncAnimation(
        fig, 
        update, 
        frames=frames,
        init_func=init, 
        blit=False, 
        interval=100  # milliseconds between frames
    )
    
    plt.tight_layout()
    return fig, anim

def write_collisions_to_file(collisions, filename="sample_output/collisions.txt"):
    """Write collision data to an output file"""
    with open(filename, 'w') as file:
        file.write("ASTEROID COLLISION SIMULATION RESULTS\n")
        file.write("====================================\n\n")
        file.write(f"Total collisions detected: {len(collisions)}\n\n")
        file.write("Time (s) | Asteroid ID 1 | Asteroid ID 2\n")
        file.write("---------|--------------|--------------\n")
        
        for collision in collisions:
            file.write(f"{collision[0]:.1f}      | {collision[1]:12d} | {collision[2]:12d}\n")
        
        file.write("\n====================================\n")
        file.write("End of collision report")
    
    print(f"Collision data successfully written to {filename}")

def main():
    """Main function to run the simulation with visualization"""
    asteroid_filename = "asteroid.txt"  # Default to using asteroid.txt
    
    start_time = time.time()
    print(f"Loading asteroid data from {asteroid_filename}...")
    asteroids_by_id = load_asteroids(asteroid_filename)
    print(f"Loaded {len(asteroids_by_id)} asteroids.")
    
    print("Simulating asteroid movement and detecting collisions...")
    duration = 10.0
    time_step = 0.1
    collisions = simulate_collisions(asteroids_by_id, duration, time_step)
    
    print(f"\nDetected {len(collisions)} collisions within {duration} seconds.")
    
    # Write collisions to output file
    write_collisions_to_file(collisions, "sample_output/collisions.txt")
    
    # Print all collisions to console
    print("\nAll detected collisions:")
    print("Time    Asteroid IDs")
    print("-" * 20)
    for collision in collisions:
        print(f"{collision[0]:.1f}     {collision[1]} {collision[2]}")
    
    # Create animation
    print("\nCreating animation...")
    fig, anim = animate_asteroids(asteroids_by_id, collisions, duration, time_step)
    
    # Save animation as MP4 (requires ffmpeg)
    try:
        print("Saving animation as MP4...")
        anim.save('sample_output/asteroid_collision_animation.mp4', writer='ffmpeg', fps=10, dpi=100)
        print("Animation saved as 'asteroid_collision_animation.mp4'")
    except Exception as e:
        print(f"Could not save animation: {e}")
        print("You may need to install ffmpeg to save as MP4.")
    
    # Show the animation
    print("Displaying animation...")
    plt.show()
    
    end_time = time.time()
    print(f"\nSimulation completed in {end_time - start_time:.4f} seconds.")

if __name__ == "__main__":
    main()
