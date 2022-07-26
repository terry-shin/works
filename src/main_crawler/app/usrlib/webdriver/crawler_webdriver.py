import os
import random

from config.setting import CRAWLER_ENV, CMN_CONFIG

# web driver
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome import service as fs

# gcp service
from google.cloud import storage


def setting_webdriver(mb_flg=""):
    """
    selnium set up
    """
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

    if not mb_flg:
        options.add_argument('--window-size=1280,1024')  # 画面サイズの指定
        options.add_argument(f'user-agent={CMN_CONFIG.USER_AGEMT[random.randint(0, 1)]}')
    else:
        # mobile mode
        options.add_argument('--window-size=375,812')  # 画面サイズの指定
        mobile_emulation = {"deviceName": "iPhone X"}
        options.add_experimental_option("mobileEmulation", mobile_emulation)

    options.add_argument('sec-ch-ua=" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"')

    # ip block対策検証
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('prefs', {'intl.accept_languages': 'ja'})

    chrome_service = fs.Service(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def save_html(save_file, html):
    """
    save html to CloudStrage
    """
    print(f"save html START:{save_file['file_name']}")
    temp_file = f"/usr/local/src/works/src/main_crawler/app/tmp/{save_file['file_name']}.html"

    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(html)

    if CRAWLER_ENV != "local":

        storage_client = storage.Client()
        myBucket = storage_client.bucket(f"{CRAWLER_ENV}-{CMN_CONFIG.HTML_BUCKET}")

        blob = myBucket.blob(
            f"{save_file['path']}{save_file['file_name']}.html"
        )
        blob.upload_from_filename(temp_file)

        os.remove(temp_file)

    print("save html END")
    return
