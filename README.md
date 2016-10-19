
# Open Power System Data: Aggregated Generation Capacity by Technology and Country

## About this Notebook

This is a ipython notebook that processes data on aggregated generation capacities for European countries. The data includes generation capacities for nuclear, fossil and renewable fuels on an aggregated and, if possible, disaggregated technology levels. The data mostly reflects the years 2013 and 2014.

The final output of the notebook is a list of national generation capacities differentiated by input fuels and technologies, as well as by different data sources

## Data Sources

The raw data is based on an extensive research of available national and international statistics. Due to the diverse structure of data sources, a compiled and structured dataset is used as input for further processing. Generally, two cross-national data sources are considered, complemented by national data sources.

The cross-national data sources are:
- [ENTSOE "Scenario Outlook & Adequacy Forecasts 2014-2030"](https://www.entsoe.eu/publications/system-development-reports/adequacy-forecasts/soaf-2014-2030/Pages/default.aspx)
- [ENTSOE "Scenario Outlook & Adequacy Forecasts 2013-2030"](https://www.entsoe.eu/publications/system-development-reports/adequacy-forecasts/soaf-2013-2030/Pages/default.aspx)
- EUROSTAT "Energy Statistics" compiled in [EU Commission's "Energy datasheets"](http://ec.europa.eu/energy/en/statistics/country)

Beside this, the data is complemented by national sources, which includes national statistical offices, ministries, regulatory authorities, transmission system operators, as well as other associations. All data sources are listed in the datapackage.json file including their link.  

## Links to Notebooks

The following notebooks are used to process the input data:
- [processing.ipynb](https://github.com/Open-Power-System-Data/datapackage_national_generation_capacities/blob/master/processing.ipynb) - Processing of the input data.
- [tests.ipynb](https://github.com/Open-Power-System-Data/datapackage_national_generation_capacities/blob/master/tests.ipynb) - Consistency checks and visualization of the dataset.

