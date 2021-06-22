# AUTOMATED WATER TEMPERATURE ALERT PROGRAM

'''This program uses USGS webservices to call temperature data from gauges
on the Eagle and Colorado River, assess the temperatures against cold-
water fishery risk levels, and utilize email and social media portals to
issue alerts for area anglers.'''

# Author: Bill Hoblitzell/Lotic Hydrological 6/14/2021
# Contact: bill@lotichydrological.com, www.lotichydrological.com
# Modified: 6/16/2021
# Status: Prototype/testing
# Copyright: Lotic Hydrological
# Version 1.0


###############################################################################
# REQUIREMENTS
###############################################################################
import os
import sys
import requests
from datetime import datetime
import smtplib
import build_email
from dotenv import load_dotenv
import mail_chimp_functions as mc
from time import sleep

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

# reply-to email
reply_to = 'alerts@erwc.org'
# my_email = 'billhoblitzell80@gmail.com'
# my_password = 'NewRiverGorge4500'
# to_email = ['billhoblitzell@yahoo.com', 'bill@lotichydrological.com']


###############################################################################
# FUNCTIONS
###############################################################################

def call_USGS_api(site):

    """Calls the USGS Webservice and passes the API a gauge ID to get the most recent water temperature reading.
    Return a JSON object"""

    print(f"Calling USGS Webservice for {site}")
    url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={site}&parameterCd=00010&siteStatus=all"
    print(url)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(err)


def unpack_USGS_response(data):

    """ Extracts only the desired information (temperature and site metadata) from the USGS JSON object.
    Return a list with the information"""

    print("Unpacking JSON response")
    try:
        temp_c = data["value"]["timeSeries"][0]["values"][0]["value"][0]["value"]
        obs_datetime = data["value"]["timeSeries"][0]["values"][0]["value"][0]["dateTime"]
        print("Data added to site list")
    except (NameError, KeyError) as error:
        print("Unpacking JSON object was unsuccessful, check for key errors or that data actually exists.")
        return error
    else:
        # Sites that had temp monitoring in the past will return the last date and obs that exists in the record
        # to avoid this, check to see that the observation date matches today's date
        if datetime.now().date().today().strftime("%Y-%m-%d") == \
                datetime.strptime(obs_datetime, '%Y-%m-%dT%H:%M:%S.%f%z').date().strftime("%Y-%m-%d"):
            temp_f = round(float(temp_c) * (9 / 5) + 32, 1)
            obs_time = datetime.strptime(obs_datetime, '%Y-%m-%dT%H:%M:%S.%f%z').time().strftime("%H:%M")
            site_name = data["value"]["timeSeries"][0]["sourceInfo"]["siteName"]
            site_id = data["value"]["timeSeries"][0]["sourceInfo"]["siteCode"][0]["value"]
            return [site_name, site_id, obs_time, temp_f]


def gather_site_data(sites):

    """ Aggregate the data for all the monitoring sites. Return of list of lists for the sites"""

    assessment_list = []
    for site in sites:
        data = call_USGS_api(site)
        if data is not None:
            print(f"Assessing {site}")
            assessment = unpack_USGS_response(data)
            if assessment is not None:
                assessment_list.append(assessment)
        else:
            print(f"No data found for {site}")
    return assessment_list


def evaluate_temp_risk(data_list):

    """ Using the current temperature, assign a narrative ordinal rating for fish at the site. Append the
     rating to that site's information list"""

    for site_info in data_list:
        print(site_info)
        temp = float(site_info[3])
        risk = 'Not assigned'
        if temp < 67:
            risk = "LOW"
        elif 67 <= temp < 70:
            risk = "MODERATE"
        elif temp >= 70:
            risk = "HIGH"
        elif temp is None:
            risk = "<no rating>"
        print(f"Evaluating temperature for fishing risk level at {site_info[0]}, current temp is {temp}, risk is {risk}.")
        site_info.append(risk)


def get_river_reach(info_lists):

    """Append the local nicknames for stream reaches associated with different temperature monitoring sites
    to the site's information list"""

    for info_list in info_lists:
        site_id = info_list[1]
        if site_id == "09060799":
            alias = 'Colorado River below State Bridge'
        elif site_id == "09058000":
            alias = 'Colorado River between Pumphouse and State Bridge'
        elif site_id == "394220106431500":
            alias = 'Lower Eagle River'
        elif site_id == "09066510":
            alias = 'Gore Creek in Vail'
        elif site_id == "09071750":
            alias = 'Colorado River in Glenwood Canyon'
        elif site_id == "09070500":
            alias = 'Colorado River above and below Dotsero'
        elif site_id == "09085100":
            alias = 'Lower Roaring Fork River'
        else:
            alias = info_list[0]  # just assign the gauge name if no reach nickname is found
        info_list.append(alias)


def add_risk_message(info_lists):

    """ Append a risk information message to the site information list that gives additional information
    on how to interpret the risk rating level.  This is now deprecated in the html email and only used
    in the plain text fallback email."""

    for info_list in info_lists:
        risk = info_list[4]
        reach_alias = info_list[5]
        if risk == "LOW":
            risk_msg = f"Water temperature risk currently is LOW for fishing {reach_alias.upper()}.\n\n" \
                       f" > Water temperatures are generally safe for fishing and fish health."
        elif risk == "MODERATE":
            risk_msg = f"Water temperature risk currently is MODERATE for fishing {reach_alias.upper()}.\n\n" \
                       f" > Monitor water temperatures closely for further warming and consider packing it up as they " \
                       f"approach or exceed 67 degrees F.\n" \
                       f" > Stress from being caught can impact or kill fish well after the time of release.\n" \
                       f" > Consider avoiding this stream reach until water temperatures cool off."
        elif risk == "HIGH":
            risk_msg = f"Water temperature risk currently is HIGH for fishing {reach_alias.upper()}.\n\n" \
                       f" > Stress from being caught may kill fish several hours or even a day after release.\n" \
                       f" > It is recommended to completely avoid fishing this reach, or stop fishing now."
        else:
            risk_msg = "No risk level currently assigned for this reach"
        info_list.append(risk_msg)


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
    '394220106431500',  # Eagle River blw Milk Creek at Wolcott (Lower Eagle)
    '09066510',  # Gore Creek at Mouth (below Vail)
    '09058000',  # Colorado River at Kremmling (Gore Canyon)
    '09060799',  # Colorado River at Catamount (Downstream of State Bridge)
    '09070500',  # Colorado River at Dotsero (Below Eagle River confluence)
    '09071750',  # Colorado River above Glenwood Springs (No Name exit)
    '09085000',  # Roaring Fork River in Glenwood Springs (Lower Roaring Fork... applicable to Emma/El Jebel/Basalt?)
    #'09064600',  # Eagle River near Minturn (NO TEMPERATURE DATA AVAILABLE, JUST HERE FOR API ERROR TESTING)
    #'123xyzas',  # FOR API ERROR TESTING
    #'',  # FOR API ERROR TESTING
]

# Set the hours that alerts will go out here, using a string format 'HH' (single digits preceded by '0')
notification_hours = ['14', '16']


##############################################################################
# MAIN PROGRAM
##############################################################################

# PythonAnywhere.com runs this script every hour.  Only send emails at specified AM and PM times
if not check_time(notification_hours):
    sys.exit()

# call the USGS api for each site and get current temperature and some site metadata
sites_data = gather_site_data(site_list)
# print(sites_data)

# if the site data object is available, analyze it and send the email alerts
if sites_data is not None:
    # assign a narrative risk level to each site
    evaluate_temp_risk(sites_data)
    # add some information for the email
    get_river_reach(sites_data)
    add_risk_message(sites_data)

    # create the email message body
    text_content = build_email.build_text_email_message(sites_data)
    html_content = build_email.build_html_email_message(sites_data)

    # # Send email via MailChimp by creating a Campaign, populating an email, then sending it.
    current_campaign_id = mc.create_new_daily_campaign(
        api_key=MC_API_KEY,
        server_prefix=MC_SERVER_PREFIX,
        audience_list=ERWC_LIST,
        segment_id=int(ALERT_SEGMENT_ID),
        reply_to='alerts@erwc.org'
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

        # campaign sending may take several seconds, pause execution until sending is finished, otherwise
        # the delete function call may return an error.
        sleep(10)

        mc.delete_campaign(
            api_key=MC_API_KEY,
            server_prefix=MC_SERVER_PREFIX,
            campaign_id_str=current_campaign_id
        )

    else:
        print('Email Campaign was not successfully created, stopping program.')

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

# recipients = [
#     'billhoblitzell@yahoo.com',
#     'smith@erwc.org',
#     'seth@lotichydrological.com',
#     'loff@erwc.org',
#     'dilzell@erwc.org',
#     'djohnson@erwsd.org',
#     'marks@minturnanglers.com',
#     'nickkeogh@minturnanglers.com',
#     'kendall.bakich@state.co.us'
# ]
#
# recipients = [
#     'billhoblitzell@yahoo.com',
#     'billhoblitzell80@gmail.com',
# ]
