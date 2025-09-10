import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import numpy as np


albedo_file = '../data/inputs/ghimire_curve_fit.csv'
df_in = pd.read_csv(albedo_file, index_col=0)

target_years = [1980, 1750]
years = df_in.index.values
forcing = df_in['flux'].values

fit = CubicSpline(years, forcing)

years_ext = np.insert(years, years.shape[0], 2019)
forcing_ext = np.insert(forcing, forcing.shape[0], -0.15 + forcing[0])
forcing_ext_nooffset = np.insert(forcing, forcing.shape[0], -0.15)
fit_ext = CubicSpline(years_ext, forcing_ext)
fit_ext_nooffset = CubicSpline(years_ext, forcing_ext_nooffset)

years_plot = 1750+np.arange(272)


forcing_cf_1750 = forcing - forcing[0]

coef = np.polyfit(years, forcing_cf_1750, 1)
poly1d_fn = np.poly1d(coef) 

approx_2019_forcing = poly1d_fn(2019)

forcing_cf_1750_full = np.concatenate((forcing_cf_1750, [approx_2019_forcing]))
years_full = np.concatenate((years, [2019]))

fit_full = CubicSpline(years_full, forcing_cf_1750_full)

full_fit_1750_2019 = fit_full(years_plot)

full_forcing = full_fit_1750_2019*(-0.15/np.mean(full_fit_1750_2019[-15:]))

plt.plot(years_plot, full_forcing)

offset_1980_cf_1750 = full_forcing[-40]

dataset = pd.DataFrame({'Year': years_plot, 'Albedo ERF': full_forcing})

dataset.to_csv('../data/outputs/Albedo_ERF.csv', index=False)
