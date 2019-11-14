import pandas as pd
import math

import bokeh.plotting as plt
from bokeh.models import ColumnDataSource, Legend, LegendItem


colormap = {
    'Fossil fuels': 'Black',
    'Lignite': '#754937',
    'Hard coal': '#4d3e35',
    'Oil': '#272724',
    'Natural gas': '#e54213',
    'Combined cycle': '#ff814b',
    'Gas turbine': '#880000',
    'Other and unknown natural gas': '#e54213',
    'Differently categorized natural gas': '#e54213',
    'Non-renewable waste': '#b7c7cd',
    'Mixed fossil fuels': '#e9f9fd',
    'Other fossil fuels': '#6f7d84',
    'Differently categorized fossil fuels': '#6f7d84',
    'Nuclear': '#ae393f',
    'Renewable energy sources': '#24693d',
    'Hydro': '#0d47a1',
    'Run-of-river': '#6782e4',
    'Reservoir': '#2e56b4',
    'Reservoir including pumped storage': '#5472d3',
    'Pumped storage': '#002171',
    'Pumped storage with natural inflow': '#00125e',
    'Differently categorized hydro': '#0d47a1',
    'Wind': '#326776',
    'Onshore': '#518696',
    'Offshore': '#215968',
    'Differently categorized wind': '#00303d',
    'Solar': '#ffeb3b',
    'Photovoltaics': '#fffb4e',
    'Concentrated solar power': '#d5c200',
    'Differently categorized solar': '#ffeb3b',
    'Geothermal': '#ef9347',
    'Marine': '#002171',
    'Bioenergy and renewable waste': '#7cb342',
    'Biomass and biogas': '#c2f08e',
    'Sewage and landfill gas': '#95cb59',
    'Other bioenergy and renewable waste': '#316a00',
    'Differently categorized renewable energy sources': '#dce775',
    'Other or unspecified energy sources': '#9526b7',
    'Total': 'Black',
    'renewable': '#316a00'
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





