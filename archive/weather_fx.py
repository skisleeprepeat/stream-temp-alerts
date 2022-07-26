"""
Collection of functions to call NOAA and get the local weather forecast.
Bill Hoblitzell 6/24/2021
"""

# Requirements
import requests


def get_noaa_grid_endpoints(coords):
    url = f"https://api.weather.gov/points/{coords[0]},{coords[1]}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(err)


def get_noaa_fx(office, grid_X, grid_Y):

    url = f"https://api.weather.gov/gridpoints/{office}/{grid_X},{grid_Y}/forecast"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(err)


def get_loc_fx(location):

    # get the NOAA grid number
    fx_grid = get_noaa_grid_endpoints([location[1], location[2]])
    loc_x = fx_grid["properties"]["gridX"]
    loc_y = fx_grid["properties"]["gridY"]
    loc_office = fx_grid["properties"]["gridId"]

    # get the forecast for the grid and return it as a dictionary
    fx = get_noaa_fx(office=loc_office, grid_X=loc_x, grid_Y=loc_y)
    today_fx = fx["properties"]["periods"][0]
    fx_dict = {
        "location":location[0],
        "high": today_fx['temperature'],
        "desc": today_fx['shortForecast']
    }
    return fx_dict


def build_fx_table(locations):
    table_header = f"<tr><td style='text-align:center'><strong>Zone</strong></td><td style='border: 1px solid;'><strong>High Air Temp</strong></td><td style='font-face:bold; text-align:center'><strong>Forecast</strong></td></tr>"
    inner_table = ""
    for location in locations:
        fx_items = get_loc_fx(location)
        table_row = f"<tr style='border: 1px solid;'><td>{fx_items['location']}</td><td style='text-align:center; border: 1px solid;'>{fx_items['high']}</td><td>{fx_items['desc']}</td></tr>"
        inner_table = inner_table + table_row
    fx_table = f"<h3>Zone weather forecasts</h3><table cellpadding='3' style='border: 1px solid; border-collapse:collapse;'>{table_header}{inner_table}</table><br>"
    return fx_table

#################################################################################################
# testing

# Locations are currently hard-coded into the 'build_email' function 'build_html_email_message()'
# locations = [
#     ["Statebridge/Upper Colorado Region", "39.874807", "-106.687783"],
#     ["Lower Eagle/Colorado R @ Dotsero", "39.650938", "-106.942805"],
#     ["Basalt/Lower Roaring Fork Valley", "39.413287", "-107.215794"]
# ]

# fx_html = build_fx_table(locations)

# Dump the html to a file for viewing the table in the browser
# with open('fx_html.html', 'w') as f:
#     f.write(f"<html><body>{fx_html}</html></body>")








#





