import pygame
import random
import sys
import math

# Initialize pygame
pygame.init()

# Game constants
CELL_SIZE = 40
GRID_WIDTH = 30  # Grid width
VISIBLE_GRID_HEIGHT = 20  # Visible grid height
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = VISIBLE_GRID_HEIGHT * CELL_SIZE
FPS = 60

# Camera positioning - player will be in bottom third
CAMERA_FOLLOW_OFFSET = VISIBLE_GRID_HEIGHT * (2/3)  # Position player in bottom third

# Player movement
GRID_MOVE_COOLDOWN = 200  # Milliseconds between grid movements
PLAYER_HOP_HEIGHT = 0.3  # Maximum height of player hop in grid units
HOP_ANIMATION_DURATION = 200  # Milliseconds for hop animation

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 0, 200)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

# Game difficulty settings
DIFFICULTY = 5  # Default difficulty (1-10 scale)
MIN_CAR_SPEED = 0.02
MAX_CAR_SPEED = 0.08
CAR_DENSITY = 0.6  # 0.0 to 1.0
MAX_LANES_PER_ROAD = 3  # Maximum number of lanes per road

# Game state
player_x = int(GRID_WIDTH / 2)  # Integer grid position
player_y = 0  # Integer grid position
target_player_x = player_x  # Target position for animation
target_player_y = player_y  # Target position for animation
camera_y = -CAMERA_FOLLOW_OFFSET  # Camera position
hopping = False  # Whether player is in hopping animation
hop_start_time = 0  # When the current hop started
hop_direction = {'x': 0, 'y': 0}  # Direction of current hop
last_move_time = 0  # Time of last movement
score = 0
game_over = False
cars = []  # List to store car positions and speeds
lanes = []  # List to store lane information (y position, height, speed, etc.)
current_top_lane_y = -10  # Keep track of the topmost lane for infinite generation
current_bottom_lane_y = 10  # Keep track of the bottommost lane

# Initialize pygame display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Crossy Roads")
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 20)

def change_difficulty(new_difficulty):
    """Change the game difficulty (1-10 scale)"""
    global DIFFICULTY, MIN_CAR_SPEED, MAX_CAR_SPEED, CAR_DENSITY, MAX_LANES_PER_ROAD
    
    # Clamp difficulty between 1 and 10
    DIFFICULTY = max(1, min(10, new_difficulty))
    
    # Adjust car speed range based on difficulty
    MIN_CAR_SPEED = 0.01 + (DIFFICULTY * 0.003)  # 0.013 to 0.04
    MAX_CAR_SPEED = 0.04 + (DIFFICULTY * 0.01)   # 0.05 to 0.14
    
    # Adjust car density based on difficulty
    CAR_DENSITY = 0.3 + (DIFFICULTY * 0.05)  # 0.35 to 0.8
    
    # Adjust maximum lanes per road based on difficulty
    if DIFFICULTY >= 7:
        MAX_LANES_PER_ROAD = 5  # Allow up to 5 lanes for difficulty 7+
    else:
        MAX_LANES_PER_ROAD = min(4, 1 + (DIFFICULTY // 3))  # 1 to 4 lanes for difficulty 1-6
    
    print(f"Difficulty set to {DIFFICULTY}")
    print(f"- Car speed: {MIN_CAR_SPEED:.3f} to {MAX_CAR_SPEED:.3f}")
    print(f"- Car density: {CAR_DENSITY:.2f}")
    print(f"- Max lanes per road: {MAX_LANES_PER_ROAD}")
    
    # Return the current settings
    return {
        "difficulty": DIFFICULTY,
        "min_car_speed": MIN_CAR_SPEED,
        "max_car_speed": MAX_CAR_SPEED,
        "car_density": CAR_DENSITY,
        "max_lanes": MAX_LANES_PER_ROAD
    }

def create_lane(y_position, is_safe=False):
    """Create a new lane with properties aligned to the grid"""
    if is_safe:
        # Safe zones are exact multiples of 1 (2, 3, or 4 units high)
        lane_height = random.choice([2, 3, 4])
        
        lane = {
            'y': int(y_position),  # Ensure y-position is an integer
            'height': lane_height,
            'is_safe': True
        }
    else:
        # Roads with multiple lanes (1-MAX_LANES_PER_ROAD)
        num_lanes = random.randint(1, MAX_LANES_PER_ROAD)
        lane_height = num_lanes  # Each sub-lane is 1 unit high (aligned with grid)
        
        lane = {
            'y': int(y_position),  # Ensure y-position is an integer
            'height': lane_height,
            'is_safe': False,
            'num_lanes': num_lanes,
            'sub_lanes': []
        }
        
        # Create sub-lanes with different car directions and speeds
        for i in range(num_lanes):
            sub_lane_y = int(y_position) - i  # Integer positions for alignment
            direction = 1 if random.random() > 0.5 else -1
            
            # Assign a SINGLE speed to this lane
            speed = random.uniform(MIN_CAR_SPEED, MAX_CAR_SPEED)
            
            sub_lane = {
                'y': sub_lane_y,
                'height': 1,  # Each sub-lane is exactly 1 unit high (aligned with grid)
                'direction': direction,
                'speed': speed
            }
            lane['sub_lanes'].append(sub_lane)
    
    return lane

def create_car(x, lane_y, lane_height, speed):
    """Create a car with consistent properties"""
    car_length = random.uniform(1.0, 2.0)
    
    # Generate a fixed color for this car (that won't change)
    car_color = (
        random.randint(150, 250),
        random.randint(0, 200),
        random.randint(0, 200)
    )
    
    return {
        'x': x,
        'y': lane_y,
        'lane_y': lane_y,
        'lane_height': lane_height,
        'speed': speed,
        'length': car_length,
        'width': lane_height * 0.8,
        'color': car_color
    }

def initialize_game():
    """Initialize the game"""
    global player_x, player_y, target_player_x, target_player_y, camera_y
    global score, game_over, cars, lanes, current_top_lane_y, current_bottom_lane_y
    global hopping, hop_start_time, hop_direction, last_move_time
    
    player_x = int(GRID_WIDTH / 2)
    player_y = 5.0  # Start at position 5 (to allow room for lanes below), now a float for precise positioning
    target_player_x = player_x
    target_player_y = player_y
    camera_y = player_y - CAMERA_FOLLOW_OFFSET  # Position camera to show player in bottom third
    score = 0
    game_over = False
    hopping = False
    hop_start_time = 0
    hop_direction = {'x': 0, 'y': 0}
    last_move_time = pygame.time.get_ticks()
    cars = []
    lanes = []
    
    # Set default difficulty
    change_difficulty(DIFFICULTY)
    
    # Calculate the bottom of the visible screen
    bottom_of_screen = camera_y + VISIBLE_GRID_HEIGHT + 10  # Add extra units for margin
    
    # Create lanes starting from below the player and extending upward
    # First, create the initial safe zone where the player starts that extends beyond the screen
    initial_safe_zone_top = int(player_y) + 1  # Top of the safe zone
    safe_zone_height = bottom_of_screen - initial_safe_zone_top + 15  # Ensure it extends beyond screen (+15 for extra margin)
    
    initial_safe_zone = {
        'y': initial_safe_zone_top,  # Top of the safe zone
        'height': max(20, int(safe_zone_height)),  # Make sure it's at least 20 units high
        'is_safe': True
    }
    lanes.append(initial_safe_zone)
    current_bottom_lane_y = initial_safe_zone_top  # Set this to the top of our initial safe zone
    
    # Generate lanes below the player first (to fill the bottom of the screen)
    y = int(player_y) - 2  # Start below the player
    while y > player_y - 20:  # Generate enough lanes below
        # Create a road
        road_lane = create_lane(y, is_safe=False)
        lanes.append(road_lane)
        y -= road_lane['height']
        
        # Create a safe zone
        safe_lane = create_lane(y, is_safe=True)
        lanes.append(safe_lane)
        y -= safe_lane['height']
    
    # Update the top lane position
    current_top_lane_y = y
    
    # Add initial cars (but not in safe zones!)
    generate_cars(density_multiplier=CAR_DENSITY)
    
    # Ensure the player is positioned on a safe zone
    is_player_safe = False
    for lane in lanes:
        if lane['is_safe']:
            lane_top = lane['y']
            lane_bottom = lane_top - lane['height']
            if lane_top >= player_y >= lane_bottom:
                # Player is in a safe zone, this is good
                is_player_safe = True
                break
    
    # If player is not in a safe zone, adjust their position
    if not is_player_safe:
        # Find the nearest safe zone
        nearest_safe_y = None
        min_distance = float('inf')
        
        for lane in lanes:
            if lane['is_safe']:
                lane_mid_y = lane['y'] - lane['height'] / 2
                distance = abs(player_y - lane_mid_y)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_safe_y = lane_mid_y
        
        if nearest_safe_y is not None:
            player_y = nearest_safe_y
            target_player_y = player_y

def generate_cars(density_multiplier=1.0):
    """Generate cars for all lanes with adjustable density"""
    global cars
    
    for lane in lanes:
        if not lane['is_safe']:  # Only generate cars in road lanes
            for sub_lane in lane['sub_lanes']:
                # Get lane info
                sub_lane_y = sub_lane['y']
                sub_lane_height = sub_lane['height']
                
                # Calculate lane midpoint (center of lane)
                lane_mid_y = sub_lane_y - sub_lane_height / 2
                
                # Determine car parameters - use the lane's speed
                car_speed = sub_lane['speed'] * sub_lane['direction']
                
                # Create cars with appropriate spacing (adjusted by density multiplier)
                x = 0 if sub_lane['direction'] > 0 else GRID_WIDTH
                car_count = 0
                max_cars = int(8 * density_multiplier)  # Maximum number of cars per lane
                
                # Place cars with proper spacing
                while (0 <= x <= GRID_WIDTH) and car_count < max_cars:
                    # Skip the area where the player starts
                    if sub_lane_y < player_y + 2 and sub_lane_y > player_y - 2:
                        break
                    
                    # Only add a car with probability based on density
                    if random.random() < 0.7 * density_multiplier:
                        # Add car at this position
                        new_car = create_car(x, lane_mid_y, sub_lane_height, car_speed)
                        cars.append(new_car)
                        car_count += 1
                    
                    # Move to next position
                    if sub_lane['direction'] > 0:
                        # Cars moving right, start from left
                        gap = random.uniform(3.0, 6.0) / density_multiplier
                        x += gap
                    else:
                        # Cars moving left, start from right
                        gap = random.uniform(3.0, 6.0) / density_multiplier
                        x -= gap

def generate_new_lanes():
    """Generate new lanes as player moves up"""
    global lanes, current_top_lane_y
    
    # Check if we need to generate more lanes (generate much further ahead)
    if current_top_lane_y > camera_y - 50:  # Generate lanes 50 units ahead
        # Create new alternating lanes
        for i in range(10):  # Generate in batches of 10 pairs
            # Create a road
            road_lane = create_lane(current_top_lane_y, is_safe=False)
            lanes.append(road_lane)
            y = current_top_lane_y - road_lane['height']
            
            # Create a safe zone
            safe_lane = create_lane(y, is_safe=True)
            lanes.append(safe_lane)
            current_top_lane_y = y - safe_lane['height']
        
        # Generate cars for the new lanes
        generate_cars_for_new_lanes(density_multiplier=CAR_DENSITY)

def generate_cars_for_new_lanes(density_multiplier=1.0):
    """Generate cars specifically for newly created lanes"""
    # Find all lanes without cars and add cars to them
    for lane in lanes:
        if not lane['is_safe']:  # Only generate cars in road lanes
            # Check if this lane already has cars by looking at y-coordinate
            lane_has_cars = False
            lane_y_min = lane['y'] - lane['height']
            lane_y_max = lane['y']
            
            for car in cars:
                if lane_y_min <= car['y'] <= lane_y_max:
                    lane_has_cars = True
                    break
            
            # If no cars found in this lane, add them
            if not lane_has_cars:
                for sub_lane in lane['sub_lanes']:
                    # Get lane info
                    sub_lane_y = sub_lane['y']
                    sub_lane_height = sub_lane['height']
                    
                    # Calculate lane midpoint
                    lane_mid_y = sub_lane_y - sub_lane_height / 2
                    
                    # Determine car parameters - use the lane's speed
                    car_speed = sub_lane['speed'] * sub_lane['direction']
                    
                    # Skip generation if too close to player's starting position
                    if sub_lane_y < player_y + 2 and sub_lane_y > player_y - 2:
                        continue
                    
                    # Create cars with appropriate spacing
                    if sub_lane['direction'] > 0:  # Cars moving right
                        # Start off-screen
                        x = -3.0
                        car_count = 0
                        max_cars = int(6 * density_multiplier)
                        
                        while x < GRID_WIDTH + 3 and car_count < max_cars:
                            # Only add a car with probability based on density
                            if random.random() < 0.7 * density_multiplier:
                                new_car = create_car(x, lane_mid_y, sub_lane_height, car_speed)
                                cars.append(new_car)
                                car_count += 1
                            
                            # Add random gap
                            gap = random.uniform(4.0, 8.0) / density_multiplier
                            x += gap
                    else:  # Cars moving left
                        # Start off-screen
                        x = GRID_WIDTH + 3.0
                        car_count = 0
                        max_cars = int(6 * density_multiplier)
                        
                        while x > -3 and car_count < max_cars:
                            # Only add a car with probability based on density
                            if random.random() < 0.7 * density_multiplier:
                                new_car = create_car(x, lane_mid_y, sub_lane_height, car_speed)
                                cars.append(new_car)
                                car_count += 1
                            
                            # Add random gap
                            gap = random.uniform(4.0, 8.0) / density_multiplier
                            x -= gap

def get_input():
    """Handle pygame events and return player action in a discrete manner"""
    current_time = pygame.time.get_ticks()
    movement_ready = current_time - last_move_time >= GRID_MOVE_COOLDOWN
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                return 'Q'
            elif event.key == pygame.K_r and game_over:
                return 'R'  # Restart game
            # Difficulty adjustment keys
            elif event.key == pygame.K_1:
                change_difficulty(1)
            elif event.key == pygame.K_2:
                change_difficulty(2)
            elif event.key == pygame.K_3:
                change_difficulty(3)
            elif event.key == pygame.K_4:
                change_difficulty(4)
            elif event.key == pygame.K_5:
                change_difficulty(5)
            elif event.key == pygame.K_6:
                change_difficulty(6)
            elif event.key == pygame.K_7:
                change_difficulty(7)
            elif event.key == pygame.K_8:
                change_difficulty(8)
            elif event.key == pygame.K_9:
                change_difficulty(9)
            elif event.key == pygame.K_0:
                change_difficulty(10)
    
    # Only allow discrete movements when not currently in a hop animation and cooldown has passed
    if not hopping and movement_ready:
        keys_pressed = pygame.key.get_pressed()
        movement = {'x': 0, 'y': 0}
        
        # Only allow one direction at a time for grid-based movement
        if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
            movement['y'] = -1  # Move up one grid space
        elif keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
            movement['x'] = -1  # Move left one grid space
        elif keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
            movement['x'] = 1   # Move right one grid space
        # No backward movement allowed (commented out)
        # elif keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
        #     movement['y'] = 1   # Move down one grid space
        
        # Only return movement if any key was pressed
        if movement['x'] != 0 or movement['y'] != 0:
            return movement
    
    return None

def is_in_safe_zone(y_pos):
    """Check if a y-coordinate is in a safe zone"""
    for lane in lanes:
        if lane['is_safe'] and lane['y'] >= y_pos >= lane['y'] - lane['height']:
            return True
    return False

def update_player_position(movement):
    """Update player position in a discrete, grid-based manner with hopping animation"""
    global player_x, player_y, target_player_x, target_player_y, camera_y, score, game_over
    global hopping, hop_start_time, hop_direction, last_move_time
    
    if movement is None or game_over or isinstance(movement, str):
        return
    
    # Save current position
    old_x, old_y = player_x, player_y
    
    # Calculate new target position (grid-based)
    target_player_x = player_x + movement['x']
    target_player_y = player_y + movement['y']
    
    # Add boundary checking for grid position
    if target_player_x < 0:
        target_player_x = 0
    elif target_player_x >= GRID_WIDTH:
        target_player_x = GRID_WIDTH - 1
        
    # Check if the player is moving onto a car lane and adjust position
    if movement['y'] != 0:  # Only check for vertical movement
        for lane in lanes:
            if not lane['is_safe']:  # Check if it's a car lane
                lane_top = lane['y']
                lane_bottom = lane_top - lane['height']
                
                # Check if target position falls within this lane
                if lane_top >= target_player_y >= lane_bottom:
                    # Find the closest sub-lane midpoint
                    closest_midpoint = None
                    closest_distance = float('inf')
                    
                    for sub_lane in lane['sub_lanes']:
                        sub_lane_y = sub_lane['y']
                        sub_lane_midpoint = sub_lane_y - 0.5  # Midpoint of a sub-lane with height 1
                        
                        distance = abs(target_player_y - sub_lane_midpoint)
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_midpoint = sub_lane_midpoint
                    
                    if closest_midpoint is not None:
                        # Snap to the exact midpoint of the car lane
                        target_player_y = closest_midpoint
                    break
    
    # Start hopping animation
    hopping = True
    hop_start_time = pygame.time.get_ticks()
    hop_direction = movement.copy()
    last_move_time = hop_start_time
    
    # Update actual position
    player_x = target_player_x
    player_y = target_player_y
    
    # Update camera to keep player in view
    camera_y = player_y - CAMERA_FOLLOW_OFFSET
    
    # Update score when moving up
    if player_y < old_y:
        delta_y = old_y - player_y
        score += 10 * delta_y  # Score based on how far upward moved (10 points per grid)
    
    # Generate new lanes if player is moving up
    generate_new_lanes()

def update_hop_animation():
    """Update the hopping animation"""
    global hopping
    
    current_time = pygame.time.get_ticks()
    
    # Check if the hop animation should end
    if current_time - hop_start_time >= HOP_ANIMATION_DURATION:
        hopping = False

def get_hop_height():
    """Calculate the current hop height based on animation progress"""
    if not hopping:
        return 0
    
    current_time = pygame.time.get_ticks()
    hop_progress = (current_time - hop_start_time) / HOP_ANIMATION_DURATION
    
    # Hop height follows a sine curve (0 to 1 to 0)
    if hop_progress <= 1.0:
        return PLAYER_HOP_HEIGHT * math.sin(hop_progress * math.pi)
    else:
        return 0

def check_collision():
    """Check if player collides with any car"""
    global game_over
    
    player_radius = 0.4  # Player collision radius in grid units
    
    # First, check if player is in a car lane (not in a safe zone)
    is_in_car_lane = False
    for lane in lanes:
        if not lane['is_safe']:  # It's a car lane
            lane_top = lane['y']
            lane_bottom = lane_top - lane['height']
            
            if lane_top >= player_y >= lane_bottom:
                is_in_car_lane = True
                break
    
    # If player is not in a car lane, they can't collide with cars
    if not is_in_car_lane:
        return False
    
    for car in cars:
        # Car dimensions
        car_half_length = car['length'] / 2
        car_half_width = car['width'] / 2
        
        # Calculate distance between player and car
        dx = abs(player_x - car['x'])
        dy = abs(player_y - car['y'])
        
        # Check if distance is small enough for collision
        if dx < (car_half_length + player_radius) and dy < (car_half_width + player_radius):
            game_over = True
            output("Game Over! You were hit by a car!")
            pygame.time.delay(2000)  # Pause for 2 seconds to show message
            return True
    
    return False

def cars_will_collide(car1, car2):
    """Determine if two cars will collide if they continue their movement"""
    # Only check cars in the same lane
    if abs(car1['y'] - car2['y']) > 0.1:
        return False
    
    # Only check cars moving in the same direction
    if (car1['speed'] > 0 and car2['speed'] < 0) or (car1['speed'] < 0 and car2['speed'] > 0):
        return False
    
    car1_left = car1['x'] - car1['length'] / 2
    car1_right = car1['x'] + car1['length'] / 2
    car2_left = car2['x'] - car2['length'] / 2
    car2_right = car2['x'] + car2['length'] / 2
    
    # Check if car1 will catch up to car2
    if car1['speed'] > car2['speed']:
        # Car1 is faster and behind car2
        if car1_left < car2_right and car1['x'] < car2['x']:
            return True
    elif car1['speed'] < car2['speed']:
        # Car2 is faster and behind car1
        if car2_left < car1_right and car2['x'] < car1['x']:
            return True
    
    return False

def move_cars():
    """Move cars continuously and handle car-to-car collisions"""
    global cars
    
    # Create temp list for removals
    cars_to_remove = []
    
    # Sort cars by y position (lane) and then x position
    cars.sort(key=lambda car: (car['y'], car['x']))
    
    # First move all cars
    for car in cars:
        old_x = car['x']
        car['x'] += car['speed']
        
        # Check if car is far off-screen (for cleanup)
        if (car['y'] - camera_y > VISIBLE_GRID_HEIGHT + 5 or 
            car['y'] - camera_y < -20 or  # Keep more cars ahead of the player
            (car['speed'] > 0 and car['x'] - car['length'] > GRID_WIDTH + 5) or
            (car['speed'] < 0 and car['x'] + car['length'] < -5)):
            cars_to_remove.append(car)
            continue
    
    # Remove cars that are off-screen
    for car in cars_to_remove:
        if car in cars:
            cars.remove(car)
    
    # Handle collisions
    for i in range(len(cars)):
        car1 = cars[i]
        
        # Check for collisions with other cars in the same lane
        for j in range(len(cars)):
            if i == j:
                continue
                
            car2 = cars[j]
            
            # Only check cars in the same lane
            if abs(car1['y'] - car2['y']) > 0.1:
                continue
            
            car1_left = car1['x'] - car1['length'] / 2
            car1_right = car1['x'] + car1['length'] / 2
            car2_left = car2['x'] - car2['length'] / 2
            car2_right = car2['x'] + car2['length'] / 2
            
            # Check for overlap
            if car1_left < car2_right and car1_right > car2_left:
                # Cars are overlapping, adjust position
                if car1['speed'] > 0 and car2['speed'] > 0:
                    # Both moving right
                    if car1['x'] < car2['x']:
                        # Car1 is behind, slow it down
                        car1['x'] = car2_left - car1['length'] / 2 - 0.05
                    else:
                        # Car2 is behind, slow it down
                        car2['x'] = car1_left - car2['length'] / 2 - 0.05
                elif car1['speed'] < 0 and car2['speed'] < 0:
                    # Both moving left
                    if car1['x'] > car2['x']:
                        # Car1 is behind, slow it down
                        car1['x'] = car2_right + car1['length'] / 2 + 0.05
                    else:
                        # Car2 is behind, slow it down
                        car2['x'] = car1_right + car2['length'] / 2 + 0.05

def output(message=None):
    """Render the game to the pygame screen"""
    # Fill the background with black
    screen.fill(BLACK)
    
    # Draw lanes (roads and safe zones)
    for lane in lanes:
        lane_top = lane['y'] - camera_y
        lane_height = lane['height']
        lane_bottom = lane_top - lane_height
        
        # Skip lanes that are completely outside the visible area
        if lane_bottom > VISIBLE_GRID_HEIGHT or lane_top < 0:
            continue
        
        # Convert to screen coordinates
        screen_top = lane_top * CELL_SIZE
        screen_height = lane_height * CELL_SIZE
        
        # Draw the lane background
        lane_rect = pygame.Rect(0, screen_top - screen_height, SCREEN_WIDTH, screen_height)
        
        if lane['is_safe']:
            # Safe zone (plain green)
            pygame.draw.rect(screen, GREEN, lane_rect)
        else:
            # Road with multiple lanes (gray)
            pygame.draw.rect(screen, GRAY, lane_rect)
            
            # Draw lane dividers for multi-lane roads
            if lane.get('num_lanes', 1) > 1:
                for i in range(1, lane['num_lanes']):
                    divider_y = screen_top - (i * screen_height / lane['num_lanes'])
                    pygame.draw.line(screen, WHITE, (0, divider_y), (SCREEN_WIDTH, divider_y), 2)
            
            # Draw central yellow line for each lane
            for i in range(lane.get('num_lanes', 1)):
                central_y = screen_top - ((i + 0.5) * screen_height / lane.get('num_lanes', 1))
                for x in range(0, SCREEN_WIDTH, 40):
                    pygame.draw.line(screen, YELLOW, (x, central_y), (x + 20, central_y), 3)
    
    # Draw cars (simple rectangles)
    for car in cars:
        # Convert car position to screen coordinates
        car_screen_x = car['x'] * CELL_SIZE
        car_screen_y = (car['y'] - camera_y) * CELL_SIZE
        car_width = car['length'] * CELL_SIZE
        car_height = car['width'] * CELL_SIZE
        
        # Skip cars that are completely outside the visible area
        if car_screen_y + car_height < 0 or car_screen_y - car_height > SCREEN_HEIGHT:
            continue
        
        # Draw car body - use stored color
        car_color = car.get('color', RED)
        
        car_rect = pygame.Rect(
            car_screen_x - car_width / 2,
            car_screen_y - car_height / 2,
            car_width,
            car_height
        )
        pygame.draw.rect(screen, car_color, car_rect)
    
    # Draw player with hopping animation
    hop_height = get_hop_height()
    
    # Get actual player position for rendering (add hop height for y)
    player_screen_x = player_x * CELL_SIZE
    player_screen_y = (player_y - camera_y - hop_height) * CELL_SIZE  # Subtract hop height to make player go up
    player_radius = CELL_SIZE * 0.4
    
    # Draw player shadow (slightly transparent dark circle)
    shadow_radius = player_radius * 0.8
    shadow_surface = pygame.Surface((shadow_radius*2, shadow_radius*2), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surface, (0, 0, 0, 128), (shadow_radius, shadow_radius), shadow_radius)
    screen.blit(shadow_surface, (player_screen_x - shadow_radius, (player_y - camera_y) * CELL_SIZE - shadow_radius))
    
    # Draw player (blue circle)
    pygame.draw.circle(screen, BLUE, (player_screen_x, player_screen_y), player_radius)
    
    # Draw score and difficulty
    score_text = font.render(f"Score: {score}   Difficulty: {DIFFICULTY}/10", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Draw grid movement cooldown indicator if waiting
    current_time = pygame.time.get_ticks()
    cooldown_progress = min(1.0, (current_time - last_move_time) / GRID_MOVE_COOLDOWN)
    if cooldown_progress < 1.0:
        cooldown_width = 100
        pygame.draw.rect(screen, GRAY, (10, 40, cooldown_width, 5))
        pygame.draw.rect(screen, YELLOW, (10, 40, cooldown_width * cooldown_progress, 5))
    
    # Draw message if provided
    if message:
        message_text = font.render(message, True, YELLOW)
        text_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        # Draw a background for the message
        bg_rect = text_rect.inflate(20, 20)
        pygame.draw.rect(screen, BLACK, bg_rect)
        pygame.draw.rect(screen, WHITE, bg_rect, 2)
        screen.blit(message_text, text_rect)
    
    # Draw grid lines (for debugging lane alignment)
    if False:  # Set to True to show grid lines
        for y in range(-20, VISIBLE_GRID_HEIGHT + 20):
            grid_y = (y - camera_y % 1) * CELL_SIZE
            pygame.draw.line(screen, (50, 50, 50), (0, grid_y), (SCREEN_WIDTH, grid_y), 1)
    
    # Update display
    pygame.display.flip()

def spawn_new_cars():
    """Spawn new cars at the edges of the screen"""
    for lane in lanes:
        if not lane['is_safe']:  # Only spawn cars in road lanes
            for sub_lane in lane['sub_lanes']:
                # Get lane info
                sub_lane_y = sub_lane['y']
                sub_lane_height = sub_lane['height']
                
                # Calculate lane midpoint
                lane_mid_y = sub_lane_y - sub_lane_height / 2
                
                # Skip if lane is not visible or too far ahead
                if (sub_lane_y - camera_y < -20 or 
                    sub_lane_y - sub_lane_height - camera_y > VISIBLE_GRID_HEIGHT + 5):
                    continue
                
                # Determine car parameters - use the lane's speed
                car_speed = sub_lane['speed'] * sub_lane['direction']
                
                # Skip generation if too close to player's starting position
                if sub_lane_y < player_y + 2 and sub_lane_y > player_y - 2:
                    continue
                
                # Randomly spawn new cars at edges with probability based on car density
                spawn_chance = 0.02 * CAR_DENSITY
                if random.random() < spawn_chance:
                    # Check if there's already a car near the spawn point
                    spawn_blocked = False
                    spawn_x = -3.0 if sub_lane['direction'] > 0 else GRID_WIDTH + 3.0
                    
                    for car in cars:
                        if (abs(car['y'] - lane_mid_y) < 0.1 and  # Same lane
                            ((sub_lane['direction'] > 0 and car['x'] < 3 and car['x'] > -3) or  # Left edge
                             (sub_lane['direction'] < 0 and car['x'] > GRID_WIDTH - 3 and car['x'] < GRID_WIDTH + 3))):  # Right edge
                            spawn_blocked = True
                            break
                    
                    if not spawn_blocked:
                        if sub_lane['direction'] > 0:  # Cars moving right
                            # Spawn at left edge
                            new_car = create_car(-3.0, lane_mid_y, sub_lane_height, car_speed)
                            cars.append(new_car)
                        else:  # Cars moving left
                            # Spawn at right edge
                            new_car = create_car(GRID_WIDTH + 3.0, lane_mid_y, sub_lane_height, car_speed)
                            cars.append(new_car)

def game_loop():
    """Main game loop"""
    global game_over
    
    initialize_game()
    welcome_message = "Welcome to CrossyRoads! Use WASD or arrow keys to move. Press 1-0 to change difficulty."
    output(welcome_message)
    pygame.time.delay(2000)  # Show welcome message for 2 seconds
    
    last_score_milestone = 0
    
    while True:
        # Handle input
        movement = get_input()
        if movement == 'Q':
            break
        elif movement == 'R' and game_over:
            initialize_game()
            continue
        
        # Update hop animation
        update_hop_animation()
        
        # Update player position if movement input received
        if movement is not None and not isinstance(movement, str) and not game_over:
            update_player_position(movement)
        
        # Always update these regardless of player movement
        if not game_over:
            # Move cars
            move_cars()
            
            # Check for collisions
            check_collision()
            
            # Spawn new cars at edges
            spawn_new_cars()
            
            # Add more cars periodically
            if score // 100 > last_score_milestone:
                last_score_milestone = score // 100
                # Make game slightly harder by increasing car speeds
                for lane in lanes:
                    if not lane['is_safe']:
                        for sub_lane in lane['sub_lanes']:
                            sub_lane['speed'] *= 1.03  # Increase speed by 3%
        
        # Render game
        message = None
        if game_over:
            message = f"Game Over! Final Score: {score} - Press R to restart"
        output(message)
        
        # Cap the frame rate
        clock.tick(FPS)

# Start the game when the script is run
if __name__ == "__main__":
    game_loop()
    pygame.quit()
