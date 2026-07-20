'''
TomoDist (Tomograms' Distance and Distribution)
Developed and tested on Python 3.10.0

Initially was written to determine particle distribution from manually picked particles and planes for "Acoustofluidic Cryo-EM Enables In Situ Particle Manipulation for Uniform, High-Quality Cryo-EM Specimens". 
Has since become a bit of a side passion project to make it easier to use and add features. 
Has since accrued an additional contributor (Mehmet Tasdelen https://github.com/tasdelenmf). 

Written by Abigail Watson 2025-2026 with help from Mario Borgnia (conceptualization, math advice), Mehmet Tasdelen (dataclass restructuring advice, restructured code to take config file), 
and ChatGPT (debugging, and so I did't have to search stack overflow when I knew a function existed but couldn't remember the name)
'''

import os
import sys
import yaml

from data_handling import load_point_data, Dataset
from detect_planes import make_planes, do_best_fit
from dist_calculation import calc_distances, add_distances, add_ice
from visualization import visualize_basename, plot_comparison


# Runs the program by calling functions from other files and passing user arguments. Prints progress statements so user is aware of what step is being done.
def main(): 
    '''
    I tried to keep this main function as clean as possible. As such, there's not much detail about what's going on under the hood here. 
    Basic overview: 
        1. Determine if the user is comparing data or not. If yes, run fuctions on both datasets, if no, just run on one. 
        2. Load the data into a dataclass structure 
            Dataset
                contains dataset level data (name, pixel size, tomogram dimensions)
                contains a dictionary with keys being tomogram basenames and calls to the TomogramDist dataclass
            TomogramDist
                contains data on the tomogram level, starting with just the tomogram name and particle and plane points and gaining data as the program runs
            *note* --> If a tomogram name can't be found for both planes and particles it is skipped. 
        3. Make planes. Plane points are clustered into 2 clusters using K-Means with Z-weighting and then the clusters are used to fit planes. 
        4. Distance Calculation. Point distances to planes are calculated. Absolute distances are used to calculate the ice thickness and normalized distances are used to 
        display the particle distribution. A couple of initial text files are saved to the output directory here for plotting in other software. 
        5. Determine if the user wants a plane of best fit. If yes, calculate this. Just a best fit plane to the particle positions. 
        6. Visualize the results. You get some dataset level and tomogram level visualization results. These are plotted with MatPlotLib, there is some freedom for changing
        colors and such, but for true flexibility use the visualization file and edit yourself, or use the txt files to plot elsewhere. Saves as both .png and .svg files
        for high resolution images in publications/posters. 
            P.S. If you aren't familiar with Python, feel free to copy-paste visualization.py into ChatGPT and ask it for whatever formatting change you need to the plots. 
    '''

    if compare:
        data1 = Dataset(
            name=dataname, voxel_size=pixel_size, dimensions=tomo_dims, tomograms={}
            )
        data2 = Dataset(
            name=dataname2, voxel_size=pixel_size, dimensions=tomo_dims, tomograms={}
            )
        
        
        print("You've elected to compare data. Loading", data1.name, "and", data2.name, "...")
        data1 = load_point_data(data1, particles, plane_coors, outdir1, keep)
        data2 = load_point_data(data2, particles2, plane_coors2, outdir2, keep)
        
        print("Detecting planes for", data1.name, "and", data2.name, "...")
        data1 = make_planes(data1, z_weight, outdir1)
        data2 = make_planes(data2, z_weight, outdir2) 
        
        print("Calculating particle distributions and ice thickness...")
        data1 = calc_distances(data1, outdir1)    
        data2 = calc_distances(data2, outdir2)   

        if best_fit: 
            print("A best fit plane through the particles will be calculated...")
            data1 = do_best_fit(data1)
            data2 = do_best_fit(data2)

        print("Will now plot data using matplot...")
        # --- This section used for visualization, I have not yet conceived a way to make it as clean as the analysis section
        for tomo in data1.tomograms: 
            tomogram = data1.tomograms[tomo] #particles are broken here
            visualize_basename(outdir1, tomogram, data1.voxel_size, plane_color, bf_plane_color, point_color, data1.name, best_fit)
        for tomo in data2.tomograms: 
            tomogram = data2.tomograms[tomo]
            visualize_basename(outdir2, tomogram, data2.voxel_size, plane_color, bf_plane_color, point_color, data2.name, best_fit)

        dist1 = add_distances(data1)
        dist2 = add_distances(data2)

        #print('dist1', dist1)
        #print('dist2', dist2)

        ice1 = add_ice(data1)
        ice2 = add_ice(data2)

        labels = [data1.name, data2.name]

        print(f"Plotting comparison results, will save in {outdir}")

        plot_comparison(dist1, dist2, labels, "Normalized Distance", "Distribution of Particles in Tomograms", 0.5, outdir, "DistributionComparison.png")

        plot_comparison(ice1, ice2, labels, "Ice Thickness (nm)", "Average Ice Thickness per Tomogram", 500, outdir, "IceComparison.png")

        print("Done!")

    else: 
        data = Dataset(
            name=dataname, voxel_size=pixel_size, dimensions=tomo_dims, tomograms={}
            )

        print("Loading", data.name, "...")
        data = load_point_data(data, particles, plane_coors, outdir, keep)
        
        print("Detecting planes for", data.name, "...")
        data = make_planes(data, z_weight, outdir)
        
        print("Calculating particle distributions and ice thickness...")
        data = calc_distances(data, outdir)

        if best_fit: 
            print("A best fit plane through the particles will be calculated...")
            data = do_best_fit(data)

        print("Will now plot data using matplot...")
        for tomo in data.tomograms:
            tomogram = data.tomograms[tomo]
            #print(tomogram)
            visualize_basename(outdir, tomogram, data.voxel_size, plane_color, bf_plane_color, point_color, data.name, best_fit)
        
        print("Done!")




# Parses User arguments, determines arguments are valid and calls the main function
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python3 main.py <config.yml>")
        sys.exit(1)

    config_file = sys.argv[1]

    # Load YAML
    with open(config_file, "r") as f:
        cfg = yaml.safe_load(f)

    # Read required parameters
    plane_coors = cfg["planes_dir"]
    particles = cfg["particles_dir"]
    pixel_size = float(cfg["pixel_size"])

    # YAML gives you a string "512,512,256" — convert to tuple of ints
    tomo_dims = tuple(map(int, str(cfg["tomo_dimensions"]).split(",")))

    outdir = cfg["output_dir"]

    # Compare options
    dataname = cfg.get("dataname")
    compare = bool(cfg.get("compare", False))
    plane_coors2 = cfg.get("planes_dir_2")
    particles2 = cfg.get("particles_dir_2")
    dataname2 = cfg.get("dataname_2")

    # Optional processing
    best_fit = bool(cfg.get("best_fit", False))
    keep = bool(cfg.get("keep", False))
    z_weight = int(cfg.get("z_weight", 10))

    # Visualization settings
    rotate = bool(cfg.get("rotate", False))
    plane_color = cfg.get("plane_color", "blue")
    bf_plane_color = cfg.get("bfplane_color", "green")
    point_color = cfg.get("point_color", "black")
    v_color1 = cfg.get("violin_color1", "blue")
    v_color2 = cfg.get("violin_color2", "blue")


    # Test input directories exist
    if os.path.exists(plane_coors) == False: 
        print("The directory {plane_coors} does not exist")
        exit
    if os.path.exists(particles) == False: 
        print("The directory {particles} does not exist")
        exit

    # Create output directory if it does not exist and add a dataname directory under it
    os.makedirs(outdir, exist_ok=True)
    outdir = os.path.join(outdir, '')
    plane_coors = os.path.join(plane_coors, '')    
    particles = os.path.join(particles, '')
    

    # Test users have necessary inputs if comparing data before starting processing
    if compare: 
        try: 
            if not dataname or not dataname2: 
                raise ValueError("Both --data_name and --data_name2 are required when comparing datasets (--compare was passed)")
            if dataname == dataname2: 
                raise ValueError("Datanames must be different when comparing data.")
            if not plane_coors2 or not particles2:
                raise ValueError("You must provide a second dataset to perform a comparison (-planes2 and --particles2)")

            outdir1 = os.path.join(outdir, dataname)
            os.makedirs(outdir1, exist_ok=True)
            os.path.join(outdir1, '')

            outdir2 = os.path.join(outdir, dataname2)
            os.makedirs(outdir2, exist_ok=True)
            os.path.join(outdir2, '')

            os.path.join(particles2, '')
            os.path.join(plane_coors2, '')

        except ValueError as e: 
            print(f"Error: {e}")
            exit(1)
        
        # Test input directories exist
        if os.path.exists(plane_coors2) == False: 
            print("The directory {plane_coors2} does not exist")
            exit
        if os.path.exists(particles2) == False: 
            print("The directory {particles2} does not exist")
            exit


   
    # Start the program 
    print("Hello! Starting TomoDist")
    main()
