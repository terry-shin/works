import datetime
import usrlib.scraping.amazon_ads_rank_xpath as amazon_ads_rank_xpath
import usrlib.ecpf_utils.scraping_utils as scraping_utils

from usrlib.logger import crawler_logger
from google.cloud import bigquery
from config.setting import CRAWLER_ENV, CMN_CONFIG

from selenium.webdriver.common.by import By

# crawl対象asinリスト
target_asin_list = []

# module logger
module_logger = crawler_logger.get_module_logger(__name__)


def scraping_main(target_url, driver, crawl_started_at):
    module_logger.info('amazon_ads_rank_scraping START')
    crawl_keyword = scraping_utils.fetch_keyword_from_url(target_url)
    module_logger.info(f'crawl_keyword:{crawl_keyword}')

    kwsearch_ads_list = []
    target_asin_list.clear()

    kwsearch_ads_list += fetch_sponsor_ads(
        driver,
        amazon_ads_rank_xpath.sponsor_ads_xpath_list,
        amazon_ads_rank_xpath.sponsor_ads_title_xpath_list
        )

    if len(kwsearch_ads_list) > 0:
        register_data(crawl_keyword, crawl_started_at, kwsearch_ads_list)
    module_logger.info('amazon_ads_rank_scraping END')
    return crawl_keyword


def register_data(crawl_keyword, crawl_started_at, search_page_ads):
    # bigqueryで利用するテーブル [project ID].[データセット名].[テーブル名]
    table_name = "{}.{}_{}.amazon_ads_rank".format(CMN_CONFIG.GCP_PROJECT, CRAWLER_ENV, CMN_CONFIG.ECPF_DATA_SET)
    bigquery_client = bigquery.Client()

    for search_page_ad in search_page_ads:
        current_datetime = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")

        target_asin = ""

        # json形式でデータを登録
        try:
            insert_row = [
                {u"keyword": f"{crawl_keyword}",
                    u"ad_type": f"{search_page_ad['ad_type']}",
                    u"rank": f"{search_page_ad['rank']}",
                    u"asin": f"{search_page_ad['asin']}",
                    u"crawl_started_at": f"{crawl_started_at}",
                    u"created_at": f"{current_datetime}",
                    u"updated_at": f"{current_datetime}",
                    u"product_name": f"{search_page_ad['product_name']}"}
                ]
            # 登録成功時にasinの製品情報の取得対象とする
            target_asin = search_page_ad['asin']

        except Exception as e:
            module_logger.error(f'regist error:{e}')

        module_logger.info(f'insert_row{insert_row}')
        errors = bigquery_client.insert_rows_json(table_name, insert_row)
        if errors == []:
            module_logger.debug('New rows have been added.')

            # 登録成功時、asin設定あればクローリング対象とする
            if len(target_asin) > 0 and target_asin not in target_asin_list:
                target_asin_list.append(target_asin)
        else:
            module_logger.warning("Encountered errors while inserting rows: {}".format(errors))

    scraping_utils.publish_keepa_call_product(list(set(target_asin_list)))


def fetch_sponsor_ads(driver, sp_xpath_list, sponsor_ads_title_xpath_list):
    # プロダクト広告取得
    module_logger.debug('START')

    sp_ads_list = []
    rank = 0
    for sp_xpath in sp_xpath_list:
        sponsor_ads = driver.find_elements(by=By.XPATH, value=sp_xpath)

        # sp_xpath_list中の他のsp_xpathで既に広告取得できていたらループを抜ける
        if len(sp_ads_list) > 0:
            break

        if len(sponsor_ads) > 0:
            for sponsor_ad in sponsor_ads:
                if 'スポンサー' in sponsor_ad.get_attribute("textContent"):
                    asin = sponsor_ad.get_attribute("data-asin")
                else:
                    continue

                for title_xpath in sponsor_ads_title_xpath_list:
                    product_title_list = sponsor_ad.find_elements(by=By.XPATH, value=title_xpath)
                    if len(product_title_list) > 0:
                        product_name = product_title_list[0].text
                        break
                    else:
                        product_name = "取得不可"

                if asin:
                    ad_type = "スポンサープロダクト広告"
                    rank += 1

                    ad_elem = {
                        "ad_type": ad_type,
                        "rank": rank,
                        "asin": asin,
                        "product_name": product_name
                    }
                    module_logger.debug(f'{rank}:{ad_type}:{asin}:{product_name}')
                    sp_ads_list.append(ad_elem)

    module_logger.debug('SP_ADS_LIST LENGTH')
    module_logger.debug(len(sp_ads_list))

    if len(sp_ads_list) <= 0:
        module_logger.warning(f'[{driver.title}] SP_ADS_LIST: No Data')

    module_logger.debug('END')
    return sp_ads_list
