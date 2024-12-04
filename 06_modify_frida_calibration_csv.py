import pandas as pd
import copy
from dotenv import load_dotenv
import os

load_dotenv()

climate_start = int(os.getenv("climate_start"))
climate_end = int(os.getenv("climate_end"))

frida_start = int(os.getenv("frida_start"))
frida_calib_end = int(os.getenv("frida_calib_end"))

df_frida_current = pd.read_csv('../WorldTransFRIDA/Data/Calibration Data.csv', index_col=0)

df_frida_current = df_frida_current.T

df_frida_new = copy.deepcopy(df_frida_current)

df_frida_calib_inputs = pd.read_csv("data/outputs/frida_calibration_data.csv")
df_frida_calib_inputs = df_frida_calib_inputs.set_index("Year")

df_frida_calib_inputs['Emissions.Total CH4 Emissions[1]'] = df_frida_calib_inputs[
            ['Emissions.CH4 Emissions from Energy[1]',
            'Emissions.CH4 Emissions from Food and Land Use[1]',
            'Emissions.CH4 Emissions from Other[1]']].sum(axis=1)


df_frida_calib_inputs['Emissions.Total CO2 Emissions[1]'] = df_frida_calib_inputs[
           ['Concrete.CO2 Emissions[1]',
           'Emissions.CO2 Emissions from Energy[1]',
           'Emissions.CO2 Emissions from Food and Land Use[1]']].sum(axis=1)

df_frida_calib_inputs['Emissions.Total SO2 Emissions[1]'] = df_frida_calib_inputs[
           ['Emissions.SO2 Emissions from Energy[1]',
           'Emissions.SO2 Emissions from Food and Land Use[1]']].sum(axis=1)

df_frida_calib_inputs['Emissions.Total N2O Emissions[1]'] = df_frida_calib_inputs[
           ['Emissions.N2O Emissions from Food and Land Use[1]',
           'Emissions.N2O Emissions from Other[1]',
           'Emissions.N2O Emissions from Energy[1]']].sum(axis=1)

df_frida_calib_inputs['Emissions.Total NOx Emissions[1]'] = df_frida_calib_inputs[
           ['Emissions.NOx non AFOLU Emissions[1]',
           'Emissions.NOx AFOLU Emissions[1]']].sum(axis=1)

vars_for_frida = [key for key in df_frida_calib_inputs.keys() if key not in ['Unnamed: 0', 'Year']]

for var in vars_for_frida:
    if 'emissions' in var:
        raise Exception(f'need uppercase Emissions in {var}')
    if var in df_frida_new.keys():
        df_frida_new = df_frida_new.drop([var], axis=1)

    df_frida_new.loc[len(df_frida_new)] = None # this could do with fixing

    for idx in df_frida_calib_inputs.index:
        if str(idx) in df_frida_new.index and type(idx) == int:
            df_frida_new.loc[str(idx), var] = df_frida_calib_inputs[var][idx]
            
    if var.replace(" Emissions", " emissions") in df_frida_new.keys():
        df_frida_new = df_frida_new.drop([var.replace(" Emissions", " emissions")], axis=1)



# crop off old vars if necessary - e.g. CO2 from Other is replaced by concrete
# in current version. make sure this list is right!
vars_to_drop = ['Emissions.CO2 emissions from Other[1]']

for var in vars_to_drop:
    if var in df_frida_new.keys():
        print(f'Dropping {var}')
        df_frida_new = df_frida_new.drop([var], axis=1)
    elif var.replace(" Emissions", " emissions") in df_frida_new.keys():
        print(f'Dropping {var.replace(" Emissions", " emissions")}')
        df_frida_new = df_frida_new.drop([var.replace(" Emissions", " emissions")], axis=1)


#%%

documentation = {
     'Concrete.CO2 Emissions[1]':"'Cement.emission' in GCP https://globalcarbonbudgetdata.org/latest-data.html v2024, v1.0.",
     'Emissions.CO2 Emissions from Energy[1]':"'fossil.emissions.excluding.carbonation' minus 'Cement.emission' in GCP https://globalcarbonbudgetdata.org/latest-data.html v2024, v1.0.",
     'Emissions.CO2 Emissions from Food and Land Use[1]':"'land-use change emissions' in GCP https://globalcarbonbudgetdata.org/latest-data.html v2024, v1.0.",
     'Emissions.N2O Emissions from Food and Land Use[1]':"Category 3 in PRIMAP https://zenodo.org/records/13752654 2024 v2.6",
     'Emissions.N2O Emissions from Other[1]':"Categories 4+5 in PRIMAP https://zenodo.org/records/13752654 2024 v2.6",
     'Emissions.N2O Emissions from Energy[1]':"Categories 1+2 in PRIMAP https://zenodo.org/records/13752654 2024 v2.6",
     'Emissions.CH4 Emissions from Energy[1]':"Categories 1+2, plus 7A_Fossil-fuel-fires, in CEDS https://zenodo.org/records/12803197",
     'Emissions.CH4 Emissions from Food and Land Use[1]':"Category 3 in CEDS https://zenodo.org/records/12803197 plus time-averaged GFED (https://zenodo.org/records/4589756 1750-1997, https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/gfed4.1s_1997-2023.csv post-1997)",
     'Emissions.CH4 Emissions from Other[1]':"Categories 5+6, plus 7BC_Indirect-N2O-non-agricultural-N, in CEDS https://zenodo.org/records/12803197",
     'Emissions.SO2 Emissions from Energy[1]':"All categories in CEDS https://zenodo.org/records/12803197",
     'Emissions.SO2 Emissions from Food and Land Use[1]':"time-averaged GFED (https://zenodo.org/records/4589756 1750-1997, https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/gfed4.1s_1997-2023.csv post-1997)",
     'Emissions.CO Emissions[1]':"CEDS https://zenodo.org/records/12803197 plus GFED ()",
     'Emissions.VOC Emissions[1]':"CEDS https://zenodo.org/records/12803197 plus GFED ()",
     'Emissions.NOx non AFOLU Emissions[1]':"Category 3 CEDS https://zenodo.org/records/12803197 plus BB4CMIP (consistent with GFED 4.1s, produced by the CMIP7 ScenarioMIP team led by IIASA)",
     'Emissions.NOx AFOLU Emissions[1]':"Categories except 3 CEDS https://zenodo.org/records/12803197 plus BB4CMIP (consistent with GFED 4.1s, produced by the CMIP7 ScenarioMIP team led by IIASA)",
     'Emissions.HFC134a eq Emissions[1]':"Converted from https://github.com/ClimateIndicator/data/blob/main/data/greenhouse_gas_concentrations/ghg_concentrations.csv",
     'Emissions.Total CH4 Emissions[1]':"CEDS https://zenodo.org/records/12803197 plus time-averaged GFED (https://zenodo.org/records/4589756 1750-1997, https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/gfed4.1s_1997-2023.csv post-1997)",
     'Emissions.Total CO2 Emissions[1]':"GCP https://globalcarbonbudgetdata.org/latest-data.html v2024, v1.0.",
     'Emissions.Total SO2 Emissions[1]':"CEDS https://zenodo.org/records/12803197 plus time-averaged GFED (https://zenodo.org/records/4589756 1750-1997, https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/gfed4.1s_1997-2023.csv post-1997)",
     'Emissions.Total N2O Emissions[1]':"PRIMAP https://zenodo.org/records/13752654 2024 v2.6",
     'Emissions.Total NOx Emissions[1]':"CEDS https://zenodo.org/records/12803197 plus BB4CMIP (consistent with GFED 4.1s, produced by the CMIP7 ScenarioMIP team led by IIASA)",
    }

units = {
    "Concrete.CO2 Emissions[1]":"MtCO2/year",
    "Emissions.CO2 Emissions from Energy[1]":"MtCO2/year",
    "Emissions.CO2 Emissions from Food and Land Use[1]":"MtCO2/year",
    "Emissions.N2O Emissions from Food and Land Use[1]":"ktN2O/Year",
    "Emissions.N2O Emissions from Other[1]":"ktN2O/Year",
    "Emissions.N2O Emissions from Energy[1]":"ktN2O/Year",
    "Emissions.CH4 Emissions from Energy[1]":"MtCH4/Year",
    "Emissions.CH4 Emissions from Food and Land Use[1]":"MtCH4/Year",
    "Emissions.CH4 Emissions from Other[1]":"MtCH4/Year",
    "Emissions.SO2 Emissions from Energy[1]":"MtSO2/year",
    "Emissions.SO2 Emissions from Food and Land Use[1]":"MtSO2/year",
    "Emissions.CO Emissions[1]":"Mt CO/yr",
    "Emissions.VOC Emissions[1]":"Mt VOC/yr",
    "Emissions.NOx non AFOLU Emissions[1]":"Mt NOx/yr",
    "Emissions.NOx AFOLU Emissions[1]":"Mt NOx/yr",
    "Emissions.HFC134a eq Emissions[1]":"kt/year",
    'Emissions.Total CH4 Emissions[1]':"MtCH4/Year",
    'Emissions.Total CO2 Emissions[1]':"MtCO2/year",
    'Emissions.Total SO2 Emissions[1]':"MtSO2/year",
    'Emissions.Total N2O Emissions[1]':"ktN2O/Year",
    'Emissions.Total NOx Emissions[1]':"Mt NOx/yr",
    }

for var in vars_for_frida:
    df_frida_new[var]['Reference'] = documentation[var]
    df_frida_new[var]['Units'] = units[var]


#%%

df_forc = pd.read_csv('data/inputs/ERF_best_1750-2023.csv', index_col=0)

forcing_vars = ['CO2 Forcing.CO2 Effective Radiative Forcing[1]', 
                'CH4 Forcing.CH4 Effective Radiative Forcing[1]', 
                'N2O Forcing.N2O Effective Radiative Forcing[1]']

for var in forcing_vars:
    forc_spec = var.split(" ")[0]
    # forc_data = df_forc[forc_spec].loc[(forc_spec.index >= frida_start) &
    #                                    (forc_spec.index <= frida_calib_end)]
    
    if var in df_frida_new.keys():
        df_frida_new = df_frida_new.drop([var], axis=1)

    df_frida_new.loc[len(df_frida_new)] = None # this could do with fixing

    for idx in df_frida_calib_inputs.index:
        if str(idx) in df_frida_new.index and type(idx) == int:
            df_frida_new.loc[str(idx), var] = df_forc[forc_spec][idx]

    df_frida_new[var]['Units'] = 'w/m^2'
    df_frida_new[var]['Reference'] = 'https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/ERF_best_1750-2023.csv'

            #%%

df_conc = pd.read_csv('data/inputs/ghg_concentrations_1750-2023.csv', index_col=0)

conc_vars = {
    'CO2 Forcing.Atmospheric CO2 Concentration[1]':'ppm',
    'N2O Forcing.Atmospheric N2O Concentration[1]':'ppb', 
    'CH4 Forcing.Atmospheric CH4 Concentration[1]':'ppb',
    }

for var in conc_vars.keys():
    conc_spec = var.split(" ")[0]
    # forc_data = df_forc[forc_spec].loc[(forc_spec.index >= frida_start) &
    #                                    (forc_spec.index <= frida_calib_end)]
    
    if var in df_frida_new.keys():
        df_frida_new = df_frida_new.drop([var], axis=1)

    df_frida_new.loc[len(df_frida_new)] = None # this could do with fixing

    for idx in df_frida_calib_inputs.index:
        if str(idx) in df_frida_new.index and type(idx) == int:
            df_frida_new.loc[str(idx), var] = df_conc[conc_spec][idx]

    df_frida_new[var]['Units'] = conc_vars[var]
    df_frida_new[var]['Reference'] = 'https://github.com/ClimateIndicator/forcing-timeseries/blob/main/output/ghg_concentrations_1750-2023.csv'

  
#%%

df_gmst = pd.read_csv('data/inputs/annual_averages.csv', index_col=0)
   
var = 'Energy Balance Model.Surface Temperature Anomaly[1]'
df_var = 'gmst'

if var in df_frida_new.keys():
    df_frida_new = df_frida_new.drop([var], axis=1)

df_frida_new.loc[len(df_frida_new)] = None # this could do with fixing

for idx in df_frida_calib_inputs.index:
    if str(idx) in df_frida_new.index and type(idx) == int:
        df_frida_new.loc[str(idx), var] = df_gmst[df_var][idx+0.5]

df_frida_new[var]['Units'] = 'deg C'
df_frida_new[var]['Reference'] = ''


#%%
       
df_frida_new = df_frida_new.T
df_frida_new.to_csv('data/outputs/Calibration Data new.csv')
