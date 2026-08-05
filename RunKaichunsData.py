'''
A function for running Kaichun's sample data, this will be expanded out for running on any manually determined plane dataset in future updates. 
'''

import os
import sys
import numpy as np 
from dataclasses import dataclass

parent_directory = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
sys.path.insert(0, parent_directory)

from visualization import visualize_basename, plot_comparison
from data_handling import TomogramDist, Dataset
from dist_calculation import calc_distances, add_distances, add_ice


def load_point_data(dataset, particles, planes, outdir=None, keep=False):
    '''
    Read in the manually detected planes and particles, the particles are yz flipped, so will correct that
    planes in txt file in format:
        basename plane x y x xnorm ynorm znorm 
    '''
    tomo_dict = {} #temporary dictionary for storing particles and planes before loading them into the TomogramDist class
    particle_tomos = [] #temporary list for making sure all tomograms have both particles and planes
    plane_tomos = [] #temporary list for making sure all tomograms have both particles and planes
    
    # If input points are in a spk format, convert to .txt 
    particles_files = [particles + f for f in os.listdir(path=particles) if f.endswith('.txt')]
  
    
    # Read the .txt into numpy arrays and turn to xyz for particles
    for f in particles_files: 
        print(f)
        tomo_name = os.path.splitext(os.path.basename(f))[0]
        #print(f)
        data_xzy = np.loadtxt(f)
        data_xyz = data_xzy[:, [0,2,1]]

        particle_tomos.append(tomo_name)

        if tomo_name not in tomo_dict: 
            tomo_dict[tomo_name] = {}

        tomo_dict[tomo_name]['particles'] = data_xyz

    # Open the planes file and read out the necessary data
    if not os.path.isfile(planes): 
        raise FileNotFoundError(f"File does not exist: {planes}")
        
    with open(planes, "r", encoding="utf-8") as file: 
        next(file)

        for line in file: 
            tomo_name, plane_number, *values = line.split()
            values = np.asarray(values, dtype=float)

            plane = { 
                "origin": values[:3],
                "normal": values[3:],
            }
            if tomo_name not in tomo_dict: 
                print(f"There are no particle coordinates for {tomo_name}. Skipping...")
                continue
            if plane_number == "1": 
                tomo_dict[tomo_name]['plane1'] = plane
                plane_tomos.append(tomo_name)
            elif plane_number == "2": 
                tomo_dict[tomo_name]['plane2'] = plane
            else: 
                print("plane number was not defined as 1 or 2")

    print(f"particle tomos: {particle_tomos} plane tomos: {plane_tomos}")

    # Remove any keys that do not contain data for both particles and planes. Report to User. 
    common_keys = np.intersect1d(particle_tomos, plane_tomos)
    no_planes = np.setdiff1d(particle_tomos, common_keys)

    if len(no_planes) > 0:
        print("\nThere are no plane coordinates for tomograms:")
    for tomo_name in no_planes:
        print(f"  - {tomo_name}")  
        del tomo_dict[tomo_name]

    print(f"\nContinuing processing for {len(common_keys)} tomograms.")

    # Load the common tomograms into the data objects
    for tomo_name in tomo_dict: 
        particles=(tomo_dict[tomo_name]['particles'])
        plane1=(tomo_dict[tomo_name]["plane1"])
        plane2=(tomo_dict[tomo_name]["plane2"])
        tomogram = TomogramDist(name=tomo_name, particles=particles, plane_points=None, plane1=plane1, plane2=plane2)
        dataset.tomograms[tomo_name] = tomogram

    return dataset


def main():
    'Function for executing code to show replicability of publication results.'
    
    dataname= "Standard"
    dataname2= "ACE"
    pixel_size=1.08
    tomo_dims=512,512,256
    particles="./ACE_Data/Control_noC/"
    plane_coors="./ACE_Data/ManualPlanesStandard.txt"
    outdir1="./ACE_Data/StandardPlots/"
    particles2="./ACE_Data/ACE_noC/"
    plane_coors2="./ACE_Data/ManualPlanesACE.txt"
    outdir2="./ACE_Data/ACEPlots/"
    outdir="./ACE_Data/ComparisonResults/"

    data1 = Dataset(
        name=dataname, voxel_size=pixel_size, dimensions=tomo_dims, tomograms={}
        )
    data2 = Dataset(
        name=dataname2, voxel_size=pixel_size, dimensions=tomo_dims, tomograms={}
        )
    
    print("A distribution comparison will be run for publication datasets", data1.name, "and", data2.name, "...")
    data1 = load_point_data(data1, particles, plane_coors)
    data2 = load_point_data(data2, particles2, plane_coors2)
    
    print("Calculating particle distributions and ice thickness...")
    data1 = calc_distances(data1, outdir1)    
    data2 = calc_distances(data2, outdir2)   

    print("Will now plot data using matplot...")
    
    for tomo in data1.tomograms: 
        tomogram = data1.tomograms[tomo] 
        visualize_basename(outdir1, tomogram, data1.voxel_size, plane_color="blue", bf_plane_color="green", point_color="black", tag=data1.name)
    for tomo in data2.tomograms: 
        tomogram = data2.tomograms[tomo]
        visualize_basename(outdir2, tomogram, data2.voxel_size, plane_color="blue", bf_plane_color="green", point_color="black", tag=data2.name)

    dist1 = add_distances(data1)
    dist2 = add_distances(data2)

    ice1 = add_ice(data1)
    ice2 = add_ice(data2)

    labels = [data1.name, data2.name]

    print(f"Plotting comparison results, will save in {outdir}")

    plot_comparison(dist1, dist2, labels, "Normalized Distance", "Distribution of Particles in Tomograms", 0.5, outdir, "DistributionComparison.png")

    plot_comparison(ice1, ice2, labels, "Ice Thickness (nm)", "Average Ice Thickness per Tomogram", 500, outdir, "IceComparison.png")

    print("Done!")


if __name__ == "__main__":
    print("Hello, you are running the sample data for publication Acoustofluidic Cryo-EM Enables In Situ Particle Manipulation for Uniform, High-Quality Cryo-EM Specimens. " \
    "This function is hardcoded to run this data only. If you want to process your own data, please type Ctrl + C and see the README for instructions.")
    print("...")
    print("Starting TomoDist Publication Sample....")
    main()