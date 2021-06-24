import requests
import datetime as dt
import dataretrieval.nwis as nwis


def get_q_median(site):

    """ use the python USGS dataretrieval package to get 50th percentile flows for the date"""

    param = '00060'
    print(f"getting median flows for {site}")
    q_stats, md = nwis.get_stats(sites=site, parameterCd=param, statReportType='daily', statTypeCd='p50')
    # extract the media flow for today's date
    current_month = dt.datetime.today().month
    current_day = dt.datetime.today().day
    median_flow = int(q_stats.loc[(q_stats['month_nu'] == current_month) & (q_stats['day_nu'] == current_day), 'p50_va'])
    return median_flow


def calc_flow_stats(info_lists):

    """If the site data has flow data, call for the median flow and calculate percent of median"""

    for info_list in info_lists:
        site_id = info_list[1]
        print(f"site id is: {site_id}")
        if info_list[4] != '--':
            q_current = int(info_list[4])
            print(f"current discharge is: {q_current}")
            q_median = get_q_median(site=site_id)
            if q_median is not None:
                q_perc_median = round((q_current / q_median)*100)
            else:
                q_perc_median = '--'
            print(f"Percent of median is: {q_perc_median}")
            info_list.append(q_perc_median)
        else:
            info_list.append('--')


def call_USGS_api(site):

    """Calls the USGS Webservice and passes the API a gauge ID to get the most recent water temperature reading.
    Return a JSON object"""

    # Call for temp C and discharge
    params = ['00010', '00060']
    param_str = ','.join(params)
    url = f"https://waterservices.usgs.gov/nwis/iv/?format=json&sites={site}&parameterCd={param_str}&siteStatus=all"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(err)









#