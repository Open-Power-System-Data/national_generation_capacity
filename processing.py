import functions.helper_functions as f
import functions.soaf as soaf
import os
import pandas as pd
import numpy as np




data_file = 'National_Generation_Capacities.xlsx'
filepath = os.path.join('input', data_file)

# Read data into pandas
data_raw = pd.read_excel(filepath,
                         sheet_name='Summary',
                         header=None,
                         na_values=['-'],
                         skiprows=0)




# Deal with merged cells from Excel: fill first three rows with information
data_raw.iloc[0:2] = data_raw.iloc[0:2].fillna(method='ffill', axis=1)

# Set index for rows
data_raw = data_raw.set_index([0])
data_raw.index.name = 'technology'

# Extract energylevels from raw data
energylevels_raw = data_raw.iloc[:, 0:5]


# Delete definition of energy levels from raw data
data_raw = data_raw.drop(data_raw.columns[[0, 1, 2, 3, 4]], axis=1)

# Set multiindex column names
data_raw.columns = pd.MultiIndex.from_arrays(data_raw[:6].values,
                                             names=['country', 'type', 'year',
                                                    'source', 'source_type',
                                                    'capacity_definition'])

# Remove 3 rows which are already used as column names
data_raw = data_raw[pd.notnull(data_raw.index)]

# Extract the ordering of technologies
technology_order = data_raw.index.str.replace('- ', '').values.tolist()

# Reshape dataframe to list
data_opsd = pd.DataFrame(data_raw.stack(level=['source', 'source_type', 'year',
                                               'type', 'country',
                                               'capacity_definition']))


# Reset index for dataframe
data_opsd = data_opsd.reset_index()
data_opsd['technology'] = data_opsd['technology'].str.replace('- ', '')


# Delete entries with missing source
data_opsd = data_opsd[data_opsd['source'].isnull() == False]
data_opsd = data_opsd[data_opsd['source'] != 0]

# Delete entries from EUROSTAT and entsoe as they will be directly used from original sources
data_opsd = data_opsd[data_opsd['source'] != 'EUROSTAT']
data_opsd = data_opsd[data_opsd['source'] != 'entsoe']


data_opsd = data_opsd.rename(columns={0: 'capacity'})

data_opsd['capacity'] = pd.to_numeric(data_opsd['capacity'], errors='coerce')


# For some source, permission to publish data
data_opsd.loc[(data_opsd['source'] == 'ELIA'),
              'comment'] = 'data available, but cannot be provided'
data_opsd.loc[(data_opsd['source'] == 'BMWi'),
              'comment'] = 'data available, but cannot be provided'
data_opsd.loc[(data_opsd['source'] == 'Mavir'),
              'comment'] = 'data available, but cannot be provided'







### Eurostat ##################################################################
url_eurostat = ('http://ec.europa.eu/eurostat/estat-navtree-portlet-prod/'
                'BulkDownloadListing?sort=1&downfile=data%2Fnrg_113a.tsv.gz')


filepath_eurostat = f.downloadandcache(url_eurostat, 'Eurostat.tsv.gz', 'Eurostat')



data_eurostat = pd.read_csv(filepath_eurostat,
                               compression='gzip',
                               sep='\t|,',
                               engine='python'
                               )

id_vars = ['unit', 'product','indic_nrg', 'geo\\time']
data_eurostat = pd.melt(data_eurostat, id_vars=id_vars,
                        var_name='year', value_name='value')



data_definition = pd.read_csv(os.path.join('input', 'definition_EUROSTAT_indic.txt'),
                              header=None,
                              names=['indic', 'description',
                                     'energy source'],
                              sep='\t')

data_eurostat = data_eurostat.merge(data_definition,
                                    how='left',
                                    left_on='indic_nrg',
                                    right_on='indic')

data_eurostat = data_eurostat[data_eurostat['energy source'].isnull() == False]

values_as_string = data_eurostat['value'].astype(str)
string_values = values_as_string.str.split(' ', 1).str[0]
string_values.replace(':', np.nan, inplace=True)
subset_nan = string_values.isnull()

data_eurostat['value'] = string_values
#data_eurostat['comment'] = ''
#data_eurostat.loc[subset_nan, 'comment'] = 'not available'

data_eurostat['year'] = data_eurostat['year'].astype(int)
data_eurostat['value'] = data_eurostat['value'].astype(float)

data_eurostat = data_eurostat.drop(['unit', 'product', 'indic_nrg',
                                    'indic', 'description'], axis=1)

data_eurostat = data_eurostat.rename(columns={'geo\\time': 'country',
                                              'energy source': 'technology',
                                              'value': 'capacity'})

data_eurostat['country'].replace({'UK': 'GB', 'EL': 'GR'}, inplace=True)

drop_list = data_eurostat[data_eurostat['country'].isin(['EU28','EA19'])].index
data_eurostat.drop(drop_list, inplace=True)

by_columns = ['technology', 'year', 'country']
data_eurostat = pd.DataFrame(data_eurostat.groupby(by_columns)['capacity'].sum())
data_eurostat_isnull = data_eurostat['capacity'].isnull() == True
#data_eurostat.loc[data_eurostat_isnull, 'comment'] = 'not available'
#data_eurostat['comment'] = data_eurostat['comment'].fillna('').astype(str)
data_eurostat.reset_index(inplace=True)


#########

eurostat_pivot = data_eurostat.pivot_table(values='capacity',
                                 index=['country','year'],
                                 columns='technology')


eurostat_pivot['Differently categorized solar'] = 0
eurostat_pivot['Solar'] = eurostat_pivot[['Photovoltaics', 'Concentrated solar power']].sum(axis=1)
eurostat_pivot['Differently categorized wind'] = eurostat_pivot['Wind']
bio_arr = ['Biomass and biogas', 'Other bioenergy and renewable waste']
eurostat_pivot['Bioenergy and renewable waste'] = eurostat_pivot[bio_arr].sum(axis=1)
res_arr = ['Hydro', 'Wind', 'Solar', 'Geothermal', 'Marine',
           'Bioenergy and renewable waste']
eurostat_pivot['Renewable energy sources'] = eurostat_pivot[res_arr].sum(axis=1)


eurostat_pivot['Fossil fuels'] = eurostat_pivot['Fossil fuels'] - eurostat_pivot['Bioenergy and renewable waste']
eurostat_pivot['Differently categorized fossil fuels'] = eurostat_pivot['Fossil fuels']\
                                             - eurostat_pivot['Non-renewable waste']

total_arr = ['Fossil fuels','Nuclear','Renewable energy sources']
eurostat_pivot['Total'] = eurostat_pivot[total_arr].sum(axis=1)

data_eurostat = eurostat_pivot.stack().reset_index().rename(columns={0: 'capacity'})

idx = data_eurostat[data_eurostat['technology'] == 'Fossil fuels'].index
data_eurostat.drop(idx, inplace=True)


data_eurostat['source'] = 'EUROSTAT'
data_eurostat['source_type'] = 'Statistical Office'
data_eurostat['capacity_definition'] = 'Unknown'
data_eurostat['type'] = 'Installed capacity in MW'


############ENTSOE SOAF###############

soafs = [soaf.SoafDataRaw('https://www.entsoe.eu/fileadmin/user_upload/_library/SDC/SOAF/SO_AF_2011_-_2025_.zip',
                          'SO_AF_2011_-_2025_.zip',
                          'SO&AF 2011 - 2025 Scenario B.xls',
                          2011),

        soaf.SoafDataRaw('https://www.entsoe.eu/fileadmin/user_upload/_library/SDC/SOAF/120705_SOAF_2012_Dataset.zip',
                         '120705_SOAF_2012_Dataset.zip',
                         'SOAF 2012 Scenario B.xls',
                         2012),
                             
        soaf.SoafDataRaw('https://www.entsoe.eu/fileadmin/user_upload/_library/publications/entsoe/So_AF_2013-2030/130403_SOAF_2013-2030_dataset.zip',
                         '130403_SOAF_2013-2030_dataset.zip',
                         'ScB.xls',
                         2013),
                             
        soaf.SoafDataRaw('https://www.entsoe.eu/Documents/SDC%20documents/SOAF/140602_SOAF%202014_dataset.zip',
                         '140602_SOAF%202014_dataset.zip',
                         'ScB.xlsx',
                         2014),
                             
        soaf.SoafDataRaw('https://www.entsoe.eu/Documents/Publications/SDC/data/SO_AF_2015_dataset.zip',
                         'SO_AF_2015_dataset.zip',
                         os.path.join('SO&AF 2015 dataset', 'ScB_publication.xlsx'),
                         2016)]


data_soaf = pd.concat([s.transformed_df for s in soafs])

# Correct that in the Soaf2015 datatset the year column is 2016 instead of 2015
data_soaf['year'].replace({2016 : 2015}, inplace=True)

   
soaf_unstacked = f.unstackData(data_soaf)

soaf_unstacked['Differently categorized solar'] = soaf_unstacked['Solar']

soaf_unstacked['Differently categorized wind'] = soaf_unstacked['Wind']\
                                                - soaf_unstacked['Offshore']\
                                                - soaf_unstacked['Onshore']

soaf_unstacked['Differently categorized hydro'] = soaf_unstacked['Hydro']\
                                                - soaf_unstacked['Run-of-river']\
                                                - soaf_unstacked['Reservoir including pumped storage']
                                                

soaf_unstacked['Bioenergy and renewable waste'] = soaf_unstacked['Biomass and biogas']
                                                
soaf_unstacked['Differently categorized renewable energy sources'] = (
                                          soaf_unstacked['renewable']
                                        - soaf_unstacked['Wind']
                                        - soaf_unstacked['Solar']
                                        - soaf_unstacked['Biomass and biogas'])

subtract_fossils_arr = ['Lignite','Hard coal','Oil','Natural gas','Mixed fossil fuels']

soaf_unstacked['Differently categorized fossil fuels'] = soaf_unstacked['Fossil fuels']\
                                                        - soaf_unstacked[subtract_fossils_arr].sum(axis=1)


res_arr = ['Solar','Wind','Bioenergy and renewable waste','Hydro',
           'Differently categorized renewable energy sources']

soaf_unstacked['Renewable energy sources'] = soaf_unstacked[res_arr].sum(axis=1)

total_arr = ['Renewable energy sources','Fossil fuels','Nuclear',
             'Other or unspecified energy sources']

soaf_unstacked['Total'] = soaf_unstacked[total_arr].sum(axis=1)



data_soaf = f.restackData(soaf_unstacked)

data_soaf.loc[data_soaf['capacity'] < 0, 'capacity'] = 0

data_soaf['source'] = 'entsoe SOAF'
data_soaf['type'] = 'Installed capacity in MW'
data_soaf['capacity_definition'] = 'Net capacity'
data_soaf['source_type'] = 'Other association'


############ENTSOE statistical data ###############

url_entsoe = 'https://docstore.entsoe.eu/Documents/Publications/Statistics/NGC_2010-2015.xlsx'

filepath_entsoe = f.downloadandcache(url_entsoe, 'Statistics.xls',
                                     os.path.join('ENTSO-E','Statistical data 2010-2015')
                                     )

data_entsoe_raw = pd.read_excel(filepath_entsoe)


dict_energy_source = {'hydro': 'Hydro',
                      'of which storage': 'Reservoir',
                      'of which run of river': 'Run-of-river',
                      'of which pumped storage': 'Pumped storage',
                      'nuclear': 'Nuclear',
                      'of which wind': 'Wind',
                      'of which solar': 'Solar',
                      'of which biomass': 'Biomass and biogas',
                      'fossil_fuels': 'Fossil fuels',
                      'other': 'Other or unspecified energy sources',
                      "Country": "country",
                      'fossil_fueals': 'Fossil fuels'}

data_entsoe_raw.rename(columns=dict_energy_source,
                       inplace=True)

data_entsoe_raw.drop(columns='representativity', inplace=True)

data_entsoe_raw['Differently categorized solar'] = data_entsoe_raw['Solar']
data_entsoe_raw['Differently categorized wind'] = data_entsoe_raw['Wind']
data_entsoe_raw['Bioenergy and renewable waste'] = data_entsoe_raw['Biomass and biogas']
data_entsoe_raw['Differently categorized fossil fuels'] = data_entsoe_raw['Fossil fuels']


data_entsoe_raw['Differently categorized hydro'] = (
        data_entsoe_raw['Hydro']
        - data_entsoe_raw['Run-of-river']
        - data_entsoe_raw['Reservoir']
        - data_entsoe_raw['Pumped storage'])

data_entsoe_raw['Differently categorized renewable energy sources'] = (
        data_entsoe_raw['renewable']
        - data_entsoe_raw['Wind']
        - data_entsoe_raw['Solar']
        - data_entsoe_raw['Biomass and biogas'])

data_entsoe_raw['Renewable energy sources'] = (
        data_entsoe_raw['Hydro']
        + data_entsoe_raw['Wind']
        + data_entsoe_raw['Solar']
        + data_entsoe_raw['Bioenergy and renewable waste']
        + data_entsoe_raw['Differently categorized renewable energy sources'])

data_entsoe_raw['Total'] = (
        data_entsoe_raw['Renewable energy sources']
        + data_entsoe_raw['Nuclear']
        + data_entsoe_raw['Fossil fuels']
        + data_entsoe_raw['Other or unspecified energy sources'])

data_entsoe = pd.melt(data_entsoe_raw,
                      id_vars=['country', 'year'],
                      var_name='energy_source',
                      value_name='capacity')

data_entsoe['country'].replace('NI', 'GB', inplace=True)
data_entsoe.loc[data_entsoe['capacity'] < 0, 'capacity'] = 0

data_entsoe['source'] = 'entsoe Statistics'
data_entsoe['source_type'] = 'Other association'
data_entsoe['capacity_definition'] = 'Net capacity'
data_entsoe['type'] = 'Installed capacity in MW'

##############################################################################

data = pd.concat([data_opsd, data_eurostat, data_soaf, data_entsoe], sort=False)
data['comment'] = data['comment'].fillna('').astype(str)

col_order = ['technology', 'source', 'source_type', 'year', 'type', 'country',
             'capacity_definition', 'capacity', 'comment']

data = data[col_order]

energy_source_mapping = pd.read_csv('energy_source_mapping.csv', index_col ='name')
energy_source_mapping.replace({0: False, 1: True}, inplace=True)

data = data.merge(energy_source_mapping,
                  left_on='technology',
                  right_index=True,
                  how='left')

###############################################################################