import os
import base64
import json
import datetime
import requests

from importlib import import_module
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
from google.cloud import bigquery


credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)

CMN_CONFIG = import_module("config.common")

# env
CRAWLER_ENV = os.environ.get('CRAWLER_ENV', 'local')


def regist_crawler_ip_history(setting_list):
    print("use ip regist START")

    # 割り当てられていたipを記録
    request = service.instances().get(
        project=CMN_CONFIG.GCP_PROJECT,
        zone=setting_list["vm_zone"],
        instance=setting_list["host_name"]
    )
    response = request.execute()

    if "networkInterfaces" in response:
        network_if_info = response["networkInterfaces"][0]
        access_config = network_if_info["accessConfigs"][0]

        print(access_config)
        if "natIP" in access_config:
            use_ip = access_config["natIP"]
            print(use_ip)

            # bigqueryで利用するテーブル [project ID].[データセット名].[テーブル名]
            table_name = f"{CMN_CONFIG.GCP_PROJECT}.{CRAWLER_ENV}_{CMN_CONFIG.DATA_SET}.crawler_ip_history"
            bigquery_client = bigquery.Client()

            # json形式でデータを登録
            insert_row = [
                {
                    u"crawl_started_at": datetime.datetime.now().strftime('%Y-%m-%d %H:00:00'),
                    u"host_name": setting_list["host_name"],
                    u"zone": setting_list["vm_zone"],
                    u"ip": use_ip,
                    u"status": setting_list["status"],
                    u"created_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            ]

            errors = bigquery_client.insert_rows_json(table_name, insert_row)
            if errors == []:
                print("New rows have been added.")
            else:
                print("Encountered errors while inserting rows: {}".format(errors))
        else:
            print("no ip")

    print("use ip regist END")
    return


def main(event, context):
    if 'data' in event:
        event_data = base64.b64decode(event['data']).decode('utf8')
        setting_list = json.loads(event_data)
    else:
        return "undefined msg"

    # 利用ip履歴登録
    regist_crawler_ip_history(setting_list)
    return 'Success'
