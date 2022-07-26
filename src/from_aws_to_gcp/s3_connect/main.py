import os
import boto3
import json
import base64

from datetime import datetime, timedelta
from google.cloud import secretmanager, storage, bigquery
from config.setting import CMN_CONFIG, ENV_CONFIG, GCP_ENV, REPORT_LIST


def get_object_list(session, target_date, report_name):
    object_list = []

    s3_client = session.client('s3')
    response = s3_client.list_objects_v2(
                Bucket=ENV_CONFIG.S3_BUCKET,
                Prefix=f"{target_date}/{report_name}"
    )
    for obj in response['Contents']:
        print(obj['Key'])
        object_list.append(obj['Key'])

    return object_list


# BigQuery テーブルカラム取得
def get_column_list(target_report):
    table_column_json = open(f"doc/bigquery/{target_report}.json", "r")
    table_column_list = json.load(table_column_json)
    column_list = []

    for column_info in table_column_list:
        column_list.append(column_info["name"])

    print(column_list)
    return column_list


def read_csv_file(file_list):
    """
    ファイル取得
    """
    read_storage_client = storage.Client()
    bucket = read_storage_client.get_bucket(f"{GCP_ENV}-{CMN_CONFIG.SETTING_BUCKET}")

    for file_path in file_list:

        blob = bucket.blob(file_path)
        get_csv_string = blob.download_as_string().decode('utf-8')
        csv_rows = get_csv_string.strip().splitlines()

        header_list = []
        insert_data_list = []
        for idx, csv_row in enumerate(csv_rows):
            row_array = csv_row.split(',')
            if idx == 0:
                # ヘッダ行処理
                header_list = row_array
            else:
                # データ格納
                insert_data = {}
                for idx, row_data in enumerate(row_array):
                    insert_data[header_list[idx]] = row_data
                insert_data_list.append(insert_data)
        break
    return insert_data_list


def save_object(session, s3_resource, object_list):

    print(f"save object START:{ENV_CONFIG.S3_BUCKET}")
    save_file_list = []
    s3_bucket = s3_resource.Bucket(ENV_CONFIG.S3_BUCKET)

    for object_name in object_list:
        object_array = object_name.split("/")
        object_array.reverse()
        file_name = object_array[0]
        tmp_file = f"/tmp/{file_name}"

        s3_bucket.download_file(object_name, tmp_file)
        print("download ok")
        if GCP_ENV != "local":
            storage_client = storage.Client()
            myBucket = storage_client.bucket(f"{GCP_ENV}-{CMN_CONFIG.SETTING_BUCKET}")

            blob = myBucket.blob(
                f"s3/{object_name}"
            )
            blob.upload_from_filename(tmp_file)
            os.remove(tmp_file)

            save_file_list.append(f"s3/{object_name}")

    print("save object END")
    return save_file_list


def regist_csv_data(target_table, insert_data_list):
    print(f"===========Get Report Data：{target_table}=========")
    # カラムを定義ファイルから取得
    table_column_list = get_column_list(target_table)

    # bigqueryで利用するテーブル [project ID].[データセット名].[テーブル名]
    table_name = "{}.{}_{}.c_flow_{}".format(CMN_CONFIG.PROJECT_ID, GCP_ENV, CMN_CONFIG.DATA_SET, target_table)
    print(table_name)
    bigquery_client = bigquery.Client()

    for insert_data in insert_data_list:
        '''
        current_datetime = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S")
        '''

        # json形式でデータを登録
        try:
            insert_row = []
            insert_dict = {}
            for column_name in table_column_list:
                insert_dict[column_name] = insert_data[column_name]

            insert_row.append(insert_dict)

        except Exception as e:
            print(f"regist error:{e}")

        print(insert_row)
        errors = bigquery_client.insert_rows_json(table_name, insert_row)
        if errors == []:
            print("New rows have been added.")
        else:
            print("Encountered errors while inserting rows: {}".format(errors))


def get_secret_key(property=""):
    if property != "":
        client = secretmanager.SecretManagerServiceClient()
        secret_path = client.secret_version_path(CMN_CONFIG.PROJECT_ID, property, "latest")
        secret_response = client.access_secret_version({"name": secret_path})

        return secret_response.payload.data.decode('UTF-8')

    return ""


def main(event, context):

    if 'data' in event:
        event_data = base64.b64decode(event['data']).decode('utf8')
        setting_list = json.loads(event_data)
    else:
        setting_list = {}

    # 処理レポートの指定
    if "target_report" in setting_list:
        target_report = setting_list['target_report']
    else:
        target_report = ""

    # 日付の指定（デフォルトは前日）
    if "target_date" in setting_list:
        target_date = setting_list['target_date']
    else:
        now_datetime = datetime.now()
        target_datetime = now_datetime - timedelta(days=1)
        target_date = target_datetime.strftime("%Y%m%d")

    # amcと同じキー
    access_key_id = get_secret_key("amc_accesskey")
    secret_access_key = get_secret_key("amc_secretkey")

    session = boto3.session.Session(
        region_name="us-east-1",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key
    )

    # ロール切り替え
    sts_client = session.client('sts')
    assumed_role_object = sts_client.assume_role(
        RoleArn=CMN_CONFIG.ROLE_ARN,
        RoleSessionName="AssumeRoleSession1"
    )
    credentials = assumed_role_object['Credentials']

    # セッション貼り直し
    session = boto3.session.Session(
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    for report_name in REPORT_LIST:
        if "target_report" in setting_list and target_report != report_name:
            print(f"{target_report}： Not subject to processing")
            continue

        object_list = get_object_list(session, target_date, report_name)

        s3_resource = boto3.resource(
            "s3",
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        save_file_list = save_object(session, s3_resource, object_list)
        print(save_file_list)
        insert_data_list = read_csv_file(save_file_list)
        regist_csv_data(report_name, insert_data_list)
    return "OK"
