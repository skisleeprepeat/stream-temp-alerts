###############################################################################
# Requirements
###############################################################################

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

## TODO: remove unnecessary imports

###############################################################################
# Constants for html table formatting
###############################################################################

# Risk Level colors
risk_colors = {
    "green": "#32CD32",
    "yellow": "yellow",
    "red": "red"
}

# discharge colors based on USGS coloring scheme
q_colors = {
    "orange": "#f3a711",
    "yellow": "yellow",
    "green": "#32CD32",
    "light-blue-green": "#00f4ef",
    "blue": "#1870d5"
}


##############################################################################
# Mailing functions
###############################################################################

# Testing dictionary with example key/value pairs
# {'site': '09064600', 'yesterday_mean_q': 57, 'yesterday_max_t': nan, 'alias': 'Upper Eagle River, Minturn Area', 'risk': '<no rating>', 'percent_of_median': 76}


def build_yesterday_conditions_table(site_data_list):

    """
    Create a color-coded html table element of temperatures, flows, and fish risk rating from
    the previous afternoon gauge site readings. Accepts a list of dictionaries that have
    site information (name, risk level, etc.).  Loops through the list and uses them
    to build an html table that is inserted into a longer html that forms the email body.
    Return this string of html to use in the update email.
    """

    table_header_str = "<tr>" \
                       "<th style='text-align:center; border-bottom: solid 1px;'><strong>Location</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:100px; border-bottom: solid 1px; border-left: 1px solid; '><strong>Yesterday High Water Temp &#176;F</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:150px; border-bottom: solid 1px;'><strong>Yesterday PM Fishing Risk</strong></th>" \
                       "<th style='text-align:center; border-bottom: solid 1px; border-left: 1px solid'><strong>Streamflow (cfs)</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:120px;border-bottom: solid 1px;'><strong>Percent of Median Flow for this Date<strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:150px;border-bottom: solid 1px;'><strong>Seasonal Flow Conditions Rating<strong></th>" \
                       "</tr>"

    all_rows_str = ""
    for site_info in site_data_list:
        print(f"site_info: {site_info}")
        # assign css cell colors for temperature risk
        if site_info['t_risk'] == "LOW":
            risk_col = risk_colors["green"]
        elif site_info['t_risk'] == "CONCERN":
            risk_col = risk_colors["yellow"]
        elif site_info['t_risk'] == "HIGH":
            risk_col = risk_colors["red"]
        else:
            risk_col = "white"

        # assign css colors for flow conditions
        q_rating = site_info['q_rating']

        if q_rating == "Low":
            q_col = q_colors["orange"]
        elif q_rating == "Below Normal":
            q_col = q_colors["yellow"]
        elif q_rating == "Normal":
            q_col = q_colors["green"]
        elif q_rating == "Above Normal":
            q_col = q_colors["light-blue-green"]
        elif q_rating == "High":
            q_col = q_colors["blue"]
        else:
            q_col = "white"

        row_str = f"<tr>" \
                  f"<td style='font-size:0.9rem; '>{site_info['alias']}</td>" \
                  f"<td style='text-align:center; border-left: 1px solid; background-color:{risk_col};'>{site_info['yesterday_max_t']}</td>" \
                  f"<td style='text-align:center; font-weight: bold; background-color:{risk_col};'>{site_info['t_risk']}</td>" \
                  f"<td style='text-align:center; color:DarkBlue; border-left: 1px solid; '>{site_info['yesterday_mean_q']}</td>" \
                  f"<td style='text-align:center; color:DarkBlue;'>{site_info['percent_of_median']} %</td>" \
                  f"<td style='text-align:center; background-color:{q_col}'><strong>{site_info['q_rating'].upper()}</strong></td>" \
                  f"</tr>"
        all_rows_str = all_rows_str + row_str

    full_table_str = f"<div><hr><nbsp><h3>Yesterday's <em>OBSERVED</em> Stream Temperature and Flow Conditions</h3>" \
                     f"<table cellspacing='0' cellpadding='3' style='border: 1px solid black;'>" \
                     f"{table_header_str}{all_rows_str}</table></div>" \
                     f"<p style='text-align:center; font-size:90%;'>This data service is made possible by real-time stream monitoring " \
                     f"sites operated by the " \
                     f"<a href='https://www.usgs.gov/centers/co-water/' target='_blank'>US Geological Survey</a> and the " \
                     f"<a href='https://www.coloradoriverdistrict.org' target='_blank'>Colorado River District</a>, " \
                     f"with public funding from national, state, and local partners like " \
                     f"<a href='https://www.erwc.org' target='_blank'>Eagle River Watershed Council</a>, " \
                     f"<a href='https://www.erwsd.org' target='_blank'>Eagle River Water and Sanitation District</a>," \
                     f" and <a href='https://www.eaglecounty.us' target='_blank'>Eagle County Government</a>.</p><br>"
    return full_table_str


def build_forecast_table(zone_list):
    table_header_str = "<tr>" \
                       "<th style='text-align:center; border-bottom: solid 1px; '><strong>River Zone</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:120px; border-bottom: solid 1px; border-left: 1px solid;'><strong>Current Morning Water Temp &#176;F</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:150px; word-wrap: break-word; max-width: 150px; border-bottom: solid 1px; border-left: 1px solid;'><strong>Afternoon Predicted High Water Temp &#176;F</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:150px; border-bottom: solid 1px;'><strong>Afternoon Predicted Fishing Risk</strong></th>" \
                       "<th style='text-align:center; word-wrap:break-word; max-width:130px; border-bottom: solid 1px; border-left: 1px solid; '><strong>Predicted High Air Temp &#176;F</strong></th>" \
                       "<th style='text-align:center; border-bottom: solid 1px;  word-wrap:break-word; '><strong>PM Weather</strong></th>" \
                       "</tr>"
    all_rows_str = ""
    if len(zone_list) > 0:
        for item in zone_list:
            print(item)
            if item['pm_risk'] == "Low":
                pm_risk_col = risk_colors["green"]
            elif item['pm_risk'] == "Concern":
                pm_risk_col = risk_colors["yellow"]
            elif item['pm_risk'] == "High":
                pm_risk_col = risk_colors["red"]
            else:
                pm_risk_col = "white"

            row_str = f"<tr>" \
                      f"<td style='font-size:0.9rem; '>{item['zone']}</td>" \
                      f"<td style='text-align:center; border-left: 1px solid; '>{item['current_temp']}</td>" \
                      f"<td style='text-align:center; border-left: 1px solid; background-color:{pm_risk_col} '>{item['max_temp']}</td>" \
                      f"<td style='text-align:center; font-weight: bold; background-color:{pm_risk_col}'>{item['pm_risk'].upper()}</td>" \
                      f"<td style='text-align:center; border-left: 1px solid'>{item['pm_air_temp']}</td>" \
                      f"<td><em>{item['pm_weather'].title()}</em></td>" \
                      f"</tr>"
            all_rows_str = all_rows_str + row_str

        full_table_str = f"<div><hr><nbsp><h3>Today's <em>PREDICTED</em> Water Temperature and Weather Forecast</h3>" \
                         f"<table cellspacing='0' cellpadding='3' style='border: 1px solid black;'>" \
                         f"{table_header_str}{all_rows_str}</table></div>" \
                         f"<p style='text-align:center; font-size:90%;'>" \
                         f"Water temperature predictions are made " \
                         f"using a predictive model developed by " \
                         f"<a href='https://www.lotichydrological.com'>Lotic Hydrological</a>" \
                         f" for streams in the ERWC service area. Specific stream reaches may be warmer or " \
                         f"cooler than those predicted here based on local factors like habitat, topography, and " \
                         f"changing weather; always directly check conditions at your location.</p><br>"
        return full_table_str
    else:
        return None


def build_html_email_message(conditions, forecast):

    """  Create an html email body with the risk ratings for each site, tips on warm water fishing, and information
    about the Eagle River Watershed Council. Return the message body as a long string"""

    print("\nBuilding html email message.")

    update_time = f"{datetime.now().strftime('%A')}, " \
                  f"{datetime.now().strftime('%B')} " \
                  f"{datetime.now().strftime('%d')} at " \
                  f"{datetime.now().strftime('%H:%M')}"

    # read in the header
    with open(f"email_templates/header.html") as template:
        contents = template.read()
        header_html = contents.replace('[update_time]', update_time)

    # make the table of current conditions
    yesterday_table_html = conditions
    # make the afternoon forecast table
    fx_table_html = forecast

    # read in the rest of the email body... the risk key and the footer
    with open("email_templates/risk_key_and_footer.html") as template:
        contents = template.read()
    contents = contents.replace('[risk_green]', risk_colors["green"])
    contents = contents.replace('[risk_yellow]', risk_colors["yellow"])
    contents = contents.replace('[risk_red]', risk_colors["red"])
    risk_key_and_footer = contents
    # put all the parts together
    email_html = header_html + fx_table_html + yesterday_table_html + risk_key_and_footer

    # Dump the html to a file for inspection (development only, comment out during deployment)
    # with open('dev_outputs/view_email_html.html', 'w') as f:
    #     f.write(f"<html><body>{email_html}</html></body>")

    # return a long html string
    return email_html


def build_text_email_message(sites_data):

    """Create a text email body with the risk ratings for each site, tips on warm water fishing, and information
    about the Eagle River Watershed Council. Return the message body as a long string"""

    print("Building text email message.")

    # unpack site lists and build the body header
    full_summary = ""
    for site_data in sites_data:
        site_name = site_data[0]
        site_obs_time = site_data[2]
        site_temp = site_data[3]
        site_msg = site_data[6]
        reach_summary = f"\n----  {site_data[5].upper()}  ----\n\n" \
                        f"The most recent reading for {site_name} was {site_temp} F, at {site_obs_time}.\n" \
                        f"{site_msg}\n\n"
        full_summary = full_summary + reach_summary

    # paste together the body header (site summaries) with message footer
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    with open("email_templates/header.txt") as txt_file:
        message_header = txt_file.read()
    message_header.replace('[current_time]', current_time)

    with open("email_templates/footer.txt") as txt_file:
        message_footer = txt_file.read()

    message_body = message_header + full_summary + message_footer
    # print(message_body)
    return message_body

#
