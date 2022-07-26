import os
import base64
import json
import requests
import csv
import random

from datetime import datetime
from google.cloud import pubsub_v1, storage
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from config.setting import CRAWLER_ENV, ENV_CONFIG, CMN_CONFIG

credentials = GoogleCredentials.get_application_default()
service = discovery.build('compute', 'v1', credentials=credentials)

# 時間帯によって、稼働対象のzoneを切り替える
ZONE_KEY = datetime.now().strftime('%p')


def setup_topic_list(crawling_setting):
    topic_mapping = {}
    publisher = pubsub_v1.PublisherClient()

    if crawling_setting in CMN_CONFIG.TOPIC_MAPPING:
        key = CMN_CONFIG.TOPIC_MAPPING[crawling_setting]
    else:
        key = "A"

    # 定期実行MSGトピック(1時間に一回)
    topic_mapping['hourly'] = publisher.topic_path(
        CMN_CONFIG.GCP_PROJECT, f"{CRAWLER_ENV}-{CMN_CONFIG.TOPIC_LIST[key]['hourly']}"
    )

    #  不定期実行MSGトピック
    topic_mapping['daily'] = publisher.topic_path(
        CMN_CONFIG.GCP_PROJECT, f"{CRAWLER_ENV}-{CMN_CONFIG.TOPIC_LIST[key]['daily']}"
    )

    return topic_mapping


def read_url_list_by_path(url_list_path):
    """
    URLリスト取得
    """
    url_list = []

    if CRAWLER_ENV == "local":
        url_list_path = f"{ENV_CONFIG.SETTING_BUCKET}{url_list_path}"

        with open(url_list_path, "r") as f:
            reader = csv.reader(f, delimiter=',')
            for line in reader:
                url_list.append(line[0])
    else:
        read_storage_client = storage.Client()
        bucket = read_storage_client.get_bucket(ENV_CONFIG.SETTING_BUCKET)

        blob = bucket.blob(url_list_path)
        url_list_string = blob.download_as_string().decode('utf-8')
        url_list = url_list_string.strip().splitlines()

        print("url_list shuffle start")
        random.shuffle(url_list)
        print("url_list shuffle end")

    print(url_list)
    return url_list


def get_url_list(crawling_setting, mode):

    # 処理間隔別にトピック切り替え
    topic_mapping = setup_topic_list(crawling_setting)

    url_list_array = []

    publisher = pubsub_v1.PublisherClient()
    storage_client = storage.Client()
    for file in storage_client.list_blobs(ENV_CONFIG.SETTING_BUCKET, prefix=f"{crawling_setting}/url_list/{mode}/url_list"):
        print(file)
        url_list_array.append(file.name)

    for url_list_name in url_list_array:
        url_list = read_url_list_by_path(url_list_name)

        mb_target = ""
        if crawling_setting in ENV_CONFIG.MB_TARGET:
            mb_target = "mobile"

        for target_url in url_list:
            data = crawling_setting
            data = data.encode("utf-8")
            future = publisher.publish(
                topic_mapping[mode],
                data,
                url=target_url
            )

            if mb_target != "":
                future = publisher.publish(
                    topic_mapping[mode],
                    data,
                    url=target_url,
                    mb_flg=mb_target
                )

            print(future.result())


def main(event, context):
    if 'data' in event:
        event_data = base64.b64decode(event['data']).decode('utf8')
        setting_list = json.loads(event_data)
    else:
        return "no crawling setting"

    # 対象のurl listファイル群を取得
    mode = "daily"
    if "mode" in setting_list:
        mode = setting_list['mode']

    for crawling_seting in setting_list["crawling_setting"]:
        get_url_list(crawling_seting, mode)

    for zone in ENV_CONFIG.ZONE_LIST[f"{ZONE_KEY}"]:
        # インスタンス起動(停止中かつcrawler-envに設定あるもの)
        request = service.instances().list(
            project=CMN_CONFIG.GCP_PROJECT,
            zone=zone,
            filter=f'(status="TERMINATED") AND (labels.crawler-env="{CRAWLER_ENV}")'
        )
        response = request.execute()
        print(response)

        if 'items' in response:
            print(f"{zone} start crawler instances")
            for item in response["items"]:

                request = service.instances().start(project=CMN_CONFIG.GCP_PROJECT, zone=zone, instance=item["name"])
                response = request.execute()
                print(response)
        else:
            print(f"{zone}: no instance")

    return 'Success'
