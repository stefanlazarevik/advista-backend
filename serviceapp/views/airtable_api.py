from pyairtable import Table
from rest_framework.views import APIView

from .helper import LogHelper
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
        try:
            # filterValue = "AND(NOT({{Account ID}}=''),DATESTR({{Created}})='{}')".format(date)
            # filterValue = "AND(NOT({Account ID}=''),{BC}='PixelMind')"
            accounts_data = AirtableView.get_airtable_accounts(None, Accounts_Links_Hub_BASE_ID)
            for i in accounts_data:
                data = i['fields']
                id = data['Requested by']['id'].strip()
                account_id = data['Account ID'].strip() if 'Account ID' in data else None
                bc = data['BC'] if 'BC' in data else None

                if id in media_buyer:
                    media_buyer[id]['advertiser_ids'].append(account_id)
                    media_buyer[id]['bc'].append(bc)
                else:
                    result = {'media_buyer_id': id,
                              'email': data['Requested by']['email'].strip(),
                              'name': data['Requested by']['name'].strip(), 'advertiser_ids': [account_id], 'bc': [bc]}
                    media_buyer[id] = result
                media_buyer[id]['bc'] = list(set(media_buyer[id]['bc']))
        except Exception as e:
            LogHelper.efail(e)
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
        print("new_media_buyer_ids", len(new_media_buyer_ids))
        for i in media_buyer:
            try:
                data = media_buyer[i]
                id = data['media_buyer_id']
                if id in new_media_buyer_ids:
                    create_media_buyer.append(
                        MediaBuyer(media_buyer_id=data['media_buyer_id'], email=data['email'],
                                   name=data['name'], bc=data['bc']))
                else:
                    media_buyer_obj = MediaBuyer.objects.get(media_buyer_id=data['media_buyer_id'])
                    update_media_buyer.append(
                        MediaBuyer(pk=media_buyer_obj.id, email=data['email'], name=data['name'], bc=data['bc']))
            except Exception as e:
                LogHelper.efail(e)
                continue
        if create_media_buyer:
            rsp = MediaBuyer.objects.bulk_create(create_media_buyer, batch_size=100)
        if update_media_buyer:
            MediaBuyer.objects.bulk_update(update_media_buyer, ['email', 'name', 'bc'],
                                           batch_size=100)
        return response

    @staticmethod
    def save_media_buyer_advertiser_into_db(media_buyer):
        new_ids = []
        account_id_list = [i['advertiser_ids'] for i in media_buyer.values()]
        for i in account_id_list:
            media_buyer_accounts_ids = MediaBuyerAdvertiser.objects.filter(advertiser_id__in=i).values_list(
                'advertiser_id', flat=True)
            new_media_buyer_accounts_ids = list(set(i).difference(media_buyer_accounts_ids))
            print("new_media_buyer_accounts_ids", len(new_media_buyer_accounts_ids))
            for id in new_media_buyer_accounts_ids:
                new_ids.append(id)
        print(len(new_ids))
        new_media_buyer_advertiser = []
        update_media_buyer_advertiser = []
        for i in media_buyer:
            try:
                data = media_buyer[i]
                media_buyer_id = data['media_buyer_id']
                account_ids = data['advertiser_ids']
                for id in account_ids:
                    advertiser_obj = Advertisers.objects.filter(advertiser_id=id).first()
                    media_buyer_obj = MediaBuyer.objects.filter(media_buyer_id=media_buyer_id).first()
                    if advertiser_obj:
                        if id in new_ids:
                            new_media_buyer_advertiser.append(
                                MediaBuyerAdvertiser(media_buyer_id=media_buyer_obj, advertiser_id=advertiser_obj))
                        else:
                            if media_buyer:
                                update_media_buyer_advertiser.append(
                                    MediaBuyerAdvertiser(pk=media_buyer_obj.id, advertiser_id=advertiser_obj))
            except Exception as e:
                LogHelper.efail(e)
                continue
        print('new_media_buyer_advertiser_size--->', len(new_media_buyer_advertiser))
        if new_media_buyer_advertiser:
            MediaBuyerAdvertiser.objects.bulk_create(new_media_buyer_advertiser, batch_size=1000)
        print('update_media_buyer_advertiser_size--->', len(update_media_buyer_advertiser))
        if update_media_buyer_advertiser:
            MediaBuyerAdvertiser.objects.bulk_update(update_media_buyer_advertiser, ['advertiser_id'],
                                                             batch_size=1000)
        return True

    @staticmethod
    def get_airtable_verticals_data():
        # filterValue = "NOT({Domains}='')"
        advertiser_ids = {}
        count = 0
        verticals_data = AirtableView.get_airtable_verticals()
        print("verticals_data-size", len(verticals_data))
        for i in AirtableView.get_airtable_accounts(filterValue="AND(NOT({Account ID}=''))",
                                                    base_id=Search_Arbitrage_Hub_BASE_ID):
            data = i['fields']
            if 'Domains' in data:
                for domain in data['Domains']:
                    advertiser_ids[domain] = {'account_id': data['Account ID'].strip(), 'bc': data['BC']}
        for i in verticals_data:
            data = i['fields']
            if 'Domains' in data:
                for domain in data['Domains']:
                    try:
                        if 'Account ID' in data:
                            data['Account ID'].append(advertiser_ids[domain]['account_id'])
                        else:
                            data['Account ID'] = [advertiser_ids[domain]['account_id']]
                        if 'BC' in data:
                            data['BC'].append(advertiser_ids[domain]['bc'])
                        else:
                            data['BC'] = [advertiser_ids[domain]['bc']]
                    except Exception as e:
                        continue
        return verticals_data

    @staticmethod
    def get_airtable_domains_data():
        # filterValue = "AND({BC (from Tiktok Account)}='PixelMind',NOT({Account ID (from Accounts)}=''))"
        # domains_data = AirtableView.get_airtable_domains(filterValue)
        domains_data = AirtableView.get_airtable_domains()
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
        print("new_vertical_data_list---size------->", len(new_vertical_data_list))
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
                bc = data['BC'] if 'BC' in data else None
                if i['id'] in new_vertical_data_list:
                    new_vertical_data.append(
                        Vertical(vertical_id=i['id'], details=details_json, bc=bc, created_time=i['createdTime']))
                    if 'Account ID' in data:
                        new_vertical_advertiser_obj[i['id']] = data['Account ID']
                else:
                    vertical = Vertical.objects.filter(vertical_id=i['id']).first()
                    if vertical:
                        update_vertical_data.append(
                            Vertical(pk=vertical.id, details=details_json, bc=bc, created_time=i['createdTime']))
            except Exception as e:
                print(e)
                continue
        if new_vertical_data:
            print("new_vertical_data-size--->", len(new_vertical_data))
            response['new_vertical_data'] = Vertical.objects.bulk_create(new_vertical_data, batch_size=100)
            response['new_vertical_advertiser_obj'] = new_vertical_advertiser_obj
        if update_vertical_data:
            print("update_vertical_data-size--->", len(update_vertical_data))
            Vertical.objects.bulk_update(update_vertical_data, ['details', 'bc', 'created_time'], batch_size=100)
        return response

    @staticmethod
    def save_vertical_advertiser_ids_into_db(new_vertical_response, vertical_data):
        new_vertical_advertiser_data = []
        for i in new_vertical_response['new_vertical_data']:
            try:
                if i.vertical_id in list(new_vertical_response['new_vertical_advertiser_obj'].keys()):
                    advertiser_ids = new_vertical_response['new_vertical_advertiser_obj'][i.vertical_id]
                    for advertiser_id in advertiser_ids:
                        advertiser = Advertisers.objects.filter(advertiser_id=str(advertiser_id).strip()).first()
                        if advertiser:
                            new_vertical_advertiser_data.append(
                                VerticalAdvertiser(vertical_id=i, advertiser_id=advertiser))
                        else:
                            new_vertical_advertiser_data.append(
                                VerticalAdvertiser(vertical_id=i, advertiser_id=advertiser))
            except Exception as e:
                continue
        if new_vertical_advertiser_data:
            VerticalAdvertiser.objects.bulk_create(new_vertical_advertiser_data, batch_size=100)
        return True

    @staticmethod
    def save_revenue_into_reports_db(get_system1_revenue_using_domain):
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
                    'partner_url': data["Partner URL"] if "Partner URL" in data else None,
                    'source': data["Source"] if "Source" in data else None,
                    'stats': data["Stats"] if "Stats" in data else None,
                    'pixel_id': data["Pixel ID"] if 'Pixel ID' in data else None,
                    'country': data['Country'] if "Country" in data else None,
                    'creative_text': data['Creative Text'] if "Creative Text" in data else None,
                    'create_video': {'id': data['Creative Video'][0]['id'], 'url': data['Creative Video'][0]['url'],
                                     'filename': data['Creative Video'][0]['filename'],
                                     'size': data['Creative Video'][0]['size'],
                                     'type': data['Creative Video'][0]['type'],
                                     } if "Creative Video" in data else None,
                    'language': data['Language'] if "Language" in data else None,
                    'network': data['Network'] if "Network" in data else None,
                    'tracker_url': data['Tracker URL'] if "Tracker URL" in data else None,
                    'ticket_no': data['Ticket #'] if 'Ticket #' in data else None,
                    'tiktok_account': data['Tiktok Account'] if "Tiktok Account" in data else None,
                    'type': data['Type'] if "Type" in data else None,
                    'request_id': data["Request ID"].strip() if "Request ID" in data else None,
                    'category': data['Category'] if "Category" in data else None,
                    'create_pixel': {'label': data["Create Pixel"]["label"],
                                     'url': data["Create Pixel"]["url"]} if "Create Pixel" in data else None,
                    'status': data['Status (from Accounts)'] if "Status (from Accounts)" in data else None,
                    'open_account': data[
                        'Open Account (from Accounts)'] if "Open Account (from Accounts)" in data else None,
                    'account_button': data['Account Button'] if "Account Button" in data else None,
                    'pixel_fire': {'label': data["Pixel Fire"]["label"],
                                   'url': data["Pixel Fire"]["url"]} if "Pixel Fire" in data else None,
                    'bc': data['BC (from Tiktok Account)'] if "BC (from Tiktok Account)" in data else None,
                    'vertical_name': data['Vertical Name'] if "Vertical Name" in data else None,
                    'name': data['Name (from Tiktok Account)'] if "Name (from Tiktok Account)" in data else None,
                    'created_time': data["Created time"]})
            except Exception as e:
                print(e)
                continue
        print("total-size-->", len(domains_data_obj))
        existence_domains_ids = Domains.objects.values_list('domain_id', flat=True).filter(domain_id__in=domains_ids)
        new_domains_ids = list(set(domains_ids).difference(existence_domains_ids))
        print("new_domains_ids_size-->", len(new_domains_ids))

        for i in domains_data_obj:
            try:
                data = i
                domain_id = data['domain_id']
                advertiser = Advertisers.objects.filter(advertiser_id=data['account_id']).first()
                if domain_id in new_domains_ids:
                    new_domain_data.append(
                        Domains(domain_id=data['domain_id'], advertiser_id=advertiser if advertiser else None,
                                domain_for=data['domain_for'],
                                partner_url=data['partner_url'],
                                source=data['source'], stats=data['stats'], pixel_id=data['pixel_id'],
                                country=data['country'], creative_text=['creative_text'],
                                creative_video=data['create_video'],
                                language=data['language'], network=data['network'], tracker_url=data['tracker_url'],
                                ticket_no=data['ticket_no'], tiktok_account=data['tiktok_account'], type=['type'],
                                request_id=data['request_id'], category=data['category'],
                                create_pixel=data['create_pixel'], status=data['status'],
                                open_account=data['open_account'], account_button=data['account_button'],
                                pixel_fire=data['pixel_fire'], bc=data['bc'], vertical_name=data['vertical_name'],
                                name=data['name'],
                                created_time=data['created_time']))
                else:
                    domain_obj = Domains.objects.filter(domain_id=domain_id).first()
                    update_domain_data.append(
                        Domains(pk=domain_obj.id, advertiser_id=advertiser if advertiser else None,
                                domain_for=data['domain_for'],
                                partner_url=data['partner_url'],
                                source=data['source'], stats=data['stats'], pixel_id=data['pixel_id'],
                                country=data['country'], creative_text=['creative_text'],
                                creative_video=data['create_video'],
                                language=data['language'], network=data['network'], tracker_url=data['tracker_url'],
                                ticket_no=data['ticket_no'], tiktok_account=data['tiktok_account'], type=['type'],
                                request_id=data['request_id'], category=data['category'],
                                create_pixel=data['create_pixel'], status=data['status'],
                                open_account=data['open_account'], account_button=data['account_button'],
                                pixel_fire=data['pixel_fire'], bc=data['bc'], vertical_name=data['vertical_name'],
                                name=data['name'],
                                created_time=data['created_time']))
            except Exception as e:
                continue
        if new_domain_data:
            print("new_domain_data-->", len(new_domain_data))
            Domains.objects.bulk_create(new_domain_data, batch_size=100)
        if update_domain_data:
            print("update_domain_data-->", len(update_domain_data))
            Domains.objects.bulk_update(update_domain_data,
                                        ['advertiser_id', 'domain_for', 'partner_url', 'source', 'stats',
                                         'pixel_id', 'country', 'creative_text', 'creative_video', 'language',
                                         'network', 'tracker_url', 'ticket_no', 'tiktok_account', 'type',
                                         'request_id',
                                         'category', 'create_pixel', 'status', 'open_account', 'account_button',
                                         'pixel_fire', 'bc', 'vertical_name', 'name',
                                         'created_time'],
                                        batch_size=200)
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
        print("domain_ids-size--->", len(domain_ids))
        print("domain_ids-size--->", len(set(domain_ids)))
        # new_domain_ids = list(set(domain_ids).difference(existence_domains_ids))
        # print("domain_ids--->", len(new_domain_ids))
        for i in list(get_system1_revenue_using_domain.values()):
            try:
                domain_id = i['domain_id']
                if domain_id in existence_domains_ids:
                    data = System1Revenue.objects.filter(domain_id=domain_id, report_date=date).first()
                    advertiser = Advertisers.objects.filter(advertiser_id=i['advertiser_id']).first()
                    if data:
                        update_domain_advertiser_revenue.append(
                            System1Revenue(pk=data.id, campaign=i['campaign'], total_sessions=i['total_sessions'],
                                           mobile_sessions=i['mobile_sessions'], desktop_sessions=i['desktop_sessions'],
                                           mobile_sessions_percentage=i['mobile_sessions_percentage'],
                                           distinct_ip=i['distinct_ip'],
                                           distinct_mobile_ip=i['distinct_mobile_ip'],
                                           distinct_desktop_ip=i['distinct_desktop_ip'],
                                           distinct_mobile_ip_percentage=i['distinct_mobile_ip_percentage'],
                                           searches=i['searches'],
                                           clicks=i['clicks'],
                                           revenue=i['revenue'],
                                           revenue_per_session=i['revenue_per_session'],
                                           revenue_per_search=i['revenue_per_search'],
                                           revenue_per_ip=i['revenue_per_ip'],
                                           revenue_per_click=i['revenue_per_click'],
                                           click_per_session_percentage=i['click_per_session_percentage'],
                                           advertiser_id=advertiser
                                           ))
                else:
                    domain = Domains.objects.filter(domain_id=domain_id).first()
                    advertiser = Advertisers.objects.filter(advertiser_id=i['advertiser_id']).first()
                    new_domain_advertiser_revenue.append(
                        System1Revenue(domain_id=domain, report_date=i['report_date'], campaign=i['campaign'],
                                       total_sessions=i['total_sessions'],
                                       mobile_sessions=i['mobile_sessions'], desktop_sessions=i['desktop_sessions'],
                                       mobile_sessions_percentage=i['mobile_sessions_percentage'],
                                       distinct_ip=i['distinct_ip'],
                                       distinct_mobile_ip=i['distinct_mobile_ip'],
                                       distinct_desktop_ip=i['distinct_desktop_ip'],
                                       distinct_mobile_ip_percentage=i['distinct_mobile_ip_percentage'],
                                       searches=i['searches'],
                                       clicks=i['clicks'],
                                       revenue=i['revenue'],
                                       revenue_per_session=i['revenue_per_session'],
                                       revenue_per_search=i['revenue_per_search'],
                                       revenue_per_ip=i['revenue_per_ip'],
                                       revenue_per_click=i['revenue_per_click'],
                                       click_per_session_percentage=i['click_per_session_percentage'],
                                       advertiser_id=advertiser
                                       ))
            except Exception as e:
                print("error-->", e)
                continue
        print("new-revenue--->", len(new_domain_advertiser_revenue))
        print("update-revenue--->", len(update_domain_advertiser_revenue))
        if new_domain_advertiser_revenue:
            rsp = System1Revenue.objects.bulk_create(new_domain_advertiser_revenue, batch_size=1000)
        if update_domain_advertiser_revenue:
            rsp = System1Revenue.objects.bulk_update(update_domain_advertiser_revenue,
                                                     ['campaign', 'total_sessions', 'mobile_sessions',
                                                      'desktop_sessions', 'mobile_sessions_percentage', 'distinct_ip',
                                                      'distinct_mobile_ip', 'distinct_desktop_ip',
                                                      'distinct_mobile_ip_percentage', 'searches', 'clicks', 'revenue',
                                                      'revenue_per_session', 'revenue_per_search', 'revenue_per_ip',
                                                      'revenue_per_click', 'click_per_session_percentage',
                                                      'advertiser_id'], batch_size=100)

        return True

    @staticmethod
    def save_advertiser_data_campaign_name(domain_data_obj):
        advertiser_list = {}
        update_advertiser_tonic_campaign_name = []
        for i in domain_data_obj:
            advertiser_list[i['account_id']] = i['request_id']
        get_advertiser_list = Advertisers.objects.filter(advertiser_id__in=list(advertiser_list.keys()))
        for i in get_advertiser_list:
            update_advertiser_tonic_campaign_name.append(
                Advertisers(pk=i.id, tonic_campaign_name=advertiser_list[i.advertiser_id]))
        if update_advertiser_tonic_campaign_name:
            Advertisers.objects.bulk_update(update_advertiser_tonic_campaign_name, ['tonic_campaign_name'],
                                            batch_size=100)
