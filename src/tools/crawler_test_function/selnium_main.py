import os
import random

from usrlib.scraping import amazon_ads_rank_scraping

from datetime import datetime, timedelta, timezone
from unicodedata import name
from bs4 import BeautifulSoup

from google.cloud import storage
from fake_useragent import UserAgent
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from usrlib.logger import crawler_logger

JST = timezone(timedelta(hours=+9), 'JST')
crawl_started_at = datetime.now(JST).strftime('%Y-%m-%d %H:00:00')
EXEC_AMPM = datetime.now(JST).strftime('%p')

logger = crawler_logger.get_module_logger(__name__)


USER_AGEMT = [
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
]

tmp_file_path = "/tmp/"

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
        f"{save_file['path']}{save_file['file_name']}.html"
    )
    blob.upload_from_filename(temp_file)

    os.remove(temp_file)

    return


def crawler(request):

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # ヘッドレスで起動
    options.add_argument('--disable-gpu')   # ヘッドレスモードで起動するときに必要
    options.add_argument('--no-sandbox')  # 仮想環境下では、sandboxで起動すると失敗するので無効にする
    options.add_argument('--disable-extensions')  # extensionの利用をしない
    options.add_argument("--proxy-server='direct://'")  # Proxy経由ではなく直接接続する
    options.add_argument('--proxy-bypass-list=*')
    options.add_argument('--disable-dev-shm-usage')  # メモリファイルでshm利用しない様にする
    options.add_argument('--disable-application-cache')  # HTML5のApp Cacheを無効。
    options.add_argument('--hide-scrollbars')  # スクロールバーを隠す
    options.add_argument('--enable-logging')  # console.log　保存用
    options.add_argument('--log-level=0')
    options.add_argument('--v=99')
    options.add_argument('--ignore-certificate-errors')  # SSLセキュリティ証明書のエラーページ非表示
    options.add_argument('--incognito')  # シークレット モードincognito.gifで起動
    options.add_argument('--lang=ja-JP')

    options.add_argument('--window-size=1280,1024')  # 画面サイズの指定
    options.add_argument(f'user-agent={USER_AGEMT[random.randint(0, 1)]}')
    options.add_argument('sec-ch-ua=" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"')

    # ip block対策検証
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})

    options.binary_location = os.getcwd() + "/bin/headless-chromium"
    driver = webdriver.Chrome(
        os.getcwd() + "/bin/chromedriver", chrome_options=options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    driver.get(target_url)
    logger.debug(target_url)
    line = driver.title

    target_html = driver.page_source
    save_file_name = f"{os.environ.get('REGION', default='default')}_test_{target}"
    save_html({"file_name": save_file_name, "path": ""}, target_html)

    driver.get(access_check_target_url)
    logger.debug(access_check_target_url)
    line = driver.title

    target_html = driver.page_source
    save_file_name = f"{os.environ.get('REGION', default='default')}_test_{access_check_target}"
    save_html({"file_name": save_file_name, "path": ""}, target_html)
    driver.quit()
    return "OK"

    '''
    # dailyの場合はクロール時間補正
    # 午前午後、1−3時間かけて１回ずつ稼働。その為、午前午後でのクロール時間を統一する。
    if EXEC_AMPM == "AM":
        crawl_hour = "10"
    elif EXEC_AMPM == "PM":
        crawl_hour = "18"
    else:
        crawl_hour = "%H"
    target_crawl_started_at = datetime.now().strftime(f'%Y-%m-%d {crawl_hour}:00:00')
    target_keyword = amazon_ads_rank_scraping.scraping_main(target_url, driver, target_crawl_started_at)

    driver.quit()

    return f"{line}:{target_keyword}"
    '''
