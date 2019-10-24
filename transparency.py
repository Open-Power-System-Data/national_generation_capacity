# -*- coding: utf-8 -*-
"""
Created on Wed Oct 23 17:32:28 2019

@author: mak
"""


PSRTYPE_MAPPINGS = {
    'A03': 'Mixed',
    'A04': 'Generation',
    'A05': 'Load',
    'B01': 'Biomass',
    'B02': 'Fossil Brown coal/Lignite',
    'B03': 'Fossil Coal-derived gas',
    'B04': 'Fossil Gas',
    'B05': 'Fossil Hard coal',
    'B06': 'Fossil Oil',
    'B07': 'Fossil Oil shale',
    'B08': 'Fossil Peat',
    'B09': 'Geothermal',
    'B10': 'Hydro Pumped Storage',
    'B11': 'Hydro Run-of-river and poundage',
    'B12': 'Hydro Water Reservoir',
    'B13': 'Marine',
    'B14': 'Nuclear',
    'B15': 'Other renewable',
    'B16': 'Solar',
    'B17': 'Waste',
    'B18': 'Wind Offshore',
    'B19': 'Wind Onshore',
    'B20': 'Other',
    'B21': 'AC Link',
    'B22': 'DC Link',
    'B23': 'Substation',
    'B24': 'Transformer'}

import requests
import pandas as pd
import pytz
import bs4

def _extract_timeseries(xml_text):
    """
    Parameters
    ----------
    xml_text : str
    Yields
    -------
    bs4.element.tag
    """
    if not xml_text:
        return
    soup = bs4.BeautifulSoup(xml_text, 'html.parser')
    for timeseries in soup.find_all('timeseries'):
        yield timeseries

def parse_generation(xml_text):
    """
    Parameters
    ----------
    xml_text : str
    Returns
    -------
    pd.DataFrame
    """
    all_series = {}
    for soup in _extract_timeseries(xml_text):
        ts = _parse_generation_forecast_timeseries(soup)
        series = all_series.get(ts.name)
        if series is None:
            all_series[ts.name] = ts
        else:
            series = series.append(ts)
            series.sort_index()
            all_series[series.name] = series

    for name in all_series:
        ts = all_series[name]
        all_series[name] = ts[~ts.index.duplicated(keep='first')]

    df = pd.DataFrame.from_dict(all_series)
    return df

def _parse_generation_forecast_timeseries(soup):
    """
    Parameters
    ----------
    soup : bs4.element.tag
    Returns
    -------
    pd.Series
    """
    psrtype = soup.find('psrtype').text
    positions = []
    quantities = []
    for point in soup.find_all('point'):
        positions.append(int(point.find('position').text))
        quantity = point.find('quantity')
        if quantity is None:
            raise LookupError(f'No quantity found in this point, it should have one: {point}')
        quantities.append(float(quantity.text))

    series = pd.Series(index=positions, data=quantities)
    series = series.sort_index()
    series.index = _parse_datetimeindex(soup)

    series.name = PSRTYPE_MAPPINGS[psrtype]
    return series

def _parse_datetimeindex(soup):
    """
    Create a datetimeindex from a parsed beautifulsoup,
    given that it contains the elements 'start', 'end'
    and 'resolution'
    Parameters
    ----------
    soup : bs4.element.tag
    Returns
    -------
    pd.DatetimeIndex
    """
    start = pd.Timestamp(soup.find('start').text)
    end = pd.Timestamp(soup.find('end').text)
    delta = _resolution_to_timedelta(res_text=soup.find('resolution').text)
    index = pd.date_range(start=start, end=end, freq=delta, closed='left')
    return index

def _resolution_to_timedelta(res_text: str) -> str:
    """
    Convert an Entsoe resolution to something that pandas can understand
    """
    resolutions = {
        'PT60M': '60min',
        'P1Y': '12M',
        'PT15M': '15min',
        'PT30M': '30min'
    }
    delta = resolutions.get(res_text)
    if delta is None:
        raise NotImplementedError("Sorry, I don't know what to do with the "
                                  "resolution '{}', because there was no "
                                  "documentation to be found of this format. "
                                  "Everything is hard coded. Please open an "
                                  "issue.".format(res_text))
    return delta

def _datetime_to_str(dtm):
    """
    Convert a datetime object to a string in UTC
    of the form YYYYMMDDhh00
    Parameters
    ----------
    dtm : pd.Timestamp
        Recommended to use a timezone-aware object!
        If timezone-naive, UTC is assumed
    Returns
    -------
    str
    """
    if dtm.tzinfo is not None and dtm.tzinfo != pytz.UTC:
        dtm = dtm.tz_convert("UTC")
    fmt = '%Y%m%d%H00'
    ret_str = dtm.strftime(fmt)
    return ret_str

start = _datetime_to_str(pd.Timestamp('20171231', tz='Europe/Brussels'))
end = _datetime_to_str(pd.Timestamp('20181231', tz='Europe/Brussels'))

tok = '254d4cea-5670-43f0-ad39-ef7eaddeb6a5'

params = {'documentType': 'A68',
          'processType': 'A33',
          'in_Domain': '10YAT-APG------L',
          'securityToken': tok,
          'periodStart': start,
          'periodEnd': end}
url = 'https://transparency.entsoe.eu/api'

response = requests.get(url, params=params)
data = response.text
result = parse_generation(data)


