import time

import urllib.parse as urlparse
import usrlib.scraping.amazon_organic_rank_xpath as amazon_organic_rank_xpath
import usrlib.utils.scraping_utils as scraping_utils

from datetime import datetime
from google.cloud import bigquery
from config.setting import CRAWLER_ENV, CMN_CONFIG
from selenium.webdriver.common.by import By

# 取得する件数
GET_RANKING_NUM = 100

# crawl対象asinリスト
target_asin_list = []


def scraping_main(target_url, driver, crawl_started_at):
    print("------kwsearch search page scraping function START------")
    print("[kwsearch ranking scraping START]")
    kwsearch_ranking_list = []
    target_asin_list.clear()

    while len(kwsearch_ranking_list) < GET_RANKING_NUM:
        kwsearch_ranking_list += fetch_product_ranking(
            driver,
            len(kwsearch_ranking_list)
        )

        i = len(kwsearch_ranking_list)
        print(f"now ranking count:{i}")

        if len(kwsearch_ranking_list) < GET_RANKING_NUM:
            # 次ページリンクのチェック
            print("check1 pagination")
            pagination_element = driver.find_elements(by=By.XPATH, value=amazon_organic_rank_xpath.pagination_xpath[0])

            if len(pagination_element) <= 0:
                print("check2 pagination")
                pagination_element = driver.find_elements_by_partial_link_text("次へ")

            elm_cnt = len(pagination_element)
            print(f"pagination：{elm_cnt}")

            if len(pagination_element) > 0:
                print("move next result")
                pagination_element[0].click()
                time.sleep(10)
            else:
                print("no pagination")
                break

    crawl_keyword = ""
    if len(kwsearch_ranking_list) > 0:
        crawl_keyword = scraping_utils.fetch_keyword_from_url(urlparse.unquote(target_url))
        register_data(crawl_keyword, crawl_started_at, kwsearch_ranking_list)

    print(f"[kwsearch ranking:{crawl_keyword} scraping END]")
    print("------kwsearch search page scraping function END------")
    return crawl_keyword


def fetch_product_ranking(driver, now_rank):
    rank_product_list = []
    ranking = now_rank

    for rank_xpath in amazon_organic_rank_xpath.ranking_xpath_list:
        result_products = driver.find_elements(by=By.XPATH, value=rank_xpath)

        if len(result_products) > 0:
            for result_product in result_products:

                # asinなし、または広告の場合は除外
                asin = result_product.get_attribute("data-asin")
                class_name = result_product.get_attribute("class")
                if not asin or "AdHolder" in class_name:
                    continue

                # 製品名取得
                for title_xpath in amazon_organic_rank_xpath.title_xpath_list:
                    product_title_list = result_product.find_elements(
                        by=By.XPATH,
                        value=title_xpath
                    )
                    if len(product_title_list) > 0:
                        product_name = product_title_list[0].text
                        break
                    else:
                        product_name = "取得不可"

                print(f"{ranking}:{asin}:{product_name}")
                ranking += 1

                if asin:
                    ad_elem = {
                        "ranking": ranking,
                        "asin": asin,
                        "product_name": product_name
                    }
                    rank_product_list.append(ad_elem)

                if ranking >= GET_RANKING_NUM:
                    break

    return rank_product_list


def register_data(crawl_keyword, crawl_started_at, kwsearch_ranking_list):
    table_name = "{}.{}_{}.amazon_organic_rank".format(
        CMN_CONFIG.GCP_PROJECT,
        CRAWLER_ENV,
        CMN_CONFIG.DATA_SET
    )
    bigquery_client = bigquery.Client()

    for kwsearch_ranking in kwsearch_ranking_list:
        current_datetime = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")

        target_asin = ""

        try:
            insert_row = [
                {
                    u"keyword": f"{crawl_keyword}",
                    u"ranking": f"{kwsearch_ranking['ranking']}",
                    u"asin": f"{kwsearch_ranking['asin']}",
                    u"product_name": f"{kwsearch_ranking['product_name']}",
                    u"crawl_started_at": f"{crawl_started_at}",
                    u"created_at": f"{current_datetime}",
                    u"updated_at": f"{current_datetime}"
                }
            ]
            print(insert_row)
            # 登録成功時にasinの製品情報の取得対象とする
            target_asin = kwsearch_ranking['asin']
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

    scraping_utils.publish_keepa_call_product(list(set(target_asin_list)))
