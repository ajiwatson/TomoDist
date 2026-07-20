"""
Functions for detecting ice planes from contamination point data using KMeans clustering.
""" 

import numpy as np
from sklearn.cluster import KMeans

# Functions for KMeans Clustering 
def find_centroids(points, tomo_dimensions): 
    # Find the centroids to assign for KMeans, uses the minimum and 
    # maximum z values and the midpoints of the x and y axes
    min_z = np.min(points[:, 2])
    max_z = np.max(points[:, 2])

    x = float(tomo_dimensions[0]) / 2
    y = float(tomo_dimensions[1]) / 2

    min_coordinate = [x, y, min_z]
    max_coordinate = [x, y, max_z]

    initial_centroids = [min_coordinate, max_coordinate]

    return initial_centroids

def cluster_planes(points, initial_centroids, z_weight):
    
    # Weight the z dimension (work on a copy to avoid mutating the original)
    weighted = points.copy()
    weighted[:, 2] = weighted[:, 2] * z_weight
    
    # Perform clustering
    kmeans = KMeans(n_clusters=2, init=initial_centroids)
    kmeans.fit(weighted)

    centers = kmeans.cluster_centers_
    labels = kmeans.labels_

    # Undo weighting on centers only
    centers[:, 2] = centers[:, 2] / z_weight

    # Seperate out clusters (using original unmodified points)
    cluster1 = points[labels == 0]
    cluster2 = points[labels == 1]

    ## -------------- Visualization for testing KMeans Clustering -----------------------------------------    
    # # Plot the clusters in 3D
    # fig = plt.figure(figsize=(10, 8))
    # ax = fig.add_subplot(111, projection='3d')
    # ax.view_init(elev=7, azim=35)
    # # Scatter plot for clusters
    # ax.scatter(points[:, 0], points[:, 1], points[:, 2], c=labels, cmap='viridis', s=50, alpha=0.6)

    # # Scatter plot for centroids
    # ax.scatter(centers[:, 0], centers[:, 1], centers[:, 2], c='red', marker='x', s=100, label='Centroids')

    # # Labels and title
    # ax.set_xlabel('X')
    # ax.set_ylabel('Y')
    # ax.set_zlabel('Z')
    # ax.set_title('3D KMeans Clustering')

    # # Add legend
    # ax.legend()

    # # Show plot 
    # plt.show()
    ## ---------------------------------------------------------------------------------------------------

    return cluster1, cluster2

# For each cluster find best fit planes 
def compute_best_fit_plane(points):
    """
    Fit a plane to the 3D points via PCA.
    Returns a dict with 'origin' and 'normal'.
    """
    centroid = np.mean(points, axis=0)
    centered = points - centroid
    _, _, vh = np.linalg.svd(centered)
    normal = vh[-1]  # least variance distance
    return {'origin': centroid, 'normal': normal}


# Run detectPlanes
def make_planes(dataset, z_weight, outdir): 

    for tomo_name in dataset.tomograms:
        tomogram = dataset.tomograms[tomo_name]
        points = tomogram.plane_points
        initial_centroids = find_centroids(points, dataset.dimensions)
        cluster1, cluster2 = cluster_planes(points, initial_centroids, z_weight)
        tomogram.plane1 = compute_best_fit_plane(cluster1)
        tomogram.plane2 = compute_best_fit_plane(cluster2)

        ## -------------- Visualization for testing best fit planes ---------------------
        # visualize_basename(ice, plane1, plane2, tomogram, outdir)
        ## ------------------------------------------------------------------------------

    return dataset

# Run just the best fit plane function, but with passing in and out only a Dataset
def do_best_fit(dataset): 
    '''
    Just unpacking and repacking data to run compute_best_fit_plane on the particles. 
    Keeping the main function as clean as possible. 
    '''

    for tomo_name in dataset.tomograms: 
        tomogram = dataset.tomograms[tomo_name]
        tomogram.bestfit_plane = compute_best_fit_plane(tomogram.particles)

    return dataset