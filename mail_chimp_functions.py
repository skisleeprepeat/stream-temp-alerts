# Mail_chimp_api.py contains functions for accessing ERWC email user lists and sending automated emails to MailChimp
# Bill Hoblitzell 6/22/2021

import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from datetime import datetime


def create_new_daily_campaign(api_key, server_prefix, audience_list, segment_id, reply_to):

    """Create a new email Campaign. Each campaign receives a unique title using the current date string"""

    # Additional variables for campaign creation
    subject_date = f"{datetime.now().strftime('%A')} {datetime.now().strftime('%B')} {datetime.now().strftime('%d')}"
    title_time = f"{datetime.now().strftime('%H:%M')}"
    subject_str = f"ERWC Stream Temperature Update for {subject_date}"
    title_str = f"Temp Alert for {subject_date} at {title_time}"
    # Campaign information:
    # The audience list is the full ERWC mailing list id, it is then subsetted by segment.
    # ALERT_SEGMENT_ID was created in the MailChimp web GUI by segmenting  using the 'River Alert Recipient' tag.
    recipient_opts = {
        "list_id": audience_list,
        "segment_opts": {
            "saved_segment_id": segment_id
        }
    }

    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": api_key,
            "server": server_prefix
        })
        response = client.campaigns.create(
            {
                "type": "regular",
                "recipients": recipient_opts,
                "settings": {
                    "subject_line": subject_str,
                    "title": title_str,
                    "from_name": 'Eagle River Watershed Council updates',
                    "reply_to": reply_to,
                    "to_name": '*|FNAME|*',
                    "auto_footer": True,
                }
            }
        )
        # Catch the new campaign id after it is created to use in the update-content and send-email functions
        campaign_id_str = response['id']
        # Dump some metadata into an html file to view in browser if needed
        segment_text = response['recipients']['segment_text']
        recipient_count = response['recipients']['recipient_count']
        # Logging errors to an html file for troubleshooting
        with open('campaign_response_log.html', 'a') as f:
            f.write(f"<html><body><p>Campaign created for {subject_date} {title_time}</p>{segment_text}<p>"
                    f"Emails will be sent to a total of {recipient_count} recipients</p></body></html>")
        print(f"Campaign id {campaign_id_str} successfully created")
        return campaign_id_str
    except ApiClientError as error:
        print("Error: {}".format(error.text))
        with open('campaign_response_log.html', 'a') as f:
            f.write("Error during campaign creation: {}".format(error.text))


def upload_email_contents(api_key, server_prefix, campaign_id_str, html_msg, text_msg):
    """Update the draft (un-sent) Campaign with email contents by sending it a string of html content and text
    content for fallback"""
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": api_key,
            "server": server_prefix
         })
        response = client.campaigns.set_content(
            campaign_id=campaign_id_str,
            body={
                "html": html_msg,
                "plain_text": text_msg
            }
         )
        #print(response)
        print("Email content successfully uploaded")
    except ApiClientError as error:
        print("Error: {}".format(error.text))


# Send the email
def send_email_campaign(api_key, server_prefix, campaign_id_str):
    """Send the email campaign"""
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": api_key,
            "server": server_prefix
        })
        response = client.campaigns.send(campaign_id=campaign_id_str)
        #print(response)
        print(f"Email Campaign {campaign_id_str} successfully sent")
    except ApiClientError as error:\
        print("Error: {}".format(error.text))


# DELETE the campaign after it's creation
def delete_campaign(api_key, server_prefix, campaign_id_str):
    """Remove the campaign from the account (this application generates a new campaign for every daily email,
    it will accumulate campaigns quickly in the MailChimp dash if not removed."""
    try:
        client = MailchimpMarketing.Client()
        client.set_config({
            "api_key": api_key,
            "server": server_prefix
        })
        response = client.campaigns.remove(campaign_id_str)
        print("Email Campaign {campaign_id_str} has been cleaned/removed")
        #print(response)
    except ApiClientError as error:
        print("Error: {}".format(error.text))


#
