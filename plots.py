import pandas as pd
import numpy as np
import os.path
import math

import bokeh.plotting as plt
from bokeh.io import output_notebook, curdoc
from bokeh.layouts import row, column
from bokeh.models import Callback, ColumnDataSource, FactorRange
from bokeh.models.widgets import RangeSlider, MultiSelect, Select, RadioButtonGroup

data_file = 'national_generation_capacity_stacked.csv'
filepath = os.path.join('output', data_file)
data = pd.read_csv(filepath, index_col=0)
data["capacity"] = data["capacity"]/1000

colormap = {
    'Fossil fuels': 'Black',
    'Lignite': 'SaddleBrown',
    'Hard coal': 'Black',
    'Oil': 'Violet',
    'Natural gas': 'IndianRed',
    'Combined cycle': '#d57676',
    'Gas turbine': '#e19d9d',
    'Other and unknown natural gas': '#c33c3c',
    'Differently categorized natural gas': 'IndianRed',
    'Non-renewable waste': 'SandyBrown',
    'Mixed fossil fuels': 'LightGray',
    'Other fossil fuels': 'DarkGray',
    'Differently categorized fossil fuels': 'Gray',
    'Nuclear': 'Red',
    'Renewable energy sources': 'Green',
    'Hydro': 'Navy',
    'Run-of-river': '#0000b3',
    'Reservoir': '#0000e6',
    'Reservoir including pumped storage': '#0000e6',
    'Pumped storage': '#1a1aff',
    'Pumped storage with natural inflow': '#1a1aff',
    'Differently categorized hydro': 'Navy',
    'Wind': 'SkyBlue',
    'Onshore': 'LightSkyBlue',
    'Offshore': 'DeepSkyBlue',
    'Differently categorized wind': 'SkyBlue',
    'Solar': 'Yellow',
    'Photovoltaics': '#ffff33',
    'Concentrated solar power': '#ffff66',
    'Differently categorized solar': 'Yellow',
    'Geothermal': 'DarkRed',
    'Marine': 'Blue',
    'Bioenergy and renewable waste': 'Green',
    'Biomass and biogas': '#00b300',
    'Sewage and landfill gas': '#00e600',
    'Other bioenergy and renewable waste': 'Green',
    'Differently categorized renewable energy sources': 'Green',
    'Other or unspecified energy sources': 'Orange',
    'Total': 'Black',
    'renewable': 'Green'
}

global_sources = ['EUROSTAT','ENTSO-E SOAF','ENTSO-E Data Portal',
                  'ENTSO-E Transparency Platform','ENTSO-E Power Statistics',
                  'National source']


def which_source(x):
    if x in global_sources:
        return x
    else:
        return 'National source'

oldest_year = min(data["year"])
newest_year = max(data["year"])

input_co = list(data["country"].unique())
data["source_new"] = data["source"].apply(which_source)
energy_levels = ['energy_source_level_0','energy_source_level_1',
                 'energy_source_level_2', 'energy_source_level_3',
                 'technology_level']


def create_data_set(input_co, input_year, input_source, level):
    
    co_subset = data['country'] == input_co
    y_subset = data['year'].isin(input_year)
    energy_source_level = data[level] == True
    
    if isinstance(input_source, str):
        input_source = [input_source]
        
    source_subset = data['source_new'].isin(input_source)
    drop_list = co_subset & y_subset & energy_source_level & source_subset
    ret_data = data.loc[drop_list, :]
    y_col = ret_data["year"].astype(str, copy=True).to_numpy()
    ret_data.drop(labels='year', axis=1, inplace=True)
    ret_data.loc[:,"year"] = y_col

  
    sources = list(ret_data.source.unique())
    technologies = list(ret_data.technology.unique())
    years = list(ret_data.year.unique())
    
    
    source_data = pd.pivot_table(ret_data, 
                              index=('year','source'),
                              columns='technology',
                              values='capacity',
                              aggfunc=sum,
                              margins=False)
    
    source_data.fillna(0, inplace=True)
    x_axis = list(source_data.index)
    source_data.reset_index(inplace=True)
    source_data['index'] = x_axis
    
    return source_data, x_axis, sources, technologies, years

source_data , x_axis, sources, technologies, years = create_data_set('DE', [2015,2016], ['EUROSTAT','ENTSO-E SOAF'], 'energy_source_level_2')

#tes = create_data_set('FR', [2015,2015], ['EUROSTAT','ENTSO-E SOAF'], 'energy_source_level_2')


source = ColumnDataSource(source_data)
colors = [colormap[t] for t in technologies]

p = plt.figure(x_range=[], title="Comparison", plot_width=1200, plot_height=800,
               y_axis_label='GW')

p.vbar_stack(technologies, x='index', width=0.6, source=source, #legend_label=technologies,
             color=colors)

p.xaxis.major_label_orientation = math.pi/2

y_slider = RangeSlider(title="Years", value=(2015,2016), start=oldest_year, end=newest_year, step=1)

m_select = MultiSelect(title="Available Sources:", value=['EUROSTAT','ENTSO-E SOAF'],
                       options=[(s,s) for s in global_sources])

c_select = Select(title="Country", options=input_co, value='FR')

level_button = RadioButtonGroup(labels=energy_levels, active=2)

wid = [c_select, y_slider, m_select]

def update(attrname, old, new):

    # Get the current slider values
    y = y_slider.value
    y_range = [x for x in range(y[0],y[1]+1)]
    
    s_selected = m_select.value
    co = c_select.value
    
    level = energy_levels[level_button.active]
    
    source_data, _x_axis, _sources, _technologies, _years = create_data_set(co, y_range, s_selected, level)
    source.data = source_data
    p.x_range.factors = _x_axis



for w in wid:
    w.on_change('value', update)

level_button.on_change('active', update)

rows = row(wid)
layout = column(rows, p, level_button)

#plt.show(layout)

curdoc().add_root(layout)
curdoc().title = "asdf"

p.xaxis()









#source_data1 , x_axis1, sources1, technologies1, years1 = create_data_set('DE', [2015,2016], global_sources, 'energy_source_level_2')





