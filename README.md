# TomoDist

TomoDist (Tomograms' Distance and Distribution) is used to calculated the normalized distance of particles from the tomogram surface, giving the user insight into the distribution of the particles in the tomogram. It also provides data on the estimated ice thickness of the tomogram and can plot this data using MatPlotLib. The program uses fairly standard python3 libraries and IMOD. 

## External Dependency
This software requires Python 3.12+ and currently requires IMOD model2point executable to run. I figured this is a common enough software for people working in EM/Tomo that it shouldn't be an unreasonable dependency. Just make sure IMOD model2point is installed and available on your PATH before running. You can check by putting model2point in your terminal and seeing if you get help information. 

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
Thanks to Mehmet Tasdelen (https://github.com/tasdelenmf) for adding compatability with a config file! Initially, I had a single command with a small army of flags to pass. Edit your config.yml file (If running tutorial the config.yml file comes set up assuming you have unzipped the data inside the Tutorial_Data directory. Change this if you unzipped it somewhere else)

`python3 main.py config.yml`

### 3. Look at your results
If you go into the Results directory you should be able to see the results! Note that the normalized distances are unitless. The ice thickness and visualization plots are all done in nanometers (or unitless if displaying normalized distances). If you want to test the comparison options you can break up the tutorial data into two sets, or simply run it as both datasets being the EMPIAR-10164 dataset. Change the dataname for the second one if you do this though, I'm not sure how the code will behave if the two datanames are the same.


## Configuration Parameters

All parameters are set in `config.yml`. See the example file included in the repository.

### Required

| Parameter | Description |
|---|---|
| `planes_dir` | Directory containing .spk files with plane coordinates (ice contamination points) |
| `particles_dir` | Directory containing .spk files with particle picks |
| `pixel_size` | Binned pixel size of your tomograms in nanometers |
| `tomo_dimensions` | Dimensions of the binned tomogram as `X,Y,Z` (Z should typically be the smallest dimension) |
| `output_dir` | Output directory for plots and results |
| `dataname` | Name for plot labels (e.g. sample name or method type) |

### Comparison of two datasets

| Parameter | Default | Description |
|---|---|---|
| `compare` | `False` | Set to `True` to compare two datasets |
| `planes_dir_2` | `None` | Plane coordinates directory for the second dataset (required if `compare` is True) |
| `particles_dir_2` | `None` | Particle picks directory for the second dataset (required if `compare` is True) |
| `dataname_2` | `None` | Dataset name for the second dataset (required if `compare` is True) |

### Optional data processing

| Parameter | Default | Description |
|---|---|---|
| `best_fit` | `True` | Calculate and draw a best-fit plane through the particles |
| `keep` | `False` | Keep the intermediate .txt files generated from .spk conversion |
| `z_weight` | `10` | Weighting for z-dimension in KMeans clustering. Increase for greater separation, decrease for less. Use whole numbers. |

### Optional visualization

| Parameter | Default | Description |
|---|---|---|
| `plane_color` | `'blue'` | Color for ice boundary planes in plots |
| `bfplane_color` | `'green'` | Color for best-fit plane in plots |
| `point_color` | `'black'` | Color for particle points in plots |
| `violin_color1` | `'blue'` | Color for violin plots (dataset 1) |
| `violin_color2` | `'blue'` | Color for violin plots (dataset 2) |

## Publications
Pending publication: Used in "Acoustofluidic Cryo-EM Enables In Situ Particle Manipulation for Uniform, High-Quality Cryo-EM Specimens" to validate the freezing method altered distribution of particles. Planes were manually drawn as code for automated plane detection was not yet written. Datasets were given to be processed blind (ie: I did not know which dataset was frozen with the ACE module)

### Running Publication data tutorial
When I originally wrote this code to process data for "Acoustofluidic Cryo-EM Enables In Situ Particle Manipulation for Uniform, High-Quality Cryo-EM Specimens", I had not yet devised a method for automated plane detection. As such, the data included for the publication has manually determined planes and particles and instructions on how you would get those yourself. On this ReadMe are only instructions for running the analysis once you have the planes and particles. 

Everything is hardcoded for the publication data results: 
Activate the conda environment (see Tutorial)
Enter command: 

python3 RunKaichunsData.py