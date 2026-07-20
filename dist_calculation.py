'''
This file performs calculations using the data. It uses only the raw data, and therefore any functions are called prior to rotations.
While I've said this on the rotation.py file, do NOT use rotated data for distance calculations. Rotation is for visualization only. 
Rotations must round to pixel/point locations and doing this rounding prior to calculations can cause incorrect calculations. 

point_to_plane_distance
    calculates the distance between the point and the closest point on the plane by using dot product
    
    Inputs
    point: The point to run a calculation on
    plane_origin: The origin of the plane to run a calculation on 
    plane_normal: The plane normal, used to calculate dot product
    
    Output
    The distance from the point to a plane (absolute value so always positive)

is_between_planes
    checks that a given point lies between the two planes, and removes it from consideration if it does not. (Anything picked outside the ice would be either on carbon or a 
    false positive)
    To accomplish this, the vector between the point and the plane origin in caclulated. Then the dot product between the plane normal and the point vector is used. 
    In order to ignore the direction of the normal, in case of non-standard normal orientation placement, whether the normals face the same direction is determined and then 
    that informaiton is used to filter the particles. 

    Inputs
    Tomogram class: A class containing the points and planes and other information
        {tomogram: {
            "particles": <3D particle points array>,
            "plane_points": <3D particle points array> (not used in this function)
            "plane1": {
                "origin": (x,y,z)
                "normal": (xnormal,ynormal,znormal)
                }
            }
            "plane2": {
                "origin": (x,y,z)
                "normal": (xnormal,ynormal,znormal)
                }            
        }
    
    Output
    results: an updated dictionary with points that fall outside the range removed. (Same structure as input)
'''
import numpy as np
import os


def add_distances(dataset):
    # Small function to queue up distances for plotting
    distances = []
    for tomo in dataset.tomograms:
        tomogram = dataset.tomograms[tomo]
        for d in tomogram.distances:
            distances.append(d)
    return distances

def add_ice(dataset):
    # Small function to queue up ice thicknesses for plotting
    ice = []
    for tomo in dataset.tomograms:
        tomogram = dataset.tomograms[tomo]
        ice.append(tomogram.ice_thickness)
    return ice


def point_to_plane_distance(point, plane_origin, plane_normal):
    diff = point - plane_origin
    distance = np.abs(np.dot(diff, plane_normal) / np.linalg.norm(plane_normal))
    return distance

# Function to check if a point is between two planes
def is_between_planes(dataset):
    
    for tomo_name in dataset.tomograms:
        
        tomogram = dataset.tomograms[tomo_name]
        points = np.asarray(tomogram.particles)

        # Access the origins and normals of the two planes
        plane1_origin = tomogram.plane1["origin"]
        plane1_normal = tomogram.plane1["normal"]
        plane2_origin = tomogram.plane2["origin"]
        plane2_normal = tomogram.plane2["normal"]
        
        # Determine if plane normals are facing the same direction or opposite directions
        same = (plane1_normal[2] * plane2_normal[2]) >= 0

        # Vectorized: compute projections for all points at once
        proj1 = (points - plane1_origin) @ plane1_normal
        proj2 = (points - plane2_origin) @ plane2_normal
        product = proj1 * proj2

        if same:
            mask = product <= 0
        else:
            mask = product >= 0

        tomogram.particles = points[mask]
    return dataset

# Find the distances of points to planes and normalize these values. 
def collect_normalized_distances(dataset, outdir):

    output = os.path.join(outdir, "Average_Distances_and_Ice_Thickness.txt")
    with open(output, 'w') as file:
        file.write("Tomogram\tAverage Ice Thickness\tAverage Distance (normalized to ice thickness)\n")

        for tomo_name in dataset.tomograms:
            tomogram = dataset.tomograms[tomo_name]
            points = np.asarray(tomogram.particles)
            p1origin = tomogram.plane1['origin']
            p1normal = tomogram.plane1['normal']
            p2origin = tomogram.plane2['origin']
            p2normal = tomogram.plane2['normal']

            # Vectorized distance calculation for all points at once
            d1 = np.abs((points - p1origin) @ p1normal) / np.linalg.norm(p1normal)
            d2 = np.abs((points - p2origin) @ p2normal) / np.linalg.norm(p2normal)
            min_d = np.minimum(d1, d2)
            max_d = np.maximum(d1, d2)
            total = min_d + max_d
            norm_d = np.where(total != 0, min_d / total, 0.0)

            tomogram.distances = norm_d.tolist()
            ice_thicks = total * dataset.voxel_size

            # write values to file
            file.write(f"{tomo_name}\t{np.mean(ice_thicks):.2f}\t{np.mean(norm_d):.2f}\n")
            
            tomogram.ice_thickness = float(np.mean(ice_thicks))
            tomogram.average_dist = float(np.mean(norm_d))

    return dataset

def write_distances(dataset, outdir):
    output = os.path.join(outdir, "Normalized Distances.txt")
    with open(output, 'w') as file: 
        file.write("All of the normalized distances from every particle in every tomogram. To the 4th decimal. Useful for plotting in external programs.\n")
        for tomo_name in dataset.tomograms:
            tomogram = dataset.tomograms[tomo_name]
            for distance in tomogram.distances:
                file.write(f"{distance: .4f}\n")

# Function that runs the other functions in this file. 
def calc_distances(dataset, outdir):

    dataset = is_between_planes(dataset) # Remove any particles that are not between the planes, assumption is these are false picks or on carbon
    dataset = collect_normalized_distances(dataset, outdir)
    write_distances(dataset, outdir)

    return dataset



    