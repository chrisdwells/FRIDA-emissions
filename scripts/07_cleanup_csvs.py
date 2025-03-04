import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

# this cleans up the outputs from prior scripts to align them with the
# input format needed for FRIDA

# we can improve this in future by building in to prior scripts... 

datadir = os.getenv("datadir")

df_frida_calibration_data = pd.read_csv(f"{datadir}/outputs/frida_calibration_data.csv")
df_frida_calibration_data = df_frida_calibration_data.drop(['Unnamed: 0'], axis=1)

df_baseline_values = pd.read_csv(f"{datadir}/outputs/baseline_values.csv")
df_baseline_values = df_baseline_values.drop(['Unnamed: 0.1', 'Unnamed: 0', 'Year'], axis=1)


df_regression_parameters = pd.read_csv(f"{datadir}/outputs/regression_parameters.csv")
df_regression_parameters = df_regression_parameters.drop(['Index'], axis=1)

df_climate_calibration_data = pd.read_csv(f"{datadir}/outputs/climate_calibration_data.csv")
df_climate_calibration_data = df_climate_calibration_data.drop(
    ['Unnamed: 0.1', 'Unnamed: 0'], axis=1)

df_climate_calibration_data = df_climate_calibration_data.set_index('Year')

df_frida_calibration_data.to_csv(f'{datadir}/outputs/frida_calibration_data.csv')
df_baseline_values.to_csv(f'{datadir}/outputs/baseline_values.csv')
df_regression_parameters.to_csv(f'{datadir}/outputs/regression_parameters.csv')
df_climate_calibration_data.to_csv(f'{datadir}/outputs/climate_calibration_data.csv')

