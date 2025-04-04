import numpy as np
# from sklearn.linear_model import RANSACRegressor
from scipy.optimize import minimize
from math import *

def compute_rigid_transform(original, moved):
    """
    Computes translation (dx, dy) and rotation angle (degrees) between two rectangle configurations.
    
    Parameters:
        original : numpy array (4x2)
            Initial rectangle coordinates [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        moved : numpy array (4x2)
            Transformed rectangle coordinates in the same order
    
    Returns:
        translation : tuple (dx, dy)
        rotation_angle : float (degrees)
    """
    # Compute centroids
    centroid_orig = np.mean(original, axis=0)
    centroid_moved = np.mean(moved, axis=0)

    # print centroid_orig and centroid_moved
    print("centroid_orig:", centroid_orig)
    print("centroid_moved:", centroid_moved)
    
    # Center points by subtracting centroids
    orig_centered = original - centroid_orig
    moved_centered = moved - centroid_moved
    
    # # Compute covariance matrix H
    # H = orig_centered.T @ moved_centered
    
    # # Singular Value Decomposition
    # U, _, Vt = np.linalg.svd(H)
    
    # # Compute rotation matrix
    # R = Vt.T @ U.T
    
    # # Handle reflection case
    # if np.linalg.det(R) < 0:
    #     Vt[-1, :] *= -1
    #     R = Vt.T @ U.T
    
    # # Extract rotation angle
    # angle_rad = np.arctan2(R[1, 0], R[0, 0])
    # angle_deg = np.degrees(angle_rad)

    # Step 3: Compute rotation matrix R using SVD

    x = orig_centered
    y = moved_centered

    ss = 0
    sc = 0
    for i in range(len(original)):
        ss += y[i, 1] * x[i, 0] - y[i, 0] * x[i, 1]
        sc += y[i, 0] * x[i, 0] + y[i, 1] * x[i, 1]
    norm_v = sqrt(ss * ss + sc * sc)
    s = ss / norm_v
    c = sc / norm_v
    alpha = atan2(s, c)
    angle_shift = alpha * 180 / pi
    
    # Compute translation
    translation = centroid_moved - centroid_orig
    
    return translation, angle_shift

def rearrange_coordinates(positions):
    # Convert to a NumPy array if not already
    positions_array = np.array(positions)
    
    # Sort the coordinates based on y values (ascending)
    sorted_by_y = positions_array[np.argsort(positions_array[:, 1])]
    
    # Identify upper left and upper right (top two points)
    upper_left = sorted_by_y[0] if sorted_by_y[0][0] < sorted_by_y[1][0] else sorted_by_y[1]
    upper_right = sorted_by_y[1] if sorted_by_y[0][0] < sorted_by_y[1][0] else sorted_by_y[0]
    
    # Identify bottom left and bottom right (bottom two points)
    bottom_left = sorted_by_y[2] if sorted_by_y[2][0] < sorted_by_y[3][0] else sorted_by_y[3]
    bottom_right = sorted_by_y[3] if sorted_by_y[2][0] < sorted_by_y[3][0] else sorted_by_y[2]

    return np.array([upper_left, upper_right, bottom_left, bottom_right])


def enforce_rectangle(points, angle_tol=5):
    centroid = np.mean(points, axis=0)
    # Sort points clockwise around centroid
    angles = np.arctan2(points[:,1] - centroid[1], points[:,0] - centroid[0])
    sorted_indices = np.argsort(angles)
    points = points[sorted_indices]
    
    # Enforce right angles using optimization
    def loss(adjusted_points):
        adjusted_points = adjusted_points.reshape(4, 2)
        # Penalize deviations from detected positions
        position_error = np.sum((adjusted_points - points)**2)
        # Penalize non-right angles
        angle_error = 0
        for i in range(4):
            v1 = adjusted_points[i] - adjusted_points[i-1]
            v2 = adjusted_points[(i+1)%4] - adjusted_points[i]
            cos_theta = np.dot(v1, v2) / (np.linalg.norm(v1)*np.linalg.norm(v2))
            angle_error += (cos_theta - 0)**2  # 90° implies dot product = 0
        return position_error + 10 * angle_error  # Weighted loss
    
    result = minimize(loss, points.flatten(), method='L-BFGS-B')
    return result.x.reshape(4, 2)


# def adaptive_ransac(original, moved, noise_scale=5.0):
#     # Estimate inlier threshold based on expected noise
#     residual_threshold = 2.0 * noise_scale  # 2σ coverage for Gaussian noise
    
#     model = RANSACRegressor(
#         min_samples=3,  # More robust than 2-point samples
#         max_trials=500,  # Increased sampling
#         residual_threshold=residual_threshold,
#         random_state=42
#     )
#     model.fit(original, moved)
    
#     if sum(model.inlier_mask_) < 3:  # Fallback to all points
#         return compute_rigid_transform(original, moved)
    
#     return compute_rigid_transform(original[model.inlier_mask_], 
#                                  moved[model.inlier_mask_])


def sort_points_anticlockwise(points):
    centroid = np.mean(points, axis=0)
    angles = np.arctan2(points[:,1] - centroid[1], points[:,0] - centroid[0])
    return centroid,points[np.argsort(angles)]


def robust_transform(original, moved):
    # Step 1: Reorder points consistently
    #original = sort_points_anticlockwise(original_raw)
    #moved = sort_points_anticlockwise(moved_raw)

    # Step 2: Enforce geometric rectangle properties
    original_rect = enforce_rectangle(original)
    moved_rect = enforce_rectangle(moved)
    
    # Step 3: Apply RANSAC to reject outliers
    translation, angle = compute_rigid_transform(original_rect, moved_rect)
    translation = translation*(5/47)
    translation = np.round(translation,1)
    angle = round(angle,1)
    return translation, angle

def filiter_Result(API_Returnresult):
    positions_q = []

    for detection in API_Returnresult['predictions']:
        if detection['confidence'] < 0.8:
            continue
        x_center = detection['x']
        y_center = detection['y']
        positions_q.append([x_center, y_center])
    return np.array(positions_q)