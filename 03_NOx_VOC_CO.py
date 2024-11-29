
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# import pooch
# import pickle
from fair import FAIR
from fair.io import read_properties
from fair.interface import fill, initialise
from sklearn.linear_model import LinearRegression
from dotenv import load_dotenv
import os

load_dotenv()

# This makes the NOx, VOC, CO timeseries used for the FRIDA calibration. CEDS + GFED.
# It also makes the regression coefficients used in both. 

climate_start = int(os.getenv("climate_start"))
climate_end = int(os.getenv("climate_end"))

frida_start = int(os.getenv("frida_start"))
frida_calib_end = int(os.getenv("frida_calib_end"))

ktco_to_mtco = 0.001 # ceds
ktvoc_to_mtvoc = 0.001 # ceds
ktnox_to_mtnox = 0.001 #ceds
ktbc_to_mtbc = 0.001 #ceds

df_frida_calib = pd.read_csv(
    "data/outputs/frida_calibration_data.csv")
df_frida_calib = df_frida_calib.set_index('Year')

df_frida_baselines = pd.read_csv(
    "data/outputs/baseline_values.csv")
df_frida_baselines = df_frida_baselines.set_index('Year')

regression_data =  pd.DataFrame()
regression_data['Year'] = np.arange(climate_start, climate_end+1)
regression_data = regression_data.set_index('Year')

#%%

df_gfed_full = pd.read_csv(
    "data/inputs/gfed-bb4cmip_cmip7_national_alpha.csv")

df_gfed_full = df_gfed_full.loc[df_gfed_full['region'] == 'World'
                                ].drop(['model', 'scenario', 'region', 'unit'], axis=1
                               ).set_index('variable').transpose()

df_gfed_full.index = [int(idx) for idx in df_gfed_full.index]

#%%

df_co_ceds = pd.read_csv(
    "data/inputs/CO_CEDS_global_emissions_by_sector_v2024_07_08.csv")

df_co_ceds_crop = df_co_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_co_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_co_ceds_crop.index]

df_sector_sum = ktco_to_mtco*df_co_ceds_crop.sum(axis=1)
    
df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= climate_start
                                    ) & (df_sector_sum.index <= climate_end)]

df_gfed_full_co_bb = df_gfed_full['CMIP7 History|Emissions|CO|Biomass Burning'
                              ].loc[(df_gfed_full.index >= climate_start
                             ) & (df_gfed_full.index <= climate_end)]

co_emissions = df_sector_sum_frida + df_gfed_full_co_bb

regression_data['CO Emissions'] = co_emissions

df_frida_calib['Emissions.CO Emissions[1]'] = co_emissions.loc[(co_emissions.index >= frida_start
                                                            ) & (co_emissions.index <= frida_calib_end)]
   
df_frida_baselines['Emissions.Baseline CO Emissions'] = regression_data.loc[
    regression_data.index==1750]['CO Emissions'].values[0]


#%%

df_voc_ceds = pd.read_csv(
    "data/inputs/NMVOC_CEDS_global_emissions_by_sector_v2024_07_08.csv")

df_voc_ceds_crop = df_voc_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_voc_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_voc_ceds_crop.index]

df_sector_sum = ktvoc_to_mtvoc*df_voc_ceds_crop.sum(axis=1)
    
df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= climate_start
                                    ) & (df_sector_sum.index <= climate_end)]

df_gfed_full_voc_bb = df_gfed_full['CMIP7 History|Emissions|NMVOC|Biomass Burning'
                              ].loc[(df_gfed_full.index >= climate_start
                             ) & (df_gfed_full.index <= climate_end)]

                                     

voc_emissions = df_sector_sum_frida + df_gfed_full_voc_bb

regression_data['VOC Emissions'] = voc_emissions

df_frida_calib['Emissions.VOC Emissions[1]'] = voc_emissions.loc[(voc_emissions.index >= frida_start
                                                            ) & (voc_emissions.index <= frida_calib_end)]
   
df_frida_baselines['Emissions.Baseline VOC Emissions'] = regression_data.loc[
    regression_data.index==1750]['VOC Emissions'].values[0]

#%%


ceds_to_frida_nox = {
    "1A1a_Electricity-autoproducer":"non AFOLU",
    "1A1a_Electricity-public":"non AFOLU",
    "1A1a_Heat-production":"non AFOLU",
    "1A1bc_Other-transformation":"non AFOLU",
    "1A2a_Ind-Comb-Iron-steel":"non AFOLU",
    "1A2b_Ind-Comb-Non-ferrous-metals":"non AFOLU",
    "1A2c_Ind-Comb-Chemicals":"non AFOLU",
    "1A2d_Ind-Comb-Pulp-paper":"non AFOLU",
    "1A2e_Ind-Comb-Food-tobacco":"non AFOLU",
    "1A2f_Ind-Comb-Non-metalic-minerals":"non AFOLU",
    "1A2g_Ind-Comb-Construction":"non AFOLU",
    "1A2g_Ind-Comb-machinery":"non AFOLU",
    "1A2g_Ind-Comb-mining-quarying":"non AFOLU",
    "1A2g_Ind-Comb-other":"non AFOLU",
    "1A2g_Ind-Comb-textile-leather":"non AFOLU",
    "1A2g_Ind-Comb-transpequip":"non AFOLU",
    "1A2g_Ind-Comb-wood-products":"non AFOLU",
    "1A3ai_International-aviation":"non AFOLU",
    "1A3aii_Domestic-aviation":"non AFOLU",
    "1A3b_Road":"non AFOLU",
    "1A3c_Rail":"non AFOLU",
    "1A3di_International-shipping":"non AFOLU",
    "1A3di_Oil_Tanker_Loading":"non AFOLU",
    "1A3dii_Domestic-navigation":"non AFOLU",
    "1A3eii_Other-transp":"non AFOLU",
    "1A4a_Commercial-institutional":"non AFOLU",
    "1A4b_Residential":"non AFOLU",
    "1A4c_Agriculture-forestry-fishing":"non AFOLU",
    "1A5_Other-unspecified":"non AFOLU",
    "1B1_Fugitive-solid-fuels":"non AFOLU",
    "1B2_Fugitive-petr":"non AFOLU",
    "1B2b_Fugitive-NG-distr":"non AFOLU",
    "1B2b_Fugitive-NG-prod":"non AFOLU",
    "1B2d_Fugitive-other-energy":"non AFOLU",
    "2A1_Cement-production":"non AFOLU",
    "2A2_Lime-production":"non AFOLU",
    "2Ax_Other-minerals":"non AFOLU",
    "2B_Chemical-industry":"non AFOLU",
    "2B2_Chemicals-Nitric-acid":"non AFOLU",
    "2B3_Chemicals-Adipic-acid":"non AFOLU",
    "2C1_Iron-steel-alloy-prod":"non AFOLU",
    "2C3_Aluminum-production":"non AFOLU",
    "2C4_Non-Ferrous-other-metals":"non AFOLU",
    "2D_Chemical-products-manufacture-processing":"non AFOLU",
    "2D_Degreasing-Cleaning":"non AFOLU",
    "2D_Other-product-use":"non AFOLU",
    "2D_Paint-application":"non AFOLU",
    "2H_Pulp-and-paper-food-beverage-wood":"non AFOLU",
    "3B_Manure-management":"AFOLU",
    "3D_Rice-Cultivation":"AFOLU",
    "3D_Soil-emissions":"AFOLU",
    "3E_Enteric-fermentation":"AFOLU",
    "3I_Agriculture-other":"AFOLU",
    "5A_Solid-waste-disposal":"non AFOLU",
    "5C_Waste-combustion":"non AFOLU",
    "5D_Wastewater-handling":"non AFOLU",
    "5E_Other-waste-handling":"non AFOLU",
    "6A_Other-in-total":"non AFOLU",
    "6B_Other-not-in-total":"non AFOLU",
    "7A_Fossil-fuel-fires":"non AFOLU",
    "7BC_Indirect-N2O-non-agricultural-N":"non AFOLU",
    }

df_nox_ceds = pd.read_csv(
    "data/inputs/NOx_CEDS_global_emissions_by_sector_v2024_07_08.csv")

df_nox_ceds_crop = df_nox_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_nox_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_nox_ceds_crop.index]


for sector in ["non AFOLU", "AFOLU"]:
    ceds_sectors = [key for key, value in ceds_to_frida_nox.items() if value == sector]
    
    df_sector_sum = ktnox_to_mtnox*df_nox_ceds_crop[ceds_sectors].sum(axis=1)
    
    df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= climate_start
                                        ) & (df_sector_sum.index <= climate_end)]
    

    regression_data[f'NOx {sector} Emissions'] = df_sector_sum_frida

    df_frida_calib[f'Emissions.NOx {sector} Emissions[1]'
                   ] = df_sector_sum_frida.loc[(df_sector_sum_frida.index >= frida_start
                    ) & (df_sector_sum_frida.index <= frida_calib_end)]
    
        
df_gfed_full_nox_bb = df_gfed_full['CMIP7 History|Emissions|NOx|Biomass Burning'
                              ].loc[(df_gfed_full.index >= climate_start
                             ) & (df_gfed_full.index <= climate_end)]
                                     
df_frida_calib['Emissions.NOx AFOLU Emissions[1]'
               ] += df_gfed_full_nox_bb.loc[(df_gfed_full_nox_bb.index >= frida_start
                 ) & (df_gfed_full_nox_bb.index <= frida_calib_end)].values*46.006/30.006

regression_data['NOx AFOLU Emissions'] += df_gfed_full_nox_bb.values*46.006/30.006

df_frida_baselines['Emissions.Baseline NOx AFOLU Emissions'] = regression_data.loc[
    regression_data.index==1750]['NOx AFOLU Emissions'].values[0]

df_frida_baselines['Emissions.Baseline NOx non AFOLU Emissions'] = regression_data.loc[
    regression_data.index==1750]['NOx non AFOLU Emissions'].values[0]

#%%
df_old_calib = pd.read_csv(
    "../WorldTransFRIDA/Data/Calibration Data.csv")


spec_plots = ['Emissions.CO Emissions[1]', 'Emissions.VOC Emissions[1]',
    'Emissions.NOx non AFOLU Emissions[1]',
    'Emissions.NOx AFOLU Emissions[1]']

idx1 = 1
idx2 = 45

time_old = [int(key) for key in df_old_calib.keys()[idx1:idx2]]

spec_plots_to_gfed = {
    "Emissions.CO Emissions[1]":"CO",
    "Emissions.VOC Emissions[1]":"NMVOC",
    "Emissions.NOx non AFOLU Emissions[1]":"NOx",
    "Emissions.NOx AFOLU Emissions[1]":"NOx",    
    }

for spec in spec_plots:
    
    fig = plt.figure()
    
    plt.plot(frida_start + np.arange(frida_calib_end + 1 - frida_start),
             df_frida_calib[spec], label='New')
    
    if spec in list(df_old_calib.values[:,0]):
        idx_data = list(df_old_calib.values[:,0]).index(spec)
    else:
        idx_data = list(df_old_calib.values[:,0]).index(spec.replace("Emissions[1]", "emissions[1]"))
    plot_data = df_old_calib.values[idx_data,idx1:idx2]
    plt.plot(time_old, plot_data, label='Old')
    
    # plt.plot(df_gfed['Unnamed: 0'], df_gfed[spec_plots_to_gfed[spec]], label='GFED')
    
    plt.legend()
    plt.title(spec)
    
#%%


df_frida_calib.to_csv('data/outputs/frida_calibration_data.csv')

df_frida_baselines.to_csv('data/outputs/baseline_values.csv')


#%%

# To update BC Snow forcing output, for the regression
df_bc_ceds = pd.read_csv(
    "data/inputs/BC_CEDS_global_emissions_by_sector_v2024_07_08.csv")

df_bc_ceds_crop = df_bc_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_bc_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_bc_ceds_crop.index]

df_sector_sum = ktbc_to_mtbc*df_bc_ceds_crop.sum(axis=1)
    
df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= climate_start
                                    ) & (df_sector_sum.index <= climate_end)]

df_gfed_full_bc_bb = df_gfed_full['CMIP7 History|Emissions|BC|Biomass Burning'
                              ].loc[(df_gfed_full.index >= climate_start
                             ) & (df_gfed_full.index <= climate_end)]

                                     

bc_emissions = df_sector_sum_frida + df_gfed_full_bc_bb

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


fill(
    f_cmip6_hist.emissions, bc_emissions.values[:,None], specie='BC', scenario='ssp245'
)

f_cmip6_hist.run()

regression_data['BC Snow Forcing'] = f_cmip6_hist.forcing[
    :-1,0,0,f_cmip6_hist.species.index('Light absorbing particles on snow and ice')]

#%%

df_climate_calib = pd.read_csv(
    "data/outputs/climate_calibration_data.csv")
df_climate_calib = df_climate_calib.set_index("Year")

regression_data['CO2 AFOLU Emissions'] = df_climate_calib[
    'Emissions.CO2 Emissions from Food and Land Use']

regression_data['Sulfur Emissions'] = df_climate_calib[
    'Emissions.Total SO2 Emissions']

        
regression_data['CH4 Emissions'] = df_climate_calib[
    'Emissions.Total CH4 Emissions']

regression_data['N2O non AFOLU Emissions'] = df_climate_calib[
    'Emissions.N2O non AFOLU Emissions']

        
        
#%%

regr = LinearRegression(fit_intercept=False)

regr_data = {}

potential_links = {
    'BC Snow Forcing':['CO2 AFOLU Emissions', 'Sulfur Emissions'],
    'VOC Emissions':['CH4 Emissions'],
    'CO Emissions':['CH4 Emissions'],
    'NOx non AFOLU Emissions':['N2O non AFOLU Emissions'],
    'NOx AFOLU Emissions':['Sulfur Emissions'],
    }


for targ in potential_links.keys():
    regr_data[targ] = {}
    
    pred = potential_links[targ]
        
    pred_array = np.zeros((climate_end - climate_start + 1, len(pred)))
    for pred_i, pred_component in enumerate(pred):
        pred_array[:,pred_i] = np.asarray(regression_data[pred_component].values)
    
    pred_array = pred_array - pred_array[0,:]
    
    targ_data = regression_data[targ].values
    targ_data = targ_data - targ_data[0]
    
    regr.fit(pred_array, targ_data)
    
    regr_data[targ] = regr.coef_
    
    fig = plt.figure()
    
    plt.plot(np.arange(climate_start, climate_end+1), regression_data[targ].values, label='Target')
    plt.plot(np.arange(climate_start, climate_end+1), regression_data[targ].values[0
               ] + regr.predict(pred_array), label='Fit')

    plt.legend()
    plt.title(targ)
    
#%%


regression_parameters =  pd.DataFrame()
regression_parameters['Index'] = [0]
regression_parameters = regression_parameters.set_index('Index')

regression_parameters['BC on Snow Forcing.Effective Radiative Forcing of Black Carbon on Snow per unit CO2 AFOLU Emissions'
                      ] = regr_data['BC Snow Forcing'][0]

regression_parameters['BC on Snow Forcing.Effective Radiative Forcing of Black Carbon on Snow per unit SO2 Emissions'
                      ] = regr_data['BC Snow Forcing'][1]

regression_parameters['Emissions.VOC Emissions per CH4 Emissions'
                      ] = regr_data['VOC Emissions'][0]

regression_parameters['Emissions.CO Emissions per CH4 Emissions'
                      ] = regr_data['CO Emissions'][0]

regression_parameters['Emissions.NOx AFOLU Emissions per SO2 Emissions'
                      ] = regr_data['NOx AFOLU Emissions'][0]

regression_parameters['Emissions.NOx non AFOLU Emissions per N2O non AFOLU Emissions'
                      ] = regr_data['NOx non AFOLU Emissions'][0]

regression_parameters.to_csv('data/outputs/regression_parameters.csv')
