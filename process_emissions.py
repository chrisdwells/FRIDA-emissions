import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pooch

# This creates the emissions which go into FRIDA, and the Climate Calibration
# FRIDA emissions are from 1980; calibration from 1750; both end 2022
# They should overlap exactly

climate_start = 1750
climate_end = 2022

frida_start = 1980
frida_end = 2022


df_climate = pd.DataFrame()
df_climate['Year'] = np.arange(climate_start, climate_end+1)
df_climate = df_climate.set_index('Year')

df_frida = pd.DataFrame()
df_frida['Year'] = np.arange(frida_start, frida_end+1)
df_frida = df_frida.set_index('Year')

df_frida_baselines = {}

co2_molec_weight = 44.009
c_molec_weight = 12.0107

gtc_to_mtco2 = 1000 * co2_molec_weight/c_molec_weight # gcb
mtc_to_mtco2 = co2_molec_weight/c_molec_weight # gcb

ggn2o_to_ktn2o = 1 # primap

ktch4_to_mtch4 = 0.001 # ceds

ggch4_to_mtch4 = 0.001 # primap

ktso2_to_mtso2 = 0.001 # ceds

#%%
"""
CO2

Use Global Carbon Project. https://globalcarbonbudgetdata.org/latest-data.html
Current version: v2024, v1.0.

Get xlsx, then have to save Fossil Emissions by Category, Historical Budget as 
separate csvs, and delete rows above data.

We use Historical Budget 'fossil emissions excluding carbonation' for
total fossil emissions from 1750 for the calibration.

We use Fossil Emissions by Category 'Cement.emission' as FRIDA Cement emissions,
and 'fossil.emissions.excluding.carbonation' minus this as FRIDA Energy emissions.

1750-1850 cumulative land use emissions are 30GtC from 
https://essd.copernicus.org/articles/15/5301/2023/ - we assume linear to 1850.

Output in MtCO2. Inputs vary between sheets.

"""

# Total budget for calibration
df_gcb_budget = pd.read_csv(
    "data/inputs/Global_Carbon_Budget_2024_v1.0_historical_budget.csv")

df_gcb_budget_crop = df_gcb_budget.loc[(df_gcb_budget['Year'] >= climate_start
                                    ) & (df_gcb_budget['Year'] <= climate_end)]

land_use_from_1850 = df_gcb_budget_crop.loc[df_gcb_budget[
                    'Year'] >= 1850]['land-use change emissions']

cumulative_land_use_1750_to_1849 = 30

annual_emissions_1849 = 2*cumulative_land_use_1750_to_1849/100 # assume linear

land_use_1750_to_1850 = np.linspace(0,annual_emissions_1849, 100)

assert np.sum(land_use_1750_to_1850) == cumulative_land_use_1750_to_1849

land_use = np.concatenate((land_use_1750_to_1850, land_use_from_1850))

df_climate['CO2 Emissions'] = gtc_to_mtco2*(land_use + df_gcb_budget_crop[
                                'fossil emissions excluding carbonation'].values)


# By sector for FRIDA
df_gcb_by_cat = pd.read_csv(
    "data/inputs/Global_Carbon_Budget_2024_v1.0_fossil_emissions_by_category.csv")

df_gcb_by_cat_crop = df_gcb_by_cat.loc[(df_gcb_by_cat['Year'] >= frida_start
                                    ) & (df_gcb_by_cat['Year'] <= frida_end)]

df_frida['Concrete.CO2 emissions[1]'] = mtc_to_mtco2*df_gcb_by_cat_crop['Cement.emission'].values

df_frida['Emissions.CO2 emissions from Energy[1]'
         ] = mtc_to_mtco2*(df_gcb_by_cat_crop['fossil.emissions.excluding.carbonation'
            ].values - df_gcb_by_cat_crop['Cement.emission'].values)

land_use_frida = df_gcb_budget_crop.loc[(df_gcb_budget_crop['Year'] >= frida_start
                ) & (df_gcb_budget_crop['Year'] <= frida_end)]['land-use change emissions'].values

df_frida['Emissions.CO2 emissions from Food and Land Use[1]'
         ] = gtc_to_mtco2*land_use_frida                                          
       
assert df_frida[['Concrete.CO2 emissions[1]', 'Emissions.CO2 emissions from Energy[1]',
       'Emissions.CO2 emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values == df_climate.loc[
       df_climate.index == 2015]['CO2 Emissions'].values

#%%
                                
"""
N2O

Use PRIMAP-hist data
Current version: 2024 v2.6 https://zenodo.org/records/13752654

"""

df_primap = pd.read_csv(
    "data/inputs/Guetschow_et_al_2024a-PRIMAP-hist_v2.6_final_no_rounding_13-Sep-2024.csv")

df_primap_crop = df_primap.loc[(df_primap['area (ISO3)'] == 'EARTH') &
                               (df_primap['scenario (PRIMAP-hist)'] == 'HISTTP')]


df_primap_n2o_crop = df_primap_crop.loc[df_primap_crop['entity'] == 'N2O']

df_primap_n2o_crop = df_primap_n2o_crop.drop(['source', 'scenario (PRIMAP-hist)', 
      'provenance', 'entity', 'area (ISO3)', 'unit'], axis=1)

df_primap_n2o = df_primap_n2o_crop.set_index('category (IPCC2006_PRIMAP)').transpose()

df_primap_n2o.index = df_primap_n2o.index.astype(int)


df_primap_n2o_frida = df_primap_n2o.loc[(df_primap_n2o.index >= frida_start
                                    ) & (df_primap_n2o.index <= frida_end)]

n2o_energy = df_primap_n2o_frida['1'] + df_primap_n2o_frida['2']
n2o_other = df_primap_n2o_frida['4'] + df_primap_n2o_frida['5']
n2o_food_and_lu = df_primap_n2o_frida['3']


df_frida['Emissions.N2O emissions from Food and Land Use[1]'
         ] = ggn2o_to_ktn2o*n2o_energy.values

df_frida['Emissions.N2O emissions from Other[1]'
         ] = ggn2o_to_ktn2o*n2o_other.values

df_frida['Emissions.N2O emissions from Energy[1]'
         ] = ggn2o_to_ktn2o*n2o_food_and_lu.values


df_primap_n2o_climate = df_primap_n2o.loc[(df_primap_n2o.index >= climate_start
                                    ) & (df_primap_n2o.index <= climate_end)]

df_climate['N2O Emissions'] = ggn2o_to_ktn2o*(df_primap_n2o_climate['1'
                            ] + df_primap_n2o_climate['2'] + df_primap_n2o_climate['3'
                           ] + df_primap_n2o_climate['4'] + df_primap_n2o_climate['5']).values

df_frida_baselines['N2O'] = df_climate.loc[df_climate.index==1750]['N2O Emissions'].values[0]

                                                                                   
# plt.plot(1750 + np.arange(273), df_primap_n2o_climate['3'], label='LU')
# plt.plot(1750 + np.arange(273), df_primap_n2o_climate['1'] + df_primap_n2o_climate['2'], label='Energy')
# plt.plot(1750 + np.arange(273), df_primap_n2o_climate['4'] + df_primap_n2o_climate['5'], label='Other')
# plt.legend()
# plt.title('N2O Emissions')

# plt.xlim([1745, 1800])
# plt.ylim([-1, 200])

assert df_frida[['Emissions.N2O emissions from Other[1]', 'Emissions.N2O emissions from Energy[1]',
       'Emissions.N2O emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values == df_climate.loc[
       df_climate.index == 2015]['N2O Emissions'].values


#%%

"""
CH4

1970 onwards (by sector) from CEDS https://zenodo.org/records/12803197
Pre-1970 (for climate, so summed over all sources) from PRIMAP-hist

Biomass Burning separately, from GFED - averaged due to no process-based 
representation in FRIDA.

"""

df_ch4_ceds = pd.read_csv(
    "data/inputs/CH4_CEDS_global_emissions_by_sector_v2024_07_08.csv")

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
                                        ) & (df_sector_sum.index <= frida_end)]

    df_frida[f'Emissions.CH4 emissions from {sector}[1]'] = df_sector_sum_frida.values
    
#     plt.plot(df_sector_sum.index, df_sector_sum, label=sector)
# plt.legend()

# BB from GFED - add to land use


df_gfed = pd.read_csv(
    "data/inputs/gfed4.1s_1997-2023.csv")


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

ch4_gfed_1997_plus = df_gfed['CH4'].loc[
            df_gfed['Unnamed: 0'] <= climate_end].values
ch4_gfed = np.concatenate((ch4_gfed_pre_1997, ch4_gfed_1997_plus))
ch4_gfed_mean = np.mean(ch4_gfed)

df_frida['Emissions.CH4 emissions from Food and Land Use[1]'
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

# plt.plot(df_climate['Year'], ch4_for_climate, label = 'Combined')
# plt.plot(df_primap_ch4.index, ggch4_to_mtch4*df_primap_ch4['0'], label = 'PRIMAP')
# plt.plot(df_ceds_sum.index, df_ceds_sum, label = 'CEDS')
# plt.legend()

df_climate['CH4 Emissions'] = ch4_for_climate + ch4_gfed_mean

df_frida_baselines['CH4'] = df_climate.loc[df_climate.index==1750]['CH4 Emissions'].values[0]

assert np.around(df_frida[['Emissions.CH4 emissions from Other[1]', 'Emissions.CH4 emissions from Energy[1]',
       'Emissions.CH4 emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values[0], decimals=3) == np.around(df_climate.loc[
       df_climate.index == 2015]['CH4 Emissions'].values[0], decimals=3)

                                                                    
#%%

"""
SO2

Assume all CEDS data is Energy.

Use GFED 4.1s for biomass burning, aggregated here from 1997:
https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/gfed4.1s_1997-2023.csv
and from RCMIP for pre-1997. Since FRIDA doesn't have process-based BB emissions, 
use the historical average. 

Baseline SO2 emissions are the BB emissions plus the 1750 CEDS emissions, to 
ensure forcing is 0 in 1750.
                   
"""

df_so2_ceds = pd.read_csv(
    "data/inputs/SO2_CEDS_global_emissions_by_sector_v2024_07_08.csv")

df_so2_ceds_crop = df_so2_ceds.drop(['em', 'units'], 
               axis=1).set_index('sector').transpose()

df_so2_ceds_crop.index = [int(idx.replace("X", "")) for idx in df_so2_ceds_crop.index]

df_sector_sum = ktso2_to_mtso2*df_so2_ceds_crop.sum(axis=1)
    
df_sector_sum_frida = df_sector_sum.loc[(df_sector_sum.index >= frida_start
                                    ) & (df_sector_sum.index <= frida_end)]

df_frida['Emissions.SO2 emissions from Energy[1]'] = df_sector_sum_frida.values
    

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

df_frida['Emissions.SO2 emissions from Food and Land Use[1]'
         ] = np.repeat(so2_gfed_mean, frida_end - frida_start + 1)



df_climate['SO2 Emissions'
         ] = df_sector_sum_climate.values + so2_gfed_mean

df_frida_baselines['SO2'] = df_climate.loc[df_climate.index==1750]['SO2 Emissions'].values[0]

assert df_frida[['Emissions.SO2 emissions from Energy[1]',
       'Emissions.SO2 emissions from Food and Land Use[1]']].loc[
       df_frida.index == 2015].sum(axis=1).values == df_climate.loc[
       df_climate.index == 2015]['SO2 Emissions'].values

           
#%%

for spec in ['CO2', 'N2O', 'CH4', 'SO2']:
    fig = plt.figure()
    
    plt.plot(df_climate.index, df_climate[f'{spec} Emissions'], label='Total for Calibration')

    frida_vars = [var for var in df_frida.keys() if spec in var]
    # plt.plot(df_frida.index, df_frida[frida_vars])
    plt.plot(df_frida.index, df_frida[frida_vars].sum(axis=1), label='FRIDA Sum')
    
    plt.title(spec)    
    plt.legend()
    plt.xlim([1950, 2024])


