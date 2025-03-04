import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pooch
from dotenv import load_dotenv
import os

load_dotenv()

# This creates the CO2, CH4, N2O, SO2 Emissions which go into FRIDA for calibration, 
# and the Climate Calibration.
# FRIDA Emissions are from 1980; calibration from 1750; both end 2022 (currently)
# They should overlap exactly - and are checked in 2015

# Get Emissions from various sources, by species. Use Indicators for 1750 concs 
# where needed in FRIDA.

datadir = os.getenv("datadir")

climate_start = int(os.getenv("climate_start"))
climate_end = int(os.getenv("climate_end"))

frida_start = int(os.getenv("frida_start"))
frida_calib_end = int(os.getenv("frida_calib_end"))

# the names assume climate_start = 1750, but it's the end years which we 
# expect to change.

df_climate = pd.DataFrame()
df_climate['Year'] = np.arange(climate_start, climate_end+1)
df_climate = df_climate.set_index('Year')

df_frida = pd.DataFrame()
df_frida['Year'] = np.arange(frida_start, frida_calib_end+1)
df_frida = df_frida.set_index('Year')

df_frida_baselines = pd.DataFrame()
df_frida_baselines['Year'] = [1750]
df_frida_baselines = df_frida_baselines.set_index('Year')

co2_molec_weight = 44.009
c_molec_weight = 12.0107

gtc_to_mtco2 = 1000 * co2_molec_weight/c_molec_weight # gcb
mtc_to_mtco2 = co2_molec_weight/c_molec_weight # gcb

ggn2o_to_ktn2o = 1 # primap

mtn2o_to_ktn2o = 1000 # GFED 

ktch4_to_mtch4 = 0.001 # ceds

ggch4_to_mtch4 = 0.001 # primap

tgch4_to_mtch4 = 1 # GFED

ktso2_to_mtso2 = 0.001 # ceds

df_indicators = pd.read_csv(f'{datadir}/inputs/ghg_concentrations_1750-2023.csv', index_col=0)


#%%
"""
CO2

Use Global Carbon Project. https://globalcarbonbudgetdata.org/latest-data.html
Current version: v2024, v1.0.

Get xlsx, then have to save Fossil Emissions by Category, Historical Budget as 
separate csvs, and delete rows above data.

We use Historical Budget 'fossil Emissions excluding carbonation' for
total fossil Emissions from 1750 for the calibration.

We use Fossil Emissions by Category 'Cement.emission' as FRIDA Cement emissions,
and 'fossil.emissions.excluding.carbonation' minus this as FRIDA Energy emissions.

1750-1850 cumulative land use Emissions are 30GtC from 
https://essd.copernicus.org/articles/15/5301/2023/ - we assume linear to 1850.

Output in MtCO2. Inputs vary between sheets.

"""

# Total budget for calibration
df_gcb_budget = pd.read_csv(
    f"{datadir}/inputs/Global_Carbon_Budget_2024_v1.0_historical_budget.csv")

df_gcb_budget_crop = df_gcb_budget.loc[(df_gcb_budget['Year'] >= climate_start
                                    ) & (df_gcb_budget['Year'] <= climate_end)]

land_use_from_1850 = df_gcb_budget_crop.loc[df_gcb_budget[
                    'Year'] >= 1850]['land-use change emissions']

cumulative_land_use_1750_to_1849 = 30

annual_emissions_1849 = 2*cumulative_land_use_1750_to_1849/100 # assume linear

land_use_1750_to_1850 = np.linspace(0,annual_emissions_1849, 100)

assert np.sum(land_use_1750_to_1850) == cumulative_land_use_1750_to_1849

land_use = np.concatenate((land_use_1750_to_1850, land_use_from_1850))

df_climate['Emissions.CO2 Emissions from Fossil use'] = gtc_to_mtco2*df_gcb_budget_crop[
                                'fossil emissions excluding carbonation'].values

df_climate['Emissions.CO2 Emissions from Food and Land Use'] = gtc_to_mtco2*land_use


# By sector for FRIDA
df_gcb_by_cat = pd.read_csv(
    f"{datadir}/inputs/Global_Carbon_Budget_2024_v1.0_fossil_emissions_by_category.csv")

df_gcb_by_cat_crop = df_gcb_by_cat.loc[(df_gcb_by_cat['Year'] >= frida_start
                                    ) & (df_gcb_by_cat['Year'] <= frida_calib_end)]

df_frida['Concrete.CO2 Emissions[1]'] = mtc_to_mtco2*df_gcb_by_cat_crop['Cement.emission'].values

df_frida['Emissions.CO2 Emissions from Energy[1]'
         ] = mtc_to_mtco2*(df_gcb_by_cat_crop['fossil.emissions.excluding.carbonation'
            ].values - df_gcb_by_cat_crop['Cement.emission'].values)

land_use_frida = df_gcb_budget_crop.loc[(df_gcb_budget_crop['Year'] >= frida_start
                ) & (df_gcb_budget_crop['Year'] <= frida_calib_end)]['land-use change emissions'].values

df_frida['Emissions.CO2 Emissions from Food and Land Use[1]'
         ] = gtc_to_mtco2*land_use_frida                                          

# Make sure consistent between climate calibration and FRIDA calibration
assert df_frida[['Concrete.CO2 Emissions[1]', 'Emissions.CO2 Emissions from Energy[1]',
       'Emissions.CO2 Emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values == df_climate.loc[
       df_climate.index == 2015]['Emissions.CO2 Emissions from Fossil use'
         ].values + df_climate.loc[
         df_climate.index == 2015]['Emissions.CO2 Emissions from Food and Land Use'
           ].values

#%%
                                
"""
N2O

Use PRIMAP-hist data
Current version: 2024 v2.6 https://zenodo.org/records/13752654

Biomass Burning separately, from GFED - averaged due to no process-based 
representation in FRIDA. 

"""

df_primap = pd.read_csv(
    f"{datadir}/inputs/Guetschow_et_al_2024a-PRIMAP-hist_v2.6_final_no_rounding_13-Sep-2024.csv")

df_primap_crop = df_primap.loc[(df_primap['area (ISO3)'] == 'EARTH') &
                               (df_primap['scenario (PRIMAP-hist)'] == 'HISTTP')]


df_primap_n2o_crop = df_primap_crop.loc[df_primap_crop['entity'] == 'N2O']

df_primap_n2o_crop = df_primap_n2o_crop.drop(['source', 'scenario (PRIMAP-hist)', 
      'provenance', 'entity', 'area (ISO3)', 'unit'], axis=1)

df_primap_n2o = df_primap_n2o_crop.set_index('category (IPCC2006_PRIMAP)').transpose()

df_primap_n2o.index = df_primap_n2o.index.astype(int)


df_primap_n2o_frida = df_primap_n2o.loc[(df_primap_n2o.index >= frida_start
                                    ) & (df_primap_n2o.index <= frida_calib_end)]

n2o_energy = df_primap_n2o_frida['1'] + df_primap_n2o_frida['2']
n2o_other = df_primap_n2o_frida['4'] + df_primap_n2o_frida['5']
n2o_food_and_lu = df_primap_n2o_frida['3']


df_frida['Emissions.N2O Emissions from Food and Land Use[1]'
         ] = ggn2o_to_ktn2o*n2o_food_and_lu.values

df_frida['Emissions.N2O Emissions from Other[1]'
         ] = ggn2o_to_ktn2o*n2o_other.values

df_frida['Emissions.N2O Emissions from Energy[1]'
         ] = ggn2o_to_ktn2o*n2o_energy.values


df_primap_n2o_climate = df_primap_n2o.loc[(df_primap_n2o.index >= climate_start
                                    ) & (df_primap_n2o.index <= climate_end)]

df_climate['Emissions.Total N2O Emissions'] = ggn2o_to_ktn2o*(df_primap_n2o_climate['1'
                            ] + df_primap_n2o_climate['2'] + df_primap_n2o_climate['3'
                           ] + df_primap_n2o_climate['4'] + df_primap_n2o_climate['5']).values

df_climate['Emissions.N2O non AFOLU Emissions'] = ggn2o_to_ktn2o*(df_primap_n2o_climate['1'
                            ] + df_primap_n2o_climate['2'] + df_primap_n2o_climate['4'
                               ] + df_primap_n2o_climate['5']).values
               
# BB GFED

df_gfed_n2o = pd.read_csv(
    f"{datadir}/inputs/N2O_BB4CMIP.csv")

df_gfed_n2o_crop = df_gfed_n2o.loc[df_gfed_n2o['region'] == 'World'
             ].drop(['model', 'scenario', 'unit', 'variable', 'region'], 
               axis=1).transpose()

df_gfed_n2o_crop.index = df_gfed_n2o_crop.index.astype(int)

n2o_gfed = df_gfed_n2o_crop.loc[
        (df_gfed_n2o_crop.index >= climate_start) &
        (df_gfed_n2o_crop.index <= climate_end) 
    ].values*mtn2o_to_ktn2o

n2o_gfed_mean = np.mean(n2o_gfed)

df_climate['Emissions.Total N2O Emissions'] += n2o_gfed_mean

df_frida['Emissions.N2O Emissions from Food and Land Use[1]'
          ] += n2o_gfed_mean


# scale N2O emissions to better match concentrations
n2o_scaling = 1.07

df_frida['Emissions.N2O Emissions from Food and Land Use[1]'
         ] = df_frida['Emissions.N2O Emissions from Food and Land Use[1]'
                  ]*n2o_scaling

df_frida['Emissions.N2O Emissions from Other[1]'
         ] = df_frida['Emissions.N2O Emissions from Other[1]'
                  ]*n2o_scaling
                      
df_frida['Emissions.N2O Emissions from Energy[1]'
         ] = df_frida['Emissions.N2O Emissions from Energy[1]'
                  ]*n2o_scaling
                      
df_climate['Emissions.Total N2O Emissions'
       ] = df_climate['Emissions.Total N2O Emissions'
         ]*n2o_scaling

df_climate['Emissions.N2O non AFOLU Emissions'
           ] = df_climate['Emissions.N2O non AFOLU Emissions'
             ]*n2o_scaling
                                                                                   

# baselines
df_frida_baselines['Emissions.N2O Baseline Emissions'] = df_climate.loc[df_climate.index==1750]['Emissions.Total N2O Emissions'].values[0]

df_frida_baselines['Emissions.Baseline N2O non AFOLU Emissions'] = df_climate.loc[df_climate.index==1750]['Emissions.N2O non AFOLU Emissions'].values[0]

# 1750 concentration for FRIDA
df_frida_baselines['N2O Forcing.Atmospheric N2O Concentration 1750'
           ] = df_indicators['N2O'].loc[df_indicators.index==1750].values[0]
          
                                                                         
# Make sure consistent between climate calibration and FRIDA calibration
assert np.around(df_frida[['Emissions.N2O Emissions from Other[1]', 'Emissions.N2O Emissions from Energy[1]',
       'Emissions.N2O Emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values, decimals=3) == np.around(df_climate.loc[
       df_climate.index == 2015]['Emissions.Total N2O Emissions'].values, decimals=3)


#%%

"""
CH4

1970 onwards (by sector) from CEDS https://zenodo.org/records/12803197
Pre-1970 (for climate, so summed over all sources) from PRIMAP-hist

Biomass Burning separately, from GFED - averaged due to no process-based 
representation in FRIDA.

"""

df_ch4_ceds = pd.read_csv(
    f"{datadir}/inputs/CH4_CEDS_global_emissions_by_sector_v2024_07_08.csv")

ceds_to_frida_ch4 = {
    "1A1a_Electricity-autoproducer":"Energy",
    "1A1a_Electricity-public":"Energy",
    "1A1a_Heat-production":"Energy",
    "1A1bc_Other-transformation":"Energy",
    "1A2a_Ind-Comb-Iron-steel":"Energy",
    "1A2b_Ind-Comb-Non-ferrous-metals":"Energy",
    "1A2c_Ind-Comb-Chemicals":"Energy",
    "1A2d_Ind-Comb-Pulp-paper":"Energy",
    "1A2e_Ind-Comb-Food-tobacco":"Energy",
    "1A2f_Ind-Comb-Non-metalic-minerals":"Energy",
    "1A2g_Ind-Comb-Construction":"Energy",
    "1A2g_Ind-Comb-machinery":"Energy",
    "1A2g_Ind-Comb-mining-quarying":"Energy",
    "1A2g_Ind-Comb-other":"Energy",
    "1A2g_Ind-Comb-textile-leather":"Energy",
    "1A2g_Ind-Comb-transpequip":"Energy",
    "1A2g_Ind-Comb-wood-products":"Energy",
    "1A3ai_International-aviation":"Energy",
    "1A3aii_Domestic-aviation":"Energy",
    "1A3b_Road":"Energy",
    "1A3c_Rail":"Energy",
    "1A3di_International-shipping":"Energy",
    "1A3di_Oil_Tanker_Loading":"Energy",
    "1A3dii_Domestic-navigation":"Energy",
    "1A3eii_Other-transp":"Energy",
    "1A4a_Commercial-institutional":"Energy",
    "1A4b_Residential":"Energy",
    "1A4c_Agriculture-forestry-fishing":"Energy",
    "1A5_Other-unspecified":"Energy",
    "1B1_Fugitive-solid-fuels":"Energy",
    "1B2_Fugitive-petr":"Energy",
    "1B2b_Fugitive-NG-distr":"Energy",
    "1B2b_Fugitive-NG-prod":"Energy",
    "1B2d_Fugitive-other-energy":"Energy",
    "2A1_Cement-production":"Energy",
    "2A2_Lime-production":"Energy",
    "2Ax_Other-minerals":"Energy",
    "2B_Chemical-industry":"Energy",
    "2B2_Chemicals-Nitric-acid":"Energy",
    "2B3_Chemicals-Adipic-acid":"Energy",
    "2C1_Iron-steel-alloy-prod":"Energy",
    "2C3_Aluminum-production":"Energy",
    "2C4_Non-Ferrous-other-metals":"Energy",
    "2D_Chemical-products-manufacture-processing":"Energy",
    "2D_Degreasing-Cleaning":"Energy",
    "2D_Other-product-use":"Energy",
    "2D_Paint-application":"Energy",
    "2H_Pulp-and-paper-food-beverage-wood":"Energy",
    "3B_Manure-management":"Food and Land Use",
    "3D_Rice-Cultivation":"Food and Land Use",
    "3D_Soil-emissions":"Food and Land Use",
    "3E_Enteric-fermentation":"Food and Land Use",
    "3I_Agriculture-other":"Food and Land Use",
    "5A_Solid-waste-disposal":"Other",
    "5C_Waste-combustion":"Other",
    "5D_Wastewater-handling":"Other",
    "5E_Other-waste-handling":"Other",
    "6A_Other-in-total":"Other",
    "6B_Other-not-in-total":"Other",
    "7A_Fossil-fuel-fires":"Energy",
    "7BC_Indirect-N2O-non-agricultural-N":"Other",
    }

df_ceds_crop = df_ch4_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_ceds_crop.index]

for sector in ["Energy", "Food and Land Use", "Other"]:
    ceds_sectors = [key for key, value in ceds_to_frida_ch4.items() if value == sector]
    
    df_sector_sum = ktch4_to_mtch4*df_ceds_crop[ceds_sectors].sum(axis=1)
    
    df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= frida_start
                                        ) & (df_sector_sum.index <= frida_calib_end)]

    df_frida[f'Emissions.CH4 Emissions from {sector}[1]'] = df_sector_sum_frida.values
    
# BB from GFED - add to land use

rcmip_emissions_file = pooch.retrieve(
    url="doi:10.5281/zenodo.4589756/rcmip-emissions-annual-means-v5-1-0.csv",
    known_hash="md5:4044106f55ca65b094670e7577eaf9b3",
)

df_emis = pd.read_csv(rcmip_emissions_file)

ch4_afolu_pre_1997 = (
    df_emis.loc[
        (df_emis["Scenario"] == 'historical')
        & (
            df_emis["Variable"] == 'Emissions|CH4|MAGICC AFOLU'
        )
        & (df_emis["Region"] == "World"),
        f"{climate_start}":"1996",
    ]
    .interpolate(axis=1)
    .values.squeeze()
)

ch4_agri_pre_1997 = (
    df_emis.loc[
        (df_emis["Scenario"] == 'historical')
        & (
            df_emis["Variable"] == 'Emissions|CH4|MAGICC AFOLU|Agriculture'
        )
        & (df_emis["Region"] == "World"),
        f"{climate_start}":"1996",
    ]
    .interpolate(axis=1)
    .values.squeeze()
)


ch4_gfed_pre_1997 = ch4_afolu_pre_1997 - ch4_agri_pre_1997

df_gfed = pd.read_csv(
    f"{datadir}/inputs/gfed4.1s_1997-2023.csv")

ch4_gfed_1997_plus = df_gfed['CH4'].loc[
            df_gfed['Unnamed: 0'] <= climate_end].values*tgch4_to_mtch4
ch4_gfed = np.concatenate((ch4_gfed_pre_1997, ch4_gfed_1997_plus))
ch4_gfed_mean = np.mean(ch4_gfed)

df_frida['Emissions.CH4 Emissions from Food and Land Use[1]'
         ] += ch4_gfed_mean



# pre-1971 for climate calibration
df_ceds_sum = ktch4_to_mtch4*df_ceds_crop.sum(axis=1) 

df_primap_ch4_crop = df_primap_crop.loc[(df_primap_crop['entity'] == 'CH4')
                        & (df_primap_crop['category (IPCC2006_PRIMAP)'] == '0')]

df_primap_ch4_crop = df_primap_ch4_crop.drop(['source', 'scenario (PRIMAP-hist)', 
      'provenance', 'entity', 'area (ISO3)', 'unit'], axis=1)

df_primap_ch4 = df_primap_ch4_crop.set_index('category (IPCC2006_PRIMAP)').transpose()

df_primap_ch4.index = df_primap_ch4.index.astype(int)



primap_scaling_factor = df_ceds_sum.loc[df_ceds_sum.index == 1970].values[0
          ]/(ggch4_to_mtch4*df_primap_ch4.loc[df_primap_ch4.index == 1970].values[0][0])

ch4_for_climate  = np.concatenate((primap_scaling_factor*ggch4_to_mtch4*df_primap_ch4.loc[
    df_primap_ch4.index < 1970].values[:,0], df_ceds_sum.values))

df_climate['Emissions.Total CH4 Emissions'] = ch4_for_climate + ch4_gfed_mean

df_frida_baselines['Emissions.CH4 Baseline Emissions'] = df_climate.loc[df_climate.index==1750]['Emissions.Total CH4 Emissions'].values[0]

df_frida_baselines['CH4 Forcing.Atmospheric CH4 Concentration 1750'
           ] = df_indicators['CH4'].loc[df_indicators.index==1750].values[0]
                              
# Make sure consistent between climate calibration and FRIDA calibration
assert np.around(df_frida[['Emissions.CH4 Emissions from Other[1]', 'Emissions.CH4 Emissions from Energy[1]',
       'Emissions.CH4 Emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values[0], decimals=3) == np.around(df_climate.loc[
       df_climate.index == 2015]['Emissions.Total CH4 Emissions'].values[0], decimals=3)

                                                                    
#%%

"""
SO2

Assume all CEDS data is Energy.

Use GFED 4.1s for biomass burning, aggregated here from 1997:
https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/gfed4.1s_1997-2023.csv
and from RCMIP for pre-1997. Since FRIDA doesn't have process-based BB emissions, 
use the historical average. 

Baseline SO2 Emissions are the BB Emissions plus the 1750 CEDS emissions, to 
ensure forcing is 0 in 1750.
                   
"""

df_so2_ceds = pd.read_csv(
    f"{datadir}/inputs/SO2_CEDS_global_emissions_by_sector_v2024_07_08.csv")

df_so2_ceds_crop = df_so2_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_so2_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_so2_ceds_crop.index]

df_sector_sum = ktso2_to_mtso2*df_so2_ceds_crop.sum(axis=1)
    
df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= frida_start
                                    ) & (df_sector_sum.index <= frida_calib_end)]

df_frida['Emissions.SO2 Emissions from Energy[1]'] = df_sector_sum_frida.values
    

df_sector_sum_climate = df_sector_sum.loc[(df_sector_sum.index >= climate_start
                                    ) & (df_sector_sum.index <= climate_end)]


so2_gfed_pre_1997 = (
    df_emis.loc[
        (df_emis["Scenario"] == 'historical')
        & (
            df_emis["Variable"] == 'Emissions|Sulfur|MAGICC AFOLU'
        )
        & (df_emis["Region"] == "World"),
        f"{climate_start}":"1996",
    ]
    .interpolate(axis=1)
    .values.squeeze()
)

so2_gfed_1997_plus = df_gfed['SO2'].loc[
            df_gfed['Unnamed: 0'] <= climate_end].values
so2_gfed = np.concatenate((so2_gfed_pre_1997, so2_gfed_1997_plus))
so2_gfed_mean = np.mean(so2_gfed)

df_frida['Emissions.SO2 Emissions from Food and Land Use[1]'
         ] = np.repeat(so2_gfed_mean, frida_calib_end - frida_start + 1)



df_climate['Emissions.Total SO2 Emissions'
         ] = df_sector_sum_climate.values + so2_gfed_mean

df_frida_baselines['Emissions.SO2 Baseline Emissions'] = df_climate.loc[df_climate.index==1750]['Emissions.Total SO2 Emissions'].values[0]

# Make sure consistent between climate calibration and FRIDA calibration
assert df_frida[['Emissions.SO2 Emissions from Energy[1]',
       'Emissions.SO2 Emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values == df_climate.loc[
       df_climate.index == 2015]['Emissions.Total SO2 Emissions'].values

           
#%%

for spec in ['CO2', 'N2O', 'CH4', 'SO2']:
    fig = plt.figure()
    
    if spec == 'CO2':
        plt.plot(df_climate.index, 
         df_climate[f'Emissions.{spec} Emissions from Fossil use'
            ] + df_climate[f'Emissions.{spec} Emissions from Food and Land Use'], 
         label='Total for Calibration')

    else:    
        plt.plot(df_climate.index, df_climate[f'Emissions.Total {spec} Emissions'], label='Total for Calibration')

    frida_vars = [var for var in df_frida.keys() if spec in var]
    # plt.plot(df_frida.index, df_frida[frida_vars])
    plt.plot(df_frida.index, df_frida[frida_vars].sum(axis=1), label='FRIDA Sum')
    
    plt.title(spec)    
    plt.legend()
    plt.xlim([1950, 2024])


#%%

df_frida.to_csv(f'{datadir}/outputs/frida_calibration_data.csv')
df_climate.to_csv(f'{datadir}/outputs/climate_calibration_data.csv')
df_frida_baselines.to_csv(f'{datadir}/outputs/baseline_values.csv')
