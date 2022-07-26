# Development code...
# import a saved data output from the USGS gauge calls directly without making an api call

import os
import build_email
import numpy as np
import water_forecasts

print(os.getcwd())
os.chdir("/")
print(os.getcwd())

# with open('./test_data_list.txt', 'r') as f:
#     sites_data = [site_data.rstrip() for site_data in f.readlines()]
#
# for site_info in sites_data:
#     print(type(site_info))
#     print(site_info)
#
#

# print(conditions_html)
#
sites_data = [
    {'site': '09066510', 'yesterday_mean_q': 27, 'yesterday_max_t': 63, 'alias': 'Lower Gore Creek', 't_risk': 'LOW', 'percent_of_median': 47, 'q_rating': 'Low'},
    {'site': '09064600', 'yesterday_mean_q': 51, 'yesterday_max_t': np.nan, 'alias': 'Upper Eagle River, Minturn Area', 't_risk': '<em>no rating</em>', 'percent_of_median': 70, 'q_rating': 'Below Normal'},
    {'site': '394220106431500', 'yesterday_mean_q': 159, 'yesterday_max_t': 67, 'alias': 'Middle Eagle River, Wolcott Area', 't_risk': 'CONCERN', 'percent_of_median': 65, 'q_rating': 'Below Normal'},
    {'site': '09070000', 'yesterday_mean_q': 204, 'yesterday_max_t': np.nan, 'alias': 'Lower Eagle River, Eagle/Gypsum Area', 't_risk': '<em>no rating</em>', 'percent_of_median': 62, 'q_rating': 'Below Normal'},
    {'site': '09058000', 'yesterday_mean_q': 997, 'yesterday_max_t': 61, 'alias': 'Colorado River, Pumphouse/Radium/State Bridge Area', 't_risk': 'LOW', 'percent_of_median': 98, 'q_rating': 'Normal'},
    {'site': '09060799', 'yesterday_mean_q': 1125, 'yesterday_max_t': 65, 'alias': 'Colorado River, Two Bridge/Catamount/Burns Area', 't_risk': 'CONCERN', 'percent_of_median': 78, 'q_rating': 'Below Normal'},
    {'site': '09070500', 'yesterday_mean_q': 1402, 'yesterday_max_t': 67, 'alias': 'Colorado River, Dotsero Area', 't_risk': 'CONCERN', 'percent_of_median': 92, 'q_rating': 'Normal'},
    {'site': '09071750', 'yesterday_mean_q': np.nan, 'yesterday_max_t': 65, 'alias': 'Colorado River, Glenwood Canyon', 't_risk': 'CONCERN', 'percent_of_median': '---', 'q_rating': '---'},
    {'site': '09085000', 'yesterday_mean_q': 557, 'yesterday_max_t': 66, 'alias': 'Lower Roaring Fork River', 't_risk': 'CONCERN', 'percent_of_median': 61, 'q_rating': 'Below Normal'}
]


conditions_html = build_email.build_yesterday_conditions_table(sites_data)
forecast_html = water_forecasts.forecast_stream_temperature()

print(conditions_html)
print(forecast_html)
#
#

