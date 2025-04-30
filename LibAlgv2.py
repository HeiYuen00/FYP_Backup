import numpy as np
from scipy.optimize import least_squares

def compute_angle_and_shift(original_rect, transformed_rect, h, k):
    """
    Compute the rotation angle (degrees) and XY shift (tx, ty) between two rectangles.
    
    Args:
        original_rect (np.ndarray): Original rectangle vertices (4x2).
        transformed_rect (np.ndarray): Transformed rectangle vertices (4x2).
        h (float): Known x-coordinate of the rotation center.
        k (float): Known y-coordinate of the rotation center.
        
    Returns:
        tuple: (angle_deg, tx, ty) where:
            angle_deg (float): Rotation angle in degrees.
            tx (float): X-axis translation.
            ty (float): Y-axis translation.
    """
    # Step 1: Compute initial angle (assuming no translation)
    def compute_initial_theta():
        # Translate coordinates to rotation center
        original_rel = original_rect - np.array([[h, k]])
        transformed_rel = transformed_rect - np.array([[h, k]])
        
        # Build linear system to solve for rotation matrix components
        A, B = [], []
        for (dx, dy), (dx_t, dy_t) in zip(original_rel, transformed_rel):
            A.append([dx, -dy])
            B.append(dx_t)
            A.append([dy, dx])
            B.append(dy_t)
        
        A_np = np.array(A, dtype=np.float64)
        B_np = np.array(B, dtype=np.float64)
        c, s = np.linalg.lstsq(A_np, B_np, rcond=None)[0]
        return np.degrees(np.arctan2(s, c))
    
    theta_initial = compute_initial_theta()
    
    # Step 2: Compute initial translation estimate
    def rotate_point(x, y, theta_deg):
        theta_rad = np.radians(theta_deg)
        c, s = np.cos(theta_rad), np.sin(theta_rad)
        x_rot = (x - h) * c - (y - k) * s + h
        y_rot = (x - h) * s + (y - k) * c + k
        return np.array([x_rot, y_rot])
    
    rotated_initial = np.array([rotate_point(x, y, theta_initial) for x, y in original_rect])
    tx_initial = np.mean(transformed_rect[:, 0] - rotated_initial[:, 0])
    ty_initial = np.mean(transformed_rect[:, 1] - rotated_initial[:, 1])
    
    # Step 3: Nonlinear least squares refinement
    def residuals(params):
        theta_rad, tx, ty = params
        c, s = np.cos(theta_rad), np.sin(theta_rad)
        residuals = []
        for (x, y), (xp, yp) in zip(original_rect, transformed_rect):
            dx = x - h
            dy = y - k
            x_model = dx * c - dy * s + h + tx
            y_model = dx * s + dy * c + k + ty
            residuals.append(xp - x_model)
            residuals.append(yp - y_model)
        return np.array(residuals)
    
    # Initial guess: [theta_radians, tx, ty]
    params_initial = [
        np.radians(theta_initial),
        tx_initial,
        ty_initial
    ]
    
    # Solve using Levenberg-Marquardt
    result = least_squares(residuals, params_initial)
    theta_opt_rad, tx_opt, ty_opt = result.x
    theta_opt_deg = np.degrees(theta_opt_rad)

    # print h,k
    print ("rotation center:", h, k)
    
    tx_opt = np.round(tx_opt*100/917,2)
    ty_opt = np.round(ty_opt*100/917,2)

    theta_opt_deg = np.round(theta_opt_deg, 2)
    return [tx_opt, ty_opt],theta_opt_deg

def compute_original_rect(transformed_rect, h, k, theta_deg, tx, ty):
    """
    Reconstruct the original rectangle from the transformed rectangle using rotation center (h, k),
    rotation angle (theta_deg), and translation (tx, ty).
    
    Args:
        transformed_rect (np.ndarray): Transformed rectangle vertices (4x2).
        h (float): x-coordinate of the rotation center.
        k (float): y-coordinate of the rotation center.
        theta_deg (float): Rotation angle in degrees.
        tx (float): Translation along the x-axis.
        ty (float): Translation along the y-axis.
        
    Returns:
        np.ndarray: Original rectangle vertices (4x2).
    """
    # Convert angle to radians
    theta = np.radians(theta_deg)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    
    # Step 1: Undo translation
    untranslated = transformed_rect - np.array([tx, ty])
    
    # Step 2: Undo rotation
    # Translate points relative to rotation center
    relative = untranslated - np.array([h, k])
    # Reverse rotation matrix (for -θ)
    rotation_matrix = np.array([[cos_theta, sin_theta],
                                [-sin_theta, cos_theta]])
    # Apply rotation
    rotated_back = relative @ rotation_matrix.T  # Matrix multiplication
    
    # Step 3: Translate back to original coordinates
    original_rect = rotated_back + np.array([h, k])


    
    return original_rect

import numpy as np

def find_rotation_center(original_rect, rotated_rect):
    """
    Find the rotation center between two rectangles using their corresponding vertices.
    
    Args:
        original_rect (np.ndarray): A 4x2 array of vertices for the original rectangle.
        rotated_rect (np.ndarray): A 4x2 array of vertices for the rotated rectangle.
        
    Returns:
        np.ndarray: The rotation center as a 1D array [h, k].
    """
    A = []
    B = []
    # Iterate over corresponding vertex pairs
    for (x1, y1), (x2, y2) in zip(original_rect, rotated_rect):
        # Coefficients for the equation: a*h + b*k = c
        a = x2 - x1
        b = y2 - y1
        c = 0.5 * ((x2**2 - x1**2) + (y2**2 - y1**2))
        A.append([a, b])
        B.append(c)
    
    # Solve using least squares
    A_np = np.array(A, dtype=np.float64)
    B_np = np.array(B, dtype=np.float64)
    center = np.linalg.lstsq(A_np, B_np, rcond=None)[0]
    return center


def rotate_rectangle(original_rect, h, k, angle_degrees):
    """
    Rotate a rectangle around a center point (h, k) by a given angle.
    
    Args:
        original_rect (np.ndarray): Input rectangle vertices as a 4x2 numpy array.
        h (float): x-coordinate of the rotation center.
        k (float): y-coordinate of the rotation center.
        angle_degrees (float): Rotation angle in degrees (counter-clockwise).
        
    Returns:
        np.ndarray: Rotated rectangle vertices as a 4x2 numpy array.
    """
    # Convert angle to radians
    theta = np.radians(angle_degrees)
    c, s = np.cos(theta), np.sin(theta)
    
    # Translate rectangle to origin (relative to rotation center)
    translated = original_rect - np.array([h, k])
    
    # Apply rotation matrix
    x_rot = translated[:, 0] * c - translated[:, 1] * s
    y_rot = translated[:, 0] * s + translated[:, 1] * c
    
    # Translate back to original coordinate system
    rotated_rect = np.column_stack((x_rot + h, y_rot + k))
    
    return rotated_rect

def sort_points_anticlockwise(points):
    centroid = np.mean(points, axis=0)
    angles = np.arctan2(points[:,1] - centroid[1], points[:,0] - centroid[0])
    return centroid,points[np.argsort(angles)]

def filiter_Result(API_Returnresult):
    positions_q = []

    for detection in API_Returnresult['predictions']:
        if detection['confidence'] < 0.88:
            continue
        x_center = detection['x']
        y_center = detection['y']
        positions_q.append([x_center, y_center])
    return np.array(positions_q)