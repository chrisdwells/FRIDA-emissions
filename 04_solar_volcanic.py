import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
import pooch
# import pickle
from dotenv import load_dotenv
import os

load_dotenv()

# This makes the natural forcing timeseries; uses updated values to 2025, then
# CMIP6 approach after.

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


rcmip_forcing_file = pooch.retrieve(
    url=(
        "doi:10.5281/zenodo.4589756/"
        "rcmip-radiative-forcing-annual-means-v5-1-0.csv"
    ),
    known_hash="md5:87ef6cd4e12ae0b331f516ea7f82ccba",
)

df_forc = pd.read_csv(rcmip_forcing_file)

forc_in = (
    df_forc.loc[
        (df_forc["Scenario"] == 'ssp245')
        & (
            df_forc["Variable"].str.endswith(
                "|" + 'Solar'
            )
        )
        & (df_forc["Region"] == "World"),
        "2024":f"{frida_end-1}",
    ]
    .interpolate(axis=1)
    .values.squeeze()
)

#%%

df_forcings = pd.read_csv(
    "data/inputs/volcanic_solar.csv")

df_volc = df_forcings.loc[(df_forcings['Scenario'] == 'ssp245') & (df_forcings['Variable'] == 'Volcanic')].drop(['Scenario', 'Region', 'Unit', 'Variable'], axis=1).transpose()
df_volc.index = df_volc.index.astype(int)

df_solar = df_forcings.loc[(df_forcings['Scenario'] == 'ssp245') & (df_forcings['Variable'] == 'Solar')].drop(['Scenario', 'Region', 'Unit', 'Variable'], axis=1).transpose()
df_solar.index = df_solar.index.astype(int)


solar_extended = np.concatenate((df_solar.loc[(df_solar.index >= frida_start+1) & (df_solar.index <= frida_end+1)].values[:,0],
                    forc_in))

volc_initial = df_volc.loc[(df_volc.index >= frida_start+1) & (df_volc.index <= frida_end+1)].values[:,0]

volc_extended = np.concatenate((volc_initial, np.linspace(volc_initial[-1], 0, 10), np.zeros(frida_end - frida_start - volc_initial.shape[0] - 10 + 1)))

#%%
df_frida['Natural Forcing.Baseline Effective Radiative Forcing from Solar Output Variations'
          ] = solar_extended

df_climate['Natural Forcing.Baseline Effective Radiative Forcing from Solar Output Variations'
         ] = df_solar.loc[(df_solar.index >= climate_start+1) & (df_solar.index <= climate_end+1)].values[:,0]


df_frida['Natural Forcing.Baseline Effective Radiative Forcing from Volcanoes'
          ] = volc_extended

df_climate['Natural Forcing.Baseline Effective Radiative Forcing from Volcanoes'
         ] = df_volc.loc[(df_volc.index >= climate_start+1) & (df_volc.index <= climate_end+1)].values[:,0]

#%%

df_frida.to_csv('data/outputs/frida_input_data.csv')
df_climate.to_csv('data/outputs/climate_calibration_data.csv')


#%%
