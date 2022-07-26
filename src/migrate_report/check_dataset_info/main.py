import os
import tempfile
import json
import time

from datetime import datetime
from google.cloud import storage, bigquery
from config.setting import GCP_ENV, ENV_CONFIG, CMN_CONFIG

a_dataset = f"{ENV_CONFIG.A_PROJECT}.a"
b_dataset = f"{CMN_CONFIG.GCP_PROJECT}.{GCP_ENV}_datalake"

bigquery_client = bigquery.Client()

template_file = "template/add_column_to_bigquery.dml"


# レスポンス内容をjsonファイルにoutput
def save_result_to_storage(result_data_set, file_name):

    f, temp_file = tempfile.mkstemp()
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(
                result_data_set,
                ensure_ascii=False,
                indent=4
                )
            )

        storage_client = storage.Client()
        myBucket = storage_client.bucket("mori-test-bucket")
        output_dir = f"{datetime.now().strftime('%Y%m')}/"

        blob = myBucket.blob(
            f"{output_dir}{file_name}.json"
        )
        blob.upload_from_filename(temp_file)
        time.sleep(1)

    except Exception as e:
        print(f"save json error:{e}")
    finally:
        os.remove(temp_file)


# カラム追加SQLを出力
def save_sql_to_storage(schema_list, file_name):

    # SQLテンプレートを呼び出し
    with open(template_file, mode="r", encoding="utf-8") as temp_f:
        temp_lines = temp_f.read()

    # value
    add_schema_list = []
    for schema in schema_list:
        add_schema_list.append(f"ADD COLUMN {schema['name']} {schema['type']}")

    output_lines = temp_lines.replace("{__TABLE_ID__}", f"{b_dataset}.{file_name}")
    output_lines = output_lines.replace("{__ADD_COLUMN__}", ",\r\n".join(add_schema_list))

    f, temp_file = tempfile.mkstemp()
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(output_lines)

        storage_client = storage.Client()
        myBucket = storage_client.bucket("mori-test-bucket")
        output_dir = f"{datetime.now().strftime('%Y%m')}/"

        blob = myBucket.blob(
            f"{output_dir}{file_name}.sql"
        )
        blob.upload_from_filename(temp_file)
        time.sleep(1)

    except Exception as e:
        print(f"save json error:{e}")
    finally:
        os.remove(temp_file)


# テーブルスキーマ出力
def output_table_schema_json(dataset, table_id):
    output_schema_list = []
    output_table = bigquery_client.get_table(f'{dataset}.{table_id}')
    for schema in output_table.schema:
        output_schema_list.append(schema.to_api_repr())

    save_result_to_storage(output_schema_list, table_id)


def diff_column(table_id):
    print("column check")

    b_column = []
    b_table = bigquery_client.get_table(f"{b_dataset}.{table_id}")
    for schema in b_table.schema:
        schema_info = schema.to_api_repr()
        b_column.append(schema_info['name'])

    # colmnチェック
    diff_column = []
    a_table = bigquery_client.get_table(f"{a_dataset}.{table_id}")
    for schema in a_table.schema:
        schema_info = schema.to_api_repr()
        if schema_info['name'] != "dump_timestamp" and schema_info['name'] not in b_column:
            diff_column.append(schema_info)

    if len(diff_column) > 0:
        save_result_to_storage(diff_column, f"diff_{table_id}")
        save_sql_to_storage(diff_column, table_id)

        # 存在しないテーブルに関しては定義も出力
        output_table_schema_json(a_dataset, table_id)


def get_tables():

    not_exist_table = []
    dataset = bigquery_client.get_dataset(a_dataset)
    a_tables = list(bigquery_client.list_tables(dataset))

    for a_table in a_tables:

        # 存在チェック
        try:
            b_table = bigquery_client.get_table(f"{b_dataset}.{a_table.table_id}")
            print(f"table exist:{b_table.table_id}")
            diff_column(b_table.table_id)

        except Exception as e:
            print(f"table no not exist {a_table.table_id}:{e}")
            not_exist_table.append(a_table.table_id)

    save_result_to_storage(not_exist_table, "not_exist_table")
    for table_id in not_exist_table:
        # 存在しないテーブルに関しては定義を出力
        output_table_schema_json(a_dataset, table_id)


def main(event, context):
    print("Start：check a table schema")
    get_tables()
    return 'Success'
