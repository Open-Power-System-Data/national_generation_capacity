import os.path
import functions.helper_functions as f
import pandas as pd

dict_energy_source = {'Nuclear Power': 'Nuclear',
                  'Lignite': 'Lignite',
                  'Hard coal': 'Hard coal',
                  'Gas': 'Natural gas',
                  'Oil': 'Oil',
                  'Renewable Energy Sources (other than hydro)': 'renewable',  # auxiliary definition, will be deleted at a later stage
                  'of which onshore': 'Wind onshore',
                  'of which offshore': 'Wind offshore',
                  'Solar': 'Solar',
                  'Biomass': 'Biomass and biogas',
                  'Hydro power (total)': 'Hydro',
                  'of which run-of-river (pre-dominantly)': 'Run of river',
                  'of which storage and pumped storage (total)':'PSP',
                  'of which renewable hydro generation': 'nochmal hydro',
                  'Not Clearly Identifiable Energy Sources': 'other'}

class SoafDataRaw:
    
    dict_energy_source = {'Nuclear Power': 'Nuclear',
                      'Lignite': 'Lignite',
                      'Hard coal': 'Hard coal',
                      'Gas': 'Natural gas',
                      'Oil': 'Oil',
                      'Renewable Energy Sources (other than hydro)': 'renewable',  # auxiliary definition, will be deleted at a later stage
                      'of which onshore': 'Wind onshore',
                      'of which offshore': 'Wind offshore',
                      'Solar': 'Solar',
                      'Biomass': 'Biomass and biogas',
                      'Hydro power (total)': 'Hydro',
                      'of which run-of-river (pre-dominantly)': 'Run of river',
                      'of which storage and pumped storage (total)':'PSP',
                      'of which renewable hydro generation': 'nochmal hydro',
                      'Not Clearly Identifiable Energy Sources': 'other'}
    
    def __init__(self, url, zipfile, xls, year):
        
        self.source = 'ENTSO-E'
        self.year = year
        self.sourcefolder = 'SO&AF {year}'.format(year=year)
        
        self.folderpath = f.downloadandcache(url,
                                             zipfile,
                                             os.path.join(self.source,
                                                          self.sourcefolder))
        
        self.filepath =  os.path.join(self.folderpath, xls)
        
        self.transformIntoDataFrame()


    
    def transformIntoDataFrame(self):
        
        print("Reading {file} and transforming into a DataFrame".format(file=self.filepath))
        
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
            collect_arr.append(df)
        
        df = pd.concat(collect_arr)
        
        self.transformed_df = df