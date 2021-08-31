# AUTOMATED WATER TEMPERATURE ALERT PROGRAM

"""
This program uses USGS webservices to call temperature data from gauges
on the Eagle and Colorado River, assess the temperatures against cold-
water fishery risk levels, and utilize email and social media portals to
issue alerts for area anglers.
"""

# Author: Bill Hoblitzell/Lotic Hydrological 6/14/2021
# Contact: bill@lotichydrological.com, www.lotichydrological.com
# Modified: 6/16/2021
# Status: Prototype/testing
# Copyright: Lotic Hydrological
# Version 1.0


###############################################################################
# REQUIREMENTS
###############################################################################

# python system modules and packages
import os
import sys
import numpy as np
from dotenv import load_dotenv
from time import sleep
from datetime import datetime

# local modules
import build_email
import mail_chimp_functions as mc
import usgs_calls
import water_forecasts

# Active during testing only, comment out otherwise
# Note; may need re-enable 'Allow less secure apps' in Google account security if testing has not been used in awhile
import email_tests


###############################################################################
# CONFIG
###############################################################################
# TODO: How to hide environmental variables in Python Anywhere scripts, dotenv...
# https://towardsdatascience.com/using-dotenv-to-hide-sensitive-information-in-python-77ab9dfdaac8

load_dotenv()
MC_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MC_SERVER_PREFIX = os.getenv('MAILCHIMP_SERVER_PREFIX')
ERWC_LIST = os.getenv('MAILCHIMP_ERWC_LIST')
ALERT_TAG = os.getenv('MAILCHIMP_ALERT_TAG')
ALERT_SEGMENT_ID = os.getenv('MAILCHIMP_ALERT_SEGMENT_ID')
ALERT_TEST_SEGMENT_ID = os.getenv('MAILCHIMP_ALERT_TEST_SEGMENT_ID')
REPLY_TO_EMAIL = os.getenv('REPLY_TO_EMAIL')

# reply-to email
# reply_to = 'alerts@erwc.org'
# my_email = 'billhoblitzell80@gmail.com'
# my_password = 'NewRiverGorge4500'
# to_email = ['billhoblitzell@yahoo.com', 'bill@lotichydrological.com']


###############################################################################
# MAIN PROGRAM FUNCTIONS
###############################################################################


def gather_site_data(sites):

    """ Aggregate the available flow and temp data for all the gauge sites.
    Return a list containing a data dictionary for each of the sites"""

    site_data_list = []
    for site in sites:
        print(f"\nGathering data for site {site} ----------------->\n")
        # Make calls to USGS webservice to get last 24 hours of instantaneous (15 min) values)
        flow_data = usgs_calls.get_site_data(site, param="00060", period="P1D")
        temp_data = usgs_calls.get_site_data(site, param="00010", period="P1D")

        # If data is returned for both calls, unpack it and get yesterday's flow and max temp
        if flow_data is None and temp_data is None:
            continue
        else:
            # Get the mean flow from yesterday
            if flow_data is not None:
                timeseries = flow_data["value"]["timeSeries"]
                if len(timeseries) > 0:
                    flow_ts = usgs_calls.extract_hourly_data(timeseries)
                    if flow_ts is not None:
                        # print(flow_ts.head())
                        mean_flow_yesterday = int(np.nanmean(flow_ts['q']))
                    else:
                        mean_flow_yesterday = np.nan
                else:
                    mean_flow_yesterday = np.nan
            # Get the maximum water temperature from yesterday
            if temp_data is not None:
                timeseries = temp_data["value"]["timeSeries"]
                if len(timeseries) > 0:
                    temp_ts = usgs_calls.extract_hourly_data(timeseries)
                    if temp_ts is not None:
                        # print(temp_ts.head())
                        max_temp_yesterday = int(np.nanmax(temp_ts['temp_c']) * (9/5) + 32)
                    else:
                        max_temp_yesterday = np.nan
                else:
                    max_temp_yesterday = np.nan
            # Pack everything into a dictionary and append to the site data list
            site_data = {'site': site, 'yesterday_mean_q': mean_flow_yesterday, 'yesterday_max_t': max_temp_yesterday}
            site_data_list.append(site_data)
    return site_data_list


def assign_river_reach(site_data_list):

    """Append the local nicknames for stream reaches associated with different temperature monitoring sites
    to the site's information list"""

    for site_info in site_data_list:
        site_id = site_info['site']
        if site_id == "09060799":
            alias = 'Colorado River @ Catamount'
        elif site_id == "09058000":
            alias = 'Colorado River @ Gore Canyon'
        elif site_id == "09070000":
            alias = 'Lower Eagle River @ Gypsum'
        elif site_id == "394220106431500":
            alias = 'Middle Eagle River @ Red Canyon'
        elif site_id == "09066510":
            alias = 'Lower Gore Creek @ Mouth'
        elif site_id == "09071750":
            alias = 'Colorado River @ No Name'
        elif site_id == "09070500":
            alias = 'Colorado River @ Dotsero'
        elif site_id == "09085000":
            alias = 'Lower Roaring Fork River @ GWS'
        elif site_id == "09064600":
            alias = 'Upper Eagle River @ Minturn'
        else:
            alias = site_id  # just assign the gauge name if no reach nickname is found
        site_info["alias"] = alias
    # Function returns nothing, dictionaries are mutable and are updated in the global scope


def evaluate_temp_risk(site_data_list):

    """ Using the max temperature, assign a narrative ordinal rating for fishing risk at the site. Append the
     rating to that site's information dictionary"""

    for site_info in site_data_list:
        # if there is no data in this slot (gauge has discharge only), replace it with a blank string, skip to next site
        if np.isnan(site_info['yesterday_max_t']):
            site_info["t_risk"] = "<em>no rating</em>"
            site_info['yesterday_max_t'] = '---'
        else:
            temp = float(site_info['yesterday_max_t'])
            risk = '<em>no rating</em>'
            if temp < 65:
                risk = "LOW"
            elif 65 <= temp < 71:
                risk = "CONCERN"
            elif temp >= 71:
                risk = "HIGH"
            print(f"Evaluating temperature for fishing risk level at {site_info['site']}, current temp is {temp}, "
                  f"risk is {risk}.")
            site_info["t_risk"] = risk


def evaluate_flow_conditions(site_data_list):
    """ Using the Percent of Median Flow value, assign a narrative ordinal rating for fishing risk at the site.
    Append the rating to that site's information dictionary.
    """
    for site_info in site_data_list:
        # if there is no data in this slot (gauge has discharge only), skip to next site
        print(f"Perc of Med: {site_info['percent_of_median']}")
        # if np.isnan(site_info['percent_of_median']):
        if site_info['percent_of_median'] == '---':
            site_info["q_rating"] = "---"
            site_info['yesterday_mean_q'] = "---"
        else:
            q_percent = float(site_info['percent_of_median'])
            q_rating = '<em>no rating</em>'
            if q_percent < 50:
                q_rating = "Low"
            elif 50 <= q_percent < 80:
                q_rating = "Below Normal"
            elif 80 <= q_percent <= 120:
                q_rating = "Normal"
            elif 120 < q_percent <= 150:
                q_rating = "Above Normal"
            elif 150 < q_percent:
                q_rating = "High"
            print(f"Evaluating flow risk level at {site_info['site']}, percent of median flow is {q_percent}, "
                  f"rating is {q_rating}.")
            site_info["q_rating"] = q_rating


def add_risk_message(info_lists):

    """ Append a risk information message to the site information list that gives additional information
    on how to interpret the risk rating level.  This is now deprecated in the html email and only used
    in the plain text fallback email."""

    for info_list in info_lists:
        risk = info_list[5]
        reach_alias = info_list[6]
        if risk == "LOW":
            risk_msg = f"Water temperature risk currently is LOW for fishing {reach_alias.upper()}.\n\n" \
                       f" > Water temperatures are generally safe for fishing and fish health."
        elif risk == "MODERATE":
            risk_msg = f"Water temperature risk currently is MODERATE for fishing {reach_alias.upper()}.\n\n" \
                       f" > Monitor water temperatures closely for further warming and consider packing it up as " \
                       f"they approach or exceed 67 degrees F.\n" \
                       f" > Stress from being caught can impact or kill fish well after the time of release.\n" \
                       f" > Consider avoiding this stream reach until water temperatures cool off."
        elif risk == "HIGH":
            risk_msg = f"Water temperature risk currently is HIGH for fishing {reach_alias.upper()}.\n\n" \
                       f" > Stress from being caught may kill fish several hours or even a day after release.\n" \
                       f" > It is recommended to completely avoid fishing this reach, or stop fishing now."
        else:
            risk_msg = "No risk level currently assigned for this reach"
        info_list.append(risk_msg)
        # print(info_list)


def check_time(alert_times):

    """The main.py script must run every hour by PythonAnywhere because its timestep options
    are only hourly or daily.  Messages should only be sent in morning and afternoon, so only finish the
    execution at certain times of day (morning, lunch, late afternoon). At other times of day, exit the
    program without making the API call or sending emails."""

    current_hour = datetime.now().strftime('%H')
    print(f"The current hour is {current_hour}.")
    if current_hour in alert_times:
        print("Alerts will be sent.")
        return True
    else:
        print("Alerts will not be sent.")
        return False


##############################################################################
# PROGRAM DATA
##############################################################################

# Stream gauge sites that also have temperature relevant to Eagle County
site_list = [
    '09066510',  # Gore Creek at Mouth (below Vail)
    '09064600',  # Eagle River near Minturn (NO TEMPERATURE DATA AVAILABLE, JUST HERE FOR API ERROR TESTING)
    '394220106431500',  # Eagle River blw Milk Creek at Wolcott (Lower Eagle)
    '09070000',  # Eagle River at Gypsum
    '09058000',  # Colorado River at Kremmling (Gore Canyon)
    '09060799',  # Colorado River at Catamount (Downstream of State Bridge)
    '09070500',  # Colorado River at Dotsero (Below Eagle River confluence)
    '09071750',  # Colorado River above Glenwood Springs (No Name exit)
    '09085000',  # Roaring Fork River in Glenwood Springs (Lower Roaring Fork... applicable to Emma/El Jebel/Basalt?)
    # '123xyzas',  # Bad site name FOR API ERROR TESTING
    # '',  # Empty site name FOR API ERROR TESTING
]

# Set the hours that alerts will go out here, using a string format 'HH' (single digits preceded by '0')
notification_hours = ['08', '14', '15', '16', '20', '22', '23']


##############################################################################
# MAIN PROGRAM
##############################################################################

# PythonAnywhere.com runs this script every hour but will only send emails at specified AM and PM times
# if not check_time(notification_hours):
#     sys.exit()

# call the USGS api for each site and get current temperature and some site metadata
print("Assessing yesterday afternoon's conditions.")
sites_data = gather_site_data(site_list)

# If the site_data object was successfully created, analyze it and send the email alerts
if (sites_data is not None) and (len(sites_data) > 0):
    assign_river_reach(sites_data)  # (dictionaries are mutable, so the function does not need to return anything)
    evaluate_temp_risk(sites_data)
    usgs_calls.calc_historical_flow_stat(sites_data)
    evaluate_flow_conditions(sites_data)
    print("Building zone forecasts.")
    zone_forecasts = water_forecasts.forecast_stream_temperature()
    print(f"\n{zone_forecasts}\n")

    # create the Yesterdays Conditions table for the email alert
    conditions_html = build_email.build_yesterday_conditions_table(sites_data)
    if not conditions_html:
        conditions_html = "<div><em>Yesterday's conditions report not available.</em></div>"

    # create the Today's Forecast table for the email alert
    forecast_html = build_email.build_forecast_table(zone_forecasts)
    if not forecast_html:
        forecast_html = "<div><hr><em>The water temp forecast application is experiencing temporary errors, no stream temperature forecast currently available for today.</em></div>"

    # Build the combined html email content
    html_content = build_email.build_html_email_message(conditions_html, forecast_html)

    # Create the fallback plain text email (need to revamp function)
    text_content = "Text email testing placeholder"

    print("\nInitiating MailChimp API calls to build campaign and send new alert email.\n")

    ### DEPLOYMENT MAILCHIMP FUNCTIONS
    # Activate MailChimp code during deployment, deactivate during testing:
    # # Send email via MailChimp by creating a Campaign, populating an email, then sending it.
    # current_campaign_id = mc.create_new_daily_campaign(
    #     api_key=MC_API_KEY,
    #     server_prefix=MC_SERVER_PREFIX,
    #     audience_list=ERWC_LIST,
    #     segment_id=int(ALERT_SEGMENT_ID),
    #     reply_to=REPLY_TO_EMAIL
    # )
    #
    # if current_campaign_id is not None:
    #
    #     mc.upload_email_contents(
    #         api_key=MC_API_KEY,
    #         server_prefix=MC_SERVER_PREFIX,
    #         campaign_id_str=current_campaign_id,
    #         html_msg=html_content,
    #         text_msg=text_content
    #     )
    #
    #     mc.send_email_campaign(
    #         api_key=MC_API_KEY,
    #         server_prefix=MC_SERVER_PREFIX,
    #         campaign_id_str=current_campaign_id
    #     )
    #
    #     # campaign sending may take several seconds, pause execution until sending is finished, otherwise
    #     # the delete function call may return an error.
    #     sleep(10)
    #
    #     mc.delete_campaign(
    #         api_key=MC_API_KEY,
    #         server_prefix=MC_SERVER_PREFIX,
    #         campaign_id_str=current_campaign_id
    #     )
    #
    # else:
    #     print('Email Campaign was not successfully created, stopping program.')

    ## TESTING MAILCHIMP FUNCTIONS
    # Activate MailChimp code during TESTING, deactivate during deployment; will
    # only send to the segment of email addresses tagged for 'Bills Test Emails':
    # Send email via MailChimp by creating a Campaign, populating an email, then sending it.
    current_campaign_id = mc.create_new_daily_campaign(
        api_key=MC_API_KEY,
        server_prefix=MC_SERVER_PREFIX,
        audience_list=ERWC_LIST,
        segment_id=int(ALERT_TEST_SEGMENT_ID),
        reply_to=REPLY_TO_EMAIL
    )

    if current_campaign_id is not None:

        mc.upload_email_contents(
            api_key=MC_API_KEY,
            server_prefix=MC_SERVER_PREFIX,
            campaign_id_str=current_campaign_id,
            html_msg=html_content,
            text_msg=text_content
        )

        mc.send_email_campaign(
            api_key=MC_API_KEY,
            server_prefix=MC_SERVER_PREFIX,
            campaign_id_str=current_campaign_id
        )

        # Campaign sending may take several seconds, pause execution until sending is finished, if it is
        # unfinished before the delete command is sent, the delete function call may return an error. (non-fatal)
        sleep(20)

        # Delete the campaign once it is sent, daily campaign frequencies will quickly fill the MC history
        # on the organization's website user interface for Campaigns
        mc.delete_campaign(
            api_key=MC_API_KEY,
            server_prefix=MC_SERVER_PREFIX,
            campaign_id_str=current_campaign_id
        )

    else:
        print('Email Campaign was not successfully created, stopping program.')

    # Activate during testing if you want to work on email formats without using the Mail Chimp
    # API every single time. Send single email with smtplib to personal addresses for feature testing
    # email_tests.send_smtp_email(text_content, html_content)

    print("Program finished.")

else:
    print("No viable data objects returned from USGS webservice, exiting program, no alerts sent.")
    sys.exit()


# TODO: Call a weather API that gets a high temperature prediction for Avon, Eagle/Gypsum, and Bond and include in the email message
# TODO: Add flow data to the email table (actual cfs, + % median)
# TODO: Write function to call the MailChimp API and update the mailing list (Audience) once a week.
# TODO: determine if we're going to keep sending these from an individual address (info@erwc.org?) or if we can send the entire message body to MailChimp and send it from there.  This may be a more secure route if it is possible?
# TODO: "yesterday the temperature climbed over at 67 at [time] and reached a max of [max_temp]. Today the high air temperature forecasted is...


###############################################################################
# EXTRAS
# Periodically send/test mail here to see spam rating:  https://www.mail-tester.com/; current rating 9.9/10 (very good)

##############################################################################
# UNUSED CODE
