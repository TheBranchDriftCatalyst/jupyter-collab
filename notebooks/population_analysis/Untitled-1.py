# %%


# %%
from concurrent.futures import ThreadPoolExecutor
import wbgapi as wb
import ipywidgets as widgets
import pandas as pd
from IPython.display import display
import matplotlib.pyplot as plt
import pickle
import os
import logging
import sys

logging.basicConfig(format='%(asctime)s | %(levelname)s : %(message)s', level=logging.ERROR, stream=sys.stdout)

# %%
# Fetch list of countries
countries = wb.economy.list()

# Create a dropdown for country selection
sorted_countries = sorted(countries, key=lambda x: x['value'].lower())

# Create a dropdown for country selection with sorted options
country_dropdown = widgets.Dropdown(
    options=[(country['value'], country['id']) for country in sorted_countries],
    description='Country:'
)

# Create a slider for year selection
year_slider = widgets.IntSlider(
    value=2020,
    min=1960,
    max=2020,
    step=1,
    description='Year:',
    continuous_update=True
)

age_group_codes = {
    '0-4': ('SP.POP.0004.MA.5Y', 'SP.POP.0004.FE.5Y'),
    '5-9': ('SP.POP.0509.MA.5Y', 'SP.POP.0509.FE.5Y'),
    '10-14': ('SP.POP.1014.MA.5Y', 'SP.POP.1014.FE.5Y'),
    '15-19': ('SP.POP.1519.MA.5Y', 'SP.POP.1519.FE.5Y'),
    '20-24': ('SP.POP.2024.MA.5Y', 'SP.POP.2024.FE.5Y'),
    '25-29': ('SP.POP.2529.MA.5Y', 'SP.POP.2529.FE.5Y'),
    '30-34': ('SP.POP.3034.MA.5Y', 'SP.POP.3034.FE.5Y'),
    '35-39': ('SP.POP.3539.MA.5Y', 'SP.POP.3539.FE.5Y'),
    '40-44': ('SP.POP.4044.MA.5Y', 'SP.POP.4044.FE.5Y'),
    '45-49': ('SP.POP.4549.MA.5Y', 'SP.POP.4549.FE.5Y'),
    '50-54': ('SP.POP.5054.MA.5Y', 'SP.POP.5054.FE.5Y'),
    '55-59': ('SP.POP.5559.MA.5Y', 'SP.POP.5559.FE.5Y'),
    '60-64': ('SP.POP.6064.MA.5Y', 'SP.POP.6064.FE.5Y'),
    '65-69': ('SP.POP.6569.MA.5Y', 'SP.POP.6569.FE.5Y'),
    '70-74': ('SP.POP.7074.MA.5Y', 'SP.POP.7074.FE.5Y'),
    '75-79': ('SP.POP.7579.MA.5Y', 'SP.POP.7579.FE.5Y'),
    '80+': ('SP.POP.80UP.MA.5Y', 'SP.POP.80UP.FE.5Y')
}

def fetch_data_for_gender_code(gender_code, age_group=None):
    logging.info(f'Fetching data for {gender_code} i.e., {age_group}')
    return wb.data.DataFrame(gender_code)

def fetch_and_save_data(gender_code, file_name):
    data = fetch_data_for_gender_code(gender_code, age_group=file_name)
    pd.to_pickle(data, file_name)
    return gender_code, data

data_cache = {}

with ThreadPoolExecutor() as executor:
    futures = []
    for age_group, (male_code, female_code) in age_group_codes.items():
        # For male data
        male_file = f'cache/male_{age_group}.pkl'
        if not os.path.exists(male_file):
            futures.append(executor.submit(fetch_and_save_data, male_code, male_file))
        
        # For female data
        female_file = f'cache/female_{age_group}.pkl'
        if not os.path.exists(female_file):
            futures.append(executor.submit(fetch_and_save_data, female_code, female_file))

    for future in futures:
        gender_code, data = future.result()
        data_cache[gender_code] = data

# Load data from files for existing cache files
for age_group, (male_code, female_code) in age_group_codes.items():
    male_file = f'cache/male_{age_group}.pkl'
    if os.path.exists(male_file) and male_code not in data_cache:
        data_cache[male_code] = pd.read_pickle(male_file)

    female_file = f'cache/female_{age_group}.pkl'
    if os.path.exists(female_file) and female_code not in data_cache:
        data_cache[female_code] = pd.read_pickle(female_file)

# %%
def plot_population_pyramid(country_code, year):
    male_population = []
    female_population = []
    age_groups = list(age_group_codes.keys())
    for age_group, (male_code, female_code) in age_group_codes.items():
        logging.debug(f'Fetching data for {age_group} for {country_code} in {year}')
        male_data = data_cache.get(male_code)
        female_data = data_cache.get(female_code)
        
        if male_data is not None and female_data is not None:
            male_population.append(-male_data.loc[country_code, f'YR{year}'])
            female_population.append(female_data.loc[country_code, f'YR{year}'])
        else:
            # Handle missing data gracefully
            male_population.append(0)
            female_population.append(0)

    # Determine the scale based on the maximum absolute value in the data
    max_value = max(max(male_population), max(female_population))
    if max_value >= 1e6:
        scale_label = 'Population (in millions)'
        male_population = [value/1e6 for value in male_population]
        female_population = [value/1e6 for value in female_population]
    else:
        scale_label = 'Population'

    # Plot
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(age_groups, male_population, color='blue', label='Male')
    ax.barh(age_groups, female_population, color='hotpink', label='Female')
    
    for i, (male, female) in enumerate(zip(male_population, female_population)):
        ax.text(male - 2.5, i - .13, f'{abs(male):.2f}M', color='black', fontsize=10)
        ax.text(female + .15, i - .13, f'{female:.2f}M', color='black', fontsize=10)
        total = abs(male) + female
        ax.text(max_value + 5, i - .13, f'{total:.2f}M', color='black', fontsize=10)
        

    
    # Adjust x-axis labels to be positive and add a label for scale
    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels([str(int(abs(tick))) for tick in ax.get_xticks()])
    ax.set_xlabel(scale_label)
    ax.set_title(f'Population Pyramid for {country_dropdown.label} in {year}')
    ax.legend()
    plt.show()

widgets.interactive(plot_population_pyramid, country_code=country_dropdown, year=year_slider)

# %%

def plot_population_and_trade(country_code, year):
    # Fetch total population data for the selected country and year
    total_population_data = wb.data.DataFrame('SP.POP.TOTL', economy=country_code, time=range(1960, year+1))
    
    # Fetch total imports and exports data for the selected country and year
    imports_data = wb.data.DataFrame('NE.IMP.GNFS.CD', economy=country_code, time=range(1960, year+1)).T
    exports_data = wb.data.DataFrame('NE.EXP.GNFS.CD', economy=country_code, time=range(1960, year+1)).T

    # Extract total population values
    # total_population_values = total_population_data['value'].values

    # Calculate total trade values (sum of imports and exports)
    total_trade_values = imports_data + exports_data

    # Create a figure with two y-axes
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Plot total population data on the left y-axis
    ax1.plot(total_population_data, color='blue', label='Total Population')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Total Population', color='blue')

    # Create a second y-axis for total imports and exports
    # ax2 = ax1.twinx()

    # Plot total trade data on the right y-axis
    # ax2.plot(range(1960, year+1), total_trade_values, color='green', label='Total Trade (USD)')
    # ax2.set_ylabel('Total Trade (USD)', color='green')

    # Set labels and title
    ax1.set_title(f'Total Population and Total Trade for {country_code} (1960-{year})')

    # Show legend
    ax1.legend(loc='upper left')
    # ax2.legend(loc='upper right')

    plt.show()

# Create interactive widgets for country selection and year
widgets.interactive(plot_population_and_trade, country_code=country_dropdown, year=year_slider)




