"""
Get an hourly temperature forecast from Openweathermap.org and return it as an
list to be used in the stream temperature prediction model
"""
import os
import requests
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
OW_API_KEY = os.getenv('OW_API_KEY')


LOWER_EAGLE_COORDS = ["39.651101", "-106.943897"]  # gypsum ponds/gypsum
SB_UPPER_C_COORDS = ["39.856671", "-106.650389"]
BASALT_RF_COORDS = ["39.413287", "-107.215794"]

#------------------------------------------------------------------------------

def get_ow_fx(lat, lon, api_key=OW_API_KEY ):
        '''
        Use the lat/lon pairs and api key to call the OW API.
        Return a json object.
        '''
        ow_api_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=imperial&exclude=minutely&appid={api_key}"
        print(f"Querying Openweathermap at forecast url:\n{ow_api_url}")
        try:
            response = requests.get(ow_api_url, timeout=30)
            print(f"Response status:  {response.status_code}")
            print(response.raise_for_status())
            # print(response.json())
            return response.json()
        except requests.exceptions.RequestException as err:
            print("Query unsuccessful, returning None")
            print(err)


def unpack_fx_data(forecast):
    """
    Unpack the json object returned from Openweather API, reformat and return the next 24 hours
    of temperatures and weather descriptions as a timeseries dataframe.
    """
    print("Unpacking forecast data")
    if forecast is not None:
        times = []
        temps = []
        weather = []
        for hourly_dict in forecast["hourly"][:12]:
            print(hourly_dict)
            # make a correction on the UTC datetime of 6 hours for Mountain Daylight Time
            fx_datetime = dt.utcfromtimestamp(int(hourly_dict["dt"])) - timedelta(hours=6)
            # times.append(fx_datetime.hour)
            times.append(fx_datetime)
            temps.append(round(hourly_dict["temp"], 1))
            weather.append(hourly_dict["weather"][0]["description"])
            fx_dataframe = pd.DataFrame({"dateTime": times, "temps": temps, "weather": weather})
            # fx_dataframe["hour"] = fx_dataframe["dateTime"].dt.strftime("%I:%M %p")
            fx_dataframe["hour"] = fx_dataframe["dateTime"].dt.hour
        print("Unpacking weather data was successful")
        # print(fx_dataframe.head(n=12))
        return fx_dataframe
    else:
        print("Unpacking weather fx unsuccessful, returning 'None'")
        return None


def get_hourly_fx(lat=LOWER_EAGLE_COORDS[0], lon=LOWER_EAGLE_COORDS[1]):

    '''
    Get an hourly weather forecast from Open Weather using lat/lon pairs.
    Return the forecast as a dataframe.
    '''

    print("Collecting hourly forecast for zone")
    try:
        fx = get_ow_fx(lat=lat, lon=lon, api_key=OW_API_KEY)
        weather_fx_df = unpack_fx_data(fx)
        # print(weather_fx_df.head())
        return weather_fx_df
    except:
        print("Unsuccessful weather forecast call")
        raise

# Testing...
# air_data = get_hourly_fx()
# print(air_data.head(n=12))
#
# print(air_data["temps"][air_data["dateTime"].dt.hour.isin([0,12])])
# print(air_data["temps"][(air_data["dateTime"].dt.hour == 0)])

#
# print(air_data[(air_data["dateTime"].dt.hour == 26)])
# print(noon_temp)
# print(air_data)
