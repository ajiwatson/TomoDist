# TomoDist

TomoDist (Tomograms' Distance and Distribution) is used to calculated the normalized distance of particles from the tomogram surface, giving the user insight into the distribution of the particles in the tomogram. It also provides data on the estimated ice thickness of the tomogram and can plot this data using MatPlotLib. The program uses fairly standard python3 libraries and IMOD. 

## External Dependency
This software currently requires IMOD model2point executable to run. I figured this is a common enough software for people working in EM/Tomo that it shouldn't be an unreasonable dependency. Just make sure IMOD model2point is installed and available on your PATH before running. You can check by putting model2point in your terminal and seeing if you get help information. 

## Installation / Tutorial
Use step 0 to install/set up even if you don't want to run the tutorial
### 0. Installation / Setup: Git Clone and Conda Environment
Navigate to whatever directory you generally keep your Git repositories in. Run the commands: 

`git clone https://github.com/ajiwatson/TomoDist.git`

`conda env create -f environment.yml`

`conda activate TomoDist`

### 1. Tutorial start: Unzip tutorial data
Use your preferred method to unzip the Tutorial_Data. These particles were generated using EMPIAR-10164 data and the geometrically constrained particle picking in nextPYP(v0.7.0)(https://github.com/nextpyp). (Note nextPYP is NOT a requirement to run TomoDist, any particle picking method works so long as it can produce .spk files) [Tomography Tutorial](https://nextpyp.app/files/pyp/0.7.0/docs/tutorials/tomo_empiar_10164.html#). Plane coordinates were manually picked. Plane and particle coordinates were exported from nextPYP using the 'Export particle coordinates in IMOD format (sva/*.spk)" option. 

### 2. Run the program! 
Thanks to Mehmet (https://github.com/tasdelenmf) for adding compatability with a config file! Initially, I had a single command with a small army of flags to pass. Edit your config.yml file (If running tutorial the config.yml file comes set up assuming you have unzipped the data inside the Tutorial_Data directory. Change this if you unzipped it somewhere else)

`python3 main.py config.yml`

### 3. Look at your results
If you go into the Results directory you should be able to see the results! Note that the normalized distances are unitless. The ice thickness and visualization plots are all done in nanometers (or unitless if displaying normalized distances). If you want to test the comparison options you can break up the tutorial data into two sets, or simply run it as both datasets being the EMPIAR-10164 dataset. Change the dataname for the second one if you do this though, I'm not sure how the code will behave if the two datanames are the same.


## List of possible parameters and how to use: These should be edited in config.yml file

    Is this essentially just the help information right now..... yes. yes it is. I will continue to improve the docs.  

    *REQUIRED*
    ('-planes', '--plane_coordinates', help="The directory containing points off of which to estimate planes. These points should correspond ot ice contamination")
    ('--particles', help="The directory containing particle picks.")
    ("--pixel_size", help="The binned pixel size of your tomograms given in nanometers")
    ('--tomo_dimensions', help="The dimensions of the binned tomogram, X,Y,Z (Z should typically be smallest dimension)")
    ("--outdir", help="Output directory for plots and results")
    
    *Comparison of two dataset inputs*
    ("--dataname", default=None, help="The name you would like to add to plot labels. Perhaps a sample name or method type. Required if compare is true.")
    ("--compare", default=False, help="Pass if you want to compare multiple datasets. Note, additional flags must be passed.")
    ("-planes2", '--plane_coordinates2', default=None, help="The directory containing points off of which to estimate planes for the second dataset.")
    ("--particles2", default=None, help="The directory containing particle picks for the second dataset.")
    ("--dataname2", default=None, help="The name of the second dataset for camparison. Required if compare is true.")
    
    *Optional data processing/storage inputs*
    ('-bf', "--best_fit", default=False, help="Pass to draw a plane/line of best fit for the particles. Defualt is False")
    ("--keep", default=False, help="Pass to keep the .txt files generated from imod load_point_data. These are xzy corrdinates.")
    ('--z_weight', default=10, help="Amount to weigh in z for performing KMeans clustering. Increase for greater separation, decrease for less. Use whole numbers.")
    
    *Optional visualization inputs*
    ("--rotate", default=False, help="Pass if you wish to also generate a plot where planes are aligned and rotated to lie in the XY plane.")
    ("--plane_color", default='blue', help="Color code for planes in plots")
    ("--bfplane_color", default= 'green', help="Color code for plane of best fit")
    ("--point_color", default='black', help="Color code for points")
    ("--violin_color1", default="blue", help="Color code for the violin plots for dataset 1.")
    ("--violin_color2", default="blue", help="Color code for the violin plots for dataset 2.")

## Publications
Pending publication: Used in "Acoustofluidic Cryo-EM Enables In Situ Particle Manipulation for Uniform, High-Quality Cryo-EM Specimens" to validate the freezing method altered distribution of particles. Planes were manually drawn as code for automated plane detection was not yet written. Datasets were given to be processed blind (ie: I did not know which dataset was frozen with the ACE module)
