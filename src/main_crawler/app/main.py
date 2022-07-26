import random
import time
import json
import logging

import usrlib.scraping as scraping

from usrlib.webdriver import crawler_webdriver
from config.setting import CRAWLER_ENV, HOST_NAME, VM_ZONE, ENV_CONFIG, CMN_CONFIG, HOURLY_SUB_PATH, IRREG_SUB_PATH

from datetime import datetime, timedelta, timezone
from google.cloud import pubsub_v1, bigquery

JST = timezone(timedelta(hours=+9), 'JST')
crawl_started_at = datetime.now(JST).strftime('%Y-%m-%d %H:00:00')
crawl_started_at_date = datetime.now(JST).strftime('%Y%m%d')
crawl_started_at_time = datetime.now(JST).strftime('%H0000')
crawl_limit_time = datetime.now(JST).strftime(f'%Y-%m-%d %H:{ENV_CONFIG.CRAWLER_END_MIN}:00')

EXEC_AMPM = datetime.now(JST).strftime('%p')


def regist_crawl_history(history_data, mb_flg=""):

    table_name = f"{CMN_CONFIG.GCP_PROJECT}.{CRAWLER_ENV}_{CMN_CONFIG.DATA_SET}.crawl_history"
    bigquery_client = bigquery.Client()

    ad_setting_str = ""
    if mb_flg:
        ad_setting_str = f":{mb_flg}"

    # json形式でデータを登録
    insert_row = [
        {
            u"crawl_started_at": crawl_started_at,
            u"host_name": HOST_NAME,
            u"crawler_setting": f"{history_data['mode']}:{history_data['crawler_setting']}{ad_setting_str}",
            u"target_url": history_data["target_url"],
            u"page_title": history_data["page_title"],
            u"html_file": history_data["html_file"],
            u"html_size": int(history_data["html_size"]),
            u"created_at": datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S'),
            u"crawl_key": history_data["crawl_key"]
        }
    ]

    errors = bigquery_client.insert_rows_json(table_name, insert_row)
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))


# subscriberから処理するurl_listを取得。メッセージがなくなるまで継続
# 定期実行MSGサブスクライバ(1時間に一回)
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    CMN_CONFIG.GCP_PROJECT, HOURLY_SUB_PATH
)
# 不定期実行MSGサブスクライバ
irreg_subscriber = pubsub_v1.SubscriberClient()
irreg_subscription_path = irreg_subscriber.subscription_path(
    CMN_CONFIG.GCP_PROJECT, IRREG_SUB_PATH
)

crawled_url_list = {}
mb_crawled_url_list = {}
blocked_flg = False

with subscriber:
    # LOOP_COUNTの回数分だけMSGを処理。MSGがない場合はbreak
    crawl_count = 0

    while crawl_count <= ENV_CONFIG.LOOP_COUNT_MAX:
        print(f"excuting...{crawl_count}／{ENV_CONFIG.LOOP_COUNT_MAX}")
        mode = "hourly"
        target_crawl_started_at = crawl_started_at
        target_subscription_path = subscription_path

        response = subscriber.pull(
            request={"subscription": target_subscription_path, "max_messages": 1}
        )

        # 定期実行MSGない場合は不定期実行から取得
        if not response.received_messages:
            print("get crawler_irreg message")
            mode = "daily"
            target_subscription_path = irreg_subscription_path
            response = irreg_subscriber.pull(
                request={"subscription": target_subscription_path, "max_messages": 1}
            )

            # dailyの場合はクロール時間補正
            # 午前午後、1−3時間かけて１回ずつ稼働。その為、午前午後でのクロール時間を統一する。
            if EXEC_AMPM == "AM":
                crawl_hour = "10"
            elif EXEC_AMPM == "PM":
                crawl_hour = "18"
            else:
                crawl_hour = "%H"
            target_crawl_started_at = datetime.now().strftime(f'%Y-%m-%d {crawl_hour}:00:00')

        # msg単位での所要時間を計る
        print(f"Crawl Start：{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')}")
        if response.received_messages:
            # pub/sub
            received_message = response.received_messages[0]
            crawler_setting = received_message.message.data.decode("utf-8")
            target_url = received_message.message.attributes.get("url")
            crawled_url_list.setdefault(crawler_setting, [])
            mb_crawled_url_list.setdefault(crawler_setting, [])

            # モバイルフラグ
            mb_flg = received_message.message.attributes.get("mb_flg")
            try:

                # ドライバー立ち上げ
                driver = crawler_webdriver.setting_webdriver(mb_flg)

                # 同じ設定でurlが重複している場合はクロールしない
                if (not mb_flg and target_url in crawled_url_list[crawler_setting]) or \
                        (mb_flg and target_url in mb_crawled_url_list[crawler_setting]) or \
                        target_url == "":

                    print(f"[Duplicate url]{crawler_setting}：{target_url}")
                else:

                    print(f"GET target_url：{target_url}")
                    driver.get(target_url)
                    # bot判定回避 ランダムでX秒待機
                    print(f"sleep START：{datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')}")
                    time.sleep(random.randint(ENV_CONFIG.SLEEP_MIN, ENV_CONFIG.SLEEP_MAX))
                    print(f"sleep END：{datetime.now(JST).strftime('%Y/%m/%d %H:%M:%S')}")

                    # ファイル保存名の仕様を要変更 urlそのままだと文字数制限で保存不可となる。それまでコメントアウト(20211011)
                    '''
                    save_file = {}
                    save_file["path"] = f"{crawler_setting}/{crawl_started_at_date}/{crawl_started_at_time}/"
                    save_file["file_name"] = f"{datetime.now(JST).strftime('%Y%m%d%H%M%S')}_{urllib.parse.quote(target_url, safe='')}"
                    '''
                    crawl_history = {}
                    crawl_history["mode"] = mode
                    crawl_history["crawler_setting"] = crawler_setting
                    crawl_history["target_url"] = target_url
                    crawl_history["page_title"] = driver.title
                    crawl_history["html_file"] = ""  # save_file["file_name"]

                    print("GET html")
                    target_html = driver.page_source
                    crawl_history["html_size"] = len(target_html)
                    if (
                        crawl_history["html_size"] <= ENV_CONFIG.IP_BLOCKED_HTML_SIZE
                        and crawl_history["page_title"] != "ページが見つかりません"
                        and crawl_history["page_title"] != "Access Checker"
                    ):
                        # blockされたと推測された場合は保存しない
                        print("****ip BLOCKED****")
                        blocked_flg = True
                        # 保存しないのでhtml_fileを空にする
                        crawl_history["html_file"] = ""
                    else:
                        '''crawler_webdriver.save_html(save_file, target_html)'''

                        print("*********scraping START************")
                        if not mb_flg:
                            print("pc")
                            crawl_history["crawl_key"] = eval(f"scraping.{crawler_setting}_scraping").scraping_main(target_url, driver, target_crawl_started_at)
                            crawled_url_list[crawler_setting].append(target_url)
                        else:
                            print("mobile")
                            crawl_history["crawl_key"] = eval(f"scraping.{crawler_setting}_scraping").mb_scraping_main(target_url, driver, target_crawl_started_at)
                            mb_crawled_url_list[crawler_setting].append(target_url)
                        print("*********scraping END************")

                    regist_crawl_history(crawl_history, mb_flg)
                    crawl_count += 1
                    print(f"crawl count:{crawl_count}")

                ack_ids = []
                ack_ids.append(received_message.ack_id)

                print(f"Crawl End：{datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')}")
                if blocked_flg:
                    # クロールに失敗した場合は、処理中MSGの再試行をpus/subにリクエスト
                    print("ip blocked")
                    subscriber.modify_ack_deadline(
                        request={
                            "subscription": target_subscription_path,
                            "ack_ids": ack_ids,
                            "ack_deadline_seconds": 0,
                        }
                    )
                    break
                else:
                    # 処理したメッセージをacknowledge
                    subscriber.acknowledge(
                        request={
                            "subscription": target_subscription_path,
                            "ack_ids": ack_ids
                        }
                    )
            except Exception:
                logging.error("traceback", exc_info=True)
            finally:
                driver.close()
                driver.quit()
        else:
            print("no crawler_admin message")
            break

        # 特定の時間が過ぎたも処理終了
        if datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S') >= crawl_limit_time:
            print("crawler time_limit ")
            break


# 停止メッセージ
if HOST_NAME != "" and HOST_NAME != "VM_ZONE":
    topic_id = f"{CRAWLER_ENV}-{CMN_CONFIG.CRAWLER_STOP_TOPIC}"

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(CMN_CONFIG.GCP_PROJECT, topic_id)

    data = {}
    data["host_name"] = HOST_NAME
    data["vm_zone"] = VM_ZONE
    data["status"] = "blocked" if blocked_flg else "success"

    data = json.dumps(data).encode("utf-8")
    future = publisher.publish(
        topic_path, data
    )

print("crawling end")
