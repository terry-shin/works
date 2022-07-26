import time
import pandas

import usrlib.scraping.amazon_category_rank_xpath as amazon_category_rank_xpath
import usrlib.utils.scraping_utils as scraping_utils

from io import BytesIO
from selenium.webdriver.common.by import By
from datetime import datetime
from google.cloud import bigquery, storage
from config.setting import CRAWLER_ENV, CMN_CONFIG, ENV_CONFIG

# 取得する件数
GET_RANKING_NUM = 100

# crawl対象asinリスト
target_asin_list = []


def fetch_ranking_products(driver, xpath_setting):
    rank_product_list = []
    data_count = 0

    driver = scroll_browser(driver)

    for ranking_item_xpath in xpath_setting.ranking_item_xpath_list:
        data_count += 1
        ranking_items = driver.find_elements(by=By.XPATH, value=ranking_item_xpath)
        if len(ranking_items) <= 0:
            continue

        for item in ranking_items:
            rank_product = {
                "rank": 0,
                "asin": "",
                "product_name": ""
            }

            # ランキング取得
            for rank_xpath in xpath_setting.rank_xpath_list:
                rank_elements = item.find_elements(by=By.XPATH, value=rank_xpath)
                if len(rank_elements) > 0:
                    rank_product["rank"] = int(rank_elements[0].text.replace('#', ''))

            # asin取得
            for url_xpath in xpath_setting.url_xpath_list:
                asin_elements = item.find_elements(by=By.XPATH, value=url_xpath)
                if len(asin_elements) > 0:
                    target_url = asin_elements[0].get_attribute('href')
                    rank_product["asin"] = scraping_utils.fetch_asin_from_url(target_url)

            # タイトル取得
            for title_xpath in xpath_setting.title_xpath_list:
                title_elements = item.find_elements(by=By.XPATH, value=title_xpath)
                if len(title_elements) > 0:
                    rank_product["product_name"] = title_elements[0].text

            if rank_product["rank"] and rank_product["asin"] and rank_product["product_name"]:
                rank_product_list.append(rank_product)

    return rank_product_list


# ランキングが全部表示されるまでスクロール
def scroll_browser(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height

    return driver


def scroll_by_elem_and_offset(driver, element, offset=0):

    driver.execute_script("arguments[0].scrollIntoView();", element)

    if (offset != 0):
        script = "window.scrollTo(0, window.pageYOffset + " + str(offset) + ");"
        driver.execute_script(script)


# 改ページ処理
def click_pagenation(driver):
    pagination_element = driver.find_elements(by=By.XPATH, value="//ul[@class='a-pagination']//li[@class='a-last']/a")

    if len(pagination_element) > 0:
        scroll_by_elem_and_offset(driver, pagination_element[0], -10)

    if len(pagination_element) > 0:
        print("move next result")
        pagination_element[0].click()
        time.sleep(10)
        return True
    else:
        print("no pagination")
        return False


# urlからカテゴリを特定する
def get_url_info(target_url):

    url_info = {
        "url": target_url,
        "first_category": "",
        "second_category": ""
    }

    if CRAWLER_ENV == "local":
        category_list = pandas.read_csv(
            f"{ENV_CONFIG.SETTING_BUCKET}amazon_category_rank/category_master.csv", encoding="utf_8"
        )

    else:
        bucket_name = f"{CRAWLER_ENV}-crawler-setting-bucket"
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(bucket_name)

        blob = bucket.blob("amazon_category_rank/category_master.csv")
        category_master_string = blob.download_as_string()

        category_list = pandas.read_csv(BytesIO(category_master_string))

    query_result = category_list.query(f'url=="{target_url}"').to_dict()
    if len(query_result) > 0:
        for id in query_result['first_category'].keys():
            url_info['first_category'] = query_result['first_category'][id]
            url_info['second_category'] = query_result['second_category'][id]

    return url_info


def register_data(url_info, crawl_started_at, rank_product_list):
    table_name = "{}.{}_{}.amazon_category_rank".format(
        CMN_CONFIG.GCP_PROJECT,
        CRAWLER_ENV,
        CMN_CONFIG.DATA_SET
    )
    bigquery_client = bigquery.Client()

    for rank_product in rank_product_list:
        current_datetime = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")

        target_asin = ""

        try:
            insert_row = [
                {
                    u"first_category": f"{url_info['first_category']}",
                    u"second_category": f"{url_info['second_category']}",
                    u"ranking": f"{rank_product['rank']}",
                    u"asin": f"{rank_product['asin']}",
                    u"url": f"{url_info['url']}",
                    u"product_name": f"{rank_product['product_name']}",
                    u"crawl_started_at": f"{crawl_started_at}",
                    u"created_at": f"{current_datetime}"
                }
            ]
            print(insert_row)
            # 登録成功時にasinの製品情報の取得対象とする
            target_asin = rank_product['asin']
        except Exception as e:
            print(f"regist error:{e}")

        errors = bigquery_client.insert_rows_json(table_name, insert_row)
        if errors == []:
            print("New rows have been added.")

            # 登録成功時、asin設定あればクローリング対象とする
            if len(target_asin) > 0 and target_asin not in target_asin_list:
                target_asin_list.append(target_asin)

        else:
            print("Encountered errors while inserting rows: {}".format(errors))
    # 重複ASINを除外して、対象に追加
    scraping_utils.publish_keepa_call_product(list(set(target_asin_list)))


def scraping_main(target_url, driver, crawl_started_at):
    print("------amazon ranking page scraping function START------")
    rank_product_list = []
    target_asin_list.clear()

    while len(rank_product_list) < GET_RANKING_NUM:
        rank_product_list += fetch_ranking_products(
            driver,
            amazon_category_rank_xpath
        )

        if len(rank_product_list) >= GET_RANKING_NUM or not click_pagenation(driver):
            break

    if len(rank_product_list) > 0:
        # urlからカテゴリ情報を取得する
        url_info = get_url_info(target_url)
        register_data(url_info, crawl_started_at, rank_product_list)
        return f"{url_info['first_category']}:{url_info['second_category']}"

    print("------amazon ranking page scraping function END------")
    return
