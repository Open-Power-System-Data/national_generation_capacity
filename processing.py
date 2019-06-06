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

test = data_eurostat.pivot_table(values='capacity',
                                 index=['country','year'],
                                 columns='technology')


test['Differently categorized solar'] = 0
test['Solar'] = test[['Photovoltaics', 'Concentrated solar power']].sum(axis=1)
test['Differently categorized wind'] = test['Wind']
bio_arr = ['Biomass and biogas', 'Other bioenergy and renewable waste']
test['Bioenergy and renewable waste'] = test[bio_arr].sum(axis=1)
res_arr = ['Hydro', 'Wind', 'Solar', 'Geothermal', 'Marine',
           'Bioenergy and renewable waste']
test['Renewable energy sources'] = test[res_arr].sum(axis=1)


test['Fossil fuels'] = test['Fossil fuels'] - test['Bioenergy and renewable waste']
test['Differently categorized fossil fuels'] = test['Fossil fuels']\
                                             - test['Non-renewable waste']

total_arr = ['Fossil fuels','Nuclear','Renewable energy sources']
test['Total'] = test[total_arr].sum(axis=1)

data_eurostat = test.stack().reset_index().rename(columns={0: 'capacity'})

idx = data_eurostat[data_eurostat['technology'] == 'Fossil fuels'].index
data_eurostat.drop(idx, inplace=True)


data_eurostat['source'] = 'EUROSTAT'
data_eurostat['source_type'] = 'Statistical Office'
data_eurostat['capacity_definition'] = 'Unknown'
data_eurostat['type'] = 'Installed capacity in MW'


############ENTSOE###############

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


soaf_data = pd.concat([soaf.transformed_df for soaf in soafs])

# Correct that in the Soaf2015 datatset the year column is 2016 instead of 2015
soaf_data['year'].replace({2016 : 2015}, inplace=True)