# STREAM WATER TEMPERATURE FORECASTING FUNCTIONS
# Bill Hoblitzell, bill@lotichydrological.com,
# Last modified 8/28/2021

"""
    These functions are called from the main temperature program. They use current stream and
    weather info to make a prediction of stream temperatures using a generalized additive model
    developed each stream reach that has adequate datasets available.

    The general workflow is:
    - get current discharge from gauge sites
    - get the minimum water temperature from gauge sites from this morning (since midnight)
    - get today's julian date
    - pack these into a dataframe and send it to the prediction model to return a water temp prediction
    - create a dictionary with the stream forecast information and send it back to the main program
      to use in building a forecast table for the email alerts.
"""

###############################################################################
# REQUIREMENTS
###############################################################################

# Python system packages
import numpy as np
import pandas as pd
from datetime import datetime as dt
import pickle

# Local modules
import hourly_weather
import usgs_calls

###############################################################################
# FORECAST FUNCTIONS
###############################################################################


def build_prediction_dataset(params, air_fx):
    """
    Package the parameters needed for the water temperature prediction model into.
    Accepts a dictionary of parameters and returns a single row dataframe.    a
    """
    print("building prediction dataset")
    data = pd.DataFrame({
        'ta_f': air_fx["temps"],
        'tw_min': params['tw_min_wolcott'],
        'q_mean': params['q_gypsum'],
        'doy': params['doy']
    })
    return data


def predict_temps(pred_data, model_name):
    """
    Load a pre-built GAM model for a stream location and feed it the prediction data.
    Requires a dataframe of prediction data and the appropriate GAM model name for
    a given river reach.
    Returns the predicted high stream temperature of the day for the site.
    """
    print(f"Predicting temps with model {model_name}")
    try:
        # load gam model
        file_name = f"./gam_models/{model_name}"
        with open(file_name, 'rb') as model_file:
            gam = pickle.load(model_file)
        # feed it the prediction dataset
        x_data = pred_data.values
        predicted_temp_f = gam.predict(x_data)
        # ci_95 = gam.confidence_intervals(x_data)
        # print(f"95% confidence interval is: {ci_95}")
        # format the results and append to the prediction dataframe
        # pred_data["tw_max_f.predicted"] = pred_temps_f
        # pred_data["tw_max_f.predicted"] = pred_data["tw_max_f.predicted"].round()
        # pred_data["tw_max_f.ci95_upper"] = ci_95[0][1].round(1)
        # pred_data["tw_max_f.ci95_lower"] = ci_95[0][0].round(1)
        # return a dictionary of prediction results
        return predicted_temp_f[0].round()
    except Exception as error:
        print("Model prediction was unsuccessful")
        print(error)
        raise


# THIS FUNCTION IS FROM THE ORIGINAL TEXT EMAILS AND IS DEPRECATED FOR THE TIME BEING UNTIL
# THE CREATION/FORMATTING FUNCTIONS FOR THOSE EMAILS ARE UPDATED BH 8/26/2021
# def identify_daily_concerns(temp_pred):
#     """
#     Review water temperature forecast data to determine when and if temperatures will reach either 'Concern' risk
#     levels or 'High' risk levels for fishing and report the time of day and a narrative outreach message.
#     """
#
#     danger_level_time = None
#     concern_level_time = None
#     for index, row in temp_pred.iterrows():
#         print(row["tw_max_f.predicted"])
#         if row["tw_max_f.predicted"] > 70:
#             print(f"temp at {row['time']}  is {row['tw_max_f.predicted']}")
#             danger_level_time = row["time"]
#             break
#             # return {'concern_time': concern_level_time, 'danger_time': danger_level_time}
#         if row["tw_max_f.predicted"] > 65:
#             print(f"Concern: temp at {row['time']}  is {row['tw_max_f.predicted']}")
#             if concern_level_time is not None:
#                 concern_level_time = min(row["time"], concern_level_time)
#             else:
#                 concern_level_time = row["time"]
#
#     print(concern_level_time)
#     print(danger_level_time)
#
#     if (concern_level_time is None) & (danger_level_time is not None):
#         warning_message = f"Water temperatures are expected to exceed 'High' risk levels (> 70 F) for fish by around {danger_level_time}."
#     if (concern_level_time is None) & (danger_level_time is None):
#         warning_message = f"Water temperatures are not expected to meet 'Concern' or 'High' risk levels today. " \
#                           f"Monitor your local venue for unexpectedly warm conditions."
#     if (concern_level_time is not None) & (danger_level_time is None):
#         warning_message = f"Water temperatures are expected to reach 'Concern' risk levels (65-70 F) by around {concern_level_time}."
#     if (concern_level_time is not None) & (danger_level_time is not None):
#         warning_message = f"Water temperatures are expected to reach 'Concern' risk levels (65-70 F) by around {concern_level_time} " \
#                           f"and exceed 'High' risk levels (> 70 F) for fish around {danger_level_time}."
#
#     return warning_message


def get_risk_level(temp):
    """
    Return a narrative risk level rating based on an integer temperature value input.
    """
    if temp >= 71:
        risk = "High"
    if (temp > 65) & (temp < 71):
        risk = "Concern"
    if temp <= 65:
        risk = "Low"
    print(f"The assessed water temp risk for {temp} F is: {risk}")
    return risk


def load_site_config_file():
    """
    Load the site configuration file. This .csv file contains various data
    about each temperature prediction reach including the usgs gauge name for getting streamflow
    and current water temperature data.
    """
    return pd.read_csv("./program_files/weather_fx_sites.csv",
                       header=1, dtype={'flow_gauge': str, 'temp_gauge': str,})


def fix_site_id(site_no):
    """
    Read in a USGS site number, convert it to a string, and re-append the '0' in front of
    any of the sites in our area (Upper Colorado River Basin) that are prefixed with '09....'
    If .csv files are viewed or manipulated in Excel, USGS site names are often interpreted
    as numbers the preceeding '0' is removed, causing errors later when trying to call the site.
    """
    site_str = str(site_no)
    if site_str[0] == '9':  # fix local Colorado/Eagle basin USGS site names that get truncated by excel
        site_str = f"0{site_str}"
    return site_str


#################################################################################################
# PROGRAM CONTROL FUNCTION
###############################################################################


def forecast_stream_temperature():
    """
    Create a list of dictionaries for each stream temperature forecasting reach. Return the
    list to be used in creating an HTML table in email alerts.
    """
    prediction_sites = load_site_config_file()
    zone_forecasts = []
    proceed = True
    for index, site_data in prediction_sites.iterrows():
        print("************************************************************************")
        print(f"\nAssessing {site_data['zone']}\n")
        # get the flow and temperature data since midnight
        print('getting flow data')
        flow_data = usgs_calls.get_site_data(site=fix_site_id(site_data["flow_gauge"]), param='00060')
        print('getting temperature data')
        temp_data = usgs_calls.get_site_data(site=fix_site_id(site_data["temp_gauge"]), param='00010')

        # If both temperature and flow data is available, unpack it and get the relevant values
        # for the prediction model, otherwise go to next site in the loop.
        if (flow_data is not None) and (temp_data is not None):
            
            # # TODO: These functions break for timeseries around midnight, (which is okay, the program isn't called at those times), but could use some work

            # Get most recent streamflow
            timeseries = flow_data["value"]["timeSeries"]
            if len(timeseries) > 0:
                flow_ts = usgs_calls.extract_hourly_data(timeseries)
                print(flow_ts.tail())
                current_flow = usgs_calls.get_most_recent_value(flow_ts)
                print(f"Current flow at {site_data['flow_gauge']} is {current_flow}")
            else:
                current_flow = np.nan
                proceed = False

            # Get this morning's minimum temperature (Minimum since midnight up until now)
            timeseries = temp_data["value"]["timeSeries"]
            if len(timeseries) > 0:
                temp_ts = usgs_calls.extract_hourly_data(timeseries)
                am_tw_min_temp = usgs_calls.get_morning_minimum(temp_ts)
                current_temp = usgs_calls.get_most_recent_value(temp_ts)
            else:
                am_tw_min_temp = np.nan
                current_temp = np.nan
                proceed = False

        else:
            print("Flow and temperature retrieval unsuccessful, site will not be assessed.")
            proceed = False
            # continue

        # get the next day of hourly weather forecasts, including air temperature and sky cover
        print(f"-------------------------------------------------")
        print(f"Getting hourly weather for {site_data['zone']}...")
        hourly_air_fx = hourly_weather.get_hourly_fx(lat=site_data["lat"], lon=site_data["lon"])

        # If weather data is successfully returned from the api, unpack it and get the predicted temperature
        # at noon and the predicted maximum temperature for the day
        if hourly_air_fx is not None:
            try:
                max_air_temp = np.nanmax(hourly_air_fx["temps"])
                afternoon_sky = hourly_air_fx["weather"][hourly_air_fx["hour"] == 15].values[0]
                print(f"Max air temp: {max_air_temp}, pm sky: {afternoon_sky}")
                print(f"-------------------------------------------------")
            except Exception as error:
                print(f"No current air forecast available for {site_data['zone']}, site will not be assessed.")
                print(f"-------------------------------------------------")
                print(error)
                proceed=False
        else:
            proceed = False

        # Just to help with development/debugging...
        if proceed:
            print(f"Proceed status is: {proceed}, predicting water temperature for reach.")
        else:
            print(f"Proceed status is: {proceed}, no prediction can be made, attempting next site.")

        # If there is USGS data present (flow, water temp) and weather data (predicted air temp) present,
        # load the model for that river section and send it these data points to make a water temperature
        # prediction for noon and for the hottest portion of the day.
        # TODO: this function has gotten way too long, consider breaking up into 3(?) parts as well as moving the try/except blocks to inside of their respective function calls

        if proceed:
            prediction_data = {
                "ta_max": [max_air_temp],
                "tw_min": [am_tw_min_temp],
                "q_mean": [current_flow],
                "doy": [dt.now().timetuple().tm_yday]
            }
            print(f"Prediction dataset:   {prediction_data}")

            # cast it to a dataframe for feeding to the pygam model
            pred_data_max = pd.DataFrame(prediction_data)

            # send to pygam model to get a water temperature prediction
            try:
                high_temp = predict_temps(pred_data=pred_data_max, model_name=site_data["model_name"])
                print(f"Predicted high water temp is {high_temp}")
            except Exception as error:
                print(error)
                raise

            # assign the predicted risk level
            pm_risk = get_risk_level(high_temp)

            # Pack everything into a dictionary then append it to the list of prediction dictionaries
            zone_info = {
                "zone": site_data["zone"],
                "current_temp": current_temp,
                "max_temp": int(high_temp),
                "pm_risk": pm_risk,
                "pm_air_temp": int(max_air_temp),
                "pm_weather": afternoon_sky
            }
            print("------------------------------------------------------------------------")
            print("Returning zone data:")
            print(f"{zone_info['zone']}")
            print(zone_info)
            print("------------------------------------------------------------------------\n")
            print("************************************************************************")
            zone_forecasts.append(zone_info)

    print("\nAll sites assessed, returning any data found:")

    if zone_forecasts is not None:
        return zone_forecasts
    else:
        return None


#################################################################################
# USE BELOW ONLY FOR DEVELOPMENT/TESTING THESE FUNCTIONS

# This line will be inserted in main.py as stream_forecast.forecast_stream_temperature() and will return
# an html string that builds a forecast table to be put into the morning email.
# fx_data = forecast_stream_temperature()
# for item in fx_data:
#     print(item)
#
# # Dump the html to a file for viewing the table in the browser
# with open('fx_html.html', 'w') as f:
#     f.write(f"<html><body>{fx_table_html}</html></body>")
# print(fx_table_html)
