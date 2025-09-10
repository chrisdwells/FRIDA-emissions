import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import numpy as np

datadir = '../data'

# We have the present-day irrigation forcing. 
# Assuming the forcing scales with irrigation, we need the timeseries of 
# irrigation to scale this by. 
# We have data from FAOSTAT on irrigated area from 1961-2022, and from 
# Angelakis et al. 2021 https://www.mdpi.com/2073-4441/12/5/1285 for earlier -
# Figure 21 for data points from 1900. Then in the text, it notes (p30) a
# value of 8 mha for 1800 - and we assume the same for 1750.

irrigation_pd_forcing = -0.05 # in pd_years
pd_years = [2019, 2019]
irrigation_zero_forcing = 1750 # force 0 forcing here

units_1000ha_to_Mha = 0.001

df_fao = pd.read_csv(
    f"{datadir}/inputs/FAOSTAT_data_en_2-7-2025.csv",
)

df_fao_crop = df_fao[["Year", "Value"]]

irr_file = f'{datadir}/inputs/Angelakis_fig21_curve_fit.csv'
df_angelakis = pd.read_csv(irr_file)

df_angelakis.loc[len(df_angelakis)] = [1750, 8]
df_angelakis.loc[len(df_angelakis)] = [1800, 8]

df_angelakis = df_angelakis.sort_values(by = ['years'])

fit = CubicSpline(df_angelakis.years, df_angelakis.data)

fao_scaling_factor = units_1000ha_to_Mha*df_fao_crop['Value'
                     ].loc[df_fao_crop['Year'] == 1961].values[0]/fit(1961)

for year in np.arange(1750, 1961, 1):
    df_fao_crop.loc[len(df_fao_crop)] = [year, fao_scaling_factor*fit(year)/units_1000ha_to_Mha]

df_fao_crop = df_fao_crop.sort_values(by = ['Year'])

df_fao_crop['irr_land_offset'] = (df_fao_crop['Value'] - df_fao_crop['Value'
              ].loc[df_fao_crop['Year'] == irrigation_zero_forcing].values[0])

df_fao_crop['irr_land_offset_norm'] = df_fao_crop['irr_land_offset']/np.mean(df_fao_crop[
                        'irr_land_offset'].loc[(df_fao_crop['Year'] >= pd_years[0]) &
                                               (df_fao_crop['Year'] <= pd_years[1])])
                                               
df_fao_crop['irr_erf'] = irrigation_pd_forcing*df_fao_crop['irr_land_offset_norm']

fig = plt.figure(figsize=(12, 10))
plt.plot(df_fao_crop['Year'], df_fao_crop['irr_erf'])
plt.axhline(y=0, color='grey', linestyle='--')
plt.title('Irrigation ERF')
plt.ylabel('W/m2')

plt.tight_layout()
plt.savefig('../figures/irr_erf.png', dpi=100)

df_out = pd.DataFrame(data = {
    'Year':df_fao_crop['Year'],
    'Irrigation ERF':df_fao_crop['irr_erf'],
    })

df_out.to_csv(f'{datadir}/outputs/Irrigation_ERF.csv', index=False)


