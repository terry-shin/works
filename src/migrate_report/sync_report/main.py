import sys
import base64
import json
import time

from datetime import datetime, timedelta
from google.cloud import bigquery
from config.setting import ENV_CONFIG, GCP_ENV, CMN_CONFIG, TABLE_LIST

if GCP_ENV == 'local':
    sys.path.append('usrlib/')
import etc_utils.slack_utils as slack_utils


notice_title = f"【{GCP_ENV}】Export report"


# BigQuery テーブルカラム取得
def get_column_list(target_report):
    table_column_json = open(f"doc/bigquery/datalake/{target_report}.json", "r")
    table_column_list = json.load(table_column_json)
    column_list = []

    for column_info in table_column_list:
        column_list.append(column_info["name"])

    return column_list


# 初期処理
def initial_data_copy(target_report):
    print(f"=========Inital Data Copy: {target_report}=========")
    bigquery_client = bigquery.Client()

    # カラム編集
    table_column_list = get_column_list(target_report)

    # 一括で取得する
    select_insert_query = f"""
        INSERT INTO `{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_datalake.tmp_{target_report}` ({','.join(table_column_list)})
        SELECT {','.join(table_column_list)} FROM `{ENV_CONFIG.A_PROJECT}.a.{target_report}`;
    """
    bigquery_client.query(select_insert_query)


# バックアップ作成
def create_backup_table(target_table, date_list):
    print(f"===========Backup Table: {target_table}=========")
    bigquery_client = bigquery.Client()

    # バックアップ名に時間も含める
    now = datetime.now()
    now_str = now.strftime("%H%M%S")

    try:
        query_job = bigquery_client.copy_table(
            f"{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.{target_table}",
            f"{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_BACKUP}.{target_table}_{date_list['now']}_{now_str}"
        )
        test = query_job.result()
        print(test)
        return True
    except Exception as e:
        msg_body = {}
        msg_body["title"] = f"{target_table}：{date_list['target']}〜{date_list['now']} インポート"
        msg_body["text"] = f"バックアップ作成エラー\nFailure:{e}"
        slack_utils.send_notice(notice_title, "danger", msg_body)
        return False


# 洗い替えデータのクリーニング
def delete_replace_target_data(target_table, date_list):
    print(f"===========Delete Old Data：{target_table}=========")
    bigquery_client = bigquery.Client()
    target_date = date_list["target"]

    try:
        # 洗い替え対象のデータを削除
        delete_query = f"""
            DELETE FROM `{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.{target_table}`
                WHERE
                    date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
        """
        print(f"Send DELETE Query:{delete_query}")
        bigquery_client.query(delete_query)

        return True
    except Exception as e:
        msg_body = {}
        msg_body["title"] = f"{target_table}：{date_list['target']}〜{date_list['now']} インポート"
        msg_body["text"] = f"洗い替えデータ削除エラー\nFailure:{e}"
        slack_utils.send_notice(notice_title, "danger", msg_body)
        return False


# 過去{ENV_CONFIG.TARGET_DATE_RANGE}日分を洗い替え(json入れ子)
def ex_get_report_data_from_a(target_table, date_list):
    print(f"===========EX Get Report Data：{target_table}=========")
    bigquery_client = bigquery.Client()
    result_count_list = {"a": 0, "b": 0}
    target_date = date_list["target"]

    # カラムを定義ファイルから取得
    table_column_list = get_column_list(target_table)

    a_table = f"{ENV_CONFIG.A_PROJECT}.a.{target_table}"
    b_table = f"{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.{target_table}"

    try:
        a_count_query = f"""
            SELECT * FROM `{a_table}`
                WHERE
                    date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
        """
        select_result = bigquery_client.query(a_count_query).result()

        result_count_list["a"] = select_result.total_rows
        if result_count_list["a"] <= 0:
            return result_count_list

        print("target record count")
        print(result_count_list["a"])

        insert_rows = []
        insert_count = 0
        for idx, row in enumerate(select_result):
            insert_row = {}
            creative_json = {}
            landing_page_json = {}

            for col_idx, column in enumerate(table_column_list):
                if column == "dump_timestamp" or column == "date":
                    insert_row[column] = row[col_idx].isoformat()
                elif column == "creative":
                    if row[col_idx] is None:
                        continue

                    creative_json = json.loads(row[col_idx])
                    if 'brandName' in creative_json:
                        insert_row['creative_brand_name'] = creative_json['brandName']
                        insert_row['creative_brand_logo_asset_id'] = creative_json['brandLogoAssetID'] if "brandLogoAssetID" in creative_json else ""
                        insert_row['creative_headline'] = creative_json['headline'] if "headline" in creative_json else ""
                        insert_row['creative_asins'] = ",".join(creative_json['asins']) if "asins" in creative_json else ""
                        insert_row['creative_brand_logo_crop'] = json.dumps(creative_json['brandLogoCrop']) if "brandLogoCrop" in creative_json else "{}"
                        insert_row['creative_custom_image_crop'] = json.dumps(creative_json['customImageCrop']) if "customImageCrop" in creative_json else "{}"
                        insert_row['creative_custom_image_asset_id'] = creative_json['customImageAssetId'] if "customImageAssetId" in creative_json else ""
                        insert_row['creative_brand_logo_url'] = creative_json['brandLogoUrl'] if "brandLogoUrl" in creative_json else ""
                    else:
                        insert_row['creative_asins'] = ",".join(creative_json['asins']) if "asins" in creative_json else ""
                        insert_row['creative_video_media_ids'] = ",".join(creative_json['videoMediaIds']) if "videoMediaIds" in creative_json else ""
                        insert_row['creative_type'] = creative_json['type'] if "type" in creative_json else ""
                elif column == "landing_page":
                    if row[col_idx] is None:
                        continue

                    landing_page_json = json.loads(row[col_idx])
                    insert_row['landing_page_type'] = landing_page_json['pageType']
                    insert_row['landing_page_url'] = landing_page_json['url']
                else:
                    insert_row[column] = row[col_idx]
            insert_rows.append(insert_row)
            insert_count += 1

            # 1000件目または最後のレコードの場合、insertを実行
            if insert_count >= 1000 or idx >= result_count_list["a"]-1:
                errors = bigquery_client.insert_rows_json(b_table, insert_rows)
                if errors == []:
                    print(f"New rows have been added. {idx+1}/{result_count_list['a']}")
                else:
                    print("Encountered errors while inserting rows: {}".format(errors))
                insert_rows = []
                insert_count = 0

        # 登録結果の確認
        # 加工の場合は長めに待機
        time.sleep(90)
        b_count_query = f"""
            SELECT count(*) FROM `{b_table}`
                WHERE
                    date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
        """
        select_result = bigquery_client.query(b_count_query).result()

        for b_count in select_result:
            result_count_list["b"] = b_count[0]

    except Exception as e:
        msg_body = {}
        msg_body["title"] = f"{target_table}：{date_list['target']}〜{date_list['now']} インポート"
        msg_body["text"] = f"データインポートエラー\nFailure:{e}"
        slack_utils.send_notice(notice_title, "danger", msg_body)
    finally:
        return result_count_list


# 過去{ENV_CONFIG.TARGET_DATE_RANGE}日分を洗い替え
def get_report_data_from_a(target_table, date_list):
    print(f"===========Get Report Data：{target_table}=========")
    bigquery_client = bigquery.Client()
    result_count_list = {"a": 0, "b": 0}
    target_date = date_list["target"]

    # カラムを定義ファイルから取得
    table_column_list = get_column_list(target_table)

    try:
        a_count_query = f"""
            SELECT count(*) FROM `{ENV_CONFIG.A_PROJECT}.b.{target_table}`
                WHERE
                    date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
        """
        select_result = bigquery_client.query(a_count_query).result()

        for a_count in select_result:
            result_count_list["a"] = a_count[0]

        if target_table == "ams_profiles":
            migrate_ams_profiles(target_table, date_list)
        else:
            # 容量が大きすぎるので直接インサート
            select_insert_query = f"""
                INSERT INTO `{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.{target_table}`
                    ({','.join(table_column_list)})
                SELECT {','.join(table_column_list)} FROM `{ENV_CONFIG.A_PROJECT}.a.{target_table}`
                    WHERE
                        date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
            """

            print(f"Send Query:{select_insert_query}")
            bigquery_client.query(select_insert_query)

        # 登録結果の確認
        time.sleep(90)
        b_count_query = f"""
            SELECT count(*) FROM `{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.{target_table}`
                WHERE
                    date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
        """
        select_result = bigquery_client.query(b_count_query).result()

        for b_count in select_result:
            result_count_list["b"] = b_count[0]

    except Exception as e:
        msg_body = {}
        msg_body["title"] = f"{target_table}：{date_list['target']}〜{date_list['now']} インポート"
        msg_body["text"] = f"データインポートエラー\nFailure:{e}"
        slack_utils.send_notice(notice_title, "danger", msg_body)
    finally:
        return result_count_list


# ams_profilesのみjsonの解析あるため別処理
def migrate_ams_profiles(target_table, date_list):
    target_date = date_list["target"]

    bigquery_client = bigquery.Client()
    insert_list = []

    try:
        select_query = f"""
            SELECT * FROM `{ENV_CONFIG.A_PROJECT}.b.{target_table}`
                    WHERE
                        date >= '{target_date[:4]}-{target_date[4:6]}-{target_date[6:]}';
        """

        select_job = bigquery_client.query(select_query)
        select_result = select_job.result()

        if select_result.total_rows > 0:
            for row in select_result:
                insert_row = {}
                insert_row['dump_timestamp'] = row[0].isoformat()
                insert_row['date'] = row[1].isoformat()
                insert_row['account_id'] = row[2]
                insert_row['profile_id'] = row[3]

                account_info = json.loads(row[4])
                insert_row['marketplace_string_id'] = account_info['marketplaceStringId']
                insert_row['id'] = account_info['id']
                insert_row['type'] = account_info['type']
                insert_row['name'] = account_info['name']

                if "validPaymentMethod" in account_info:
                    insert_row['valid_payment_method'] = account_info['validPaymentMethod']
                else:
                    insert_row['valid_payment_method'] = False

                insert_row['country_code'] = row[5]
                insert_row['currency_code'] = row[6]
                insert_row['daily_budget'] = row[7]
                insert_row['timezone'] = row[8]

                print(insert_row)
                insert_list.append(insert_row)

            errors = bigquery_client.insert_rows_json(
                f"{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.{target_table}",
                insert_list
            )
            if errors == []:
                print("New rows have been added.")
            else:
                print("Encountered errors while inserting rows: {}".format(errors))
    except Exception as e:
        print(f"migrate_ams_profiles error:{e}")


# 連携履歴記録
def regist_sync_history(history_data):

    table_name = f"{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_{CMN_CONFIG.B_DATALAKE}.sync_history"
    bigquery_client = bigquery.Client()

    # json形式でデータを登録
    insert_row = [
        {
            u"sync_date": datetime.now().strftime('%Y-%m-%d'),
            u"start_date": history_data['start_date'],
            u"end_date": history_data['end_date'],
            u"target_table": history_data['target_table'],
            u"a_record_count": history_data['a_record_count'],
            u"b_record_count": history_data['b_record_count'],
            u"status": history_data["status"],
            u"created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
    ]

    errors = bigquery_client.insert_rows_json(table_name, insert_row)
    if errors == []:
        print("New rows have been added.")
    else:
        print("Encountered errors while inserting rows: {}".format(errors))


def main(event, context):

    # パラメータで処理対象日指定がある場合に取得
    setting_list = {}
    if 'data' in event:
        event_data = base64.b64decode(event['data']).decode('utf8')
        setting_list = json.loads(event_data)
    else:
        return "no parameter"
    print(setting_list)

    # 初期処理の場合
    if "initial_flg" in setting_list and setting_list["initial_flg"]:
        if "target_report" in setting_list and\
                (setting_list["target_report"] and setting_list["target_report"] in TABLE_LIST):
            initial_data_copy(setting_list["target_report"])

            msg_body = {}
            msg_body["title"] = f"{setting_list['target_report']}：初期データ投入"
            msg_body["text"] = "処理完了"
            result = "good"

            slack_utils.send_notice(notice_title, result, msg_body)
    else:
        # 基準日の指定がない場合は、処理当日の日付を起点として、データの洗い替えを実施
        # 対象日付を{ENV_CONFIG.TARGET_DATE_RANGE}日前に設定
        date_list = {}
        now = datetime.now()
        date_list["now"] = now.strftime('%Y%m%d')

        if "target_date" not in setting_list or not setting_list["target_date"]:
            target = now - timedelta(days=ENV_CONFIG.TARGET_DATE_RANGE)
            date_list["target"] = target.strftime('%Y%m%d')
        else:
            date_list["target"] = setting_list["target_date"]

        for target_report in TABLE_LIST:

            # パラメータによる指定がある場合、対象以外はskip
            if "target_report" in setting_list and\
                    (setting_list["target_report"] and setting_list["target_report"] != target_report):
                print(f"{target_report}： Not subject to processing")
                continue

            # モニタリング用履歴
            history_data = {
                "start_date": f'{date_list["target"][:4]}-{date_list["target"][4:6]}-{date_list["target"][6:]}',
                "end_date": datetime.now().strftime('%Y-%m-%d'),
                "target_table": target_report,
                "a_record_count": 0,
                "b_record_count": 0,
                "status": "Failure"
            }

            # インポート結果
            msg_body = {}
            msg_body["title"] = f"{target_report}：{date_list['target']}〜{date_list['now']} インポート実行結果"
            msg_body["text"] = "取込み結果：エラー"
            result = "danger"
            if create_backup_table(target_report, date_list):

                if delete_replace_target_data(target_report, date_list):
                    print("OK")
                    if target_report == "ams_sponsored_brands_campaigns":
                        result_count_list = ex_get_report_data_from_a(target_report, date_list)
                    else:
                        result_count_list = get_report_data_from_a(target_report, date_list)

                    history_data['a_record_count'] = int(result_count_list['a'])
                    history_data['b_record_count'] = int(result_count_list['b'])

                    msg_body["text"] = f"取込み結果：{result_count_list['a']}レコード中 / {result_count_list['b']}レコード登録"
                    if result_count_list['b'] == result_count_list['a']:
                        result = "good"
                        history_data['status'] = "Success"
                    else:
                        result = "danger"

            regist_sync_history(history_data)
            slack_utils.send_notice(notice_title, result, msg_body)
