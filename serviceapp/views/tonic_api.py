import json

import requests
from datetime import datetime, timezone

BASE_URL = 'https://api.publisher.tonic.com'


def datetime_timezone():
    return datetime.utcnow().strftime("%Y-%m-%d")


def get_access_token():
    path = BASE_URL + '/jwt/authenticate'
    headers = {
        "Content-Type": 'application/json',
    }
    body = {
        "consumer_key": "2148688206145166766",
        "consumer_secret": "294de7600dee7ec0305020045205b63c84e26de5"
    }
    rsp = requests.post(path, json=body, headers=headers)
    return rsp


def get_tonic_daily_report(access_token):
    tonic_result = []
    path = BASE_URL + '/privileged/v3/reports/tracking'
    date = datetime_timezone()
    params = {
        'date': date,
        'output': 'json'
    }
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "Content-Type": 'application/json',
    }
    rsp = requests.get(path, params=params, headers=headers)
    for i in rsp.json():
        try:
            tonic_result.append({
                'report_date': i['date'],
                'revenue': i['revenueUsd'],
                'tonic_campaign_id': i['subid1'],
                'tonic_campaign_name': i['campaign_name'],
                'clicks': i['clicks'],
                'keyword': i['keyword'],
                'adtitle': i['adtitle'],
                'device': i['device'],
            })
        except Exception as e:
            print(e)
    return tonic_result
