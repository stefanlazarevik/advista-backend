from pyairtable import Table
from requests import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from .system1_api import get_system1_campaign_data

Search_Arbitrage_Hub_BASE_ID = 'appLB431vvCqF2Hqg'
Accounts_Links_Hub_BASE_ID = 'app8wTJzMsSOYPxiP'
API_KEY = 'keyr6r3tYDGne9P8m'


class AirtableView(APIView):
    @api_view(["get"])
    def get_scheduler_data(self):
        response = {"success": True}
        media_buyer = AirtableView.get_airtable_media_buyer_data(self)
        vertical_data = AirtableView.get_airtable_verticals_data(self)
        domain_data = AirtableView.get_get_airtable_domains_data(self)
        get_system1_revenue_using_domain = AirtableView.get_system1_campaign_revenue(self, domain_data)

        return Response(response, status=status.HTTP_200_OK)

    def get_airtable_data(self, base_id, table_name, filterValue=None):
        filterValue = filterValue if filterValue else ''
        airtable_data = Table(API_KEY, base_id, table_name).all(formula=[filterValue])
        return airtable_data

    def get_airtable_verticals(self, filterValue=None):
        base_id = Search_Arbitrage_Hub_BASE_ID
        table_name = 'Verticals'
        filterValue = filterValue if filterValue else ''
        verticales_data = AirtableView.get_airtable_data(self, base_id=base_id, table_name=table_name,
                                                         filterValue=filterValue)
        return verticales_data

    def get_airtable_accounts(self, filterValue=None):
        base_id = Search_Arbitrage_Hub_BASE_ID
        table_name = 'Accounts'
        filterValue = filterValue if filterValue else ''
        accounts_data = AirtableView.get_airtable_data(self, base_id=base_id, table_name=table_name,
                                                       filterValue=filterValue)
        return accounts_data

    def get_airtable_domains(self, filterValue=None):
        base_id = Search_Arbitrage_Hub_BASE_ID
        table_name = 'Domains'
        filterValue = filterValue if filterValue else ''
        domains_data = AirtableView.get_airtable_data(self, base_id=base_id, table_name=table_name,
                                                      filterValue=filterValue)
        return domains_data

    def get_airtable_media_buyer_data(self):
        media_buyer = {}
        filterValue = "AND(NOT({Account ID}=''))"
        accounts_data = AirtableView.get_airtable_accounts(self, filterValue)
        for i in accounts_data:
            data = i['fields']
            buyer = data['Requested by']
            account_id = data['Account ID'].strip() if data['Account ID'] else None
            if account_id:
                data['Account ID'] = account_id
                if buyer in media_buyer:
                    media_buyer[buyer].append(data)
                else:
                    media_buyer[buyer] = [data]
        return media_buyer

    def get_airtable_verticals_data(self):
        filterValue = "NOT({Domains}='')"
        advertiser_ids = {}
        verticals_data = AirtableView.get_airtable_verticals(self, filterValue)
        for i in AirtableView.get_airtable_accounts(self, filterValue="AND(NOT({Account ID}=''))"):
            data = i['fields']
            if 'Domains' in data:
                for domain in data['Domains']:
                    advertiser_ids[domain] = data['Account ID']

        for i in verticals_data:
            data = i['fields']
            if 'Domains' in data:
                for domain in data['Domains']:
                    try:
                        data['Account ID'] = advertiser_ids[domain]
                    except:
                        continue
        return verticals_data

    def get_get_airtable_domains_data(self):
        filterValue = "AND({Source}='System1',NOT({Account ID (from Accounts)}=''))"
        domains_data = AirtableView.get_airtable_domains(self, filterValue)
        return domains_data

    def get_system1_campaign_revenue(self, domains_data):
        result = {}
        campaign = ""
        for i in domains_data:
            data = i['fields']
            domain = \
                data['Partner URL'].replace('http://', '').replace("/", '').replace(":", "").replace("https", "").split(
                    "?rskey")[0]
            advertiser_id = data['Account ID (from Accounts)'][0].strip()
            result[domain] = [advertiser_id]

        domain_list = list(result.keys())
        for i in domain_list:
            campaign += i.strip()
            campaign += ','
        params = {
            'days': '2022-11-20',
            'campaign': campaign
        }
        get_system1_campaign = get_system1_campaign_data(params)
        total_revenue = {}
        for i in get_system1_campaign[1:]:
            domain = i[1]
            revenue = i[12]
            if domain:
                if domain in total_revenue:
                    total_revenue = total_revenue[domain] + revenue
                else:
                    total_revenue[domain] = revenue
        return total_revenue
