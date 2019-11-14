import pandas as pd
import math

import bokeh.plotting as plt
from bokeh.models import ColumnDataSource, Legend, LegendItem


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


energy_levels = ['energy_source_level_0','energy_source_level_1',
                 'energy_source_level_2', 'energy_source_level_3',
                 'technology_level']

global_sources = ['EUROSTAT','ENTSO-E SOAF','ENTSO-E Data Portal',
                  'ENTSO-E Transparency Platform','ENTSO-E Power Statistics',
                  'National source']


def which_source(x):
    if x in global_sources:
        return x
    else:
        return 'National source'
    
def load_opsd_data(filepath):
    data = pd.read_csv(filepath, index_col=0)
    data["capacity"] = data["capacity"]/1000
    data["source_new"] = data["source"].apply(which_source)
    return data



def filter_data_set(data, input_co, input_year, input_source, level, unique=False):
    
    co_subset = data['country'] == input_co
    y_subset = data['year'].isin(input_year)
    energy_source_level = data[level] == True
    
    if isinstance(input_source, str):
        input_source = [input_source]
        
    source_subset = data['source_new'].isin(input_source)
    drop_list = co_subset & y_subset & energy_source_level & source_subset
    ret_data = data.loc[drop_list, :].copy()
    y_col = ret_data["year"].astype(str, copy=True).to_numpy()
    ret_data.drop(labels='year', axis=1, inplace=True)
    ret_data.loc[:,"year"] = y_col

    if unique:
        technologies = list(ret_data.technology.unique())
        years = list(ret_data.year.unique())
        return ret_data, technologies, years
    else:
        return ret_data
    

def prepare_data(data):
    source_data = pd.pivot_table(data, 
                                index=('year','source'),
                                columns='technology',
                                values='capacity',
                                aggfunc=sum,
                                margins=False)
    
    source_data.fillna(0, inplace=True)
    x_axis = list(source_data.index)
    source_data.reset_index(inplace=True)
    source_data['index'] = x_axis
    
    return source_data, x_axis


def init_plot(data, level, size=(800,800)):
    
    ret_data, technologies, years = filter_data_set(data,
                                                    'DE',
                                                    [2015,2016],
                                                    ['EUROSTAT','ENTSO-E SOAF'],
                                                    level,
                                                    unique=True)
    
    source_data, x_axis = prepare_data(ret_data)
    
    source = ColumnDataSource(source_data)
    colors = [colormap[t] for t in technologies]
    
    p = plt.figure(x_range=[], title="Comparison "+level, plot_width=size[0], plot_height=size[1],
                   y_axis_label='GW', toolbar_location="above")
    
    p.x_range.factors = x_axis
    
    r = p.vbar_stack(technologies, x='index', width=0.8, source=source,
                 color=colors)
    
    p.xaxis.major_label_orientation = math.pi/2
    
    it = [LegendItem(label=t, renderers=[r[i]]) for i,t in enumerate(technologies)]
    legend = Legend(items=it)
    p.add_layout(legend, 'right')
    
    return source, p





