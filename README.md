# Target
Target stands for The Air-temperature Response to Green/blue-infrastructure Evaluation Tool. Check out the [publication](https://www.geosci-model-dev.net/12/785/2019/gmd-12-785-2019.html).
## Installation

### Git
```sh 
git clone https://gitlab.ethz.ch/chenjix/target-v1.0.git
pip install target-v1.0/
```


### No Git

Download the repository. Unpack the downloaded repo and then install the package via pip.
```sh
pip install <path-to-unpacked-repo>
```
Use `./` as `<path-to-unpacked-repo>`, if your terminal's working directory is the unpacked target folder.


## Usage

### Option 1 - via Python

```python
from target import Target
from target import generate_example
import os

# generate example input data your home directory
home_path = os.path.expanduser("~")
generate_example(
    path=home_path,        # where to generate the example
    site_name="my_site",   # the examples site name
    run_name="my_run",     # the simulation's run name
    obs=False,             # do not generate observation to sample data for later validation
    grid=False,             # generate a non-grid example
    empty=False            # do not generate an empty example
)

# creating a model instance and loading configuration 
conf_path = os.path.join(home_path, "my_site","config.ini")
tar = Target(
  conf_path,            # passing the simulation's config file
  progress=True         # show progress bars
  )
tar.load_config()

# run simulation
tar.run_simulation(
    save_csv=True,      # save model results in csv format
)

# save parameters and config used for simulation
tar.save_simulation_parameters()
```


### Option 2 - via Terminal

Get the command line interface's help:
```sh
python -m target --help
```
Two possible tasks are available `run` and `gen`.
You might want to check out their help sections:
```sh 
python -m target run --help
python -m target gen --help
```

Generate an example:
```sh
python -m target gen -p "your-desired-path" --site my_site --run my_run_name
```

You can also generate an 'empty' example, which will only create the folder structure, configuration file and parameters file:
```sh
python -m target gen -p "your-desired-path" --empty --site my_new_site --run my_run_name
```

**Run the model:**
 - pass configuration file `-c`
 - showing a progress bar during simulation `-p`
 - saving output in csv files `--save-csv`
```sh
python -m target run -c "path-to-ini-file"  -p --save-csv
```

## Tips - Parameters

You can write `formulas` in the `parameters.json`. 
These will be parsed and calculated using the math module of python.
`List values can not be used for formulas!`

In order to write a formula, the entry must start with `"formula_"`.
Functions from the python `math` module must be referred to using the module. 
For Example `math.sqrt()` not `sqrt()`.
Dependencies to other parameters can be formulated with  a dollar sign `$`.
Getting the value `K` for `SoilW = saturated soil layer benath water` can be accessed like this `$K_soilW`.
An underscore `_` signifies a nested value. (Nested as in two keywords.)

A example for a valid formula would be:
```
formula_math.sqrt(2.*$K_soilW/(2.*math.pi / 86400.)*$cp)
```




## Notes

The target air temp modules use "control files" to the run simulations.

In the control file the user must define:


>**work_dir** - directory where input and output is stored  
>**para_json_path** - path to parameters filer  
>**site name** - string that creates folders for different sites  
>**run name**   - string for name of run  
>**inpt_met_file** - file name of input meteorological file  
>**inpt_lc_file** - file name of input land cover file  
>**date_fmt**  - format of datetime in input met files  
>**timestep** - number of minutes for each timestep (30 min is recommended)  
>**date1A** - start date for simulation (should be a minimum of 24 hours prior to date1)  
>**date1** - start date for validation period  
>**date2** - end of model run  



The other fields in the control file are for setting up model validation and generating output plots. The plotting scripts are not yet setup for general use. However, if you run either of the two example control files they should work.  

### There are example control files for two different model runs

**Input files:**

Each run requires input Meteorology file and input land cover file in the provided example: 

- Input meteorology should be placed in ./**site_name**/input/MET/
- Input land cover should be placed in ./**site_name**/input/LC/

File names for each input file are defined the in control file. 


#### Met forcing file must have following fields (in any order):

>**datetime** (format for this can be set in control file):  
>**Ta** (air temperature in C)  
>**RH** (relative humidity)  
>**WS** (wind speed in ms-1)  
>**P**  (pressure in hPa)
>**Kd** (incoming shortwave Wm-2)  
>**Ld** (incoming longwave Wm-2)  

The land cover data must have the fraction of each land cover type and building heights and street widths (m) (keep headers the same as example). The “FID” is the identifier for each point – this can be stations numbers (as in the Mawson_stations eg) or grid cells. In the case of the Mawson grid, the FID values correspond to a grid shape file (.shp), so output can easily mapped to a GIS grid. 


**Outputs:**

At the moment, the code dumps the output as a numpy array (*.npy) in ./**site name**/output/_run name_.npy

This can be read with `numpy.load`

The array has the following cols:

>**ID** – same as FID
>**Ws** – wind speed     
>**Ts** – surface temperature  
>**Ta** – canyon air temperature  
>**Rn** net radiation  
>**Qg** -storage flux  
>**Qe** – latent heat flux  
>**Qh** - sensible heat flux  
>**date** – datetime object  

You can index the array to desired ID and/or times and then output the variables. I'm sure there is a better way to this... but that is that at the moment. 


#### The LC shp file must have following fields:

>**FID** (object id)
>**roof** (percent)  
>**road** (percent)  
>**watr** (percent)  
>**conc**  (percent)
>**Veg** (percent)  
>**dry** (percent)  
>**irr** (percent)  
>**H** (house height)  
>**W** (canyon width)

##### Important

*W (canyon width) my not be 0!*
