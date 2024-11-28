import pandas as pd
import copy

df_frida_current = pd.read_csv('../WorldTransFRIDA/Data/Calibration Data.csv', index_col=0)

df_frida_current = df_frida_current.T

df_frida_new = copy.deepcopy(df_frida_current)

df_frida_calib_inputs = pd.read_csv("data/outputs/frida_calibration_data.csv")
df_frida_calib_inputs = df_frida_calib_inputs.set_index("Year")

vars_for_frida = [key for key in df_frida_calib_inputs.keys() if key not in ['Unnamed: 0', 'Year']]

for var in vars_for_frida:
    if var not in df_frida_new.keys():
        df_frida_new.loc[len(df_frida_new)] = None # this could do with fixing

    for idx in df_frida_calib_inputs.index:
        if str(idx) in df_frida_new.index and type(idx) == int:
            df_frida_new.loc[str(idx), var] = df_frida_calib_inputs[var][idx]
            
    if var.replace(" Emissions", " emissions") in df_frida_new.keys():
        df_frida_new = df_frida_new.drop([var.replace(" Emissions", " emissions")], axis=1)


# Documentation?
       
df_frida_new = df_frida_new.T
df_frida_new.to_csv('data/outputs/Calibration Data new.csv')
