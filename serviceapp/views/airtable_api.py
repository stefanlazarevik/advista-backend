from datetime import timedelta

from pyairtable import Table
from requests import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from .system1_api import get_system1_campaign_data
from ..models import *

Search_Arbitrage_Hub_BASE_ID = 'appLB431vvCqF2Hqg'
Accounts_Links_Hub_BASE_ID = 'app8wTJzMsSOYPxiP'
API_KEY = 'keyr6r3tYDGne9P8m'


class AirtableView(APIView):
    @api_view(["get"])
    def get_scheduler_data(request):
        response = {"success": True}
        if "today" in request.GET:
            timezone_date = request.GET.get('today')
        else:
            today = datetime.now().date()
            timezone_date = today + timedelta(days=-1)
        print("-------------media_buyer start................")
        media_buyer = AirtableView.get_airtable_media_buyer_data(request,
                                                                 timezone_date)  # Get media_buyer_data from airtable api.
        new_media_buyer_response = AirtableView.save_media_buyer_into_db(request, media_buyer)
        if 'new_media_buyer_data' in new_media_buyer_response:
            AirtableView.save_media_buyer_advertiser_into_db(request, new_media_buyer_response, media_buyer)
        print("-------------media_buyer end................")
        print("-------------verticals start................")
        vertical_data = AirtableView.get_airtable_verticals_data(request, timezone_date)
        new_vertical_response = AirtableView.save_verticals_data_into_db(request, vertical_data)
        if 'new_vertical_data' in new_vertical_response:
            AirtableView.save_vertical_advertiser_ids_into_db(request, new_vertical_response, vertical_data)
        print("-------------verticals end................")
        # print("-------------domain_data start................")
        # domain_data = AirtableView.get_get_airtable_domains_data(request)
        # print("-------------domain_data end................")
        # get_system1_revenue_using_domain = AirtableView.get_system1_campaign_revenue(request, domain_data)
        # if len(get_system1_revenue_using_domain) > 0:
        #     AirtableView.save_revenue_into_reports_db(request, get_system1_revenue_using_domain)
        # print(get_system1_revenue_using_domain)

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

    def get_airtable_accounts(self, filterValue=None, base_id=None):
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

    def get_airtable_media_buyer_data(self, date):
        media_buyer = {}
        # filterValue = "AND(NOT({{Account ID}}=''),DATESTR({{Created}})='{}')".format(date)
        filterValue = "AND(NOT({Account ID}=''),{BC}='PixelMind')"
        accounts_data = AirtableView.get_airtable_accounts(self, filterValue, Accounts_Links_Hub_BASE_ID)
        for i in accounts_data:
            data = i['fields']
            id = data['Requested by']['id'].strip()
            account_id = data['Account ID'].strip() if data['Account ID'] else None
            if account_id:
                if id in media_buyer:
                    media_buyer[id]['advertiser_ids'].append(account_id)
                else:
                    result = {'media_buyer_id': id,
                              'email': data['Requested by']['email'].strip(),
                              'name': data['Requested by']['name'].strip(), 'advertiser_ids': [account_id]}
                    media_buyer[id] = result
        return media_buyer

    def save_media_buyer_into_db(self, media_buyer):
        response = {}
        create_media_buyer = []
        update_media_buyer = []
        requests_ids = [i for i in list(media_buyer.keys())]
        media_buyer_ids = MediaBuyer.objects.values_list('media_buyer_id', flat=True).filter(
            media_buyer_id__in=requests_ids)
        new_media_buyer_ids = list(set(requests_ids).difference(media_buyer_ids))
        existence_media_buyer = list(set(requests_ids).intersection(media_buyer_ids))
        for i in new_media_buyer_ids:
            data = media_buyer[i]
            create_media_buyer.append(
                MediaBuyer(media_buyer_id=data['media_buyer_id'], email=data['email'],
                           name=data['name']))
        for i in existence_media_buyer:
            try:
                data = media_buyer[i]
                media_buyer_obj = MediaBuyer.objects.get(media_buyer_id=data['media_buyer_id'])
                update_media_buyer.append(
                    MediaBuyer(pk=media_buyer_obj.id, email=data['email'], name=data['name']))
            except Exception as e:
                continue
        if create_media_buyer:
            rsp = MediaBuyer.objects.bulk_create(create_media_buyer, batch_size=100)
            response['new_media_buyer_data'] = rsp
        #     response['media_buyer'] = media_buyer
        if update_media_buyer:
            MediaBuyer.objects.bulk_update(create_media_buyer, ['email', 'name'],
                                           batch_size=100)
        return response

    def save_media_buyer_advertiser_into_db(self, new_media_buyer_response, media_buyer):
        new_media_buyer_advertiser = []
        new_media_buyer_data = new_media_buyer_response['new_media_buyer_data']
        for i in new_media_buyer_data:
            media_buyer_id = i.media_buyer_id
            try:
                if media_buyer[media_buyer_id]:
                    advertiser_ids = media_buyer[media_buyer_id]['advertiser_ids']
                    if advertiser_ids:
                        for advertiser_id in advertiser_ids:
                            advertiser_obj = Advertisers.objects.get(advertiser_id=advertiser_id)
                            new_media_buyer_advertiser.append(
                                MediaBuyerAdvertiser(media_buyer_id=i, advertiser_id=advertiser_obj))
            except Exception as e:
                print(e)
                continue
        if new_media_buyer_advertiser:
            MediaBuyerAdvertiser.objects.bulk_create(new_media_buyer_advertiser, batch_size=100)
        return True

    def get_airtable_verticals_data(self, date):
        filterValue = "NOT({Domains}='')"
        advertiser_ids = {}
        verticals_data = AirtableView.get_airtable_verticals(self, filterValue)
        for i in AirtableView.get_airtable_accounts(self,
                                                    filterValue="AND(NOT({Account ID}=''),{BC}='PixelMind')",
                                                    base_id=Search_Arbitrage_Hub_BASE_ID):
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
        response = {}
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

        for i in total_revenue:
            try:
                advertiser = result[i][0]
                response[advertiser] = total_revenue[i]
            except Exception as e:
                continue
        return response

    def save_verticals_data_into_db(self, vertical_data):
        response = {}
        new_vertical_advertiser_obj = {}
        new_vertical_data = []
        update_vertical_data = []
        request_ids = [i['id'] for i in vertical_data]
        vertical_data_list = Vertical.objects.values_list('vertical_id', flat=True).filter(vertical_id__in=request_ids)
        new_vertical_data_list = list(set(request_ids).difference(vertical_data_list))
        for i in vertical_data:
            try:
                data = i['fields']
                details_json = {
                    "name": data['Name'] if 'Name' in data else None,
                    "category": data['Category'] if 'Category' in data else None,
                    "domains": data['Domains'] if 'Domains' in data else None,
                    "stats": data['Stats (from Domains)'] if 'Stats (from Domains)' in data else None,
                    "source": data['Source'] if 'Source' in data else None,
                    "url": data['URL'] if 'URL' in data else None
                }
                if i['id'] in new_vertical_data_list:
                    new_vertical_data.append(
                        Vertical(vertical_id=i['id'], details=details_json, created_time=i['createdTime']))
                    new_vertical_advertiser_obj[i['id']] = data['Account ID']
                else:
                    vertical = Vertical.objects.filter(vertical_id=i['id']).first()
                    if vertical:
                        update_vertical_data.append(
                            Vertical(pk=vertical.id, details=details_json, created_time=i['createdTime']))
            except Exception as e:
                continue

        if new_vertical_data:
            response['new_vertical_data'] = Vertical.objects.bulk_create(new_vertical_data, batch_size=100)
            response['new_vertical_advertiser_obj'] = new_vertical_advertiser_obj
        if update_vertical_data:
            Vertical.objects.bulk_update(update_vertical_data, ['details', 'created_time'], batch_size=100)
        return response

    def save_vertical_advertiser_ids_into_db(self, new_vertical_response, vertical_data):
        new_vertical_advertiser_data = []
        for i in new_vertical_response['new_vertical_data']:
            try:
                if i.vertical_id in list(new_vertical_response['new_vertical_advertiser_obj'].keys()):
                    advertiser_id = new_vertical_response['new_vertical_advertiser_obj'][i.vertical_id]
                    if advertiser_id:
                        advertiser = Advertisers.objects.get(advertiser_id=str(advertiser_id).strip())
                        new_vertical_advertiser_data.append(VerticalAdvertiser(vertical_id=i, advertiser_id=advertiser))
            except:
                continue
        if new_vertical_advertiser_data:
            VerticalAdvertiser.objects.bulk_create(new_vertical_advertiser_data, batch_size=100)
        return True

    def save_revenue_into_reports_db(self, get_system1_revenue_using_domain):
        for i in get_system1_revenue_using_domain:
            try:
                revenue = get_system1_revenue_using_domain[i]
                report = Reports.objects.filter(advertiser_id=i).first()
            except Exception as e:
                continue
