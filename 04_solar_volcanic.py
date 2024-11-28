import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
# import pooch
# import pickle
from fair import FAIR
from fair.io import read_properties
from fair.interface import fill, initialise
from dotenv import load_dotenv
import os

load_dotenv()

# This makes the natural forcing timeseries, currently just using FaIR

climate_start = int(os.getenv("climate_start"))
climate_end = int(os.getenv("climate_end"))

frida_start = int(os.getenv("frida_start"))
frida_end = int(os.getenv("frida_end"))

df_frida = pd.read_csv(
    "data/outputs/frida_input_data.csv")
df_frida = df_frida.set_index('Year')

df_climate = pd.read_csv(
    "data/outputs/climate_calibration_data.csv")
df_climate = df_climate.set_index('Year')

#%%

min_start = np.amin((climate_start, frida_start))
max_end = np.amax((climate_end, frida_end))

f_cmip6 = FAIR()

f_cmip6.define_time(min_start, max_end+1, 1)

scenarios = ['ssp245']
f_cmip6.define_scenarios(scenarios)
configs = ['test']
f_cmip6.define_configs(configs)
species, properties = read_properties()

f_cmip6.define_species(species, properties)
f_cmip6.allocate()
f_cmip6.fill_species_configs()
f_cmip6.fill_from_rcmip()

initialise(f_cmip6.concentration, f_cmip6.species_configs['baseline_concentration'])
initialise(f_cmip6.forcing, 0)
initialise(f_cmip6.temperature, 0)
initialise(f_cmip6.cumulative_emissions, 0)
initialise(f_cmip6.airborne_emissions, 0)

capacities = [4.22335014, 16.5073541, 86.1841127]
kappas = [1.31180598, 2.61194068, 0.92986733]
epsilon = 1.29020599
fill(f_cmip6.climate_configs['ocean_heat_capacity'], capacities)
fill(f_cmip6.climate_configs['ocean_heat_transfer'], kappas)
fill(f_cmip6.climate_configs['deep_ocean_efficacy'], epsilon)

f_cmip6.run()

#%%

solar_forcing = f_cmip6.forcing[:,0,0,f_cmip6.species.index("Solar")]
volc_forcing = f_cmip6.forcing[:,0,0,f_cmip6.species.index("Volcanic")]


#%%
df_frida['Natural Forcing.Baseline Effective Radiative Forcing from Solar Output Variations'
         ] = solar_forcing[np.where((f_cmip6.timebounds >= frida_start) & 
                                    (f_cmip6.timebounds <= frida_end))]

df_climate['Natural Forcing.Baseline Effective Radiative Forcing from Solar Output Variations'
         ] = solar_forcing[np.where((f_cmip6.timebounds >= climate_start) & 
                                    (f_cmip6.timebounds <= climate_end))]  
                                    
                                    
df_frida['Natural Forcing.Baseline Effective Radiative Forcing from Volcanoes'
         ] = volc_forcing[np.where((f_cmip6.timebounds >= frida_start) & 
                                    (f_cmip6.timebounds <= frida_end))]

df_climate['Natural Forcing.Baseline Effective Radiative Forcing from Volcanoes'
         ] = volc_forcing[np.where((f_cmip6.timebounds >= climate_start) & 
                                    (f_cmip6.timebounds <= climate_end))]    

#%%

df_frida.to_csv('data/outputs/frida_input_data.csv')
df_climate.to_csv('data/outputs/climate_calibration_data.csv')
