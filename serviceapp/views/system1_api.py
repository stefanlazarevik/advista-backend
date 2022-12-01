import requests

BASE_URL = 'https://reports.openmail.com/v2/'
auth_key = 'DV69sEoVxUfNYoVIrl3Y'


def get_system1_campaign_data(params):
    days = params['days'] if 'days' in params else ''
    campaign = params['campaign'] if 'campaign' in params else ''
    url = BASE_URL + 'campaign.json'
    params = {
        'auth_key': auth_key,
        'days': days,
        'campaign': campaign
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data


# def get_subid_estimated_intraday():
#     url = BASE_URL + 'subid_estimated_intraday.json?auth_key={}&days=2022-11-20'.format(auth_key)
#     print(url)
#     response = requests.get(url)
#     data = response.json()['subids']
#     return data


# def get_system1_campaign_revenue(campaign_list):
#     result = {}
#     domain_list = campaign_list
#     campaign = ""
#     for i in domain_list:
#         campaign += i.strip()
#         campaign += ','
#     print(campaign)
#     params = {
#         'days': '2022-11-20',
#         'campaign': campaign
#     }
#     get_campaign = get_campaign_data(params)
#     for i in get_campaign[1:]:
#         domain = i[1]
#         revenue = i[12]
#         if domain:
#             if domain in result:
#                 result[domain] = result[domain] + revenue
#             else:
#                 result[domain] = revenue
#     return result
#
#
