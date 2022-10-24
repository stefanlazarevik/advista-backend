# coding=utf-8
import json
import requests

from six import string_types
from six.moves.urllib.parse import urlencode, urlunparse  # noqa

ACCESS_TOKEN = "xxx"
PATH = "/open_api/v1.3/report/integrated/get/"


def build_url(path, query=""):
    # type: (str, str) -> str
    """
    Build request URL
    :param path: Request path
    :param query: Querystring
    :return: Request URL
    """
    scheme, netloc = "https", "biz-api.tiktok.com/open_api/v1.3"
    return urlunparse((scheme, netloc, path, "", query, ""))


def tiktok_get(json_str, path, access_token):
    # type: (str) -> dict
    """
    Send GET request
    :param json_str: Args in JSON format
    :return: Response in JSON format
    """
    args = json.loads(json_str)
    query_string = urlencode({k: v if isinstance(v, string_types) else json.dumps(v) for k, v in args.items()})
    url = build_url(path, query_string)
    headers = {
        "Access-Token": access_token,
    }
    rsp = requests.get(url, headers=headers)
    return rsp.json()

# if __name__ == '__main__':
#     metrics_list = METRICS
#     metrics = json.dumps(metrics_list)
#     data_level = DATA_LEVEL
#     end_date = END_DATE
#     order_type = ORDER_TYPE
#     order_field = ORDER_FIELD
#     page_size = PAGE_SIZE
#     start_date = START_DATE
#     advertiser_id = ADVERTISER_ID
#     filter_value = FILTER_VALUE
#     field_name = FIELD_NAME
#     filter_type = FILTER_TYPE
#     service_type = SERVICE_TYPE
#     report_type = REPORT_TYPE
#     page = PAGE
#     dimensions_list = DIMENSIONS
#     dimensions = json.dumps(dimensions_list)
#
#     # Args in JSON format
#     my_args = "{\"metrics\": %s, \"data_level\": \"%s\", \"end_date\": \"%s\", \"order_type\": \"%s\", \"order_field\": \"%s\", \"page_size\": \"%s\", \"start_date\": \"%s\", \"advertiser_id\": \"%s\", \"filtering\": [{\"filter_value\": \"%s\", \"field_name\": \"%s\", \"filter_type\": \"%s\"}], \"service_type\": \"%s\", \"report_type\": \"%s\", \"page\": \"%s\", \"dimensions\": %s}" % (metrics, data_level, end_date, order_type, order_field, page_size, start_date, advertiser_id, filter_value, field_name, filter_type, service_type, report_type, page, dimensions)
#     print(get(my_args))