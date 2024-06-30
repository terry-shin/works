import os
import random
import time

from datetime import datetime
from unicodedata import name
from bs4 import BeautifulSoup

from google.cloud import storage


USER_AGEMT = [
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
]

tmp_file_path = '/tmp/'

# プロキシテスト
PROXY ='zproxy.lum-superproxy.io:22225' 
PROXY_AUTH = 'brd-customer-c_736b5137-zone-ecpf_test-country-jp:gc3dyp1y4clq'

access_check_target_url = 'https://asia-northeast1-ecpf-301506.cloudfunctions.net/crawler_access_checker'
access_check_target = 'アクセスチェック'

target_url = 'https://www.amazon.co.jp/s?k=%E3%83%93%E3%83%BC%E3%83%AB'
target = 'ビール'


def save_html(save_file, html):
    """
    save html to CloudStrage
    """
    temp_file = f"{tmp_file_path}{datetime.now()}.html"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(html)

    storage_client = storage.Client()
    myBucket = storage_client.bucket("mori-test-bucket")

    blob = myBucket.blob(
        f"{save_file['path']}{save_file['file_name']}_{datetime.now()}.html"
    )
    blob.upload_from_filename(temp_file)

    os.remove(temp_file)

    return


def crawler(request):

    import urllib.request

    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler(
            {'http': f'{PROXY_AUTH}@{PROXY}',
            'https': f'{PROXY_AUTH}@{PROXY}'}))
    opener.addheaders = [("User-Agent", USER_AGEMT[random.randint(0, 1)])]

    # 検証用
    html = opener.open(access_check_target_url).read().decode('utf-8')
    save_file_name = f"proxy_{os.environ.get('REGION', default='default')}_test_{access_check_target}"
    save_html({"file_name": save_file_name, "path": ""}, html)

    html = opener.open(target_url).read().decode('utf-8')
    time.sleep(5)
    save_file_name = f"proxy_{os.environ.get('REGION', default='default')}_test_{target}"
    save_html({"file_name": save_file_name, "path": ""}, html)


    return f"{target} :END"

