import pandas as pd

# we can improve this in future by building in... but just tidy up for
# stella here

df_frida_calibration_data = pd.read_csv("data/outputs/frida_calibration_data.csv")
df_frida_calibration_data = df_frida_calibration_data.drop(['Unnamed: 0'], axis=1)

df_baseline_values = pd.read_csv("data/outputs/baseline_values.csv")
df_baseline_values = df_baseline_values.drop(['Unnamed: 0.1', 'Unnamed: 0'], axis=1)

# df_climate_calibration_data = pd.read_csv("data/outputs/climate_calibration_data.csv")

# df_frida_input_data = pd.read_csv("data/outputs/frida_input_data.csv")

df_regression_parameters = pd.read_csv("data/outputs/regression_parameters.csv")
df_regression_parameters = df_regression_parameters.drop(['Index'], axis=1)

#%%
df_frida_calibration_data.to_csv('data/outputs/frida_calibration_data.csv')
df_baseline_values.to_csv('data/outputs/baseline_values.csv')
df_regression_parameters.to_csv('data/outputs/regression_parameters.csv')
