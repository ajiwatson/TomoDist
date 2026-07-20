'''
This file contains functions required to read in the data and build a dictionary for a dataset.

model2point_wrapper
    Takes IMOD model .spk files (can generate using nextPYP or IMOD) and adds the coordinates to a dictionary
    Note that this function will still run even if the user does not have particles or planes for a given tomogram. This is intentional. 
    Checks for both are later to allow for user to manually draw and input planes if they so desire. (Use paraview and keep the .txt file) 
    
    Inputs
    particles: (str) the directory containing particle positions in .spk format
    planes: (str) the directory containing plane positions (the ice contaimination coordinates) in .spk formation
    keep: (bool) default False, whether or not to keep the .txt files for external use
   
    Output
    dataset: a multi-dimensional dictionary for storing information about a given tomogram 
        {tomogram (the basename of the file): {
            "particles": <3D particle points array>,
            "plane_points": <3D particle points array>
            }
        }

It also contains functions required for the visualization/reading/writing of data. 
'''

import os
import subprocess
import numpy as np
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional 
from dataclasses import dataclass

@dataclass
class Dataset: 
    '''
    Dataset containing tomogram data

    A class used to store dataset level data and a dictionary referencing tomograms 
    
    Attributes
    ----------
    name: Optional[string]
        name of the dataset
    voxel_size: float
        the binned voxel size of the tomograms in the dataset
    dimensions: tuple
        the dimensions of the tomograms in the dataset
    tomograms: dictionary
        A dictionary containing references to the class TomogramDist containing tomogram level information. 
    '''
    name: str 
    voxel_size: float
    dimensions: tuple
    tomograms: Optional[Any] = None

@dataclass
class TomogramDist: 
    '''
    Tomograms' Distances and Distributions

    A class used to store particle point data, plane point data, planes, and average ice thickness. 
    Also contains general data about the dataset: voxel size, dimensions and name. 

    Attributes
    ----------
    name: string
        basename of the file containing the particles/planes
    particles: np.ndarray
        particle coordinates, 3D array
    plane_points: np.ndarray
        plane coordinates, 3D array
    plane1: Optional[Any]
        plane origin and normals {'origin': x,y,z; 'normals': xnorm, ynorm, znorm}
    plane2: Optional[Any]
        plane origin and normals {'origin': x,y,z; 'normals': xnorm, ynorm, znorm}
    bestfit_plane: Optional[Any]
        plane origin and normals {'origin': x,y,z; 'normals': xnorm, ynorm, znorm}
    ice_thickness: 
        average calculated thickness of ice across a tomogram in nanometers
    average_dist: 
        average calculated distance of particles from the air water interface in nanometers
    distances:
        all distances of particles from air water interface, normalized so unitless
    '''
    name: str 
    particles: np.ndarray 
    plane_points: np.ndarray 
    plane1: Optional[Any] = None
    plane2: Optional[Any] = None
    bestfit_plane: Optional[Any] = None
    ice_thickness: Optional[Any] = None
    average_dist: Optional[Any] = None
    distances: Optional[Any] = None

def load_point_data(dataset, particles, planes, outdir, keep=False):
    '''
    Read in .spk files and convert them to .txt files. Read the .txt files into numpy arrays. Deletes the .txt files unless specified otherwise
    '''

    tomo_dict = {} #temporary dictionary for storing particles and planes before loading them into the TomogramDist class
    particle_tomos = [] #temporary list for making sure all tomograms have both particles and planes
    plane_tomos = [] #temporary list for making sure all tomograms have both particles and planes

    # Create temporary directories for storing text files. Kept if keep=True
    temp_particles_dir = os.path.join(outdir, 'temp_particle_coors/')
    os.makedirs(temp_particles_dir, exist_ok=True)
    temp_planes_dir = os.path.join(outdir, 'temp_plane_coors/')
    os.makedirs(temp_planes_dir, exist_ok=True)
    
    # Generate .txt files (xzy) from .spk files (xyz) for particles
    spk_files = [(particles + f, os.path.join(temp_particles_dir, f.replace('.spk', '.txt')))
                 for f in os.listdir(path=particles) if f.endswith('.spk')]
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(subprocess.run, ['model2point', inp, out])
                   for inp, out in spk_files]
        for f in as_completed(futures):
            f.result()
    
    # Read the .txt into numpy arrays and turn to xyz for particles
    particle_files_txt = os.listdir(path=temp_particles_dir)
    for particle_file in particle_files_txt: 
        particle_file = temp_particles_dir + particle_file
        tomo_name = os.path.splitext(os.path.basename(particle_file))[0]
        data_xzy = np.loadtxt(particle_file)
        data_xyz = data_xzy[:, [0,2,1]]

        particle_tomos.append(tomo_name)

        if tomo_name not in tomo_dict: 
            tomo_dict[tomo_name] = {}

        tomo_dict[tomo_name]['particles'] = data_xyz

    # Generate .txt files (xzy) from .spk files (xyz) for planes
    spk_files = [(planes + f, os.path.join(temp_planes_dir, f.replace('.spk', '.txt')))
                 for f in os.listdir(path=planes) if f.endswith('.spk')]
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(subprocess.run, ['model2point', inp, out])
                   for inp, out in spk_files]
        for f in as_completed(futures):
            f.result()
    
    # Read the .txt into numpy arrays and turn to xyz for planes
    plane_files_txt = os.listdir(path=temp_planes_dir)
    for plane_file in plane_files_txt: 
        plane_file = temp_planes_dir + plane_file
        tomo_name = os.path.splitext(os.path.basename(plane_file))[0]
        data_xzy = np.loadtxt(plane_file)
        data_xyz = data_xzy[:, [0,2,1]]

        plane_tomos.append(tomo_name)

        if tomo_name not in tomo_dict: 
            print(f"There are no particle coordinates for {tomo_name}. Skipping...")
            continue

        tomo_dict[tomo_name]["planes"] = data_xyz

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
        planes=(tomo_dict[tomo_name]["planes"])
        tomogram = TomogramDist(name=tomo_name, particles=particles, plane_points=planes)
        dataset.tomograms[tomo_name] = tomogram

    # Delete the txt directory if keep is false
    if not keep: 
        shutil.rmtree(temp_planes_dir)
        shutil.rmtree(temp_particles_dir)

    return dataset
