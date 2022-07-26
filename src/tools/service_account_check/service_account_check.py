import os

from google.cloud import storage


# GCP設定
base_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"{base_dir}/cre/cre.json"

def cloud_storage_upload_check():

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket("upload_bucket")

        blob = bucket.blob("test.txt")
        blob.upload_from_filename(filename="./input/test.txt")

        for f in bucket.list_blobs():
            print(f)
    except Exception as e:
        print(f"ERR:{e}")

# サービスアカウントの動作チェック用コード
# 必要に応じて関数を追加していく
# 不要なチェックはコメントアウト
print("START：Service Account Check")

# cloud storageチェック
# print("[CHECK]Cloud Storage")
# cloud_storage_upload_check()

print("END：Service Account Check")
