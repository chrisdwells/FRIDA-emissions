import pandas as pd
from fair import FAIR
from fair.io import read_properties
from fair.interface import fill, initialise
import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

# This generates the exogenous timeseries of Montreal gas ERF and EESC effect -
# from 1750 to 2022 for the climate calib, and 1980-2130 for FRIDA.

climate_start = int(os.getenv("climate_start"))
climate_end = int(os.getenv("climate_end"))

frida_start = int(os.getenv("frida_start"))
frida_end = int(os.getenv("frida_end"))

# load in data, say which species to change

df_hist_concs = pd.read_csv(
    "data/inputs/ghg_concentrations_1750-2023.csv")

df_hist_concs = df_hist_concs.set_index("YYYY")


montreals = ['CFC-11', 'CFC-12', 'CFC-113', 'CFC-114', 'CFC-115', 
             'HCFC-141b', 'HCFC-142b', 'HCFC-22', 'CCl4', 'CHCl3',
             'CH2Cl2', 'CH3Cl', 'CH3CCl3', 'CH3Br',  
             'Halon-1211', 'Halon-1301', 'Halon-2402'] 
# bin 'Halon-1202' due to missing data - is 0 always anyway


#%%

f_cmip6_hist = FAIR()

f_cmip6_hist.define_time(1750, climate_end+1, 1)
scenarios = ['ssp245']
f_cmip6_hist.define_scenarios(scenarios)
configs = ['test']
f_cmip6_hist.define_configs(configs)
species, properties = read_properties()

f_cmip6_hist.define_species(species, properties)
f_cmip6_hist.allocate()
f_cmip6_hist.fill_species_configs()
f_cmip6_hist.fill_from_rcmip()

initialise(f_cmip6_hist.concentration, f_cmip6_hist.species_configs['baseline_concentration'])
initialise(f_cmip6_hist.forcing, 0)
initialise(f_cmip6_hist.temperature, 0)
initialise(f_cmip6_hist.cumulative_emissions, 0)
initialise(f_cmip6_hist.airborne_emissions, 0)

capacities = [4.22335014, 16.5073541, 86.1841127]
kappas = [1.31180598, 2.61194068, 0.92986733]
epsilon = 1.29020599
fill(f_cmip6_hist.climate_configs['ocean_heat_capacity'], capacities)
fill(f_cmip6_hist.climate_configs['ocean_heat_transfer'], kappas)
fill(f_cmip6_hist.climate_configs['deep_ocean_efficacy'], epsilon)

f_cmip6_hist.run()

#%%


f_new_hist = FAIR()

f_new_hist.define_time(1750, climate_end+1, 1)
scenarios = ['ssp245']
f_new_hist.define_scenarios(scenarios)
configs = ['test']
f_new_hist.define_configs(configs)
species, properties = read_properties()

for spec in montreals:
    properties[spec]['input_mode'] = 'concentration'
    
f_new_hist.define_species(species, properties)
f_new_hist.allocate()
f_new_hist.fill_species_configs()
f_new_hist.fill_from_rcmip()

initialise(f_new_hist.concentration, f_new_hist.species_configs['baseline_concentration'])
initialise(f_new_hist.forcing, 0)
initialise(f_new_hist.temperature, 0)
initialise(f_new_hist.cumulative_emissions, 0)
initialise(f_new_hist.airborne_emissions, 0)

capacities = [4.22335014, 16.5073541, 86.1841127]
kappas = [1.31180598, 2.61194068, 0.92986733]
epsilon = 1.29020599
fill(f_new_hist.climate_configs['ocean_heat_capacity'], capacities)
fill(f_new_hist.climate_configs['ocean_heat_transfer'], kappas)
fill(f_new_hist.climate_configs['deep_ocean_efficacy'], epsilon)


for spec in montreals:
    conc_in = df_hist_concs[spec]
    conc_1750_to_1850 = np.linspace(conc_in[1750], conc_in[1850], 101)
    conc_full = np.concatenate((conc_1750_to_1850, conc_in.loc[conc_in.index > 1850]))
    f_new_hist.concentration[:,0,0, f_new_hist.species.index(spec)] = conc_full
    
f_new_hist.run()

#%%


f_ssps = FAIR()

f_ssps.define_time(1750, 2130, 1)

scenarios = ['ssp119', 'ssp126', 'ssp245', 'ssp370', 'ssp585']
f_ssps.define_scenarios(scenarios)

configs = ['test']
f_ssps.define_configs(configs)

species, properties = read_properties()
    
f_ssps.define_species(species, properties)

f_ssps.allocate()
f_ssps.fill_species_configs()
f_ssps.fill_from_rcmip()

initialise(f_ssps.concentration, f_ssps.species_configs['baseline_concentration'])
initialise(f_ssps.forcing, 0)
initialise(f_ssps.temperature, 0)
initialise(f_ssps.cumulative_emissions, 0)
initialise(f_ssps.airborne_emissions, 0)

capacities = [4.22335014, 16.5073541, 86.1841127]
kappas = [1.31180598, 2.61194068, 0.92986733]
epsilon = 1.29020599
fill(f_ssps.climate_configs['ocean_heat_capacity'], capacities)
fill(f_ssps.climate_configs['ocean_heat_transfer'], kappas)
fill(f_ssps.climate_configs['deep_ocean_efficacy'], epsilon)


f_ssps.run()

#%%

for spec in montreals:
    fig = plt.figure()
    plt.plot(f_cmip6_hist.timebounds,f_cmip6_hist.concentration[:,0,0,f_cmip6_hist.species.index(spec)], label = 'CMIP6 Hist+SSP245')
    plt.plot(f_new_hist.timebounds,f_new_hist.concentration[:,0,0,f_new_hist.species.index(spec)], label = 'Indicators')
        
    for s_i, scen in enumerate(scenarios):
        plt.plot(f_ssps.timebounds, f_ssps.concentration[:,s_i,0,f_new_hist.species.index(spec)], label = scen)

    plt.legend()
    plt.title(spec)

#%%
montreal_idxs = [f_cmip6_hist.species.index(spec) for spec in montreals]

montreal_forcing_cmip6_hist = f_cmip6_hist.forcing[:,0,0,montreal_idxs].sum(axis=1)
montreal_forcing_new_hist = f_new_hist.forcing[:,0,0,montreal_idxs].sum(axis=1)
montreal_forcing_ssps = f_ssps.forcing[:,:,0,montreal_idxs].sum(axis=2)

montreal_forcing_new_hist_present = montreal_forcing_new_hist[np.where(f_new_hist.timebounds==climate_end)]

montreal_forcing_from_present_plus1 = montreal_forcing_ssps[np.where(f_ssps.timebounds>climate_end)]
montreal_forcing_ssp245_from_present_plus1 = montreal_forcing_from_present_plus1[:,scenarios.index('ssp245')]

montreal_forcing_present = montreal_forcing_ssps[np.where(f_ssps.timebounds==climate_end)]
montreal_forcing_ssp245_present = montreal_forcing_present[:,scenarios.index('ssp245')]

scaling_factor = (montreal_forcing_new_hist_present/montreal_forcing_ssp245_present).values[0]


montreal_forcing_ssp245_from_present_plus1_scaled = montreal_forcing_ssp245_from_present_plus1*scaling_factor

montreal_forcing_hist_future_new = np.concatenate((montreal_forcing_new_hist[np.where(f_new_hist.timebounds<=climate_end)],
                                  montreal_forcing_ssp245_from_present_plus1_scaled))

fig = plt.figure()
plt.plot(f_cmip6_hist.timebounds, montreal_forcing_cmip6_hist, label='CMIP6 Hist+SSP245')
plt.plot(f_new_hist.timebounds, montreal_forcing_new_hist, label='Indicators')

for s_i, scen in enumerate(scenarios):
    plt.plot(f_ssps.timebounds, montreal_forcing_ssps[:,s_i], label = scen)

plt.plot(f_ssps.timebounds, montreal_forcing_hist_future_new, label='New combined')

plt.legend()
plt.title('Montreal gases ERF')


#%%

eesc_conc_cmip6_hist = f_cmip6_hist.concentration[:,0,0,f_cmip6_hist.species.index('Equivalent effective stratospheric chlorine')]
eesc_conc_new_hist = f_new_hist.concentration[:,0,0,f_new_hist.species.index('Equivalent effective stratospheric chlorine')]
eesc_conc_ssps = f_ssps.concentration[:,:,0,f_ssps.species.index('Equivalent effective stratospheric chlorine')]

eesc_conc_new_hist_present = eesc_conc_new_hist[np.where(f_new_hist.timebounds==climate_end)]

eesc_conc_from_present_plus1 = eesc_conc_ssps[np.where(f_ssps.timebounds>climate_end)]
eesc_conc_ssp245_from_present_plus1 = eesc_conc_from_present_plus1[:,scenarios.index('ssp245')]

eesc_conc_present = eesc_conc_ssps[np.where(f_ssps.timebounds==climate_end)]
eesc_conc_ssp245_present = eesc_conc_present[:,scenarios.index('ssp245')]

scaling_factor = (eesc_conc_new_hist_present/eesc_conc_ssp245_present).values[0]


eesc_conc_ssp245_from_present_plus1_scaled = eesc_conc_ssp245_from_present_plus1*scaling_factor

eesc_hist_future_new = np.concatenate((eesc_conc_new_hist[np.where(f_new_hist.timebounds<=climate_end)],
                                  eesc_conc_ssp245_from_present_plus1_scaled))

fig = plt.figure()
plt.plot(f_cmip6_hist.timebounds, eesc_conc_cmip6_hist, label='CMIP6 Hist+SSP245')
plt.plot(f_new_hist.timebounds, eesc_conc_new_hist, label='Indicators')

for s_i, scen in enumerate(scenarios):
    plt.plot(f_ssps.timebounds, eesc_conc_ssps[:,s_i], label = scen)

plt.plot(f_ssps.timebounds, eesc_hist_future_new, label='New combined')

plt.legend()
plt.title('EESC conc')


#%%

# add them to the climate calib data, i.e. 1750-2022 (which exists from the 
# other species), and to the FRIDA input data, i.e. 1980-2130 (which is new here)

df_calib = pd.read_csv(
    "data/outputs/climate_calibration_data.csv")

df_calib['Minor GHGs Forcing.Montreal Gases Effective Radiative Forcing'
         ] = montreal_forcing_hist_future_new[np.where(f_ssps.timebounds<=climate_end)]

df_calib['Ozone Forcing.Montreal gases equivalent effective stratospheric chlorine'
         ] = eesc_hist_future_new[np.where(f_ssps.timebounds<=climate_end)]

df_calib.to_csv('data/outputs/climate_calibration_data.csv')


df_frida_inputs = pd.DataFrame()
df_frida_inputs['Year'] = np.arange(frida_start, frida_end+1)
df_frida_inputs = df_frida_inputs.set_index('Year')

df_frida_inputs['Minor GHGs Forcing.Montreal Gases Effective Radiative Forcing'
         ] = montreal_forcing_hist_future_new[np.where((f_ssps.timebounds>=frida_start) & (f_ssps.timebounds<=frida_end))]

df_frida_inputs['Ozone Forcing.Montreal gases equivalent effective stratospheric chlorine'
         ] = eesc_hist_future_new[np.where((f_ssps.timebounds>=frida_start) & (f_ssps.timebounds<=frida_end))]


df_frida_inputs.to_csv('data/outputs/frida_input_data.csv')



df_frida_baselines = pd.read_csv(
    "data/outputs/baseline_values.csv")

df_frida_baselines['Ozone Forcing.Montreal gases equivalent effective stratospheric chlorine 1750'
           ] = eesc_conc_cmip6_hist[np.where(f_cmip6_hist.timebounds==1750)].values[0]

df_frida_baselines.to_csv('data/outputs/baseline_values.csv')

