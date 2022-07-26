import json

from google.cloud import pubsub_v1
from config.setting import GCP_ENV, CMN_CONFIG, TABLE_LIST

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(CMN_CONFIG.GCP_PROJECT, f"{GCP_ENV}-{CMN_CONFIG.SYMC_ADMIN_TOPIC}")


def publish_msg(msg_body):

    data = json.dumps(msg_body)
    data = data.encode("utf-8")
    future = publisher.publish(
        topic_path,
        data
    )
    print(future.result())


# デフォルト処理msgをpublish
def main(event, context):

    for target_report in TABLE_LIST:
        msg_body = {
            "target_report": target_report
        }
        publish_msg(msg_body)
