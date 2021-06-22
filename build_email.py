###############################################################################
# Requirements
###############################################################################

import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

###############################################################################
# Constants for html formatting
###############################################################################

# Risk Level colors
risk_colors = {
    "green": "#32CD32",
    "yellow": "yellow",
    "red": "red"
}

##############################################################################
# Mailing functions
###############################################################################


def build_table_rows(sites_data):
    table_header_string = "<tr><td colspan='2' style='font-size: 1.3rem'><h3>Current Stream Conditions</h3></td></tr>" \
                    "<tr style='font-size:1.2rem'><td><strong>Location</strong></td><td><strong>Time</strong></td>" \
                    "<td><strong>Temp &#176;F</strong></td><td><strong>Fishing Risk Level</strong></td></tr>"
    all_rows_string = ""
    for site in sites_data:
        risk_color = ""
        if site[4] == "LOW":
            risk_color = risk_colors["green"]
        if site[4] == "MODERATE":
            risk_color = risk_colors["yellow"]
        if site[4] == "HIGH":
            risk_color = risk_colors["red"]
        row_string = f"<tr><" \
                     f"td>{site[0]}</td>" \
                     f"<td style='text-align:center'>{site[2]}</td>" \
                     f"<td style='text-align:center'>{site[3]}</td>" \
                     f"<td style='text-align:center; font-weight: bold; background-color:{risk_color}'>{site[4]}</td>" \
                     f"</tr>"

        all_rows_string = all_rows_string + row_string
    full_table_string = f"<div><hr><nbsp><table cellpadding='3'>{table_header_string}{all_rows_string}</table></div>"
    return full_table_string


def build_html_email_message(sites_data):

    """  Create an html email body with the risk ratings for each site, tips on warm water fishing, and information
    about the Eagle River Watershed Council. Return the message body as a long string"""

    print("Building html email message.")

    update_time = f"{datetime.now().strftime('%A')}, " \
                  f"{datetime.now().strftime('%B')} " \
                  f"{datetime.now().strftime('%d')} at " \
                  f"{datetime.now().strftime('%H:%M')}"

    # read in the header
    with open(f"email_templates/header.html") as template:
        contents = template.read()
        header_html = contents.replace('[update_time]', update_time)

    # make the table of current conditions
    table_html = build_table_rows(sites_data)

    # read in the rest of the email body... the risk key and the footer
    with open("email_templates/risk_key_and_footer.html") as template:
        contents = template.read()
    contents = contents.replace('[risk_green]', risk_colors["green"])
    contents = contents.replace('[risk_yellow]', risk_colors["yellow"])
    contents = contents.replace('[risk_red]', risk_colors["red"])
    risk_key_and_footer = contents

    # put all the parts together
    email_html = header_html + table_html + risk_key_and_footer

    # dump the message string to an html file for checking/viewing while building the email up
    with open("old/template_practice.html", 'w') as html_file:
        html_file.write(email_html)

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
    print(message_body)
    return message_body


def send_email(msg_body_text, msg_body_html, msg_recipients, sndr_email, sndr_password):

    """Use smtp library to send an alert email with the current risk message to the app user list."""

    # print(msg_body_html)
    print("Sending email alert")

    # set up the MIME message object
    message = MIMEMultipart("alternative")
    message["Subject"] = 'HTML format email test'
    message["From"] = sndr_email
    message["To"] = ", ".join(msg_recipients)

    # Turn the email bodies into plain/html MIMEText objects
    text_part = MIMEText(msg_body_text, "plain")
    html_part = MIMEText(msg_body_html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(text_part)
    message.attach(html_part)

    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        connection.ehlo()
        connection.starttls()
        connection.login(
            user=sndr_email,
            password=sndr_password
        )
        connection.sendmail(
            from_addr=sndr_email,
            to_addrs=msg_recipients,
            msg=message.as_string()
        )
        print("...message sent.")




 ##############################################################################################################
# table testing data, (must be moved to the top to be used)
# sites_data = [['EAGLE RIVER BELOW MILK CREEK NEAR WOLCOTT, CO', '394220106431500', '12:15', 55.0, 'LOW', 'Lower Eagle River', 'Water temperature risk currently is LOW for fishing LOWER EAGLE RIVER.\n\n > Water temperatures are generally safe for fishing and fish health.'],
#               ['GORE CREEK AT MOUTH NEAR MINTURN, CO', '09066510', '11:15', 48.2, 'LOW', 'Gore Creek in Vail', 'Water temperature risk currently is LOW for fishing GORE CREEK IN VAIL.\n\n > Water temperatures are generally safe for fishing and fish health.'],
#               ['COLORADO RIVER NEAR KREMMLING, CO', '09058000', '11:15', 64.6, 'MODERATE', 'Colorado River between Pumphouse and State Bridge', 'Water temperature risk currently is MODERATE for fishing COLORADO RIVER BETWEEN PUMPHOUSE AND STATE BRIDGE.\n\n > Monitor water temperatures closely for further warming and consider packing it up as they approach or exceed 65 degrees F.\n > Stress from being caught can impact or kill fish well after the time of release.\n > Consider avoiding this stream reach until water temperatures cool off.'],
#               ['COLORADO RIVER AT CATAMOUNT BRIDGE, CO', '09060799', '11:30', 66.9, 'HIGH', 'Colorado River below State Bridge', 'Water temperature risk currently is HIGH for fishing COLORADO RIVER BELOW STATE BRIDGE.\n\n > Stress from being caught may kill fish several hours or even a day after release.\n > Consider avoiding this stream reach until water temperatures cool off.'],
#               ['COLORADO RIVER NEAR DOTSERO, CO', '09070500', '12:00', 61.9, 'MODERATE', 'Colorado River above and below Dotsero', 'Water temperature risk currently is MODERATE for fishing COLORADO RIVER ABOVE AND BELOW DOTSERO.\n\n > Monitor water temperatures closely for further warming and consider packing it up as they approach or exceed 65 degrees F.\n > Stress from being caught can impact or kill fish well after the time of release.\n > Consider avoiding this stream reach until water temperatures cool off.'],
#               ['COLORADO RIVER ABOVE GLENWOOD SPRINGS, CO', '09071750', '11:30', 65.5, 'HIGH', 'Colorado River in Glenwood Canyon', 'Water temperature risk currently is HIGH for fishing COLORADO RIVER IN GLENWOOD CANYON.\n\n > Stress from being caught may kill fish several hours or even a day after release.\n > Consider avoiding this stream reach until water temperatures cool off.'],
#               ['ROARING FORK RIVER AT GLENWOOD SPRINGS, CO.', '09085000', '11:45', 55.4, 'LOW', 'ROARING FORK RIVER AT GLENWOOD SPRINGS, CO.', 'Water temperature risk currently is LOW for fishing ROARING FORK RIVER AT GLENWOOD SPRINGS, CO..\n\n > Water temperatures are generally safe for fishing and fish health.']]
# site_data = sites_data[0]
