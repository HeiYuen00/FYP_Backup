import random
import os

# Define the range for the random numbers
random_min_value = -10
random_max_value = 10

# Define the range of times to add rows
num_rows = 70

# Define the current position
x_position = 0
y_position = 0
angle_position = 0

# Define range of position
x_position_max_range = 8
x_position_min_range = -8

y_position_max_range = 20
y_position_min_range = -10

angle_position_max_range = 45
angle_position_min_range = -45

# Define the relative path to the file
file_path = os.path.join(os.path.dirname(__file__), 'collectmodecfg.txt')

def generate_random_within_range(min_value, max_value, current_position, min_range, max_range):
    """Generate a random number within the specified range and update the position."""
    while True:
        value = round(random.uniform(min_value, max_value), 1) # one decimal place
        if min_range <= current_position + value <= max_range:
            return value

# Open the file in append mode
with open(file_path, 'a') as file:
    for _ in range(num_rows):
        # Generate random numbers within the specified range for x, y, and angle
        x = generate_random_within_range(random_min_value, random_max_value, x_position, x_position_min_range, x_position_max_range)
        x_position += x

        y = generate_random_within_range(random_min_value, random_max_value, y_position, y_position_min_range, y_position_max_range)
        y_position += y

        angle = generate_random_within_range(random_min_value, random_max_value, angle_position, angle_position_min_range, angle_position_max_range)
        # angle = 0
        angle_position += angle

        # Write the numbers to the file, separated by spaces
        file.write(f'{x} {y} {angle}\n')