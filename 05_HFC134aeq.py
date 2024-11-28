import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

# This makes the HFC134a equivalent emissions for the minor GHGs in FRIDA.
# This makes the emissions that drive the climate calibration, and are used
# for the FRIDA calibration - since these emissions are modelled.

climate_start = int(os.getenv("climate_start"))
climate_end = int(os.getenv("climate_end"))

frida_start = int(os.getenv("frida_start"))
frida_calib_end = int(os.getenv("frida_calib_end"))

years = np.arange(climate_start, climate_end+1)

# get IGCC GHGS
df = pd.read_csv('data/inputs/ghg_concentrations_1750-2023.csv', index_col=0)

f_gases = ['CF4', 'C2F6', 'C3F8', 'c-C4F8', 'n-C4F10', 'n-C5F12',
       'n-C6F14', 'i-C6F14', 'C7F16', 'C8F18', 'NF3', 'SF6', 'SO2F2', 'HFC-125',
       'HFC-134a', 'HFC-143a', 'HFC-152a', 'HFC-227ea', 'HFC-23',
       'HFC-236fa', 'HFC-245fa', 'HFC-32', 'HFC-365mfc', 'HFC-43-10mee']

# source: Hodnebrog et al 2020 https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2019RG000691
radeff = {
    'HFC-125':      0.23378,
    'HFC-134a':     0.16714,
    'HFC-143a':     0.168,
    'HFC-152a':     0.10174,
    'HFC-227ea':    0.27325,
    'HFC-23':       0.19111,
    'HFC-236fa':    0.25069,
    'HFC-245fa':    0.24498,
    'HFC-32':       0.11144,
    'HFC-365mfc':   0.22813,
    'HFC-43-10mee': 0.35731,
    'NF3':          0.20448,
    'C2F6':         0.26105,
    'C3F8':         0.26999,
    'n-C4F10':      0.36874,
    'n-C5F12':      0.4076,
    'n-C6F14':      0.44888,
    'i-C6F14':      0.44888,
    'C7F16':        0.50312,
    'C8F18':        0.55787,
    'CF4':          0.09859,
    'c-C4F8':       0.31392,
    'SF6':          0.56657,
    'SO2F2':        0.21074,
    'CCl4':         0.16616,
    'CFC-11':       0.25941,
    'CFC-112':      0.28192,
    'CFC-112a':     0.24564,
    'CFC-113':      0.30142,
    'CFC-113a':     0.24094, 
    'CFC-114':      0.31433,
    'CFC-114a':     0.29747,
    'CFC-115':      0.24625,
    'CFC-12':       0.31998,
    'CFC-13':       0.27752,
    'CH2Cl2':       0.02882,
    'CH3Br':        0.00432,
    'CH3CCl3':      0.06454,
    'CH3Cl':        0.00466,
    'CHCl3':        0.07357,
    'HCFC-124':     0.20721,
    'HCFC-133a':    0.14995,
    'HCFC-141b':    0.16065,
    'HCFC-142b':    0.19329,
    'HCFC-22':      0.21385,
    'HCFC-31':      0.068,
    'Halon-1202':   0,       # not in dataset
    'Halon-1211':   0.30014,
    'Halon-1301':   0.29943,
    'Halon-2402':   0.31169,
    'CO2':          0,       # different relationship
    'CH4':          0,       # different relationship
    'N2O':          0        # different relationship
}

hfc134a_eq = np.zeros(climate_end - climate_start + 1)
for gas in f_gases:
    
    conc_in = df[gas]
    
    conc_1750_to_1850 = np.linspace(conc_in[1750], conc_in[1850], 101)
    conc_full = np.concatenate((conc_1750_to_1850, conc_in.loc[(conc_in.index > 1850) 
                                                           & (conc_in.index <= climate_end)]))

    hfc134a_eq = hfc134a_eq + conc_full * radeff[gas] / radeff['HFC-134a']


#%%
# back calculate emissions
lifetime = 14
decay_rate = 1 / lifetime
decay_factor = np.exp(-decay_rate)

mass_atmosphere = 5.1352e18 # kg
molecular_weight_air = 28.97 # g/mol
molecular_weight_hfc134a = 102.03 # g/mol

concentration_per_emission = 1 / (
    mass_atmosphere / 1e18 * molecular_weight_hfc134a / molecular_weight_air
)


#%%

# change in conc between year i-1 and year i is attributable to emissions in year i

hfc134a_eq_minus_baseline = hfc134a_eq - hfc134a_eq[0]

anthro_ems = np.zeros(climate_end - climate_start + 1)
for i in range(1, climate_end - climate_start + 1):
    anthro_ems[i] = (hfc134a_eq_minus_baseline[i] - hfc134a_eq_minus_baseline[i-1
                       ]*decay_factor)/concentration_per_emission
  

#%%

df_calib = pd.read_csv(
    "data/outputs/climate_calibration_data.csv")
df_calib['Emissions.HFC134a eq Emissions'] = anthro_ems

df_frida_baselines = pd.read_csv(
    "data/outputs/baseline_values.csv")
df_frida_baselines['Minor GHGs Forcing.Atmospheric HFC134a eq Concentration 1750'
               ] = hfc134a_eq[0]


df_frida_calib = pd.read_csv(
    "data/outputs/frida_calibration_data.csv")
df_frida_calib['Emissions.HFC134a eq Emissions[1]'] = anthro_ems[np.where((years >= frida_start) 
                                                   & (years <= frida_calib_end))]

df_calib.to_csv('data/outputs/climate_calibration_data.csv')
df_frida_baselines.to_csv('data/outputs/baseline_values.csv')
df_frida_calib.to_csv('data/outputs/frida_calibration_data.csv')

