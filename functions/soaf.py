import os.path
import functions.helper_functions as f
import pandas as pd
import numpy as np
from . import logger


dict_energy_source = {'Nuclear Power': 'Nuclear',
                     'Fossil Fuels': 'Fossil fuels',
                     'Hard Coal': 'Hard coal',
                     'Lignite': 'Lignite',
                     'Gas': 'Natural gas',
                     'Oil': 'Oil',
                     'Mixed Fuels': 'Mixed fossil fuels',
                     'Hydro power (total)': 'Hydro',
                     'of which renewable hydro generation': 'NaN',
                     'of which run-of-river (pre-dominantly)': 'Run-of-river',
                     'of which storage and pumped storage (total)': 'Reservoir including pumped storage', # auxiliary class definition
                     'Renewable Energy Sources (other than hydro)': 'renewable',
                     'Solar': 'Solar',
                     'Wind': 'Wind',
                     'of which offshore': 'Offshore',
                     'of which onshore': 'Onshore',
                     'Biomass': 'Biomass and biogas',
                     'Not Clearly Identifiable Energy Sources': 'Other or unspecified energy sources',
                     'Net generating Capacity': 'NaN',
                     'Import Capacity': 'NaN',
                     'Export Capacity': 'NaN',
                     'Load': 'NaN',
                     'Load Management': 'NaN',
                     'Maintenance and Overhauls': 'NaN',
                     'Margin Against Seasonal Peak Load': 'NaN',
                     'Adequacy Reference Margin': 'NaN',
                     'National Power Data': 'NaN',
                     'Non-Usable Capacity': 'NaN',
                     'Outages': 'NaN',
                     'Reliable Available Capacity': 'NaN',
                     'Remaining Capacity': 'NaN',
                     'Spare Capacity': 'NaN',
                     'System Service Reserve': 'NaN',
                     'Unavailable Capacity': 'NaN',
                     'Simultaneous Exportable Capacity for Adequacy': 'NaN',
                     'Simultaneous Importable Capacity for Adequacy': 'NaN',
                     '“The values of Simultaneous Importable/Exportable Capacity for Adequacy do not include the border with Austria as there is a common market between Germany and Austria for which no NTC exists.”': 'NaN'}

class SoafDataRaw:
    
    
    def __init__(self, url, zipfile, xls, year):
        
        self.source = 'ENTSO-E'
        self.year = year
        self.sourcefolder = os.path.join('SO&AF', str(year))
        
        self.folderpath = f.downloadandcache(url,
                                             zipfile,
                                             os.path.join(self.source,
                                                          self.sourcefolder))
        
        self.filepath =  os.path.join(self.folderpath, xls)
        
       
        self.transformIntoDataFrame()


    
    def transformIntoDataFrame(self):
        
        s = "Reading {file} and transforming into a DataFrame".format(file=self.filepath)
        logger.info(s)
          
        dict_with_dfs = pd.read_excel(self.filepath, sheet_name=None,
                                      skiprows=11, header=[0], index_col=0)
        
        collect_arr =  list()
        for key,df in dict_with_dfs.items():
            df.reset_index(inplace=True)
            df = df[['index', self.year]].rename(columns={'index': 'technology'})
            subset = df['technology'].isin(dict_energy_source.keys())
            df= df[subset]
            
            df['technology'].replace(dict_energy_source, inplace=True)
            df['country'] = key[0:2]
            df['year'] = self.year
            df.rename(columns={self.year: 'value'}, inplace=True)
            df['value'] = 1000 * df['value']
            df['value'].replace({'NaN' : 0, np.nan : 0}, inplace=True)
            df.rename(columns={'value' : 'capacity'}, inplace=True)
            df['technology'].replace('NaN', np.nan, inplace=True)
            df = df[df['technology'].isnull() == False]
            df['capacity'] = df['capacity'].astype(float)
            
            collect_arr.append(df)
        
        df = pd.concat(collect_arr)
        
        self.transformed_df = df