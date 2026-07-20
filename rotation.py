# rotationTransform
# Rotates planes and data points for visualization purposes ONLY. Do NOT use these results for data analysis as rotations
# are imperfect and must be rounded to pixel locations, this may result in distance calculation errors up to about half 
# your tomogram pixel size.

import os
import numpy as np
import argparse

from visualization import visualize_basename


def normalize(v):
    return v / np.linalg.norm(v)

def compute_average_normal(n1, n2):
    abs_n1 = np.abs(n1)
    abs_n2 = np.abs(n2)
    avg_normal = normalize((abs_n1 + abs_n2) / 2.0)
    return avg_normal

def compute_rotation_matrix(from_vec, to_vec=np.array([0, 0, 1])):
    from_vec = normalize(from_vec)
    to_vec = normalize(to_vec)
    v = np.cross(from_vec, to_vec)
    c = np.dot(from_vec, to_vec)
    s = np.linalg.norm(v)

    if s < 1e-8:
        return np.eye(3) if c > 0 else -np.eye(3)

    vx = np.array([[    0, -v[2],  v[1]],
                   [ v[2],     0, -v[0]],
                   [-v[1],  v[0],    0]])
    
    R = np.eye(3) + vx + (vx @ vx) * ((1 - c) / (s ** 2))
    return R

def transform_points(points, R):
    return np.dot(points, R.T)

def transform_plane(plane, R):
    new_origin = np.dot(R, plane['origin'])
    new_normal = normalize(np.dot(R, plane['normal']))
    return {'origin': new_origin, 'normal': new_normal}

def align_planes_and_points(points, plane1, plane2):
    # Step 1: Make normals parallel via averaging of absolute normals
    avg_normal = compute_average_normal(plane1['normal'], plane2['normal'])

    # Overwrite both planes to use the averaged normal
    plane1_parallel = {'origin': plane1['origin'], 'normal': avg_normal}
    plane2_parallel = {'origin': plane2['origin'], 'normal': avg_normal}

    # Step 2: Compute rotation to align avg_normal → [0, 0, 1]
    R = compute_rotation_matrix(avg_normal, np.array([0, 0, 1]))

    # Step 3: Apply transform
    transformed_points = transform_points(points, R)
    plane1_aligned = transform_plane(plane1_parallel, R)
    plane2_aligned = transform_plane(plane2_parallel, R)

    return transformed_points, plane1_aligned, plane2_aligned

def parse_plane(plane_str):
    values = list(map(float, plane_str.strip("()").split(',')))
    if len(values) != 6:
        raise ValueError("Each plane must be 6 values: (x,y,z,xnorm,ynorm,znorm)")
    origin = np.array(values[0:3])
    normal = np.array(values[3:6])
    return {'origin': origin, 'normal': normal}

def compute_best_fit_plane(points):
    """
    Fit a plane to the 3D points via PCA.
    Returns a dict with 'origin' and 'normal' just like the other planes.
    """
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    _, _, vh = np.linalg.svd(centered)
    normal = vh[-1]  # least variance distance
    return {'origin': centroid, 'normal': normal}


def main():
    parser = argparse.ArgumentParser(description="Align 3D points and planes to face +Z.")
    parser.add_argument('--points', required=True, help='Path to .txt file with point coordinates in X,Z,Y order')
    parser.add_argument('--plane1', required=True, help='Plane 1: (x,y,z,xnorm,ynorm,znorm)')
    parser.add_argument('--plane2', required=True, help='Plane 2: (x,y,z,xnorm,ynorm,znorm)')
    parser.add_argument('--basename', default=None, help='Base name for output image (defaults to basename of the .txt file)')
    parser.add_argument('--outdir', default='.', help='Directory to save visualization')
    parser.add_argument('--bfplane', default=False, help='Set to True if you want to calculate and visualize a plane of bestfit after roation. (Default is False)')

    args = parser.parse_args()

    # Derive basename from points filename if not provided
    if args.basename is None:
        args.basename = os.path.splitext(os.path.basename(args.points))[0]


    # Load points (and convert from X,Z,Y → X,Y,Z)
    raw_points = np.loadtxt(args.points)
    points = raw_points[:, [0, 2, 1]]  # convert to [X, Y, Z]

    # Parse planes
    plane1 = parse_plane(args.plane1)
    plane2 = parse_plane(args.plane2)

    # Apply alignment
    aligned_points, aligned_plane1, aligned_plane2 = align_planes_and_points(points, plane1, plane2)

    # Calculate best fit plane
    if args.bfplane:
        print("Calculating plane of bestfit before visualizing.")
        best_fit_plane = compute_best_fit_plane(aligned_points)
    else: 
        best_fit_plane = args.bfplane    

    # Visualize result
    visualize_basename(aligned_points, aligned_plane1, aligned_plane2, args.basename, args.outdir, tag="aligned", best_fit_plane=best_fit_plane)
    
    print("Done!")

if __name__ == "__main__":
    main()
