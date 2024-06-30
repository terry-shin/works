import re
import json

from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

from google.cloud import pubsub_v1
from config.setting import CRAWLER_ENV, CMN_CONFIG


def fetch_keyword_from_url(url: str):
    """URLからキーワードを取得する
    Args:
        url (str):
            ターゲットURL
    Returns:
        str: URLクエリに含まれるキーワード
    """
    qs = urlparse(url).query
    qs_dict = parse_qs(qs)

    if "k" in qs_dict:
        return qs_dict["k"][0].strip()
    else:
        print("no keyword")
        return


def fetch_asin_from_url(url: str):
    """URLからASINを取得する
    Args:
        url (str):
            decodeされたURL
    Returns:
        str: URLに含まれるASIN
    """
    regex_pattern = r"/dp/([0-9a-zA-Z]+)"
    matched_obj = re.search(regex_pattern, url)
    if matched_obj is None:
        crawl_asin = ""
        print("asin was not found:" + url)
    else:
        crawl_asin = matched_obj.group().replace("/dp/", "").strip()
    return crawl_asin


def publish_keepa_call_product(asin_list):
    """
    keepa api:productに問い合わせるmsgを作成
    Args:
        asin_list (list):
            取得したASINのリスト
    Returns:
        pub/subメッセージ送信
    """
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(CMN_CONFIG.GCP_PROJECT, f"{CRAWLER_ENV}-keepa_admin")

    now = datetime.now()
    check_datetime = now - timedelta(days=7)

    data = "product"
    data = data.encode("utf-8")

    # 広告枠に表示されているASINをproductのクローラー対象としてMSG送信
    for target_asin in asin_list:
        param_list = {
            "api": "product",
            "asin": [target_asin]
        }
        param_str = json.dumps(param_list)

        future = publisher.publish(
            topic_path,
            param_str.encode("utf-8")
        )
        print(future.result())

    return
