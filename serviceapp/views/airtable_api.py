from pyairtable import Table
from rest_framework.views import APIView
from .system1_api import get_system1_campaign_data
from ..models import *

Search_Arbitrage_Hub_BASE_ID = 'appLB431vvCqF2Hqg'
Accounts_Links_Hub_BASE_ID = 'app8wTJzMsSOYPxiP'
API_KEY = 'keyr6r3tYDGne9P8m'


class AirtableView(APIView):
    @staticmethod
    def get_airtable_data(base_id, table_name, filterValue=None):
        filterValue = filterValue if filterValue else ''
        airtable_data = Table(API_KEY, base_id, table_name).all(formula=[filterValue])
        return airtable_data

    @staticmethod
    def get_airtable_verticals(filterValue=None):
        base_id = Search_Arbitrage_Hub_BASE_ID
        table_name = 'Verticals'
        filterValue = filterValue if filterValue else ''
        verticales_data = AirtableView.get_airtable_data(base_id=base_id, table_name=table_name,
                                                         filterValue=filterValue)
        return verticales_data

    @staticmethod
    def get_airtable_accounts(filterValue=None, base_id=None):
        table_name = 'Accounts'
        filterValue = filterValue if filterValue else ''
        accounts_data = AirtableView.get_airtable_data(base_id=base_id, table_name=table_name,
                                                       filterValue=filterValue)
        return accounts_data

    @staticmethod
    def get_airtable_domains(filterValue=None):
        base_id = Search_Arbitrage_Hub_BASE_ID
        table_name = 'Domains'
        filterValue = filterValue if filterValue else ''
        domains_data = AirtableView.get_airtable_data(base_id=base_id, table_name=table_name,
                                                      filterValue=filterValue)
        return domains_data

    @staticmethod
    def get_airtable_media_buyer_data():
        media_buyer = {}
        # filterValue = "AND(NOT({{Account ID}}=''),DATESTR({{Created}})='{}')".format(date)
        filterValue = "AND(NOT({Account ID}=''),{BC}='PixelMind')"
        accounts_data = AirtableView.get_airtable_accounts(filterValue, Accounts_Links_Hub_BASE_ID)
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

    @staticmethod
    def save_media_buyer_into_db(media_buyer):
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

    @staticmethod
    def save_media_buyer_advertiser_into_db(new_media_buyer_response, media_buyer):
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

    @staticmethod
    def get_airtable_verticals_data():
        filterValue = "NOT({Domains}='')"
        advertiser_ids = {}
        verticals_data = AirtableView.get_airtable_verticals(filterValue)
        for i in AirtableView.get_airtable_accounts(filterValue="AND(NOT({Account ID}=''),{BC}='PixelMind')",
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

    @staticmethod
    def get_airtable_domains_data():
        filterValue = "AND({BC (from Tiktok Account)}='PixelMind',NOT({Account ID (from Accounts)}=''))"
        domains_data = AirtableView.get_airtable_domains(filterValue)
        return domains_data

    @staticmethod
    def get_system1_campaign_revenue(date):
        domains_data = Domains.objects.all().prefetch_related('advertiser_id')
        result = {}
        for i in domains_data:
            data = i
            if data.source == 'System1':
                domain = \
                    data.partner_url.replace('http://', '').replace("/", '').replace(":", "").replace("https",
                                                                                                      "").split(
                        "?rskey")[0]
                advertiser_id = data.advertiser_id.advertiser_id.strip()
                result[domain] = {
                    'advertiser_id': advertiser_id,
                    'domain_id': data.domain_id
                }
        domain_list = list(result.keys())
        campaign = ','.join(domain_list)
        params = {
            'days': date,
            'campaign': campaign
        }
        get_system1_campaign = get_system1_campaign_data(params)
        system1_obj = {}
        for i in get_system1_campaign[1:]:
            domain = i[1]
            if domain:
                revenue = i[12]
                clicks = i[11]
                revenue_per_click = i[16]
                if domain in system1_obj:
                    system1_obj[domain]['revenue'] = system1_obj[domain]['revenue'] + float(revenue)
                    system1_obj[domain]['clicks'] = system1_obj[domain]['clicks'] + clicks
                    system1_obj[domain]['revenue_per_click'] = system1_obj[domain]['revenue_per_click'] + float(
                        revenue_per_click)
                else:
                    system1_obj[domain] = {
                        'report_date': date,
                        'clicks': i[11],
                        'revenue': i[12],
                        'revenue_per_click': i[16],
                    }
        for i in system1_obj:
            try:
                advertiser = result[i]['advertiser_id']
                system1_obj[i]['advertiser_id'] = advertiser
                system1_obj[i]['domain_id'] = result[i]['domain_id']
            except Exception as e:
                continue
        return system1_obj

    @staticmethod
    def save_verticals_data_into_db(vertical_data):
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

    @staticmethod
    def save_vertical_advertiser_ids_into_db(new_vertical_response, vertical_data):
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

    @staticmethod
    def save_revenue_into_reports_db( get_system1_revenue_using_domain):
        for i in get_system1_revenue_using_domain:
            try:
                revenue = get_system1_revenue_using_domain[i]
                report = Reports.objects.filter(advertiser_id=i).first()
            except Exception as e:
                continue

    @staticmethod
    def save_domains_data_into_db(domain_data):
        domains_data_obj = []
        new_domain_data = []
        update_domain_data = []
        domains_ids = []
        for i in domain_data:
            try:
                domains_ids.append(i['id'])
                data = i['fields']
                domains_data_obj.append({
                    'domain_id': i['id'],
                    'account_id': data[
                        "Account ID (from Accounts)"][0].strip() if "Account ID (from Accounts)" in data else None,
                    'domain_for': {'id': data['Domain for']['id'],
                                   'email': data['Domain for']['email'],
                                   'name': data['Domain for']['name']} if 'Domain for' in data else None,
                    'partner_url': data["Partner URL"],
                    'source': data["Source"],
                    'stats': data["Stats"],
                    'pixel_id': data["Pixel ID"] if 'Pixel ID' in data else None,
                    'campaign_name': data["Request ID"].strip() if "Request ID" in data else None,
                    'created_time': data["Created time"]})
            except Exception as e:
                print(e)
                continue

        existence_domains_ids = Domains.objects.values_list('domain_id', flat=True).filter(domain_id__in=domains_ids)
        new_domains_ids = list(set(domains_ids).difference(existence_domains_ids))
        for i in domains_data_obj:
            try:
                data = i
                advertiser = Advertisers.objects.filter(advertiser_id=data['account_id']).first()
                if data['domain_id'] in new_domains_ids and advertiser:
                    new_domain_data.append(
                        Domains(domain_id=data['domain_id'], domain_for=data['domain_for'],
                                advertiser_id=advertiser,
                                partner_url=data['partner_url'],
                                source=data['source'], stats=data['stats'], pixel_id=data['pixel_id'],
                                created_time=data['created_time']))
                else:
                    if advertiser:
                        domain_obj = Domains.objects.filter(domain_id=data['domain_id']).first()
                        update_domain_data.append(
                            Domains(pk=domain_obj.id, advertiser_id=advertiser, domain_for=data['domain_for'],
                                    partner_url=data['partner_url'],
                                    source=data['source'], stats=data['stats'], pixel_id=data['pixel_id'],
                                    created_time=data['created_time']))
            except:
                continue
        if new_domain_data:
            Domains.objects.bulk_create(new_domain_data, batch_size=100)
        if update_domain_data:
            Domains.objects.bulk_update(update_domain_data,
                                        ['advertiser_id', 'domain_for', 'partner_url', 'source', 'stats', 'pixel_id',
                                         'created_time'],
                                        batch_size=100)
        return domains_data_obj

    @staticmethod
    def save_system1_campaign_revenue_into_db(get_system1_revenue_using_domain, date):
        domain_ids = []
        new_domain_advertiser_revenue = []
        update_domain_advertiser_revenue = []
        for i in list(get_system1_revenue_using_domain.values()):
            domain_ids.append(i['domain_id'])
        existence_domains_ids = System1Revenue.objects.values_list('domain_id', flat=True).filter(
            domain_id__in=domain_ids, report_date=date)
        new_domain_ids = list(set(domain_ids).difference(existence_domains_ids))
        for i in list(get_system1_revenue_using_domain.values()):
            try:
                domain_id = i['domain_id']
                if domain_id in new_domain_ids:
                    domain = Domains.objects.filter(domain_id=domain_id).first()
                    advertiser = Advertisers.objects.get(advertiser_id=i['advertiser_id'])
                    if domain and advertiser:
                        new_domain_advertiser_revenue.append(
                            System1Revenue(domain_id=domain, report_date=i['report_date'], clicks=i['clicks'],
                                           revenue=i['revenue'],
                                           revenue_per_click=i['revenue_per_click'], advertiser_id=advertiser))
                else:
                    data = System1Revenue.objects.filter(domain_id=domain_id, report_date=date).first()
                    if data:
                        update_domain_advertiser_revenue.append(
                            System1Revenue(pk=data.id, clicks=i['clicks'],
                                           revenue=i['revenue'],
                                           revenue_per_click=i['revenue_per_click']))
            except:
                continue
        if new_domain_advertiser_revenue:
            rsp = System1Revenue.objects.bulk_create(new_domain_advertiser_revenue, batch_size=1000)
            print(rsp)
        if update_domain_advertiser_revenue:
            rsp = System1Revenue.objects.bulk_update(update_domain_advertiser_revenue,
                                                     ['clicks', 'revenue', 'revenue_per_click'], batch_size=100)
        return True

    @staticmethod
    def save_advertiser_data_campaign_name(domain_data_obj):
        advertiser_list = {}
        update_advertiser_tonic_campaign_name = []
        for i in domain_data_obj:
            advertiser_list[i['account_id']] = i['campaign_name']
        get_advertiser_list = Advertisers.objects.filter(advertiser_id__in=list(advertiser_list.keys()))
        for i in get_advertiser_list:
            update_advertiser_tonic_campaign_name.append(
                Advertisers(pk=i.id, tonic_campaign_name=advertiser_list[i.advertiser_id]))
        if update_advertiser_tonic_campaign_name:
            Advertisers.objects.bulk_update(update_advertiser_tonic_campaign_name, ['tonic_campaign_name'],
                                            batch_size=100)
