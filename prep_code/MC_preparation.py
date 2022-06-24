# API calls to get MailChimp backend information for properly setting up the alert emails

import os
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
from dotenv import load_dotenv
import json


load_dotenv()
MC_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MC_SERVER_PREFIX = os.getenv('MAILCHIMP_SERVER_PREFIX')
ERWC_LIST = os.getenv('MAILCHIMP_ERWC_LIST')

print(f'current dir is: {os. getcwd()}')

# Get information for ERWC's lists. In MailChimp a List, also known as your audience,
# is  where you store and manage all of your contacts.
try:
    client = MailchimpMarketing.Client()
    client.set_config({
      "api_key": MC_API_KEY,
      "server": MC_SERVER_PREFIX
    })
    response = client.lists.get_all_lists()
    print(response)
    with open("../dev_outputs/MC_ERWC_list_info_2022.json", "w") as f:
        f.write(json.dumps(response))
except ApiClientError as error:
    print("Error: {}".format(error.text))




# Get information about all available segments for a specific list.
# In MailChimp, a segment is a list of filtered contacts.

# The MC API uses pagination and will only return the first 10 segments unless the 'count' argument is set higher (i.e. 100);
# an alternative/manual way to retrieve a segment ID if it doesn't show here is to log into the
# website under your credentials, then go to Audience>Manage>Segments, find the segment
# you are looking for, right-click it, then select 'copy link address' and paste it directly
# into the browser, you will be able to see the segment ID as a parameter in the URL
# https://stackoverflow.com/questions/55071895/where-can-i-find-the-segment-id-of-a-tag-in-mailchimp

try:
    client = MailchimpMarketing.Client()
    client.set_config({
        "api_key": MC_API_KEY,
        "server": MC_SERVER_PREFIX
    })
    response = client.lists.list_segments(list_id=ERWC_LIST,count=100)
    print(response)
    with open("../dev_outputs/MC_ERWC_segment_info_2022.json", "w") as f:
        f.write(json.dumps(response))
except ApiClientError as error:
    print("Error: {}".format(error.text))
