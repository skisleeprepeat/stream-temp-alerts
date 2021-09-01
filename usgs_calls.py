"""
Collection of functions to call-for, extract, and manipulate data from USGS webservices.
Bill Hoblitzell bill@lotichydrological.com 6/24/2021
"""

###############################################################################
# REQUIREMENTS
###############################################################################

import requests
from datetime import datetime as dt
import dataretrieval.nwis as nwis
import pandas as pd
import numpy as np

###############################################################################
# FUNCTIONS
###############################################################################

def get_site_data(site, param, period='P1D'):
    """
    Use a USGS numeric site code and a USGS parameter code to retrieve site data
    for the last 24 hours. Return the webservice response as a json object
    (json object = python dictionary).
    """
    url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={site}" \
          f"&parameterCd={param}&siteStatus=all&period={period}"
    print(f"Querying USGS webservice at: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print("Response successful")
        return response.json()
    except requests.exceptions.RequestException as err:
        print(err)
        print("response unsuccessful, returning 'None'")


def extract_hourly_data(timeseries):
    """
    Accept the 'timeseries' subset of data from the full USGS json response object.
    This part of the data contains the last 24 hours of instantaneous value  (iv) gauge data
    and extract the observations then return them as a time series dataframe
    with two columns:
    col 1) datetime (dtype datetime)
    col 2) [parameter name] ...(should be either 'temp_c' or 'q' (dtype int)
    """
    try:
        print("\nExtracting USGS gauge timeseries data from json")
        param = timeseries[0]["variable"]["variableCode"][0]["value"]
        if param == "00010":
            param = "temp_c"
        if param == "00060":
            param = "q"
        print(f"Parameter is: {param}\n")
        # Sometime a parameter was formerly collected at a station but no longer is,
        # check to make sure there is data in the 'timeseries>values>value slot
        if len(timeseries[0]["values"][0]["value"]) > 0:
            var_ts = []
            datetime_ts = []
            observations = timeseries[0]["values"][0]["value"]
            for obs in observations:
                var_ts.append(float(obs["value"]))
                datetime_formatted = dt.strptime(obs["dateTime"], '%Y-%m-%dT%H:%M:%S.%f%z')
                datetime_ts.append(datetime_formatted)
            df = pd.DataFrame(list(zip(datetime_ts, var_ts)), columns=["dateTime", param])
            print(f"Returning timeseries dataframe for {param}\n")
            return df
        else:
            return None
    except Exception as err:
        print(err)
        raise


def get_morning_minimum(ts):
    """
    Filter the timseries dataframe for just values since midnight then find the minimum value and convert
    from C to F
    """
    # Filter the dataframe for just the values since midnight
    today = dt.now().date().today()
    today_df = ts.loc[(ts["dateTime"].dt.date == today)]
    print(today_df.head(n=5))
    # Find the minimum temperature from this morning and convert from C to F)
    tw_min_c = np.nanmin(today_df.iloc[:, 1])
    min_row = today_df[today_df.iloc[:, 1] == tw_min_c]
    print(f"Minimum temperature readings from this morning's data call:\n{min_row}")
    tw_min = round(tw_min_c * (9 / 5) + 32)
    print(f"The minimum temp value since midnight is {tw_min_c} C / {tw_min} F.\n")
    return tw_min


def get_most_recent_value(ts):
    """
    Return the most recent value from the timeseries dataframe.
    """
    print(ts.head())
    # Find the current water temperature
    today = dt.now().date().today()
    today_df = ts.loc[(ts["dateTime"].dt.date == today)]
    most_recent_temp = today_df.iloc[len(today_df) - 1][1]
    most_recent_time = today_df.iloc[len(today_df) - 1][0]
    print(f"Most recent value is {most_recent_temp} at {most_recent_time}.\n")
    tw_curr = round(most_recent_temp * (9 / 5) + 32)
    return tw_curr


def get_q_median(site):
    """
    Use the USGS dataretrieval package to return the 50th percentile (median) flow for this date in the POR
    """
    param = '00060'
    print(f"Getting median flows for {site}")
    try:
        q_stats, md = nwis.get_stats(sites=site, parameterCd=param, statReportType='daily', statTypeCd='p50')
        # extract the median flow for today's date
        current_month = dt.today().month
        current_day = dt.today().day
        median_flow = int(q_stats.loc[(q_stats['month_nu'] == current_month) & (q_stats['day_nu'] == current_day), 'p50_va'])
        return median_flow
    except Exception as err:
        print(err)
        return None


def calc_historical_flow_stat(site_data_list):
    """
    Call the USGS gauge site to get the median flows for the recent POR and
    determine the current discharge values as a percentage of the historic median.
    Appends this statistic directlhy to the site information dictionary.
    """
    for site_info in site_data_list:
        # if there is discharge at the site, make the api call, otherwise fill the
        # dictionary slot with 'no rating'
        if np.isnan(site_info['yesterday_mean_q']):
            site_info['percent_of_median'] = '---'
        else:
            q_median = get_q_median(site_info['site'])
            if q_median is not None:
                q_perc_median = round((site_info['yesterday_mean_q'] / q_median) * 100)
            else:
                q_perc_median = '---'
            print(f"Percent of median is: {q_perc_median}")
            site_info['percent_of_median'] = q_perc_median


#
