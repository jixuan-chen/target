from target import Target
from target import generate_example
import os

# generate example input data your home directory
home_path = r'C:\Users\jxche\Thesis\Simulations'
run_name = 'Zurich_4days'
site_name = 'InnerZurich_new'
folder = os.path.join(home_path, site_name, 'output')
save_folder = os.path.join(home_path, site_name, 'output', 'plot', run_name)

# creating a model instance passing in a configuration file
# and loading the configuration data
conf_path = os.path.join(home_path, site_name, "config_Zurich_4days.ini")
t = Target(conf_path)
t.load_config()

# run simulation and saving result in csv files
t.run_simulation()

# save parameters and config used for simulation
t.save_simulation_parameters()


